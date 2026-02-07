"""
FastAPI WebSocket routes for real-time workflow status updates.

This module provides WebSocket endpoints for the frontend to receive
real-time updates during AI workflow execution.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse

from agents.unified_navigator.websocket_handler import (
    get_workflow_broadcaster, 
    get_sse_handler
)
from agents.unified_navigator.models import WorkflowStatus

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/workflow/{workflow_id}")
async def websocket_workflow_status(
    websocket: WebSocket,
    workflow_id: str,
    user_id: str = Query(...)
):
    """
    WebSocket endpoint for real-time workflow status updates.
    
    Args:
        websocket: WebSocket connection
        workflow_id: Workflow identifier to listen to
        user_id: User identifier for authorization
    """
    broadcaster = get_workflow_broadcaster()
    
    try:
        # Connect and register the WebSocket
        await broadcaster.connect(websocket, user_id, workflow_id)
        
        logger.info(f"WebSocket connected for workflow {workflow_id}, user {user_id}")
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for incoming messages (like pings from client)
                message = await websocket.receive_text()
                
                # Handle client messages if needed (e.g., ping responses)
                if message == "pong":
                    logger.debug(f"Received pong from client for workflow {workflow_id}")
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for workflow {workflow_id}")
                break
            except Exception as e:
                logger.error(f"WebSocket error for workflow {workflow_id}: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection failed for workflow {workflow_id}: {e}")
    finally:
        # Clean up connection
        await broadcaster.disconnect(websocket)


@router.get("/api/workflow/{workflow_id}/status/stream")
async def sse_workflow_status(
    workflow_id: str,
    user_id: str = Query(...)
):
    """
    Server-Sent Events endpoint for workflow status updates.
    
    Args:
        workflow_id: Workflow identifier
        user_id: User identifier for authorization
        
    Returns:
        StreamingResponse with SSE events
    """
    
    async def event_stream():
        """Generator for SSE events."""
        sse_handler = get_sse_handler()
        
        # Send connection confirmation
        yield f"event: connected\ndata: {{\"workflow_id\": \"{workflow_id}\", \"user_id\": \"{user_id}\"}}\n\n"
        
        # Register this stream
        await sse_handler.create_stream(None, user_id, workflow_id)  # Stream will be handled differently
        
        # Keep connection alive with periodic heartbeats
        try:
            while True:
                # Send heartbeat every 30 seconds
                await asyncio.sleep(30)
                yield f"event: heartbeat\ndata: {{\"timestamp\": \"{asyncio.get_event_loop().time()}\"}}\n\n"
                
        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for workflow {workflow_id}")
        except Exception as e:
            logger.error(f"SSE stream error for workflow {workflow_id}: {e}")
            yield f"event: error\ndata: {{\"error\": \"{str(e)}\"}}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.get("/api/workflow/connections/stats")
async def get_connection_stats():
    """
    Get statistics about active WebSocket connections.
    
    Returns:
        Connection statistics
    """
    broadcaster = get_workflow_broadcaster()
    stats = broadcaster.get_connection_stats()
    
    return {
        "success": True,
        "data": stats
    }


@router.post("/api/workflow/{workflow_id}/broadcast/test")
async def test_broadcast_status(
    workflow_id: str,
    step: str = "testing",
    message: str = "Test broadcast message"
):
    """
    Test endpoint for broadcasting status updates.
    
    Args:
        workflow_id: Workflow identifier
        step: Test step name
        message: Test message
        
    Returns:
        Broadcast result
    """
    try:
        from datetime import datetime
        
        broadcaster = get_workflow_broadcaster()
        
        # Create test status
        status = WorkflowStatus(
            step=step,
            message=message,
            progress=0.5,
            timestamp=datetime.utcnow()
        )
        
        # Broadcast to connected clients
        await broadcaster.broadcast_status(workflow_id, status)
        
        return {
            "success": True,
            "message": f"Test broadcast sent to workflow {workflow_id}",
            "status": {
                "step": status.step,
                "message": status.message,
                "progress": status.progress
            }
        }
        
    except Exception as e:
        logger.error(f"Test broadcast failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Background task to keep connections alive
async def connection_keepalive():
    """Background task to send periodic pings to maintain connections."""
    broadcaster = get_workflow_broadcaster()
    
    while True:
        try:
            await asyncio.sleep(60)  # Ping every minute
            await broadcaster.ping_connections()
        except Exception as e:
            logger.error(f"Connection keepalive error: {e}")


# Initialize background task when module is imported
def start_background_tasks():
    """Start background tasks for WebSocket management."""
    try:
        # Create background task for connection keepalive
        asyncio.create_task(connection_keepalive())
        logger.info("WebSocket background tasks started")
    except Exception as e:
        logger.error(f"Failed to start WebSocket background tasks: {e}")


# Auto-start background tasks
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        start_background_tasks()
except RuntimeError:
    # No event loop running yet, will start when FastAPI starts
    pass