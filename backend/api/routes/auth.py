"""Authentication middleware and dependencies."""
from fastapi import APIRouter, Depends, HTTPException, Form, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from typing import Optional

from backend.services.auth import get_auth_service, get_current_user, User


router = APIRouter(prefix="/auth", tags=["Authentication"])


class SignUpRequest(BaseModel):
    """Sign up request model."""
    email: EmailStr
    password: str
    name: Optional[str] = None


class SignInRequest(BaseModel):
    """Sign in request model."""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Auth response model."""
    user: dict
    session: Optional[dict] = None


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignUpRequest):
    """Register a new user."""
    auth = get_auth_service()
    
    try:
        result = await auth.create_user(
            email=request.email,
            password=request.password,
            name=request.name
        )
        
        return AuthResponse(
            user={
                "id": result["id"],
                "email": result["email"],
                "name": request.name
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post("/login")
async def login(email: str = Form(), password: str = Form()):
    """
    Login endpoint that redirects to Supabase OAuth.
    For client-side auth, use the Supabase JS client directly.
    """
    auth = get_auth_service()
    login_url = auth.create_login_url()
    
    return {
        "message": "Use Supabase client for authentication",
        "login_url": login_url,
        "instructions": "Set up Supabase Auth client in frontend with the login URL"
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "avatar_url": current_user.avatar_url,
        "metadata": current_user.metadata
    }


@router.delete("/me")
async def delete_account(current_user: User = Depends(get_current_user)):
    """Delete the current user account."""
    auth = get_auth_service()
    success = await auth.delete_user(current_user.id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user")
    
    return {"message": "User deleted successfully"}


# Public endpoints that don't require auth
public_router = APIRouter(tags=["Public"])


@public_router.get("/health")
async def public_health():
    """Public health check (no auth required)."""
    return {"status": "ok"}


@public_router.get("/docs")
async def public_docs():
    """Public API documentation."""
    return {
        "message": "API documentation",
        "version": "0.1.0"
    }