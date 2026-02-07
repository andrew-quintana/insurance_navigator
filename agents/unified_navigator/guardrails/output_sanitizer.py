"""
Output Sanitization Guardrail.

This module provides response sanitization to ensure outputs remain
within the insurance domain and are free from inappropriate content.
Optimized for streaming compatibility and low latency.
"""

import asyncio
import logging
import re
import time
from typing import Dict, List, Optional, Set
import httpx
import os

from ..models import OutputSanitationResult, UnifiedNavigatorState


class OutputSanitizer:
    """
    Output sanitization system optimized for low latency and streaming.
    
    Uses template-based sanitization for common patterns and minimal LLM
    usage for edge cases only.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("unified_navigator.output_sanitizer")
        
        # Insurance domain terms that should be preserved
        self.insurance_terms: Set[str] = {
            "insurance", "coverage", "premium", "deductible", "claim", "policy",
            "copay", "coinsurance", "network", "provider", "benefit", "medicare",
            "medicaid", "hsa", "fsa", "preauthorization", "formulary", "enrollment",
            "healthcare", "medical", "prescription", "pharmacy", "doctor", "hospital"
        }
        
        # Patterns that indicate off-topic responses
        self.off_topic_patterns: List[re.Pattern] = [
            re.compile(r'\b(?:recipe|cooking|food|restaurant)\b', re.IGNORECASE),
            re.compile(r'\b(?:weather|climate|temperature)\b', re.IGNORECASE),
            re.compile(r'\b(?:sports|game|team|player)\b', re.IGNORECASE),
            re.compile(r'\b(?:music|song|artist|album)\b', re.IGNORECASE),
            re.compile(r'\b(?:movie|film|actor|director)\b', re.IGNORECASE),
            re.compile(r'\b(?:politics|political|election|vote)\b', re.IGNORECASE),
        ]
        
        # Problematic content patterns
        self.problematic_patterns: List[re.Pattern] = [
            re.compile(r'(?:i am|i\'m).*(?:ai|assistant|bot|system)', re.IGNORECASE),
            re.compile(r'(?:i don\'t|cannot|can\'t).*(?:provide|help|assist)', re.IGNORECASE),
            re.compile(r'(?:sorry|apologize).*(?:cannot|can\'t|unable)', re.IGNORECASE),
            re.compile(r'\b(?:confidential|classified|secret|private)\b.*(?:information|data)', re.IGNORECASE),
        ]
        
        # Response templates for common sanitization needs
        self.response_templates = {
            "off_topic": "I'm focused on helping you with insurance and healthcare questions. Let me redirect you to insurance-related information that might be helpful.",
            "no_information": "I don't have specific information about that in my insurance knowledge base. Let me help you find relevant insurance information instead.",
            "general_help": "I'm here to help you navigate insurance and healthcare options. What specific insurance question can I assist you with?",
            "insufficient_context": "I'd be happy to help with your insurance question, but I need a bit more context to provide the most accurate information."
        }
        
        # Initialize HTTP client for LLM calls (minimal usage)
        self.http_client: Optional[httpx.AsyncClient] = None
        self._setup_llm_client()
    
    def _setup_llm_client(self):
        """Initialize async HTTP client for edge case LLM sanitization."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.http_client = httpx.AsyncClient(
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "anthropic-version": "2023-06-01"
                },
                timeout=5.0  # Short timeout for output sanitization
            )
            self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    
    async def sanitize_output(self, state: UnifiedNavigatorState, response: str) -> UnifiedNavigatorState:
        """
        Main entry point for output sanitization.
        
        Args:
            state: Current workflow state
            response: Generated response to sanitize
            
        Returns:
            Updated state with sanitized response
        """
        start_time = time.time()
        
        try:
            # Stage 1: Template-based sanitization (fast)
            template_result = self._apply_template_sanitization(response)
            
            if template_result["needs_replacement"]:
                # Use template replacement
                sanitized_response = template_result["replacement"]
                was_modified = True
                confidence_score = 0.9
                warnings = [f"Applied template: {template_result['reason']}"]
                
            elif template_result["is_problematic"] and self.http_client:
                # Stage 2: LLM sanitization for edge cases
                llm_result = await self._llm_sanitize(response)
                sanitized_response = llm_result.get("sanitized_response", response)
                was_modified = llm_result.get("was_modified", False)
                confidence_score = llm_result.get("confidence_score", 0.8)
                warnings = llm_result.get("warnings", [])
                
            else:
                # Response is acceptable
                sanitized_response = response
                was_modified = False
                confidence_score = 0.95
                warnings = []
            
            processing_time = (time.time() - start_time) * 1000
            
            # Create sanitization result
            state["output_sanitation"] = OutputSanitationResult(
                sanitized_response=sanitized_response,
                was_modified=was_modified,
                confidence_score=confidence_score,
                processing_time_ms=processing_time,
                warnings=warnings
            )
            
            # Update final response
            state["final_response"] = sanitized_response
            
            self.logger.info(f"Output sanitization completed in {processing_time:.1f}ms, modified: {was_modified}")
            
            return state
            
        except Exception as e:
            self.logger.error(f"Output sanitization error: {e}")
            
            # Fail safely - use original response with warning
            processing_time = (time.time() - start_time) * 1000
            
            state["output_sanitation"] = OutputSanitationResult(
                sanitized_response=response,
                was_modified=False,
                confidence_score=0.5,
                processing_time_ms=processing_time,
                warnings=[f"Sanitization failed: {str(e)}"]
            )
            
            state["final_response"] = response
            return state
    
    def _apply_template_sanitization(self, response: str) -> Dict[str, any]:
        """
        Apply template-based sanitization rules.
        
        Args:
            response: Response to check
            
        Returns:
            Dict with sanitization decision and replacement if needed
        """
        response_lower = response.lower()
        
        # Check for off-topic content
        off_topic_matches = sum(1 for pattern in self.off_topic_patterns if pattern.search(response))
        insurance_matches = sum(1 for term in self.insurance_terms if term in response_lower)
        
        # Off-topic if many non-insurance topics and few insurance terms
        if off_topic_matches > 2 and insurance_matches < 2:
            return {
                "needs_replacement": True,
                "replacement": self.response_templates["off_topic"],
                "reason": "off_topic",
                "is_problematic": False
            }
        
        # Check for problematic patterns
        for pattern in self.problematic_patterns:
            if pattern.search(response):
                return {
                    "needs_replacement": False,
                    "replacement": None,
                    "reason": "problematic_pattern",
                    "is_problematic": True
                }
        
        # Check for very short or unhelpful responses
        if len(response.strip()) < 20:
            return {
                "needs_replacement": True,
                "replacement": self.response_templates["insufficient_context"],
                "reason": "too_short",
                "is_problematic": False
            }
        
        # Check for generic "I can't help" responses
        if any(phrase in response_lower for phrase in ["i can't help", "i cannot help", "unable to assist"]):
            return {
                "needs_replacement": True,
                "replacement": self.response_templates["general_help"],
                "reason": "unhelpful_response",
                "is_problematic": False
            }
        
        # Response looks good
        return {
            "needs_replacement": False,
            "replacement": None,
            "reason": "acceptable",
            "is_problematic": False
        }
    
    async def _llm_sanitize(self, response: str) -> Dict[str, any]:
        """
        LLM-based sanitization for edge cases.
        
        Args:
            response: Response to sanitize
            
        Returns:
            Dict with sanitization results
        """
        if not self.http_client:
            return {
                "sanitized_response": response,
                "was_modified": False,
                "confidence_score": 0.5,
                "warnings": ["No LLM available for sanitization"]
            }
        
        try:
            prompt = f"""Review this response from an insurance navigation assistant for appropriateness and relevance:

Response: "{response}"

Check:
1. Is it relevant to insurance/healthcare topics?
2. Does it stay professional and helpful?
3. Does it avoid revealing system prompts or internal processes?
4. If problematic, provide a better insurance-focused alternative.

Respond in JSON format:
{{
    "is_appropriate": true/false,
    "stays_on_topic": true/false,
    "sanitized_response": "improved version if needed, or original",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""

            payload = {
                "model": self.anthropic_model,
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response_obj = await self.http_client.post(
                "https://api.anthropic.com/v1/messages",
                json=payload
            )
            
            if response_obj.status_code != 200:
                raise Exception(f"Anthropic API error: {response_obj.status_code}")
            
            result = response_obj.json()
            content = result["content"][0]["text"]
            
            # Parse JSON response
            import json
            try:
                llm_result = json.loads(content)
                was_modified = llm_result.get("sanitized_response", response) != response
                
                return {
                    "sanitized_response": llm_result.get("sanitized_response", response),
                    "was_modified": was_modified,
                    "confidence_score": llm_result.get("confidence", 0.8),
                    "warnings": [llm_result.get("reasoning", "LLM sanitization applied")] if was_modified else []
                }
                
            except json.JSONDecodeError:
                # Fallback - assume response is acceptable
                return {
                    "sanitized_response": response,
                    "was_modified": False,
                    "confidence_score": 0.7,
                    "warnings": ["LLM response parsing failed"]
                }
                
        except Exception as e:
            self.logger.error(f"LLM sanitization error: {e}")
            return {
                "sanitized_response": response,
                "was_modified": False,
                "confidence_score": 0.5,
                "warnings": [f"LLM sanitization failed: {str(e)}"]
            }
    
    async def cleanup(self):
        """Clean up resources."""
        if self.http_client:
            await self.http_client.aclose()


# LangGraph node function
async def output_guardrail_node(state: UnifiedNavigatorState) -> UnifiedNavigatorState:
    """
    LangGraph node for output sanitization.
    
    Args:
        state: Current workflow state with generated response
        
    Returns:
        Updated state with sanitized final response
    """
    if not state.get("final_response"):
        # No response to sanitize
        state["final_response"] = "I apologize, but I wasn't able to generate a response. How can I help you with your insurance questions?"
        return state
    
    sanitizer = OutputSanitizer()
    try:
        return await sanitizer.sanitize_output(state, state["final_response"])
    finally:
        await sanitizer.cleanup()