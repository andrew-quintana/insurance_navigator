#!/usr/bin/env python3
"""
Test Server for Thinking Messages Demo
=====================================

Minimal FastAPI server that demonstrates the real-time thinking messages
feature without requiring database connectivity. Perfect for testing the
WebSocket integration and frontend components.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our thinking messages components
from agents.unified_navigator.navigator_agent import UnifiedNavigatorAgent
from agents.unified_navigator.models import UnifiedNavigatorInput
from agents.unified_navigator.websocket_handler import get_workflow_broadcaster

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Insurance Navigator - Thinking Messages Demo",
    description="Minimal server to demonstrate real-time thinking messages",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    text: str
    response: str
    conversation_id: str
    workflow_id: Optional[str] = None
    timestamp: str
    metadata: Dict[str, Any]

# Mock authentication for demo
async def get_current_user():
    """Mock authentication - returns a demo user"""
    return {
        "id": "demo_user_123",
        "email": "demo@example.com",
        "name": "Demo User"
    }

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Insurance Navigator - Thinking Messages Demo Server",
        "features": [
            "Real-time thinking messages via WebSocket",
            "UnifiedNavigatorAgent integration", 
            "No database dependency",
            "Perfect for frontend testing"
        ],
        "endpoints": {
            "chat": "/chat",
            "websocket": "/ws/workflow/{workflow_id}?user_id={user_id}",
            "health": "/"
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Chat endpoint with real-time thinking messages support.
    
    This endpoint:
    1. Processes the user's message using UnifiedNavigatorAgent
    2. Includes workflow_id in response for WebSocket connection
    3. Broadcasts thinking messages in real-time via WebSocket
    4. Returns the final response with metadata
    """
    try:
        logger.info(f"Processing chat request from user {current_user['id']}: {request.message}")
        
        # Create navigator input
        navigator_input = UnifiedNavigatorInput(
            user_query=request.message,
            user_id=current_user["id"],
            session_id=request.conversation_id or f"session_{datetime.now().timestamp()}"
        )
        
        # Process with UnifiedNavigatorAgent (with real thinking messages!)
        agent = UnifiedNavigatorAgent(use_mock=True)  # Use mock mode for demo
        response = await agent.execute(navigator_input)
        
        # Create comprehensive API response
        final_response = ChatResponse(
            text=response.response,
            response=response.response,
            conversation_id=navigator_input.session_id,
            workflow_id=response.workflow_id,  # Key for WebSocket connection!
            timestamp=datetime.now().isoformat(),
            metadata={
                "processing_time": response.total_processing_time_ms / 1000.0,
                "tool_used": response.tool_used.value,
                "input_safety_check": {
                    "is_safe": response.input_safety_check.is_safe,
                    "confidence": response.input_safety_check.confidence
                },
                "workflow_tracking": {
                    "workflow_id": response.workflow_id,
                    "websocket_endpoint": f"/ws/workflow/{response.workflow_id}" if response.workflow_id else None,
                    "thinking_messages_enabled": True,
                    "real_time_updates": True
                }
            }
        )
        
        logger.info(f"Chat response ready (workflow_id: {response.workflow_id})")
        return final_response
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Chat processing failed",
                "message": str(e),
                "type": "internal_error"
            }
        )

@app.websocket("/ws/workflow/{workflow_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_id: str, user_id: str):
    """
    WebSocket endpoint for real-time workflow status updates.
    
    This endpoint:
    1. Connects the frontend to workflow status broadcasts
    2. Receives thinking messages from the workflow logger
    3. Sends real-time updates to the frontend WorkflowStatus component
    4. Handles connection lifecycle and errors gracefully
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for workflow {workflow_id}, user {user_id}")
    
    # Register this WebSocket with the broadcaster
    broadcaster = get_workflow_broadcaster()
    connection_id = f"{user_id}_{workflow_id}_{id(websocket)}"
    
    try:
        # Add connection to broadcaster
        await broadcaster.add_connection(workflow_id, user_id, websocket)
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection_confirmed",
            "workflow_id": workflow_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to workflow status updates"
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages (like pong responses to ping)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                if message == "pong":
                    logger.debug(f"Received pong from {connection_id}")
                else:
                    logger.info(f"Received message from {connection_id}: {message}")
                    
            except asyncio.TimeoutError:
                # Send heartbeat ping
                await websocket.send_json({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for workflow {workflow_id}")
    except Exception as e:
        logger.error(f"WebSocket error for workflow {workflow_id}: {e}")
    finally:
        # Clean up connection
        await broadcaster.remove_connection(workflow_id, user_id, websocket)
        logger.info(f"WebSocket cleanup completed for {connection_id}")

@app.get("/ws/status")
async def websocket_status():
    """Get current WebSocket connection statistics"""
    broadcaster = get_workflow_broadcaster()
    stats = broadcaster.get_connection_stats()
    
    return {
        "websocket_connections": stats,
        "status": "healthy",
        "features": [
            "Real-time workflow status broadcasts",
            "Automatic connection management", 
            "Heartbeat/keepalive support",
            "Graceful error handling"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Insurance Navigator - Thinking Messages Demo Server")
    print("=" * 60)
    print("✨ Features:")
    print("   • Real-time thinking messages via WebSocket")
    print("   • UnifiedNavigatorAgent with workflow logging")
    print("   • No database dependency - perfect for testing")
    print("   • CORS enabled for frontend development")
    print()
    print("🔗 Endpoints:")
    print("   • Chat API: http://localhost:8000/chat")
    print("   • WebSocket: ws://localhost:8000/ws/workflow/{workflow_id}?user_id={user_id}")
    print("   • Health Check: http://localhost:8000/")
    print("   • WebSocket Status: http://localhost:8000/ws/status")
    print()
    print("🎯 Ready for Frontend Testing:")
    print("   1. Start this server: python test_server.py")
    print("   2. Start frontend: cd ui && npm run dev")
    print("   3. Navigate to: http://localhost:3000/chat")
    print("   4. Send a message and watch the thinking messages! ✨")
    print("=" * 60)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        reload=False  # Disable reload for stability
    )