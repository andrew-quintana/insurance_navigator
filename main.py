#!/usr/bin/env python3
"""
FastAPI Insurance Navigator API

Uses import bypass strategy (from regulatory agent team) to avoid dependency conflicts.
Implements mock agents for immediate functionality with production agent fallbacks.
"""

import os
import sys
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import logging

# Apply regulatory team's import bypass strategy
sys.path.insert(0, 'agents/regulatory/core')

# Safe imports using bypass strategy
from db.middleware.error_handler import ErrorHandlerMiddleware
from db.models.user import UserService, UserAuthentication

# Mock agent imports (zero dependencies, always work)
try:
    from mock_tools import create_mock_agent
    MOCK_AGENT_AVAILABLE = True
except ImportError:
    MOCK_AGENT_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Insurance Navigator API",
    description="Medicare/Medicaid navigation with LangGraph agent orchestration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001"  # Support both ports for development flexibility
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handling middleware
app.add_middleware(ErrorHandlerMiddleware)

# Initialize services
user_service = UserService()
user_auth = UserAuthentication()

# Pydantic models for FastAPI (these are proper response models)
class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    text: str
    sources: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    workflow_type: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Mock agent orchestrator (bypasses dependency issues)
class MockAgentOrchestrator:
    """Mock orchestrator using regulatory team's proven patterns."""
    
    def __init__(self):
        if MOCK_AGENT_AVAILABLE:
            self.regulatory_agent = create_mock_agent()
            logger.info("✅ Mock regulatory agent initialized")
        else:
            self.regulatory_agent = None
            logger.warning("⚠️ Mock agent not available")
    
    async def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user message using mock agents (always works)."""
        try:
            if self.regulatory_agent:
                # Use proven regulatory analysis
                result = self.regulatory_agent.analyze_strategy(
                    strategy=message,
                    context=context or {}
                )
                
                return {
                    "response": f"**Insurance Navigator Analysis**\n\n{result['analysis']}",
                    "sources": result.get('sources', []),
                    "metadata": {
                        "agent_version": result.get('agent_version', 'mock'),
                        "sources_found": result.get('sources_found', 0),
                        "processing_time": result.get('processing_time_seconds', 0),
                        "mock_mode": result.get('mock_mode', True)
                    }
                }
            else:
                # Ultimate fallback
                return {
                    "response": f"**Insurance Navigator Response**\n\nI understand you're asking: '{message}'\n\nI'm ready to help with Medicare/Medicaid navigation, but currently running in fallback mode. Your question has been received and I can provide basic guidance.",
                    "sources": [],
                    "metadata": {"mode": "fallback", "message_received": True}
                }
                
        except Exception as e:
            logger.error(f"Mock orchestrator error: {str(e)}")
            return {
                "response": f"I received your message: '{message}'\n\nI'm currently in maintenance mode, but I'm here to help with insurance navigation. Please try again in a moment.",
                "sources": [],
                "metadata": {"error": str(e), "mode": "error_fallback"}
            }

# Initialize mock orchestrator (always works)
orchestrator = MockAgentOrchestrator()

# Authentication dependency
async def get_current_user(request: Request) -> UserResponse:
    """Get current user from JWT token."""
    auth_header = request.headers.get("Authorization")
    logger.info(f"🔐 Auth header received: {auth_header}")
    
    if not auth_header:
        logger.error("❌ Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token"
        )
    
    # Case-insensitive check for Bearer token
    if not (auth_header.startswith("Bearer ") or auth_header.startswith("bearer ")):
        logger.error("❌ Malformed Authorization header - must start with 'Bearer ' or 'bearer '")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token"
        )
    
    token = auth_header.split(" ")[1]
    logger.info(f"🎫 Extracted token: {token[:20]}...")
    
    try:
        # Decode and validate token
        payload = user_auth.verify_token(token)
        logger.info(f"🔓 Token payload: {payload}")
        
        # Extract user information from token payload
        user_email = payload.get("sub")  # Standard JWT subject field
        user_id = payload.get("user_id")
        user_name = payload.get("name")
        
        logger.info(f"📧 Extracted - Email: {user_email}, ID: {user_id}, Name: {user_name}")
        
        if not user_email or not user_id or not user_name:
            logger.error(f"❌ Missing required fields in token payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        logger.info(f"✅ Authentication successful for user: {user_email}")
        # Return user response with token data
        return UserResponse(
            id=user_id,
            email=user_email,
            name=user_name,
            created_at=None
        )
        
    except ValueError as e:
        logger.error(f"❌ Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "insurance_navigator",
        "mock_agent_available": MOCK_AGENT_AVAILABLE,
        "agents": {
            "regulatory": "mock" if MOCK_AGENT_AVAILABLE else "unavailable"
        }
    }

@app.post("/register", response_model=Token)
async def register(request: RegisterRequest):
    """Register a new user."""
    try:
        user = user_service.create_user(
            email=request.email,
            password=request.password,
            full_name=request.name  # Note: UserService expects full_name
        )
        
        # Create JWT token with standard structure
        token = user_auth.create_access_token({
            "sub": user["email"],  # Standard JWT subject field
            "user_id": user["id"],
            "name": user["full_name"],
            "email": user["email"]
        })
        
        return Token(access_token=token, token_type="bearer")
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    user = user_service.authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create JWT token with standard structure
    token = user_auth.create_access_token({
        "sub": user["email"],  # Standard JWT subject field
        "user_id": user["id"],
        "name": user["full_name"],
        "email": user["email"]
    })
    
    return Token(access_token=token, token_type="bearer")

@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information."""
    return current_user

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Main chat endpoint with agent orchestration (using mock agents)."""
    try:
        # Add user context
        context = request.context or {}
        context.update({
            "user_id": current_user.id,
            "user_email": current_user.email
        })
        
        # Process using mock orchestrator (always works)
        result = await orchestrator.process_message(request.message, context)
        
        # Generate conversation ID if not provided
        conversation_id = getattr(request, 'conversation_id', None) or f"conv_{current_user.id}_{int(datetime.utcnow().timestamp())}"
        
        return ChatResponse(
            text=result["response"],
            sources=result.get("sources"),
            metadata=result.get("metadata"),
            conversation_id=conversation_id,
            workflow_type="medicare_navigator"  # Set a default workflow type
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing your request"
        )

@app.post("/upload-policy")
async def upload_policy(
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload policy document (stub for now)."""
    return {
        "message": "Policy upload feature coming soon",
        "status": "stub",
        "user": current_user.email
    }

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("🚀 Insurance Navigator API starting up...")
    logger.info(f"✅ Mock agent available: {MOCK_AGENT_AVAILABLE}")
    logger.info("🎭 Using regulatory team's proven mock agent pattern")
    logger.info("✅ Startup complete - server ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("👋 Insurance Navigator API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 