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

# Centralized CORS configuration
from utils.cors_config import cors_config, create_preflight_response, add_cors_headers

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agent orchestration import - LAZY LOADED for faster startup
AGENT_ORCHESTRATOR_AVAILABLE = False
_agent_orchestrator = None

def get_agent_orchestrator():
    """Lazy load AgentOrchestrator only when needed."""
    global _agent_orchestrator, AGENT_ORCHESTRATOR_AVAILABLE
    if _agent_orchestrator is None and not AGENT_ORCHESTRATOR_AVAILABLE:
try:
    from graph.agent_orchestrator import AgentOrchestrator
            _agent_orchestrator = AgentOrchestrator()
    AGENT_ORCHESTRATOR_AVAILABLE = True
            logger.info("✅ AgentOrchestrator loaded on-demand")
except ImportError as e:
            logger.error(f"❌ AgentOrchestrator import failed: {e}")
    AGENT_ORCHESTRATOR_AVAILABLE = False
            return None
    return _agent_orchestrator

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
        
        if not all([self.supabase_url, self.supabase_anon_key, self.supabase_service_role_key]):
            raise ValueError("Missing Supabase configuration - need URL, anon key, and service role key")
    
    async def call_edge_function(self, function_name: str, method: str, payload: Dict[str, Any], user_token: str, user_id: str = None) -> Dict[str, Any]:
        """Call a Supabase Edge Function with proper authentication."""
        url = f"{self.supabase_url}/functions/v1/{function_name}"
        
        # ✅ CRITICAL FIX: Use service role key for backend-to-edge-function calls
        # This ensures edge functions have the necessary permissions
        headers = {
            'Authorization': f'Bearer {self.supabase_service_role_key}',
            'Content-Type': 'application/json',
            'apikey': self.supabase_anon_key,
            'X-Client-Info': 'insurance-navigator/3.0.0'
        }
        
        # Add user context headers for edge function user identification
        if user_id:
            headers['X-User-ID'] = user_id
            headers['X-User-Token'] = user_token
            headers['X-User-Context'] = 'backend-orchestrated'
        
        # Add request ID for tracing
        headers['X-Request-ID'] = str(uuid.uuid4())
        
        timeout = aiohttp.ClientTimeout(total=120)  # Increased timeout for Render
        
        logger.info(f"🔗 Calling edge function {function_name} with method {method}")
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
            if method.upper() == 'POST':
                async with session.post(url, json=payload, headers=headers) as response:
                    return await self._handle_response(response, function_name)
            elif method.upper() == 'PATCH':
                async with session.patch(url, json=payload, headers=headers) as response:
                    return await self._handle_response(response, function_name)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            except asyncio.TimeoutError:
                logger.error(f"❌ Edge function {function_name} timeout (120s)")
                raise HTTPException(
                    status_code=504,
                    detail=f"Edge function {function_name} timeout - processing may continue in background"
                )
            except aiohttp.ClientError as e:
                logger.error(f"❌ Edge function {function_name} connection error: {e}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Edge function {function_name} connection failed"
                )
    
    async def _handle_response(self, response: aiohttp.ClientResponse, function_name: str) -> Dict[str, Any]:
        """Handle edge function response with comprehensive error handling."""
        try:
            response_text = await response.text()
            
        if response.status == 200:
                try:
                    result = json.loads(response_text) if response_text else {}
            logger.info(f"✅ Edge function {function_name} succeeded")
            return result
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Edge function {function_name} returned non-JSON response")
                    return {"success": True, "message": response_text}
        else:
                # Enhanced error logging for debugging
                logger.error(f"❌ Edge function {function_name} failed: {response.status}")
                logger.error(f"Response body: {response_text[:500]}...")
                
                # Parse error details if available
                error_details = {"status": response.status, "raw_response": response_text}
                try:
                    error_json = json.loads(response_text)
                    error_details.update(error_json)
                except json.JSONDecodeError:
                    pass
                
                # Create user-friendly error messages
                if response.status == 401:
                    error_message = "Authentication failed with edge function"
                elif response.status == 403:
                    error_message = "Access denied to edge function"
                elif response.status == 404:
                    error_message = f"Edge function {function_name} not found"
                elif response.status == 500:
                    error_message = f"Edge function {function_name} internal error"
                elif response.status == 504:
                    error_message = f"Edge function {function_name} timeout"
                else:
                    error_message = f"Edge function {function_name} failed with status {response.status}"
                
            raise HTTPException(
                status_code=response.status,
                    detail={"error": error_message, "details": error_details}
                )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"❌ Edge function {function_name} response handling error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Edge function {function_name} response handling failed"
            )
    
    async def upload_file_to_signed_url(self, signed_url: str, file_data: bytes, content_type: str) -> bool:
        """Upload file data to Supabase Storage using signed URL with Render optimizations."""
        headers = {
            'Content-Type': content_type,
            'Content-Length': str(len(file_data))
        }
        
        # ✅ RENDER FIX: Shorter timeout for serverless environment
        timeout = aiohttp.ClientTimeout(total=300, connect=30, sock_read=60)  # 5 min total, faster connection/read
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
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
            except asyncio.TimeoutError:
                logger.error(f"❌ File upload timeout - file size: {len(file_data)} bytes")
                raise HTTPException(
                    status_code=504,
                    detail="File upload timeout - please try with a smaller file"
                )
            except Exception as e:
                logger.error(f"❌ File upload error: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"File upload failed: {str(e)}"
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

# 🚀 REFACTORED: Backend-First Document Upload Endpoint
@app.post("/upload-document-backend", response_model=DocumentUploadResponse)
async def upload_document_backend(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    file: UploadFile = File(...)
):
    """
    REFACTORED: Backend-first document upload flow.
    
    ✅ NEW ARCHITECTURE:
    1. Backend generates signed URL directly from storage
    2. Backend uploads file to signed URL
    3. Backend calls edge function to process uploaded file
    4. Edge function focuses on processing, not storage management
    """
    upload_start_time = time.time()
    
    try:
        logger.info(f"🚀 Starting backend-first upload for user {current_user.id}: {file.filename}")
        
        # Read file data with size validation early
        file_data = await file.read()
        
        # Validate file size (50MB limit) - fail fast
        MAX_FILE_SIZE = 50 * 1024 * 1024
        if len(file_data) > MAX_FILE_SIZE:
            logger.warning(f"❌ File too large: {len(file_data)} bytes (max: {MAX_FILE_SIZE})")
            raise HTTPException(
                status_code=413,
                detail={
                    "error": "File too large",
                    "message": f"File size is {len(file_data) // (1024*1024)}MB. Maximum allowed is {MAX_FILE_SIZE // (1024*1024)}MB",
                    "max_size_mb": MAX_FILE_SIZE // (1024*1024),
                    "actual_size_mb": len(file_data) // (1024*1024)
                }
            )
        
        if len(file_data) == 0:
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "Empty file",
                    "message": "The uploaded file is empty. Please select a valid file."
                }
            )
        
        # Validate file type
        allowed_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Unsupported file type",
                    "message": f"File type '{file.content_type}' is not supported. Please upload PDF, DOCX, or TXT files.",
                    "allowed_types": ["PDF", "DOCX", "TXT"]
                }
            )
        
        # Get user token for edge function calls
        auth_header = request.headers.get("authorization")
        user_token = auth_header.split(" ")[1] if auth_header else None
        
        if not user_token:
            raise HTTPException(
                status_code=401, 
                detail={
                    "error": "Missing authentication",
                    "message": "User authentication token is required"
                }
            )
        
        # ✅ STEP 1: Create document record and upload file directly
        logger.info(f"📄 Step 1: Creating document record and uploading file directly...")
        
        # Generate file hash for deduplication
        file_hash = hashlib.sha256(f"{file.filename}-{len(file_data)}-{current_user.id}-{time.time()}".encode()).hexdigest()
        
        # Create storage path
        storage_path = f"{current_user.id}/{file_hash}/{file.filename}"
        
        # Get storage service
        global storage_service_instance
        if not storage_service_instance:
            storage_service_instance = await get_storage_service()
        
        # Create document record in database first
        pool = await get_db_pool()
        document_id = str(uuid.uuid4())
        
        async with pool.get_connection() as conn:
            await conn.execute("""
                INSERT INTO documents (
                    id, user_id, original_filename, file_size, content_type, 
                    file_hash, storage_path, status, progress_percentage,
                    processed_chunks, failed_chunks, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
            """, 
            document_id, current_user.id, file.filename, len(file_data), file.content_type,
            file_hash, storage_path, 'uploading', 5, 0, 0
            )
        
        logger.info(f"✅ Step 1a: Document record created with ID {document_id}")
        
        # ✅ STEP 2: Upload file directly to Supabase Storage
        logger.info(f"📤 Step 2: Uploading file directly to storage...")
        
        try:
            # Upload using storage service
            upload_response = storage_service_instance.supabase.storage.from_('raw_documents').upload(
                storage_path,
                file_data,
                file_options={
                    "content-type": file.content_type,
                    "upsert": "false"  # Don't allow overwrite
                }
            )
            
            # ✅ FIX: Proper Supabase upload response handling
            # Supabase upload() returns a response object, not a dict
            # Success is indicated by no 'error' field in the response
            upload_successful = True
            upload_error = None
            
            # Check if upload response has an error
            if hasattr(upload_response, 'get') and upload_response.get('error'):
                upload_successful = False
                upload_error = upload_response.get('error', 'Unknown storage error')
            elif hasattr(upload_response, 'error') and upload_response.error:
                upload_successful = False
                upload_error = str(upload_response.error)
            elif not upload_response:
                upload_successful = False
                upload_error = 'No response from storage'
            
            if not upload_successful:
                logger.error(f"❌ File upload failed: {upload_error}")
                # Update document status to failed
                async with pool.get_connection() as conn:
                    await conn.execute("""
                        UPDATE documents SET status = 'failed', updated_at = NOW()
                        WHERE id = $1
                    """, document_id)
                
            raise HTTPException(
                status_code=500,
                    detail={
                        "error": "File upload failed",
                        "message": f"Storage error: {upload_error}",
                        "document_id": document_id
                    }
            )
        
            logger.info(f"✅ Step 2 complete: File uploaded to {storage_path}")
            
        except HTTPException:
            # Re-raise HTTP exceptions (already handled above)
            raise
        except Exception as upload_error:
            logger.error(f"❌ File upload exception: {upload_error}")
            # Update document status to failed
            async with pool.get_connection() as conn:
                await conn.execute("""
                    UPDATE documents SET status = 'failed', updated_at = NOW()
                    WHERE id = $1
                """, document_id)
            
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "File upload failed",
                    "message": f"Upload error: {str(upload_error)}",
                    "document_id": document_id
                }
            )
        
        # Update document status to processing
        async with pool.get_connection() as conn:
            await conn.execute("""
                UPDATE documents SET status = 'processing', progress_percentage = 20, 
                updated_at = NOW()
                WHERE id = $1
            """, document_id)
        
        # ✅ STEP 3: Call edge function to process the uploaded file
        logger.info(f"🔄 Step 3: Triggering document processing...")
        
        processing_payload = {
            "documentId": document_id,
            "path": storage_path,
            "filename": file.filename,
            "contentType": file.content_type,
            "fileSize": len(file_data),
            "documentType": "regulatory"  # Regulatory uploads go to 'regulatory_documents' table
        }
        
        processing_success = False
        processing_error_message = None
        
        try:
            processing_result = await edge_orchestrator.call_edge_function(
                'doc-parser',  # ✅ Call doc-parser directly to process uploaded file
                'POST',
                processing_payload,
            user_token,
            current_user.id
        )
        
            # Check if edge function processing actually succeeded
            if processing_result.get('status') == 'success' or processing_result.get('success'):
                logger.info(f"✅ Step 3 complete: Document processing triggered successfully")
                processing_success = True
            else:
                processing_error_message = processing_result.get('error', 'Unknown processing error')
                logger.error(f"❌ Document processing failed: {processing_error_message}")
                
        except Exception as processing_error:
            processing_error_message = f"Processing trigger failed: {str(processing_error)}"
            logger.error(f"❌ Processing trigger exception: {processing_error}")
        
        # Update document status based on processing result
        if processing_success:
            final_status = "processing"
            final_message = f"Document '{file.filename}' uploaded and processing started successfully."
        else:
            final_status = "failed"
            final_message = f"Document '{file.filename}' uploaded but processing failed: {processing_error_message}"
            
            # Update document status to failed in database
            async with pool.get_connection() as conn:
                await conn.execute("""
                    UPDATE documents SET status = 'failed', updated_at = NOW()
                    WHERE id = $1
                """, document_id)
        
        # Determine processing method
        processing_method = "llamaparse" if file.content_type == "application/pdf" else "direct"
        
        processing_time = time.time() - upload_start_time
        logger.info(f"📊 Upload completed in {processing_time:.2f}s")
        
        return DocumentUploadResponse(
            success=processing_success,
            document_id=document_id,
            filename=file.filename,
            status=final_status,
            message=final_message,
            processing_method=processing_method
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        processing_time = time.time() - upload_start_time
        logger.error(f"❌ Unexpected error after {processing_time:.2f}s: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred during upload. Please try again.",
                "processing_time": f"{processing_time:.2f}s"
            }
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
                    metadata = COALESCE(metadata, '{}'::jsonb) || COALESCE($4::jsonb, '{}'::jsonb),
                    updated_at = NOW()
                WHERE id = $1
            """, 
            payload.document_id,
            payload.status,
            payload.progress,
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
    upload_start_time = time.time()
    
    try:
        logger.info(f"🏛️ Starting regulatory document upload: {document_title}")
        
        # Read file data with validation
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
        
        # Validate file type
        allowed_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{file.content_type}'. Please upload PDF, DOCX, or TXT files."
            )
        
        # Get user token for edge function calls
        auth_header = request.headers.get("authorization")
        user_token = auth_header.split(" ")[1] if auth_header else None
        
        if not user_token:
            raise HTTPException(status_code=401, detail="Missing user token")
        
        # ✅ STEP 1: Create regulatory document record and upload file directly
        logger.info(f"📄 Step 1: Creating regulatory document record and uploading file...")
        
        # Generate file hash for deduplication
        file_hash = hashlib.sha256(f"{file.filename}-{len(file_data)}-{current_user.id}-{time.time()}".encode()).hexdigest()
        
        # Create storage path for regulatory documents
        storage_path = f"regulatory/{current_user.id}/{file_hash}/{file.filename}"
        
        # Get storage service
        global storage_service_instance
        if not storage_service_instance:
            storage_service_instance = await get_storage_service()
        
        # Create regulatory document record in regulatory_documents table
        pool = await get_db_pool()
        document_id = str(uuid.uuid4())
        
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
            "upload_method": "backend_orchestrated",
            **additional_metadata
        }
        
        async with pool.get_connection() as conn:
            # Create record in regulatory_documents table (uses document_id as primary key)
            await conn.execute("""
                INSERT INTO regulatory_documents (
                    document_id, raw_document_path, title, jurisdiction, program, 
                    document_type, source_url, extraction_method, version,
                    content_hash, priority_score, search_metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """, 
            document_id, storage_path, document_title, additional_metadata.get('jurisdiction', 'federal'), 
            [additional_metadata.get('program', 'insurance')], document_type, source_url, 
            'api_upload', 1, file_hash, 1.0, json.dumps({})
            )
            
            # Also create in documents table for vectorization compatibility
            await conn.execute("""
                INSERT INTO documents (
                    id, user_id, original_filename, file_size, content_type, 
                    file_hash, storage_path, document_type, status, metadata,
                    progress_percentage, processed_chunks, failed_chunks, 
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW(), NOW())
            """, 
            document_id, current_user.id, file.filename, len(file_data), file.content_type,
            file_hash, storage_path, 'regulatory', 'uploading', json.dumps(regulatory_metadata),
            5, 0, 0
            )
        
        logger.info(f"✅ Step 1a: Regulatory document record created with ID {document_id}")
        
        # ✅ STEP 2: Upload file directly to Supabase Storage
        logger.info(f"📤 Step 2: Uploading regulatory file to storage...")
        
        try:
            # Upload using storage service to raw_documents bucket
            upload_response = storage_service_instance.supabase.storage.from_('raw_documents').upload(
                storage_path,
                file_data,
                file_options={
                    "content-type": file.content_type,
                    "upsert": "false"
                }
            )
            
            # ✅ FIX: Proper Supabase upload response handling
            # Supabase upload() returns a response object, not a dict
            # Success is indicated by no 'error' field in the response
            upload_successful = True
            upload_error = None
            
            # Check if upload response has an error
            if hasattr(upload_response, 'get') and upload_response.get('error'):
                upload_successful = False
                upload_error = upload_response.get('error', 'Unknown storage error')
            elif hasattr(upload_response, 'error') and upload_response.error:
                upload_successful = False
                upload_error = str(upload_response.error)
            elif not upload_response:
                upload_successful = False
                upload_error = 'No response from storage'
            
            if not upload_successful:
                logger.error(f"❌ File upload failed: {upload_error}")
                # Update document status to failed
                async with pool.get_connection() as conn:
                    await conn.execute("""
                        UPDATE regulatory_documents SET updated_at = NOW()
                        WHERE document_id = $1
                    """, document_id)
                    await conn.execute("""
                        UPDATE documents SET status = 'failed', updated_at = NOW()
                        WHERE id = $1
                    """, document_id)
                
            raise HTTPException(
                status_code=500,
                    detail=f"Regulatory file upload failed: {upload_error}"
            )
        
            logger.info(f"✅ Step 2 complete: Regulatory file uploaded to {storage_path}")
            
        except Exception as upload_error:
            logger.error(f"❌ Regulatory file upload exception: {upload_error}")
            async with pool.get_connection() as conn:
                await conn.execute("""
                    UPDATE regulatory_documents SET updated_at = NOW()
                    WHERE document_id = $1
                """, document_id)
                await conn.execute("""
                    UPDATE documents SET status = 'failed', updated_at = NOW()
                    WHERE id = $1
                """, document_id)
            
            raise HTTPException(
                status_code=500,
                detail=f"Regulatory file upload failed: {str(upload_error)}"
            )
        
        # Update document status to processing
        async with pool.get_connection() as conn:
            await conn.execute("""
                UPDATE regulatory_documents SET updated_at = NOW()
                WHERE document_id = $1
            """, document_id)
            await conn.execute("""
                UPDATE documents SET status = 'processing', progress_percentage = 20, 
                updated_at = NOW()
                WHERE id = $1
            """, document_id)
        
        # ✅ STEP 3: Call edge function to process the uploaded regulatory file
        logger.info(f"🔄 Step 3: Triggering regulatory document processing...")
        
        processing_payload = {
            "documentId": document_id,
            "path": storage_path,
            "filename": file.filename,
            "contentType": file.content_type,
            "fileSize": len(file_data),
            "documentType": "regulatory"  # Regulatory uploads go to 'regulatory_documents' table
        }
        
        processing_success = False
        processing_error_message = None
        
        try:
            processing_result = await edge_orchestrator.call_edge_function(
                'doc-parser',  # Use doc-parser directly like user uploads
                'POST',
                processing_payload,
            user_token,
            current_user.id
        )
        
            # Check if edge function processing actually succeeded
            if processing_result.get('status') == 'success' or processing_result.get('success'):
                logger.info(f"✅ Step 3 complete: Regulatory document processing triggered successfully")
                processing_success = True
            else:
                processing_error_message = processing_result.get('error', 'Unknown processing error')
                logger.error(f"❌ Regulatory document processing failed: {processing_error_message}")
                
        except Exception as processing_error:
            processing_error_message = f"Processing trigger failed: {str(processing_error)}"
            logger.error(f"❌ Regulatory processing trigger exception: {processing_error}")
        
        # Update document status based on processing result
        if processing_success:
            final_status = "processing"
            final_message = f"Regulatory document '{document_title}' uploaded and processing started successfully!"
        else:
            final_status = "failed"
            final_message = f"Regulatory document '{document_title}' uploaded but processing failed: {processing_error_message}"
            
            # Update document status to failed in database
            async with pool.get_connection() as conn:
            await conn.execute("""
                    UPDATE regulatory_documents SET updated_at = NOW()
                    WHERE document_id = $1
                """, document_id)
                await conn.execute("""
                    UPDATE documents SET status = 'failed', updated_at = NOW()
                WHERE id = $1
                """, document_id)
        
        # Determine processing method
        processing_method = "llamaparse" if file.content_type == "application/pdf" else "direct"
        
        processing_time = time.time() - upload_start_time
        logger.info(f"📊 Regulatory upload completed in {processing_time:.2f}s")
        
        logger.info(f"✅ Regulatory document uploaded: {document_title}")
        
        return DocumentUploadResponse(
            success=processing_success,
            document_id=document_id,
            filename=file.filename,
            status=final_status,
            message=final_message,
            processing_method=processing_method
        )
        
    except Exception as e:
        logger.error(f"❌ Regulatory document upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Regulatory upload failed: {str(e)}"
        )

# 📄 NEW: Document Management Endpoints
@app.get("/documents")
async def list_user_documents(
    current_user: UserResponse = Depends(get_current_user),
    limit: int = 50,
    document_type: Optional[str] = None
):
    """List user's documents - SIMPLIFIED MVP VERSION."""
    try:
        # Direct database query - no service dependencies  
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            # Build query with optional document_type filter
            where_clause = "WHERE user_id = $1"
            params = [current_user.id]
            
            if document_type:
                where_clause += " AND document_type = $2"
                params.append(document_type)
                params.append(limit)
                limit_param = "$3"
            else:
                params.append(limit)
                limit_param = "$2"
            
            docs = await conn.fetch(f"""
                SELECT 
                    id, original_filename, status, progress_percentage,
                    file_size, content_type, document_type, created_at
                FROM documents
                {where_clause}
                ORDER BY created_at DESC
                LIMIT {limit_param}
            """, *params)
            
            # Return clean document list
            return [{
                'document_id': str(doc['id']),
                'filename': doc['original_filename'],
                'status': doc['status'],
                'progress_percentage': doc['progress_percentage'] or 0,
                'file_size': doc['file_size'],
                'content_type': doc['content_type'],
                'document_type': doc['document_type'],
                'created_at': doc['created_at'],
                'processing_complete': doc['status'] in ['completed', 'ready']
            } for doc in docs]
        
    except Exception as e:
        logger.error(f"Error listing documents for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )

@app.get("/documents/{document_id}/status")
async def get_document_status(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get specific document status - SIMPLIFIED MVP VERSION."""
    try:
        # Direct database query - no service dependencies
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            doc = await conn.fetchrow("""
                SELECT 
                    id, original_filename, status, progress_percentage,
                    file_size, content_type, created_at, updated_at,
                    document_type
                FROM documents
                WHERE id = $1 AND user_id = $2
            """, document_id, current_user.id)
            
            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Return clean status response
            return {
                'document_id': str(doc['id']),
                'filename': doc['original_filename'],
                'status': doc['status'],
                'progress_percentage': doc['progress_percentage'] or 0,
                'file_size': doc['file_size'],
                'content_type': doc['content_type'],
                'document_type': doc['document_type'],
                'created_at': doc['created_at'],
                'updated_at': doc['updated_at'],
                'processing_complete': doc['status'] in ['completed', 'ready']
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document status {document_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document status: {str(e)}"
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
            "list_documents": "/documents",
            "document_status": "/documents/{document_id}/status",
            "webhook_processing": "/webhooks/document-processing",
            "debug_progress": "/debug/documents/{document_id}/progress"
        }
    }

# 🛠️ DEBUG: Manual progress update for testing
@app.post("/debug/documents/{document_id}/progress")
async def debug_update_progress(
    document_id: str,
    progress: int,
    status: str = "processing",
    current_user: UserResponse = Depends(get_current_user)
):
    """Debug endpoint to manually update document progress for testing."""
    try:
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            # Verify document belongs to user
            doc_exists = await conn.fetchval("""
                SELECT EXISTS(SELECT 1 FROM documents WHERE id = $1 AND user_id = $2)
            """, document_id, current_user.id)
            
            if not doc_exists:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Update progress
            await conn.execute("""
                UPDATE documents 
                SET progress_percentage = $1, status = $2, updated_at = NOW()
                WHERE id = $3 AND user_id = $4
            """, progress, status, document_id, current_user.id)
            
            return {
                "success": True,
                "document_id": document_id,
                "progress": progress,
                "status": status,
                "message": f"Progress updated to {progress}%"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating progress for {document_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update progress: {str(e)}"
        )

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
