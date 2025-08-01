from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel

# Plan Constraints
@dataclass
class PlanConstraints:
    copay: int
    deductible: int
    network_providers: List[str]
    geographic_scope: str
    specialty_access: List[str]

# Context Retrieval
@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    relevance_score: float

@dataclass
class QueryMetadata:
    query: str
    optimization_type: str
    timestamp: datetime

@dataclass
class ContextRetrievalResult:
    web_search_results: List[SearchResult]
    relevant_strategies: List[Dict[str, Any]]
    query_metadata: QueryMetadata

# Strategy Types
@dataclass
class StrategyScores:
    speed: float  # 0.0-1.0
    cost: float   # 0.0-1.0
    effort: float # 0.0-1.0

@dataclass
class Strategy:
    id: str
    title: str
    category: str
    approach: str
    rationale: str
    actionable_steps: List[str]
    plan_constraints: PlanConstraints
    llm_scores: StrategyScores
    content_hash: str
    validation_status: str
    created_at: datetime

# Validation Types
@dataclass
class ValidationReason:
    category: Literal['legal', 'feasibility', 'ethical']
    description: str
    severity: Literal['info', 'warning', 'critical']

@dataclass
class SourceReference:
    source: str
    url: Optional[str]
    confidence: float

@dataclass
class ValidationResult:
    strategy_id: str
    compliance_status: Literal['approved', 'flagged', 'rejected']
    validation_reasons: List[ValidationReason]
    confidence_score: float
    source_references: List[SourceReference]

# Storage Types
@dataclass
class StorageResult:
    strategy_id: str
    storage_status: Literal['success', 'failed', 'duplicate']
    message: str
    timestamp: datetime

# Workflow State
@dataclass
class StrategyWorkflowState:
    plan_constraints: PlanConstraints
    context_result: Optional[ContextRetrievalResult] = None
    strategies: Optional[List[Strategy]] = None
    validation_results: Optional[List[ValidationResult]] = None
    storage_confirmation: Optional[StorageResult] = None
    errors: Optional[List[str]] = None

# Configuration Types
@dataclass
class WorkflowConfig:
    use_mock: bool = False
    timeout_seconds: int = 30
    max_retries: int = 3
    enable_logging: bool = True
    enable_audit_trail: bool = True 