"""
AI Workflow Logger for Unified Navigator.

This module provides comprehensive logging and observability for the entire
AI workflow, tracking performance, costs, and decisions at each step.
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel

from ..models import ToolType, SafetyLevel, InputSafetyResult, ToolSelection, ToolExecutionResult


class WorkflowStep(str, Enum):
    """Workflow step identifiers for logging."""
    WORKFLOW_START = "workflow_start"
    INPUT_SANITIZATION = "input_sanitization"
    TOOL_SELECTION = "tool_selection"
    TOOL_EXECUTION = "tool_execution"
    RESPONSE_GENERATION = "response_generation"
    OUTPUT_SANITIZATION = "output_sanitization"
    WORKFLOW_COMPLETION = "workflow_completion"
    ERROR_HANDLING = "error_handling"


class WorkflowEvent(str, Enum):
    """Specific events within workflow steps."""
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    LLM_CALL = "llm_call"
    TOOL_SELECTED = "tool_selected"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    FALLBACK_TRIGGERED = "fallback_triggered"


class LLMInteraction(BaseModel):
    """Model for LLM interaction logging."""
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    processing_time_ms: float
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class WorkflowMetrics(BaseModel):
    """Model for workflow performance metrics."""
    total_processing_time_ms: float
    step_timings: Dict[str, float]
    total_tokens_used: int
    total_estimated_cost: float
    api_calls_made: int
    cache_hit_rate: float
    success: bool


class WorkflowLogger:
    """
    Comprehensive AI workflow logger with structured logging and metrics tracking.
    
    Provides observability for the entire unified navigator workflow including
    performance metrics, cost tracking, decision logging, and error handling.
    """
    
    def __init__(self, logger_name: str = "unified_navigator_workflow"):
        """
        Initialize the workflow logger.
        
        Args:
            logger_name: Name for the logger instance
        """
        self.logger = logging.getLogger(logger_name)
        self.workflow_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.workflow_start_time: Optional[float] = None
        self.step_timings: Dict[str, float] = {}
        self.total_tokens: int = 0
        self.total_cost: float = 0.0
        self.api_calls: int = 0
        self.cache_hits: int = 0
        self.cache_misses: int = 0
    
    def start_workflow(self, user_id: str, user_query: str, session_id: Optional[str] = None) -> str:
        """
        Start a new workflow and initialize tracking.
        
        Args:
            user_id: User identifier
            user_query: User's input query
            session_id: Optional session identifier
            
        Returns:
            Generated workflow ID
        """
        self.workflow_id = str(uuid.uuid4())
        self.user_id = user_id
        self.session_id = session_id
        self.workflow_start_time = time.time()
        self.step_timings = {}
        self.total_tokens = 0
        self.total_cost = 0.0
        self.api_calls = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        self._log_event(
            step=WorkflowStep.WORKFLOW_START,
            event=WorkflowEvent.STARTED,
            data={
                "user_query": user_query[:200] + "..." if len(user_query) > 200 else user_query,
                "query_length": len(user_query),
                "query_word_count": len(user_query.split()),
                "user_id": user_id,
                "session_id": session_id
            }
        )
        
        return self.workflow_id
    
    def log_input_sanitization(
        self,
        query: str,
        safety_result: InputSafetyResult,
        processing_time_ms: float,
        sanitized_query: Optional[str] = None
    ):
        """
        Log input sanitization step.
        
        Args:
            query: Original user query
            safety_result: Safety assessment result
            processing_time_ms: Time taken for sanitization
            sanitized_query: Modified query if sanitization occurred
        """
        step_key = "input_sanitization"
        self.step_timings[step_key] = processing_time_ms
        
        self._log_event(
            step=WorkflowStep.INPUT_SANITIZATION,
            event=WorkflowEvent.COMPLETED,
            data={
                "is_safe": safety_result.is_safe,
                "is_insurance_domain": safety_result.is_insurance_domain,
                "safety_level": safety_result.safety_level.value,
                "confidence_score": safety_result.confidence_score,
                "reasoning": safety_result.reasoning,
                "was_sanitized": sanitized_query is not None,
                "processing_time_ms": processing_time_ms,
                "original_query_length": len(query),
                "sanitized_query_length": len(sanitized_query) if sanitized_query else len(query)
            }
        )
    
    def log_tool_selection(
        self,
        tool_selection: ToolSelection,
        processing_time_ms: float,
        alternatives_considered: Optional[List[ToolType]] = None
    ):
        """
        Log tool selection decision.
        
        Args:
            tool_selection: Selected tool and reasoning
            processing_time_ms: Time taken for selection
            alternatives_considered: Other tools that were considered
        """
        step_key = "tool_selection"
        self.step_timings[step_key] = processing_time_ms
        
        self._log_event(
            step=WorkflowStep.TOOL_SELECTION,
            event=WorkflowEvent.TOOL_SELECTED,
            data={
                "selected_tool": tool_selection.selected_tool.value,
                "reasoning": tool_selection.reasoning,
                "confidence_score": tool_selection.confidence_score,
                "fallback_tool": tool_selection.fallback_tool.value if tool_selection.fallback_tool else None,
                "alternatives_considered": [tool.value for tool in alternatives_considered] if alternatives_considered else [],
                "processing_time_ms": processing_time_ms
            }
        )
    
    def log_tool_execution(
        self,
        tool_result: ToolExecutionResult,
        context_data: Optional[Dict[str, Any]] = None
    ):
        """
        Log tool execution results.
        
        Args:
            tool_result: Tool execution result
            context_data: Additional context data
        """
        step_key = f"tool_execution_{tool_result.tool_type.value}"
        self.step_timings[step_key] = tool_result.processing_time_ms
        
        # Extract relevant metrics based on tool type
        result_metrics = {}
        if tool_result.result:
            if hasattr(tool_result.result, 'total_results'):
                result_metrics['results_count'] = tool_result.result.total_results
            if hasattr(tool_result.result, 'total_chunks'):
                result_metrics['chunks_count'] = tool_result.result.total_chunks
            if hasattr(tool_result.result, 'processing_time_ms'):
                result_metrics['tool_processing_time'] = tool_result.result.processing_time_ms
        
        data = {
            "tool_type": tool_result.tool_type.value,
            "success": tool_result.success,
            "processing_time_ms": tool_result.processing_time_ms,
            "error_message": tool_result.error_message,
            **result_metrics
        }
        
        if context_data:
            data.update(context_data)
        
        event = WorkflowEvent.COMPLETED if tool_result.success else WorkflowEvent.FAILED
        self._log_event(
            step=WorkflowStep.TOOL_EXECUTION,
            event=event,
            data=data
        )
    
    def log_llm_interaction(
        self,
        interaction: LLMInteraction,
        context: Optional[str] = None
    ):
        """
        Log LLM API interaction.
        
        Args:
            interaction: LLM interaction details
            context: Context about when/why the LLM was called
        """
        self.total_tokens += interaction.total_tokens
        self.total_cost += interaction.estimated_cost
        self.api_calls += 1
        
        self._log_event(
            step=WorkflowStep.TOOL_EXECUTION,  # Usually happens during tool execution
            event=WorkflowEvent.LLM_CALL,
            data={
                "model": interaction.model,
                "prompt_tokens": interaction.prompt_tokens,
                "completion_tokens": interaction.completion_tokens,
                "total_tokens": interaction.total_tokens,
                "estimated_cost": interaction.estimated_cost,
                "processing_time_ms": interaction.processing_time_ms,
                "temperature": interaction.temperature,
                "max_tokens": interaction.max_tokens,
                "context": context
            }
        )
    
    def log_response_generation(
        self,
        context_size: int,
        response_length: int,
        processing_time_ms: float,
        response_preview: Optional[str] = None
    ):
        """
        Log response generation step.
        
        Args:
            context_size: Size of context provided to LLM
            response_length: Length of generated response
            processing_time_ms: Time taken for generation
            response_preview: First 100 chars of response for debugging
        """
        step_key = "response_generation"
        self.step_timings[step_key] = processing_time_ms
        
        self._log_event(
            step=WorkflowStep.RESPONSE_GENERATION,
            event=WorkflowEvent.COMPLETED,
            data={
                "context_size": context_size,
                "response_length": response_length,
                "processing_time_ms": processing_time_ms,
                "response_preview": response_preview[:100] + "..." if response_preview and len(response_preview) > 100 else response_preview
            }
        )
    
    def log_output_sanitization(
        self,
        original_response: str,
        sanitized_response: str,
        was_modified: bool,
        processing_time_ms: float,
        warnings: Optional[List[str]] = None
    ):
        """
        Log output sanitization step.
        
        Args:
            original_response: Original LLM response
            sanitized_response: Sanitized response
            was_modified: Whether response was modified
            processing_time_ms: Time taken for sanitization
            warnings: Any warnings generated during sanitization
        """
        step_key = "output_sanitization"
        self.step_timings[step_key] = processing_time_ms
        
        self._log_event(
            step=WorkflowStep.OUTPUT_SANITIZATION,
            event=WorkflowEvent.COMPLETED,
            data={
                "was_modified": was_modified,
                "original_length": len(original_response),
                "sanitized_length": len(sanitized_response),
                "processing_time_ms": processing_time_ms,
                "warnings": warnings or [],
                "modification_ratio": abs(len(sanitized_response) - len(original_response)) / len(original_response) if original_response else 0
            }
        )
    
    def log_cache_event(self, cache_key: str, hit: bool, context: Optional[str] = None):
        """
        Log cache hit or miss event.
        
        Args:
            cache_key: The cache key accessed
            hit: Whether it was a hit (True) or miss (False)
            context: Context about what was cached
        """
        if hit:
            self.cache_hits += 1
            event = WorkflowEvent.CACHE_HIT
        else:
            self.cache_misses += 1
            event = WorkflowEvent.CACHE_MISS
        
        self._log_event(
            step=WorkflowStep.TOOL_EXECUTION,
            event=event,
            data={
                "cache_key": cache_key[:50] + "..." if len(cache_key) > 50 else cache_key,
                "context": context
            }
        )
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        recovery_action: Optional[str] = None,
        step: Optional[WorkflowStep] = None
    ):
        """
        Log error occurrence and recovery.
        
        Args:
            error_type: Type/class of error
            error_message: Error description
            stack_trace: Stack trace if available
            recovery_action: Action taken to recover
            step: Workflow step where error occurred
        """
        self._log_event(
            step=step or WorkflowStep.ERROR_HANDLING,
            event=WorkflowEvent.FAILED,
            data={
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace,
                "recovery_action": recovery_action
            },
            level=logging.ERROR
        )
    
    def log_workflow_start(
        self,
        user_id: str,
        query: str,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """
        Log workflow start.
        
        Args:
            user_id: User identifier
            query: User query
            session_id: Session identifier
            correlation_id: Workflow correlation ID
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())[:8]
            
        self.workflow_id = correlation_id
        self.user_id = user_id
        self.session_id = session_id
        self.workflow_start_time = time.time()
        
        self._log_event_simple(
            type="workflow_start",
            data={
                "user_id": user_id,
                "query": query[:200] + "..." if len(query) > 200 else query,
                "session_id": session_id,
                "correlation_id": correlation_id
            }
        )
    
    def log_workflow_step(self, step: str, message: str, correlation_id: Optional[str] = None):
        """
        Log a workflow step update.
        
        Args:
            step: Step name (sanitizing, thinking, determining, skimming, wording)
            message: Step description
            correlation_id: Workflow correlation ID
        """
        try:
            self._log_event_simple(
                type="workflow_step",
                data={
                    "step": step,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "correlation_id": correlation_id or self.workflow_id
                }
            )
            
            # Broadcast status update via WebSocket if correlation_id available
            if correlation_id or self.workflow_id:
                try:
                    from ..websocket_handler import get_workflow_broadcaster
                    from ..models import WorkflowStatus
                    
                    # Calculate progress based on step
                    progress_map = {
                        "sanitizing": 0.1,
                        "determining": 0.2,
                        "thinking": 0.5,
                        "skimming": 0.5,
                        "wording": 0.8
                    }
                    
                    status = WorkflowStatus(
                        step=step,
                        message=message,
                        progress=progress_map.get(step, 0.5),
                        timestamp=datetime.utcnow()
                    )
                    
                    broadcaster = get_workflow_broadcaster()
                    # Use asyncio to schedule the broadcast
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        loop.create_task(broadcaster.broadcast_status(correlation_id or self.workflow_id, status))
                    except RuntimeError:
                        # No event loop running, skip broadcast
                        pass
                        
                except Exception as broadcast_error:
                    self.logger.warning(f"Failed to broadcast workflow step: {broadcast_error}")
            
        except Exception as e:
            self.logger.error(f"Failed to log workflow step: {e}")
    
    def log_workflow_completion(
        self,
        user_id: str,
        success: bool,
        total_time_ms: float,
        correlation_id: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ):
        """
        Log workflow completion.
        
        Args:
            user_id: User identifier
            success: Whether workflow succeeded
            total_time_ms: Total processing time
            correlation_id: Workflow correlation ID
            context_data: Additional context data
        """
        self._log_event_simple(
            type="workflow_completion",
            data={
                "user_id": user_id,
                "success": success,
                "total_time_ms": total_time_ms,
                "correlation_id": correlation_id or self.workflow_id,
                **(context_data or {})
            }
        )
        
        # Broadcast completion via WebSocket
        if correlation_id or self.workflow_id:
            try:
                from ..websocket_handler import get_workflow_broadcaster
                
                broadcaster = get_workflow_broadcaster()
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    response = context_data.get("response", "") if context_data else ""
                    loop.create_task(broadcaster.broadcast_completion(
                        correlation_id or self.workflow_id, 
                        success, 
                        response
                    ))
                except RuntimeError:
                    # No event loop running, skip broadcast
                    pass
                    
            except Exception as broadcast_error:
                self.logger.warning(f"Failed to broadcast workflow completion: {broadcast_error}")

    def complete_workflow(self, success: bool, final_response: Optional[str] = None) -> WorkflowMetrics:
        """
        Complete the workflow and generate final metrics.
        
        Args:
            success: Whether workflow completed successfully
            final_response: Final response generated
            
        Returns:
            Comprehensive workflow metrics
        """
        if not self.workflow_start_time:
            raise ValueError("Workflow not properly initialized")
        
        total_time = (time.time() - self.workflow_start_time) * 1000
        cache_hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0.0
        
        metrics = WorkflowMetrics(
            total_processing_time_ms=total_time,
            step_timings=self.step_timings,
            total_tokens_used=self.total_tokens,
            total_estimated_cost=self.total_cost,
            api_calls_made=self.api_calls,
            cache_hit_rate=cache_hit_rate,
            success=success
        )
        
        self._log_event(
            step=WorkflowStep.WORKFLOW_COMPLETION,
            event=WorkflowEvent.COMPLETED if success else WorkflowEvent.FAILED,
            data={
                "success": success,
                "total_processing_time_ms": total_time,
                "total_tokens_used": self.total_tokens,
                "total_estimated_cost": self.total_cost,
                "api_calls_made": self.api_calls,
                "cache_hit_rate": cache_hit_rate,
                "final_response_length": len(final_response) if final_response else 0,
                "step_count": len(self.step_timings),
                "step_timings": self.step_timings
            }
        )
        
        return metrics
    
    def _log_event(
        self,
        step: WorkflowStep,
        event: WorkflowEvent,
        data: Dict[str, Any],
        level: int = logging.INFO
    ):
        """
        Internal method to log structured workflow events.
        
        Args:
            step: Workflow step
            event: Specific event
            data: Event data
            level: Log level
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "workflow_id": self.workflow_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "step": step.value,
            "event": event.value,
            "data": data
        }
        
        # Log as structured JSON
        self.logger.log(level, json.dumps(log_entry, default=str))
    
    def _log_event_simple(
        self,
        type: str,
        data: Dict[str, Any],
        level: int = logging.INFO
    ):
        """
        Simple event logging for workflow steps.
        
        Args:
            type: Event type
            data: Event data
            level: Log level
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": type,
            "data": data
        }
        
        # Log as structured JSON
        self.logger.log(level, json.dumps(log_entry, default=str))


# Global workflow logger instance for easy access
_global_workflow_logger: Optional[WorkflowLogger] = None


def get_workflow_logger() -> WorkflowLogger:
    """Get or create global workflow logger instance."""
    global _global_workflow_logger
    if _global_workflow_logger is None:
        _global_workflow_logger = WorkflowLogger()
    return _global_workflow_logger