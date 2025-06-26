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

# Database service imports
from db.services.user_service import get_user_service, UserService
from db.services.conversation_service import get_conversation_service, ConversationService
from db.services.storage_service import get_storage_service, StorageService
from db.services.document_service import DocumentService
from db.services.db_pool import get_db_pool

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
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

# Debug middleware for CORS
class CORSDebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only log CORS issues
        origin = request.headers.get("origin")
        if origin:
            cors_config = get_cors_config()
            is_allowed = False
            
            # Check exact matches
            if origin in cors_config["allow_origins"]:
                is_allowed = True
            else:
                # Check wildcards
                for allowed_origin in cors_config["allow_origins"]:
                    if '*' in allowed_origin:
                        pattern = allowed_origin.replace('*', '.*').replace('.', '\.')
                        if re.match(pattern, origin):
                            is_allowed = True
                            break
                
                # Check regex
                if not is_allowed and "allow_origin_regex" in cors_config:
                    pattern = re.compile(cors_config["allow_origin_regex"])
                    if pattern.match(origin):
                        is_allowed = True
            
            if not is_allowed:
                logger.warning(f"❌ CORS: Origin not allowed: {origin}")
        
        response = await call_next(request)
        return response

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for debugging."""
    start_time = time.time()
    
    # Only log the path and method
    logger.info(f"➡️ {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Only log errors or slow responses
        if response.status_code >= 400 or process_time > 1.0:
            logger.info(f"⬅️ {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.2f}s")
        
        return response
    except Exception as e:
        logger.error(f"❌ Request failed: {str(e)}")
        raise

# Health check cache
_health_cache = {"result": None, "timestamp": 0}

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
        db_pool = await get_db_pool()
        if db_pool:
            try:
                async with db_pool.get_connection() as conn:
                    await conn.execute("SELECT 1")
                db_status = "healthy"
            except Exception as e:
                db_status = f"error: {str(e)[:50]}"
                logger.warning(f"⚠️ Database connection error: {e}")
        else:
            db_status = "unavailable"
            logger.warning("⚠️ Database pool unavailable")

        result = {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
            "version": "3.0.0"
        }
        
        # Cache the result
        _health_cache["result"] = result
        _health_cache["timestamp"] = current_time
        
        return result
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# Pydantic models
class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: Optional[datetime] = None
    is_active: bool = True
    roles: List[str] = []

# Global service instances
user_service_instance = None
conversation_service_instance = None
storage_service_instance = None

# Initialize services
storage_service: Optional[StorageService] = None

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
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@app.get("/documents/{document_id}/status")
async def get_document_status(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get simplified document status."""
    try:
        # Get document service
        doc_service = DocumentService()
        
        # Get document status
        status = await doc_service.get_document_status(document_id, str(current_user.id))
        
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
    current_user: UserResponse = Depends(get_current_user)
):
    """Handle document upload with simplified processing."""
    logger.info(f"📄 Upload request received - File: {file.filename}, Size: {file.size if hasattr(file, 'size') else 'unknown'}, User: {current_user.email}")
    
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
            user_id=str(current_user.id),
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
                    'X-User-ID': str(current_user.id)
                },
                json={
                    'userId': str(current_user.id),
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
    """Initialize services on startup."""
    logger.info("🚀 Starting Insurance Navigator API v3.0.0")
    logger.info("🔧 Backend-orchestrated processing enabled")
    
    global user_service_instance, conversation_service_instance, storage_service_instance
    
    try:
        logger.info("🔄 Service initialization starting...")
        
        # Initialize core services synchronously to ensure they're ready
        user_service_instance = await get_user_service()
        conversation_service_instance = await get_conversation_service()
        storage_service_instance = await get_storage_service()
        
        logger.info("✅ Core services initialized")
        
    except Exception as e:
        logger.error(f"⚠️ Service initialization failed: {e}")
        # Re-raise to prevent app from starting in bad state
        raise

async def initialize_background_services():
    """Initialize non-critical services in background."""
    try:
        # Initialize additional services here
        logger.info("🔄 Background service initialization complete")
    except Exception as e:
        logger.error(f"⚠️ Background service initialization failed: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("🛑 Shutting down Insurance Navigator API")

@app.post("/login")
async def login(request: Request, response: Response):
    """Login endpoint with proper error handling."""
    try:
        # Get request body
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        
        if not email or not password:
            logger.warning("Login attempt failed: Missing email or password")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        
        # Get user service
        user_service = await get_user_service()
        
        # Authenticate user
        auth_result = await user_service.authenticate_user(email, password)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
