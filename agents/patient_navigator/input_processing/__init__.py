"""Input Processing Workflow for Insurance Navigator.

This module provides multilingual voice and text input processing capabilities,
translating and sanitizing input for downstream multi-agent workflows.
"""

from .types import (
    InputHandler,
    TranslationProvider,
    TranslationResult,
    QualityScore,
    UserContext,
    SanitizedOutput,
    AgentPrompt,
    WorkflowHandoff
)

from .handler import DefaultInputHandler
from .router import IntelligentTranslationRouter
from .sanitizer import SanitizationAgent
from .integration import DefaultWorkflowHandoff
from .cli_interface import EnhancedCLIInterface
from .config import get_config

__all__ = [
    "InputHandler",
    "TranslationProvider", 
    "TranslationResult",
    "QualityScore",
    "UserContext",
    "SanitizedOutput",
    "AgentPrompt",
    "WorkflowHandoff",
    "DefaultInputHandler",
    "IntelligentTranslationRouter",
    "SanitizationAgent",
    "DefaultWorkflowHandoff",
    "EnhancedCLIInterface",
    "get_config"
]