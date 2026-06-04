"""Configuration management for the project."""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class GitHubConfig:
    token: str
    token_2: Optional[str] = None


@dataclass
class HuggingFaceConfig:
    token: str


@dataclass
class VercelConfig:
    token: str


@dataclass
class E2BConfig:
    api_key: str


@dataclass
class DatabaseConfig:
    url: str


@dataclass
class RedisConfig:
    url: str


@dataclass
class FirebaseConfig:
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    client_x509_cert_url: str
    universe_domain: str = "googleapis.com"

    def to_dict(self) -> dict:
        return {
            "type": "service_account",
            "project_id": self.project_id,
            "private_key_id": self.private_key_id,
            "private_key": self.private_key,
            "client_email": self.client_email,
            "client_id": self.client_id,
            "auth_uri": self.auth_uri,
            "token_uri": self.token_uri,
            "auth_provider_x509_cert_url": self.auth_provider_x509_cert_url,
            "client_x509_cert_url": self.client_x509_cert_url,
            "universe_domain": self.universe_domain,
        }


class Config:
    """Main configuration class that loads all settings from environment variables."""
    
    def __init__(self):
        # GitHub
        self.github = GitHubConfig(
            token=os.getenv("GITHUB_TOKEN", ""),
            token_2=os.getenv("GITHUB_TOKEN_2", ""),
        )
        
        # Hugging Face
        self.huggingface = HuggingFaceConfig(
            token=os.getenv("HF_TOKEN", ""),
        )
        
        # Vercel
        self.vercel = VercelConfig(
            token=os.getenv("VERCEL_TOKEN", ""),
        )
        
        # E2B
        self.e2b = E2BConfig(
            api_key=os.getenv("E2B_API_KEY", ""),
        )
        
        # Database
        self.database = DatabaseConfig(
            url=os.getenv("DATABASE_URL", ""),
        )
        
        # Redis
        self.redis = RedisConfig(
            url=os.getenv("REDIS_URL", ""),
        )
        
        # Firebase (from individual env vars)
        self.firebase = FirebaseConfig(
            project_id=os.getenv("FIREBASE_PROJECT_ID", "manus-poe-agent"),
            private_key_id=os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
            private_key=os.getenv("FIREBASE_PRIVATE_KEY", ""),
            client_email=os.getenv("FIREBASE_CLIENT_EMAIL", ""),
            client_id=os.getenv("FIREBASE_CLIENT_ID", ""),
            auth_uri=os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            token_uri=os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
            auth_provider_x509_cert_url=os.getenv(
                "FIREBASE_AUTH_PROVIDER_X509_CERT_URL",
                "https://www.googleapis.com/oauth2/v1/certs"
            ),
            client_x509_cert_url=os.getenv(
                "FIREBASE_CLIENT_X509_CERT_URL",
                ""
            ),
        )
    
    def save_firebase_service_account(self, path: str = "config/firebase-service-account.json"):
        """Save Firebase service account JSON to a file."""
        import json
        import os
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.firebase.to_dict(), f, indent=2)


# Global config instance
config = Config()