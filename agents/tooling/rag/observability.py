"""
RAG Observability Module

This module provides enhanced observability features for RAG operations including:
- Similarity histogram logging with UUID traceability
- Performance monitoring and metrics collection
- Configurable threshold management
- Operation correlation and debugging support

Implements Phase 4 requirements for RAG Performance & Observability.
"""

import uuid
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class RAGOperationMetrics:
    """Metrics for a single RAG operation."""
    operation_uuid: str
    user_id: str
    query_text: Optional[str] = None
    query_embedding_dim: Optional[int] = None
    similarity_threshold: float = 0.5
    max_chunks: int = 5
    token_budget: int = 4000
    
    # Performance metrics
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    
    # Retrieval metrics
    total_chunks_available: int = 0
    chunks_above_threshold: int = 0
    chunks_returned: int = 0
    total_tokens_used: int = 0
    
    # Similarity distribution
    similarity_scores: List[float] = field(default_factory=list)
    histogram_bins: List[float] = field(default_factory=lambda: [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    histogram_counts: List[int] = field(default_factory=list)
    
    # Quality metrics
    avg_similarity: Optional[float] = None
    min_similarity: Optional[float] = None
    max_similarity: Optional[float] = None
    median_similarity: Optional[float] = None
    
    # Status
    success: bool = True
    error_message: Optional[str] = None


class RAGObservabilityLogger:
    """Enhanced logging for RAG operations with histogram support."""
    
    def __init__(self, logger_name: str = "RAGObservability"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        
        # Ensure we have a handler
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def generate_operation_uuid(self) -> str:
        """Generate a new operation UUID for traceability."""
        return str(uuid.uuid4())
    
    def log_similarity_histogram(self, similarities: List[float], operation_uuid: str, **kwargs):
        """
        Log similarity histogram with developer-friendly format.
        
        Args:
            similarities: List of similarity scores
            operation_uuid: Operation UUID for traceability
            **kwargs: Additional context data
        """
        if not similarities:
            self.logger.info(f"RAG Similarity Distribution [{operation_uuid}]: No similarities to log", **kwargs)
            return
        
        # Define histogram bins
        bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        
        # Calculate histogram
        hist_counts, _ = np.histogram(similarities, bins=bins)
        
        # Create developer-friendly histogram string
        hist_parts = []
        for i, count in enumerate(hist_counts):
            bin_start = bins[i]
            bin_end = bins[i + 1]
            hist_parts.append(f"{bin_start:.1f}-{bin_end:.1f}:{count}")
        
        histogram_str = " ".join(hist_parts)
        
        # Calculate statistics
        avg_sim = np.mean(similarities)
        min_sim = np.min(similarities)
        max_sim = np.max(similarities)
        median_sim = np.median(similarities)
        
        # Log the histogram with context
        log_message = (
            f"RAG Similarity Distribution [{operation_uuid}]: {histogram_str} | "
            f"Avg:{avg_sim:.3f} Min:{min_sim:.3f} Max:{max_sim:.3f} Median:{median_sim:.3f}"
        )
        
        # Create structured log data
        log_data = {
            "operation_uuid": operation_uuid,
            "histogram": histogram_str,
            "avg_similarity": avg_sim,
            "min_similarity": min_sim,
            "max_similarity": max_sim,
            "median_similarity": median_sim,
            "total_scores": len(similarities),
            **kwargs
        }
        
        # Log with structured data
        self.logger.info(f"{log_message} | Data: {json.dumps(log_data)}")
    
    def log_rag_operation_start(self, operation_uuid: str, user_id: str, query_text: Optional[str] = None, **kwargs):
        """Log the start of a RAG operation."""
        log_message = f"RAG Operation Started [{operation_uuid}]"
        log_data = {
            "operation_uuid": operation_uuid,
            "user_id": user_id,
            "query_text": query_text,
            "event_type": "rag_operation_start",
            **kwargs
        }
        self.logger.info(f"{log_message} | Data: {json.dumps(log_data)}")
    
    def log_rag_operation_end(self, metrics: RAGOperationMetrics, **kwargs):
        """Log the completion of a RAG operation with full metrics."""
        # Log similarity histogram if we have scores
        if metrics.similarity_scores:
            self.log_similarity_histogram(
                metrics.similarity_scores, 
                metrics.operation_uuid,
                user_id=metrics.user_id,
                **kwargs
            )
        
        # Log operation summary
        status = "SUCCESS" if metrics.success else "FAILED"
        log_message = (
            f"RAG Operation {status} [{metrics.operation_uuid}] - "
            f"Duration:{metrics.duration_ms:.1f}ms "
            f"Chunks:{metrics.chunks_returned}/{metrics.chunks_above_threshold} "
            f"Tokens:{metrics.total_tokens_used}"
        )
        log_data = {
            "operation_uuid": metrics.operation_uuid,
            "user_id": metrics.user_id,
            "status": status,
            "duration_ms": metrics.duration_ms,
            "chunks_returned": metrics.chunks_returned,
            "chunks_above_threshold": metrics.chunks_above_threshold,
            "total_chunks_available": metrics.total_chunks_available,
            "total_tokens_used": metrics.total_tokens_used,
            "similarity_threshold": metrics.similarity_threshold,
            "avg_similarity": metrics.avg_similarity,
            "event_type": "rag_operation_end",
            **kwargs
        }
        self.logger.info(f"{log_message} | Data: {json.dumps(log_data)}")
        
        # Log error details if operation failed
        if not metrics.success and metrics.error_message:
            log_message = f"RAG Operation Error [{metrics.operation_uuid}]: {metrics.error_message}"
            log_data = {
                "operation_uuid": metrics.operation_uuid,
                "user_id": metrics.user_id,
                "error_message": metrics.error_message,
                "event_type": "rag_operation_error",
                **kwargs
            }
            self.logger.error(f"{log_message} | Data: {json.dumps(log_data)}")
    
    def log_threshold_analysis(self, operation_uuid: str, similarities: List[float], 
                             current_threshold: float, suggested_threshold: Optional[float] = None, **kwargs):
        """Log threshold analysis for optimization."""
        if not similarities:
            return
        
        above_threshold = sum(1 for s in similarities if s >= current_threshold)
        total_scores = len(similarities)
        threshold_effectiveness = above_threshold / total_scores if total_scores > 0 else 0
        
        log_message = (
            f"RAG Threshold Analysis [{operation_uuid}]: "
            f"Current:{current_threshold:.3f} Above:{above_threshold}/{total_scores} "
            f"({threshold_effectiveness:.1%})"
        )
        log_data = {
            "operation_uuid": operation_uuid,
            "current_threshold": current_threshold,
            "suggested_threshold": suggested_threshold,
            "above_threshold_count": above_threshold,
            "total_scores": total_scores,
            "threshold_effectiveness": threshold_effectiveness,
            "event_type": "rag_threshold_analysis",
            **kwargs
        }
        self.logger.info(f"{log_message} | Data: {json.dumps(log_data)}")


class RAGPerformanceMonitor:
    """Performance monitoring for RAG operations."""
    
    def __init__(self, logger: Optional[RAGObservabilityLogger] = None):
        self.logger = logger or RAGObservabilityLogger()
        self.operation_metrics: Dict[str, RAGOperationMetrics] = {}
    
    def start_operation(self, user_id: str, query_text: Optional[str] = None, 
                       similarity_threshold: float = 0.5, max_chunks: int = 5, 
                       token_budget: int = 4000) -> RAGOperationMetrics:
        """Start monitoring a RAG operation."""
        operation_uuid = self.logger.generate_operation_uuid()
        
        metrics = RAGOperationMetrics(
            operation_uuid=operation_uuid,
            user_id=user_id,
            query_text=query_text,
            similarity_threshold=similarity_threshold,
            max_chunks=max_chunks,
            token_budget=token_budget,
            start_time=datetime.utcnow()
        )
        
        self.operation_metrics[operation_uuid] = metrics
        
        self.logger.log_rag_operation_start(
            operation_uuid=operation_uuid,
            user_id=user_id,
            query_text=query_text,
            similarity_threshold=similarity_threshold,
            max_chunks=max_chunks,
            token_budget=token_budget
        )
        
        return metrics
    
    def record_similarity_scores(self, operation_uuid: str, similarities: List[float]):
        """Record similarity scores for an operation."""
        if operation_uuid not in self.operation_metrics:
            return
        
        metrics = self.operation_metrics[operation_uuid]
        metrics.similarity_scores = similarities
        
        if similarities:
            metrics.avg_similarity = float(np.mean(similarities))
            metrics.min_similarity = float(np.min(similarities))
            metrics.max_similarity = float(np.max(similarities))
            metrics.median_similarity = float(np.median(similarities))
            
            # Calculate histogram
            hist_counts, _ = np.histogram(similarities, bins=metrics.histogram_bins)
            metrics.histogram_counts = hist_counts.tolist()
    
    def record_retrieval_results(self, operation_uuid: str, chunks_returned: int, 
                               total_tokens_used: int, total_chunks_available: int = 0):
        """Record retrieval results for an operation."""
        if operation_uuid not in self.operation_metrics:
            return
        
        metrics = self.operation_metrics[operation_uuid]
        metrics.chunks_returned = chunks_returned
        metrics.total_tokens_used = total_tokens_used
        metrics.total_chunks_available = total_chunks_available
        metrics.chunks_above_threshold = sum(1 for s in metrics.similarity_scores 
                                           if s >= metrics.similarity_threshold)
    
    def complete_operation(self, operation_uuid: str, success: bool = True, 
                          error_message: Optional[str] = None):
        """Complete monitoring for a RAG operation."""
        if operation_uuid not in self.operation_metrics:
            return
        
        metrics = self.operation_metrics[operation_uuid]
        metrics.end_time = datetime.utcnow()
        metrics.success = success
        metrics.error_message = error_message
        
        if metrics.start_time and metrics.end_time:
            duration = (metrics.end_time - metrics.start_time).total_seconds() * 1000
            metrics.duration_ms = duration
        
        # Log the operation completion
        self.logger.log_rag_operation_end(metrics)
        
        # Log threshold analysis
        if metrics.similarity_scores:
            self.logger.log_threshold_analysis(
                operation_uuid=operation_uuid,
                similarities=metrics.similarity_scores,
                current_threshold=metrics.similarity_threshold
            )
        
        # Clean up
        del self.operation_metrics[operation_uuid]
        
        return metrics


class ConfigurableThresholdManager:
    """Manages configurable similarity thresholds per user/context."""
    
    def __init__(self, default_threshold: float = 0.5):
        self.default_threshold = default_threshold
        self.user_thresholds: Dict[str, float] = {}
        self.context_thresholds: Dict[str, float] = {}
        self.logger = RAGObservabilityLogger("ThresholdManager")
    
    def get_threshold(self, user_id: str, context: Optional[str] = None) -> float:
        """Get the appropriate threshold for a user and context."""
        # Check context-specific threshold first
        if context and context in self.context_thresholds:
            threshold = self.context_thresholds[context]
            self.logger.logger.debug(f"Using context threshold {threshold} for context '{context}'")
            return threshold
        
        # Check user-specific threshold
        if user_id in self.user_thresholds:
            threshold = self.user_thresholds[user_id]
            self.logger.logger.debug(f"Using user threshold {threshold} for user '{user_id}'")
            return threshold
        
        # Use default threshold
        self.logger.logger.debug(f"Using default threshold {self.default_threshold}")
        return self.default_threshold
    
    def set_user_threshold(self, user_id: str, threshold: float):
        """Set a custom threshold for a specific user."""
        if not 0.0 < threshold <= 1.0:
            raise ValueError("Threshold must be in (0, 1]")
        
        self.user_thresholds[user_id] = threshold
        self.logger.logger.info(f"Set threshold {threshold} for user '{user_id}'")
    
    def set_context_threshold(self, context: str, threshold: float):
        """Set a custom threshold for a specific context."""
        if not 0.0 < threshold <= 1.0:
            raise ValueError("Threshold must be in (0, 1]")
        
        self.context_thresholds[context] = threshold
        self.logger.logger.info(f"Set threshold {threshold} for context '{context}'")
    
    def reset_user_threshold(self, user_id: str):
        """Reset a user to use the default threshold."""
        if user_id in self.user_thresholds:
            del self.user_thresholds[user_id]
            self.logger.logger.info(f"Reset threshold for user '{user_id}' to default")
    
    def reset_context_threshold(self, context: str):
        """Reset a context to use the default threshold."""
        if context in self.context_thresholds:
            del self.context_thresholds[context]
            self.logger.logger.info(f"Reset threshold for context '{context}' to default")
    
    def get_all_thresholds(self) -> Dict[str, Any]:
        """Get all configured thresholds for debugging."""
        return {
            "default_threshold": self.default_threshold,
            "user_thresholds": self.user_thresholds,
            "context_thresholds": self.context_thresholds
        }


# Global instances for easy access
rag_observability_logger = RAGObservabilityLogger()
rag_performance_monitor = RAGPerformanceMonitor(rag_observability_logger)
threshold_manager = ConfigurableThresholdManager(default_threshold=0.5)
