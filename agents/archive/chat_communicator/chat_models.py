"""
Models for the Chat Communicator Agent.

This module defines the Pydantic models used by the Chat Communicator Agent
for input validation and response structures, ensuring type safety.
"""

from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

# Import existing models that this agent consumes
from agents.patient_navigator.navigator_models import NavigatorOutput
from agents.service_access_strategy.strategy_models import ServiceAccessStrategy


class ChatInput(BaseModel):
    """Model representing input to the Chat Communicator Agent."""
    source_type: str = Field(
        description="Type of source agent (navigator_output or service_strategy)"
    )
    data: Union[NavigatorOutput, ServiceAccessStrategy] = Field(
        description="Structured data from source agent"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for personalization"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for context"
    )
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default_factory=list,
        description="Previous conversation messages"
    )
    user_context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional user context information"
    )


class ChatResponse(BaseModel):
    """Model representing the Chat Communicator's response."""
    message: str = Field(
        description="The conversational response to the user"
    )
    response_type: str = Field(
        description="Type of response (informational, request, guidance, emergency)"
    )
    next_steps: Optional[List[str]] = Field(
        default_factory=list,
        description="Suggested next steps for the user"
    )
    requires_action: bool = Field(
        default=False,
        description="Whether user action is required"
    )
    urgency_level: str = Field(
        default="normal",
        description="Urgency level (low, normal, high, emergency)"
    )
    confidence: float = Field(
        default=1.0,
        description="Confidence in the response (0.0-1.0)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the response"
    )


class ConversationContext(BaseModel):
    """Model for managing conversation context."""
    user_id: str = Field(
        description="User identifier"
    )
    session_id: str = Field(
        description="Session identifier"
    )
    conversation_start: datetime = Field(
        description="When the conversation started"
    )
    last_interaction: datetime = Field(
        description="Last interaction timestamp"
    )
    interaction_count: int = Field(
        default=0,
        description="Number of interactions in this session"
    )
    user_preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="User communication preferences"
    )
    conversation_summary: Optional[str] = Field(
        default=None,
        description="Summary of the conversation so far"
    )


class CommunicationPreferences(BaseModel):
    """Model for user communication preferences."""
    tone: str = Field(
        default="friendly",
        description="Preferred communication tone (formal, friendly, casual)"
    )
    detail_level: str = Field(
        default="moderate",
        description="Preferred level of detail (brief, moderate, detailed)"
    )
    language: str = Field(
        default="en",
        description="Preferred language code"
    )
    accessibility_needs: List[str] = Field(
        default_factory=list,
        description="Accessibility requirements"
    )
    contact_methods: List[str] = Field(
        default_factory=list,
        description="Preferred contact methods"
    ) 