"""
Input Processing Workflow Orchestrator.

This module provides a complete workflow that orchestrates:
1. Input capture (text/voice)
2. Translation (if needed)
3. Sanitization
4. Workflow handoff to downstream agents
"""

import logging
import time
from typing import Dict, Any, Optional

from .types import UserContext, SanitizedOutput, AgentPrompt
from .handler import DefaultInputHandler
from .sanitizer import SanitizationAgent
from .router import IntelligentTranslationRouter
from .integration import DefaultWorkflowHandoff

logger = logging.getLogger(__name__)


class InputProcessingWorkflow:
    """
    Complete input processing workflow orchestrator.
    
    This class coordinates all the components of the input processing pipeline:
    - Input capture (text/voice)
    - Translation (if needed)
    - Sanitization
    - Workflow handoff
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the input processing workflow."""
        self.config = config or {}
        
        # Initialize components
        self.input_handler = DefaultInputHandler()
        
        # For MVP, skip translation router initialization since we don't need real translation
        # TODO: Implement proper translation when needed
        self.translation_router = None
        
        self.sanitization_agent = SanitizationAgent()
        self.workflow_handoff = DefaultWorkflowHandoff()
        
        logger.info("Input Processing Workflow initialized")
    
    async def process_input(self, text: str, user_context: UserContext) -> AgentPrompt:
        """
        Process user input through the complete workflow.
        
        Args:
            text: User input text
            user_context: User context information
            
        Returns:
            AgentPrompt ready for downstream agents
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing input for user {user_context.user_id}")
            
            # Step 1: Validate input quality
            quality_score = self.input_handler.validate_input_quality(text)
            logger.info(f"Input quality score: {quality_score.score}")
            
            # Step 2: Translate if needed (for MVP, assume English input)
            # TODO: Implement language detection and translation when translation_router is available
            if self.translation_router:
                # Use translation router when available
                translated_text = await self.translation_router.translate(text, "en", "en")
            else:
                # For MVP, no translation needed
                translated_text = text
            
            # Step 3: Sanitize input
            sanitized_output = await self.sanitization_agent.sanitize(
                translated_text, user_context
            )
            logger.info(f"Input sanitized with confidence: {sanitized_output.confidence}")
            
            # Step 4: Format for downstream workflow
            agent_prompt = await self.workflow_handoff.format_for_downstream(
                sanitized_output, user_context
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Input processing completed in {processing_time:.2f}s")
            
            return agent_prompt
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Input processing failed after {processing_time:.2f}s: {e}")
            raise
    
    async def process_voice_input(self, audio_data: bytes, user_context: UserContext) -> AgentPrompt:
        """
        Process voice input through the complete workflow.
        
        Args:
            audio_data: Raw audio bytes
            user_context: User context information
            
        Returns:
            AgentPrompt ready for downstream agents
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing voice input for user {user_context.user_id}")
            
            # Step 1: Validate audio quality
            quality_score = self.input_handler.validate_input_quality(audio_data)
            logger.info(f"Audio quality score: {quality_score.score}")
            
            # Step 2: Convert speech to text (for MVP, return placeholder)
            # TODO: Implement speech-to-text conversion
            transcribed_text = "Voice input received - speech-to-text not implemented in MVP"
            
            # Step 3: Process as text input
            return await self.process_input(transcribed_text, user_context)
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Voice input processing failed after {processing_time:.2f}s: {e}")
            raise


# Convenience function for easy integration
async def create_input_processing_workflow(config: Dict[str, Any] = None) -> InputProcessingWorkflow:
    """Create and return a configured input processing workflow."""
    return InputProcessingWorkflow(config)
