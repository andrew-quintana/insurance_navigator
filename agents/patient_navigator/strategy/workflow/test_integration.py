#!/usr/bin/env python3
"""
Test Script for Strategy Workflow Integration

This script demonstrates the complete workflow integration with:
- Mock mode for testing without external APIs
- Real API mode for production use
- Performance monitoring and error handling
- Component validation and system status

Usage:
    python test_integration.py --mock    # Test with mock APIs
    python test_integration.py --real    # Test with real APIs (requires API keys)
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime

# Add the project root to the path for imports
sys.path.append('../../../')

from agents.patient_navigator.strategy.types import PlanConstraints, WorkflowConfig
from agents.patient_navigator.strategy.workflow.runner import StrategyWorkflowRunner, run_strategy_workflow

def create_test_plan_constraints() -> PlanConstraints:
    """Create test plan constraints for demonstration."""
    return PlanConstraints(
        copay=25,
        deductible=1000,
        network_providers=["Kaiser Permanente", "Sutter Health", "Dignity Health"],
        geographic_scope="Northern California",
        specialty_access=["Cardiology", "Orthopedics", "Neurology", "Oncology"]
    )

async def test_mock_workflow():
    """Test the workflow with mock APIs."""
    print("=== Testing Strategy Workflow with Mock APIs ===")
    
    # Create test configuration
    config = WorkflowConfig(
        use_mock=True,
        timeout_seconds=30,
        enable_logging=True
    )
    
    # Create workflow runner
    runner = StrategyWorkflowRunner(config)
    
    # Validate components
    print("\n1. Validating workflow components...")
    validation_results = await runner.validate_workflow_components()
    for component, is_valid in validation_results.items():
        status = "✅ PASS" if is_valid else "❌ FAIL"
        print(f"   {component}: {status}")
    
    # Get system status
    print("\n2. System status:")
    status = runner.get_system_status()
    for component, details in status.items():
        print(f"   {component}: {details}")
    
    # Run test workflow
    print("\n3. Running test workflow...")
    test_constraints = create_test_plan_constraints()
    
    try:
        workflow_state = await runner.run_workflow(test_constraints)
        
        print("\n4. Workflow Results:")
        print(f"   Strategies generated: {len(workflow_state.strategies) if workflow_state.strategies else 0}")
        print(f"   Strategies validated: {len(workflow_state.validation_results) if workflow_state.validation_results else 0}")
        print(f"   Storage success: {workflow_state.storage_confirmation and workflow_state.storage_confirmation.storage_status == 'success'}")
        
        if workflow_state.errors:
            print(f"   Errors: {len(workflow_state.errors)}")
            for error in workflow_state.errors:
                print(f"     - {error}")
        
        # Display generated strategies
        if workflow_state.strategies:
            print("\n5. Generated Strategies:")
            for i, strategy in enumerate(workflow_state.strategies, 1):
                print(f"   Strategy {i}: {strategy.title}")
                print(f"     Category: {strategy.category}")
                print(f"     Scores: Speed={strategy.llm_scores.speed:.2f}, Cost={strategy.llm_scores.cost:.2f}, Effort={strategy.llm_scores.effort:.2f}")
                print(f"     Approach: {strategy.approach[:100]}...")
                print()
        
        return True
        
    except Exception as error:
        print(f"❌ Workflow test failed: {error}")
        return False

async def test_real_workflow():
    """Test the workflow with real APIs (requires API keys)."""
    print("=== Testing Strategy Workflow with Real APIs ===")
    
    # Check for required environment variables
    import os
    required_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]  # OpenAI API key used for Claude completions and embeddings
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please set the following environment variables:")
        for var in missing_vars:
            print(f"   {var}")
        return False
    
    # Create production configuration
    config = WorkflowConfig(
        use_mock=False,
        timeout_seconds=30,
        enable_logging=True
    )
    
    # Create workflow runner
    runner = StrategyWorkflowRunner(config)
    
    # Validate components
    print("\n1. Validating workflow components...")
    validation_results = await runner.validate_workflow_components()
    for component, is_valid in validation_results.items():
        status = "✅ PASS" if is_valid else "❌ FAIL"
        print(f"   {component}: {status}")
    
    # Run real workflow
    print("\n2. Running real workflow...")
    test_constraints = create_test_plan_constraints()
    
    try:
        workflow_state = await runner.run_workflow(test_constraints)
        
        print("\n3. Workflow Results:")
        print(f"   Strategies generated: {len(workflow_state.strategies) if workflow_state.strategies else 0}")
        print(f"   Strategies validated: {len(workflow_state.validation_results) if workflow_state.validation_results else 0}")
        print(f"   Storage success: {workflow_state.storage_confirmation and workflow_state.storage_confirmation.storage_status == 'success'}")
        
        if workflow_state.errors:
            print(f"   Errors: {len(workflow_state.errors)}")
            for error in workflow_state.errors:
                print(f"     - {error}")
        
        return True
        
    except Exception as error:
        print(f"❌ Real workflow test failed: {error}")
        return False

async def test_convenience_function():
    """Test the convenience function for workflow execution."""
    print("=== Testing Convenience Function ===")
    
    test_constraints = create_test_plan_constraints()
    
    try:
        # Test with mock mode
        print("\n1. Testing with mock mode...")
        workflow_state = await run_strategy_workflow(
            plan_constraints=test_constraints,
            use_mock=True,
            timeout_seconds=30
        )
        
        print(f"   Mock workflow completed successfully")
        print(f"   Strategies generated: {len(workflow_state.strategies) if workflow_state.strategies else 0}")
        
        return True
        
    except Exception as error:
        print(f"❌ Convenience function test failed: {error}")
        return False

async def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test Strategy Workflow Integration")
    parser.add_argument("--mock", action="store_true", help="Test with mock APIs")
    parser.add_argument("--real", action="store_true", help="Test with real APIs")
    parser.add_argument("--convenience", action="store_true", help="Test convenience function")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    # If no specific test is selected, run mock test by default
    if not any([args.mock, args.real, args.convenience, args.all]):
        args.mock = True
    
    results = {}
    
    if args.mock or args.all:
        print("\n" + "="*60)
        results["mock"] = await test_mock_workflow()
    
    if args.real or args.all:
        print("\n" + "="*60)
        results["real"] = await test_real_workflow()
    
    if args.convenience or args.all:
        print("\n" + "="*60)
        results["convenience"] = await test_convenience_function()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.upper()}: {status}")
    
    all_passed = all(results.values())
    overall_status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
    print(f"\nOVERALL: {overall_status}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 