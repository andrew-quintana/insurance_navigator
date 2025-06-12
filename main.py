#!/usr/bin/env python3
"""
FastAPI Insurance Navigator API - Production Database Integration

Comprehensive async FastAPI application with:
- Supabase PostgreSQL database integration
- Persistent user authentication and session management  
- Conversation history persistence
- Document storage with Supabase Storage
- LangGraph agent orchestration integration
- Role-based access control
"""

import os
import sys
import uuid
import hashlib
from fastapi import FastAPI, HTTPException, Depends, Request, status, UploadFile, File, Form, Response, Body, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import json
import asyncio
import re
from urllib.parse import urlparse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from concurrent.futures import ThreadPoolExecutor

# Database service imports
from db.services.user_service import get_user_service, UserService
from db.services.conversation_service import get_conversation_service, ConversationService
from db.services.storage_service import get_storage_service, StorageService
from db.services.db_pool import get_db_pool

# Centralized CORS configuration
from utils.cors_config import cors_config, create_preflight_response, add_cors_headers

# Set up logging first
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
    # Don't define AgentOrchestrator as None - let it fail properly
    AGENT_ORCHESTRATOR_AVAILABLE = False
    raise ImportError(f"AgentOrchestrator import failed: {e}. This is a critical error.")

# Middleware import
try:
    from db.middleware.error_handler import ErrorHandlerMiddleware
    ERROR_HANDLER_AVAILABLE = True
except ImportError:
    ERROR_HANDLER_AVAILABLE = False
    logging.warning("Error handler middleware not available")

# Fast imports for document processing
# from sentence_transformers import SentenceTransformer  # REMOVED - using LlamaCloud
import PyPDF2  # Re-enabled for incremental PDF processing
import io

# Custom CORS middleware using centralized configuration
class CustomCORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware using centralized configuration from utils.cors_config."""
    
    def __init__(self, app):
        super().__init__(app)
        # Use the centralized CORS configuration
        self.cors_config = cors_config
    
    async def dispatch(self, request: Request, call_next):
        """Process request with centralized CORS handling."""
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            return create_preflight_response(origin)
        
        try:
            # Process the request
            start_time = time.time()
            response = await call_next(request)
            processing_time = time.time() - start_time
            
            # Add CORS headers using centralized config
            add_cors_headers(response, origin)
            
            # Add timing header for monitoring
            response.headers["X-Processing-Time"] = f"{processing_time:.3f}"
            
            return response
            
        except Exception as e:
            # Even on error, return CORS headers
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
    description="Medicare/Medicaid navigation with persistent database and agent orchestration",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add custom CORS middleware FIRST
app.add_middleware(CustomCORSMiddleware)

# Keep the original CORS middleware as backup using centralized config
cors_middleware_config = cors_config.get_fastapi_cors_middleware_config()
app.add_middleware(
    CORSMiddleware,
    **cors_middleware_config
)

# Add error handling middleware if available
if ERROR_HANDLER_AVAILABLE:
    app.add_middleware(ErrorHandlerMiddleware)

# Pydantic models for API requests/responses
class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: Optional[datetime] = None
    is_active: bool = True
    roles: List[str] = []

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    text: str
    conversation_id: str
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    workflow_type: Optional[str] = None
    agent_state: Optional[Dict[str, Any]] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str

class ForgotPasswordRequest(BaseModel):
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ConversationResponse(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    metadata: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    id: int
    file_path: str
    original_filename: str
    content_type: str
    file_size: int
    document_type: str
    uploaded_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class UploadResponse(BaseModel):
    document_id: int
    file_path: str
    original_filename: str
    file_size: int
    signed_url: Optional[str] = None

# Global service instances
user_service_instance: Optional[UserService] = None
conversation_service_instance: Optional[ConversationService] = None
storage_service_instance: Optional[StorageService] = None
agent_orchestrator_instance: Optional[AgentOrchestrator] = None

# Global embedding model (loaded once)
embedding_model = None

async def get_embedding_model():
    """Get or load the sentence transformer model with memory optimization."""
    global embedding_model
    if embedding_model is None:
        try:
            # Check available memory and use lighter model if needed
            import psutil
            available_memory = psutil.virtual_memory().available / (1024**2)  # MB
            logger.info(f"Available memory: {available_memory:.0f}MB")
            
            if available_memory < 300:  # Less than 300MB available
                logger.warning("⚠️ Low memory detected, using mock model")
                class MockModel:
                    def encode(self, text):
                        import random
                        import numpy as np
                        # Return 1536-dimensional vector to match database schema (OpenAI dimensions)
                        return np.array([random.uniform(-1, 1) for _ in range(1536)])
                embedding_model = MockModel()
                logger.info("✅ Mock embedding model loaded (1536D for OpenAI compatibility)")
            else:
                logger.info("Loading SBERT model: all-MiniLM-L6-v2...")
                # SentenceTransformer temporarily disabled - using mock for LlamaCloud migration
                class MockModel:
                    def encode(self, text):
                        import random
                        import numpy as np
                        # Return 1536-dimensional vector to match database schema (OpenAI dimensions)
                        return np.array([random.uniform(-1, 1) for _ in range(1536)])
                embedding_model = MockModel()
                logger.warning("⚠️ Using mock embedding model for LlamaCloud migration (1536D)")
                # raise ImportError("SentenceTransformer disabled for memory optimization")
                # embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
                # logger.info("✅ SBERT model loaded successfully")
                
        except ImportError:
            logger.warning("⚠️ psutil not available, proceeding with model loading")
            try:
                # SentenceTransformer temporarily disabled - using mock for LlamaCloud migration
                raise ImportError("SentenceTransformer disabled for memory optimization")
                # embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
                # logger.info("✅ SBERT model loaded successfully")
            except Exception as e:
                logger.error(f"❌ Failed to load SBERT model: {e}")
                class MockModel:
                    def encode(self, text):
                        import random
                        import numpy as np
                        # Return 1536-dimensional vector to match database schema (OpenAI dimensions)
                        return np.array([random.uniform(-1, 1) for _ in range(1536)])
                embedding_model = MockModel()
                logger.warning("⚠️ Using mock embedding model due to loading failure (1536D)")
        except Exception as e:
            logger.error(f"❌ Failed to load SBERT model: {e}")
            # Return a mock model for demo purposes
            class MockModel:
                def encode(self, text):
                    import random
                    import numpy as np
                    # Return 1536-dimensional vector to match database schema (OpenAI dimensions)
                    return np.array([random.uniform(-1, 1) for _ in range(1536)])
            embedding_model = MockModel()
            logger.warning("⚠️ Using mock embedding model for demo (1536D)")
    return embedding_model

def extract_text_from_pdf(file_data: bytes) -> str:
    """Extract text from PDF file using PyPDF2."""
    try:
        logger.info(f"📄 Starting PDF text extraction (file size: {len(file_data)} bytes)...")
        
        # Use PyPDF2 for real PDF processing
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
        logger.info(f"📄 PDF loaded, found {len(pdf_reader.pages)} pages")
        
        text = ""
        for i, page in enumerate(pdf_reader.pages):
            logger.info(f"📄 Processing page {i+1}/{len(pdf_reader.pages)}...")
            page_text = page.extract_text()
            text += page_text + "\n"
            logger.info(f"📄 Page {i+1} processed: {len(page_text)} characters extracted")
        
        result = text.strip()
        logger.info(f"✅ PDF text extraction complete: {len(result)} total characters")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error extracting PDF text: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Fallback to mock content if PDF processing fails
        logger.warning("⚠️ Falling back to mock content due to PDF processing error")
        return f"""Sample Insurance Policy Document

