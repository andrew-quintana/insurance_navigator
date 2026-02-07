"""
WebSocket handler for real-time workflow status updates.

This module provides WebSocket/SSE capabilities for broadcasting
real-time status updates during workflow execution.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
import weakref

from .models import WorkflowStatus

logger = logging.getLogger(__name__)


class WorkflowStatusBroadcaster:
    """
    Broadcaster for real-time workflow status updates.
    
    Manages WebSocket connections and broadcasts status updates
    during workflow execution.
    """
    
    def __init__(self):
        """Initialize the status broadcaster."""
        self.active_connections: Dict[str, Set[Any]] = {}  # workflow_id -> connections
        self.connection_metadata: Dict[Any, Dict[str, Any]] = weakref.WeakKeyDictionary()
        self.logger = logger
        
    async def connect(self, websocket: Any, user_id: str, workflow_id: Optional[str] = None):
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection object
            user_id: User identifier
            workflow_id: Optional specific workflow to listen to
        """
        try:
            await websocket.accept()
            
            # Store connection metadata
            self.connection_metadata[websocket] = {
                "user_id": user_id,
                "workflow_id": workflow_id,
                "connected_at": datetime.utcnow(),
                "last_ping": time.time()
            }
            
            # Add to active connections for workflow
            if workflow_id:
                if workflow_id not in self.active_connections:
                    self.active_connections[workflow_id] = set()
                self.active_connections[workflow_id].add(websocket)
            
            self.logger.info(f"WebSocket connected: user={user_id}, workflow={workflow_id}")
            
            # Send connection confirmation
            await self._send_to_connection(websocket, {
                "type": "connection_confirmed",
                "user_id": user_id,
                "workflow_id": workflow_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {e}")
            await self.disconnect(websocket)
    
    async def disconnect(self, websocket: Any):
        """
        Disconnect a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to disconnect
        """
        try:
            # Get connection metadata
            metadata = self.connection_metadata.get(websocket, {})
            workflow_id = metadata.get("workflow_id")
            user_id = metadata.get("user_id", "unknown")
            
            # Remove from active connections
            if workflow_id and workflow_id in self.active_connections:
                self.active_connections[workflow_id].discard(websocket)
                if not self.active_connections[workflow_id]:
                    del self.active_connections[workflow_id]
            
            # Clean up metadata
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
            
            self.logger.info(f"WebSocket disconnected: user={user_id}, workflow={workflow_id}")
            
        except Exception as e:
            self.logger.error(f"WebSocket disconnect error: {e}")
    
    async def broadcast_status(self, workflow_id: str, status: WorkflowStatus):
        """
        Broadcast workflow status to connected clients.
        
        Args:
            workflow_id: Workflow identifier
            status: Status update to broadcast
        """
        if workflow_id not in self.active_connections:
            return
        
        message = {
            "type": "workflow_status",
            "workflow_id": workflow_id,
            "status": {
                "step": status.step,
                "message": status.message,
                "progress": status.progress,
                "timestamp": status.timestamp.isoformat()
            }
        }
        
        # Send to all connections for this workflow
        connections_to_remove = []
        for websocket in self.active_connections[workflow_id]:
            success = await self._send_to_connection(websocket, message)
            if not success:
                connections_to_remove.append(websocket)
        
        # Clean up failed connections
        for websocket in connections_to_remove:
            await self.disconnect(websocket)
    
    async def broadcast_completion(self, workflow_id: str, success: bool, response: str):
        """
        Broadcast workflow completion to connected clients.
        
        Args:
            workflow_id: Workflow identifier
            success: Whether workflow completed successfully
            response: Final response
        """
        if workflow_id not in self.active_connections:
            return
        
        message = {
            "type": "workflow_complete",
            "workflow_id": workflow_id,
            "success": success,
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to all connections for this workflow
        connections_to_remove = []
        for websocket in self.active_connections[workflow_id]:
            success = await self._send_to_connection(websocket, message)
            if not success:
                connections_to_remove.append(websocket)
        
        # Clean up failed connections
        for websocket in connections_to_remove:
            await self.disconnect(websocket)
    
    async def _send_to_connection(self, websocket: Any, message: Dict[str, Any]) -> bool:
        """
        Send message to a specific WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            message: Message to send
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            await websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            self.logger.warning(f"Failed to send WebSocket message: {e}")
            return False
    
    async def ping_connections(self):
        """Send ping to all active connections to keep them alive."""
        ping_message = {
            "type": "ping",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        all_connections = set()
        for connections in self.active_connections.values():
            all_connections.update(connections)
        
        connections_to_remove = []
        for websocket in all_connections:
            success = await self._send_to_connection(websocket, ping_message)
            if not success:
                connections_to_remove.append(websocket)
        
        # Clean up failed connections
        for websocket in connections_to_remove:
            await self.disconnect(websocket)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about active connections.
        
        Returns:
            Connection statistics
        """
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        active_workflows = len(self.active_connections)
        
        return {
            "total_connections": total_connections,
            "active_workflows": active_workflows,
            "workflows": list(self.active_connections.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global broadcaster instance
_broadcaster = None


def get_workflow_broadcaster() -> WorkflowStatusBroadcaster:
    """
    Get the global workflow status broadcaster instance.
    
    Returns:
        WorkflowStatusBroadcaster instance
    """
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = WorkflowStatusBroadcaster()
    return _broadcaster


class SSEHandler:
    """
    Server-Sent Events handler for clients that prefer SSE over WebSocket.
    
    Provides similar functionality to WebSocket but using HTTP streaming.
    """
    
    def __init__(self):
        """Initialize the SSE handler."""
        self.active_streams: Dict[str, List[Any]] = {}  # workflow_id -> response streams
        self.logger = logger
    
    async def create_stream(self, response_stream: Any, user_id: str, workflow_id: str):
        """
        Create a new SSE stream for workflow updates.
        
        Args:
            response_stream: FastAPI StreamingResponse or similar
            user_id: User identifier
            workflow_id: Workflow to listen to
        """
        if workflow_id not in self.active_streams:
            self.active_streams[workflow_id] = []
        
        self.active_streams[workflow_id].append(response_stream)
        self.logger.info(f"SSE stream created: user={user_id}, workflow={workflow_id}")
    
    async def send_status_update(self, workflow_id: str, status: WorkflowStatus):
        """
        Send status update to SSE streams.
        
        Args:
            workflow_id: Workflow identifier
            status: Status update to send
        """
        if workflow_id not in self.active_streams:
            return
        
        data = {
            "step": status.step,
            "message": status.message,
            "progress": status.progress,
            "timestamp": status.timestamp.isoformat()
        }
        
        sse_data = f"event: status\ndata: {json.dumps(data)}\n\n"
        
        # Send to all streams for this workflow
        streams_to_remove = []
        for stream in self.active_streams[workflow_id]:
            try:
                await stream.write(sse_data.encode())
            except Exception as e:
                self.logger.warning(f"SSE stream write failed: {e}")
                streams_to_remove.append(stream)
        
        # Clean up failed streams
        for stream in streams_to_remove:
            self.active_streams[workflow_id].remove(stream)
    
    async def send_completion(self, workflow_id: str, success: bool, response: str):
        """
        Send completion event to SSE streams.
        
        Args:
            workflow_id: Workflow identifier
            success: Whether workflow completed successfully
            response: Final response
        """
        if workflow_id not in self.active_streams:
            return
        
        data = {
            "success": success,
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        sse_data = f"event: complete\ndata: {json.dumps(data)}\n\n"
        
        # Send to all streams for this workflow
        for stream in self.active_streams[workflow_id]:
            try:
                await stream.write(sse_data.encode())
                await stream.write("event: close\ndata: \n\n".encode())
            except Exception as e:
                self.logger.warning(f"SSE completion send failed: {e}")
        
        # Clean up streams for completed workflow
        if workflow_id in self.active_streams:
            del self.active_streams[workflow_id]


# Global SSE handler instance
_sse_handler = None


def get_sse_handler() -> SSEHandler:
    """
    Get the global SSE handler instance.
    
    Returns:
        SSEHandler instance
    """
    global _sse_handler
    if _sse_handler is None:
        _sse_handler = SSEHandler()
    return _sse_handler