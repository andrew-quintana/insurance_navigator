"""
Unified Navigator API Endpoint.

This module provides FastAPI endpoints for the unified navigator agent,
replacing the complex multi-agent supervisor system with a single endpoint.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

from agents.unified_navigator import (
    UnifiedNavigatorAgent,
    UnifiedNavigatorInput,
    UnifiedNavigatorOutput,
    ToolType,
    SafetyLevel
)
from agents.unified_navigator.config import get_config, UnifiedNavigatorConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Unified Navigator API",
    description="Single agent API for insurance navigation with guardrails",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
navigator_agent: Optional[UnifiedNavigatorAgent] = None


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    user_id: str = Field(..., description="Unique user identifier")
    session_id: Optional[str] = Field(None, description="Chat session identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="Agent response")
    success: bool = Field(..., description="Whether request was successful")
    
    # Tool information
    tool_used: ToolType = Field(..., description="Tool used for response")
    web_search_results: Optional[Dict[str, Any]] = Field(None, description="Web search results if used")
    rag_results: Optional[Dict[str, Any]] = Field(None, description="RAG search results if used")
    
    # Safety information
    input_safe: bool = Field(..., description="Whether input passed safety checks")
    safety_level: SafetyLevel = Field(..., description="Safety assessment level")
    output_sanitized: bool = Field(..., description="Whether output was sanitized")
    
    # Performance metrics
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    
    # Session tracking
    session_id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    # Warnings and errors
    warnings: list[str] = Field(default_factory=list, description="Any warnings during processing")
    error_message: Optional[str] = Field(None, description="Error message if request failed")


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    config_valid: bool
    agent_ready: bool
    components: Dict[str, Any]


async def get_agent() -> UnifiedNavigatorAgent:
    """Dependency to get the navigator agent instance."""
    global navigator_agent
    if navigator_agent is None:
        try:
            config = get_config()
            config.validate()
            navigator_agent = UnifiedNavigatorAgent(use_mock=False)
            logger.info("Unified Navigator Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            navigator_agent = UnifiedNavigatorAgent(use_mock=True)
            logger.warning("Using mock mode due to initialization failure")
    
    return navigator_agent


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Unified Navigator API...")
    
    try:
        # Pre-initialize the agent
        await get_agent()
        logger.info("Unified Navigator API startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        # Continue with mock mode
        pass


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    try:
        config = get_config()
        agent = await get_agent()
        
        # Test agent health
        agent_health = await agent.health_check()
        
        return HealthCheckResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            config_valid=True,
            agent_ready=agent_health.get("status") == "healthy",
            components={
                "unified_navigator": agent_health,
                "config": {
                    "has_anthropic_key": bool(config.anthropic_api_key),
                    "has_brave_key": bool(config.web_search_config.api_key),
                    "model": config.anthropic_model
                },
                "guardrails": {
                    "input_sanitization": config.guardrail_config.enable_fast_safety_check,
                    "output_sanitization": config.guardrail_config.enable_template_sanitization,
                    "llm_safety_checks": config.guardrail_config.enable_llm_safety_check
                }
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            config_valid=False,
            agent_ready=False,
            components={"error": str(e)}
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, agent: UnifiedNavigatorAgent = Depends(get_agent)):
    """
    Chat endpoint for unified navigator agent.
    
    This replaces the complex multi-agent supervisor system with a single,
    optimized endpoint that handles input sanitization, tool selection,
    and output sanitization automatically.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing chat request from user {request.user_id}")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Create input for unified navigator
        navigator_input = UnifiedNavigatorInput(
            user_query=request.message,
            user_id=request.user_id,
            session_id=session_id,
            workflow_context=request.context
        )
        
        # Execute unified navigator workflow
        navigator_output = await agent.execute(navigator_input)
        
        # Convert to API response format
        response = ChatResponse(
            response=navigator_output.response,
            success=navigator_output.success,
            tool_used=navigator_output.tool_used,
            web_search_results=navigator_output.web_search_results.model_dump() if navigator_output.web_search_results else None,
            rag_results=navigator_output.rag_search_results.model_dump() if navigator_output.rag_search_results else None,
            input_safe=navigator_output.input_safety_check.is_safe,
            safety_level=navigator_output.input_safety_check.safety_level,
            output_sanitized=navigator_output.output_sanitized,
            processing_time_ms=navigator_output.total_processing_time_ms,
            session_id=session_id,
            warnings=navigator_output.warnings,
            error_message=navigator_output.error_message
        )
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"Chat request completed in {total_time:.1f}ms for user {request.user_id}")
        
        return response
        
    except Exception as e:
        total_time = (time.time() - start_time) * 1000
        logger.error(f"Chat request failed after {total_time:.1f}ms: {e}")
        
        return ChatResponse(
            response="I apologize, but I encountered an error processing your request. Please try again.",
            success=False,
            tool_used=ToolType.RAG_SEARCH,  # Default
            input_safe=True,  # Assume safe for error case
            safety_level=SafetyLevel.UNCERTAIN,
            output_sanitized=False,
            processing_time_ms=total_time,
            session_id=request.session_id or str(uuid.uuid4()),
            error_message=str(e)
        )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest, agent: UnifiedNavigatorAgent = Depends(get_agent)):
    """
    Streaming chat endpoint for real-time responses.
    
    Note: This is a simplified streaming implementation. For production,
    you would want to implement proper streaming at the LLM level.
    """
    async def generate_response():
        try:
            # For now, just return the full response as a single chunk
            # In a full implementation, you'd stream from the LLM directly
            navigator_input = UnifiedNavigatorInput(
                user_query=request.message,
                user_id=request.user_id,
                session_id=request.session_id or str(uuid.uuid4()),
                workflow_context=request.context
            )
            
            navigator_output = await agent.execute(navigator_input)
            
            # Send response in chunks for streaming effect
            response_text = navigator_output.response
            chunk_size = 50
            
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i + chunk_size]
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0.05)  # Small delay for streaming effect
            
            yield f"data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/config")
async def get_configuration():
    """Get current configuration (without sensitive data)."""
    try:
        config = get_config()
        return config.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


@app.get("/metrics")
async def get_metrics():
    """Get basic metrics about the agent."""
    try:
        agent = await get_agent()
        
        # Basic metrics - in production, you'd want proper metrics collection
        return {
            "agent_name": agent.name,
            "status": "running",
            "mock_mode": agent.mock,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


if __name__ == "__main__":
    # For development/testing
    uvicorn.run(
        "api.unified_navigator_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )