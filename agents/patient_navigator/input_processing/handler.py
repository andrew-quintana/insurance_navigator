"""Input Handler implementation for voice and text input capture."""

import asyncio
import logging
from typing import Union, List
import sys

from .types import InputHandler, QualityScore, InputType, InputCaptureError
from .config import get_input_config

logger = logging.getLogger(__name__)


class DefaultInputHandler(InputHandler):
    """Default implementation of the InputHandler protocol."""
    
    def __init__(self):
        """Initialize the input handler."""
        self.config = get_input_config()
        logger.info("Input handler initialized")
    
    async def capture_voice_input(self, timeout: float = 30.0) -> bytes:
        """Capture audio from microphone and return raw audio bytes.
        
        Note: This is a stub implementation for Phase 1.
        Full audio capture will be implemented in Phase 2.
        
        Args:
            timeout: Maximum time to wait for input in seconds
            
        Returns:
            Raw audio bytes
            
        Raises:
            TimeoutError: If no input received within timeout
            RuntimeError: If microphone access fails
        """
        logger.warning("Voice input capture not yet implemented - returning placeholder")
        
        # Placeholder: Return empty audio data for now
        # In Phase 2, this will use PyAudio to capture from microphone
        await asyncio.sleep(0.1)  # Simulate brief processing
        
        # For now, return empty bytes to indicate no audio captured
        return b""
    
    async def capture_text_input(self, prompt: str = "Enter your message: ") -> str:
        """Capture text input from CLI.
        
        Args:
            prompt: Prompt to display to user
            
        Returns:
            User input text
            
        Raises:
            KeyboardInterrupt: If user cancels input
        """
        try:
            logger.debug(f"Capturing text input with prompt: {prompt}")
            
            # Use asyncio to make this non-blocking
            loop = asyncio.get_event_loop()
            user_input = await loop.run_in_executor(None, input, prompt)
            
            # Validate input length
            max_length = self.config["max_text_length"]
            if len(user_input) > max_length:
                logger.warning(f"Input truncated from {len(user_input)} to {max_length} characters")
                user_input = user_input[:max_length]
            
            logger.info(f"Captured text input: {len(user_input)} characters")
            return user_input.strip()
            
        except KeyboardInterrupt:
            logger.info("Text input cancelled by user")
            raise
        except Exception as e:
            logger.error(f"Error capturing text input: {e}")
            raise InputCaptureError(f"Failed to capture text input: {e}")
    
    def validate_input_quality(self, input_data: Union[bytes, str]) -> QualityScore:
        """Validate quality of input data.
        
        Args:
            input_data: Raw input data (audio bytes or text string)
            
        Returns:
            QualityScore with assessment and issues
        """
        issues = []
        
        if isinstance(input_data, bytes):
            # Audio quality validation
            if len(input_data) == 0:
                issues.append("No audio data captured")
                return QualityScore(score=0.0, confidence=1.0, issues=issues)
            
            # Placeholder audio quality checks
            # In Phase 2, implement proper audio analysis
            score = 0.8  # Assume good quality for now
            confidence = 0.9
            
        else:  # text input
            # Text quality validation
            text = input_data.strip()
            
            if len(text) == 0:
                issues.append("Empty text input")
                return QualityScore(score=0.0, confidence=1.0, issues=issues)
            
            if len(text) < 3:
                issues.append("Text input too short")
            
            if len(text) > self.config["max_text_length"]:
                issues.append(f"Text input exceeds maximum length ({self.config['max_text_length']} characters)")
            
            # Check for suspicious patterns
            if text.count(' ') == 0 and len(text) > 10:
                issues.append("No spaces detected - possible input error")
            
            # Calculate quality score based on issues
            score = max(0.1, 1.0 - (len(issues) * 0.2))
            confidence = 0.8 if issues else 0.95
        
        logger.debug(f"Input quality validation: score={score}, confidence={confidence}, issues={issues}")
        return QualityScore(score=score, confidence=confidence, issues=issues)
    
    def get_supported_input_types(self) -> List[InputType]:
        """Get list of supported input types."""
        # For Phase 1, support both text and voice (voice is placeholder)
        return [InputType.TEXT, InputType.VOICE]