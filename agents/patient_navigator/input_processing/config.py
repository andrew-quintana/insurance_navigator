"""Configuration management for the Input Processing Workflow.

This module handles loading and managing configuration for all input processing
components, integrating with the existing project configuration system.
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class InputProcessingConfig:
    """Configuration for the input processing workflow."""
    
    # Translation service API keys
    elevenlabs_api_key: Optional[str] = None
    flash_api_key: Optional[str] = None
    
    # Language configuration
    default_language: str = "es"
    target_language: str = "en"
    
    # Input processing settings
    voice_timeout: float = 30.0
    max_text_length: int = 5000
    
    # Cache configuration
    cache_size: int = 1000
    cache_ttl: int = 3600  # seconds
    
    # Performance settings
    max_concurrent_requests: int = 10
    request_timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # Quality thresholds
    min_audio_quality_score: float = 0.3
    min_translation_confidence: float = 0.5
    min_sanitization_confidence: float = 0.6
    
    # Provider preferences
    preferred_provider: str = "elevenlabs"  # or "flash"
    enable_fallback: bool = True
    
    # Domain-specific settings
    domain_context: str = "insurance"
    enable_context_validation: bool = True
    
    @classmethod
    def from_environment(cls) -> "InputProcessingConfig":
        """Create configuration from environment variables."""
        return cls(
            elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY"),
            flash_api_key=os.getenv("FLASH_API_KEY"),
            default_language=os.getenv("INPUT_PROCESSING_DEFAULT_LANGUAGE", "es"),
            target_language=os.getenv("INPUT_PROCESSING_TARGET_LANGUAGE", "en"),
            voice_timeout=float(os.getenv("INPUT_PROCESSING_VOICE_TIMEOUT", "30.0")),
            max_text_length=int(os.getenv("INPUT_PROCESSING_MAX_TEXT_LENGTH", "5000")),
            cache_size=int(os.getenv("INPUT_PROCESSING_CACHE_SIZE", "1000")),
            cache_ttl=int(os.getenv("INPUT_PROCESSING_CACHE_TTL", "3600")),
            max_concurrent_requests=int(os.getenv("INPUT_PROCESSING_MAX_CONCURRENT", "10")),
            request_timeout=float(os.getenv("INPUT_PROCESSING_REQUEST_TIMEOUT", "30.0")),
            retry_attempts=int(os.getenv("INPUT_PROCESSING_RETRY_ATTEMPTS", "3")),
            retry_delay=float(os.getenv("INPUT_PROCESSING_RETRY_DELAY", "1.0")),
            min_audio_quality_score=float(os.getenv("INPUT_PROCESSING_MIN_AUDIO_QUALITY", "0.3")),
            min_translation_confidence=float(os.getenv("INPUT_PROCESSING_MIN_TRANSLATION_CONFIDENCE", "0.5")),
            min_sanitization_confidence=float(os.getenv("INPUT_PROCESSING_MIN_SANITIZATION_CONFIDENCE", "0.6")),
            preferred_provider=os.getenv("INPUT_PROCESSING_PREFERRED_PROVIDER", "elevenlabs"),
            enable_fallback=os.getenv("INPUT_PROCESSING_ENABLE_FALLBACK", "true").lower() == "true",
            domain_context=os.getenv("INPUT_PROCESSING_DOMAIN_CONTEXT", "insurance"),
            enable_context_validation=os.getenv("INPUT_PROCESSING_ENABLE_CONTEXT_VALIDATION", "true").lower() == "true"
        )
    
    def validate(self) -> None:
        """Validate the configuration."""
        errors = []
        
        # Check required API keys
        if not self.elevenlabs_api_key and not self.flash_api_key:
            errors.append("At least one translation service API key is required (ELEVENLABS_API_KEY or FLASH_API_KEY)")
        
        # Check timeout values
        if self.voice_timeout <= 0:
            errors.append("voice_timeout must be positive")
        
        if self.request_timeout <= 0:
            errors.append("request_timeout must be positive")
        
        # Check cache settings
        if self.cache_size <= 0:
            errors.append("cache_size must be positive")
        
        if self.cache_ttl <= 0:
            errors.append("cache_ttl must be positive")
        
        # Check quality thresholds
        if not (0.0 <= self.min_audio_quality_score <= 1.0):
            errors.append("min_audio_quality_score must be between 0.0 and 1.0")
        
        if not (0.0 <= self.min_translation_confidence <= 1.0):
            errors.append("min_translation_confidence must be between 0.0 and 1.0")
        
        if not (0.0 <= self.min_sanitization_confidence <= 1.0):
            errors.append("min_sanitization_confidence must be between 0.0 and 1.0")
        
        # Check provider preference
        if self.preferred_provider not in ["elevenlabs", "flash"]:
            errors.append("preferred_provider must be 'elevenlabs' or 'flash'")
        
        if errors:
            raise ValueError("Configuration validation errors:\n" + "\n".join(f"  - {error}" for error in errors))
        
        logger.info("Input processing configuration validated successfully")
    
    def get_active_providers(self) -> Dict[str, Optional[str]]:
        """Get the active translation providers and their API keys."""
        providers = {}
        
        if self.elevenlabs_api_key:
            providers["elevenlabs"] = self.elevenlabs_api_key
        
        if self.flash_api_key:
            providers["flash"] = self.flash_api_key
        
        return providers
    
    def get_provider_priority(self) -> list[str]:
        """Get the provider priority order based on configuration."""
        providers = list(self.get_active_providers().keys())
        
        # Put preferred provider first
        if self.preferred_provider in providers:
            providers.remove(self.preferred_provider)
            providers.insert(0, self.preferred_provider)
        
        # Always add mock provider as last fallback if not already present
        if "mock" not in providers:
            providers.append("mock")
        
        return providers


# Global configuration instance
_config: Optional[InputProcessingConfig] = None


def get_config() -> InputProcessingConfig:
    """Get the global input processing configuration instance."""
    global _config
    if _config is None:
        _config = InputProcessingConfig.from_environment()
        try:
            _config.validate()
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise
    return _config


def reload_config() -> InputProcessingConfig:
    """Reload the configuration from environment variables."""
    global _config
    _config = None
    return get_config()


def get_translation_config() -> Dict[str, Any]:
    """Get translation-specific configuration."""
    config = get_config()
    return {
        "default_language": config.default_language,
        "target_language": config.target_language,
        "providers": config.get_active_providers(),
        "provider_priority": config.get_provider_priority(),
        "timeout": config.request_timeout,
        "retry_attempts": config.retry_attempts,
        "retry_delay": config.retry_delay,
        "min_confidence": config.min_translation_confidence,
        "enable_fallback": config.enable_fallback
    }


def get_cache_config() -> Dict[str, Any]:
    """Get caching-specific configuration."""
    config = get_config()
    return {
        "size": config.cache_size,
        "ttl": config.cache_ttl
    }


def get_quality_config() -> Dict[str, Any]:
    """Get quality assessment configuration."""
    config = get_config()
    return {
        "min_audio_quality": config.min_audio_quality_score,
        "min_translation_confidence": config.min_translation_confidence,
        "min_sanitization_confidence": config.min_sanitization_confidence
    }


def get_input_config() -> Dict[str, Any]:
    """Get input processing configuration."""
    config = get_config()
    return {
        "voice_timeout": config.voice_timeout,
        "max_text_length": config.max_text_length,
        "domain_context": config.domain_context,
        "enable_context_validation": config.enable_context_validation
    }