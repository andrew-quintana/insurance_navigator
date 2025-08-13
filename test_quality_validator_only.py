#!/usr/bin/env python3
"""Test script for Quality Validator only (no API keys required)."""

import asyncio
import logging
from agents.patient_navigator.input_processing.quality_validator import QualityValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_quality_validator():
    """Test the quality validator functionality."""
    print("🧪 Testing Quality Validator (No API Keys Required)")
    print("=" * 60)
    
    # Initialize the quality validator
    validator = QualityValidator()
    
    # Test case 1: Basic quality validation
    print("\n📝 Test Case 1: Basic Quality Validation")
    print("-" * 40)
    
    original_text = "I need help with my health insurance claim. I had surgery last month."
    translated_text = "Necesito ayuda con mi reclamo de seguro de salud. Tuve cirugía el mes pasado."
    sanitized_text = "Necesito ayuda con mi reclamo de seguro de salud. Tuve cirugía el mes pasado."
    source_language = "en"
    target_language = "es"
    
    result = await validator.validate_complete_workflow(
        original_input=original_text,
        translation_result=type('TranslationResult', (), {
            'text': translated_text,
            'confidence': 0.9,
            'source_language': source_language,
            'target_language': target_language
        })(),
        sanitized_output=type('SanitizedOutput', (), {
            'cleaned_text': sanitized_text,
            'confidence': 0.95,
            'metadata': {}
        })()
    )
    
    print(f"✅ Quality validation successful")
    print(f"   Overall score: {result.overall_score * 100:.1f}/100")
    print(f"   Translation quality: {result.translation_accuracy * 100:.1f}/100")
    print(f"   Sanitization quality: {result.sanitization_effectiveness * 100:.1f}/100")
    print(f"   Intent preservation: {result.intent_preservation * 100:.1f}/100")
    
    if result.issues:
        print(f"   Issues: {', '.join(result.issues)}")
    
    # Test case 2: Poor quality example
    print("\n📝 Test Case 2: Poor Quality Example")
    print("-" * 40)
    
    poor_translation = "I need help with my health insurance claim. I had surgery last month."  # Same as original
    poor_sanitization = "I need help with my health insurance claim. I had surgery last month."  # Same as original
    
    result2 = await validator.validate_complete_workflow(
        original_input=original_text,
        translation_result=type('TranslationResult', (), {
            'text': poor_translation,
            'confidence': 0.5,
            'source_language': source_language,
            'target_language': target_language
        })(),
        sanitized_output=type('SanitizedOutput', (), {
            'cleaned_text': poor_sanitization,
            'confidence': 0.6,
            'metadata': {}
        })()
    )
    
    print(f"✅ Quality validation successful")
    print(f"   Overall score: {result2.overall_score * 100:.1f}/100")
    print(f"   Translation quality: {result2.translation_accuracy * 100:.1f}/100")
    print(f"   Sanitization quality: {result2.sanitization_effectiveness * 100:.1f}/100")
    print(f"   Intent preservation: {result2.intent_preservation * 100:.1f}/100")
    
    if result2.issues:
        print(f"   Issues: {', '.join(result2.issues)}")
    
    # Test case 3: Quality assessment only
    print("\n📝 Test Case 3: Quality Assessment Only")
    print("-" * 40)
    
    assessment = await validator.assess_translation_quality(
        original_text=original_text,
        translated_text=translated_text,
        source_language="en",
        target_language="es"
    )
    
    print(f"✅ Translation assessment successful")
    print(f"   Accuracy score: {assessment['accuracy_score']:.1f}/100")
    print(f"   Fluency score: {assessment['fluency_score']:.1f}/100")
    print(f"   Domain score: {assessment['domain_score']:.1f}/100")
    print(f"   Overall score: {assessment['overall_score']:.1f}/100")
    
    # Test case 4: Sanitization assessment
    print("\n📝 Test Case 4: Sanitization Assessment")
    print("-" * 40)
    
    sanitization_assessment = await validator.assess_sanitization_quality(
        original_text=original_text,
        sanitized_text=sanitized_text
    )
    
    print(f"✅ Sanitization assessment successful")
    print(f"   Safety score: {sanitization_assessment['safety_score']:.1f}/100")
    print(f"   Compliance score: {sanitization_assessment['compliance_score']:.1f}/100")
    print(f"   Consistency score: {sanitization_assessment['consistency_score']:.1f}/100")
    print(f"   Overall score: {sanitization_assessment['overall_score']:.1f}/100")
    
    # Test case 5: Intent preservation assessment
    print("\n📝 Test Case 5: Intent Preservation Assessment")
    print("-" * 40)
    
    intent_assessment = await validator.assess_intent_preservation(
        original_text=original_text,
        processed_text=sanitized_text
    )
    
    print(f"✅ Intent preservation assessment successful")
    print(f"   Meaning retention: {intent_assessment['meaning_retention']:.1f}/100")
    print(f"   Context preservation: {intent_assessment['context_preservation']:.1f}/100")
    print(f"   Actionability: {intent_assessment['actionability']:.1f}/100")
    print(f"   Overall score: {intent_assessment['overall_score']:.1f}/100")
    
    print("\n🎉 Quality Validator Testing Complete!")
    print("\n📊 Summary:")
    print(f"   Test Case 1 (Good Quality): {result.overall_score * 100:.1f}/100")
    print(f"   Test Case 2 (Poor Quality): {result2.overall_score * 100:.1f}/100")
    print(f"   Translation Assessment: {assessment['overall_score']:.1f}/100")
    print(f"   Sanitization Assessment: {sanitization_assessment['overall_score']:.1f}/100")
    print(f"   Intent Assessment: {intent_assessment['overall_score']:.1f}/100")


if __name__ == "__main__":
    asyncio.run(test_quality_validator()) 