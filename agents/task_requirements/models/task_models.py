"""
Models for the Task Requirements Agent.

This module defines the Pydantic models used by the Task Requirements Agent for
managing document requirements and validation.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentStatus(BaseModel):
    """Model representing the status of a required document."""
    type: str = Field(
        description="Type of required item (document, information)"
    )
    present: Optional[bool] = Field(
        default=None,
        description="Whether the document is present"
    )
    source: Optional[str] = Field(
        default=None,
        description="Source of the document (user upload, database, etc.)"
    )
    user_validated: bool = Field(
        default=False,
        description="Whether the document has been validated by the user"
    )
    description: str = Field(
        description="Description of the document"
    )
    date_added: Optional[str] = Field(
        default=None,
        description="Date the document was added"
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Unique ID for the document"
    )


class ReactStep(BaseModel):
    """Model representing a step in the ReAct framework."""
    thought: Optional[str] = Field(
        default=None,
        description="The reasoning for this step"
    )
    act: Optional[str] = Field(
        default=None,
        description="The action to take"
    )
    action_name: Optional[str] = Field(
        default=None,
        description="Name of the action function to call"
    )
    action_args: Optional[str] = Field(
        default=None,
        description="Arguments for the action function"
    )
    observation: Optional[str] = Field(
        default=None,
        description="Observation after taking the action"
    )


class TaskProcessingResult(BaseModel):
    """Model representing the result of task processing."""
    input: Dict[str, Any] = Field(
        description="The original input to the agent"
    )
    required_context: Dict[str, DocumentStatus] = Field(
        description="The required context with document statuses"
    )
    status: str = Field(
        description="The status of the task processing (complete, failed, etc.)"
    )
    timestamp: str = Field(
        description="The timestamp of the processing"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if processing failed"
    ) 