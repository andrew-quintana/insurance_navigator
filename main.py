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

# Database service imports
from db.services.user_service import get_user_service, UserService
from db.services.conversation_service import get_conversation_service, ConversationService
from db.services.storage_service import get_storage_service, StorageService
from db.services.document_service import DocumentService
from db.services.db_pool import get_db_pool
from db.services.document_processing_service import DocumentProcessingService
from db.services.queue_service import QueueService
from db.services.llamaparse_service import LlamaParseService
from db.services.vector_service import VectorService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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

# Add CORS middleware with environment-aware configuration
origins = [
    "https://insurance-navigator-hr7oebcu2-andrew-quintanas-projects.vercel.app",
    "https://insurance-navigator.vercel.app",
    "https://insurance-navigator-staging.vercel.app"
]

if os.getenv("ENVIRONMENT") == "development":
    origins.extend([
        "http://localhost:8080",
        "http://localhost:3000"
    ])

# Add debug logging middleware for CORS
class CORSDebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"🔍 Incoming request: {request.method} {request.url}")
        logger.info(f"📨 Headers: {dict(request.headers)}")
        
        if request.method == "OPTIONS":
            logger.info("🔄 CORS Preflight request detected")
            logger.info(f"🌐 Origin: {request.headers.get('Origin')}")
            logger.info(f"📝 Request Method: {request.headers.get('Access-Control-Request-Method')}")
            logger.info(f"📋 Request Headers: {request.headers.get('Access-Control-Request-Headers')}")
        
        response = await call_next(request)
        
        logger.info(f"📤 Response status: {response.status_code}")
        logger.info(f"📤 Response headers: {dict(response.headers)}")
        
        return response

# Add debug middleware before CORS middleware
app.add_middleware(CORSDebugMiddleware)

# Update CORS middleware with logging
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Credentials"
    ],
    max_age=3600,
    expose_headers=["Content-Length", "Content-Range"]
)

# Health check cache
_health_cache = {"result": None, "timestamp": 0}

@app.get("/health")
async def health_check():
    """Health check endpoint with caching to reduce database load."""
    global _health_cache
    current_time = time.time()
    cache_duration = 30  # seconds
    
    # Return cached result if still valid
    if _health_cache["result"] and (current_time - _health_cache["timestamp"]) < cache_duration:
        return _health_cache["result"]
    
    # Perform actual health check
    try:
        # Test database connection
        db_pool = await get_db_pool()
        if db_pool:
            try:
                async with db_pool.get_connection() as conn:  # Changed from acquire() to get_connection()
                    await conn.execute("SELECT 1")
                db_status = "healthy"
                logger.debug("✅ Health check: Database connection successful")
            except Exception as e:
                db_status = f"error: {str(e)[:50]}"
                logger.warning(f"⚠️ Health check: Database connection error: {e}")
        else:
            db_status = "unavailable"
            logger.warning("⚠️ Health check: Database pool unavailable")

        result = {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
            "version": "3.0.0",
            "services": {
                "database": db_status,
                "user_service": "available",
                "conversation_service": "available",
                "storage_service": "available",
                "agent_orchestrator": "available"
            },
            "cached": False
        }
        
        # Cache the result
        _health_cache["result"] = result
        _health_cache["timestamp"] = current_time
        
        return result
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        error_result = {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": f"error: {str(e)[:50]}",
            "version": "3.0.0",
            "services": {
                "database": "error",
                "user_service": "unknown",
                "conversation_service": "unknown",
                "storage_service": "unknown",
                "agent_orchestrator": "unknown"
            },
            "cached": False
        }
        return error_result

# Pydantic models
class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: Optional[datetime] = None
    is_active: bool = True
    roles: List[str] = []

# Global service instances
user_service_instance: Optional[UserService] = None
conversation_service_instance: Optional[ConversationService] = None
storage_service_instance: Optional[StorageService] = None

# Initialize services
storage_service: Optional[StorageService] = None
queue_service: Optional[QueueService] = None
llamaparse_service: Optional[LlamaParseService] = None
vector_service: Optional[VectorService] = None
document_processing_service: Optional[DocumentProcessingService] = None

async def get_services():
    """Initialize all required services."""
    global storage_service, queue_service, llamaparse_service, vector_service, document_processing_service
    
    if not storage_service:
        storage_service = await get_storage_service()
        
    if not queue_service:
        pool = await get_db_pool()
        queue_service = QueueService(pool)
        
    if not llamaparse_service:
        llamaparse_service = LlamaParseService(
            api_key=os.getenv("LLAMAPARSE_API_KEY")
        )
        
    if not vector_service:
        pool = await get_db_pool()
        vector_service = VectorService(
            api_key=os.getenv("OPENAI_API_KEY"),
            pool=pool
        )
        
    if not document_processing_service:
        document_processing_service = DocumentProcessingService(
            storage_service=storage_service,
            queue_service=queue_service,
            llamaparse_service=llamaparse_service,
            vector_service=vector_service
        )
        
    return {
        "storage": storage_service,
        "queue": queue_service,
        "llamaparse": llamaparse_service,
        "vector": vector_service,
        "document_processing": document_processing_service
    }

