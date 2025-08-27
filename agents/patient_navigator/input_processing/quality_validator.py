"""Quality Validation and Assessment for Input Processing Workflow.

This module provides comprehensive quality validation for translations,
sanitization, and user intent preservation with scoring and feedback mechanisms.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import re
import json

from .performance_monitor import track_performance, get_performance_monitor
from .types import TranslationResult, SanitizedOutput

logger = logging.getLogger(__name__)


class QualityScore(Enum):
    """Quality score levels."""
    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"           # 80-89%
    ACCEPTABLE = "acceptable"  # 70-79%
    POOR = "poor"           # 60-69%
    UNACCEPTABLE = "unacceptable"  # <60%


@dataclass
class QualityMetrics:
    """Quality assessment metrics."""
    
    overall_score: float
    translation_accuracy: float
    sanitization_effectiveness: float
    intent_preservation: float
    confidence_score: float
    quality_level: QualityScore
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TranslationQualityAssessment:
    """Translation quality assessment results."""
    
    accuracy_score: float
    fluency_score: float
    terminology_consistency: float
    cultural_appropriateness: float
    domain_relevance: float
    issues_detected: List[str]
    confidence: float


@dataclass
class SanitizationQualityAssessment:
    """Sanitization quality assessment results."""
    
    content_cleaning_score: float
    context_preservation_score: float
    domain_relevance_score: float
    user_intent_clarity: float
    issues_detected: List[str]
    confidence: float


class QualityValidator:
    """Comprehensive quality validation for input processing workflow."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize quality validator.
        
        Args:
            config: Quality validation configuration
        """
        self.config = config or {}
        self.performance_monitor = get_performance_monitor()
        
        # Quality thresholds
        self.min_translation_accuracy = self.config.get("min_translation_accuracy", 0.7)
        self.min_sanitization_effectiveness = self.config.get("min_sanitization_effectiveness", 0.6)
        self.min_intent_preservation = self.config.get("min_intent_preservation", 0.8)
        
        # Insurance domain keywords for relevance checking
        self.insurance_keywords = {
            "en": [
                "insurance", "policy", "claim", "coverage", "deductible", "premium",
                "benefits", "provider", "network", "copay", "coinsurance", "out-of-pocket",
                "enrollment", "renewal", "cancellation", "appeal", "denial", "approval"
            ],
            "es": [
                "seguro", "póliza", "reclamo", "cobertura", "deducible", "prima",
                "beneficios", "proveedor", "red", "copago", "coaseguro", "gastos",
                "inscripción", "renovación", "cancelación", "apelación", "negación", "aprobación"
            ]
        }
        
        # Quality scoring weights
        self.scoring_weights = {
            "translation_accuracy": 0.35,
            "sanitization_effectiveness": 0.25,
            "intent_preservation": 0.25,
            "confidence_score": 0.15
        }
        
        logger.info("Quality validator initialized")
    
    @track_performance("quality_validation")
    async def validate_complete_workflow(
        self,
        original_input: str,
        translation_result: TranslationResult,
        sanitized_output: SanitizedOutput,
        user_context: Optional[Dict[str, Any]] = None
    ) -> QualityMetrics:
        """Validate complete workflow quality.
        
        Args:
            original_input: Original user input
            translation_result: Translation result
            sanitized_output: Sanitized output
            user_context: User context information
            
        Returns:
            Comprehensive quality metrics
        """
        try:
            # Assess translation quality
            translation_quality = await self._assess_translation_quality(
                original_input, translation_result
            )
            
            # Assess sanitization quality
            sanitization_quality = await self._assess_sanitization_quality(
                translation_result.text, sanitized_output
            )
            
            # Assess intent preservation
            intent_preservation = await self._assess_intent_preservation(
                original_input, sanitized_output.cleaned_text
            )
            
            # Calculate overall quality score
            overall_score = self._calculate_overall_score(
                translation_quality, sanitization_quality, intent_preservation
            )
            
            # Determine quality level
            quality_level = self._determine_quality_level(overall_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                translation_quality, sanitization_quality, intent_preservation
            )
            
            # Create quality metrics
            metrics = QualityMetrics(
                overall_score=overall_score,
                translation_accuracy=translation_quality.accuracy_score,
                sanitization_effectiveness=sanitization_quality.content_cleaning_score,
                intent_preservation=intent_preservation,
                confidence_score=translation_result.confidence,
                quality_level=quality_level,
                issues=self._collect_issues(translation_quality, sanitization_quality),
                recommendations=recommendations,
                metadata={
                    "translation_quality": translation_quality,
                    "sanitization_quality": sanitization_quality,
                    "intent_preservation": intent_preservation
                }
            )
            
            logger.info(f"Quality validation complete: {overall_score:.2f} ({quality_level.value})")
            return metrics
            
        except Exception as e:
            logger.error(f"Quality validation failed: {e}")
            # Return minimal quality metrics on failure
            return QualityMetrics(
                overall_score=0.0,
                translation_accuracy=0.0,
                sanitization_effectiveness=0.0,
                intent_preservation=0.0,
                confidence_score=0.0,
                quality_level=QualityScore.UNACCEPTABLE,
                issues=[f"Validation error: {e}"],
                recommendations=["Review system logs for validation errors"]
            )
    
    async def _assess_translation_quality(
        self, 
        original_input: str, 
        translation_result: TranslationResult
    ) -> TranslationQualityAssessment:
        """Assess translation quality."""
        try:
            # Basic accuracy scoring based on confidence
            accuracy_score = min(translation_result.confidence, 1.0)
            
            # Fluency scoring (basic heuristic)
            fluency_score = self._assess_fluency(translation_result.text)
            
            # Terminology consistency
            terminology_consistency = self._assess_terminology_consistency(
                translation_result.text, translation_result.target_language
            )
            
            # Cultural appropriateness
            cultural_appropriateness = self._assess_cultural_appropriateness(
                translation_result.text, translation_result.target_language
            )
            
            # Domain relevance
            domain_relevance = self._assess_domain_relevance(
                translation_result.text, translation_result.target_language
            )
            
            # Detect issues
            issues_detected = self._detect_translation_issues(
                original_input, translation_result
            )
            
            # Overall confidence
            confidence = (accuracy_score + fluency_score + terminology_consistency + 
                        cultural_appropriateness + domain_relevance) / 5
            
            return TranslationQualityAssessment(
                accuracy_score=accuracy_score,
                fluency_score=fluency_score,
                terminology_consistency=terminology_consistency,
                cultural_appropriateness=cultural_appropriateness,
                domain_relevance=domain_relevance,
                issues_detected=issues_detected,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Translation quality assessment failed: {e}")
            return TranslationQualityAssessment(
                accuracy_score=0.0,
                fluency_score=0.0,
                terminology_consistency=0.0,
                cultural_appropriateness=0.0,
                domain_relevance=0.0,
                issues_detected=[f"Assessment error: {e}"],
                confidence=0.0
            )
    
    async def _assess_sanitization_quality(
        self, 
        translated_text: str, 
        sanitized_output: SanitizedOutput
    ) -> SanitizationQualityAssessment:
        """Assess sanitization quality."""
        try:
            # Content cleaning effectiveness
            content_cleaning_score = self._assess_content_cleaning(
                translated_text, sanitized_output.cleaned_text
            )
            
            # Context preservation
            context_preservation_score = self._assess_context_preservation(
                translated_text, sanitized_output
            )
            
            # Domain relevance
            target_language = getattr(sanitized_output, 'target_language', 'en')
            domain_relevance_score = self._assess_domain_relevance(
                sanitized_output.cleaned_text, target_language
            )
            
            # User intent clarity
            user_intent_clarity = self._assess_user_intent_clarity(
                sanitized_output.cleaned_text
            )
            
            # Detect issues
            issues_detected = self._detect_sanitization_issues(
                translated_text, sanitized_output
            )
            
            # Overall confidence
            confidence = (content_cleaning_score + context_preservation_score + 
                        domain_relevance_score + user_intent_clarity) / 4
            
            return SanitizationQualityAssessment(
                content_cleaning_score=content_cleaning_score,
                context_preservation_score=context_preservation_score,
                domain_relevance_score=domain_relevance_score,
                user_intent_clarity=user_intent_clarity,
                issues_detected=issues_detected,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Sanitization quality assessment failed: {e}")
            return SanitizationQualityAssessment(
                content_cleaning_score=0.0,
                context_preservation_score=0.0,
                domain_relevance_score=0.0,
                user_intent_clarity=0.0,
                issues_detected=[f"Assessment error: {e}"],
                confidence=0.0
            )
    
    async def _assess_intent_preservation(
        self, 
        original_input: str, 
        processed_output: str
    ) -> float:
        """Assess how well user intent is preserved."""
        try:
            # Simple keyword preservation check
            original_keywords = self._extract_keywords(original_input.lower())
            output_keywords = self._extract_keywords(processed_output.lower())
            
            if not original_keywords:
                return 1.0  # No keywords to preserve
            
            # Calculate keyword preservation ratio
            preserved_keywords = len(original_keywords.intersection(output_keywords))
            total_keywords = len(original_keywords)
            
            preservation_ratio = preserved_keywords / total_keywords
            
            # Boost score if output is longer (more detailed)
            if len(processed_output) > len(original_input) * 0.8:
                preservation_ratio = min(preservation_ratio * 1.1, 1.0)
            
            return preservation_ratio
            
        except Exception as e:
            logger.error(f"Intent preservation assessment failed: {e}")
            return 0.5  # Neutral score on error
    
    def _assess_fluency(self, text: str) -> float:
        """Assess text fluency (basic heuristic)."""
        if not text:
            return 0.0
        
        # Simple fluency indicators
        sentences = text.split('.')
        words = text.split()
        
        if not sentences or not words:
            return 0.5
        
        # Average sentence length (optimal: 15-25 words)
        avg_sentence_length = len(words) / len(sentences)
        if 15 <= avg_sentence_length <= 25:
            fluency_score = 1.0
        elif 10 <= avg_sentence_length <= 30:
            fluency_score = 0.8
        elif 5 <= avg_sentence_length <= 40:
            fluency_score = 0.6
        else:
            fluency_score = 0.4
        
        # Penalize excessive punctuation
        punctuation_ratio = sum(1 for c in text if c in '!?;:') / len(text)
        if punctuation_ratio > 0.1:
            fluency_score *= 0.8
        
        return min(fluency_score, 1.0)
    
    def _assess_terminology_consistency(self, text: str, language: str) -> float:
        """Assess insurance terminology consistency."""
        if not text or language not in self.insurance_keywords:
            return 0.5
        
        keywords = self.insurance_keywords[language]
        text_lower = text.lower()
        
        # Count relevant insurance terms
        relevant_terms = sum(1 for keyword in keywords if keyword in text_lower)
        
        # Score based on term density (optimal: 2-5 terms per 100 words)
        word_count = len(text.split())
        term_density = relevant_terms / max(word_count / 100, 1)
        
        if 2 <= term_density <= 5:
            consistency_score = 1.0
        elif 1 <= term_density <= 6:
            consistency_score = 0.8
        elif 0.5 <= term_density <= 8:
            consistency_score = 0.6
        else:
            consistency_score = 0.4
        
        return consistency_score
    
    def _assess_cultural_appropriateness(self, text: str, language: str) -> float:
        """Assess cultural appropriateness (basic implementation)."""
        # For now, return a high score as this requires more sophisticated analysis
        # In production, this could use cultural sensitivity models
        return 0.9
    
    def _assess_domain_relevance(self, text: str, language: str) -> float:
        """Assess domain relevance for insurance context."""
        return self._assess_terminology_consistency(text, language)
    
    def _assess_content_cleaning(self, original: str, cleaned: str) -> float:
        """Assess content cleaning effectiveness."""
        if not original or not cleaned:
            return 0.0
        
        # Check if inappropriate content was removed
        inappropriate_patterns = [
            r'\b(fuck|shit|damn|hell)\b',
            r'\b(ass|bitch|bastard)\b',
            r'[!]{3,}',  # Excessive exclamation marks
            r'[?]{3,}',  # Excessive question marks
        ]
        
        original_inappropriate = sum(
            1 for pattern in inappropriate_patterns 
            if re.search(pattern, original, re.IGNORECASE)
        )
        cleaned_inappropriate = sum(
            1 for pattern in inappropriate_patterns 
            if re.search(pattern, cleaned, re.IGNORECASE)
        )
        
        # Score based on inappropriate content removal
        if original_inappropriate == 0:
            cleaning_score = 1.0  # No inappropriate content to clean
        else:
            removal_ratio = (original_inappropriate - cleaned_inappropriate) / original_inappropriate
            cleaning_score = 0.5 + (removal_ratio * 0.5)
        
        # Bonus for maintaining meaning
        if len(cleaned) >= len(original) * 0.7:
            cleaning_score = min(cleaning_score * 1.1, 1.0)
        
        return min(cleaning_score, 1.0)
    
    def _assess_context_preservation(self, original: str, sanitized_output: SanitizedOutput) -> float:
        """Assess context preservation during sanitization."""
        # Check if key context elements are preserved
        context_elements = [
            "insurance", "policy", "claim", "coverage", "deductible", "premium",
            "benefits", "provider", "network", "copay", "coinsurance"
        ]
        
        original_context = sum(1 for element in context_elements if element in original.lower())
        sanitized_context = sum(1 for element in context_elements if element in sanitized_output.cleaned_text.lower())
        
        if original_context == 0:
            return 1.0  # No context to preserve
        
        preservation_ratio = sanitized_context / original_context
        return min(preservation_ratio, 1.0)
    
    def _assess_user_intent_clarity(self, text: str) -> float:
        """Assess clarity of user intent in processed text."""
        if not text:
            return 0.0
        
        # Simple clarity indicators
        clarity_score = 1.0
        
        # Penalize very short outputs (might lose context)
        if len(text.split()) < 3:
            clarity_score *= 0.7
        
        # Penalize excessive technical jargon
        technical_terms = len([word for word in text.split() if len(word) > 12])
        if technical_terms > len(text.split()) * 0.3:
            clarity_score *= 0.8
        
        # Bonus for clear question structure
        if text.strip().endswith('?'):
            clarity_score *= 1.1
        
        return min(clarity_score, 1.0)
    
    def _extract_keywords(self, text: str) -> set:
        """Extract meaningful keywords from text."""
        # Simple keyword extraction (in production, use NLP libraries)
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        
        keywords = {word for word in words if len(word) > 2 and word not in stop_words}
        return keywords
    
    def _detect_translation_issues(
        self, 
        original_input: str, 
        translation_result: TranslationResult
    ) -> List[str]:
        """Detect translation quality issues."""
        issues = []
        
        # Check for empty translation
        if not translation_result.text.strip():
            issues.append("Empty translation result")
        
        # Check for very low confidence
        if translation_result.confidence < 0.3:
            issues.append(f"Low translation confidence: {translation_result.confidence:.2f}")
        
        # Check for significant length mismatch
        original_length = len(original_input.split())
        translated_length = len(translation_result.text.split())
        
        if original_length > 0:
            length_ratio = translated_length / original_length
            if length_ratio < 0.3:
                issues.append(f"Translation too short (ratio: {length_ratio:.2f})")
            elif length_ratio > 3.0:
                issues.append(f"Translation too long (ratio: {length_ratio:.2f})")
        
        # Check for repeated words (potential translation errors)
        words = translation_result.text.split()
        if len(words) > 5:
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            
            repeated_words = [word for word, count in word_counts.items() if count > 3]
            if repeated_words:
                issues.append(f"Excessive word repetition: {repeated_words[:3]}")
        
        return issues
    
    def _detect_sanitization_issues(
        self, 
        original_text: str, 
        sanitized_output: SanitizedOutput
    ) -> List[str]:
        """Detect sanitization quality issues."""
        issues = []
        
        # Check for empty output
        if not sanitized_output.cleaned_text.strip():
            issues.append("Sanitization produced empty output")
        
        # Check for excessive content removal
        original_length = len(original_text.split())
        sanitized_length = len(sanitized_output.cleaned_text.split())
        
        if original_length > 0:
            removal_ratio = (original_length - sanitized_length) / original_length
            if removal_ratio > 0.7:
                issues.append(f"Excessive content removal: {removal_ratio:.1%}")
        
        # Check for context loss
        if hasattr(sanitized_output, 'context_preserved') and not sanitized_output.context_preserved:
            issues.append("Context information lost during sanitization")
        
        return issues
    
    def _calculate_overall_score(
        self,
        translation_quality: TranslationQualityAssessment,
        sanitization_quality: SanitizationQualityAssessment,
        intent_preservation: float
    ) -> float:
        """Calculate overall quality score."""
        try:
            # Weighted average of all quality components
            weighted_score = (
                translation_quality.confidence * self.scoring_weights["translation_accuracy"] +
                sanitization_quality.confidence * self.scoring_weights["sanitization_effectiveness"] +
                intent_preservation * self.scoring_weights["intent_preservation"] +
                translation_quality.confidence * self.scoring_weights["confidence_score"]
            )
            
            return min(max(weighted_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Score calculation failed: {e}")
            return 0.5
    
    def _determine_quality_level(self, score: float) -> QualityScore:
        """Determine quality level based on score."""
        if score >= 0.9:
            return QualityScore.EXCELLENT
        elif score >= 0.8:
            return QualityScore.GOOD
        elif score >= 0.7:
            return QualityScore.ACCEPTABLE
        elif score >= 0.6:
            return QualityScore.POOR
        else:
            return QualityScore.UNACCEPTABLE
    
    def _generate_recommendations(
        self,
        translation_quality: TranslationQualityAssessment,
        sanitization_quality: SanitizationQualityAssessment,
        intent_preservation: float
    ) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        # Translation recommendations
        if translation_quality.accuracy_score < 0.8:
            recommendations.append("Consider using a different translation provider for better accuracy")
        
        if translation_quality.fluency_score < 0.7:
            recommendations.append("Translation may benefit from post-editing for fluency")
        
        if translation_quality.terminology_consistency < 0.6:
            recommendations.append("Consider adding domain-specific terminology training")
        
        # Sanitization recommendations
        if sanitization_quality.content_cleaning_score < 0.7:
            recommendations.append("Review content cleaning rules for better effectiveness")
        
        if sanitization_quality.context_preservation_score < 0.8:
            recommendations.append("Sanitization may be too aggressive - review preservation rules")
        
        # Intent preservation recommendations
        if intent_preservation < 0.8:
            recommendations.append("Process may be losing user intent - review workflow steps")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Quality is good - continue monitoring for consistency")
        
        return recommendations
    
    def _collect_issues(
        self,
        translation_quality: TranslationQualityAssessment,
        sanitization_quality: SanitizationQualityAssessment
    ) -> List[str]:
        """Collect all detected issues."""
        issues = []
        
        # Translation issues
        issues.extend(translation_quality.issues_detected)
        
        # Sanitization issues
        issues.extend(sanitization_quality.issues_detected)
        
        # Quality threshold issues
        if translation_quality.confidence < self.min_translation_accuracy:
            issues.append(f"Translation accuracy below threshold: {translation_quality.confidence:.2f} < {self.min_translation_accuracy}")
        
        if sanitization_quality.confidence < self.min_sanitization_effectiveness:
            issues.append(f"Sanitization effectiveness below threshold: {sanitization_quality.confidence:.2f} < {self.min_sanitization_effectiveness}")
        
        return issues
    
    async def assess_translation_quality(
        self,
        original_text: str,
        translated_text: str,
        source_language: str,
        target_language: str
    ) -> Dict[str, Any]:
        """Public method to assess translation quality."""
        try:
            # Create mock TranslationResult object
            translation_result = type('TranslationResult', (), {
                'text': translated_text,
                'confidence': 0.9,
                'source_language': source_language,
                'target_language': target_language
            })()
            
            assessment = await self._assess_translation_quality(original_text, translation_result)
            
            return {
                'accuracy_score': assessment.accuracy_score * 100,
                'fluency_score': assessment.fluency_score * 100,
                'domain_score': assessment.domain_relevance * 100,
                'overall_score': assessment.confidence * 100
            }
        except Exception as e:
            logger.error(f"Translation quality assessment failed: {e}")
            return {
                'accuracy_score': 0.0,
                'fluency_score': 0.0,
                'domain_score': 0.0,
                'overall_score': 0.0
            }
    
    async def assess_sanitization_quality(
        self,
        original_text: str,
        sanitized_text: str
    ) -> Dict[str, Any]:
        """Public method to assess sanitization quality."""
        try:
            # Create mock SanitizedOutput object
            sanitized_output = type('SanitizedOutput', (), {
                'cleaned_text': sanitized_text,
                'confidence': 0.95,
                'metadata': {},
                'target_language': 'en'  # Default to English
            })()
            
            assessment = await self._assess_sanitization_quality(original_text, sanitized_output)
            
            return {
                'safety_score': assessment.content_cleaning_score * 100,
                'compliance_score': assessment.context_preservation_score * 100,
                'consistency_score': assessment.domain_relevance_score * 100,
                'overall_score': assessment.confidence * 100
            }
        except Exception as e:
            logger.error(f"Sanitization quality assessment failed: {e}")
            return {
                'safety_score': 0.0,
                'confidence_score': 0.0,
                'consistency_score': 0.0,
                'overall_score': 0.0
            }
    
    async def assess_intent_preservation(
        self,
        original_text: str,
        processed_text: str
    ) -> Dict[str, Any]:
        """Public method to assess intent preservation."""
        try:
            intent_score = await self._assess_intent_preservation(original_text, processed_text)
            
            return {
                'meaning_retention': intent_score * 100,
                'context_preservation': intent_score * 100,
                'actionability': intent_score * 100,
                'overall_score': intent_score * 100
            }
        except Exception as e:
            logger.error(f"Intent preservation assessment failed: {e}")
            return {
                'meaning_retention': 0.0,
                'context_preservation': 0.0,
                'actionability': 0.0,
                'overall_score': 0.0
            }
    
    async def validate_workflow_quality(
        self,
        original_text: str,
        translated_text: str,
        sanitized_text: str,
        source_language: str,
        target_language: str
    ) -> Dict[str, Any]:
        """Public method to validate workflow quality (CLI interface compatibility)."""
        try:
            # Create mock objects for the complete workflow validation
            translation_result = type('TranslationResult', (), {
                'text': translated_text,
                'confidence': 0.9,
                'source_language': source_language,
                'target_language': target_language
            })()
            
            sanitized_output = type('SanitizedOutput', (), {
                'cleaned_text': sanitized_text,
                'confidence': 0.95,
                'metadata': {}
            })()
            
            # Use the complete workflow validation
            quality_metrics = await self.validate_complete_workflow(
                original_input=original_text,
                translation_result=translation_result,
                sanitized_output=sanitized_output
            )
            
            return {
                'success': True,
                'overall_score': quality_metrics.overall_score * 100,
                'translation_score': quality_metrics.translation_accuracy * 100,
                'sanitization_score': quality_metrics.sanitization_effectiveness * 100,
                'intent_score': quality_metrics.intent_preservation * 100,
                'warnings': quality_metrics.issues
            }
        except Exception as e:
            logger.error(f"Workflow quality validation failed: {e}")
            return {
                'success': False,
                'warning': f"Validation failed: {str(e)}",
                'overall_score': 0.0,
                'translation_score': 0.0,
                'sanitization_score': 0.0,
                'intent_score': 0.0,
                'warnings': [f"Validation error: {e}"]
            }
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """Get quality validation summary."""
        return {
            "quality_thresholds": {
                "min_translation_accuracy": self.min_translation_accuracy,
                "min_sanitization_effectiveness": self.min_sanitization_effectiveness,
                "min_intent_preservation": self.min_intent_preservation
            },
            "scoring_weights": self.scoring_weights,
            "insurance_keywords": {
                lang: len(keywords) for lang, keywords in self.insurance_keywords.items()
            }
        }


def get_quality_validator(config: Optional[Dict[str, Any]] = None) -> QualityValidator:
    """Get quality validator instance."""
    return QualityValidator(config) 