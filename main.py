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
from fastapi import FastAPI, HTTPException, Depends, Request, status, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import json
import asyncio

# Database service imports
from db.services.user_service import get_user_service, UserService
from db.services.conversation_service import get_conversation_service, ConversationService
from db.services.storage_service import get_storage_service, StorageService
from db.services.db_pool import get_db_pool

# Agent orchestration import
try:
    from graph.agent_orchestrator import AgentOrchestrator
    AGENT_ORCHESTRATOR_AVAILABLE = True
except ImportError:
    AGENT_ORCHESTRATOR_AVAILABLE = False
    logging.warning("Agent orchestrator not available, using fallback")

# Middleware import
try:
    from db.middleware.error_handler import ErrorHandlerMiddleware
    ERROR_HANDLER_AVAILABLE = True
except ImportError:
    ERROR_HANDLER_AVAILABLE = False
    logging.warning("Error handler middleware not available")

# Fast imports for document processing
from sentence_transformers import SentenceTransformer
import PyPDF2
import io

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Insurance Navigator API",
    description="Medicare/Medicaid navigation with persistent database and agent orchestration",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://insurance-navigator.vercel.app",  # Production frontend
        "https://*.vercel.app"  # Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
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
    """Get or load the sentence transformer model."""
    global embedding_model
    if embedding_model is None:
        try:
            logger.info("Loading SBERT model: all-MiniLM-L6-v2...")
            embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ SBERT model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load SBERT model: {e}")
            # Return a mock model for demo purposes
            class MockModel:
                def encode(self, text):
                    import random
                    # Return random 384-dimensional vector for demo
                    return [random.uniform(-1, 1) for _ in range(384)]
            embedding_model = MockModel()
            logger.warning("⚠️ Using mock embedding model for demo")
    return embedding_model

def extract_text_from_pdf(file_data: bytes) -> str:
    """Extract text from PDF file."""
    try:
        logger.info(f"📄 Starting PDF text extraction (file size: {len(file_data)} bytes)...")
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
        
        # Validate token and get user data
        user_data = await user_service_instance.validate_session(token)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            created_at=user_data.get("created_at"),
            is_active=user_data.get("is_active", True),
            roles=user_data.get("roles", [])
        )
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    health_status = {
        "status": "healthy",
        "service": "insurance_navigator",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    try:
        # Check database connectivity
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            await conn.fetchval("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        # Check user service
        if not user_service_instance:
            user_svc = await get_user_service()
        health_status["services"]["user_service"] = "healthy"
    except Exception as e:
        health_status["services"]["user_service"] = f"unhealthy: {str(e)}"
    
    try:
        # Check conversation service
        conv_svc = await get_conversation_service()
        health_status["services"]["conversation_service"] = "healthy"
    except Exception as e:
        health_status["services"]["conversation_service"] = f"unhealthy: {str(e)}"
    
    try:
        # Check storage service
        storage_svc = await get_storage_service()
        health_status["services"]["storage_service"] = "healthy"
    except Exception as e:
        health_status["services"]["storage_service"] = f"unhealthy: {str(e)}"
    
    # Check agent orchestrator
    health_status["services"]["agent_orchestrator"] = "available" if AGENT_ORCHESTRATOR_AVAILABLE else "fallback"
    
    return health_status

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
                agent_orchestrator_instance = AgentOrchestrator()
            
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
    """API root endpoint with service information."""
    return {
        "service": "Insurance Navigator API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Persistent user authentication",
            "Conversation history",
            "Document storage",
            "Agent orchestration",
            "Role-based access control"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "auth": ["/register", "/login", "/me"],
            "chat": ["/chat", "/conversations"],
            "storage": ["/upload-document", "/documents"]
        }
    }

@app.post("/upload-policy", response_model=Dict[str, Any])
async def upload_policy_demo(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Demo-ready document upload with vectorization."""
    try:
        logger.info(f"🚀 Starting document upload for user {current_user.id}: {file.filename}")
        
        # Read file data
        logger.info(f"📖 Step 1: Reading file data...")
        file_data = await file.read()
        logger.info(f"✅ Step 1 complete: Read {len(file_data)} bytes")
        
        if len(file_data) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Extract text content
        logger.info(f"🔍 Step 2: Extracting text content from {file.filename}...")
        text_content = extract_text_from_file(file_data, file.filename)
        logger.info(f"✅ Step 2 complete: Extracted {len(text_content)} characters")
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        logger.info(f"🆔 Generated document ID: {document_id}")
        
        # Chunk the text
        logger.info(f"✂️  Step 3: Chunking text (length: {len(text_content)})...")
        chunks = chunk_text(text_content)
        logger.info(f"✅ Step 3 complete: Created {len(chunks)} chunks from document")
        
        # Get embedding model
        logger.info(f"🧠 Step 4: Loading embedding model...")
        model = await get_embedding_model()
        logger.info(f"✅ Step 4 complete: Embedding model loaded")
        
        # Get database connection
        logger.info(f"🗄️  Step 5: Connecting to database...")
        pool = await get_db_pool()
        logger.info(f"✅ Step 5 complete: Database connection established")
        
        vector_ids = []
        logger.info(f"🔄 Step 6: Processing {len(chunks)} chunks for embeddings...")
        
        async with pool.get_connection() as conn:
            # Process each chunk
            for i, chunk in enumerate(chunks):
                try:
                    logger.info(f"  📝 Processing chunk {i+1}/{len(chunks)} (length: {len(chunk)})...")
                    
                    # Generate embedding
                    logger.info(f"  🧮 Generating embedding for chunk {i+1}...")
                    embedding = model.encode(chunk).tolist()
                    logger.info(f"  ✅ Embedding generated: {len(embedding)} dimensions")
                    
                    # Store in user_document_vectors table
                    logger.info(f"  💾 Storing chunk {i+1} in database...")
                    vector_id = await conn.fetchval("""
                        INSERT INTO user_document_vectors 
                        (user_id, document_id, chunk_index, chunk_embedding, chunk_text, chunk_metadata)
                        VALUES ($1, $2, $3, $4::vector, $5, $6)
                        RETURNING id
                    """, 
                    current_user.id, 
                    document_id,
                    i,
                    str(embedding),
                    chunk,
                    json.dumps({
                        "filename": file.filename,
                        "file_size": len(file_data),
                        "content_type": file.content_type,
                        "chunk_length": len(chunk),
                        "total_chunks": len(chunks),
                        "uploaded_at": datetime.utcnow().isoformat()
                    }))
                    
                    vector_ids.append(vector_id)
                    logger.info(f"  ✅ Chunk {i+1} stored with vector ID: {vector_id}")
                    
                except Exception as e:
                    logger.error(f"  ❌ Error processing chunk {i+1}: {e}")
                    logger.error(f"  📊 Chunk details: length={len(chunk)}, content_preview='{chunk[:100]}...'")
                    continue
        
        logger.info(f"🎉 Step 6 complete: Successfully stored {len(vector_ids)} vectors for document {document_id}")
        
        result = {
            "success": True,
            "document_id": document_id,
            "filename": file.filename,
            "chunks_processed": len(vector_ids),
            "total_chunks": len(chunks),
            "text_length": len(text_content),
            "message": f"Successfully uploaded and vectorized {file.filename}"
        }
        
        logger.info(f"✅ Upload complete: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Document upload error: {str(e)}")
        logger.error(f"📊 Error details: type={type(e).__name__}, traceback follows...")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 