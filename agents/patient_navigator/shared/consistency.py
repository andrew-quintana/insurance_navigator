"""
Self-Consistency Implementation Utility

This module provides functionality for implementing self-consistency methodology
in response generation, ensuring high-quality and reliable responses.
"""

from typing import List, Dict, Any, Optional
import re
from difflib import SequenceMatcher


class SelfConsistencyChecker:
    """
    Implements self-consistency methodology for response validation.
    
    This utility generates multiple response variants and calculates consistency
    scores to ensure reliable and accurate responses.
    """
    
    def __init__(self, min_consistency_threshold: float = 0.8, max_variants: int = 5):
        """
        Initialize the consistency checker.
        
        Args:
            min_consistency_threshold: Minimum consistency score for acceptable responses
            max_variants: Maximum number of response variants to generate
        """
        self.min_consistency_threshold = min_consistency_threshold
        self.max_variants = max_variants
    
    def generate_variants(self, chunks: List[Any], query: str, num_variants: int = 3) -> List[str]:
        """
        Generate multiple response variants from retrieved chunks.
        
        Args:
            chunks: List of document chunks with context
            query: The original user query
            num_variants: Number of variants to generate
            
        Returns:
            List of response variant strings
        """
        # This method is now a placeholder - actual variant generation
        # is handled by the agent's _generate_response_variants method
        # which uses LLM for more sophisticated generation
        
        # For backward compatibility, return placeholder variants
        variants = []
        
        for i in range(min(num_variants, self.max_variants)):
            variant = f"Response variant {i+1} for query: {query}"
            variants.append(variant)
        
        return variants
    
    def calculate_consistency(self, responses: List[str]) -> float:
        """
        Calculate consistency score across response variants.
        
        Args:
            responses: List of response strings to compare
            
        Returns:
            Consistency score between 0.0 and 1.0
        """
        if len(responses) < 2:
            return 1.0  # Single response is perfectly consistent
        
        # Calculate pairwise similarities
        similarities = []
        
        for i in range(len(responses)):
            for j in range(i + 1, len(responses)):
                similarity = self._calculate_pairwise_similarity(responses[i], responses[j])
                similarities.append(similarity)
        
        # Return average similarity as consistency score
        if similarities:
            return sum(similarities) / len(similarities)
        else:
            return 0.0
    
    def _calculate_pairwise_similarity(self, response1: str, response2: str) -> float:
        """
        Calculate similarity between two response strings.
        
        Args:
            response1: First response string
            response2: Second response string
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Use sequence matcher for string similarity
        matcher = SequenceMatcher(None, response1.lower(), response2.lower())
        return matcher.ratio()
    
    def extract_key_points(self, responses: List[str]) -> List[str]:
        """
        Extract key points that are consistent across multiple responses.
        
        Args:
            responses: List of response strings
            
        Returns:
            List of consistent key points
        """
        if not responses:
            return []
        
        # Extract sentences from all responses
        all_sentences = []
        for response in responses:
            sentences = self._extract_sentences(response)
            all_sentences.extend(sentences)
        
        # Find sentences that appear in multiple responses (consistency)
        sentence_counts = {}
        for sentence in all_sentences:
            sentence_clean = self._clean_sentence(sentence)
            if sentence_clean:
                sentence_counts[sentence_clean] = sentence_counts.get(sentence_clean, 0) + 1
        
        # Return sentences that appear in at least 2 responses
        consistent_sentences = [
            sentence for sentence, count in sentence_counts.items()
            if count >= 2
        ]
        
        return consistent_sentences[:10]  # Limit to top 10 key points
    
    def _extract_sentences(self, text: str) -> List[str]:
        """
        Extract sentences from text.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        # Simple sentence extraction using period, exclamation, question mark
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _clean_sentence(self, sentence: str) -> str:
        """
        Clean and normalize a sentence for comparison.
        
        Args:
            sentence: Input sentence
            
        Returns:
            Cleaned sentence
        """
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', sentence.strip())
        return cleaned.lower()
    
    def synthesize_final_response(self, responses: List[str], consistency_score: float) -> str:
        """
        Synthesize final response from multiple variants.
        
        Args:
            responses: List of response variants
            consistency_score: Calculated consistency score
            
        Returns:
            Synthesized final response
        """
        if not responses:
            return ""
        
        if consistency_score >= self.min_consistency_threshold:
            # High consistency - use the most complete response
            return max(responses, key=len)
        else:
            # Low consistency - combine key points from all responses
            key_points = self.extract_key_points(responses)
            if key_points:
                return " ".join(key_points)
            else:
                # Fallback to first response
                return responses[0] if responses else ""
    
    def should_continue_generation(self, current_variants: List[str], iteration: int) -> bool:
        """
        Determine if more variants should be generated.
        
        Args:
            current_variants: List of currently generated variants
            iteration: Current iteration number
            
        Returns:
            True if more variants should be generated, False otherwise
        """
        # Stop if we've reached max variants
        if len(current_variants) >= self.max_variants:
            return False
        
        # Stop if we've reached max iterations
        if iteration >= 5:
            return False
        
        # Stop if we have high consistency
        if len(current_variants) >= 2:
            consistency = self.calculate_consistency(current_variants)
            if consistency >= self.min_consistency_threshold:
                return False
        
        return True
    
    def calculate_confidence_score(self, responses: List[str], consistency_score: float) -> float:
        """
        Calculate confidence score based on consistency and response quality.
        
        Args:
            responses: List of response variants
            consistency_score: Calculated consistency score
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not responses:
            return 0.0
        
        # Base confidence on consistency score
        confidence = consistency_score
        
        # Adjust based on number of responses (more responses = higher confidence)
        response_factor = min(len(responses) / self.max_variants, 1.0)
        confidence *= (0.7 + 0.3 * response_factor)
        
        # Adjust based on response length (longer responses = more complete)
        avg_length = sum(len(r) for r in responses) / len(responses)
        length_factor = min(avg_length / 500, 1.0)  # Normalize to 500 chars
        confidence *= (0.8 + 0.2 * length_factor)
        
        return min(confidence, 1.0)
    
    def validate_response_quality(self, response: str) -> Dict[str, Any]:
        """
        Validate the quality of a generated response.
        
        Args:
            response: The response to validate
            
        Returns:
            Dictionary with quality metrics
        """
        quality_metrics = {
            "length": len(response),
            "has_insurance_terms": False,
            "has_specific_info": False,
            "is_complete": False
        }
        
        # Check for insurance terminology
        insurance_terms = [
            "copay", "deductible", "coverage", "benefit", "physician", 
            "services", "prescription", "network", "authorization"
        ]
        quality_metrics["has_insurance_terms"] = any(
            term in response.lower() for term in insurance_terms
        )
        
        # Check for specific information (numbers, amounts)
        has_numbers = bool(re.search(r'\$\d+|\d+\s*%|\d+\s*visits?', response))
        quality_metrics["has_specific_info"] = has_numbers
        
        # Check completeness (has both question and answer)
        quality_metrics["is_complete"] = len(response) > 50 and ":" in response
        
        return quality_metrics 