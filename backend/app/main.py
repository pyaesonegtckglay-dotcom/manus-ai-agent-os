"""
PSP AI Backend - FastAPI Server
Pure API backend - no Gradio
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from app.services.key_router import router as key_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="PSP AI Backend API",
    description="Manus-Class Autonomous AI Operating System - API Backend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "gemini"
    system_prompt: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048


class ChatResponse(BaseModel):
    response: str
    model: str
    usage: Optional[Dict[str, Any]] = None


class KeyStatus(BaseModel):
    provider: str
    status: str
    available: int
    total: int
    healthy: int
    cooldown: int
    dead: int


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "psp-ai-backend"}


# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "PSP AI Backend",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "/api/chat",
            "chat-stream": "/api/chat/stream",
            "models": "/api/models",
            "keys-status": "/api/keys/status",
            "health": "/health"
        }
    }


# Chat endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a chat message and get a response"""
    try:
        # Get available key for the provider
        api_key = await key_router.get_key_with_fallback(request.model)
        
        if not api_key:
            raise HTTPException(
                status_code=503,
                detail=f"No available API keys for provider: {request.model}"
            )
        
        # Call the LLM API based on provider
        if request.model == "gemini":
            response = await call_gemini(api_key.key, request)
        elif request.model == "sambanova":
            response = await call_sambanova(api_key.key, request)
        elif request.model == "openrouter":
            response = await call_openrouter(api_key.key, request)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown model: {request.model}")
        
        # Report success
        key_router.report_success(request.model, api_key.key)
        
        return ChatResponse(
            response=response["text"],
            model=request.model,
            usage=response.get("usage")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        if api_key:
            key_router.report_error(request.model, api_key.key, str(e))
        raise HTTPException(status_code=500, detail=str(e))


async def call_gemini(api_key: str, request: ChatRequest) -> Dict[str, Any]:
    """Call Gemini API"""
    import httpx
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    
    contents = [{"parts": [{"text": request.message}]}]
    if request.system_prompt:
        contents = [{"parts": [{"text": request.system_prompt}, {"text": request.message}]}]
    
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, json={
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens
            }
        })
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()
        return {
            "text": data["candidates"][0]["content"]["parts"][0]["text"],
            "usage": data.get("usageMetadata", {})
        }


async def call_sambanova(api_key: str, request: ChatRequest) -> Dict[str, Any]:
    """Call SambaNova API"""
    import httpx
    
    url = "https://api.sambanova.ai/api/v1/chat/completions"
    
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }, json={
            "model": "Meta-Llama-3-8B-Instruct",
            "messages": [
                {"role": "system", "content": request.system_prompt or "You are a helpful AI assistant."},
                {"role": "user", "content": request.message}
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        })
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()
        return {
            "text": data["choices"][0]["message"]["content"],
            "usage": data.get("usage", {})
        }


async def call_openrouter(api_key: str, request: ChatRequest) -> Dict[str, Any]:
    """Call OpenRouter API"""
    import httpx
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }, json={
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": request.system_prompt or "You are a helpful AI assistant."},
                {"role": "user", "content": request.message}
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        })
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()
        return {
            "text": data["choices"][0]["message"]["content"],
            "usage": data.get("usage", {})
        }


# Models endpoint
@app.get("/api/models")
async def list_models():
    """List available models"""
    return {
        "models": [
            {"id": "gemini", "name": "Google Gemini", "provider": "google"},
            {"id": "sambanova", "name": "SambaNova", "provider": "sambanova"},
            {"id": "openrouter", "name": "OpenRouter", "provider": "openrouter"}
        ]
    }


# Key status endpoint
@app.get("/api/keys/status")
async def keys_status():
    """Get API key routing status"""
    stats = key_router.get_stats()
    return {"providers": stats}


# Run server
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
