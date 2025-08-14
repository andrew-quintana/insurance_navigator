"""
Main FastAPI application for the insurance document ingestion pipeline.
Phase 2: Core API endpoints and job queue system.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
import time
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

from .config import get_config
from .database import get_database
from .auth import get_current_user, User
from .rate_limiter import RateLimiter
from .endpoints.upload import router as upload_router
from .endpoints.jobs import router as jobs_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests."""
    
    async def dispatch(self, request: StarletteRequest, call_next):
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)
        
        # Get user ID from JWT token if available
        user_id = None
        try:
            user = await get_current_user(request)
            user_id = str(user.user_id)
        except:
            pass
        
        # Check rate limits
        if not rate_limiter.check_rate_limit(request.url.path, user_id):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Rate limit exceeded. Please try again later.",
                    "retry_after": rate_limiter.get_retry_after(request.url.path, user_id)
                }
            )
        
        response = await call_next(request)
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""
    
    async def dispatch(self, request: StarletteRequest, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            user_agent=request.headers.get("user-agent"),
            client_ip=request.client.host if request.client else None
        )
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time
        )
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting upload pipeline API...")
    
    # Initialize database connection
    await get_database().initialize()
    
    # Initialize rate limiter
    rate_limiter.initialize()
    
    logger.info("Upload pipeline API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down upload pipeline API...")
    
    # Close database connections
    await get_database().close()
    
    logger.info("Upload pipeline API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Accessa Insurance Document Ingestion Pipeline",
    description="API for uploading and processing insurance documents",
    version="2.0.0",
    docs_url="/docs" if get_config().environment == "development" else None,
    redoc_url="/redoc" if get_config().environment == "development" else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_config().cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=get_config().allowed_hosts)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(
        "Unhandled exception",
        exc_info=True,
        method=request.method,
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Check database connectivity
        db = get_database()
        await db.health_check()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error("Health check failed", exc_info=True)
        raise HTTPException(status_code=503, detail="Service unhealthy")


# Include API routers
app.include_router(upload_router, prefix="/api/v2", tags=["upload"])
app.include_router(jobs_router, prefix="/api/v2", tags=["jobs"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=get_config().environment == "development"
    )
