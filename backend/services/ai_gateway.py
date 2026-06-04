"""Multi-model AI Gateway for task routing."""
from typing import Optional, Literal
from enum import Enum
from openai import AsyncOpenAI
import anthropic
from backend.core.config import get_settings


class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    SAMBANOVA = "sambanova"


class ModelRole(str, Enum):
    PLANNING = "planning"  # Complex reasoning, task decomposition
    EXECUTION = "execution"  # Code generation, fast operations


class AIModel:
    """Model configuration."""
    def __init__(self, provider: ModelProvider, model_id: str, role: ModelRole):
        self.provider = provider
        self.model_id = model_id
        self.role = role


# Default model configurations
DEFAULT_MODELS = {
    "planning": AIModel(ModelProvider.ANTHROPIC, "claude-3-5-sonnet-20241022", ModelRole.PLANNING),
    "execution": AIModel(ModelProvider.OPENROUTER, "anthropic/claude-3.5-sonnet", ModelRole.EXECUTION),
}


class AIGateway:
    def __init__(self):
        self.settings = get_settings()
        self.openai = AsyncOpenAI(api_key=self.settings.OPENROUTER_API_KEY)
        self.anthropic = anthropic.AsyncAnthropic(api_key=self.settings.ANTHROPIC_API_KEY)
        self.models = DEFAULT_MODELS.copy()
    
    async def complete(
        self,
        prompt: str,
        role: ModelRole = ModelRole.EXECUTION,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """Generate completion using the appropriate model."""
        model = self.models.get(role.value, self.models["execution"])
        
        if model.provider == ModelProvider.ANTHROPIC:
            return await self._anthropic_complete(model.model_id, prompt, system, temperature, max_tokens)
        elif model.provider == ModelProvider.OPENAI or model.provider == ModelProvider.OPENROUTER:
            return await self._openai_complete(model.model_id, prompt, system, temperature, max_tokens)
        elif model.provider == ModelProvider.GEMINI:
            return await self._gemini_complete(model.model_id, prompt, system, temperature, max_tokens)
        elif model.provider == ModelProvider.SAMBANOVA:
            return await self._sambanova_complete(model.model_id, prompt, system, temperature, max_tokens)
        
        raise ValueError(f"Unsupported provider: {model.provider}")
    
    async def _anthropic_complete(
        self,
        model: str,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Complete using Anthropic/Claude."""
        messages = []
        if system:
            messages.append({"role": "assistant", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.anthropic.messages.create(
            model=model,
            messages=messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.content[0].text
    
    async def _openai_complete(
        self,
        model: str,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Complete using OpenAI-compatible API."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    async def _gemini_complete(
        self,
        model: str,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Complete using Google Gemini via API."""
        import httpx
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.settings.GEMINI_API_KEY}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    
    async def _sambanova_complete(
        self,
        model: str,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Complete using SambaNova."""
        import httpx
        
        url = f"https://api.sambanova.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.settings.SAMBANOVA_API_KEY}"}
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def set_model(self, role: ModelRole, provider: ModelProvider, model_id: str):
        """Configure a model for a specific role."""
        self.models[role.value] = AIModel(provider, model_id, role)
    
    async def health_check(self) -> dict:
        """Check AI provider health."""
        status = {}
        
        try:
            await self._anthropic_complete("claude-3-5-sonnet-20241022", "test", None, 0, 1)
            status["anthropic"] = True
        except Exception:
            status["anthropic"] = False
        
        try:
            await self._openai_complete("gpt-4o-mini", "test", None, 0, 1)
            status["openai"] = True
        except Exception:
            status["openai"] = False
        
        return status


# Singleton instance
_ai_gateway: Optional[AIGateway] = None


def get_ai_gateway() -> AIGateway:
    global _ai_gateway
    if _ai_gateway is None:
        _ai_gateway = AIGateway()
    return _ai_gateway