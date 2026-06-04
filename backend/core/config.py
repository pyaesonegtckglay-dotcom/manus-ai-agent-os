"""Application configuration using Pydantic settings."""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Manus AI Agent OS"
    APP_VERSION: str = "0.2.0"
    DEBUG: bool = True
    
    # Supabase - use environment variables
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://muqqdllxsnnhzasffbsw.supabase.co")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # E2B Sandbox
    E2B_API_KEY: str = os.getenv("E2B_API_KEY", "")
    E2B_SANDBOX_TEMPLATE: str = "base"
    
    # Upstash Redis
    UPSTASH_REDIS_REST_URL: str = os.getenv("UPSTASH_REDIS_REST_URL", "https://prime-sawfish-129006.upstash.io")
    UPSTASH_REDIS_REST_TOKEN: str = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
    
    # AI Providers
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    SAMBANOVA_API_KEY: str = os.getenv("SAMBANOVA_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # HuggingFace
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    
    # Tavily Search
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    
    # GitHub
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    
    # Google (for workspace integration)
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    
    # CORS - allow all for deployment
    CORS_ORIGINS: list[str] = ["*"]
    
    # WebSocket
    WS_PING_INTERVAL: int = 30
    WS_PING_TIMEOUT: int = 10
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"  # Allow extra environment variables
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()