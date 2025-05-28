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
from fastapi import FastAPI, HTTPException, Depends, Request, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

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
                response_text = result.get("response", "I'm processing your request...")
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
            workflow_type="medicare_navigator",
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 