# Authentication utilities
async def get_current_user(request: Request) -> UserResponse:
    """Extract and validate user from JWT token."""
    global user_service_instance
    
    if not user_service_instance:
        user_service_instance = await get_user_service()
    
    # Get token from Authorization header
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        # Validate token and get user
        user_data = await user_service_instance.get_user_from_token(token)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return UserResponse(**user_data)
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

@app.get("/documents/{document_id}/status")
async def get_document_status(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get document processing status."""
    try:
        # Get services
        services = await get_services()
        
        # Get document record
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            doc = await conn.fetchrow("""
                SELECT * FROM documents
                WHERE id = $1 AND user_id = $2
            """, document_id, current_user.id)
            
            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Get latest job status
            latest_job = await conn.fetchrow("""
                SELECT * FROM processing_jobs
                WHERE payload->>'document_id' = $1
                ORDER BY created_at DESC
                LIMIT 1
            """, document_id)
        
            # Combine status information
            return {
                "document_id": str(doc["id"]),
                "filename": doc["original_filename"],
                "status": doc["status"],
                "progress_percentage": doc["progress_percentage"],
                "created_at": doc["created_at"].isoformat(),
                "updated_at": doc["updated_at"].isoformat(),
                "job_status": latest_job["status"] if latest_job else None,
                "job_error": latest_job["error"] if latest_job else None,
                "processing_complete": doc["status"] in ["completed", "ready"]
            }
        
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
    current_user: UserResponse = Depends(get_current_user)
):
    """Handle document upload with detailed logging."""
    logger.info(f"📄 Upload request received - File: {file.filename}, Size: {file.size if hasattr(file, 'size') else 'unknown'}, User: {current_user.email}")
    
    try:
        # Validate file size
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            logger.error(f"❌ File too large: {file_size} bytes")
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB")
            
        logger.info(f"✅ File size validated: {file_size} bytes")
        
        # Initialize services
        services = await get_services()
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Process upload
        logger.info(f"🔄 Starting document processing for {file.filename}")
        result = await services["document_processing"].process_document(
            document_id=document_id,
            file_data=contents,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            user_id=str(current_user.id),
            document_type="policy",
            metadata={"policy_id": policy_id}
        )
        logger.info(f"✅ Document processing completed: {result}")
        
        return result
        
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

# Startup event - OPTIMIZED for fast Render deployment
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup - non-blocking for faster deployment."""
    logger.info("🚀 Starting Insurance Navigator API v3.0.0 - FAST MODE")
    logger.info("🔧 Backend-orchestrated processing enabled")
    logger.info("🦙 LlamaParse integration active")
    
    # Schedule background initialization to avoid blocking startup
    asyncio.create_task(initialize_services_background())

async def initialize_services_background():
    """Initialize services in background after app starts."""
    global user_service_instance, conversation_service_instance, storage_service_instance
    
    try:
        logger.info("🔄 Background service initialization starting...")
        
        # Initialize services with faster timeouts
        user_service_instance = await get_user_service()
        conversation_service_instance = await get_conversation_service()
        storage_service_instance = await get_storage_service()
        
        logger.info("✅ All services initialized in background")
        
    except Exception as e:
        logger.error(f"⚠️ Background service initialization failed: {e}")
        # Don't crash the app, let it start and handle errors per-request

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("🛑 Shutting down Insurance Navigator API")

@app.options("/login")
async def login_preflight(request: Request):
    """Handle preflight requests for login endpoint with proper CORS headers and logging."""
    logger.info("👋 Login preflight request received")
    origin = request.headers.get("Origin")
    logger.info(f"🌐 Request Origin: {origin}")
    logger.info(f"📨 Request Headers: {dict(request.headers)}")
    
    # Log allowed origins for debugging
    logger.info(f"✅ Allowed Origins: {origins}")
    
    # Validate origin
    if origin and origin in origins:
        logger.info(f"✅ Origin {origin} is allowed")
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, X-Requested-With",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600"
        }
        logger.info(f"📤 Responding with headers: {headers}")
        return Response(status_code=200, headers=headers)
    
    logger.warning(f"❌ Origin {origin} is not allowed")
    return Response(status_code=400)

@app.post("/login")
async def login(request: Request, response: Response):
    """Login endpoint with proper CORS and error handling."""
    logger.info("🔐 Login request received")
    logger.info(f"📨 Request Headers: {dict(request.headers)}")
    
    try:
        # Get request body
        body = await request.json()
        email = body.get("email")
        logger.info(f"📧 Login attempt for email: {email}")
        
        if not email or "password" not in body:
            logger.warning("❌ Login failed: Missing email or password")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        
        # Get user service
        user_service = await get_user_service()
        
        # Authenticate user
        auth_result = await user_service.authenticate_user(email, body["password"])
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
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information."""
    try:
        # Get user service
        user_service = await get_user_service()
        
        # Get fresh user data
        user_data = await user_service.get_user_by_id(current_user.id)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
