"""
Pydantic models for Patient Navigator Supervisor Workflow.

These models define the structured input and output formats for the supervisor workflow,
ensuring type safety and validation for LangGraph state management.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum


class WorkflowType(str, Enum):
    """Enumeration of supported workflow types for the MVP."""
    INFORMATION_RETRIEVAL = "information_retrieval"
    STRATEGY = "strategy"


class SupervisorWorkflowInput(BaseModel):
    """
    Input model for supervisor workflow requests.
    
    This represents the structured input from users or other system components,
    containing the user query and context information.
    """
    
    user_query: str = Field(
        description="The user's natural language query about healthcare access"
    )
    
    user_id: str = Field(
        description="User identifier for access control and document retrieval"
    )
    
    workflow_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context from previous workflow executions"
    )


class WorkflowPrescriptionResult(BaseModel):
    """
    Result from workflow prescription agent with confidence scoring.
    """
    
    prescribed_workflows: List[WorkflowType] = Field(
        description="List of workflows prescribed for the user request",
        min_items=1,
        max_items=2  # MVP: information_retrieval and strategy only
    )
    
    confidence_score: float = Field(
        description="Confidence score for the prescription (0.0-1.0)",
        ge=0.0,
        le=1.0,
        examples=[0.85, 0.92, 0.78]
    )
    
    reasoning: str = Field(
        description="Explanation of why these workflows were prescribed",
        examples=[
            "User query requires information retrieval to understand coverage details",
            "Complex request requires both information retrieval and strategic planning",
            "User needs help with provider selection and benefit optimization"
        ]
    )
    
    execution_order: List[WorkflowType] = Field(
        description="Deterministic execution order for prescribed workflows",
        examples=[
            [WorkflowType.INFORMATION_RETRIEVAL],
            [WorkflowType.INFORMATION_RETRIEVAL, WorkflowType.STRATEGY]
        ]
    )


class DocumentAvailabilityResult(BaseModel):
    """
    Result from document availability checking.
    """
    
    is_ready: bool = Field(
        description="Whether all required documents are available for workflow execution"
    )
    
    available_documents: List[str] = Field(
        description="List of document types that are available",
        default_factory=list
    )
    
    missing_documents: List[str] = Field(
        description="List of document types that are missing",
        default_factory=list
    )
    
    document_status: Dict[str, bool] = Field(
        description="Mapping of document types to availability status",
        default_factory=dict
    )


class SupervisorState(BaseModel):
    """
    LangGraph state model for supervisor workflow orchestration.
    
    This model manages the state throughout the LangGraph workflow execution,
    tracking workflow prescription, document availability, and routing decisions.
    """
    
    # Input fields
    user_query: str = Field(description="Original user query")
    user_id: str = Field(description="User identifier")
    workflow_context: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Additional workflow context"
    )
    
    # Workflow prescription results
    prescribed_workflows: Optional[List[WorkflowType]] = Field(
        default=None,
        description="Workflows prescribed by the workflow prescription agent"
    )
    
    # Document availability results
    document_availability: Optional[DocumentAvailabilityResult] = Field(
        default=None,
        description="Results from document availability checking"
    )
    
    # Routing decision
    routing_decision: Optional[Literal["PROCEED", "COLLECT"]] = Field(
        default=None,
        description="Final routing decision based on prescription and document availability"
    )
    
    # Workflow execution results
    workflow_results: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Results from workflow execution nodes"
    )
    
    # Workflow execution tracking
    executed_workflows: Optional[List[WorkflowType]] = Field(
        default=None,
        description="List of workflows that have been executed during this workflow run"
    )
    
    # Performance tracking
    processing_time: Optional[float] = Field(
        default=None,
        description="Total processing time in seconds"
    )
    
    # Node-level performance tracking
    node_performance: Optional[Dict[str, float]] = Field(
        default=None,
        description="Performance tracking for individual workflow nodes"
    )
    
    # Error handling
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if any step failed"
    )


class SupervisorWorkflowOutput(BaseModel):
    """
    Output model for supervisor workflow responses.
    
    This provides structured output with routing decisions, prescribed workflows,
    document availability, and next steps for the user.
    """
    
    routing_decision: Literal["PROCEED", "COLLECT"] = Field(
        description="Final routing decision for the user request",
        examples=["PROCEED", "COLLECT"]
    )
    
    prescribed_workflows: List[WorkflowType] = Field(
        description="Workflows prescribed for the user request",
        examples=[
            [WorkflowType.INFORMATION_RETRIEVAL],
            [WorkflowType.INFORMATION_RETRIEVAL, WorkflowType.STRATEGY]
        ]
    )
    
    execution_order: List[WorkflowType] = Field(
        description="Deterministic execution order for prescribed workflows",
        examples=[
            [WorkflowType.INFORMATION_RETRIEVAL],
            [WorkflowType.INFORMATION_RETRIEVAL, WorkflowType.STRATEGY]
        ]
    )
    
    document_availability: DocumentAvailabilityResult = Field(
        description="Results from document availability checking"
    )
    
    workflow_prescription: WorkflowPrescriptionResult = Field(
        description="Results from workflow prescription agent"
    )
    
    next_steps: List[str] = Field(
        description="List of next steps for the user",
        examples=[
            ["Proceeding with information retrieval workflow"],
            ["Please upload your insurance documents before proceeding"],
            ["Starting with information retrieval, then strategy planning"]
        ]
    )
    
    confidence_score: float = Field(
        description="Overall confidence score for the routing decision (0.0-1.0)",
        ge=0.0,
        le=1.0,
        examples=[0.85, 0.92, 0.78]
    )
    
    processing_time: float = Field(
        description="Total processing time in seconds",
        examples=[1.2, 0.8, 1.5]
    )
    
    # Workflow execution results
    information_retrieval_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Results from InformationRetrievalAgent workflow execution"
    )
    
    strategy_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Results from StrategyWorkflowOrchestrator workflow execution"
    )
    
    workflow_results: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Complete workflow execution results from all executed workflows"
    )
    
    # Audit fields
    user_id: str = Field(
        description="User identifier for audit logging",
        examples=["user_123", "test_user_456"]
    ) 