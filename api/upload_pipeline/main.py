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
            f"Request started: {request.method} {request.url} - User-Agent: {request.headers.get('user-agent')} - Client IP: {request.client.host if request.client else 'unknown'}"
        )
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Request completed: {request.method} {request.url} - Status: {response.status_code} - Process Time: {process_time:.3f}s"
        )
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting upload pipeline API...")
    
    # Initialize database connection
    try:
        await get_database().initialize()
        logger.info("Database connection initialized successfully")
    except Exception as e:
        logger.warning(f"Database connection failed during startup: {e}")
        logger.warning("API will start but database-dependent features may not work")
    
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
        f"Unhandled exception: {request.method} {request.url}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# Test endpoint for Phase 9 validation (no authentication required)
@app.post("/test/upload", response_model=dict)
async def test_upload_endpoint(request: dict):
    """Test endpoint for Phase 9 validation without authentication."""
    try:
        # Simulate basic validation
        if not request.get("filename"):
            raise HTTPException(status_code=400, detail="Filename is required")
        
        return {
            "status": "success",
            "message": "Test upload endpoint working",
            "received_data": request,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Test endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test/jobs/{job_id}", response_model=dict)
async def test_jobs_endpoint(job_id: str):
    """Test jobs endpoint for Phase 9 validation without authentication."""
    try:
        return {
            "status": "success",
            "message": "Test jobs endpoint working",
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Test jobs endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {
            "api": "healthy",
            "database": "unknown"
        }
    }
    
    # Check database connectivity
    try:
        db = get_database()
        if await db.health_check():
            health_status["services"]["database"] = "healthy"
        else:
            health_status["services"]["database"] = "unhealthy"
            health_status["status"] = "degraded"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        health_status["services"]["database"] = "unavailable"
        health_status["status"] = "degraded"
    
    # Return 200 for degraded service (API still works)
    return health_status


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
# Force redeploy Sun Sep  7 10:38:44 PDT 2025
