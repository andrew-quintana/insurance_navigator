import logging
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import traceback
import sys

class StructuredLogger:
    """Structured logger with correlation IDs and comprehensive logging capabilities"""
    
    def __init__(self, name: str, level: str = "INFO"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Add handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _format_log(self, level: str, message: str, **kwargs) -> str:
        """Format log message with structured data"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "logger": self.name,
            "level": level,
            "message": message,
            **kwargs
        }
        
        # Filter out None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        return json.dumps(log_data, default=str)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data"""
        formatted_message = self._format_log("INFO", message, **kwargs)
        self.logger.info(formatted_message)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data"""
        formatted_message = self._format_log("WARNING", message, **kwargs)
        self.logger.warning(formatted_message)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data"""
        # Add stack trace for errors
        if "error" in kwargs and "traceback" not in kwargs:
            kwargs["traceback"] = traceback.format_exc()
        
        formatted_message = self._format_log("ERROR", message, **kwargs)
        self.logger.error(formatted_message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data"""
        formatted_message = self._format_log("DEBUG", message, **kwargs)
        self.logger.debug(formatted_message)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with structured data"""
        # Add stack trace for critical errors
        if "error" in kwargs and "traceback" not in kwargs:
            kwargs["traceback"] = traceback.format_exc()
        
        formatted_message = self._format_log("CRITICAL", message, **kwargs)
        self.logger.critical(formatted_message)
    
    def log_event(self, event_type: str, event_code: str, severity: str = "info", **kwargs):
        """Log structured event with predefined taxonomy"""
        valid_types = [
            "stage_started", "stage_done", "retry", "error", "finalized",
            "job_claimed", "job_completed", "buffer_write", "buffer_commit"
        ]
        
        valid_severities = ["info", "warn", "error"]
        
        if event_type not in valid_types:
            self.warning(f"Invalid event type: {event_type}", **kwargs)
            event_type = "unknown"
        
        if severity not in valid_severities:
            severity = "info"
        
        # Map severity to logging level
        severity_map = {
            "info": "INFO",
            "warn": "WARNING", 
            "error": "ERROR"
        }
        
        log_level = severity_map[severity]
        formatted_message = self._format_log(
            log_level, 
            f"Event: {event_type} - {event_code}",
            event_type=event_type,
            event_code=event_code,
            severity=severity,
            **kwargs
        )
        
        getattr(self.logger, severity.lower())(formatted_message)
    
    def log_processing_stage(self, stage: str, job_id: str, correlation_id: str, **kwargs):
        """Log processing stage with correlation tracking"""
        self.info(
            f"Processing stage: {stage}",
            stage=stage,
            job_id=job_id,
            correlation_id=correlation_id,
            **kwargs
        )
    
    def log_state_transition(self, from_status: str, to_status: str, job_id: str, **kwargs):
        """Log state machine transition"""
        self.info(
            f"State transition: {from_status} → {to_status}",
            from_status=from_status,
            to_status=to_status,
            job_id=job_id,
            transition_type="status_change",
            **kwargs
        )
    
    def log_buffer_operation(self, operation: str, table: str, count: int, job_id: str, **kwargs):
        """Log buffer operation with counts"""
        self.info(
            f"Buffer operation: {operation} on {table}",
            operation=operation,
            table=table,
            count=count,
            job_id=job_id,
            **kwargs
        )
    
    def log_external_service_call(self, service: str, operation: str, duration_ms: float, **kwargs):
        """Log external service call with performance metrics"""
        self.info(
            f"External service call: {service}.{operation}",
            service=service,
            operation=operation,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any], **kwargs):
        """Log error with comprehensive context"""
        self.error(
            f"Error occurred: {str(error)}",
            error=str(error),
            error_type=type(error).__name__,
            context=context,
            traceback=traceback.format_exc(),
            **kwargs
        )
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str, **kwargs):
        """Log performance metric"""
        self.info(
            f"Performance metric: {metric_name}",
            metric_name=metric_name,
            value=value,
            unit=unit,
            metric_type="performance",
            **kwargs
        )
    
    def log_health_check(self, component: str, status: str, duration_ms: float, **kwargs):
        """Log health check result"""
        self.info(
            f"Health check: {component} - {status}",
            component=component,
            status=status,
            duration_ms=duration_ms,
            health_check_type="component",
            **kwargs
        )
    
    def get_correlation_id(self) -> str:
        """Generate a new correlation ID for request tracking"""
        return str(uuid.uuid4())
    
    def set_correlation_context(self, correlation_id: str):
        """Set correlation ID context for this logger instance"""
        self.correlation_id = correlation_id
    
    def log_with_correlation(self, message: str, correlation_id: str, **kwargs):
        """Log message with correlation ID"""
        self.info(message, correlation_id=correlation_id, **kwargs)

