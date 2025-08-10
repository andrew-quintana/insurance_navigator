"""Sanitization Agent implementation for cleaning and structuring input."""

import logging
import re
from typing import Dict, List

from .types import SanitizedOutput, UserContext, SanitizationError
from .config import get_quality_config, get_input_config

logger = logging.getLogger(__name__)


class SanitizationAgent:
    """Agent for sanitizing and structuring translated input."""
    
    def __init__(self):
        """Initialize the sanitization agent."""
        self.quality_config = get_quality_config()
        self.input_config = get_input_config()
        self.domain_keywords = self._load_insurance_keywords()
        
        logger.info("Sanitization agent initialized")
    
    async def sanitize(self, input_text: str, context: UserContext) -> SanitizedOutput:
        """Clean and structure translated text for downstream agents.
        
        Args:
            input_text: Text to sanitize (typically translated)
            context: User context for disambiguation
            
        Returns:
            SanitizedOutput with cleaned text and metadata
        """
        if not input_text or not input_text.strip():
            raise SanitizationError("Empty input text provided for sanitization")
        
        logger.info(f"Sanitizing input text: {len(input_text)} characters")
        
        original_text = input_text
        modifications = []
        
        # Step 1: Basic cleaning
        cleaned_text = self._basic_cleanup(input_text)
        if cleaned_text != input_text:
            modifications.append("Basic cleanup applied")
        
        # Step 2: Resolve coreferences
        resolved_text = self._resolve_coreferences(cleaned_text, context)
        if resolved_text != cleaned_text:
            modifications.append("Coreference resolution applied")
        
        # Step 3: Clarify intent
        clarified_text = self._clarify_intent(resolved_text)
        if clarified_text != resolved_text:
            modifications.append("Intent clarification applied")
        
        # Step 4: Structure output
        structured_prompt = self._structure_output(clarified_text)
        modifications.append("Text structured as formal prompt")
        
        # Calculate confidence score
        confidence = self._calculate_confidence(original_text, structured_prompt, modifications)
        
        # Prepare metadata
        metadata = {
            "domain_context": self.input_config["domain_context"],
            "processing_steps": len(modifications),
            "text_length_before": len(original_text),
            "text_length_after": len(structured_prompt),
            "context_validation_enabled": self.input_config["enable_context_validation"]
        }
        
        result = SanitizedOutput(
            cleaned_text=clarified_text,
            structured_prompt=structured_prompt,
            confidence=confidence,
            modifications=modifications,
            metadata=metadata,
            original_text=original_text
        )
        
        logger.info(f"Sanitization completed with confidence {confidence}, {len(modifications)} modifications")
        return result
    
    def _basic_cleanup(self, text: str) -> str:
        """Perform basic text cleanup.
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Fix common punctuation issues
        cleaned = re.sub(r'\s+([,.!?])', r'\1', cleaned)
        cleaned = re.sub(r'([.!?])\s*([a-z])', r'\1 \2', cleaned)
        
        # Remove translation artifacts (for Phase 1 placeholder)
        cleaned = re.sub(r'\[TRANSLATED from \w+\]\s*', '', cleaned)
        cleaned = re.sub(r'\[FLASH-TRANSLATED from \w+\]\s*', '', cleaned)
        
        return cleaned
    
    def _resolve_coreferences(self, text: str, context: UserContext) -> str:
        """Replace pronouns with explicit references.
        
        Note: This is a basic implementation for Phase 1.
        In Phase 2, implement more sophisticated coreference resolution.
        
        Args:
            text: Input text
            context: User context for resolution
            
        Returns:
            Text with resolved coreferences
        """
        resolved = text
        
        # Basic pronoun resolution (placeholder for Phase 1)
        if context.domain_context == "insurance":
            # Replace common insurance-related pronouns
            resolved = re.sub(r'\bit\b', 'the insurance policy', resolved, flags=re.IGNORECASE)
            resolved = re.sub(r'\bthis\b(?!\s+\w)', 'this insurance matter', resolved, flags=re.IGNORECASE)
            resolved = re.sub(r'\bthat\b(?!\s+\w)', 'that insurance issue', resolved, flags=re.IGNORECASE)
        
        return resolved
    
    def _clarify_intent(self, text: str) -> str:
        """Expand ambiguous terms using domain context.
        
        Args:
            text: Input text
            
        Returns:
            Text with clarified intent
        """
        clarified = text
        
        # Expand common abbreviations and ambiguous terms
        domain_expansions = {
            r'\bcoverage\b': 'insurance coverage',
            r'\bclaim\b': 'insurance claim',
            r'\bpolicy\b': 'insurance policy',
            r'\bpremium\b': 'insurance premium',
            r'\bdeductible\b': 'insurance deductible',
            r'\bbenefits\b': 'insurance benefits'
        }
        
        for pattern, replacement in domain_expansions.items():
            if re.search(pattern, clarified, re.IGNORECASE):
                # Only replace if not already qualified
                if replacement not in clarified.lower():
                    clarified = re.sub(pattern, replacement, clarified, flags=re.IGNORECASE)
        
        return clarified
    
    def _structure_output(self, text: str) -> str:
        """Convert to structured prompt format.
        
        Args:
            text: Input text
            
        Returns:
            Structured prompt
        """
        # Ensure the text ends with proper punctuation
        if not text.endswith(('.', '!', '?')):
            text += '.'
        
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]
        
        # Structure as a formal request
        structured = f"The user is asking about the following insurance matter: {text}"
        
        return structured
    
    def _calculate_confidence(self, original: str, structured: str, modifications: List[str]) -> float:
        """Calculate confidence score for sanitization.
        
        Args:
            original: Original input text
            structured: Structured output text
            modifications: List of modifications applied
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        base_confidence = 0.8
        
        # Adjust based on text length changes
        length_ratio = len(structured) / max(len(original), 1)
        if length_ratio > 2.0:  # Text grew significantly
            base_confidence -= 0.1
        elif length_ratio < 0.5:  # Text shrank significantly
            base_confidence -= 0.05
        
        # Adjust based on number of modifications
        if len(modifications) > 4:
            base_confidence -= 0.1
        elif len(modifications) == 0:
            base_confidence += 0.1
        
        # Ensure confidence is within valid range
        return max(0.1, min(1.0, base_confidence))
    
    def _load_insurance_keywords(self) -> Dict[str, List[str]]:
        """Load domain-specific keywords for disambiguation.
        
        Returns:
            Dictionary of keyword categories and their terms
        """
        return {
            "coverage_types": [
                "health", "auto", "home", "life", "disability", "liability",
                "comprehensive", "collision", "uninsured", "underinsured"
            ],
            "claim_terms": [
                "claim", "deductible", "premium", "copay", "coinsurance",
                "out-of-pocket", "reimbursement", "settlement"
            ],
            "policy_terms": [
                "policy", "coverage", "benefits", "exclusions", "limitations",
                "renewal", "cancellation", "effective date", "expiration"
            ],
            "financial_terms": [
                "cost", "price", "payment", "billing", "invoice", "statement",
                "balance", "refund", "credit", "debit"
            ]
        }
    
    def get_domain_keywords(self) -> Dict[str, List[str]]:
        """Get domain-specific keywords for disambiguation."""
        return self.domain_keywords.copy()