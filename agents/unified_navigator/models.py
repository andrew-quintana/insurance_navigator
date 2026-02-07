"""
Data models for the unified navigator agent.

This module defines the Pydantic models used throughout the unified navigator
workflow for type safety and data validation.
"""

from typing import Any, Dict, List, Optional, Union, TypedDict
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class SafetyLevel(str, Enum):
    """Safety assessment levels for input validation."""
    SAFE = "safe"
    UNCERTAIN = "uncertain"
    UNSAFE = "unsafe"


class ToolType(str, Enum):
    """Available tools for the unified agent."""
    WEB_SEARCH = "web_search"
    RAG_SEARCH = "rag_search"
    COMBINED = "combined"


class InputSafetyResult(BaseModel):
    """Result of input safety assessment."""
    is_safe: bool
    is_insurance_domain: bool
    safety_level: SafetyLevel
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    sanitized_query: Optional[str] = None
    processing_time_ms: Optional[float] = None


class ToolSelection(BaseModel):
    """Result of tool selection logic."""
    selected_tool: ToolType
    reasoning: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    fallback_tool: Optional[ToolType] = None


class WebSearchResult(BaseModel):
    """Result from web search tool."""
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    processing_time_ms: float
    source: str = "brave_search"


class RAGSearchResult(BaseModel):
    """Result from RAG search tool."""
    query: str
    chunks: List[Dict[str, Any]]
    total_chunks: int
    processing_time_ms: float
    source: str = "rag_search"


class ToolExecutionResult(BaseModel):
    """Generic tool execution result."""
    tool_type: ToolType
    success: bool
    result: Optional[Union[WebSearchResult, RAGSearchResult]] = None
    error_message: Optional[str] = None
    processing_time_ms: float


class OutputSanitationResult(BaseModel):
    """Result of output sanitization."""
    sanitized_response: str
    was_modified: bool
    confidence_score: float = Field(ge=0.0, le=1.0)
    processing_time_ms: float
    warnings: List[str] = Field(default_factory=list)


class UnifiedNavigatorState(TypedDict, total=False):
    """State object for LangGraph workflow using TypedDict for better LangGraph compatibility."""
    # Input (required)
    user_query: str
    user_id: str
    
    # Optional input
    session_id: Optional[str]
    workflow_context: Optional[Dict[str, Any]]
    
    # Processing state
    input_safety: Optional[InputSafetyResult]
    tool_choice: Optional[ToolSelection]
    tool_results: Optional[List[ToolExecutionResult]]
    output_sanitation: Optional[OutputSanitationResult]
    
    # Final result
    final_response: Optional[str]
    error_message: Optional[str]
    
    # Metadata
    processing_start_time: Optional[datetime]
    total_processing_time_ms: Optional[float]
    node_timings: Dict[str, float]


class UnifiedNavigatorInput(BaseModel):
    """Input model for the unified navigator agent."""
    user_query: str
    user_id: str
    session_id: Optional[str] = None
    workflow_context: Optional[Dict[str, Any]] = None


class UnifiedNavigatorOutput(BaseModel):
    """Output model for the unified navigator agent."""
    response: str
    success: bool
    
    # Tool results
    web_search_results: Optional[WebSearchResult] = None
    rag_search_results: Optional[RAGSearchResult] = None
    
    # Processing metadata
    tool_used: ToolType
    input_safety_check: InputSafetyResult
    output_sanitized: bool
    total_processing_time_ms: float
    
    # Errors and warnings
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    
    # Session tracking
    session_id: Optional[str] = None
    user_id: str


class FastSafetyCheck(BaseModel):
    """Result of fast rule-based safety check."""
    is_safe: bool
    is_insurance_domain: bool
    is_obviously_unsafe: bool
    needs_llm_check: bool
    matched_patterns: List[str] = Field(default_factory=list)
    processing_time_ms: float


class LLMSafetyCheck(BaseModel):
    """Result of LLM-based safety assessment."""
    is_safe: bool
    is_unsafe: bool
    sanitized_query: Optional[str] = None
    reasoning: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    processing_time_ms: float