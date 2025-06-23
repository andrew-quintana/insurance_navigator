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

# Database service imports
from db.services.user_service import get_user_service, UserService
from db.services.conversation_service import get_conversation_service, ConversationService
from db.services.storage_service import get_storage_service, StorageService
from db.services.db_pool import get_db_pool

# Centralized CORS configuration
from utils.cors_config import cors_config, create_preflight_response, add_cors_headers

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agent orchestration import
try:
    from graph.agent_orchestrator import AgentOrchestrator
    AGENT_ORCHESTRATOR_AVAILABLE = True
    logger.info("✅ AgentOrchestrator imported successfully")
except ImportError as e:
    logger.error(f"❌ CRITICAL: AgentOrchestrator import failed: {e}")
    AGENT_ORCHESTRATOR_AVAILABLE = False
    raise ImportError(f"AgentOrchestrator import failed: {e}")

# Custom CORS middleware
class CustomCORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware using centralized configuration."""
    
    def __init__(self, app):
        super().__init__(app)
        self.cors_config = cors_config
    
    async def dispatch(self, request: Request, call_next):
        """Process request with centralized CORS handling."""
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            return create_preflight_response(origin)
        
        try:
            start_time = time.time()
            response = await call_next(request)
            processing_time = time.time() - start_time
            
            add_cors_headers(response, origin)
            response.headers["X-Processing-Time"] = f"{processing_time:.3f}"
            
            return response
            
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            error_response = Response(
                content=json.dumps({"error": "Internal server error", "message": str(e)}),
                status_code=500,
                media_type="application/json"
            )
            add_cors_headers(error_response, origin)
            return error_response

# Initialize FastAPI app
app = FastAPI(
    title="Insurance Navigator API",
    description="Backend-orchestrated document processing with LlamaParse",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(CustomCORSMiddleware)

cors_middleware_config = cors_config.get_fastapi_cors_middleware_config()
app.add_middleware(CORSMiddleware, **cors_middleware_config)

# Pydantic models
class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: Optional[datetime] = None
    is_active: bool = True
    roles: List[str] = []

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str

class Token(BaseModel):
    access_token: str
    token_type: str

class DocumentUploadResponse(BaseModel):
    success: bool
    document_id: str
    filename: str
    status: str
    message: str
    processing_method: str

class WebhookPayload(BaseModel):
    document_id: str
    status: str
    progress: Optional[int] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# Global service instances
user_service_instance: Optional[UserService] = None
conversation_service_instance: Optional[ConversationService] = None
storage_service_instance: Optional[StorageService] = None

# Edge Function Orchestration Utilities
class EdgeFunctionOrchestrator:
    """Orchestrates Supabase Edge Function calls for document processing."""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
        self.supabase_service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not all([self.supabase_url, self.supabase_anon_key]):
            raise ValueError("Missing Supabase configuration")
    
    async def call_edge_function(self, function_name: str, method: str, payload: Dict[str, Any], user_token: str, user_id: str = None) -> Dict[str, Any]:
        """Call a Supabase Edge Function with proper authentication."""
        url = f"{self.supabase_url}/functions/v1/{function_name}"
        
        # Use service role key for edge function authentication
        headers = {
            'Authorization': f'Bearer {self.supabase_service_role_key}',
            'Content-Type': 'application/json',
            'apikey': self.supabase_anon_key
        }
        
        # Add user ID header for user context
        if user_id:
            headers['X-User-ID'] = user_id
            headers['X-User-Token'] = user_token
        
        timeout = aiohttp.ClientTimeout(total=60)  # 60 second timeout
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            if method.upper() == 'POST':
                async with session.post(url, json=payload, headers=headers) as response:
                    return await self._handle_response(response, function_name)
            elif method.upper() == 'PATCH':
                async with session.patch(url, json=payload, headers=headers) as response:
                    return await self._handle_response(response, function_name)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
    
    async def _handle_response(self, response: aiohttp.ClientResponse, function_name: str) -> Dict[str, Any]:
        """Handle edge function response with proper error handling."""
        if response.status == 200:
            result = await response.json()
            logger.info(f"✅ Edge function {function_name} succeeded")
            return result
        else:
            error_text = await response.text()
            logger.error(f"❌ Edge function {function_name} failed: {response.status} - {error_text}")
            raise HTTPException(
                status_code=response.status,
                detail=f"Edge function {function_name} failed: {error_text}"
            )
    
    async def upload_file_to_signed_url(self, signed_url: str, file_data: bytes, content_type: str) -> bool:
        """Upload file data to Supabase Storage using signed URL."""
        headers = {
            'Content-Type': content_type,
            'Content-Length': str(len(file_data))
        }
        
        timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout for large files
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.put(signed_url, data=file_data, headers=headers) as response:
                if response.status in [200, 201, 204]:
                    logger.info(f"✅ File uploaded successfully to storage")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ File upload failed: {response.status} - {error_text}")
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"File upload failed: {error_text}"
                    )

# Initialize orchestrator
edge_orchestrator = EdgeFunctionOrchestrator()

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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.0.0",
        "features": {
            "edge_function_orchestration": True,
            "llamaparse_integration": True,
            "webhook_handlers": True
        }
    }

# Authentication endpoints
@app.post("/register", response_model=Token)
async def register(request: RegisterRequest):
    """Register a new user."""
    global user_service_instance
    
    try:
        if not user_service_instance:
            user_service_instance = await get_user_service()
        
        # Check if register_user method exists
        if not hasattr(user_service_instance, 'register_user'):
            logger.error("UserService missing register_user method")
            raise HTTPException(status_code=500, detail="User service not properly configured")
        
        token = await user_service_instance.register_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        
        return Token(access_token=token, token_type="bearer")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        import traceback
        logger.error(f"Registration traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """Authenticate user and return token."""
    global user_service_instance
    
    if not user_service_instance:
        user_service_instance = await get_user_service()
    
    try:
        token = await user_service_instance.authenticate_user(
            email=request.email,
            password=request.password
        )
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        return Token(access_token=token, token_type="bearer")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information."""
    return current_user

