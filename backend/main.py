"""Manus AI Agent OS - FastAPI Backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.core.config import get_settings
from backend.api.routes import tasks_router, sessions_router
from backend.models.schemas import HealthResponse
from backend.services import get_supabase, get_task_queue, get_ai_gateway

# Create FastAPI app
app = FastAPI(
    title="Manus AI Agent OS",
    description="Autonomous AI Agent with E2B Sandbox Execution",
    version="0.1.0"
)

# Get settings
settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "name": "Manus AI Agent OS",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Check health of all services."""
    supabase = get_supabase()
    queue = get_task_queue()
    ai = get_ai_gateway()
    
    services = {}
    
    # Check Supabase
    try:
        services["supabase"] = await supabase.health_check()
    except Exception:
        services["supabase"] = False
    
    # Check Redis
    try:
        services["redis"] = await queue.health_check()
    except Exception:
        services["redis"] = False
    
    # Check AI Gateway
    try:
        services["ai"] = len((await ai.health_check())) > 0
    except Exception:
        services["ai"] = False
    
    all_healthy = all(services.values())
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        version="0.1.0",
        services=services
    )


@app.get("/api", tags=["root"])
async def api_root():
    """API root endpoint."""
    return {
        "message": "Manus AI Agent OS API",
        "docs": "/docs",
        "health": "/health"
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "code": "INTERNAL_ERROR"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)