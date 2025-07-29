"""
Insurance Terminology Translation Utility

This module provides functionality to translate common language queries into
insurance-specific terminology for improved document retrieval and response generation.
"""

from typing import Dict, List, Optional
import re


class InsuranceTerminologyTranslator:
    """
    Translates common language to insurance-specific terminology.
    
    This utility provides keyword-based mapping for MVP implementation.
    Future versions will use ML-based translation for more sophisticated handling.
    """
    
    def __init__(self):
        """Initialize the terminology translator with mapping dictionaries."""
        self._common_to_expert = {
            # Doctor/Provider terms
            "doctor": "physician",
            "doctor visit": "outpatient physician services",
            "doctor visits": "outpatient physician services",
            "primary care": "primary care physician",
            "specialist": "specialist physician",
            "specialist visit": "specialist physician services",
            "specialist visits": "specialist physician services",
            "provider": "healthcare provider",
            "providers": "healthcare providers",
            
            # Coverage/Benefits terms
            "coverage": "benefit coverage",
            "covered": "covered services",
            "benefits": "benefit structure",
            "what's covered": "covered services analysis",
            "what is covered": "covered services analysis",
            "what does my insurance cover": "benefit coverage analysis",
            
            # Cost terms
            "copay": "copayment",
            "copays": "copayments",
            "cost": "cost-sharing",
            "costs": "cost-sharing",
            "deductible": "annual deductible",
            "coinsurance": "coinsurance percentage",
            "out of pocket": "out-of-pocket costs",
            "out-of-pocket": "out-of-pocket costs",
            
            # Prescription terms
            "prescription": "prescription drug",
            "prescriptions": "prescription drugs",
            "prescription drug": "prescription drug benefit",
            "prescription drugs": "prescription drug benefits",
            "medication": "prescription medication",
            "medications": "prescription medications",
            "pharmacy": "pharmacy benefit",
            "drug": "prescription drug",
            "drugs": "prescription drugs",
            
            # Service-specific terms
            "physical therapy": "physical therapy services",
            "pt": "physical therapy services",
            "rehab": "rehabilitative services",
            "rehabilitation": "rehabilitative services",
            "mental health": "mental health services",
            "therapy": "therapeutic services",
            "surgery": "surgical services",
            "hospital": "inpatient hospital services",
            "emergency": "emergency services",
            "urgent care": "urgent care services",
            
            # Network terms
            "network": "provider network",
            "in network": "participating providers",
            "out of network": "non-participating providers",
            "out-of-network": "non-participating providers",
            
            # Authorization terms
            "referral": "referral requirement",
            "referrals": "referral requirements",
            "prior authorization": "prior authorization requirement",
            "pre-authorization": "prior authorization requirement",
            "preauth": "prior authorization requirement",
            
            # Limits and restrictions
            "limit": "benefit limit",
            "limits": "benefit limits",
            "maximum": "benefit maximum",
            "restriction": "benefit restriction",
            "restrictions": "benefit restrictions",
            
            # Time periods
            "year": "calendar year",
            "annual": "annual benefit period",
            "monthly": "monthly benefit period",
            "per year": "per calendar year",
            "per month": "per month"
        }
        
        self._context_specific = {
            "coverage": {
                "contexts": ["benefits", "covered services", "benefit coverage"],
                "default": "benefit coverage"
            },
            "costs": {
                "contexts": ["copays", "deductibles", "coinsurance", "cost-sharing"],
                "default": "cost-sharing"
            },
            "limits": {
                "contexts": ["visit limits", "dollar limits", "time limits", "benefit limits"],
                "default": "benefit limits"
            }
        }
    
    def translate_query(self, query: str) -> str:
        """
        Convert user query to expert insurance terminology.
        
        Args:
            query: The user's natural language query
            
        Returns:
            Expert-level query in insurance terminology
        """
        # Convert to lowercase for matching
        query_lower = query.lower()
        translated_query = query
        
        # Apply direct mappings
        for common_term, expert_term in self._common_to_expert.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(common_term) + r'\b'
            translated_query = re.sub(pattern, expert_term, translated_query, flags=re.IGNORECASE)
        
        # Apply context-specific translations
        translated_query = self._apply_context_specific_translations(translated_query)
        
        return translated_query
    
    def _apply_context_specific_translations(self, query: str) -> str:
        """
        Apply context-specific translations based on surrounding terms.
        
        Args:
            query: The query to translate
            
        Returns:
            Query with context-specific translations applied
        """
        query_lower = query.lower()
        
        for term, context_info in self._context_specific.items():
            if term in query_lower:
                # Determine context based on surrounding words
                context = self._determine_context(query_lower, term)
                if context in context_info["contexts"]:
                    # Replace with context-specific term
                    pattern = r'\b' + re.escape(term) + r'\b'
                    query = re.sub(pattern, context, query, flags=re.IGNORECASE)
                else:
                    # Use default translation
                    pattern = r'\b' + re.escape(term) + r'\b'
                    query = re.sub(pattern, context_info["default"], query, flags=re.IGNORECASE)
        
        return query
    
    def _determine_context(self, query: str, term: str) -> str:
        """
        Determine the context of a term based on surrounding words.
        
        Args:
            query: The query to analyze
            term: The term to determine context for
            
        Returns:
            The determined context
        """
        # Simple context detection based on nearby words
        words = query.split()
        term_index = -1
        
        for i, word in enumerate(words):
            if term in word:
                term_index = i
                break
        
        if term_index == -1:
            return "default"
        
        # Check surrounding words for context clues
        context_clues = {
            "visit": "visit limits",
            "dollar": "dollar limits", 
            "time": "time limits",
            "benefit": "benefit limits",
            "copay": "copays",
            "deductible": "deductibles",
            "coinsurance": "coinsurance",
            "cost": "cost-sharing",
            "benefit": "benefit coverage",
            "covered": "covered services"
        }
        
        # Check words before and after the term
        for i in range(max(0, term_index - 2), min(len(words), term_index + 3)):
            if i != term_index:
                word = words[i]
                for clue, context in context_clues.items():
                    if clue in word:
                        return context
        
        return "default"
    
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
        insurance_terms = [
            "benefit", "coverage", "copayment", "deductible", "physician", 
            "services", "prescription", "network", "authorization"
        ]
        
        has_insurance_terms = any(term in translated.lower() for term in insurance_terms)
        
        return has_insurance_terms 