"""
Output Processing Module for Patient Navigator

This module provides the Output Communication Agent Workflow that transforms
technical agent outputs into warm, empathetic, user-friendly responses.
"""

from .agent import CommunicationAgent
from .workflow import OutputWorkflow
from .types import (
    AgentOutput,
    CommunicationRequest,
    CommunicationResponse
)
from .config import OutputProcessingConfig

__all__ = [
    "CommunicationAgent",
    "OutputWorkflow", 
    "AgentOutput",
    "CommunicationRequest",
    "CommunicationResponse",
    "OutputProcessingConfig"
]
