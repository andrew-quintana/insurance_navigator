#!/usr/bin/env python3
"""
Example: Strategy Workflow Integration

This example demonstrates how to use the complete Strategy Evaluation & Validation System
workflow with both mock and real API modes.
"""

import asyncio
import logging
from datetime import datetime

from ..types import PlanConstraints, WorkflowConfig
from .runner import StrategyWorkflowRunner, run_strategy_workflow

async def example_mock_workflow():
    """Example: Run workflow with mock APIs for testing."""
    print("=== Example: Mock Workflow ===")
    
    # Create test plan constraints
    plan_constraints = PlanConstraints(
        copay=25,
        deductible=1000,
        network_providers=["Kaiser Permanente", "Sutter Health"],
        geographic_scope="Northern California",
        specialty_access=["Cardiology", "Orthopedics"]
    )
    
    # Run workflow with mock mode
    workflow_state = await run_strategy_workflow(
        plan_constraints=plan_constraints,
        use_mock=True,
        timeout_seconds=30
    )
    
    # Display results
    print(f"\nWorkflow completed with {len(workflow_state.strategies) if workflow_state.strategies else 0} strategies")
    
    if workflow_state.strategies:
        print("\nGenerated Strategies:")
        for i, strategy in enumerate(workflow_state.strategies, 1):
            print(f"  {i}. {strategy.title}")
            print(f"     Category: {strategy.category}")
            print(f"     Scores: Speed={strategy.llm_scores.speed:.2f}, Cost={strategy.llm_scores.cost:.2f}, Effort={strategy.llm_scores.effort:.2f}")
            print(f"     Approach: {strategy.approach[:80]}...")
            print()
    
    if workflow_state.errors:
        print("Errors:")
        for error in workflow_state.errors:
            print(f"  - {error}")

async def example_real_workflow():
    """Example: Run workflow with real APIs (requires API keys)."""
    print("=== Example: Real Workflow ===")
    
    # Check for required environment variables
    import os
    required_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]  # OpenAI API key used for both Claude completions and embeddings
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please set the following environment variables:")
        for var in missing_vars:
            print(f"   {var}")
        return
    
    # Create plan constraints
    plan_constraints = PlanConstraints(
        copay=30,
        deductible=1500,
        network_providers=["Blue Cross Blue Shield", "Aetna"],
        geographic_scope="Texas",
        specialty_access=["Neurology", "Oncology"]
    )
    
    # Create workflow runner with real APIs
    config = WorkflowConfig(
        use_mock=False,
        timeout_seconds=30,
        enable_logging=True
    )
    
    runner = StrategyWorkflowRunner(config)
    
    # Validate components first
    print("Validating workflow components...")
    validation_results = await runner.validate_workflow_components()
    for component, is_valid in validation_results.items():
        status = "✅ PASS" if is_valid else "❌ FAIL"
        print(f"  {component}: {status}")
    
    # Run workflow
    workflow_state = await runner.run_workflow(plan_constraints)
    
    # Display results
    print(f"\nWorkflow completed with {len(workflow_state.strategies) if workflow_state.strategies else 0} strategies")
    
    if workflow_state.strategies:
        print("\nGenerated Strategies:")
        for i, strategy in enumerate(workflow_state.strategies, 1):
            print(f"  {i}. {strategy.title}")
            print(f"     Category: {strategy.category}")
            print(f"     Scores: Speed={strategy.llm_scores.speed:.2f}, Cost={strategy.llm_scores.cost:.2f}, Effort={strategy.llm_scores.effort:.2f}")
            print(f"     Approach: {strategy.approach[:80]}...")
            print()

async def example_workflow_runner():
    """Example: Using the workflow runner directly."""
    print("=== Example: Workflow Runner ===")
    
    # Create configuration
    config = WorkflowConfig(
        use_mock=True,  # Use mock for this example
        timeout_seconds=30,
        enable_logging=True
    )
    
    # Create runner
    runner = StrategyWorkflowRunner(config)
    
    # Get system status
    print("System Status:")
    status = runner.get_system_status()
    for component, details in status.items():
        print(f"  {component}: {details}")
    
    # Create test constraints
    plan_constraints = PlanConstraints(
        copay=20,
        deductible=800,
        network_providers=["Cigna", "UnitedHealth"],
        geographic_scope="Florida",
        specialty_access=["Dermatology", "Endocrinology"]
    )
    
    # Run workflow
    workflow_state = await runner.run_workflow(plan_constraints)
    
    # Display results
    print(f"\nWorkflow completed successfully!")
    print(f"Strategies generated: {len(workflow_state.strategies) if workflow_state.strategies else 0}")
    print(f"Strategies validated: {len(workflow_state.validation_results) if workflow_state.validation_results else 0}")
    print(f"Storage success: {workflow_state.storage_confirmation and workflow_state.storage_confirmation.storage_status == 'success'}")

async def main():
    """Run all examples."""
    print("Strategy Workflow Integration Examples")
    print("=" * 50)
    
    # Example 1: Mock workflow
    await example_mock_workflow()
    
    print("\n" + "=" * 50)
    
    # Example 2: Workflow runner
    await example_workflow_runner()
    
    print("\n" + "=" * 50)
    
    # Example 3: Real workflow (commented out to avoid API calls)
    # Uncomment the following line to test with real APIs
    # await example_real_workflow()
    print("Real workflow example skipped (requires API keys)")
    print("To test with real APIs, set environment variables and uncomment the example")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run examples
    asyncio.run(main()) 