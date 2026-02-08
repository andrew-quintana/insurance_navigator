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
    QUICK_INFO = "quick_info"           # Fast policy lookup with BM25/TF-IDF
    ACCESS_STRATEGY = "access_strategy" # Complex research with Tavily + RAG
    WEB_SEARCH = "web_search"           # Current events and news
    RAG_SEARCH = "rag_search"           # Traditional RAG search
    COMBINED = "combined"               # Multiple tools


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
    result: Optional[Any] = None  # Union of result types - will be properly typed at runtime
    error_message: Optional[str] = None
    processing_time_ms: float


class OutputSanitationResult(BaseModel):
    """Result of output sanitization."""
    sanitized_response: str
    was_modified: bool
    confidence_score: float = Field(ge=0.0, le=1.0)
    processing_time_ms: float
    warnings: List[str] = Field(default_factory=list)


class WorkflowStatus(BaseModel):
    """Real-time workflow status for frontend updates."""
    step: str  # 'sanitizing', 'thinking', 'determining', 'skimming', 'wording'
    message: str
    progress: float  # 0.0 to 1.0
    timestamp: datetime
    

class QuickInfoResult(BaseModel):
    """Result from quick information retrieval tool."""
    query: str
    relevant_sections: List[Dict[str, Any]]
    confidence_score: float
    processing_time_ms: float
    source: str = "quick_info"
    

class AccessStrategyResult(BaseModel):
    """Result from access strategizing tool."""
    query: str
    strategy_hypothesis: str
    tavily_research: Optional[Dict[str, Any]]
    rag_validation: Optional[Dict[str, Any]]
    confidence_score: float
    processing_time_ms: float
    source: str = "access_strategy"


class UnifiedNavigatorState(TypedDict, total=False):
    """State object for LangGraph workflow using TypedDict for better LangGraph compatibility."""
    # Input (required)
    user_query: str
    user_id: str
    
    # Optional input
    session_id: Optional[str]
    workflow_context: Optional[Dict[str, Any]]
    workflow_id: Optional[str]
    
    # Processing state
    input_safety: Optional[InputSafetyResult]
    tool_choice: Optional[ToolSelection]
    tool_results: Optional[List[ToolExecutionResult]]
    output_sanitation: Optional[OutputSanitationResult]
    workflow_status: Optional[WorkflowStatus]
    
    # Final result
    final_response: Optional[str]
    error_message: Optional[str]
    
    # Real-time status
    current_status: Optional[WorkflowStatus]
    
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
    workflow_id: Optional[str] = None


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