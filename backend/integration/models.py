"""
Data models for the integration service between upload pipeline and agent workflows.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class DocumentRAGStatus:
    """Status of a document's RAG readiness."""
    document_id: str
    filename: str
    user_id: str
    is_rag_ready: bool
    chunk_count: int
    vector_quality_score: float
    last_updated: Optional[datetime] = None
    processing_status: Optional[str] = None


@dataclass
class RAGQueryTestResult:
    """Result of a test RAG query."""
    document_id: str
    query_successful: bool
    top_similarity: float
    chunks_found: int
    response_time: float
    error_message: Optional[str] = None
    query_vector: Optional[List[float]] = None


@dataclass
class SystemHealthStatus:
    """Health status of a system component."""
    component_name: str
    status: HealthStatus
    message: str
    last_check: datetime
    response_time: Optional[float] = None
    error_details: Optional[str] = None


@dataclass
class IntegrationHealthStatus:
    """Overall integration health status."""
    overall_status: HealthStatus
    upload_pipeline_status: SystemHealthStatus
    agent_system_status: SystemHealthStatus
    database_status: SystemHealthStatus
    mock_services_status: SystemHealthStatus
    last_check: datetime
    performance_metrics: Dict[str, Any]
    recommendations: List[str]


@dataclass
class RAGQueryTestRequest:
    """Request for testing RAG functionality."""
    document_id: str
    user_id: str
    test_query: str
    similarity_threshold: float = 0.7
    max_chunks: int = 5


@dataclass
class IntegrationMetrics:
    """Performance and reliability metrics for the integration."""
    upload_processing_time_avg: float
    rag_query_time_avg: float
    agent_response_time_avg: float
    concurrent_operation_success_rate: float
    error_rate: float
    last_updated: datetime
    sample_size: int
