"""
Embedding Validation Module

This module provides comprehensive validation for embeddings to detect
zero embeddings, invalid embeddings, and other quality issues.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class EmbeddingIssueType(Enum):
    """Classification of embedding issues"""
    ALL_ZEROS = "all_zeros"
    MOSTLY_ZEROS = "mostly_zeros"
    INVALID_DIMENSIONS = "invalid_dimensions"
    EXTREME_VALUES = "extreme_values"
    NAN_VALUES = "nan_values"
    INFINITE_VALUES = "infinite_values"
    INSUFFICIENT_VARIANCE = "insufficient_variance"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    VALID = "valid"


@dataclass
class EmbeddingValidationResult:
    """Result of embedding validation"""
    is_valid: bool
    issue_type: EmbeddingIssueType
    severity: str  # "critical", "warning", "info"
    confidence: float  # 0.0 to 1.0
    details: str
    metrics: Dict[str, Any]
    recommendations: List[str]


class EmbeddingValidator:
    """
    Comprehensive embedding validator with issue detection and classification.
    
    This validator can detect:
    - Zero embeddings (all zeros or mostly zeros)
    - Invalid dimensions
    - Extreme values
    - NaN or infinite values
    - Insufficient variance (potentially mock/fake embeddings)
    - Suspicious patterns
    """
    
    def __init__(self, expected_dimension: int = 1536, logger_name: str = "embedding_validator"):
        self.expected_dimension = expected_dimension
        self.logger = logging.getLogger(logger_name)
        
        # Validation thresholds
        self.thresholds = {
            "zero_tolerance": 1e-10,  # Values below this are considered zero
            "mostly_zeros_threshold": 0.95,  # If >95% of values are near zero
            "extreme_value_threshold": 10.0,  # Values above this are suspicious
            "min_variance_threshold": 1e-6,  # Minimum variance for real embeddings
            "max_repetition_threshold": 0.8,  # Max fraction of repeated values
        }
    
    def validate_embedding(
        self, 
        embedding: List[float], 
        source_info: Optional[Dict[str, Any]] = None
    ) -> EmbeddingValidationResult:
        """
        Comprehensive validation of a single embedding.
        
        Args:
            embedding: The embedding vector to validate
            source_info: Optional context about the embedding source
            
        Returns:
            EmbeddingValidationResult with validation details
        """
        if source_info is None:
            source_info = {}
        
        # Convert to numpy array for analysis
        try:
            arr = np.array(embedding, dtype=float)
        except (ValueError, TypeError) as e:
            return EmbeddingValidationResult(
                is_valid=False,
                issue_type=EmbeddingIssueType.INVALID_DIMENSIONS,
                severity="critical",
                confidence=1.0,
                details=f"Cannot convert embedding to numeric array: {str(e)}",
                metrics={"error": str(e)},
                recommendations=["Check embedding generation process", "Verify data types"]
            )
        
        # Check dimensions
        if len(arr) != self.expected_dimension:
            return EmbeddingValidationResult(
                is_valid=False,
                issue_type=EmbeddingIssueType.INVALID_DIMENSIONS,
                severity="critical",
                confidence=1.0,
                details=f"Wrong dimension: {len(arr)} (expected {self.expected_dimension})",
                metrics={"actual_dimension": len(arr), "expected_dimension": self.expected_dimension},
                recommendations=["Check embedding model configuration", "Verify OpenAI API response"]
            )
        
        # Check for NaN or infinite values
        if np.any(np.isnan(arr)):
            return EmbeddingValidationResult(
                is_valid=False,
                issue_type=EmbeddingIssueType.NAN_VALUES,
                severity="critical",
                confidence=1.0,
                details="Embedding contains NaN values",
                metrics={"nan_count": np.sum(np.isnan(arr))},
                recommendations=["Check embedding generation API", "Verify input text quality"]
            )
        
        if np.any(np.isinf(arr)):
            return EmbeddingValidationResult(
                is_valid=False,
                issue_type=EmbeddingIssueType.INFINITE_VALUES,
                severity="critical",
                confidence=1.0,
                details="Embedding contains infinite values",
                metrics={"inf_count": np.sum(np.isinf(arr))},
                recommendations=["Check embedding generation API", "Verify input text quality"]
            )
        
        # Check for all zeros
        zero_mask = np.abs(arr) < self.thresholds["zero_tolerance"]
        zero_fraction = np.mean(zero_mask)
        
        if zero_fraction == 1.0:
            return EmbeddingValidationResult(
                is_valid=False,
                issue_type=EmbeddingIssueType.ALL_ZEROS,
                severity="critical",
                confidence=1.0,
                details="All embedding values are zero",
                metrics={
                    "zero_fraction": zero_fraction,
                    "max_abs_value": float(np.max(np.abs(arr))),
                    "source_info": source_info
                },
                recommendations=[
                    "Check if OpenAI API key is valid",
                    "Verify input text is not empty",
                    "Check for API rate limiting",
                    "Ensure embedding model is properly configured"
                ]
            )
        
        # Check for mostly zeros
        if zero_fraction > self.thresholds["mostly_zeros_threshold"]:
            return EmbeddingValidationResult(
                is_valid=False,
                issue_type=EmbeddingIssueType.MOSTLY_ZEROS,
                severity="critical",
                confidence=0.9,
                details=f"{zero_fraction*100:.1f}% of embedding values are zero",
                metrics={
                    "zero_fraction": zero_fraction,
                    "non_zero_count": int(np.sum(~zero_mask)),
                    "max_abs_value": float(np.max(np.abs(arr))),
                    "source_info": source_info
                },
                recommendations=[
                    "Check embedding generation API health",
                    "Verify input text quality and length",
                    "Check for partial API failures"
                ]
            )
        
        # Check for extreme values
        max_abs_value = np.max(np.abs(arr))
        if max_abs_value > self.thresholds["extreme_value_threshold"]:
            return EmbeddingValidationResult(
                is_valid=False,
                issue_type=EmbeddingIssueType.EXTREME_VALUES,
                severity="warning",
                confidence=0.7,
                details=f"Extreme values detected (max: {max_abs_value:.3f})",
                metrics={
                    "max_abs_value": float(max_abs_value),
                    "min_value": float(np.min(arr)),
                    "max_value": float(np.max(arr)),
                    "source_info": source_info
                },
                recommendations=[
                    "Check input text for unusual content",
                    "Verify embedding model behavior",
                    "Consider normalizing embeddings"
                ]
            )
        
        # Check variance (insufficient variance suggests mock/fake embeddings)
        variance = np.var(arr)
        if variance < self.thresholds["min_variance_threshold"]:
            return EmbeddingValidationResult(
                is_valid=False,
                issue_type=EmbeddingIssueType.INSUFFICIENT_VARIANCE,
                severity="warning",
                confidence=0.8,
                details=f"Very low variance ({variance:.2e}) suggests mock embedding",
                metrics={
                    "variance": float(variance),
                    "std_dev": float(np.std(arr)),
                    "source_info": source_info
                },
                recommendations=[
                    "Check if mock embeddings are being generated",
                    "Verify real API is being used",
                    "Check embedding generation configuration"
                ]
            )
        
        # Check for suspicious patterns (too many repeated values)
        unique_values = len(np.unique(arr))
        repetition_fraction = 1.0 - (unique_values / len(arr))
        if repetition_fraction > self.thresholds["max_repetition_threshold"]:
            return EmbeddingValidationResult(
                is_valid=False,
                issue_type=EmbeddingIssueType.SUSPICIOUS_PATTERN,
                severity="warning",
                confidence=0.6,
                details=f"High repetition ({repetition_fraction*100:.1f}%) suggests pattern generation",
                metrics={
                    "unique_values": unique_values,
                    "total_values": len(arr),
                    "repetition_fraction": repetition_fraction,
                    "source_info": source_info
                },
                recommendations=[
                    "Check embedding generation algorithm",
                    "Verify input text diversity",
                    "Check for algorithmic bias"
                ]
            )
        
        # If we get here, the embedding appears valid
        return EmbeddingValidationResult(
            is_valid=True,
            issue_type=EmbeddingIssueType.VALID,
            severity="info",
            confidence=1.0,
            details="Embedding appears valid",
            metrics={
                "dimension": len(arr),
                "zero_fraction": float(zero_fraction),
                "variance": float(variance),
                "max_abs_value": float(max_abs_value),
                "unique_values": unique_values,
                "source_info": source_info
            },
            recommendations=[]
        )
    
    def validate_batch(
        self, 
        embeddings: List[List[float]], 
        source_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[EmbeddingValidationResult], Dict[str, Any]]:
        """
        Validate a batch of embeddings and provide summary statistics.
        
        Args:
            embeddings: List of embedding vectors to validate
            source_info: Optional context about the embedding source
            
        Returns:
            Tuple of (individual results, batch summary)
        """
        results = []
        issue_counts = {issue_type: 0 for issue_type in EmbeddingIssueType}
        
        for i, embedding in enumerate(embeddings):
            individual_source_info = (source_info or {}).copy()
            individual_source_info["batch_index"] = i
            
            result = self.validate_embedding(embedding, individual_source_info)
            results.append(result)
            issue_counts[result.issue_type] += 1
        
        # Generate batch summary
        total_embeddings = len(embeddings)
        critical_issues = sum(1 for r in results if r.severity == "critical")
        warning_issues = sum(1 for r in results if r.severity == "warning")
        
        batch_summary = {
            "total_embeddings": total_embeddings,
            "valid_embeddings": issue_counts[EmbeddingIssueType.VALID],
            "critical_issues": critical_issues,
            "warning_issues": warning_issues,
            "issue_breakdown": dict(issue_counts),
            "validation_timestamp": datetime.utcnow().isoformat(),
            "batch_health_score": (total_embeddings - critical_issues) / total_embeddings if total_embeddings > 0 else 0.0
        }
        
        return results, batch_summary
    
    def create_error_from_validation_result(
        self, 
        result: EmbeddingValidationResult, 
        context: Optional[Dict[str, Any]] = None
    ) -> Exception:
        """
        Create appropriate exception from validation result.
        
        Args:
            result: Validation result
            context: Additional context for error
            
        Returns:
            Appropriate exception type
        """
        if result.is_valid:
            return None
        
        error_message = f"Embedding validation failed: {result.details}"
        
        if context:
            error_message += f" Context: {context}"
        
        if result.severity == "critical":
            if result.issue_type in [EmbeddingIssueType.ALL_ZEROS, EmbeddingIssueType.MOSTLY_ZEROS]:
                return ValueError(f"ZERO_EMBEDDING_DETECTED: {error_message}")
            elif result.issue_type == EmbeddingIssueType.INVALID_DIMENSIONS:
                return ValueError(f"INVALID_EMBEDDING_DIMENSIONS: {error_message}")
            elif result.issue_type in [EmbeddingIssueType.NAN_VALUES, EmbeddingIssueType.INFINITE_VALUES]:
                return ValueError(f"INVALID_EMBEDDING_VALUES: {error_message}")
            else:
                return RuntimeError(f"EMBEDDING_VALIDATION_CRITICAL: {error_message}")
        else:
            return Warning(f"EMBEDDING_VALIDATION_WARNING: {error_message}")