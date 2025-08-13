#!/usr/bin/env python3
"""Test script for Phase 3 Input Processing Workflow (No API Keys Required)."""

import asyncio
import logging
from agents.patient_navigator.input_processing.quality_validator import QualityValidator
from agents.patient_navigator.input_processing.performance_monitor import get_performance_monitor
from agents.patient_navigator.input_processing.circuit_breaker import CircuitBreaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_phase3_components():
    """Test the Phase 3 components without external API calls."""
    print("🧪 Testing Phase 3 Components (No API Keys Required)")
    print("=" * 60)
    
    # Test 1: Quality Validator
    print("\n📝 Test 1: Quality Validator")
    print("-" * 40)
    
    validator = QualityValidator()
    
    # Test quality validation
    original_text = "I need help with my health insurance claim. I had surgery last month."
    translated_text = "Necesito ayuda con mi reclamo de seguro de salud. Tuve cirugía el mes pasado."
    sanitized_text = "Necesito ayuda con mi reclamo de seguro de salud. Tuve cirugía el mes pasado."
    
    # Create mock objects
    translation_result = type('TranslationResult', (), {
        'text': translated_text,
        'confidence': 0.9,
        'source_language': 'en',
        'target_language': 'es'
    })()
    
    sanitized_output = type('SanitizedOutput', (), {
        'cleaned_text': sanitized_text,
        'confidence': 0.95,
        'metadata': {}
    })()
    
    quality_result = await validator.validate_complete_workflow(
        original_input=original_text,
        translation_result=translation_result,
        sanitized_output=sanitized_output
    )
    
    print(f"✅ Quality validation successful")
    print(f"   Overall score: {quality_result.overall_score * 100:.1f}/100")
    print(f"   Quality level: {quality_result.quality_level.value}")
    print(f"   Issues found: {len(quality_result.issues)}")
    print(f"   Recommendations: {len(quality_result.recommendations)}")
    
    # Test 2: Performance Monitor
    print("\n📊 Test 2: Performance Monitor")
    print("-" * 40)
    
    monitor = get_performance_monitor()
    
    # Simulate some operations using the context manager
    async with monitor.track_operation("test_operation", test_data="sample") as metric:
        metric.success = True
        await asyncio.sleep(0.1)  # Simulate work
    
    async with monitor.track_operation("test_operation", test_data="sample2") as metric:
        metric.success = True
        await asyncio.sleep(0.2)  # Simulate work
    
    async with monitor.track_operation("test_operation", test_data="sample3") as metric:
        metric.success = False
        metric.error_message = "Test error"
        await asyncio.sleep(0.15)  # Simulate work
    
    stats = monitor.get_operation_stats("test_operation")
    if stats:
        print(f"✅ Performance monitoring working")
        print(f"   Total calls: {stats.total_calls}")
        print(f"   Success rate: {stats.success_rate:.1%}")
        print(f"   Average duration: {stats.avg_duration:.3f}s")
    else:
        print("❌ No performance stats available")
    
    # Test 3: Circuit Breaker
    print("\n🔌 Test 3: Circuit Breaker")
    print("-" * 40)
    
    circuit_breaker = CircuitBreaker("test_service")
    
    # Test circuit breaker states
    print(f"✅ Circuit breaker initialized")
    print(f"   Initial state: {circuit_breaker.state}")
    print(f"   Failure threshold: {circuit_breaker.config.failure_threshold}")
    print(f"   Recovery timeout: {circuit_breaker.config.recovery_timeout}s")
    
    # Test 4: Individual Quality Assessments
    print("\n🔍 Test 4: Individual Quality Assessments")
    print("-" * 40)
    
    # Translation quality
    trans_quality = await validator.assess_translation_quality(
        original_text, translated_text, "en", "es"
    )
    print(f"✅ Translation assessment: {trans_quality['overall_score']:.1f}/100")
    
    # Sanitization quality
    sanit_quality = await validator.assess_sanitization_quality(
        original_text, sanitized_text
    )
    print(f"✅ Sanitization assessment: {sanit_quality['overall_score']:.1f}/100")
    
    # Intent preservation
    intent_quality = await validator.assess_intent_preservation(
        original_text, sanitized_text
    )
    print(f"✅ Intent preservation: {intent_quality['overall_score']:.1f}/100")
    
    # Test 5: Quality Summary
    print("\n📋 Test 5: Quality Summary")
    print("-" * 40)
    
    summary = validator.get_quality_summary()
    print(f"✅ Quality summary generated")
    print(f"   Quality thresholds: {summary['quality_thresholds']}")
    print(f"   Scoring weights: {summary['scoring_weights']}")
    print(f"   Insurance keywords: {summary['insurance_keywords']}")
    
    print("\n🎉 Phase 3 Component Testing Complete!")
    print("\n📊 Final Summary:")
    print(f"   Overall Quality Score: {quality_result.overall_score * 100:.1f}/100")
    print(f"   Quality Level: {quality_result.quality_level.value}")
    print(f"   Performance Operations: {stats.total_calls if stats else 0}")
    print(f"   Circuit Breaker State: {circuit_breaker.state}")


if __name__ == "__main__":
    asyncio.run(test_phase3_components()) 