"""
Configuration management for the Output Processing Workflow.

This module handles loading and managing configuration for the output processing
components, following the existing project configuration patterns.
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.development')

logger = logging.getLogger(__name__)


@dataclass
class OutputProcessingConfig:
    """Configuration for the output processing workflow."""
    
    # LLM configuration
    llm_model: str = "claude-3-haiku"
    
    # Performance settings
    request_timeout: float = 30.0
    max_input_length: int = 10000
    max_concurrent_requests: int = 10
    
    # Communication settings
    default_tone: str = "warm_empathetic"
    enable_tone_adaptation: bool = True
    min_empathy_score: float = 0.7
    
    # Content processing
    max_agent_outputs: int = 10
    enable_content_consolidation: bool = True
    enable_plain_language: bool = True
    
    # Quality thresholds
    min_response_quality: float = 0.8
    max_processing_time: float = 5.0  # seconds
    
    # Error handling
    enable_fallback: bool = True
    fallback_to_original: bool = True
    max_retry_attempts: int = 2
    
    @classmethod
    def from_environment(cls) -> "OutputProcessingConfig":
        """Create configuration from environment variables."""
        return cls(
            llm_model=os.getenv("OUTPUT_PROCESSING_LLM_MODEL", "claude-3-haiku"),
            request_timeout=float(os.getenv("OUTPUT_PROCESSING_TIMEOUT", "30.0")),
            max_input_length=int(os.getenv("OUTPUT_PROCESSING_MAX_INPUT_LENGTH", "10000")),
            max_concurrent_requests=int(os.getenv("OUTPUT_PROCESSING_MAX_CONCURRENT", "10")),
            default_tone=os.getenv("OUTPUT_PROCESSING_DEFAULT_TONE", "warm_empathetic"),
            enable_tone_adaptation=os.getenv("OUTPUT_PROCESSING_ENABLE_TONE_ADAPTATION", "true").lower() == "true",
            min_empathy_score=float(os.getenv("OUTPUT_PROCESSING_MIN_EMPATHY_SCORE", "0.7")),
            max_agent_outputs=int(os.getenv("OUTPUT_PROCESSING_MAX_AGENT_OUTPUTS", "10")),
            enable_content_consolidation=os.getenv("OUTPUT_PROCESSING_ENABLE_CONSOLIDATION", "true").lower() == "true",
            enable_plain_language=os.getenv("OUTPUT_PROCESSING_ENABLE_PLAIN_LANGUAGE", "true").lower() == "true",
            min_response_quality=float(os.getenv("OUTPUT_PROCESSING_MIN_QUALITY", "0.8")),
            max_processing_time=float(os.getenv("OUTPUT_PROCESSING_MAX_TIME", "5.0")),
            enable_fallback=os.getenv("OUTPUT_PROCESSING_ENABLE_FALLBACK", "true").lower() == "true",
            fallback_to_original=os.getenv("OUTPUT_PROCESSING_FALLBACK_TO_ORIGINAL", "true").lower() == "true",
            max_retry_attempts=int(os.getenv("OUTPUT_PROCESSING_MAX_RETRIES", "2"))
        )
    
    def validate(self) -> None:
        """Validate the configuration."""
        errors = []
        
        # Check timeout values
        if self.request_timeout <= 0:
            errors.append("request_timeout must be positive")
        
        if self.max_processing_time <= 0:
            errors.append("max_processing_time must be positive")
        
        # Check quality thresholds
        if not 0 <= self.min_empathy_score <= 1:
            errors.append("min_empathy_score must be between 0 and 1")
        
        if not 0 <= self.min_response_quality <= 1:
            errors.append("min_response_quality must be between 0 and 1")
        
        # Check input limits
        if self.max_input_length <= 0:
            errors.append("max_input_length must be positive")
        
        if self.max_agent_outputs <= 0:
            errors.append("max_agent_outputs must be positive")
        
        # Check retry settings
        if self.max_retry_attempts < 0:
            errors.append("max_retry_attempts must be non-negative")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for logging/debugging."""
        return {
            "llm_model": self.llm_model,
            "request_timeout": self.request_timeout,
            "max_input_length": self.max_input_length,
            "max_concurrent_requests": self.max_concurrent_requests,
            "default_tone": self.default_tone,
            "enable_tone_adaptation": self.enable_tone_adaptation,
            "min_empathy_score": self.min_empathy_score,
            "max_agent_outputs": self.max_agent_outputs,
            "enable_content_consolidation": self.enable_content_consolidation,
            "enable_plain_language": self.enable_plain_language,
            "min_response_quality": self.min_response_quality,
            "max_processing_time": self.max_processing_time,
            "enable_fallback": self.enable_fallback,
            "fallback_to_original": self.fallback_to_original,
            "max_retry_attempts": self.max_retry_attempts
        }