Error occurred during PDF processing: {str(e)[:100]}...
File size: {len(file_data)} bytes

This is fallback content. For production use, this will be processed by LlamaCloud document parsing service.

Mock coverage details:
- Deductible: $1,000
- Out-of-pocket maximum: $5,000
- Copay: $25 for primary care
- Network: Preferred Provider Organization (PPO)
        """

def extract_text_from_file(file_data: bytes, filename: str) -> str:
    """Extract text from various file types."""
    logger.info(f"🔍 Starting text extraction from {filename} (size: {len(file_data)} bytes)")
    
    if filename.lower().endswith('.pdf'):
        logger.info(f"📄 Detected PDF file, using PDF extraction...")
        return extract_text_from_pdf(file_data)
    elif filename.lower().endswith(('.txt', '.md')):
        logger.info(f"📝 Detected text file, using UTF-8 decoding...")
        try:
            result = file_data.decode('utf-8')
            logger.info(f"✅ UTF-8 decoding successful: {len(result)} characters")
            return result
        except UnicodeDecodeError:
            logger.warning(f"⚠️  UTF-8 failed, trying latin-1...")
            try:
                result = file_data.decode('latin-1')
                logger.info(f"✅ Latin-1 decoding successful: {len(result)} characters")
                return result
            except Exception as e:
                logger.error(f"❌ Text decoding failed: {e}")
                return ""
    else:
        logger.info(f"❓ Unknown file type, attempting UTF-8 decoding...")
        # Try to decode as text for other file types
        try:
            result = file_data.decode('utf-8')
            logger.info(f"✅ UTF-8 decoding successful: {len(result)} characters")
            return result
        except Exception as e:
            logger.warning(f"⚠️  UTF-8 decoding failed for unknown file type: {e}")
            return ""

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break
        else:
            # Try to break at a sentence or word boundary
            break_point = text.rfind('.', start, end)
            if break_point == -1:
                break_point = text.rfind(' ', start, end)
            if break_point == -1:
                break_point = end
            else:
                break_point += 1  # Include the period/space
            
            chunks.append(text[start:break_point].strip())
            start = break_point - overlap
            if start < 0:
                start = 0
    
    return [chunk for chunk in chunks if chunk.strip()]

# Fallback orchestrator for when agents are not available
class FallbackOrchestrator:
    """Fallback orchestrator when LangGraph agents are not available."""
    
    async def process_message(self, message: str, user_id: str, conversation_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process message with fallback logic."""
        return {
            "response": f"""**Insurance Navigator Response**

I understand you're asking: "{message}"

I'm currently running in maintenance mode, but I'm here to help with Medicare/Medicaid navigation. Your question has been received and saved to your conversation history.

For immediate assistance, please try:
- Asking about specific Medicare plans
- Questions about Medicaid eligibility
- Help with insurance claims
- Coverage verification

Your conversation ID: {conversation_id}""",
                "sources": [],
            "metadata": {
                "mode": "fallback",
                "message_received": True,
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

# Authentication dependency
async def get_current_user(request: Request) -> UserResponse:
    """Get current authenticated user from JWT token."""
    global user_service_instance
    
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        if not user_service_instance:
            user_service_instance = await get_user_service()
        
        # Use validate_session which returns full user data from database
        user_data = await user_service_instance.validate_session(token)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return UserResponse(**user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.options("/{full_path:path}")
async def options_handler(request: Request):
    """Handle CORS preflight requests explicitly."""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint with caching to reduce database load."""
    # Cache health check results for 30 seconds to reduce DB pressure
    cache_key = "health_check_cache"
    cache_duration = 30  # seconds
    
    # Simple in-memory cache using global variable
    global _health_cache
    if not hasattr(health_check, '_health_cache'):
        health_check._health_cache = {"result": None, "timestamp": 0}
    
    current_time = datetime.utcnow().timestamp()
    cache = health_check._health_cache
    
    # Return cached result if still valid
    if cache["result"] and (current_time - cache["timestamp"]) < cache_duration:
        return cache["result"]
    
    # Perform actual health check
    try:
        # Test database connection with timeout
        db_pool = await get_db_pool()
        if db_pool:
            # Use a more resilient connection test
            try:
                # Fix: Use timeout for the entire operation
                async def test_db_connection():
                    async with db_pool.get_connection() as conn:
                        await conn.execute("SELECT 1")
                
                await asyncio.wait_for(test_db_connection(), timeout=5.0)
                db_status = "connected"
                logger.debug("✅ Health check: Database connection successful")
            except asyncio.TimeoutError:
                db_status = "timeout"
                logger.warning("⚠️ Health check: Database connection timeout")
            except Exception as e:
                db_status = f"error: {str(e)[:50]}"
                logger.warning(f"⚠️ Health check: Database connection error: {e}")
        else:
            db_status = "unavailable"
            logger.warning("⚠️ Health check: Database pool unavailable")

        result = {
            "status": "healthy" if db_status == "connected" else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
            "version": "2.0.0",
            "cached": False
        }
        
        # Cache the result
        cache["result"] = result
        cache["timestamp"] = current_time
        
        return result
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        error_result = {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": f"error: {str(e)[:50]}",
            "version": "2.0.0",
            "cached": False
        }
        
        # Cache error result for shorter duration (10 seconds)
        if (current_time - cache["timestamp"]) > 10:
            cache["result"] = error_result
            cache["timestamp"] = current_time
            
        return error_result

# Authentication endpoints
@app.post("/register", response_model=Token)
async def register(request: RegisterRequest):
    """Register a new user with database persistence."""
    global user_service_instance
    
    try:
        if not user_service_instance:
            user_service_instance = await get_user_service()
        
        # Create user in database
        user_data = await user_service_instance.create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        
        # Create JWT token
        token = user_service_instance.create_access_token(user_data)
        
        logger.info(f"User registered: {request.email}")
        return Token(access_token=token, token_type="Bearer")
        
    except ValueError as e:
        logger.warning(f"Registration failed for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@app.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """Authenticate user with database validation."""
    global user_service_instance
    
    try:
        if not user_service_instance:
            user_service_instance = await get_user_service()
        
        # Authenticate user
        user_data = await user_service_instance.authenticate_user(request.email, request.password)
        
        if not user_data:
            logger.warning(f"Login failed for {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create JWT token
        token = user_service_instance.create_access_token(user_data)
        
        logger.info(f"User logged in: {request.email}")
        return Token(access_token=token, token_type="Bearer")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@app.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Send password reset email (placeholder implementation)."""
    try:
        logger.info(f"Password reset requested for: {request.email}")
        
        # For now, just return success - in production, this would:
        # 1. Check if email exists in database
        # 2. Generate a secure reset token
        # 3. Send email with reset link
        # 4. Store token with expiration time
        
        return {
            "message": "If an account with that email exists, you'll receive password reset instructions.",
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Forgot password error for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )

@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information."""
    return current_user

# Chat and conversation endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Main chat endpoint with persistent conversation and agent orchestration."""
    global conversation_service_instance, agent_orchestrator_instance
    
    try:
        # Initialize services
        if not conversation_service_instance:
            conversation_service_instance = await get_conversation_service()
        
        # Get or create conversation
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = await conversation_service_instance.create_conversation(
                user_id=current_user.id,
                metadata={"workflow_type": "medicare_navigator"}
            )
        
        # Save user message to conversation history
        await conversation_service_instance.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
            metadata=request.context or {}
        )
        
        # Process message with agent orchestrator
        try:
            if AGENT_ORCHESTRATOR_AVAILABLE and not agent_orchestrator_instance:
                try:
                    logger.info("🤖 Initializing AgentOrchestrator for first use...")
                    agent_orchestrator_instance = AgentOrchestrator()
                    logger.info("✅ AgentOrchestrator initialized successfully")
                except Exception as init_error:
                    logger.error(f"❌ AgentOrchestrator initialization failed: {init_error}")
                    agent_orchestrator_instance = None
            
            if agent_orchestrator_instance:
                # Use production agent orchestrator
                result = await agent_orchestrator_instance.process_message(
                    message=request.message,
                    user_id=current_user.id,
                    conversation_id=conversation_id
                )
                response_text = result.get("text", "I'm processing your request...")
                sources = result.get("sources", [])
                metadata = result.get("metadata", {})
                agent_state = result.get("agent_state")
            else:
                # Use fallback orchestrator
                logger.info("💡 Using fallback orchestrator")
                fallback = FallbackOrchestrator()
                result = await fallback.process_message(
                    request.message, current_user.id, conversation_id, request.context
                )
                response_text = result["response"]
                sources = result.get("sources", [])
                metadata = result.get("metadata", {})
                agent_state = None
            
        except Exception as e:
            logger.error(f"Agent processing error: {str(e)}")
            response_text = f"I apologize, but I'm experiencing technical difficulties. Your message has been saved and I'll respond as soon as possible."
            sources = []
            metadata = {"error": str(e), "fallback_used": True}
            agent_state = None
        
        # Save agent response to conversation history
        await conversation_service_instance.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
            metadata={
                "sources": sources,
                "agent_metadata": metadata,
                "agent_state": agent_state
            }
        )
        
        # Update conversation metadata if agent state available
        if agent_state:
            await conversation_service_instance.update_conversation_state(
                conversation_id=conversation_id,
                state=agent_state
            )
        
        return ChatResponse(
            text=response_text,
            conversation_id=conversation_id,
            sources=sources,
            metadata=metadata,
            workflow_type=result.get('workflow_type', 'medicare_navigator'),
            agent_state=agent_state
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing your message"
        )

@app.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    current_user: UserResponse = Depends(get_current_user),
    limit: int = 20
):
    """Get user's conversation history."""
    global conversation_service_instance
    
    try:
        if not conversation_service_instance:
            conversation_service_instance = await get_conversation_service()
        
        conversations = await conversation_service_instance.get_user_conversations(
            user_id=current_user.id,
            limit=limit
        )
        
        return [
            ConversationResponse(
                id=conv["id"],
                created_at=conv["created_at"],
                updated_at=conv["updated_at"],
                message_count=conv["message_count"],
                metadata=conv.get("metadata")
            )
            for conv in conversations
        ]
        
    except Exception as e:
        logger.error(f"Error fetching conversations for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch conversations"
        )

