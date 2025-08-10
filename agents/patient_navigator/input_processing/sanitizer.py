"""Sanitization Agent implementation for LLM-based text processing and structuring."""

import logging
import re
import asyncio
from typing import Dict, List

from .types import SanitizedOutput, UserContext, SanitizationError
from .config import get_quality_config, get_input_config

logger = logging.getLogger(__name__)


class SanitizationAgent:
    """Agent for LLM-based sanitization and structuring of translated input."""
    
    def __init__(self):
        """Initialize the sanitization agent."""
        self.quality_config = get_quality_config()
        self.input_config = get_input_config()
        
        # LLM-based processing - no deterministic mappings
        self.sanitization_prompt_template = self._get_sanitization_prompt_template()
        
        logger.info("LLM-based sanitization agent initialized")
    
    async def sanitize(self, input_text: str, context: UserContext) -> SanitizedOutput:
        """Clean and structure translated text using LLM-based processing.
        
        Args:
            input_text: Text to sanitize (typically translated)
            context: User context for disambiguation
            
        Returns:
            SanitizedOutput with cleaned text and metadata
        """
        if not input_text or not input_text.strip():
            raise SanitizationError("Empty input text provided for sanitization")
        
        logger.info(f"Starting LLM-based sanitization of {len(input_text)} characters")
        
        original_text = input_text
        modifications = []
        
        # Step 1: Basic cleanup (non-LLM preprocessing)
        cleaned_text = self._basic_cleanup(input_text)
        if cleaned_text != input_text:
            modifications.append("Basic cleanup applied")
        
        # Step 2: LLM-based sanitization and structuring
        try:
            llm_result = await self._llm_sanitize(cleaned_text, context)
            structured_prompt = llm_result["structured_prompt"]
            llm_modifications = llm_result["modifications"]
            llm_confidence = llm_result["confidence"]
            
            modifications.extend(llm_modifications)
            
            # Prepare metadata
            metadata = {
                "domain_context": self.input_config["domain_context"],
                "processing_method": "llm_based",
                "text_length_before": len(original_text),
                "text_length_after": len(structured_prompt),
                "llm_processing_time": llm_result.get("processing_time", 0),
                "context_validation_enabled": self.input_config["enable_context_validation"]
            }
            
            result = SanitizedOutput(
                cleaned_text=cleaned_text,
                structured_prompt=structured_prompt,
                confidence=llm_confidence,
                modifications=modifications,
                metadata=metadata,
                original_text=original_text
            )
            
            logger.info(f"LLM-based sanitization completed with confidence {llm_confidence}")
            return result
            
        except Exception as e:
            logger.error(f"LLM sanitization failed: {e}")
            
            # Fallback to basic formatting if LLM fails
            fallback_prompt = self._fallback_structure(cleaned_text)
            modifications.append("Fallback formatting applied (LLM unavailable)")
            
            metadata = {
                "domain_context": self.input_config["domain_context"],
                "processing_method": "fallback",
                "text_length_before": len(original_text),
                "text_length_after": len(fallback_prompt),
                "fallback_reason": str(e)
            }
            
            result = SanitizedOutput(
                cleaned_text=cleaned_text,
                structured_prompt=fallback_prompt,
                confidence=0.6,  # Lower confidence for fallback
                modifications=modifications,
                metadata=metadata,
                original_text=original_text
            )
            
            logger.warning(f"Using fallback sanitization due to LLM failure")
            return result
    
    def _basic_cleanup(self, text: str) -> str:
        """Perform minimal non-LLM text cleanup (only technical artifacts).
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text with translation artifacts removed
        """
        # Remove translation artifacts from mock/test providers only
        cleaned = re.sub(r'\[TRANSLATED from \w+\]\s*', '', text.strip())
        cleaned = re.sub(r'\[MOCK-TRANSLATED from \w+\]\s*', '', cleaned)
        cleaned = re.sub(r'\[FLASH-TRANSLATED from \w+\]\s*', '', cleaned)
        
        # Only normalize excessive whitespace (technical cleanup)
        cleaned = re.sub(r'\s+', ' ', cleaned.strip())
        
        return cleaned
    
    async def _llm_sanitize(self, text: str, context: UserContext) -> Dict:
        """Use LLM to sanitize and structure the input text.
        
        Args:
            text: Text to sanitize
            context: User context for personalization
            
        Returns:
            Dictionary containing structured_prompt, modifications, and confidence
        """
        import time
        start_time = time.time()
        
        # For Phase 2, simulate LLM processing with a structured approach
        # In production, this would call the actual LLM API
        await asyncio.sleep(0.1)  # Simulate API call delay
        
        # Create the sanitization prompt for the LLM
        llm_prompt = self.sanitization_prompt_template.format(
            input_text=text,
            domain_context=context.domain_context,
            user_language=context.language_preference,
            conversation_history=self._format_conversation_history(context.conversation_history)
        )
        
        # Simulate LLM response (in production, replace with actual LLM API call)
        structured_prompt = await self._simulate_llm_response(text, context)
        
        processing_time = time.time() - start_time
        
        return {
            "structured_prompt": structured_prompt,
            "modifications": ["LLM-based sanitization and structuring applied"],
            "confidence": 0.85,  # High confidence for LLM processing
            "processing_time": processing_time,
            "llm_prompt_used": llm_prompt[:100] + "..." if len(llm_prompt) > 100 else llm_prompt
        }
    
    async def _simulate_llm_response(self, text: str, context: UserContext) -> str:
        """Simulate LLM response for Phase 2 (replace with real LLM in production).
        
        Args:
            text: Input text
            context: User context
            
        Returns:
            Structured prompt text
        """
        # This simulates what an LLM would do - clean formatting and structure
        # without deterministic rule-based transformations
        
        # Simple reformatting that mimics LLM output
        if text.strip():
            # Ensure proper capitalization and punctuation
            formatted_text = text.strip()
            if formatted_text and not formatted_text.endswith(('.', '!', '?')):
                formatted_text += '.'
            
            if formatted_text:
                formatted_text = formatted_text[0].upper() + formatted_text[1:]
            
            # Structure as a user request for downstream agents
            structured = f"The user is requesting assistance with: {formatted_text}"
            return structured
        
        return text
    
    def _get_sanitization_prompt_template(self) -> str:
        """Get the prompt template for LLM-based sanitization.
        
        Returns:
            Prompt template string
        """
        return """
Please sanitize and structure the following user input for an insurance customer service system.

Input text: "{input_text}"
Domain context: {domain_context}
User's preferred language: {user_language}
Conversation history: {conversation_history}

Please:
1. Clean up any formatting issues or translation artifacts
2. Structure the text as a clear, professional request
3. Preserve the original meaning and intent completely
4. Do not add domain-specific assumptions or expand abbreviations
5. Format as: "The user is requesting assistance with: [cleaned text]"

Respond with only the cleaned and structured text.
        """.strip()
    
    def _format_conversation_history(self, history: List[str]) -> str:
        """Format conversation history for LLM context.
        
        Args:
            history: List of previous messages
            
        Returns:
            Formatted history string
        """
        if not history:
            return "None"
        
        recent_history = history[-3:]  # Last 3 messages for context
        return " | ".join(recent_history)
    
    def _fallback_structure(self, text: str) -> str:
        """Simple fallback formatting when LLM is unavailable.
        
        Args:
            text: Input text
            
        Returns:
            Simply formatted text
        """
        if not text.strip():
            return text
        
        # Minimal formatting - just ensure proper punctuation and structure
        formatted = text.strip()
        if formatted and not formatted.endswith(('.', '!', '?')):
            formatted += '.'
        
        if formatted:
            formatted = formatted[0].upper() + formatted[1:]
        
        # Simple structure without domain assumptions
        return f"The user is requesting assistance with: {formatted}"