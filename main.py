#!/usr/bin/env python3
"""
FastAPI Insurance Navigator API - Backend-Orchestrated Upload Pipeline

Key Features:
- Backend orchestrates Supabase Edge Function pipeline
- Ensures LlamaParse processing for PDFs
- Webhook handlers for edge function status updates
- Reliable user and regulatory document uploads
"""

import os
import sys
import uuid
import aiohttp
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Request, status, UploadFile, File, Form, Response, Body, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import json
import time
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib
from utils.cors_config import get_cors_config, get_cors_headers
import re
import psycopg2
import traceback
from config.database import db_pool

# Database service imports
from db.services.user_service import get_user_service, UserService
from db.services.improved_minimal_auth_service import improved_minimal_auth_service as simple_auth_service
from db.services.conversation_service import get_conversation_service, ConversationService
from db.services.storage_service import get_storage_service, StorageService
from db.services.document_service import DocumentService

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Insurance Navigator API",
    description="Backend-orchestrated document processing with LlamaParse",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Custom error handler middleware
class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            logger.warning(f"HTTP Exception: {str(e)} - Path: {request.url.path}")
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}\n{traceback.format_exc()}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )

# Request logging middleware with performance tracking
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Log request details
        logger.info(f"Request {request_id} started - Method: {request.method} Path: {request.url.path}")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response details
            status_code = response.status_code
            logger.info(
                f"Request {request_id} completed - "
                f"Status: {status_code} - "
                f"Time: {process_time:.2f}s"
            )
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request {request_id} failed - "
                f"Error: {str(e)} - "
                f"Time: {process_time:.2f}s"
            )
            raise

# Add middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    **get_cors_config()
)

# Health check cache with type hints
_health_cache: Dict[str, Any] = {"result": None, "timestamp": 0}

@app.head("/")
async def root_head():
    """Root endpoint for HEAD requests."""
    return Response(status_code=200)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Insurance Navigator API v3.0.0"}

@app.head("/health")
async def health_check_head():
    """Quick health check for HEAD requests."""
    return Response(status_code=200)

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint with caching to reduce database load."""
    global _health_cache
    current_time = time.time()
    cache_duration = 30  # seconds
    
    # Return cached result if still valid
    if _health_cache["result"] and (current_time - _health_cache["timestamp"]) < cache_duration:
        return _health_cache["result"]
    
    # For HEAD requests, return immediately
    if request.method == "HEAD":
        return Response(status_code=200)
    
    # Perform actual health check
    try:
        # Test database connection
        from config.database import db_pool
        if db_pool:
            try:
                # Test if pool is initialized
                client = await db_pool.get_client()
                if client:
                    db_status = "healthy"
                else:
                    db_status = "not_initialized"
                    logger.warning("⚠️ Database pool not initialized")
            except Exception as e:
                db_status = f"error: {str(e)[:50]}"
                logger.warning(f"⚠️ Database connection error: {e}")
        else:
            db_status = "unavailable"
            logger.warning("⚠️ Database client unavailable")

        # Check service dependencies
        services_status = {
            "database": db_status,
            "supabase_auth": "healthy" if os.getenv("SUPABASE_URL") else "not_configured",
            "llamaparse": "healthy" if os.getenv("LLAMAPARSE_API_KEY") else "not_configured",
            "openai": "healthy" if os.getenv("OPENAI_API_KEY") else "not_configured"
        }

        result = {
            "status": "healthy" if all(s == "healthy" for s in services_status.values()) else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": services_status,
            "version": "3.0.0"
        }
        
        # Cache the result
        _health_cache["result"] = result
        _health_cache["timestamp"] = current_time
        
        return result
    except Exception as e:
        logger.error(f"Health check failed: {e}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# Global service instances
user_service_instance = None
conversation_service_instance = None
storage_service_instance = None

# Initialize services
storage_service: Optional[StorageService] = None

# Authentication utilities
async def get_current_user(request: Request) -> Dict[str, Any]:
    """Extract and validate user from JWT token."""
    # Get tokens from Authorization header
    auth_header = request.headers.get("authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    access_token = auth_header.split(" ")[1]
    
    try:
        # Use improved minimal auth service for token validation
        user_data = simple_auth_service.validate_token(access_token)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@app.get("/documents/{document_id}/status")
async def get_document_status(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get simplified document status."""
    try:
        # Get document service
        doc_service = DocumentService()
        
        # Get document status
        status = await doc_service.get_document_status(document_id, str(current_user["id"]))
        
        if not status:
                raise HTTPException(status_code=404, detail="Document not found")
            
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )

