"""
Smart API Key Routing System
Features: Key rotation, health checks, cooldown, automatic failover
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import httpx
import logging

logger = logging.getLogger(__name__)


class KeyStatus(Enum):
    ACTIVE = "active"
    COOLDOWN = "cooldown"
    RATE_LIMITED = "rate_limited"
    DEAD = "dead"
    HEALTHY = "healthy"


@dataclass
class APIKey:
    key: str
    provider: str
    priority: int = 0
    max_requests_per_minute: int = 60
    cooldown_seconds: int = 60
    health_check_url: Optional[str] = None
    health_check_method: str = "GET"
    
    # Runtime state
    status: KeyStatus = KeyStatus.HEALTHY
    last_used: float = 0
    last_error: Optional[str] = None
    cooldown_until: float = 0
    request_count: int = 0
    error_count: int = 0
    success_count: int = 0
    
    def is_available(self) -> bool:
        now = time.time()
        if self.status == KeyStatus.DEAD:
            return False
        if self.status == KeyStatus.COOLDOWN and now < self.cooldown_until:
            return False
        if self.request_count >= self.max_requests_per_minute:
            return False
        return True
    
    def mark_success(self):
        self.last_used = time.time()
        self.request_count += 1
        self.success_count += 1
        self.error_count = 0
        self.last_error = None
        if self.status == KeyStatus.COOLDOWN:
            self.status = KeyStatus.HEALTHY
    
    def mark_error(self, error: str):
        self.last_error = error
        self.error_count += 1
        self.last_used = time.time()
        
        if self.error_count >= 3:
            self.status = KeyStatus.COOLDOWN
            self.cooldown_until = time.time() + self.cooldown_seconds
            logger.warning(f"Key {self.key[:10]}... entering cooldown: {error}")
        
        if self.error_count >= 10:
            self.status = KeyStatus.DEAD
            logger.error(f"Key {self.key[:10]}... marked as DEAD")
    
    def mark_rate_limited(self):
        self.status = KeyStatus.RATE_LIMITED
        self.cooldown_until = time.time() + self.cooldown_seconds * 2
        logger.warning(f"Key {self.key[:10]}... rate limited")
    
    def reset_rate_limit(self):
        self.request_count = 0
    
    def get_wait_time(self) -> float:
        if self.status == KeyStatus.DEAD:
            return float('inf')
        if self.status == KeyStatus.COOLDOWN:
            return max(0, self.cooldown_until - time.time())
        if self.request_count >= self.max_requests_per_minute:
            return 60
        return 0


class KeyRouter:
    """
    Smart API Key Router with:
    - Automatic key rotation
    - Health checks
    - Cooldown management
    - Rate limiting
    - Priority-based routing
    """
    
    def __init__(self):
        self.keys: Dict[str, List[APIKey]] = {}
        self.health_check_interval: int = 60
        self._health_check_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
    def register_key(self, provider: str, key: str, **kwargs):
        if provider not in self.keys:
            self.keys[provider] = []
        
        api_key = APIKey(key=key, provider=provider, **kwargs)
        self.keys[provider].append(api_key)
        self.keys[provider].sort(key=lambda k: k.priority, reverse=True)
        logger.info(f"Registered key for {provider}")
    
    def register_keys(self, provider: str, keys: List[str], **kwargs):
        for i, key in enumerate(keys):
            self.register_key(provider, key, priority=kwargs.get('priority', len(keys)-i), **kwargs)
    
    async def get_available_key(self, provider: str) -> Optional[APIKey]:
        async with self._lock:
            if provider not in self.keys:
                return None
            
            available_keys = [k for k in self.keys[provider] if k.is_available()]
            if not available_keys:
                return None
            
            return available_keys[0]
    
    async def get_key_with_fallback(self, provider: str) -> Optional[APIKey]:
        start_time = time.time()
        max_wait = 120
        
        while time.time() - start_time < max_wait:
            key = await self.get_available_key(provider)
            if key:
                return key
            
            min_wait = min(k.get_wait_time() for k in self.keys.get(provider, []))
            if min_wait == float('inf'):
                break
            
            await asyncio.sleep(min(5, min_wait))
        
        return None
    
    def report_success(self, provider: str, key: str):
        for k in self.keys.get(provider, []):
            if k.key == key:
                k.mark_success()
                break
    
    def report_error(self, provider: str, key: str, error: str):
        for k in self.keys.get(provider, []):
            if k.key == key:
                k.mark_error(error)
                if '429' in error or 'rate limit' in error.lower():
                    k.mark_rate_limited()
                break
    
    async def health_check_key(self, key: APIKey) -> bool:
        if not key.health_check_url:
            return True
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    key.health_check_url,
                    headers={"Authorization": f"Bearer {key.key}"}
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed for {key.provider}: {e}")
            return False
    
    async def _health_check_loop(self):
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                for provider, keys in self.keys.items():
                    for key in keys:
                        if key.status == KeyStatus.DEAD:
                            is_healthy = await self.health_check_key(key)
                            if is_healthy:
                                key.status = KeyStatus.HEALTHY
                                key.error_count = 0
                                logger.info(f"Key {key.key[:10]}... recovered")
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def start_health_checks(self):
        self._health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def stop_health_checks(self):
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
    
    def get_stats(self) -> Dict[str, Any]:
        stats = {}
        for provider, keys in self.keys.items():
            stats[provider] = {
                "total": len(keys),
                "available": sum(1 for k in keys if k.is_available()),
                "healthy": sum(1 for k in keys if k.status == KeyStatus.HEALTHY),
                "cooldown": sum(1 for k in keys if k.status == KeyStatus.COOLDOWN),
                "dead": sum(1 for k in keys if k.status == KeyStatus.DEAD),
                "keys": [
                    {
                        "status": k.status.value,
                        "success_count": k.success_count,
                        "error_count": k.error_count,
                        "last_used": k.last_used
                    }
                    for k in keys
                ]
            }
        return stats


# Global router instance
router = KeyRouter()


def setup_gemini_keys(keys: List[str]):
    health_url = "https://generativelanguage.googleapis.com/v1/models?key="
    for i, key in enumerate(keys):
        router.register_key(
            "gemini", key, priority=len(keys)-i, cooldown_seconds=60,
            health_check_url=health_url + key, max_requests_per_minute=60
        )

def setup_sambanova_keys(keys: List[str]):
    for i, key in enumerate(keys):
        router.register_key(
            "sambanova", key, priority=len(keys)-i, cooldown_seconds=60,
            health_check_url="https://api.sambanova.ai/api/v1/models", max_requests_per_minute=120
        )

def setup_openrouter_keys(keys: List[str]):
    for i, key in enumerate(keys):
        router.register_key(
            "openrouter", key, priority=len(keys)-i, cooldown_seconds=60,
            health_check_url="https://openrouter.ai/api/v1/models", max_requests_per_minute=100
        )

def setup_github_marketplace_keys(keys: List[str]):
    for i, key in enumerate(keys):
        router.register_key(
            "github", key, priority=len(keys)-i, cooldown_seconds=30,
            health_check_url="https://api.github.com/user", max_requests_per_minute=5000
        )


def load_keys_from_env():
    """Load API keys from environment variables"""
    import os
    
    # Gemini keys
    gemini_keys = []
    for i in range(1, 7):
        key = os.environ.get(f"GEMINI_API_KEY_{i}")
        if key:
            gemini_keys.append(key)
    if gemini_keys:
        setup_gemini_keys(gemini_keys)
    
    # SambaNova keys
    sambanova_keys = []
    for i in range(1, 11):
        key = os.environ.get(f"SAMBANOVA_API_KEY_{i}")
        if key:
            sambanova_keys.append(key)
    if sambanova_keys:
        setup_sambanova_keys(sambanova_keys)
    
    # OpenRouter keys
    openrouter_keys = []
    for i in range(1, 11):
        key = os.environ.get(f"OPENROUTER_API_KEY_{i}")
        if key:
            openrouter_keys.append(key)
    if openrouter_keys:
        setup_openrouter_keys(openrouter_keys)
    
    # GitHub keys
    github_keys = []
    for i in range(1, 11):
        key = os.environ.get(f"LLM_MARKET_KEY_{i}")
        if key:
            github_keys.append(key)
    if github_keys:
        setup_github_marketplace_keys(github_keys)
    
    return len(gemini_keys) + len(sambanova_keys) + len(openrouter_keys) + len(github_keys)


# Load keys from environment on import
total_keys = load_keys_from_env()
logger.info(f"Key router initialized with {total_keys} API keys")
