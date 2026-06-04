"""Application configuration using Pydantic settings."""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Manus AI Agent OS"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Supabase
    SUPABASE_URL: str = "https://muqqdllxsnnhzasffbsw.supabase.co"
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    
    # E2B Sandbox
    E2B_API_KEY: str = ""
    E2B_SANDBOX_TEMPLATE: str = "base"
    
    # Upstash Redis
    UPSTASH_REDIS_REST_URL: str = "https://prime-sawfish-129006.upstash.io"
    UPSTASH_REDIS_REST_TOKEN: str = ""
    
    # AI Providers
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    SAMBANOVA_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    # GitHub
    GITHUB_TOKEN: str = ""
    
    # Google (for workspace integration)
    GOOGLE_APPLICATION_CREDENTIALS: str = "config/firebase-service-account.json"
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "https://*.vercel.app"]
    
    # WebSocket
    WS_PING_INTERVAL: int = 30
    WS_PING_TIMEOUT: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()