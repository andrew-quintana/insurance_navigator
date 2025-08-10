"""Integration layer for handing off processed input to downstream workflows."""

import logging
from typing import Dict, Any

from .types import SanitizedOutput, UserContext, AgentPrompt, WorkflowHandoff, IntegrationError

logger = logging.getLogger(__name__)


class DefaultWorkflowHandoff(WorkflowHandoff):
    """Default implementation of workflow handoff to downstream agents."""
    
    def __init__(self, downstream_agent_config: Dict[str, Any] = None):
        """Initialize the workflow handoff.
        
        Args:
            downstream_agent_config: Configuration for downstream agents
        """
        self.downstream_config = downstream_agent_config or {}
        self.required_fields = [
            "prompt_text", "context", "metadata", "confidence", 
            "source_language", "processing_steps", "user_context"
        ]
        
        logger.info("Workflow handoff initialized")
    
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
        if not sanitized_output or not sanitized_output.structured_prompt:
            raise IntegrationError("Invalid sanitized output provided")
        
        if not user_context:
            raise IntegrationError("User context is required for downstream integration")
        
        logger.info("Formatting output for downstream workflow")
        
        # Create context for downstream agents
        downstream_context = {
            "user_id": user_context.user_id,
            "language_preference": user_context.language_preference,
            "domain": user_context.domain_context,
            "conversation_history": user_context.conversation_history[-5:],  # Last 5 messages
            "session_metadata": user_context.session_metadata,
            "original_text": sanitized_output.original_text,
            "sanitization_confidence": sanitized_output.confidence,
            "modifications_applied": sanitized_output.modifications
        }
        
        # Create metadata for the prompt
        prompt_metadata = {
            "processing_pipeline": "input_processing_workflow",
            "sanitization_metadata": sanitized_output.metadata,
            "input_processing_version": "1.0",
            "timestamp": user_context.session_metadata.get("timestamp"),
            "quality_scores": {
                "sanitization_confidence": sanitized_output.confidence
            }
        }
        
        # Create processing steps record
        processing_steps = [
            "input_capture",
            "translation",
            "sanitization",
            "downstream_formatting"
        ]
        
        # Add workflow metadata
        prompt = AgentPrompt(
            prompt_text=sanitized_output.structured_prompt,
            context=downstream_context,
            metadata=prompt_metadata,
            confidence=sanitized_output.confidence,
            source_language=user_context.language_preference,
            processing_steps=processing_steps,
            user_context=user_context
        )
        
        # Add workflow-specific metadata
        enhanced_prompt = self._add_workflow_metadata(prompt)
        
        # Validate compatibility
        if not self.validate_compatibility(enhanced_prompt):
            raise IntegrationError("Generated prompt is not compatible with downstream workflow")
        
        logger.info("Output successfully formatted for downstream workflow")
        return enhanced_prompt
    
    def validate_compatibility(self, prompt: AgentPrompt) -> bool:
        """Validate that prompt is compatible with downstream agents.
        
        Args:
            prompt: Agent prompt to validate
            
        Returns:
            True if compatible, False otherwise
        """
        try:
            # Check required fields
            for field in self.required_fields:
                if not hasattr(prompt, field):
                    logger.error(f"Missing required field: {field}")
                    return False
                
                value = getattr(prompt, field)
                if value is None:
                    logger.error(f"Required field {field} is None")
                    return False
            
            # Validate prompt text
            if not prompt.prompt_text or not prompt.prompt_text.strip():
                logger.error("Prompt text is empty")
                return False
            
            # Validate confidence score
            if not (0.0 <= prompt.confidence <= 1.0):
                logger.error(f"Invalid confidence score: {prompt.confidence}")
                return False
            
            # Validate context structure
            required_context_fields = ["user_id", "language_preference", "domain"]
            for field in required_context_fields:
                if field not in prompt.context:
                    logger.error(f"Missing required context field: {field}")
                    return False
            
            # Validate user context
            if not prompt.user_context or not prompt.user_context.user_id:
                logger.error("Invalid user context")
                return False
            
            logger.debug("Prompt compatibility validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error during compatibility validation: {e}")
            return False
    
    def get_downstream_requirements(self) -> Dict[str, Any]:
        """Get requirements for downstream agent compatibility."""
        return {
            "required_fields": self.required_fields,
            "prompt_format": "structured_text",
            "context_requirements": [
                "user_id", "language_preference", "domain", 
                "conversation_history", "session_metadata"
            ],
            "metadata_requirements": [
                "processing_pipeline", "sanitization_metadata", 
                "input_processing_version", "quality_scores"
            ],
            "confidence_range": [0.0, 1.0],
            "supported_languages": ["en", "es", "fr", "de", "it", "pt"],
            "max_prompt_length": 10000,
            "required_processing_steps": [
                "input_capture", "translation", "sanitization", "downstream_formatting"
            ]
        }
    
    def _add_workflow_metadata(self, prompt: AgentPrompt) -> AgentPrompt:
        """Add metadata required by existing workflow system.
        
        Args:
            prompt: Agent prompt to enhance
            
        Returns:
            Enhanced agent prompt
        """
        # Add workflow-specific metadata
        workflow_metadata = {
            "workflow_type": "patient_navigator",
            "input_source": "multilingual_input_processing",
            "requires_human_validation": prompt.confidence < 0.8,
            "priority": "normal",
            "routing_hints": {
                "use_translation_context": True,
                "preserve_cultural_context": True,
                "domain_specific_processing": True
            }
        }
        
        # Merge with existing metadata
        enhanced_metadata = {**prompt.metadata, **workflow_metadata}
        
        # Create new prompt with enhanced metadata
        enhanced_prompt = AgentPrompt(
            prompt_text=prompt.prompt_text,
            context=prompt.context,
            metadata=enhanced_metadata,
            confidence=prompt.confidence,
            source_language=prompt.source_language,
            processing_steps=prompt.processing_steps,
            user_context=prompt.user_context
        )
        
        return enhanced_prompt