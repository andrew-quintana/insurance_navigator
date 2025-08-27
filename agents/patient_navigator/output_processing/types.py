"""
Data types for the Output Processing Workflow.

Defines the input/output structures for the Communication Agent
that transforms technical agent outputs into user-friendly responses.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class AgentOutput(BaseModel):
    """Output from an upstream agent workflow."""
    
    agent_id: str = Field(..., description="Identifier for the source agent")
    content: str = Field(..., description="Main output text from the agent")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional context and metadata from the agent"
    )


class CommunicationRequest(BaseModel):
    """Request to enhance communication from multiple agent outputs."""
    
    agent_outputs: List[AgentOutput] = Field(
        ..., 
        description="List of outputs from upstream agent workflows"
    )
    user_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional user context for personalization"
    )


class CommunicationResponse(BaseModel):
    """Enhanced response with warm, empathetic communication."""
    
    enhanced_content: str = Field(
        ..., 
        description="Main user-facing response with improved tone and clarity"
    )
    original_sources: List[str] = Field(
        ..., 
        description="List of agent IDs that contributed to this response"
    )
    processing_time: float = Field(
        ..., 
        description="Time taken to process the request in seconds"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional processing information and context"
    )