# 🚀 NEW: Backend-Orchestrated Document Upload Endpoint
@app.post("/upload-document-backend", response_model=DocumentUploadResponse)
async def upload_document_backend(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    file: UploadFile = File(...)
):
    """
    Backend-orchestrated document upload using Supabase Edge Functions pipeline.
    
    This endpoint:
    1. Initializes upload via upload-handler edge function
    2. Uploads file to Supabase Storage using signed URL
    3. Triggers processing completion via upload-handler PATCH
    4. Ensures LlamaParse is used for PDF processing
    """
    try:
        logger.info(f"🚀 Starting backend-orchestrated upload for user {current_user.id}: {file.filename}")
        
        # Read file data
        file_data = await file.read()
        
        # Validate file size (50MB limit)
        MAX_FILE_SIZE = 50 * 1024 * 1024
        if len(file_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if len(file_data) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Get user token for edge function calls
        auth_header = request.headers.get("authorization")
        user_token = auth_header.split(" ")[1] if auth_header else None
        
        if not user_token:
            raise HTTPException(status_code=401, detail="Missing user token")
        
        # Step 1: Initialize upload via edge function
        logger.info(f"📤 Step 1: Initializing upload via edge function...")
        
        upload_init_payload = {
            "filename": file.filename,
            "contentType": file.content_type,
            "fileSize": len(file_data)
        }
        
        upload_result = await edge_orchestrator.call_edge_function(
            'upload-handler', 
            'POST', 
            upload_init_payload, 
            user_token,
            current_user.id
        )
        
        document_id = upload_result.get('documentId')
        upload_url = upload_result.get('uploadUrl')
        storage_path = upload_result.get('path')
        
        if not all([document_id, upload_url, storage_path]):
            raise HTTPException(
                status_code=500,
                detail="Upload initialization failed: missing required fields"
            )
        
        logger.info(f"✅ Step 1 complete: Document ID {document_id}")
        
        # Step 2: Upload file to Supabase Storage
        logger.info(f"📁 Step 2: Uploading file to Supabase Storage...")
        
        await edge_orchestrator.upload_file_to_signed_url(
            upload_url, 
            file_data, 
            file.content_type
        )
        
        logger.info(f"✅ Step 2 complete: File uploaded to storage")
        
        # Step 3: Trigger processing completion via edge function
        logger.info(f"🔄 Step 3: Triggering processing completion...")
        
        completion_payload = {
            "documentId": document_id,
            "path": storage_path
        }
        
        completion_result = await edge_orchestrator.call_edge_function(
            'upload-handler',
            'PATCH',
            completion_payload,
            user_token,
            current_user.id
        )
        
        logger.info(f"✅ Step 3 complete: Processing triggered")
        
        # Determine processing method
        processing_method = "llamaparse" if file.content_type == "application/pdf" else "direct"
        
        return DocumentUploadResponse(
            success=True,
            document_id=document_id,
            filename=file.filename,
            status="processing",
            message=f"Upload successful! Processing with {processing_method}. You'll receive updates via realtime notifications.",
            processing_method=processing_method
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Backend-orchestrated upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

# 🎯 NEW: Webhook Handlers for Edge Function Status Updates
@app.post("/webhooks/document-processing")
async def document_processing_webhook(
    payload: WebhookPayload,
    signature: Optional[str] = Header(None)
):
    """
    Receive status updates from edge functions about document processing.
    
    This webhook is called by edge functions to notify about:
    - Processing progress updates
    - Completion status
    - Error conditions
    """
    try:
        logger.info(f"📨 Received webhook for document {payload.document_id}: {payload.status}")
        
        # TODO: Verify webhook signature for security
        # if signature:
        #     verify_webhook_signature(payload, signature)
        
        # Update document status in database
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            await conn.execute("""
                UPDATE documents 
                SET 
                    status = $2,
                    progress_percentage = COALESCE($3, progress_percentage),
                    error_message = $4,
                    metadata = COALESCE(metadata, '{}'::jsonb) || COALESCE($5::jsonb, '{}'::jsonb),
                    updated_at = NOW()
                WHERE id = $1
            """, 
            payload.document_id,
            payload.status,
            payload.progress,
            payload.error,
            json.dumps(payload.metadata) if payload.metadata else None
            )
        
        # TODO: Send realtime update to frontend
        # await send_realtime_update(payload.document_id, payload.status, payload.progress)
        
        logger.info(f"✅ Webhook processed for document {payload.document_id}")
        
        return {"status": "received", "document_id": payload.document_id}
        
    except Exception as e:
        logger.error(f"❌ Webhook processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

# 🔧 NEW: Regulatory Document Upload Endpoint  
@app.post("/upload-regulatory-document", response_model=DocumentUploadResponse)
async def upload_regulatory_document(
    request: Request,
    file: UploadFile = File(...),
    document_title: str = Form(...),
    document_type: str = Form(default="insurance_policy"),
    source_url: Optional[str] = Form(None),
    category: str = Form(default="regulatory"),
    metadata: Optional[str] = Form(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Upload regulatory documents using the same backend-orchestrated pipeline.
    
    This ensures regulatory documents get the same LlamaParse processing
    and vectorization as user documents.
    """
    try:
        logger.info(f"🏛️ Starting regulatory document upload: {document_title}")
        
        # Create a mock request with the file for internal processing
        # Note: We can't directly call upload_document_backend because it's a FastAPI endpoint
        # Instead, we'll replicate the core logic here
        
        # Store file properties before reading (reading might affect the object)
        filename = file.filename
        content_type = file.content_type
        
        # Read file data
        file_data = await file.read()
        
        # Validate file size (50MB limit)
        MAX_FILE_SIZE = 50 * 1024 * 1024
        if len(file_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if len(file_data) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Get user token for edge function calls
        auth_header = request.headers.get("authorization")
        user_token = auth_header.split(" ")[1] if auth_header else None
        
        if not user_token:
            raise HTTPException(status_code=401, detail="Missing user token")
        
        # Step 1: Initialize upload via edge function
        logger.info(f"📤 Step 1: Initializing upload via edge function...")
        
        upload_init_payload = {
            "filename": file.filename,
            "contentType": file.content_type,
            "fileSize": len(file_data)
        }
        
        upload_result = await edge_orchestrator.call_edge_function(
            'upload-handler', 
            'POST', 
            upload_init_payload, 
            user_token,
            current_user.id
        )
        
        document_id = upload_result.get('documentId')
        upload_url = upload_result.get('uploadUrl')
        storage_path = upload_result.get('path')
        
        if not all([document_id, upload_url, storage_path]):
            raise HTTPException(
                status_code=500,
                detail="Upload initialization failed: missing required fields"
            )
        
        logger.info(f"✅ Step 1 complete: Document ID {document_id}")
        
        # Step 2: Upload file to Supabase Storage
        logger.info(f"📁 Step 2: Uploading file to Supabase Storage...")
        
        await edge_orchestrator.upload_file_to_signed_url(
            upload_url, 
            file_data, 
            file.content_type
        )
        
        logger.info(f"✅ Step 2 complete: File uploaded to storage")
        
        # Step 3: Trigger processing completion via edge function
        logger.info(f"🔄 Step 3: Triggering processing completion...")
        
        completion_payload = {
            "documentId": document_id,
            "path": storage_path
        }
        
        completion_result = await edge_orchestrator.call_edge_function(
            'upload-handler',
            'PATCH',
            completion_payload,
            user_token,
            current_user.id
        )
        
        logger.info(f"✅ Step 3 complete: Processing triggered")
        
        # Determine processing method
        processing_method = "llamaparse" if file.content_type == "application/pdf" else "direct"
        
        # Add regulatory-specific metadata
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            # Parse additional metadata if provided
            additional_metadata = {}
            if metadata:
                try:
                    additional_metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid metadata JSON provided: {metadata}")
            
            regulatory_metadata = {
                "document_title": document_title,
                "document_type": document_type,
                "source_url": source_url,
                "category": category,
                "is_regulatory": True,
                **additional_metadata
            }
            
            await conn.execute("""
                UPDATE documents 
                SET 
                    metadata = COALESCE(metadata, '{}'::jsonb) || $2::jsonb,
                    document_type = 'regulatory'
                WHERE id = $1
            """,
            document_id,
            json.dumps(regulatory_metadata)
            )
        
        logger.info(f"✅ Regulatory document uploaded: {document_title}")
        
        return DocumentUploadResponse(
            success=True,
            document_id=document_id,
            filename=file.filename,
            status="processing",
            message=f"Regulatory document '{document_title}' uploaded successfully! Processing with {processing_method}.",
            processing_method=processing_method
        )
        
    except Exception as e:
        logger.error(f"❌ Regulatory document upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Regulatory upload failed: {str(e)}"
        )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Insurance Navigator API - Backend-Orchestrated Processing",
        "version": "3.0.0",
        "features": {
            "backend_orchestrated_uploads": True,
            "llamaparse_integration": True,
            "webhook_status_updates": True,
            "user_document_uploads": True,
            "regulatory_document_uploads": True
        },
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "upload_user_document": "/upload-document-backend",
            "upload_regulatory_document": "/upload-regulatory-document",
            "webhook_processing": "/webhooks/document-processing"
        }
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global user_service_instance, conversation_service_instance, storage_service_instance
    
    logger.info("🚀 Starting Insurance Navigator API v3.0.0")
    logger.info("🔧 Backend-orchestrated processing enabled")
    logger.info("🦙 LlamaParse integration active")
    
    try:
        # Initialize services
        user_service_instance = await get_user_service()
        conversation_service_instance = await get_conversation_service()
        storage_service_instance = await get_storage_service()
        
        # Test edge function connectivity
        logger.info("🔗 Testing edge function connectivity...")
        # TODO: Add connectivity test
        
        logger.info("✅ All services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("🛑 Shutting down Insurance Navigator API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
