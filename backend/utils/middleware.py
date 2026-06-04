"""Error handling, logging, and middleware."""
import logging
import time
import traceback
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import json
import sys

from backend.core.config import get_settings


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("manus")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(f"→ {request.method} {request.url.path}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log response
            duration = time.time() - start_time
            logger.info(
                f"← {request.method} {request.url.path} "
                f"[{response.status_code}] {duration:.3f}s"
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"✗ {request.method} {request.url.path} "
                f"[ERROR] {duration:.3f}s - {str(e)}"
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app: ASGIApp, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        
        # Clean old requests
        now = time.time()
        if client_ip in self.requests:
            self.requests[client_ip] = [
                t for t in self.requests[client_ip]
                if now - t < self.window_seconds
            ]
        else:
            self.requests[client_ip] = []
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "retry_after": self.window_seconds
                },
                headers={"Retry-After": str(self.window_seconds)}
            )
        
        # Record request
        self.requests[client_ip].append(now)
        
        return await call_next(request)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors and formatting responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            return await self.handle_error(request, e)
    
    async def handle_error(self, request: Request, exc: Exception) -> JSONResponse:
        # Log the error
        logger.error(f"Error processing {request.method} {request.url.path}: {exc}")
        logger.error(traceback.format_exc())
        
        # Handle specific error types
        if isinstance(exc, ValueError):
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Bad Request",
                    "detail": str(exc),
                    "code": "VALIDATION_ERROR"
                }
            )
        
        if isinstance(exc, PermissionError):
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Forbidden",
                    "detail": str(exc),
                    "code": "PERMISSION_DENIED"
                }
            )
        
        # Default to 500
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred" if not settings.DEBUG else str(exc),
                "code": "INTERNAL_ERROR"
            },
            headers={"X-Error-Code": "INTERNAL_ERROR"}
        )


class CircuitBreaker:
    """Circuit breaker for external services."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker."""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.failures >= self.failure_threshold:
                self.state = "open"
                logger.warning(f"Circuit breaker opened after {self.failures} failures")
            
            raise e
    
    def reset(self):
        """Reset the circuit breaker."""
        self.failures = 0
        self.state = "closed"


# Global circuit breakers
ai_gateway_circuit = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
e2b_circuit = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
redis_circuit = CircuitBreaker(failure_threshold=3, recovery_timeout=30)


def setup_middleware(app):
    """Configure all middleware for the application."""
    settings = get_settings()
    
    # Add logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Add rate limiting in production
    if not settings.DEBUG:
        app.add_middleware(
            RateLimitMiddleware,
            max_requests=100,
            window_seconds=60
        )
    
    # Add error handling
    app.add_middleware(ErrorHandlerMiddleware)


def log_error(component: str, error: Exception, context: dict = None):
    """Log an error with context."""
    logger.error(f"[{component}] {type(error).__name__}: {str(error)}")
    if context:
        logger.error(f"Context: {json.dumps(context)}")
    logger.error(traceback.format_exc())


def log_info(component: str, message: str, context: dict = None):
    """Log an info message with context."""
    logger.info(f"[{component}] {message}")
    if context:
        logger.info(f"Context: {json.dumps(context)}")