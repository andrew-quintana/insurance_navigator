"""
Insurance Terminology Translation Utility

This module provides functionality to validate and support insurance terminology translation.
The main translation is now handled by LLM in the agent for better flexibility.
"""

from typing import Dict, List, Optional
import re


class InsuranceTerminologyTranslator:
    """
    Supports insurance terminology translation with validation and fallback capabilities.
    
    The main translation is now handled by LLM in the agent for better flexibility.
    This utility provides validation and fallback functionality.
    """
    
    def __init__(self):
        """Initialize the terminology translator with validation dictionaries."""
        # Keep a minimal set of common terms for validation and fallback
        self._common_to_expert = {
            "doctor": "physician",
            "doctor visit": "outpatient physician services",
            "prescription": "prescription drug",
            "prescription drug": "prescription drug benefits",
            "physical therapy": "physical therapy services",
            "copay": "cost-sharing",
            "deductible": "annual deductible",
            "coverage": "benefit coverage",
            "network": "provider network"
        }
        
        # Insurance terms for validation
        self._insurance_terms = [
            "benefit", "coverage", "copayment", "deductible", "physician", 
            "services", "prescription", "network", "authorization", "cost-sharing"
        ]
    
    def validate_translation(self, original: str, translated: str) -> bool:
        """
        Validate that a translation is reasonable.
        
        Args:
            original: The original query
            translated: The translated query
            
        Returns:
            True if translation is valid, False otherwise
        """
        # Basic validation checks
        if not translated or len(translated.strip()) == 0:
            return False
        
        # Check that translation is different from original (some change occurred)
        if original.lower() == translated.lower():
            return False
        
        # Check that translation contains insurance terminology
        has_insurance_terms = any(term in translated.lower() for term in self._insurance_terms)
        
        return has_insurance_terms
    
    def get_fallback_translation(self, query: str) -> str:
        """
        Get fallback translation using simple keyword replacement.
        
        Args:
            query: The user's natural language query
            
        Returns:
            Basic expert-level query
        """
        translated = query.lower()
        for common, expert in self._common_to_expert.items():
            translated = translated.replace(common, expert)
        
        return translated
    
    def get_synonyms(self, term: str) -> List[str]:
        """
        Get synonyms for a given insurance term.
        
        Args:
            term: The term to find synonyms for
            
        Returns:
            List of synonyms
        """
        synonyms = []
        
        # Find all expert terms that map to this term
        for common_term, expert_term in self._common_to_expert.items():
            if expert_term.lower() == term.lower():
                synonyms.append(common_term)
        
        # Add reverse mappings
        for common_term, expert_term in self._common_to_expert.items():
            if common_term.lower() == term.lower():
                synonyms.append(expert_term)
        
        return list(set(synonyms)) 