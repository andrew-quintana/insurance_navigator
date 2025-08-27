"""Type definitions for the Input Processing Workflow.

This module defines all protocols, data classes, and interfaces used throughout
the input processing pipeline components.
"""

from typing import Protocol, Union, Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum
import asyncio


@dataclass
class QualityScore:
    """Represents the quality assessment of input data."""
    score: float  # 0.0 to 1.0 quality score
    confidence: float  # 0.0 to 1.0 confidence in the score
    issues: List[str]  # List of detected quality issues


@dataclass
class TranslationResult:
    """Result from a translation operation."""
    text: str  # Translated text
    confidence: float  # 0.0 to 1.0 translation confidence
    provider: str  # Name of the translation provider used
    cost_estimate: float  # Estimated cost of the translation
    source_language: str  # Detected or configured source language
    target_language: str  # Target language (typically 'en')


@dataclass
class UserContext:
    """Context information about the user and conversation."""
    user_id: str  # Unique user identifier
    conversation_history: List[str]  # Previous conversation messages
    language_preference: str  # User's preferred language (ISO code)
    domain_context: str = "insurance"  # Domain context for disambiguation
    session_metadata: Dict[str, Any] = None  # Additional session data
    
    def __post_init__(self):
        if self.session_metadata is None:
            self.session_metadata = {}


@dataclass
class SanitizedOutput:
    """Output from the sanitization process."""
    cleaned_text: str  # Cleaned and structured text
    structured_prompt: str  # Formatted prompt for downstream agents
    confidence: float  # 0.0 to 1.0 confidence in sanitization quality
    modifications: List[str]  # List of modifications made during sanitization
    metadata: Dict[str, Any]  # Additional metadata about the sanitization process
    original_text: str = ""  # Original input text for reference
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentPrompt:
    """Structured prompt for downstream agent processing."""
    prompt_text: str  # The main prompt text
    context: Dict[str, Any]  # Context information for the agent
    metadata: Dict[str, Any]  # Metadata about the prompt processing
    confidence: float  # Overall confidence in the prompt quality
    source_language: str  # Original language of the input
    processing_steps: List[str]  # Steps taken during processing
    user_context: UserContext  # User context information
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.metadata is None:
            self.metadata = {}


class InputType(Enum):
    """Types of input supported by the system."""
    VOICE = "voice"
    TEXT = "text"


class TranslationProviderType(Enum):
    """Available translation provider types."""
    ELEVENLABS = "elevenlabs"
    FLASH = "flash"
    FALLBACK = "fallback"


