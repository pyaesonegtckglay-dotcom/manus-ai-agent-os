"""Authentication service using Supabase Auth."""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from dataclasses import dataclass
import httpx

from backend.core.config import get_settings


security = HTTPBearer(auto_error=False)


@dataclass
class User:
    """Authenticated user data."""
    id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    metadata: Optional[dict] = None


class AuthService:
    """Supabase Auth service."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase_url = self.settings.SUPABASE_URL
        # Note: In production, use SUPABASE_SERVICE_KEY for server-side operations
        # and client-side auth for browser
        self.service_key = self.settings.SUPABASE_SERVICE_KEY
    
    async def get_user_from_token(self, token: str) -> Optional[User]:
        """Verify JWT token and return user."""
        try:
            # Call Supabase auth endpoint to verify token
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/auth/v1/user",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "apikey": self.settings.SUPABASE_KEY
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return User(
                        id=data.get("id", ""),
                        email=data.get("email", ""),
                        name=data.get("user_metadata", {}).get("name"),
                        avatar_url=data.get("user_metadata", {}).get("avatar_url"),
                        metadata=data.get("user_metadata", {})
                    )
                return None
        except Exception:
            return None
    
    async def create_user(self, email: str, password: str, name: Optional[str] = None) -> dict:
        """Create a new user (admin only)."""
        if not self.service_key:
            raise HTTPException(status_code=500, detail="Service key not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.supabase_url}/auth/v1/admin/users",
                headers={
                    "Authorization": f"Bearer {self.service_key}",
                    "apikey": self.settings.SUPABASE_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "email": email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {"name": name} if name else {}
                }
            )
            
            if response.status_code == 200:
                return response.json()
            raise HTTPException(status_code=400, detail=response.text)
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user (admin only)."""
        if not self.service_key:
            raise HTTPException(status_code=500, detail="Service key not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.supabase_url}/auth/v1/admin/users/{user_id}",
                headers={
                    "Authorization": f"Bearer {self.service_key}",
                    "apikey": self.settings.SUPABASE_KEY
                }
            )
            
            return response.status_code == 204
    
    def create_signup_url(self, redirect_to: Optional[str] = None) -> str:
        """Get the signup URL for the client."""
        redirect = f"?redirect_to={redirect_to}" if redirect_to else ""
        return f"{self.supabase_url}/auth/v1/signup{redirect}"
    
    def create_login_url(self, redirect_to: Optional[str] = None) -> str:
        """Get the login URL for the client."""
        redirect = f"?redirect_to={redirect_to}" if redirect_to else ""
        return f"{self.supabase_url}/auth/v1/login{redirect}"


# Singleton instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """Dependency to get the current authenticated user."""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    auth = get_auth_service()
    user = await auth.get_user_from_token(credentials.credentials)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Dependency to get the current user if authenticated, otherwise None."""
    if not credentials:
        return None
    
    auth = get_auth_service()
    return await auth.get_user_from_token(credentials.credentials)


def require_role(allowed_roles: list[str]):
    """Dependency factory to require specific roles."""
    async def check_role(user: User = Depends(get_current_user)) -> User:
        user_role = user.metadata.get("role", "user")
        if user_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return check_role