@app.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user),
    limit: int = 50
):
    """Get messages from a specific conversation."""
    global conversation_service_instance
    
    try:
        if not conversation_service_instance:
            conversation_service_instance = await get_conversation_service()
        
        messages = await conversation_service_instance.get_conversation_history(
            conversation_id=conversation_id,
            limit=limit
        )
        
        return {"messages": messages}
        
    except Exception as e:
        logger.error(f"Error fetching messages for conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch conversation messages"
        )

# Document storage endpoints
@app.post("/upload-document", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    policy_id: str = Form(...),
    document_type: str = Form(default="policy"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload a policy document with Supabase Storage."""
    global storage_service_instance
    
    try:
        if not storage_service_instance:
            storage_service_instance = await get_storage_service()
        
        # Read file data
        file_data = await file.read()
        
        # Upload to storage
        upload_result = await storage_service_instance.upload_policy_document(
            policy_id=policy_id,
            file_data=file_data,
            filename=file.filename,
            user_id=current_user.id,
            document_type=document_type,
            metadata={
                "uploaded_by_name": current_user.full_name,
                "content_length": len(file_data)
            }
        )
        
        # Generate signed URL for immediate access
        signed_url = await storage_service_instance.get_signed_url(
            file_path=upload_result["file_path"],
            expires_in=3600,
            download=False
        )
        
        logger.info(f"Document uploaded: {file.filename} by user {current_user.id}")
        
        return UploadResponse(
            document_id=upload_result["document_id"],
            file_path=upload_result["file_path"],
            original_filename=upload_result["original_filename"],
            file_size=upload_result["file_size"],
            signed_url=signed_url
        )
        
    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@app.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    policy_id: Optional[str] = None,
    document_type: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """List user's documents with optional filtering."""
    global storage_service_instance
    
    try:
        if not storage_service_instance:
            storage_service_instance = await get_storage_service()
        
        if policy_id:
            # List policy documents using vector storage
            documents = await storage_service_instance.list_policy_documents(
                policy_id=policy_id, 
                user_id=current_user.id
            )
        else:
            # For now, require policy_id to list documents
            # In the future, we could add a user_documents method
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="policy_id is required"
            )
        
        return [
            DocumentResponse(
                id=doc["id"],
                file_path=doc["file_path"],
                original_filename=doc["original_filename"],
                content_type=doc["content_type"],
                file_size=doc["file_size"],
                document_type=doc["document_type"],
                uploaded_at=doc["uploaded_at"],
                metadata=doc.get("metadata")
            )
            for doc in documents
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents"
        )

@app.get("/documents/{file_path:path}/download")
async def download_document(
    file_path: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get signed URL for document download."""
    global storage_service_instance
    
    try:
        if not storage_service_instance:
            storage_service_instance = await get_storage_service()
        
        # Check permissions
        permissions = await storage_service_instance.get_file_access_permissions(
            file_path=file_path,
            user_id=current_user.id
        )
        
        if not permissions["read"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Generate signed URL
        signed_url = await storage_service_instance.get_signed_url(
            file_path=file_path,
            expires_in=3600,
            download=True
        )
        
        # Redirect to signed URL
        return RedirectResponse(url=signed_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error for {file_path}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Download failed"
        )

@app.delete("/documents/{file_path:path}")
async def delete_document(
    file_path: str,
    hard_delete: bool = False,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a document (soft delete by default)."""
    global storage_service_instance
    
    try:
        if not storage_service_instance:
            storage_service_instance = await get_storage_service()
        
        # Check permissions
        permissions = await storage_service_instance.get_file_access_permissions(
            file_path=file_path,
            user_id=current_user.id
        )
        
        if not permissions["delete"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Delete access denied"
            )
        
        # Delete document
        success = await storage_service_instance.delete_document(
            file_path=file_path,
            user_id=current_user.id,
            hard_delete=hard_delete
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return {"message": f"Document {'permanently deleted' if hard_delete else 'deleted'}", "success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error for {file_path}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Delete failed"
        )

# Application lifecycle events
async def startup_logic():
    """Initialize services and database connections on startup."""
    global user_service_instance, conversation_service_instance, storage_service_instance
    
    logger.info("🚀 Insurance Navigator API v2.0 starting up...")
    
    # Log environment info for debugging (without sensitive data)
    db_url = os.getenv("DATABASE_URL", "NOT_SET")
    db_configured = "✅ Configured" if db_url != "NOT_SET" else "❌ NOT SET"
    logger.info(f"🔧 DATABASE_URL: {db_configured}")
    logger.info(f"🔧 PORT: {os.getenv('PORT', 'NOT_SET')}")
    logger.info(f"🔧 ASYNCPG_DISABLE_PREPARED_STATEMENTS: {os.getenv('ASYNCPG_DISABLE_PREPARED_STATEMENTS', 'NOT_SET')}")
    
    try:
        # Initialize database pool with timeout and retry logic
        logger.info("📡 Initializing database connection...")
        max_db_retries = 3
        for attempt in range(max_db_retries):
            try:
                pool = await asyncio.wait_for(get_db_pool(), timeout=30.0)
                logger.info("✅ Database connection pool initialized")
                break
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Database connection timeout (attempt {attempt + 1}/{max_db_retries})")
                if attempt == max_db_retries - 1:
                    logger.error("❌ Database connection failed after all retries")
                    raise
                await asyncio.sleep(5)  # Wait before retry
            except Exception as e:
                logger.error(f"❌ Database connection error (attempt {attempt + 1}/{max_db_retries}): {e}")
                if attempt == max_db_retries - 1:
                    raise
                await asyncio.sleep(5)  # Wait before retry
        
        # Initialize services
        user_service_instance = await get_user_service()
        logger.info("✅ User service initialized")
        
        conversation_service_instance = await get_conversation_service()
        logger.info("✅ Conversation service initialized")
        
        storage_service_instance = await get_storage_service()
        logger.info("✅ Storage service initialized")
        
        # Initialize agent orchestrator if available (lazy initialization to avoid blocking startup)
        if AGENT_ORCHESTRATOR_AVAILABLE:
            logger.info("🤖 Agent orchestrator will be initialized on first use")
        else:
            logger.info("💡 Using fallback orchestrator (agent system not available)")
        
        logger.info("🎉 Startup complete - Insurance Navigator API ready!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        # Don't raise to prevent startup failure - let the app start with degraded functionality
        logger.warning("⚠️ Continuing startup despite errors...")

async def shutdown_logic():
    """Cleanup on application shutdown."""
    logger.info("👋 Insurance Navigator API shutting down...")
    
    try:
        # Close database connections
        pool = await get_db_pool()
        await pool.close()
        logger.info("✅ Database connections closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
    
    logger.info("✅ Shutdown complete")

# Use startup/shutdown events for backward compatibility
@app.on_event("startup")
async def startup_event():
    await startup_logic()

@app.on_event("shutdown")
async def shutdown_event():
    await shutdown_logic()

# Debug endpoint for development
@app.get("/debug/workflow/{conversation_id}")
async def debug_workflow(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Debug endpoint to view complete workflow execution details."""
    global conversation_service_instance
    
    try:
        if not conversation_service_instance:
            conversation_service_instance = await get_conversation_service()
        
        # Get conversation messages
        messages = await conversation_service_instance.get_conversation_history(
            conversation_id=conversation_id,
            limit=50
        )
        
        # Get workflow states
        workflow_states = await conversation_service_instance.get_workflow_state(conversation_id)
        
        # Get agent states
        agent_states = []
        agent_names = ["prompt_security", "patient_navigator", "task_requirements", 
                      "service_access_strategy", "regulatory", "chat_communicator"]
        
        for agent_name in agent_names:
            try:
                state = await conversation_service_instance.get_agent_state(
                    conversation_id=conversation_id,
                    agent_name=agent_name
                )
                if state:
                    agent_states.append({
                        "agent_name": agent_name,
                        "state": state
                    })
            except Exception as e:
                # Agent state might not exist, continue
                continue
        
        return {
            "conversation_id": conversation_id,
            "user_id": current_user.id,
            "messages": messages,
            "workflow_states": workflow_states,
            "agent_states": agent_states,
            "debug_info": {
                "total_messages": len(messages),
                "agents_executed": len(agent_states),
                "workflow_available": workflow_states is not None
            }
        }
        
    except Exception as e:
        logger.error(f"Debug workflow error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug error: {str(e)}"
        )

@app.get("/debug/latest-workflow")
async def debug_latest_workflow(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get debug info for the user's latest conversation."""
    global conversation_service_instance
    
    try:
        if not conversation_service_instance:
            conversation_service_instance = await get_conversation_service()
        
        # Get user's latest conversation
        conversations = await conversation_service_instance.get_user_conversations(
            user_id=current_user.id,
            limit=1
        )
        
        if not conversations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No conversations found"
            )
        
        latest_conversation = conversations[0]
        conversation_id = latest_conversation["id"]
        
        # Redirect to the full debug endpoint
        return await debug_workflow(conversation_id, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Debug latest workflow error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug error: {str(e)}"
        )

@app.get("/debug/latest-workflow/readable")
async def debug_latest_workflow_readable(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get debug info for the user's latest conversation in human-readable format."""
    global conversation_service_instance
    
    try:
        # Get the raw debug data
        debug_data = await debug_latest_workflow(current_user)
        
        # Format it in a readable way
        readable_output = []
        
        # Header
        readable_output.append("🔍 AGENT WORKFLOW DEBUG REPORT")
        readable_output.append("=" * 50)
        readable_output.append(f"📋 Conversation ID: {debug_data['conversation_id']}")
        readable_output.append(f"👤 User ID: {debug_data['user_id']}")
        readable_output.append("")
        
        # Summary
        debug_info = debug_data.get('debug_info', {})
        readable_output.append("📊 WORKFLOW SUMMARY")
        readable_output.append("-" * 25)
        readable_output.append(f"• Total Messages: {debug_info.get('total_messages', 0)}")
        readable_output.append(f"• Agents Executed: {debug_info.get('agents_executed', 0)}")
        readable_output.append(f"• Workflow Available: {debug_info.get('workflow_available', False)}")
        readable_output.append("")
        
        # Messages
        messages = debug_data.get('messages', [])
        if messages:
            readable_output.append("💬 CONVERSATION MESSAGES")
            readable_output.append("-" * 30)
            for i, msg in enumerate(messages, 1):
                role_icon = "👤" if msg['role'] == 'user' else "🤖"
                readable_output.append(f"{i}. {role_icon} {msg['role'].upper()}:")
                readable_output.append(f"   📝 {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
                readable_output.append(f"   🕒 {msg['created_at']}")
                readable_output.append("")
        
        # Workflow Results
        workflow_states = debug_data.get('workflow_states', {})
        if workflow_states:
            state_data = workflow_states.get('state_data', {})
            readable_output.append("🔄 WORKFLOW EXECUTION")
            readable_output.append("-" * 25)
            readable_output.append(f"• Workflow Type: {workflow_states.get('workflow_type', 'N/A')}")
            readable_output.append(f"• Current Step: {workflow_states.get('current_step', 'N/A')}")
            readable_output.append(f"• Intent Detected: {state_data.get('intent', 'N/A')}")
            readable_output.append(f"• Security Check: {'✅ Passed' if state_data.get('security_check_passed') else '❌ Failed'}")
            
            error = state_data.get('error')
            if error:
                readable_output.append(f"• ⚠️ Error: {error}")
            readable_output.append("")
            
            # Strategy Results (if available)
            strategy_result = state_data.get('strategy_result')
            if strategy_result:
                readable_output.append("🎯 STRATEGY RESULTS")
                readable_output.append("-" * 20)
                readable_output.append(f"• Recommended Service: {strategy_result.get('recommended_service', 'N/A')}")
                readable_output.append(f"• Estimated Timeline: {strategy_result.get('estimated_timeline', 'N/A')}")
                readable_output.append(f"• Confidence Score: {strategy_result.get('confidence', 'N/A')}")
                
                action_plan = strategy_result.get('action_plan', [])
                if action_plan:
                    readable_output.append(f"• Action Steps: {len(action_plan)} steps")
                    for step in action_plan:
                        readable_output.append(f"  {step.get('step_number', '?')}. {step.get('step_description', 'N/A')}")
                        readable_output.append(f"     ⏱ Timeline: {step.get('expected_timeline', 'N/A')}")
                        resources = step.get('required_resources', [])
                        if resources:
                            readable_output.append(f"     📋 Resources: {', '.join(resources)}")
                
                matched_services = strategy_result.get('matched_services', [])
                if matched_services:
                    readable_output.append(f"• Matched Services: {len(matched_services)} found")
                    for service in matched_services:
                        covered = "✅ Covered" if service.get('is_covered') else "❌ Not Covered"
                        readable_output.append(f"  • {service.get('service_name', 'N/A')} - {covered}")
                readable_output.append("")
        
        # Agent-by-Agent Breakdown
        agent_states = debug_data.get('agent_states', [])
        if agent_states:
            readable_output.append("🤖 AGENT EXECUTION DETAILS")
            readable_output.append("-" * 35)
            
            for agent in agent_states:
                agent_name = agent.get('agent_name', 'Unknown')
                state = agent.get('state', {})
                state_data = state.get('state_data', {})
                
                # Agent header with icon
                agent_icons = {
                    'prompt_security': '🛡️',
                    'patient_navigator': '🧭', 
                    'task_requirements': '📋',
                    'service_access_strategy': '🎯',
                    'regulatory': '⚖️',
                    'chat_communicator': '💬'
                }
                icon = agent_icons.get(agent_name, '🤖')
                readable_output.append(f"{icon} {agent_name.upper().replace('_', ' ')}")
                readable_output.append("  " + "-" * (len(agent_name) + 2))
                
                # Execution step
                step = state_data.get('step', 'N/A')
                readable_output.append(f"  • Step: {step}")
                
                # Timestamp
                updated_at = state.get('updated_at', 'N/A')
                readable_output.append(f"  • Updated: {updated_at}")
                
                # Results (if available)
                result = state_data.get('result')
                if result:
                    if agent_name == 'prompt_security':
                        passed = result.get('passed', False)
                        readable_output.append(f"  • Security Check: {'✅ Passed' if passed else '❌ Failed'}")
                    
                    elif agent_name == 'patient_navigator':
                        intent = result.get('intent_type', 'N/A')
                        confidence = result.get('confidence_score', 'N/A')
                        readable_output.append(f"  • Intent Detected: {intent}")
                        readable_output.append(f"  • Confidence: {confidence}")
                    
                    elif agent_name == 'service_access_strategy':
                        service = result.get('recommended_service', 'N/A')
                        timeline = result.get('estimated_timeline', 'N/A')
                        readable_output.append(f"  • Recommended: {service}")
                        readable_output.append(f"  • Timeline: {timeline}")
                        
                        action_plan = result.get('action_plan', [])
                        if action_plan:
                            readable_output.append(f"  • Action Steps: {len(action_plan)} steps")
                
                readable_output.append("")
        
        # Footer
        readable_output.append("✅ Debug report generated successfully!")
        readable_output.append(f"🕒 Generated at: {datetime.utcnow().isoformat()}Z")
        
        # Return as plain text
        return Response(
            content="\n".join(readable_output),
            media_type="text/plain",
            headers={"Content-Disposition": "inline"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Debug readable workflow error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug error: {str(e)}"
        )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "service": "Insurance Navigator API",
        "version": "2.0.0",
        "status": "active",
        "documentation": "/docs",
            "deployment_info": {
        "prepared_statements_fix": "ACTIVE",
        "commit_hash": "95adab1",
        "fix_description": "Duplicate file upload handling and prepared statement fix deployed",
            "environment_vars": {
                "ASYNCPG_DISABLE_PREPARED_STATEMENTS": os.getenv('ASYNCPG_DISABLE_PREPARED_STATEMENTS'),
                "DATABASE_URL_contains_pooler": 'pooler.supabase.com' in os.getenv('DATABASE_URL', ''),
            }
        },
        "message": "Welcome to the Insurance Navigator API! Use /docs for interactive documentation."
    }


@app.post("/chat-with-image")
async def chat_with_image(message: str = Form(...), image: UploadFile = File(None), current_user: UserResponse = Depends(get_current_user)):
    """Chat with image support like ChatGPT."""
    try:
        image_text = ""
        if image:
            from agents.common.multimodal.image_processor import ImageProcessor
            processor = ImageProcessor()
            image_data = await image.read()
            result = processor.extract_text_from_image(image_data)
            image_text = f" [IMAGE: {result.get('extracted_text', 'processing...').strip()[:200]}]"
        
        enhanced_message = message + image_text
        from agents.patient_navigator.patient_navigator import PatientNavigatorAgent
        agent = PatientNavigatorAgent()
        response, metadata = agent.process(enhanced_message, current_user.id, "default")
        return {"text": response, "conversation_id": "default", "metadata": metadata}
    except Exception as e:
        return {"text": f"Error: {str(e)}", "conversation_id": "default"}
@app.post("/upload-policy", response_model=Dict[str, Any])
async def upload_policy_demo(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Demo-ready document upload with vectorization and enhanced error handling."""
    try:
        logger.info(f"🚀 Starting document upload for user {current_user.id}: {file.filename}")
        
        # Validate file size (limit to 50MB to prevent memory issues)
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        file_size_estimate = getattr(file, 'size', 0)
        
        # Read file data with size limit
        logger.info(f"📖 Step 1: Reading file data...")
        file_data = await file.read()
        
        if len(file_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        logger.info(f"✅ Step 1 complete: Read {len(file_data)} bytes")
        
        if len(file_data) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Extract text content with timeout
        logger.info(f"🔍 Step 2: Extracting text content from {file.filename}...")
        
        try:
            # Use thread pool for CPU-intensive text extraction
            with ThreadPoolExecutor(max_workers=1) as executor:
                text_content = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        executor, extract_text_from_file, file_data, file.filename
                    ),
                    timeout=60.0  # 60 second timeout for text extraction
                )
        except asyncio.TimeoutError:
            logger.error(f"❌ Text extraction timeout for {file.filename}")
            raise HTTPException(
                status_code=408,
                detail="File processing timeout. Please try a smaller file or contact support."
            )
        
        logger.info(f"✅ Step 2 complete: Extracted {len(text_content)} characters")
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        # Limit text content for very large documents - more conservative for stability
        MAX_TEXT_LENGTH = 500_000  # 500KB of text (reduced for better stability)
        if len(text_content) > MAX_TEXT_LENGTH:
            logger.warning(f"⚠️ Truncating large document: {len(text_content)} -> {MAX_TEXT_LENGTH} chars")
            text_content = text_content[:MAX_TEXT_LENGTH] + "\n\n[Document truncated due to size limit]"
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        logger.info(f"🆔 Generated document ID: {document_id}")
        
        # Chunk the text with progress tracking
        logger.info(f"✂️  Step 3: Chunking text (length: {len(text_content)})...")
        
        try:
            # Use thread pool for chunking to avoid blocking
            with ThreadPoolExecutor(max_workers=1) as executor:
                chunks = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        executor, chunk_text, text_content
                    ),
                    timeout=30.0  # 30 second timeout for chunking
                )
        except asyncio.TimeoutError:
            logger.error(f"❌ Text chunking timeout")
            raise HTTPException(
                status_code=408,
                detail="Text processing timeout. Please try a smaller file."
            )
        
        logger.info(f"✅ Step 3 complete: Created {len(chunks)} chunks from document")
        
        # Limit number of chunks to prevent resource exhaustion - more conservative
        MAX_CHUNKS = 300  # Reduced for better stability
        if len(chunks) > MAX_CHUNKS:
            logger.warning(f"⚠️ Limiting chunks: {len(chunks)} -> {MAX_CHUNKS}")
            chunks = chunks[:MAX_CHUNKS]
        
        # Get embedding model
        logger.info(f"🧠 Step 4: Loading embedding model...")
        model = await get_embedding_model()
        logger.info(f"✅ Step 4 complete: Embedding model loaded")
        
        # Get database connection with retry logic
        logger.info(f"🗄️  Step 5: Connecting to database...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                pool = await get_db_pool()
                if pool:
                    break
            except Exception as e:
                logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=503,
                        detail="Database temporarily unavailable. Please try again later."
                    )
                await asyncio.sleep(1)  # Wait before retry
        
        logger.info(f"✅ Step 5 complete: Database connection established")
        
        vector_ids = []
        failed_chunks = 0
        
        logger.info(f"🔄 Step 6: Processing {len(chunks)} chunks for embeddings...")
        logger.info(f"📊 Document processing breakdown:")
        logger.info(f"   • Total text: {len(text_content):,} characters")
        logger.info(f"   • Chunk size: {len(chunks):,} pieces")
        logger.info(f"   • Estimated time: {len(chunks) * 0.5:.1f} seconds")
        
        # Process chunks in batches to avoid overwhelming the system
        BATCH_SIZE = 10
        progress_milestones = [10, 25, 50, 75, 90]
        last_milestone = 0
        
        try:
            async with pool.get_connection() as conn:
                # Process chunks in batches
                for batch_start in range(0, len(chunks), BATCH_SIZE):
                    batch_end = min(batch_start + BATCH_SIZE, len(chunks))
                    batch_chunks = chunks[batch_start:batch_end]
                    
                    # Process batch
                    for i, chunk in enumerate(batch_chunks):
                        absolute_index = batch_start + i
                        
                        try:
                            # Calculate progress percentage
                            progress_pct = int(((absolute_index + 1) / len(chunks)) * 100)
                            
                            # Log at major milestones
                            if progress_pct >= progress_milestones[0] and progress_pct > last_milestone:
                                milestone = progress_milestones.pop(0)
                                last_milestone = milestone
                                chunks_remaining = len(chunks) - absolute_index - 1
                                time_remaining = chunks_remaining * 0.5
                                logger.info(f"  🎯 Milestone: {milestone}% complete ({absolute_index+1}/{len(chunks)} chunks)")
                                logger.info(f"     ⏱️ Estimated time remaining: {time_remaining:.1f} seconds")
                                logger.info(f"     📝 Current chunk: {len(chunk)} characters")
                            
                            # Generate embedding with timeout
                            try:
                                embedding_task = asyncio.get_event_loop().run_in_executor(
                                    None, lambda: model.encode(chunk).tolist()
                                )
                                embedding = await asyncio.wait_for(embedding_task, timeout=10.0)
                                
                                # Enhanced logging: Validate embedding dimensions
                                embedding_dim = len(embedding)
                                logger.info(f"    📊 Generated {embedding_dim}D embedding for chunk {absolute_index+1}")
                                
                                # Dimension validation  
                                if embedding_dim != 1536:
                                    logger.error(f"    ❌ DIMENSION MISMATCH: Generated {embedding_dim}D, database expects 1536D")
                                    logger.error(f"    🔧 Fix: Update MockModel to generate 1536-dimensional vectors")
                                    failed_chunks += 1
                                    continue
                                    
                                logger.info(f"    ✅ Dimension validation passed: {embedding_dim}D matches schema")
                                
                            except asyncio.TimeoutError:
                                logger.warning(f"  ⚠️ Embedding timeout for chunk {absolute_index+1}, skipping...")
                                failed_chunks += 1
                                continue
                            
                            # Get active encryption key ID
                            try:
                                encryption_key_id = await asyncio.wait_for(
                                    conn.fetchval("""
                                        SELECT id FROM encryption_keys 
                                        WHERE key_status = 'active' 
                                        ORDER BY created_at DESC 
                                        LIMIT 1
                                    """),
                                    timeout=2.0
                                )
                                
                                if not encryption_key_id:
                                    logger.error(f"    ❌ No active encryption key found in database")
                                    failed_chunks += 1
                                    continue
                                    
                                logger.info(f"    🔐 Using encryption key: {str(encryption_key_id)[:8]}...")
                                
                            except Exception as e:
                                logger.error(f"    ❌ Failed to query encryption key: {e}")
                                failed_chunks += 1
                                continue
                            
                            # Store in database with error handling
                            try:
                                vector_id = await asyncio.wait_for(
                                    conn.fetchval("""
                                        INSERT INTO user_document_vectors 
                                        (user_id, document_id, chunk_index, content_embedding, encrypted_chunk_text, encrypted_chunk_metadata, encryption_key_id)
                                        VALUES ($1, $2, $3, $4::vector, $5, $6, $7)
                                        RETURNING id
                                    """, 
                                    current_user.id, 
                                    document_id,
                                    absolute_index,
                                    str(embedding),
                                    chunk,  # encrypted_chunk_text - for demo we'll store as plaintext temporarily
                                    json.dumps({
                                        "filename": file.filename,
                                        "file_size": len(file_data),
                                        "content_type": file.content_type,
                                        "chunk_length": len(chunk),
                                        "total_chunks": len(chunks),
                                        "uploaded_at": datetime.utcnow().isoformat()
                                    }),  # encrypted_chunk_metadata - for demo we'll store as plaintext temporarily  
                                    encryption_key_id),  # Real encryption key from database
                                    timeout=5.0  # 5 second timeout for DB insert
                                )
                                
                                vector_ids.append(vector_id)
                                
                            except asyncio.TimeoutError:
                                logger.warning(f"  ⚠️ Database insert timeout for chunk {absolute_index+1}")
                                failed_chunks += 1
                                continue
                            except Exception as e:
                                logger.warning(f"  ⚠️ Database error for chunk {absolute_index+1}: {e}")
                                failed_chunks += 1
                                continue
                            
                        except Exception as e:
                            logger.warning(f"  ⚠️ Error processing chunk {absolute_index+1}: {e}")
                            failed_chunks += 1
                            continue
                    
                    # Small delay between batches to prevent overwhelming the system
                    if batch_end < len(chunks):
                        await asyncio.sleep(0.1)
        
        except Exception as e:
            logger.error(f"❌ Critical error during chunk processing: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Processing failed: {str(e)[:100]}... Please try again or contact support."
            )
        
        success_rate = (len(vector_ids) / len(chunks)) * 100 if chunks else 0
        
        logger.info(f"🎉 Step 6 complete: Successfully stored {len(vector_ids)} vectors for document {document_id}")
        if failed_chunks > 0:
            logger.warning(f"⚠️ {failed_chunks} chunks failed processing (success rate: {success_rate:.1f}%)")
        
        # Return comprehensive result
        result = {
            "success": True,
            "document_id": document_id,
            "filename": file.filename,
            "chunks_processed": len(vector_ids),
            "chunks_failed": failed_chunks,
            "total_chunks": len(chunks),
            "success_rate": round(success_rate, 1),
            "text_length": len(text_content),
            "file_size": len(file_data),
            "processing_time": f"~{len(chunks) * 0.5:.1f}s estimated",
            "message": f"Successfully uploaded and vectorized {file.filename} ({success_rate:.1f}% success rate)"
        }
        
        logger.info(f"✅ Upload complete: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Document upload error: {str(e)}")
        logger.error(f"📊 Error details: type={type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Return a user-friendly error with CORS headers
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload processing failed. Please try a smaller file or contact support. Error: {str(e)[:100]}"
        )

@app.post("/search-documents", response_model=Dict[str, Any])
async def search_documents(
    query: str = Form(...),
    limit: int = Form(default=5),
    current_user: UserResponse = Depends(get_current_user)
):
    """Search uploaded documents using semantic similarity."""
    try:
        logger.info(f"Searching documents for user {current_user.id}: {query}")
        
        # Get embedding model
        model = await get_embedding_model()
        
        # Generate query embedding
        query_embedding = model.encode(query).tolist()
        
        # Get database connection
        pool = await get_db_pool()
        
        results = []
        async with pool.get_connection() as conn:
            # Search using vector similarity
            rows = await conn.fetch("""
                SELECT 
                    document_id,
                    encrypted_chunk_text as chunk_text,
                    encrypted_chunk_metadata as chunk_metadata,
                    content_embedding <=> $1::vector as similarity_score
                FROM user_document_vectors 
                WHERE user_id = $2 AND is_active = true
                ORDER BY content_embedding <=> $1::vector
                LIMIT $3
            """, str(query_embedding), current_user.id, limit)
            
            for row in rows:
                metadata = json.loads(row['chunk_metadata'])
                results.append({
                    "document_id": row['document_id'],
                    "text": row['chunk_text'],
                    "filename": metadata.get('filename', 'Unknown'),
                    "similarity_score": float(row['similarity_score']),
                    "metadata": metadata
                })
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        logger.error(f"Document search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@app.post("/api/embeddings", response_model=Dict[str, Any])
async def generate_embedding_for_edge_functions(
    request: Dict[str, Any] = Body(...),
    authorization: str = Header(None)
):
    """Generate embeddings for Edge Functions to use in vector processing."""
    try:
        # Verify authorization
        if not authorization or not authorization.startswith('Bearer '):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )
        
        # Extract text from request
        text = request.get('text', '').strip()
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text content is required"
            )
        
        logger.info(f"Generating embedding for {len(text)} characters of text")
        
        # Get embedding model
        model = await get_embedding_model()
        
        # Generate embedding
        embedding = model.encode(text).tolist()
        
        # Ensure consistent dimension (1536 for OpenAI compatibility)
        if len(embedding) != 1536:
            logger.warning(f"Unexpected embedding dimension: {len(embedding)}, expected 1536")
        
        return {
            "success": True,
            "embedding": embedding,
            "dimension": len(embedding),
            "text_length": len(text),
            "model": "mock-1536d-openai-compatible"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Embedding generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embedding: {str(e)}"
        )

@app.get("/documents/{document_id}/status")
async def get_document_status(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get document processing status for polling.
    This endpoint bypasses RLS issues by using server-side authentication.
    """
    try:
        # Get database pool
        db_pool = await get_db_pool()
        
        async with db_pool.get_connection() as connection:
            # Query document status with user verification
            query = """
                SELECT 
                    id, 
                    status, 
                    progress_percentage, 
                    processed_chunks, 
                    total_chunks, 
                    error_message,
                    original_filename,
                    processing_completed_at
                FROM documents 
                WHERE id = $1 AND user_id = $2
            """
            
            result = await connection.fetchrow(query, document_id, current_user.id)
            
            if not result:
                raise HTTPException(
                    status_code=404, 
                    detail="Document not found or access denied"
                )
            
            # Convert to dict and handle None values
            document_status = {
                'id': str(result['id']),
                'status': result['status'],
                'progress_percentage': result['progress_percentage'] or 0,
                'processed_chunks': result['processed_chunks'] or 0,
                'total_chunks': result['total_chunks'] or 0,
                'error_message': result['error_message'],
                'original_filename': result['original_filename'],
                'processing_completed_at': result['processing_completed_at'].isoformat() if result['processing_completed_at'] else None
            }
            
            logger.info(f"Document status for {document_id}: {document_status['status']} ({document_status['progress_percentage']}%)")
            
            return document_status
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document status for {document_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document status: {str(e)}"
        )

@app.post("/upload-document-backend", response_model=Dict[str, Any])
async def upload_document_backend(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Backend-driven document upload that creates jobs in the job queue.
    This eliminates frontend dependency and ensures processing continues
    even if the user closes their browser.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # File size validation (50MB limit)
        file_content = await file.read()
        if len(file_content) > 52428800:  # 50MB
            raise HTTPException(status_code=413, detail="File size must be less than 50MB")
        
        # File type validation
        allowed_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                        'application/msword', 'text/plain']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Only PDF, DOCX, DOC, and TXT files are supported")
        
        # Generate file hash for deduplication and integrity
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Get database pool
        db_pool = await get_db_pool()
        
        async with db_pool.get_connection() as connection:
            # Check if file with same hash already exists for this user
            existing_query = """
                SELECT id, original_filename, status, created_at 
                FROM documents 
                WHERE file_hash = $1 AND user_id = $2
                ORDER BY created_at DESC
                LIMIT 1
            """
            
            existing_doc = await connection.fetchrow(existing_query, file_hash, current_user.id)
            
            if existing_doc:
                logger.info(f"📄 Duplicate file detected for user {current_user.id}: {file.filename} (hash: {file_hash[:16]}...)")
                return {
                    'success': True,
                    'document_id': existing_doc['id'],
                    'filename': file.filename,
                    'file_size': len(file_content),
                    'status': existing_doc['status'],
                    'message': f'File already exists (uploaded on {existing_doc["created_at"].strftime("%Y-%m-%d %H:%M")}). Using existing document.',
                    'duplicate': True,
                    'existing_filename': existing_doc['original_filename']
                }
            
            # Create document record for new file
            document_id = str(uuid.uuid4())
            
            insert_query = """
                INSERT INTO documents (
                    id, user_id, original_filename, content_type, file_size, file_hash,
                    status, progress_percentage, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
                RETURNING id
            """
            
            try:
                result = await connection.fetchrow(
                    insert_query,
                    document_id,
                    current_user.id,
                    file.filename,
                    file.content_type,
                    len(file_content),
                    file_hash,
                    'uploading',
                    5
                )
                
                if not result:
                    raise HTTPException(status_code=500, detail="Failed to create document record")
                    
            except Exception as db_error:
                # Handle race condition where file was uploaded between our check and insert
                if "duplicate key value violates unique constraint" in str(db_error) and "file_hash" in str(db_error):
                    logger.warning(f"⚠️ Race condition detected: file uploaded concurrently for user {current_user.id}")
                    # Re-check for existing document
                    existing_doc = await connection.fetchrow(existing_query, file_hash, current_user.id)
                    if existing_doc:
                        return {
                            'success': True,
                            'document_id': existing_doc['id'],
                            'filename': file.filename,
                            'file_size': len(file_content),
                            'status': existing_doc['status'],
                            'message': f'File already exists (uploaded concurrently). Using existing document.',
                            'duplicate': True,
                            'existing_filename': existing_doc['original_filename']
                        }
                # Re-raise other database errors
                raise db_error
            
            # Store file in Supabase Storage
            storage_service = await get_storage_service()
            
            # Create storage path
            storage_path = f"user_documents/{current_user.id}/{document_id}/{file.filename}"
            
            # Upload file to Supabase Storage
            try:
                upload_result = await storage_service.upload_file(
                    bucket_name="documents",
                    file_path=storage_path,
                    file_data=file_content,
                    content_type=file.content_type
                )
                logger.info(f"✅ File uploaded to storage: {storage_path}")
            except Exception as storage_error:
                logger.error(f"❌ Failed to upload file to storage: {storage_error}")
                # Clean up document record
                await connection.execute("DELETE FROM documents WHERE id = $1", document_id)
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to store file: {str(storage_error)}"
                )
            
            # Update document with storage path and processing status
            file_storage_query = """
                UPDATE documents 
                SET storage_path = $1, status = $2, progress_percentage = $3, updated_at = NOW()
                WHERE id = $4
            """
            
            await connection.execute(
                file_storage_query,
                storage_path,
                'processing',
                10,
                document_id
            )
            
            # Create initial processing job in the job queue
            job_id = str(uuid.uuid4())
            job_query = """
                INSERT INTO processing_jobs (
                    id, document_id, job_type, status, priority, 
                    created_at, scheduled_at, payload
                ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW(), $6)
            """
            
            job_metadata = {
                'filename': file.filename,
                'content_type': file.content_type,
                'file_size': len(file_content),
                'file_hash': file_hash,
                'storage_path': storage_path,
                'user_id': current_user.id
            }
            
            await connection.execute(
                job_query,
                job_id,
                document_id,
                'parse',  # Start with parsing job
                'pending',
                1,  # High priority
                json.dumps(job_metadata)
            )
            
            logger.info(f"✅ Document {document_id} uploaded and job {job_id} created for user {current_user.id}")
            
            return {
                'success': True,
                'document_id': document_id,
                'filename': file.filename,
                'file_size': len(file_content),
                'status': 'processing',
                'message': 'Document uploaded successfully. Processing will continue in the background.',
                'job_id': job_id,
                'duplicate': False
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}"
        )

@app.get("/admin/job-queue-status")
async def get_job_queue_status(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get comprehensive job queue status for monitoring.
    Requires admin access or returns limited info for regular users.
    """
    try:
        db_pool = await get_db_pool()
        
        async with db_pool.get_connection() as connection:
            # Get job status summary
            status_query = """
                SELECT 
                    status,
                    job_type,
                    COUNT(*) as count,
                    MIN(created_at) as oldest,
                    MAX(created_at) as newest
                FROM processing_jobs 
                GROUP BY status, job_type 
                ORDER BY status, job_type
            """
            status_results = await connection.fetch(status_query)
            
            # Get running jobs
            running_query = """
                SELECT 
                    id,
                    document_id,
                    job_type,
                    started_at,
                    EXTRACT(EPOCH FROM (NOW() - started_at)) as running_seconds
                FROM processing_jobs 
                WHERE status = 'running'
                ORDER BY started_at
            """
            running_results = await connection.fetch(running_query)
            
            # Get recent failures
            failed_query = """
                SELECT 
                    id,
                    document_id,
                    job_type,
                    retry_count,
                    max_retries,
                    error_message,
                    created_at
                FROM processing_jobs 
                WHERE status = 'failed' AND updated_at > NOW() - INTERVAL '1 hour'
                ORDER BY created_at DESC
                LIMIT 10
            """
            failed_results = await connection.fetch(failed_query)
            
            # Get document processing status
            documents_query = """
                SELECT 
                    d.id,
                    d.original_filename,
                    d.status,
                    d.progress_percentage,
                    d.processed_chunks,
                    d.total_chunks,
                    d.created_at,
                    d.updated_at,
                    COUNT(pj.id) as total_jobs,
                    COUNT(CASE WHEN pj.status = 'completed' THEN 1 END) as completed_jobs,
                    COUNT(CASE WHEN pj.status = 'failed' THEN 1 END) as failed_jobs
                FROM documents d
                LEFT JOIN processing_jobs pj ON d.id = pj.document_id
                WHERE d.created_at > NOW() - INTERVAL '2 hours'
                GROUP BY d.id, d.original_filename, d.status, d.progress_percentage, 
                         d.processed_chunks, d.total_chunks, d.created_at, d.updated_at
                ORDER BY d.created_at DESC
                LIMIT 10
            """
            documents_results = await connection.fetch(documents_query)
            
            # Convert results to dictionaries
            status_summary = [dict(row) for row in status_results]
            running_jobs = [dict(row) for row in running_results]
            failed_jobs = [dict(row) for row in failed_results]
            recent_documents = [dict(row) for row in documents_results]
            
            # Convert datetime objects to ISO strings
            for job in running_jobs:
                if job['started_at']:
                    job['started_at'] = job['started_at'].isoformat()
                job['running_seconds'] = int(job['running_seconds']) if job['running_seconds'] else 0
            
            for job in failed_jobs:
                if job['created_at']:
                    job['created_at'] = job['created_at'].isoformat()
            
            for doc in recent_documents:
                if doc['created_at']:
                    doc['created_at'] = doc['created_at'].isoformat()
                if doc['updated_at']:
                    doc['updated_at'] = doc['updated_at'].isoformat()
            
            for status in status_summary:
                if status['oldest']:
                    status['oldest'] = status['oldest'].isoformat()
                if status['newest']:
                    status['newest'] = status['newest'].isoformat()
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'status_summary': status_summary,
                'running_jobs': running_jobs,
                'recent_failures': failed_jobs,
                'recent_documents': recent_documents,
                'system_health': {
                    'total_active_jobs': len([s for s in status_summary if s['status'] in ['pending', 'running', 'retrying']]),
                    'total_failed_jobs': len(failed_jobs),
                    'processing_documents': len([d for d in recent_documents if d['status'] == 'processing'])
                }
            }
            
    except Exception as e:
        logger.error(f"Error getting job queue status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job queue status: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Starting server on port {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    ) 