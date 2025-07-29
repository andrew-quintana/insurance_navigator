"""
Test utilities for semantic similarity validation.

This module provides utilities for comparing expected and actual outputs
using semantic similarity rather than exact text matching.
"""

from typing import List, Tuple
from difflib import SequenceMatcher
import re


class SemanticSimilarityTester:
    """
    Utility class for semantic similarity testing using difflib and keyword matching.
    
    This allows tests to compare expected and actual outputs based on semantic
    similarity rather than exact text matching, making tests more robust.
    """
    
    def __init__(self):
        """Initialize the semantic similarity tester."""
        pass
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts using difflib.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def assert_semantic_similarity(self, actual: str, expected: str, threshold: float = 0.7, 
                                 message: str = None) -> None:
        """
        Assert that two texts are semantically similar above a threshold.
        
        Args:
            actual: Actual text output
            expected: Expected text output
            threshold: Minimum similarity threshold (default: 0.7)
            message: Custom assertion message
        """
        similarity = self.calculate_similarity(actual, expected)
        
        if message is None:
            message = f"Semantic similarity {similarity:.3f} is below threshold {threshold:.3f}"
        
        assert similarity >= threshold, f"{message} (similarity: {similarity:.3f})"
    
    def assert_contains_semantic_content(self, text: str, expected_content: List[str], 
                                       threshold: float = 0.6, message: str = None) -> None:
        """
        Assert that text contains semantic content from expected list.
        
        Args:
            text: Text to check
            expected_content: List of expected semantic content
            threshold: Minimum similarity threshold (default: 0.6)
            message: Custom assertion message
        """
        max_similarity = 0.0
        best_match = ""
        
        for expected in expected_content:
            similarity = self.calculate_similarity(text, expected)
            if similarity > max_similarity:
                max_similarity = similarity
                best_match = expected
        
        if message is None:
            message = f"Text does not contain expected semantic content. Best match: '{best_match}'"
        
        assert max_similarity >= threshold, f"{message} (best similarity: {max_similarity:.3f})"
    
    def validate_translation_quality(self, original: str, translated: str, 
                                   expected_keywords: List[str] = None) -> Tuple[bool, float]:
        """
        Validate translation quality using semantic similarity.
        
        Args:
            original: Original text
            translated: Translated text
            expected_keywords: List of expected keywords in translation
            
        Returns:
            Tuple of (is_valid, similarity_score)
        """
        # Check basic similarity
        similarity = self.calculate_similarity(original, translated)
        
        # Check for expected keywords if provided
        keyword_similarity = 0.0
        if expected_keywords:
            keyword_scores = []
            for keyword in expected_keywords:
                # Check if keyword appears in translated text
                if keyword.lower() in translated.lower():
                    keyword_similarity = max(keyword_similarity, 0.8)
                else:
                    # Check semantic similarity
                    keyword_sim = self.calculate_similarity(translated, keyword)
                    keyword_similarity = max(keyword_similarity, keyword_sim)
                keyword_scores.append(keyword_similarity)
            keyword_similarity = max(keyword_scores) if keyword_scores else 0.0
        
        # Translation should be reasonably similar but not identical
        is_valid = (0.3 <= similarity <= 0.9) and (keyword_similarity >= 0.4)
        
        return is_valid, similarity
    
    def assert_contains_keywords(self, text: str, keywords: List[str], 
                               case_sensitive: bool = False, message: str = None) -> None:
        """
        Assert that text contains specific keywords.
        
        Args:
            text: Text to check
            keywords: List of keywords to find
            case_sensitive: Whether to use case-sensitive matching
            message: Custom assertion message
        """
        text_to_check = text if case_sensitive else text.lower()
        keywords_to_check = keywords if case_sensitive else [k.lower() for k in keywords]
        
        found_keywords = []
        for keyword in keywords_to_check:
            if keyword in text_to_check:
                found_keywords.append(keyword)
        
        if message is None:
            message = f"Text should contain keywords: {keywords}"
        
        assert len(found_keywords) > 0, f"{message} (found: {found_keywords})"


# Global instance for easy use in tests
semantic_tester = SemanticSimilarityTester()


def assert_semantic_match(actual: str, expected: str, threshold: float = 0.7, 
                         message: str = None) -> None:
    """
    Convenience function for semantic similarity assertion.
    
    Args:
        actual: Actual text output
        expected: Expected text output
        threshold: Minimum similarity threshold (default: 0.7)
        message: Custom assertion message
    """
    semantic_tester.assert_semantic_similarity(actual, expected, threshold, message)


def assert_contains_semantic_content(text: str, expected_content: List[str], 
                                   threshold: float = 0.6, message: str = None) -> None:
    """
    Convenience function for semantic content assertion.
    
    Args:
        text: Text to check
        expected_content: List of expected semantic content
        threshold: Minimum similarity threshold (default: 0.6)
        message: Custom assertion message
    """
    semantic_tester.assert_contains_semantic_content(text, expected_content, threshold, message)


def assert_contains_keywords(text: str, keywords: List[str], 
                           case_sensitive: bool = False, message: str = None) -> None:
    """
    Convenience function for keyword assertion.
    
    Args:
        text: Text to check
        keywords: List of keywords to find
        case_sensitive: Whether to use case-sensitive matching
        message: Custom assertion message
    """
    semantic_tester.assert_contains_keywords(text, keywords, case_sensitive, message) 