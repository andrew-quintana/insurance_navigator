#!/usr/bin/env python3
"""Test script for Phase 3 Input Processing Workflow with Quality Validation."""

import asyncio
import logging
from agents.patient_navigator.input_processing.cli_interface import EnhancedCLIInterface

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_phase3_workflow():
    """Test the complete Phase 3 workflow."""
    print("🧪 Testing Phase 3 Input Processing Workflow")
    print("=" * 60)
    
    # Initialize the enhanced CLI interface
    cli = EnhancedCLIInterface()
    
    # Test case 1: Basic text translation with quality validation
    print("\n📝 Test Case 1: Basic Text Translation")
    print("-" * 40)
    
    test_text = "I need help with my health insurance claim. I had surgery last month."
    
    result = await cli.run_complete_workflow(
        input_text=test_text,
        source_language="en",
        target_language="es",
        show_performance=True,
        export_metrics=False
    )
    
    if result["success"]:
        print(f"\n✅ Test Case 1 PASSED")
        print(f"   Original text: {result['input']['original_text']}")
        print(f"   Translated text: {result['translation']['translated_text']}")
        print(f"   Sanitized text: {result['sanitization']['sanitized_text']}")
        print(f"   Quality score: {result['quality_validation']['overall_score']:.1f}/100")
        print(f"   Total time: {result['workflow_time']:.2f}s")
    else:
        print(f"\n❌ Test Case 1 FAILED: {result.get('error', 'Unknown error')}")
    
    # Test case 2: System status
    print("\n🔍 Test Case 2: System Status")
    print("-" * 40)
    
    await cli.show_system_status()
    
    # Test case 3: Performance test
    print("\n⚡ Test Case 3: Performance Test")
    print("-" * 40)
    
    await cli.run_performance_test(
        test_text="This is a performance test for the input processing workflow.",
        iterations=3
    )
    
    print("\n🎉 Phase 3 Testing Complete!")


if __name__ == "__main__":
    asyncio.run(test_phase3_workflow()) 