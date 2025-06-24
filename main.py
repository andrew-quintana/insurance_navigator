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

# Centralized CORS configuration
from utils.cors_config import cors_config, create_preflight_response, add_cors_headers

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

# Add CORS middleware with direct configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://insurance-navigator.vercel.app",
        "https://insurance-navigator-staging.vercel.app",
        "https://insurance-navigator-dev.vercel.app",
        "***REMOVED***",
        "https://insurance-navigator-api-staging.onrender.com"
    ],
    allow_origin_regex=r"https://insurance-navigator-[a-z0-9\-]+-andrew-quintanas-projects\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "Content-Length",
        "Content-Range",
        "X-Total-Count",
        "X-Processing-Status"
    ],
    max_age=600
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
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Upload and process a document."""
    start_time = time.time()
    try:
        # Read file data
        file_data = await file.read()
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Get document service
        doc_service = DocumentService()
        
        # Create document record
        document = await doc_service.create_document(
            user_id=current_user["id"],
            filename=file.filename,
            file_size=len(file_data),
            content_type=file.content_type or "application/octet-stream",
            file_hash=hashlib.sha256(file_data).hexdigest(),
            storage_path=f"documents/{current_user['id']}/{document_id}/{file.filename}",
            document_type="user_uploaded",
            metadata={
                "upload_timestamp": datetime.utcnow().isoformat(),
                "uploader_email": current_user["email"],
                "original_filename": file.filename
            }
        )
        
        # Get storage service
        storage_service = await get_storage_service()
        
        # Upload to storage
        storage_result = await storage_service.upload_document(
            file_data=file_data,
            filename=file.filename,
            user_id=current_user["id"],
            document_type="user_uploaded",
            metadata={
                "document_id": document["document_id"],
                "uploader_email": current_user["email"]
            }
        )
        
        if not storage_result:
            raise Exception("Failed to upload file to storage")
        
        # Start processing
        processing_service = DocumentProcessingService()
        process_result = await processing_service.process_document(
            document_id=document["document_id"],
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            user_id=current_user["id"]
        )
        
        # Send WebSocket notification about upload success
        try:
            await notify_document_status(
                user_id=current_user["id"],
                document_id=document["document_id"],
                status="uploaded",
                message="Document uploaded successfully and processing started"
            )
        except Exception as ws_error:
            logger.warning(f"Failed to send WebSocket notification: {ws_error}")
        
        return {
            "status": "success",
            "document_id": document["document_id"],
            "filename": file.filename,
            "storage_path": storage_result["file_path"],
            "processing_status": process_result["status"] if process_result else "queued",
            "message": "Document uploaded and processing started"
        }
        
    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        logger.error(f"Error details: type={type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Send WebSocket notification about upload failure
        try:
            if 'document_id' in locals():
                await notify_document_status(
                    user_id=current_user["id"],
                    document_id=document_id,
                    status="failed",
                    message=f"Upload failed: {str(e)[:100]}"
                )
        except Exception as ws_error:
            logger.warning(f"Failed to send WebSocket notification: {ws_error}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred during upload. Please try again.",
                "processing_time": f"{time.time() - start_time:.2f}s"
            }
        )

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

# Login endpoint with CORS support
@app.post("/login")
async def login(request: Request, response: Response):
    """Login endpoint with proper CORS handling."""
    try:
        # Get request body
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        
        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        
        # Get user service
        user_service = await get_user_service()
        
        # Authenticate user
        auth_result = await user_service.authenticate_user(email, password)
        if not auth_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        return {
            "access_token": auth_result["access_token"],
            "token_type": "bearer",
            "user": auth_result["user"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
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