# Document upload endpoint
@app.post("/upload-document-backend")
async def upload_document_backend(
    file: UploadFile = File(...),
    policy_id: str = Form(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Handle document upload with simplified processing."""
    logger.info(f"📄 Upload request received - File: {file.filename}, Size: {file.size if hasattr(file, 'size') else 'unknown'}, User: {current_user['email']}")
    
    try:
        # Validate file size
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            logger.error(f"❌ File too large: {file_size} bytes")
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB")
            
        logger.info(f"✅ File size validated: {file_size} bytes")
        
        # Get storage service
        storage_service = await get_storage_service()
        
        # Upload document
        logger.info(f"🔄 Starting document upload for {file.filename}")
        upload_result = await storage_service.upload_document(
            user_id=str(current_user["id"]),
            file_content=contents,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream"
        )
        
        logger.info(f"✅ Document upload completed: {upload_result}")
        
        # Call upload-handler Edge Function
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_service_key:
            raise HTTPException(status_code=500, detail="Missing Supabase configuration")
            
        # Extract project ref from Supabase URL (format: https://[project-ref].supabase.co)
        try:
            project_ref = supabase_url.replace('https://', '').split('.')[0]
            upload_handler_url = f"https://{project_ref}.functions.supabase.co/upload-handler"
            logger.info(f"🔗 Constructed upload-handler URL: {upload_handler_url}")
        except Exception as e:
            logger.error(f"❌ Failed to construct upload-handler URL: {e}")
            raise HTTPException(status_code=500, detail="Invalid Supabase configuration")
        
        logger.info(f"🔄 Calling upload-handler function for document {upload_result['document_id']}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                upload_handler_url,
                headers={
                    'Authorization': f'Bearer {supabase_service_key}',
                    'Content-Type': 'application/json',
                    'X-User-ID': str(current_user["id"])
                },
                json={
                    'userId': str(current_user["id"]),
                    'filename': file.filename,
                    'fileSize': file_size,
                    'contentType': file.content_type or "application/octet-stream",
                    'storagePath': upload_result['path']
                }
            ) as response:
                response_data = await response.json()
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Upload-handler call failed: {response.status} - {error_text}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Document upload succeeded but processing failed: {error_text}"
                    )
                
                if not response_data.get('success'):
                    logger.error(f"❌ Upload-handler returned error: {response_data.get('error')}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Document processing failed: {response_data.get('error')}"
                    )
                
                logger.info(f"✅ Upload-handler started processing: {response_data}")
                
        return {
            "success": True,
            "document_id": upload_result["document_id"],
            "filename": file.filename,
            "status": "processing",
            "chunks_processed": 0,
            "total_chunks": 1
        }
        
    except Exception as e:
        logger.error(f"❌ Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def notify_document_status(
    user_id: str,
    document_id: str,
    status: str,
    message: str
):
    """Send document status notification via WebSocket."""
    try:
        # Get Supabase client
        supabase = await get_supabase_client()
        
        # Send realtime notification
        await supabase.realtime.send({
            "type": "broadcast",
            "event": "document_status",
            "topic": f"user_documents:{user_id}",
            "payload": {
                "document_id": document_id,
                "status": status,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to send WebSocket notification: {e}")
        # Don't re-raise the exception as this is a non-critical operation

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application services"""
    logger.info("🚀 Starting Insurance Navigator API v3.0.0")
    logger.info("🔧 Backend-orchestrated processing enabled")
    logger.info("🔄 Service initialization starting...")
    
    try:
        # Initialize database pool
        await db_pool.initialize()
        logger.info("✅ Database pool initialized")
        
        # Initialize other services
        user_service_instance = await get_user_service()
        logger.info("✅ User service initialized")
        
        conversation_service_instance = await get_conversation_service()
        logger.info("✅ Conversation service initialized")
        
        storage_service_instance = await get_storage_service()
        logger.info("✅ Storage service initialized")
        
        # Verify environment variables
        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
            "LLAMAPARSE_API_KEY",
            "OPENAI_API_KEY"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.warning(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
        
        logger.info("✅ Core services initialized")
        
    except Exception as e:
        logger.error(f"⚠️ Service initialization failed: {str(e)}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup application resources"""
    logger.info("🛑 Shutting down Insurance Navigator API")
    try:
        # Cleanup database pool
        await db_pool.cleanup()
        logger.info("✅ Database pool cleaned up")
        
        # Cleanup other services
        # ... existing cleanup code ...
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

@app.post("/login")
async def login(request: Request, response: Response):
    """Login endpoint with validation and proper error handling."""
    try:
        # Get request body
        body = await request.json()
        email = body.get("email", "").strip()
        password = body.get("password", "")
        
        if not email or not password:
            logger.warning("Login attempt failed: Missing email or password")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        
        # Use improved authentication service with validation
        auth_result = await simple_auth_service.authenticate_user_minimal(email, password)
        if not auth_result:
            logger.warning(f"❌ Authentication failed for user: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        logger.info(f"✅ User logged in successfully: {email}")
        return {
            "access_token": auth_result["access_token"],
            "token_type": "bearer",
            "user": auth_result["user"]
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Login failed - Invalid JSON: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

# Add /me endpoint for session validation
@app.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information."""
    try:
        # Get user service
        user_service = await get_user_service()
        
        # Get fresh user data
        user_data = await user_service.get_user_by_id(current_user["id"])
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

# Add OPTIONS route handler for explicit preflight handling
@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request, rest_of_path: str):
    """Handle preflight requests explicitly"""
    try:
        origin = request.headers.get("Origin")
        if not origin:
            return Response(status_code=400, content="Origin header is required")
            
        # Return CORS headers for the specific origin
        headers = get_cors_headers(origin)
        if not headers:
            return Response(status_code=400, content="Origin not allowed")
            
        return Response(status_code=200, headers=headers)
    except Exception as e:
        logger.error(f"Error in preflight handler: {str(e)}")
        return Response(status_code=500, content="Internal server error")

# Add middleware to ensure CORS headers on all responses
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    """Add CORS headers to all responses"""
    try:
        response = await call_next(request)
        
        # Add CORS headers based on origin
        origin = request.headers.get("Origin")
        if origin:
            headers = get_cors_headers(origin)
            for key, value in headers.items():
                response.headers[key] = value
        
        return response
    except Exception as e:
        logger.error(f"Error in CORS middleware: {str(e)}")
        return Response(status_code=500, content="Internal server error")

@app.post("/register", response_model=Dict[str, Any])
async def register(request: Dict[str, Any]):
    """Register a new user with validation and duplicate checking."""
    try:
        # Extract and validate required fields
        email = request.get("email", "").strip()
        password = request.get("password", "")
        name = request.get("name", "").strip() or request.get("full_name", "").strip()
        
        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        
        logger.info(f"🚀 Starting registration for: {email}")
        
        # Use improved authentication service with validation
        auth_result = await simple_auth_service.create_user_minimal(
            email=email,
            password=password,
            consent_version="1.0",
            consent_timestamp=datetime.now().isoformat(),
            name=name or email.split("@")[0]
        )
        
        logger.info(f"✅ User registered successfully: {email}")
        return auth_result
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Registration validation failed for {request.get('email', 'unknown')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Registration error for {request.get('email', 'unknown')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )

@app.get("/api/v1/status")
async def detailed_status():
    """Detailed status check including database connectivity"""
    try:
        # Check database connection
        conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"))
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "database": db_status,
        "environment": os.getenv("NODE_ENV", "development")
    }

# Authentication models
class SignupRequest(BaseModel):
    """Request model for user signup."""
    email: str
    password: str
    consent_version: str
    consent_timestamp: str

class LoginRequest(BaseModel):
    """Request model for user login."""
    email: str
    password: str

@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):
    """
    Sign up a new user with HIPAA consent tracking.
    
    Args:
        request: SignupRequest containing user data
        
    Returns:
        Dict containing user data and access token
    """
    try:
        # Get user service
        user_service = await get_user_service()
        
        # Create user
        user_data = await user_service.create_user(
            email=request.email,
            password=request.password,
            consent_version=request.consent_version,
            consent_timestamp=request.consent_timestamp
        )
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/auth/login")
async def login(request: LoginRequest):
    """
    Authenticate a user and return session data.
    
    Args:
        request: LoginRequest containing user credentials
        
    Returns:
        Dict containing user data and session info
    """
    try:
        # Get user service
        user_service = await get_user_service()
        
        # Authenticate user
        auth_data = await user_service.authenticate_user(
            email=request.email,
            password=request.password
        )
        
        return auth_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@app.get("/auth/user")
async def get_current_user(request: Request):
    """
    Get current user data from auth token.
    
    Args:
        request: Request object containing authorization header
        
    Returns:
        Dict containing user data
    """
    try:
        # Get authorization header
        authorization = request.headers.get("Authorization")
        
        # Validate token
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header"
            )
            
        token = authorization.split(" ")[1]
        
        # Get user service
        user_service = await get_user_service()
        
        # Get user data
        user_data = await user_service.get_user_from_token(token)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