class ProcessingStatus(Enum):
    """Status of processing operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class InputHandler(Protocol):
    """Protocol for input capture and validation."""
    
    async def capture_voice_input(self, timeout: float = 30.0) -> bytes:
        """Capture audio from microphone and return raw audio bytes.
        
        Args:
            timeout: Maximum time to wait for input in seconds
            
        Returns:
            Raw audio bytes
            
        Raises:
            TimeoutError: If no input received within timeout
            RuntimeError: If microphone access fails
        """
        ...
    
    async def capture_text_input(self, prompt: str = "Enter your message: ") -> str:
        """Capture text input from CLI.
        
        Args:
            prompt: Prompt to display to user
            
        Returns:
            User input text
            
        Raises:
            KeyboardInterrupt: If user cancels input
        """
        ...
        
    def validate_input_quality(self, input_data: Union[bytes, str]) -> QualityScore:
        """Validate quality of input data.
        
        Args:
            input_data: Raw input data (audio bytes or text string)
            
        Returns:
            QualityScore with assessment and issues
        """
        ...
    
    def get_supported_input_types(self) -> List[InputType]:
        """Get list of supported input types."""
        ...


class TranslationProvider(Protocol):
    """Protocol for translation service providers."""
    
    async def translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str = "en"
    ) -> TranslationResult:
        """Translate text from source to target language.
        
        Args:
            text: Text to translate
            source_lang: Source language ISO code
            target_lang: Target language ISO code (default: 'en')
            
        Returns:
            TranslationResult with translated text and metadata
            
        Raises:
            ValueError: If language not supported
            RuntimeError: If translation service fails
        """
        ...
    
    def get_cost_estimate(self, text: str, source_lang: str, target_lang: str = "en") -> float:
        """Estimate cost for translation.
        
        Args:
            text: Text to translate
            source_lang: Source language ISO code
            target_lang: Target language ISO code
            
        Returns:
            Estimated cost in USD
        """
        ...
        
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        ...
    
    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        ...
    
    async def health_check(self) -> bool:
        """Check if the provider service is available."""
        ...


class SanitizationAgent(Protocol):
    """Protocol for input sanitization and structuring."""
    
    async def sanitize(self, input_text: str, context: UserContext) -> SanitizedOutput:
        """Clean and structure translated text for downstream agents.
        
        Args:
            input_text: Text to sanitize (typically translated)
            context: User context for disambiguation
            
        Returns:
            SanitizedOutput with cleaned text and metadata
        """
        ...
    
    def get_domain_keywords(self) -> Dict[str, List[str]]:
        """Get domain-specific keywords for disambiguation."""
        ...


class WorkflowHandoff(Protocol):
    """Protocol for handing off processed input to downstream workflows."""
    
    async def format_for_downstream(
        self, 
        sanitized_output: SanitizedOutput, 
        user_context: UserContext
    ) -> AgentPrompt:
        """Format sanitized output for existing patient navigator workflow.
        
        Args:
            sanitized_output: Sanitized input text
            user_context: User context information
            
        Returns:
            AgentPrompt formatted for downstream agents
        """
        ...
        
    def validate_compatibility(self, prompt: AgentPrompt) -> bool:
        """Validate that prompt is compatible with downstream agents.
        
        Args:
            prompt: Agent prompt to validate
            
        Returns:
            True if compatible, False otherwise
        """
        ...
    
    def get_downstream_requirements(self) -> Dict[str, Any]:
        """Get requirements for downstream agent compatibility."""
        ...


@dataclass
class ProcessingError:
    """Error information for processing failures."""
    stage: str  # Which processing stage failed
    error_type: str  # Type of error (timeout, api_failure, etc.)
    message: str  # Human-readable error message
    details: Dict[str, Any]  # Additional error details
    timestamp: float  # Unix timestamp of error
    recoverable: bool  # Whether error can be retried
    suggested_action: str  # Suggested action for recovery


@dataclass
class ProcessingMetrics:
    """Metrics for monitoring processing performance."""
    total_processing_time: float  # Total time in seconds
    input_capture_time: float  # Time to capture input
    translation_time: float  # Time for translation
    sanitization_time: float  # Time for sanitization
    integration_time: float  # Time for downstream integration
    api_calls_made: int  # Number of external API calls
    total_cost: float  # Total estimated cost
    cache_hits: int  # Number of cache hits
    cache_misses: int  # Number of cache misses


@dataclass
class CacheEntry:
    """Entry in the translation cache."""
    key: str  # Cache key (hash of text + languages)
    translation_result: TranslationResult  # Cached translation result
    timestamp: float  # Unix timestamp when cached
    access_count: int  # Number of times accessed
    ttl: float  # Time to live in seconds


# Error types for specific failure modes
class InputProcessingError(Exception):
    """Base exception for input processing errors."""
    pass


class InputCaptureError(InputProcessingError):
    """Error during input capture phase."""
    pass


class TranslationError(InputProcessingError):
    """Error during translation phase."""
    pass


class SanitizationError(InputProcessingError):
    """Error during sanitization phase."""
    pass


class IntegrationError(InputProcessingError):
    """Error during downstream integration phase."""
    pass


class ConfigurationError(InputProcessingError):
    """Error in system configuration."""
    pass