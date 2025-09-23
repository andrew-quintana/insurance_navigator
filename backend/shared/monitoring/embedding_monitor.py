"""
Embedding Quality Monitor

This module provides real-time monitoring and alerting for embedding quality issues.
It integrates with the existing pipeline to detect and report zero embeddings and other issues.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json

from ..validation.embedding_validator import EmbeddingValidator, EmbeddingValidationResult, EmbeddingIssueType


@dataclass
class EmbeddingQualityMetrics:
    """Metrics for embedding quality monitoring"""
    total_embeddings_processed: int = 0
    valid_embeddings: int = 0
    zero_embeddings: int = 0
    mostly_zero_embeddings: int = 0
    invalid_dimension_embeddings: int = 0
    extreme_value_embeddings: int = 0
    suspicious_pattern_embeddings: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    quality_score: float = 1.0  # 0.0 to 1.0
    alerts_sent: int = 0
    
    def update_quality_score(self):
        """Update overall quality score based on metrics"""
        if self.total_embeddings_processed == 0:
            self.quality_score = 1.0
            return
        
        # Critical issues (zero embeddings, invalid dimensions) heavily penalize score
        critical_issues = self.zero_embeddings + self.mostly_zero_embeddings + self.invalid_dimension_embeddings
        critical_penalty = (critical_issues / self.total_embeddings_processed) * 0.8
        
        # Warning issues (extreme values, patterns) lightly penalize score
        warning_issues = self.extreme_value_embeddings + self.suspicious_pattern_embeddings
        warning_penalty = (warning_issues / self.total_embeddings_processed) * 0.2
        
        self.quality_score = max(0.0, 1.0 - critical_penalty - warning_penalty)


class EmbeddingQualityMonitor:
    """
    Real-time monitor for embedding quality with alerting capabilities.
    
    Features:
    - Real-time validation of embeddings
    - Quality metrics tracking
    - Alerting for critical issues
    - Batch processing with summary reports
    - Integration with existing logging infrastructure
    """
    
    def __init__(
        self, 
        validator: Optional[EmbeddingValidator] = None,
        alert_callback: Optional[Callable] = None,
        logger_name: str = "embedding_monitor"
    ):
        self.validator = validator or EmbeddingValidator()
        self.alert_callback = alert_callback
        self.logger = logging.getLogger(logger_name)
        
        # Metrics tracking
        self.metrics = EmbeddingQualityMetrics()
        self.recent_results: List[EmbeddingValidationResult] = []
        self.max_recent_results = 1000  # Keep last 1000 results for analysis
        
        # Alert configuration
        self.alert_thresholds = {
            "critical_issue_threshold": 0.05,  # Alert if >5% critical issues
            "quality_score_threshold": 0.8,    # Alert if quality score <0.8
            "zero_embedding_immediate": True,   # Immediate alert for zero embeddings
            "batch_size_threshold": 10,        # Minimum batch size for alerts
        }
        
        # Alert rate limiting
        self.last_alert_time = {}
        self.alert_cooldown = timedelta(minutes=5)  # 5 minute cooldown between similar alerts
    
    async def validate_embedding(
        self, 
        embedding: List[float], 
        source_info: Optional[Dict[str, Any]] = None,
        raise_on_critical: bool = True
    ) -> EmbeddingValidationResult:
        """
        Validate single embedding with monitoring and alerting.
        
        Args:
            embedding: The embedding vector to validate
            source_info: Context about the embedding source
            raise_on_critical: Whether to raise exception on critical issues
            
        Returns:
            EmbeddingValidationResult
            
        Raises:
            Exception: If critical issue detected and raise_on_critical=True
        """
        result = self.validator.validate_embedding(embedding, source_info)
        
        # Update metrics
        self._update_metrics_from_result(result)
        
        # Store recent result
        self.recent_results.append(result)
        if len(self.recent_results) > self.max_recent_results:
            self.recent_results.pop(0)
        
        # Handle critical issues
        if not result.is_valid and result.severity == "critical":
            await self._handle_critical_issue(result, source_info)
            
            if raise_on_critical:
                error = self.validator.create_error_from_validation_result(result, source_info)
                if error and isinstance(error, Exception):
                    raise error
        
        # Handle warnings
        elif not result.is_valid and result.severity == "warning":
            await self._handle_warning_issue(result, source_info)
        
        return result
    
    async def validate_batch(
        self, 
        embeddings: List[List[float]], 
        source_info: Optional[Dict[str, Any]] = None,
        raise_on_critical: bool = True
    ) -> Tuple[List[EmbeddingValidationResult], Dict[str, Any]]:
        """
        Validate batch of embeddings with monitoring and alerting.
        
        Args:
            embeddings: List of embedding vectors to validate
            source_info: Context about the embedding source
            raise_on_critical: Whether to raise exception on critical issues
            
        Returns:
            Tuple of (validation results, batch summary)
        """
        results, batch_summary = self.validator.validate_batch(embeddings, source_info)
        
        # Update metrics from batch
        for result in results:
            self._update_metrics_from_result(result)
        
        # Store recent results
        self.recent_results.extend(results)
        if len(self.recent_results) > self.max_recent_results:
            self.recent_results = self.recent_results[-self.max_recent_results:]
        
        # Check for batch-level alerts
        await self._check_batch_alerts(results, batch_summary, source_info)
        
        # Handle critical issues in batch
        critical_results = [r for r in results if not r.is_valid and r.severity == "critical"]
        if critical_results and raise_on_critical:
            # Raise error for first critical issue
            first_critical = critical_results[0]
            error = self.validator.create_error_from_validation_result(first_critical, source_info)
            if error and isinstance(error, Exception):
                raise error
        
        return results, batch_summary
    
    def _update_metrics_from_result(self, result: EmbeddingValidationResult):
        """Update metrics based on validation result"""
        self.metrics.total_embeddings_processed += 1
        
        if result.is_valid:
            self.metrics.valid_embeddings += 1
        else:
            if result.issue_type == EmbeddingIssueType.ALL_ZEROS:
                self.metrics.zero_embeddings += 1
            elif result.issue_type == EmbeddingIssueType.MOSTLY_ZEROS:
                self.metrics.mostly_zero_embeddings += 1
            elif result.issue_type == EmbeddingIssueType.INVALID_DIMENSIONS:
                self.metrics.invalid_dimension_embeddings += 1
            elif result.issue_type == EmbeddingIssueType.EXTREME_VALUES:
                self.metrics.extreme_value_embeddings += 1
            elif result.issue_type == EmbeddingIssueType.SUSPICIOUS_PATTERN:
                self.metrics.suspicious_pattern_embeddings += 1
        
        self.metrics.last_updated = datetime.utcnow()
        self.metrics.update_quality_score()
    
    async def _handle_critical_issue(self, result: EmbeddingValidationResult, source_info: Optional[Dict[str, Any]]):
        """Handle critical embedding issues with immediate alerting"""
        alert_key = f"critical_{result.issue_type.value}"
        
        # Check if we should send an alert (rate limiting)
        if self._should_send_alert(alert_key):
            await self._send_alert("CRITICAL", result, source_info)
            self.metrics.alerts_sent += 1
        
        # Always log critical issues
        self.logger.error(
            "Critical embedding issue detected",
            extra={
                "issue_type": result.issue_type.value,
                "details": result.details,
                "confidence": result.confidence,
                "metrics": result.metrics,
                "source_info": source_info,
                "recommendations": result.recommendations
            }
        )
    
    async def _handle_warning_issue(self, result: EmbeddingValidationResult, source_info: Optional[Dict[str, Any]]):
        """Handle warning embedding issues"""
        self.logger.warning(
            "Embedding quality warning",
            extra={
                "issue_type": result.issue_type.value,
                "details": result.details,
                "confidence": result.confidence,
                "metrics": result.metrics,
                "source_info": source_info,
                "recommendations": result.recommendations
            }
        )
    
    async def _check_batch_alerts(
        self, 
        results: List[EmbeddingValidationResult], 
        batch_summary: Dict[str, Any], 
        source_info: Optional[Dict[str, Any]]
    ):
        """Check if batch-level alerts should be sent"""
        total_embeddings = len(results)
        
        # Skip if batch is too small
        if total_embeddings < self.alert_thresholds["batch_size_threshold"]:
            return
        
        critical_count = batch_summary.get("critical_issues", 0)
        critical_rate = critical_count / total_embeddings
        
        # Check critical issue rate
        if critical_rate > self.alert_thresholds["critical_issue_threshold"]:
            alert_key = "batch_critical_rate"
            if self._should_send_alert(alert_key):
                await self._send_batch_alert("HIGH_CRITICAL_RATE", batch_summary, source_info)
                self.metrics.alerts_sent += 1
        
        # Check quality score
        health_score = batch_summary.get("batch_health_score", 1.0)
        if health_score < self.alert_thresholds["quality_score_threshold"]:
            alert_key = "batch_low_quality"
            if self._should_send_alert(alert_key):
                await self._send_batch_alert("LOW_QUALITY_SCORE", batch_summary, source_info)
                self.metrics.alerts_sent += 1
    
    def _should_send_alert(self, alert_key: str) -> bool:
        """Check if alert should be sent based on rate limiting"""
        now = datetime.utcnow()
        last_alert = self.last_alert_time.get(alert_key)
        
        if last_alert is None or (now - last_alert) > self.alert_cooldown:
            self.last_alert_time[alert_key] = now
            return True
        
        return False
    
    async def _send_alert(self, severity: str, result: EmbeddingValidationResult, source_info: Optional[Dict[str, Any]]):
        """Send alert for individual embedding issue"""
        alert_data = {
            "alert_type": "EMBEDDING_QUALITY_ISSUE",
            "severity": severity,
            "issue_type": result.issue_type.value,
            "details": result.details,
            "confidence": result.confidence,
            "metrics": result.metrics,
            "source_info": source_info,
            "recommendations": result.recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if self.alert_callback:
            try:
                await self.alert_callback(alert_data)
            except Exception as e:
                self.logger.error(f"Failed to send alert: {str(e)}")
        
        # Also log as structured data
        self.logger.error(
            f"EMBEDDING_ALERT: {severity} - {result.issue_type.value}",
            extra=alert_data
        )
    
    async def _send_batch_alert(self, alert_type: str, batch_summary: Dict[str, Any], source_info: Optional[Dict[str, Any]]):
        """Send alert for batch-level issues"""
        alert_data = {
            "alert_type": f"BATCH_{alert_type}",
            "severity": "WARNING",
            "batch_summary": batch_summary,
            "source_info": source_info,
            "current_metrics": self.get_metrics_summary(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if self.alert_callback:
            try:
                await self.alert_callback(alert_data)
            except Exception as e:
                self.logger.error(f"Failed to send batch alert: {str(e)}")
        
        # Also log as structured data
        self.logger.warning(
            f"BATCH_ALERT: {alert_type}",
            extra=alert_data
        )
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        return {
            "total_processed": self.metrics.total_embeddings_processed,
            "valid_count": self.metrics.valid_embeddings,
            "zero_count": self.metrics.zero_embeddings,
            "mostly_zero_count": self.metrics.mostly_zero_embeddings,
            "invalid_dimension_count": self.metrics.invalid_dimension_embeddings,
            "extreme_value_count": self.metrics.extreme_value_embeddings,
            "suspicious_pattern_count": self.metrics.suspicious_pattern_embeddings,
            "quality_score": self.metrics.quality_score,
            "alerts_sent": self.metrics.alerts_sent,
            "last_updated": self.metrics.last_updated.isoformat()
        }
    
    def get_recent_issues(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent embedding issues for debugging"""
        recent_issues = [
            {
                "issue_type": r.issue_type.value,
                "severity": r.severity,
                "details": r.details,
                "confidence": r.confidence,
                "metrics": r.metrics
            }
            for r in self.recent_results 
            if not r.is_valid
        ]
        
        return recent_issues[-limit:] if recent_issues else []
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)"""
        self.metrics = EmbeddingQualityMetrics()
        self.recent_results.clear()
        self.last_alert_time.clear()