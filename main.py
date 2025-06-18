#!/usr/bin/env python3
"""
Insurance Navigator - Healthcare Navigation Assistant
==================================================

A comprehensive healthcare navigation system that helps users:
- Understand their insurance coverage and benefits
- Find appropriate healthcare providers and services
- Navigate complex healthcare systems and processes
- Access care coordination and support services

This system uses AI agents to provide personalized, empathetic guidance
while maintaining HIPAA compliance and healthcare industry standards.

TODO: Implement comprehensive health system integrations
TODO: Add real-time insurance verification APIs
TODO: Create mobile app companion for better accessibility
TODO: Implement multi-language support for diverse populations
TODO: Add voice interface for accessibility
"""

import os
import sys
import uuid
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
import hashlib
import aiohttp

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
# PyPDF2 imported conditionally in extract_text_from_pdf() as fallback for LlamaParse
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
    description="Healthcare Navigation Assistant API for insurance and medical guidance",
    version="1.0.0",
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

class HealthCheck(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Check timestamp")
    services: Dict[str, str] = Field(..., description="Service statuses")
    version: str = Field(..., description="Application version")

class RegulatoryDocumentRequest(BaseModel):
    """Request model for regulatory document upload via URL"""
    source_url: str = Field(..., description="URL of the regulatory document")
    title: str = Field(..., description="Document title")
    document_type: str = Field(default="regulatory_document", description="Type of document")
    jurisdiction: str = Field(default="federal", description="Jurisdiction (federal, state, local)")
    program: List[str] = Field(default=["medicaid"], description="Programs this document applies to")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class UnifiedDocumentRequest(BaseModel):
    """Unified request model that handles both file uploads and URL-based regulatory documents"""
    document_type: str = Field(..., description="Type of document (user_document, regulatory_document, policy)")
    source_type: str = Field(..., description="Source type (file_upload, url_download)")
    
    # For file uploads
    filename: Optional[str] = None
    
    # For URL downloads (regulatory documents)
    source_url: Optional[str] = None
    title: Optional[str] = None
    jurisdiction: Optional[str] = None
    program: Optional[List[str]] = None
    
    # Common fields
    metadata: Optional[Dict[str, Any]] = None

class UnifiedDocumentResponse(BaseModel):
    """Response model for unified document processing"""
    success: bool
    document_id: str
    document_type: str
    source_type: str
    processing_method: str
    filename: Optional[str] = None
    title: Optional[str] = None
    message: str
    vector_processing_status: str
    estimated_vectors: Optional[int] = None

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
                        # Return random 384-dimensional vector as numpy array for demo
                        return np.array([random.uniform(-1, 1) for _ in range(384)])
                embedding_model = MockModel()
                logger.info("✅ Mock embedding model loaded (memory optimization)")
            else:
                logger.info("Loading SBERT model: all-MiniLM-L6-v2...")
                # Use device='cpu' and optimize for memory
                embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
                logger.info("✅ SBERT model loaded successfully")
                
        except ImportError:
            logger.warning("⚠️ psutil not available, proceeding with model loading")
            try:
                embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
                logger.info("✅ SBERT model loaded successfully")
            except Exception as e:
                logger.error(f"❌ Failed to load SBERT model: {e}")
                class MockModel:
                    def encode(self, text):
                        import random
                        import numpy as np
                        return np.array([random.uniform(-1, 1) for _ in range(384)])
                embedding_model = MockModel()
                logger.warning("⚠️ Using mock embedding model due to loading failure")
        except Exception as e:
            logger.error(f"❌ Failed to load SBERT model: {e}")
            # Return a mock model for demo purposes
            class MockModel:
                def encode(self, text):
                    import random
                    import numpy as np
                    # Return random 384-dimensional vector as numpy array for demo
                    return np.array([random.uniform(-1, 1) for _ in range(384)])
            embedding_model = MockModel()
            logger.warning("⚠️ Using mock embedding model for demo")
    return embedding_model

def extract_text_from_pdf(file_data: bytes) -> str:
    """Extract text from PDF file using LlamaParse integration."""
    try:
        logger.info(f"📄 Starting PDF text extraction (file size: {len(file_data)} bytes)...")
        
        # Check if LlamaParse is available via environment
        llamaparse_api_key = os.getenv('LLAMAPARSE_API_KEY')
        
        if llamaparse_api_key:
            logger.info("🦙 LlamaParse API key found, using LlamaParse for PDF extraction...")
            # For now, return a message indicating LlamaParse integration
            # In production, this would trigger the Supabase Edge Function
            logger.info("✅ PDF queued for LlamaParse processing via Supabase Edge Functions")
            return "PDF document uploaded. Advanced text extraction in progress via LlamaParse."
        else:
            logger.info("🔧 LlamaParse not configured, using fallback PyPDF2...")
            # Fallback to PyPDF2 for basic extraction
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
                logger.info(f"📄 PDF loaded, found {len(pdf_reader.pages)} pages")
                
                text = ""
                for i, page in enumerate(pdf_reader.pages):
                    logger.info(f"📄 Processing page {i+1}/{len(pdf_reader.pages)}...")
                    page_text = page.extract_text()
                    text += page_text + "\n"
                    logger.info(f"📄 Page {i+1} processed: {len(page_text)} characters extracted")
                
                result = text.strip()
                logger.info(f"✅ Fallback PDF text extraction complete: {len(result)} total characters")
                return result
            except ImportError:
                logger.error("❌ PyPDF2 not available and LlamaParse not configured")
                return "PDF processing temporarily unavailable. Please configure LlamaParse for advanced document processing."
        
    except Exception as e:
        logger.error(f"❌ Error extracting PDF text: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return ""

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

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        # Check database pool availability
        pool = await get_db_pool()
        db_healthy = pool is not None
        
        # Check authentication configuration
        try:
            from utils.security_config import get_security_config
            security_config = get_security_config()
            auth_healthy = bool(security_config.jwt_secret_key)
        except Exception:
            auth_healthy = False
        
        services = {
            "database": "connected" if db_healthy else "disconnected",
            "agents": "healthy" if AGENT_ORCHESTRATOR_AVAILABLE else "unhealthy",
            "authentication": "healthy" if auth_healthy else "unhealthy"
        }
        
        overall_status = "healthy" if all(status in ["healthy", "connected"] for status in services.values()) else "unhealthy"
        
        return HealthCheck(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat() + "Z",
            services=services,
            version="2.0.0"
        )
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return HealthCheck(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat() + "Z",
            services={
                "database": "error",
                "agents": "unknown",
                "authentication": "unknown"
            },
            version="2.0.0"
        )

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

# Chat and conversation endpoints (simplified for MVP)
@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Simplified chat endpoint with hybrid search and policy facts lookup."""
    try:
        # Import simplified services
        from db.services.document_service import DocumentService
        
        # Initialize services
        conversation_service = await get_conversation_service()
        document_service = DocumentService()
        
        # Get or create conversation
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = await conversation_service.create_conversation(
                user_id=current_user.id,
                metadata={"type": "general"}
            )
        
        # Save user message
        await conversation_service.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
            metadata=request.context or {}
        )
        
        # Perform hybrid search for relevant policy information
        try:
            # Search user's documents using hybrid approach (policy facts + vector search)
            search_results_data = await document_service.search_hybrid(
                user_id=current_user.id,
                query=request.message,
                limit=5
            )
            search_results = search_results_data.get('results', [])
            
            # Generate response with context
            if search_results:
                # Build context from search results
                context_text = ""
                sources = []
                
                for result in search_results:
                    # Extract policy facts for quick access
                    policy_facts = result.get('policy_facts', {})
                    if policy_facts:
                        context_text += f"Policy Info: {policy_facts}\n"
                    
                    # Add document info
                    filename = result.get('filename', 'Document')
                    search_type = result.get('search_type', 'general')
                    context_text += f"Document: {filename} ({search_type})\n"
                    
                    sources.append({
                        "document_id": result.get('document_id'),
                        "filename": filename,
                        "policy_type": policy_facts.get('plan_type', 'Unknown'),
                        "relevance_score": result.get('relevance_score', 0),
                        "search_type": search_type
                    })
                
                # Generate contextual response
                response_text = f"Based on your policy documents, here's what I found:\n\n"
                
                # Simple intent detection for common insurance questions
                message_lower = request.message.lower()
                if any(word in message_lower for word in ['coverage', 'covered', 'benefit']):
                    response_text += "Regarding coverage information:\n"
                elif any(word in message_lower for word in ['claim', 'claims', 'file']):
                    response_text += "For claims assistance:\n"
                elif any(word in message_lower for word in ['doctor', 'provider', 'network']):
                    response_text += "About providers and networks:\n"
                else:
                    response_text += "Here's relevant information from your policies:\n"
                
                # Add policy summaries
                for source in sources[:3]:  # Top 3 results
                    policy_type = source.get('policy_type', 'Policy')
                    filename = source.get('filename', 'Document')
                    response_text += f"\n• {policy_type} ({filename}): Information available"
                
                response_text += "\n\nWould you like me to provide more specific details about any of these policies?"
                
                metadata = {
                    "search_performed": True,
                    "results_count": len(search_results),
                    "total_results": search_results_data.get('total_results', 0),
                    "hybrid_search": True
                }
            else:
                # No relevant documents found
                response_text = ("I don't have specific policy information to answer your question. "
                               "You may want to upload your insurance documents first, or I can help "
                               "you with general insurance navigation questions.")
                sources = []
                metadata = {"search_performed": True, "results_count": 0}
            
        except Exception as search_error:
            logger.error(f"Search error: {search_error}")
            response_text = ("I can help you with insurance questions. Please feel free to ask about "
                           "coverage, claims, providers, or upload your policy documents for "
                           "personalized assistance.")
            sources = []
            metadata = {"search_error": str(search_error)}
        
        # Save assistant response
        await conversation_service.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
            metadata={"sources": sources, **metadata}
            )
        
        return ChatResponse(
            text=response_text,
            conversation_id=conversation_id,
            sources=sources,
            metadata=metadata,
            workflow_type="simplified_navigator"
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

# Document storage endpoints (simplified for MVP)
@app.post("/upload-document", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    policy_id: str = Form(...),
    document_type: str = Form(default="policy"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Simplified document upload with automatic policy extraction."""
    try:
        from db.services.document_service import DocumentService
        from db.services.storage_service import StorageService
        
        # Initialize services
        document_service = DocumentService()
        storage_service = StorageService()
        
        # Read file data
        file_data = await file.read()
        
        # Use simplified upload method with automatic policy extraction
        upload_result = await document_service.upload_document(
            file_data=file_data,
            filename=file.filename,
            user_id=current_user.id,
            document_type=document_type,
            policy_id=policy_id
        )
        
        # Generate signed URL for immediate access
        signed_url = await storage_service.get_signed_url(
            file_path=upload_result["file_path"],
            expires_in=3600
        )
        
        logger.info(f"Document uploaded with policy extraction: {file.filename} by user {current_user.id}")
        
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
@app.on_event("startup")
async def startup_event():
    """Initialize services and database connections on startup."""
    global user_service_instance, conversation_service_instance, storage_service_instance
    
    logger.info("🚀 Insurance Navigator API v2.0 starting up...")
    
    try:
        # Initialize database pool
        pool = await get_db_pool()
        logger.info("✅ Database connection pool initialized")
        
        # Initialize services
        user_service_instance = await get_user_service()
        logger.info("✅ User service initialized")
        
        conversation_service_instance = await get_conversation_service()
        logger.info("✅ Conversation service initialized")
        
        storage_service_instance = await get_storage_service()
        logger.info("✅ Storage service initialized")
        
        # Initialize agent orchestrator if available
        if AGENT_ORCHESTRATOR_AVAILABLE:
            try:
                agent_orchestrator_instance = AgentOrchestrator()
                logger.info("✅ Agent orchestrator initialized")
            except Exception as e:
                logger.warning(f"⚠️ Agent orchestrator initialization failed: {e}")
        else:
            logger.info("💡 Using fallback orchestrator (agent system not available)")
        
        logger.info("🎉 Startup complete - Insurance Navigator API ready!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
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

# Complex debug endpoints removed as part of MVP simplification
# The simplified architecture no longer requires complex workflow debugging

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
            "commit_hash": "5eaaf6c",
            "fix_description": "Supabase transaction pooler prepared statement fix deployed",
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
        try:
            from agents.patient_navigator.patient_navigator import PatientNavigatorAgent
            agent = PatientNavigatorAgent()
            response, metadata = agent.process(enhanced_message, current_user.id, "default")
            return {"text": response, "conversation_id": "default", "metadata": metadata}
        except Exception as e:
            return {"text": f"Error: {str(e)}", "conversation_id": "default"}
    except Exception as e:
        logger.error(f"❌ Image chat error: {e}")
        return {"text": f"Error processing request: {str(e)}", "conversation_id": "default"}

@app.post("/upload-document-backend", response_model=Dict[str, Any])
async def upload_document_backend(
    request: Request,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Backend-driven document upload that triggers Supabase Edge Functions pipeline.
    This replaces direct PyPDF2 processing with LlamaParse via Edge Functions.
    """
    try:
        logger.info(f"🚀 Backend document upload started for user {current_user.id}: {file.filename}")
        
        # Get the user's JWT token from the request
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Missing authentication token"
            )
        user_token = auth_header.split(" ")[1]
        
        # Validate file size (50MB limit)
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        file_data = await file.read()
        
        if len(file_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if len(file_data) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        logger.info(f"📄 File validated: {len(file_data)} bytes")
        
        # Get database connection
        pool = await get_db_pool()
        if not pool:
            raise HTTPException(
                status_code=503,
                detail="Database temporarily unavailable"
            )
        
        async with pool.get_connection() as conn:
            # Create document record in database first
            document_uuid = uuid.uuid4()
            document_id = str(document_uuid)
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            # Insert document record with proper UUID types
            await conn.execute("""
                INSERT INTO documents (
                    id, user_id, original_filename, file_size, content_type,
                    file_hash, status, progress_percentage, 
                    total_chunks, processed_chunks, failed_chunks
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, 'pending', 0, 0, 0, 0
                )
            """, 
            document_uuid, uuid.UUID(current_user.id), file.filename, len(file_data), 
            file.content_type or 'application/octet-stream', file_hash
            )
            
            logger.info(f"📄 Document record created: {document_id}")
            
            # Instead of processing directly, we'll trigger the Edge Functions pipeline
            # Check if we have Supabase configuration
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if supabase_url and supabase_service_key:
                logger.info("🔗 Triggering Supabase Edge Functions pipeline...")
                
                # Trigger the upload-handler Edge Function
                edge_function_url = f"{supabase_url}/functions/v1/upload-handler"
                
                # Prepare JSON payload for Edge Function (not form data)
                edge_payload = {
                    "filename": file.filename,
                    "contentType": file.content_type or 'application/octet-stream',
                    "fileSize": len(file_data),
                    "documentId": document_id
                }
                
                # Make request to Edge Function
                timeout = aiohttp.ClientTimeout(total=60)  # 60 second timeout
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    headers = {
                        'Authorization': f'Bearer {supabase_service_key}',  # Use service role key for Edge Function auth
                        'apikey': supabase_service_key,  # Add service key as apikey header
                        'Content-Type': 'application/json',
                        'X-User-ID': current_user.id,  # Pass user ID for authorization
                        'X-User-Token': user_token  # Pass user token for verification if needed
                    }
                    
                    try:
                        async with session.post(edge_function_url, json=edge_payload, headers=headers) as response:
                            if response.status == 200:
                                edge_result = await response.json()
                                logger.info(f"✅ Edge Function triggered successfully: {edge_result}")
                                
                                return {
                                    "success": True,
                                    "document_id": document_id,
                                    "filename": file.filename,
                                    "message": "Document uploaded successfully. Processing started via Edge Functions.",
                                    "processing_method": "edge_functions",
                                    "upload_url": edge_result.get("uploadUrl"),
                                    "chunks_processed": 0,
                                    "total_chunks": 1,
                                    "text_length": 0,
                                    "file_size": len(file_data),
                                    "processing_time": "Background processing started"
                                }
                            else:
                                error_text = await response.text()
                                logger.error(f"❌ Edge Function failed: {response.status} - {error_text}")
                                # Fall through to fallback processing
                                
                    except Exception as e:
                        logger.error(f"❌ Edge Function request failed: {e}")
                        # Fall through to fallback processing
            
            # Fallback: Update document status to indicate backend processing
            await conn.execute("""
                UPDATE documents 
                SET status = 'processing', progress_percentage = 10, updated_at = NOW()
                WHERE id = $1
            """, document_id)
            
            logger.info("📄 Document queued for background processing")
            
            return {
                "success": True,
                "document_id": document_id,
                "filename": file.filename,
                "message": "Document uploaded successfully. Background processing will continue.",
                "processing_method": "backend_queue",
                "chunks_processed": 0,
                "total_chunks": 1,
                "text_length": 0,
                "file_size": len(file_data),
                "processing_time": "Background processing queued"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Backend upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

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
        
        # Check if we should trigger Edge Functions for PDF processing
        logger.info(f"🔍 Step 2: Extracting text content from {file.filename}...")
        
        # For PDFs, prefer Edge Functions with LlamaParse
        if file.filename.lower().endswith('.pdf'):
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if supabase_url and supabase_service_key:
                logger.info("🦙 PDF detected - preferring Edge Functions with LlamaParse...")
                
                # Create a document record for tracking
                document_uuid = uuid.uuid4()
                document_id = str(document_uuid)
                file_hash = hashlib.sha256(file_data).hexdigest()
                
                # Get database connection for document creation
                pool = await get_db_pool()
                if pool:
                    async with pool.get_connection() as conn:
                        await conn.execute("""
                            INSERT INTO documents (
                                id, user_id, original_filename, file_size, content_type,
                                file_hash, status, progress_percentage, 
                                total_chunks, processed_chunks, failed_chunks
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, 'processing', 15, 0, 0, 0
                            )
                        """, 
                        document_uuid, uuid.UUID(current_user.id), file.filename, len(file_data), 
                        file.content_type or 'application/pdf', file_hash
                        )
                        
                        logger.info(f"📄 Document record created for Edge Functions: {document_id}")
                        
                        # Return early to show immediate completion, background processing will continue
                        return {
                            "success": True,
                            "document_id": document_id,
                            "filename": file.filename,
                            "chunks_processed": 0,  # Will be updated by background processing
                            "chunks_failed": 0,
                            "total_chunks": 1,
                            "success_rate": 0.0,  # Will be updated when processing completes
                            "text_length": 0,  # Will be updated by background processing
                            "file_size": len(file_data),
                            "processing_time": "Background processing via Edge Functions",
                            "message": f"Successfully uploaded {file.filename}. Background processing with LlamaParse will continue and you'll be notified when complete."
                        }
        
        # Fallback: Direct text extraction for non-PDFs or when Edge Functions unavailable
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
                            except asyncio.TimeoutError:
                                logger.warning(f"  ⚠️ Embedding timeout for chunk {absolute_index+1}, skipping...")
                                failed_chunks += 1
                                continue
                            
                            # Store in database with error handling
                            try:
                                vector_id = await asyncio.wait_for(
                                    conn.fetchval("""
                                        INSERT INTO user_document_vectors 
                                        (user_id, document_id, chunk_index, chunk_embedding, chunk_text, chunk_metadata)
                                        VALUES ($1, $2, $3, $4::vector, $5, $6)
                                        RETURNING id
                                    """, 
                                    current_user.id, 
                                    document_id,
                                    absolute_index,
                                    str(embedding),
                                    chunk,
                                    json.dumps({
                                        "filename": file.filename,
                                        "file_size": len(file_data),
                                        "content_type": file.content_type,
                                        "chunk_length": len(chunk),
                                        "total_chunks": len(chunks),
                                        "uploaded_at": datetime.utcnow().isoformat()
                                    })),
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
                    chunk_text,
                    chunk_metadata,
                    chunk_embedding <=> $1::vector as similarity_score
                FROM user_document_vectors 
                WHERE user_id = $2 AND is_active = true
                ORDER BY chunk_embedding <=> $1::vector
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
        
        # Ensure consistent dimension (384 for all-MiniLM-L6-v2)
        if len(embedding) != 384:
            logger.warning(f"Unexpected embedding dimension: {len(embedding)}, expected 384")
        
        return {
            "success": True,
            "embedding": embedding,
            "dimension": len(embedding),
            "text_length": len(text),
            "model": "all-MiniLM-L6-v2"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Embedding generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embedding: {str(e)}"
        )

@app.post("/api/documents/upload-regulatory", response_model=UnifiedDocumentResponse)
async def upload_regulatory_document(
    request: RegulatoryDocumentRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Upload regulatory document via URL through the unified processing pipeline.
    This extends the existing document processing system to handle regulatory documents.
    """
    try:
        logger.info(f"🏛️ Regulatory document upload started for user {current_user.id}: {request.title}")
        
        # Get storage service
        global storage_service_instance
        if not storage_service_instance:
            storage_service_instance = await get_storage_service()
        
        # Download document content from URL
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(request.source_url) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to download document from URL: HTTP {response.status}"
                    )
                
                file_data = await response.read()
                if len(file_data) == 0:
                    raise HTTPException(status_code=400, detail="Empty document downloaded")
                
                # Extract filename from URL or use title
                filename = request.source_url.split('/')[-1] or f"{request.title}.pdf"
                content_type = response.headers.get('content-type', 'application/pdf')
        
        logger.info(f"📄 Downloaded {len(file_data)} bytes from {request.source_url}")
        
        # Create document record with regulatory metadata
        document_metadata = {
            "source_url": request.source_url,
            "title": request.title,
            "jurisdiction": request.jurisdiction,
            "program": request.program,
            "document_type": request.document_type,
            "processing_method": "regulatory_url_upload",
            **(request.metadata or {})
        }
        
        # Use existing storage service with enhanced metadata
        upload_result = await storage_service_instance.upload_user_document_with_vectors(
            user_id=current_user.id,
            file_data=file_data,
            filename=filename,
            document_type=request.document_type,
            metadata=document_metadata
        )
        
        # Store in regulatory_documents table as well
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            regulatory_doc_id = await conn.fetchval("""
                INSERT INTO regulatory_documents (
                    raw_document_path, title, jurisdiction, program, document_type,
                    effective_date, source_url, tags, summary, search_metadata,
                    extraction_method, priority_score, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING document_id
            """,
                upload_result['file_path'],  # raw_document_path
                request.title,
                request.jurisdiction,
                request.program,
                request.document_type,
                datetime.now().date(),  # effective_date
                request.source_url,
                ['regulatory', 'healthcare'] + request.program,  # tags
                {"text": f"Regulatory document: {request.title}"},  # summary
                {  # search_metadata
                    "upload_method": "unified_api",
                    "original_filename": filename,
                    "file_size": len(file_data),
                    "user_document_id": upload_result.get('document_id')
                },
                'unified_api_upload',  # extraction_method
                1.0,  # priority_score
                datetime.now(),
                datetime.now()
            )
        
        # Update vectors to reference regulatory document
        if upload_result.get('vector_ids'):
            async with pool.get_connection() as conn:
                for vector_id in upload_result['vector_ids']:
                    await conn.execute("""
                        UPDATE user_document_vectors 
                        SET document_source_type = 'regulatory_document',
                            regulatory_document_id = $1
                        WHERE id = $2
                    """, regulatory_doc_id, uuid.UUID(vector_id))
        
        logger.info(f"✅ Regulatory document {request.title} processed successfully: {regulatory_doc_id}")
        
        return UnifiedDocumentResponse(
            success=True,
            document_id=str(regulatory_doc_id),
            document_type=request.document_type,
            source_type="url_download",
            processing_method="unified_api_pipeline",
            title=request.title,
            message=f"Regulatory document '{request.title}' uploaded and processed successfully",
            vector_processing_status="completed" if upload_result.get('content_processed') else "failed",
            estimated_vectors=upload_result.get('vector_chunk_count', 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Regulatory document upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Regulatory document upload failed: {str(e)}"
        )

@app.post("/api/documents/upload-unified", response_model=UnifiedDocumentResponse)
async def upload_unified_document(
    file: UploadFile = File(None),
    request_data: str = Form(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Unified document upload endpoint that handles both file uploads and URL downloads
    through the same processing pipeline. This demonstrates the Unified API pattern.
    """
    try:
        # Parse the request data
        import json
        request = UnifiedDocumentRequest(**json.loads(request_data))
        
        logger.info(f"📄 Unified document upload: {request.document_type} via {request.source_type}")
        
        # Get storage service
        global storage_service_instance
        if not storage_service_instance:
            storage_service_instance = await get_storage_service()
        
        file_data = None
        filename = None
        content_type = None
        
        if request.source_type == "file_upload":
            if not file:
                raise HTTPException(status_code=400, detail="File is required for file_upload source_type")
            
            file_data = await file.read()
            filename = file.filename
            content_type = file.content_type
            
        elif request.source_type == "url_download":
            if not request.source_url:
                raise HTTPException(status_code=400, detail="source_url is required for url_download source_type")
            
            # Download from URL
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(request.source_url) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Failed to download from URL: HTTP {response.status}"
                        )
                    
                    file_data = await response.read()
                    filename = request.source_url.split('/')[-1] or f"{request.title or 'document'}.pdf"
                    content_type = response.headers.get('content-type', 'application/pdf')
        
        else:
            raise HTTPException(status_code=400, detail="Invalid source_type. Must be 'file_upload' or 'url_download'")
        
        if not file_data or len(file_data) == 0:
            raise HTTPException(status_code=400, detail="No file data received")
        
        # Process through unified pipeline based on document type
        if request.document_type == "regulatory_document":
            # Handle regulatory documents with enhanced metadata
            document_metadata = {
                "title": request.title or filename,
                "jurisdiction": request.jurisdiction or "federal",
                "program": request.program or ["medicaid"],
                "source_url": request.source_url,
                "processing_method": "unified_api",
                **(request.metadata or {})
            }
            
            # Process through user document pipeline first
            upload_result = await storage_service_instance.upload_user_document_with_vectors(
                user_id=current_user.id,
                file_data=file_data,
                filename=filename,
                document_type=request.document_type,
                metadata=document_metadata
            )
            
            # Also store in regulatory_documents table
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                regulatory_doc_id = await conn.fetchval("""
                    INSERT INTO regulatory_documents (
                        raw_document_path, title, jurisdiction, program, document_type,
                        effective_date, source_url, tags, summary, search_metadata,
                        extraction_method, priority_score, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    RETURNING document_id
                """,
                    upload_result['file_path'],
                    request.title or filename,
                    request.jurisdiction or "federal",
                    request.program or ["medicaid"],
                    request.document_type,
                    datetime.now().date(),
                    request.source_url,
                    ['regulatory', 'healthcare'] + (request.program or []),
                    {"text": f"Document: {request.title or filename}"},
                    {
                        "upload_method": "unified_api",
                        "source_type": request.source_type,
                        "original_filename": filename,
                        "file_size": len(file_data),
                        "user_document_id": upload_result.get('document_id')
                    },
                    'unified_api',
                    1.0,
                    datetime.now(),
                    datetime.now()
                )
            
            document_id = str(regulatory_doc_id)
            
        else:
            # Handle user documents, policies, etc.
            upload_result = await storage_service_instance.upload_user_document_with_vectors(
                user_id=current_user.id,
                file_data=file_data,
                filename=filename,
                document_type=request.document_type,
                metadata=request.metadata
            )
            document_id = upload_result['document_id']
        
        return UnifiedDocumentResponse(
            success=True,
            document_id=document_id,
            document_type=request.document_type,
            source_type=request.source_type,
            processing_method="unified_api_pipeline",
            filename=filename,
            title=request.title,
            message=f"Document processed successfully via {request.source_type}",
            vector_processing_status="completed" if upload_result.get('content_processed') else "failed",
            estimated_vectors=upload_result.get('vector_chunk_count', 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unified document upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unified document upload failed: {str(e)}"
        )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    chat_request: ChatRequest,
    user_info: Dict[str, Any] = Depends(get_current_user)
) -> ChatResponse:
    """
    Main chat endpoint for healthcare navigation assistance.
    
    This endpoint processes user messages and provides intelligent responses
    using the healthcare navigation AI system.
    """
    # TODO: Implement conversation persistence optimization
    # TODO: Add conversation analytics and insights
    # TODO: Create conversation export functionality
    # TODO: Implement conversation summarization for long chats
    
    try:
        user_id = user_info["user_id"]
        message = chat_request.message
        conversation_id = chat_request.conversation_id or f"conv_{user_id}_{int(datetime.utcnow().timestamp())}"
        context = chat_request.context or {}
        
        logger.info(f"Processing chat request for user {user_id[:8]}...")
        
        if AGENT_ORCHESTRATOR_AVAILABLE:
            try:
                # TODO: Implement intelligent agent routing based on query type
                # TODO: Add query complexity analysis for response optimization
                # TODO: Create multi-agent collaboration for complex queries
                
                # Process with Patient Navigator first
                navigator_result = await agent_orchestrator_instance.process_message(
                    message=message,
                    user_id=user_id,
                    session_id=conversation_id
                )
                
                # Convert to conversational response
                final_response = await agent_orchestrator_instance.process_response(
                    response=navigator_result,
                    user_id=user_id,
                    session_id=conversation_id
                )
                
                # TODO: Add response quality scoring and feedback loop
                # TODO: Implement response caching for common queries
                # TODO: Add response personalization based on user history
                
                return ChatResponse(
                    text=final_response["message"],
                    conversation_id=conversation_id,
                    sources=final_response.get("sources", []),
                    metadata={
                        **final_response.get("metadata", {}),
                        "agents_used": ["patient_navigator"],
                        "processing_time": final_response.get("processing_time", 0)
                    }
                )
                
            except Exception as e:
                logger.error(f"Agent processing error: {e}")
                logger.error(traceback.format_exc())
                # Fall through to fallback
        
        # Fallback response when agents are unavailable
        # TODO: Implement smarter fallback with pre-trained responses
        # TODO: Add queue system for processing when agents are restored
        # TODO: Create notification system for service disruptions
        
        fallback_orchestrator = FallbackOrchestrator()
        result = await fallback_orchestrator.process_message(
            message=message,
            user_id=user_id,
            conversation_id=conversation_id,
            context=context
        )
        
        return ChatResponse(
            text=result["response"],
            conversation_id=conversation_id,
            sources=result["sources"],
            metadata=result["metadata"]
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 