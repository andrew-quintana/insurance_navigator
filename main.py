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
from datetime import datetime, timedelta
import logging
import json
import time
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib
from utils.cors_config import get_cors_config, get_cors_headers
import re
import traceback
from core import initialize_system, close_system, get_database, get_agents

# Database service imports
from db.services.user_service import get_user_service, UserService
from db.services.auth_adapter import auth_adapter
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

# System initialization and shutdown handlers
@app.on_event("startup")
async def startup_event():
    """Initialize the core system on startup."""
    try:
        logger.info("Initializing Insurance Navigator system...")
        await initialize_system()
        logger.info("System initialization completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown the core system on shutdown."""
    try:
        logger.info("Shutting down Insurance Navigator system...")
        await close_system()
        logger.info("System shutdown completed")
    except Exception as e:
        logger.error(f"Error during system shutdown: {e}")

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

@app.get("/debug-auth")
async def debug_auth():
    """Debug endpoint to check auth adapter status."""
    try:
        from db.services.auth_adapter import auth_adapter
        return {
            "auth_adapter_loaded": True,
            "backend_type": auth_adapter.backend_type,
            "test_user_info": await auth_adapter.get_user_info("test_id")
        }
    except Exception as e:
        return {
            "auth_adapter_loaded": False,
            "error": str(e)
        }

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
        # Use auth adapter for token validation
        user_data = auth_adapter.validate_token(access_token)
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

# Upload Pipeline Models
class UploadRequest(BaseModel):
    filename: str = Field(..., description="Name of the file to upload")
    bytes_len: int = Field(..., description="Size of the file in bytes")
    mime: str = Field(..., description="MIME type of the file")
    sha256: str = Field(..., description="SHA256 hash of the file content")
    ocr: bool = Field(default=False, description="Whether to perform OCR on the file")

class UploadResponse(BaseModel):
    job_id: str = Field(..., description="Unique identifier for the upload job")
    document_id: str = Field(..., description="Unique identifier for the document")
    signed_url: str = Field(..., description="Signed URL for uploading the file")
    upload_expires_at: datetime = Field(..., description="When the signed URL expires")

# Upload Pipeline Database Functions
async def get_upload_pipeline_db():
    """Get database connection for upload pipeline operations."""
    import asyncpg
    from dotenv import load_dotenv
    
    load_dotenv('.env.production')
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        raise HTTPException(status_code=500, detail="Database configuration missing")
    
    return await asyncpg.connect(database_url)

async def generate_signed_url(storage_path: str, ttl_seconds: int = 3600) -> str:
    """Generate a signed URL for file upload."""
    # For now, return a mock signed URL - in production this would use Supabase storage
    return f"https://storage.supabase.co/files/{storage_path}?signed=true&ttl={ttl_seconds}"

async def create_document_record(conn, document_id: str, user_id: str, filename: str, 
                               mime: str, bytes_len: int, file_sha256: str, raw_path: str):
    """Create a document record in the upload_pipeline.documents table."""
    await conn.execute("""
        INSERT INTO upload_pipeline.documents (
            document_id, user_id, filename, mime, bytes_len, 
            file_sha256, raw_path, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
    """, document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path)

async def create_upload_job(conn, job_id: str, document_id: str, user_id: str, 
                          request: UploadRequest, raw_path: str):
    """Create an upload job in the upload_pipeline.upload_jobs table."""
    payload = {
        "user_id": user_id,
        "document_id": document_id,
        "file_sha256": request.sha256,
        "bytes_len": request.bytes_len,
        "mime": request.mime,
        "storage_path": raw_path
    }
    
    await conn.execute("""
        INSERT INTO upload_pipeline.upload_jobs (
            job_id, document_id, status, state, progress, 
            created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
    """, job_id, document_id, "uploaded", "queued", json.dumps(payload))

# New Upload Pipeline Endpoint
@app.post("/api/v2/upload", response_model=UploadResponse)
async def upload_document_v2(
    request: UploadRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload a new document for processing using the upload pipeline.
    
    This endpoint:
    1. Validates the upload request
    2. Creates a new document record
    3. Initializes a job in the queue
    4. Returns a signed URL for file upload
    """
    logger.info(f"📄 Upload pipeline request received - File: {request.filename}, Size: {request.bytes_len}, User: {current_user['email']}")
    
    try:
        # Validate file size
        if request.bytes_len > 50 * 1024 * 1024:  # 50MB limit
            logger.error(f"❌ File too large: {request.bytes_len} bytes")
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB")
            
        logger.info(f"✅ File size validated: {request.bytes_len} bytes")
        
        # Generate document and job IDs using deterministic approach
        from utils.uuid_generation import UUIDGenerator
        
        # Use actual authenticated user ID (not a random UUID)
        user_id = current_user['id']
        
        # Generate deterministic document ID based on user and content hash
        document_id = UUIDGenerator.document_uuid(user_id, request.sha256)
        
        # Job IDs can remain random for ephemeral tracking
        job_id = UUIDGenerator.job_uuid()
        
        # Generate storage path
        timestamp = int(time.time())
        file_hash = hashlib.md5(document_id.encode()).hexdigest()[:8]
        file_ext = request.filename.split('.')[-1] if '.' in request.filename else 'pdf'
        raw_path = f"files/user/{user_id}/raw/{timestamp}_{file_hash}.{file_ext}"
        
        logger.info(f"📄 Generated storage path: {raw_path}")
        
        # Connect to database
        conn = await get_upload_pipeline_db()
        
        try:
            # Create document record
            await create_document_record(
                conn, document_id, user_id, request.filename, 
                request.mime, request.bytes_len, request.sha256, raw_path
            )
            logger.info(f"✅ Document record created: {document_id}")
            
            # Create upload job
            await create_upload_job(conn, job_id, document_id, user_id, request, raw_path)
            logger.info(f"✅ Upload job created: {job_id}")
            
            # Generate signed URL
            signed_url = await generate_signed_url(raw_path, 3600)  # 1 hour TTL
            upload_expires_at = datetime.utcnow() + timedelta(seconds=3600)
            
            logger.info(f"✅ Signed URL generated: {signed_url[:50]}...")
            
            return UploadResponse(
                job_id=job_id,
                document_id=document_id,
                signed_url=signed_url,
                upload_expires_at=upload_expires_at
            )
            
        finally:
            await conn.close()
        
    except Exception as e:
        logger.error(f"❌ Upload pipeline failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Legacy endpoint for backward compatibility
@app.post("/upload-document-backend")
async def upload_document_backend(
    file: UploadFile = File(...),
    policy_id: str = Form(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Legacy upload endpoint - redirects to new upload pipeline."""
    logger.info(f"📄 Legacy upload request received - File: {file.filename}, User: {current_user['email']}")
    
    try:
        # Read file content
        contents = await file.read()
        file_size = len(contents)
        file_sha256 = hashlib.sha256(contents).hexdigest()
        
        # Create upload request
        upload_request = UploadRequest(
            filename=file.filename,
            bytes_len=file_size,
            mime=file.content_type or "application/octet-stream",
            sha256=file_sha256,
            ocr=False
        )
        
        # Call the new upload pipeline endpoint
        return await upload_document_v2(upload_request, current_user)
        
    except Exception as e:
        logger.error(f"❌ Legacy upload failed: {str(e)}")
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
        
        # Use auth adapter for authentication
        auth_result = await auth_adapter.authenticate_user(email, password)
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
@app.post("/chat")
async def chat_with_agent(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Chat endpoint for AI agent interaction with full agentic workflow integration."""
    try:
        data = await request.json()
        message = data.get("message", "")
        conversation_id = data.get("conversation_id", "")
        user_language = data.get("user_language", "auto")
        context = data.get("context", {})
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message is required"
            )
        
        # Import the chat interface
        from agents.patient_navigator.chat_interface import PatientNavigatorChatInterface, ChatMessage
        
        # Initialize chat interface (singleton pattern for efficiency)
        if not hasattr(chat_with_agent, '_chat_interface'):
            chat_with_agent._chat_interface = PatientNavigatorChatInterface()
        
        chat_interface = chat_with_agent._chat_interface
        
        # Create ChatMessage object
        # Temporary fix: Map minimal_ prefixed IDs to known UUID with documents
        # TODO: Remove this once proper UUID generation is deployed
        raw_user_id = current_user.get("id", "anonymous")
        if raw_user_id.startswith("minimal_"):
            user_id = "936551b6-b7a4-4d3d-9fe0-a491794fd66b"  # Known user with documents
        else:
            user_id = raw_user_id
            
        chat_message = ChatMessage(
            user_id=user_id,
            content=message,
            timestamp=time.time(),
            message_type="text",
            language=user_language if user_language != "auto" else "en",
            metadata={
                "conversation_id": conversation_id,
                "context": context,
                "api_request": True
            }
        )
        
        # Process message through the complete agentic workflow
        response = await chat_interface.process_message(chat_message)
        
        # Return enhanced response with metadata
        return {
            "text": response.content,
            "response": response.content,  # For backward compatibility
            "conversation_id": conversation_id or f"conv_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "processing_time": response.processing_time,
                "confidence": response.confidence,
                "agent_sources": response.agent_sources,
                "input_processing": {
                    "original_language": user_language,
                    "translation_applied": user_language != "en" and user_language != "auto"
                },
                "agent_processing": {
                    "agents_used": response.agent_sources,
                    "processing_time_ms": int(response.processing_time * 1000)
                },
                "output_formatting": {
                    "tone_applied": "empathetic",
                    "readability_level": "8th_grade",
                    "next_steps_included": "next_steps" in response.metadata
                }
            },
            "next_steps": response.metadata.get("next_steps", []),
            "sources": response.agent_sources
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        # Return graceful error response
        return {
            "text": "I apologize, but I encountered an error processing your request. Please try again in a moment.",
            "response": "I apologize, but I encountered an error processing your request. Please try again in a moment.",
            "conversation_id": conversation_id or f"conv_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "processing_time": 0.0,
                "confidence": 0.0,
                "agent_sources": ["system"],
                "error": str(e),
                "error_type": "processing_error"
            },
            "next_steps": ["Please try rephrasing your question", "Contact support if the issue persists"],
            "sources": ["system"]
        }

@app.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information."""
    try:
        # For minimal auth, return the user data from token validation directly
        # This avoids the database lookup that causes UUID errors
        # Updated: 2025-09-05 - Force deployment
        if current_user.get("id", "").startswith("minimal_"):
            return {
                "id": current_user["id"],
                "email": current_user["email"],
                "name": current_user.get("name", current_user["email"].split("@")[0]),
                "created_at": current_user.get("iat", "2025-01-01T00:00:00Z"),
                "auth_method": "minimal_auth"
            }
        
        # For other auth methods, use auth adapter
        try:
            user_data = await auth_adapter.get_user_info(current_user["id"])
            if user_data:
                return user_data
        except Exception as e:
            logger.warning(f"Auth adapter failed, falling back to token data: {e}")
        
        # Fallback to token data
        return {
            "id": current_user["id"],
            "email": current_user["email"],
            "name": current_user.get("name", current_user["email"].split("@")[0]),
            "created_at": current_user.get("iat", "2025-01-01T00:00:00Z"),
            "auth_method": "token_fallback"
        }
        
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
        
        # Use auth adapter for user creation
        auth_result = await auth_adapter.create_user(
            email=email,
            password=password,
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
        # Use auth adapter for user creation
        user_data = await auth_adapter.create_user(
            email=request.email,
            password=request.password,
            name=request.email.split("@")[0]  # Use email prefix as name if not provided
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
        # Use auth adapter for authentication
        auth_data = await auth_adapter.authenticate_user(
            email=request.email,
            password=request.password
        )
        
        if not auth_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
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
async def get_auth_user(request: Request):
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
        
        # Use auth adapter for token validation
        user_data = auth_adapter.validate_token(token)
        
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

@app.get("/health")
async def health_check():
    """
    Health check endpoint using the new core system.
    
    Returns:
        Dict containing system health status
    """
    try:
        from core import get_system_manager
        system = await get_system_manager()
        health_status = await system.health_check()
        
        return {
            "status": health_status["status"],
            "timestamp": datetime.utcnow().isoformat(),
            "services": health_status.get("services", {}),
            "version": "3.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "version": "3.0.0"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
