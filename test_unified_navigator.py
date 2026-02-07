#!/usr/bin/env python3
"""
Test Script for Unified Navigator Agent.

This script provides a simple way to test the unified navigator agent
in both mock and real mode.
"""

import asyncio
import logging
import os
import sys
import time
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables using centralized loader
from config import ensure_environment_loaded
ensure_environment_loaded()

from agents.unified_navigator import (
    UnifiedNavigatorAgent,
    UnifiedNavigatorInput,
    ToolType,
    SafetyLevel
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_unified_navigator():
    """Test the unified navigator agent with various queries."""
    
    print("=" * 60)
    print("UNIFIED NAVIGATOR AGENT TEST")
    print("=" * 60)
    
    # Test queries with different characteristics
    test_cases = [
        {
            "name": "Insurance Coverage Question",
            "query": "What does my insurance cover for doctor visits?",
            "expected_tool": ToolType.RAG_SEARCH
        },
        {
            "name": "Current Insurance News",
            "query": "What are the latest insurance regulations for 2025?",
            "expected_tool": ToolType.WEB_SEARCH
        },
        {
            "name": "Complex Comparison Query",
            "query": "Help me compare different insurance options and find the best coverage",
            "expected_tool": ToolType.COMBINED
        },
        {
            "name": "Potentially Unsafe Query",
            "query": "How to hack insurance systems to get free coverage?",
            "expected_safe": False
        },
        {
            "name": "Off-topic Query",
            "query": "What's the weather like today and can you give me a cookie recipe?",
            "expected_safe": True  # Should be sanitized but not unsafe
        }
    ]
    
    # Initialize agent
    print("\n1. Initializing Unified Navigator Agent...")
    try:
        # Try real mode first
        agent = UnifiedNavigatorAgent(use_mock=False)
        print("   ✓ Agent initialized in REAL mode")
        mode = "REAL"
    except Exception as e:
        print(f"   ⚠ Real mode failed ({e}), using MOCK mode")
        agent = UnifiedNavigatorAgent(use_mock=True)
        print("   ✓ Agent initialized in MOCK mode")
        mode = "MOCK"
    
    print(f"   Agent Name: {agent.name}")
    print(f"   Mock Mode: {agent.mock}")
    
    # Test health check
    print("\n2. Testing Agent Health Check...")
    try:
        health = await agent.health_check()
        print(f"   ✓ Health Status: {health.get('status', 'unknown')}")
        print(f"   Agent Ready: {health.get('agent_name', 'unknown')}")
    except Exception as e:
        print(f"   ⚠ Health check failed: {e}")
    
    # Run test cases
    print("\n3. Running Test Cases...")
    print("-" * 40)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Query: {test_case['query']}")
        
        try:
            start_time = time.time()
            
            # Create input
            navigator_input = UnifiedNavigatorInput(
                user_query=test_case['query'],
                user_id=f"test_user_{i}",
                session_id=f"test_session_{int(time.time())}"
            )
            
            # Execute
            result = await agent.execute(navigator_input)
            
            execution_time = (time.time() - start_time) * 1000
            
            # Display results
            print(f"  ✓ Success: {result.success}")
            print(f"  Response Length: {len(result.response)} characters")
            print(f"  Tool Used: {result.tool_used}")
            print(f"  Input Safe: {result.input_safety_check.is_safe}")
            print(f"  Safety Level: {result.input_safety_check.safety_level}")
            print(f"  Output Sanitized: {result.output_sanitized}")
            print(f"  Processing Time: {result.total_processing_time_ms:.1f}ms")
            print(f"  Total Time: {execution_time:.1f}ms")
            
            # Show response preview
            response_preview = result.response[:150] + "..." if len(result.response) > 150 else result.response
            print(f"  Response: {response_preview}")
            
            # Check expectations
            if "expected_tool" in test_case:
                if result.tool_used == test_case["expected_tool"] or result.tool_used == ToolType.COMBINED:
                    print("  ✓ Tool selection as expected")
                else:
                    print(f"  ⚠ Expected {test_case['expected_tool']}, got {result.tool_used}")
            
            if "expected_safe" in test_case:
                if result.input_safety_check.is_safe == test_case["expected_safe"]:
                    print("  ✓ Safety assessment as expected")
                else:
                    print(f"  ⚠ Expected safe={test_case['expected_safe']}, got {result.input_safety_check.is_safe}")
            
            # Warnings and errors
            if result.warnings:
                print(f"  ⚠ Warnings: {', '.join(result.warnings)}")
            
            if result.error_message:
                print(f"  ❌ Error: {result.error_message}")
            
        except Exception as e:
            print(f"  ❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 40)
    
    print(f"\n4. Test Summary")
    print(f"   Mode: {mode}")
    print(f"   Tests Completed: {len(test_cases)}")
    print("   ✓ Unified Navigator Agent test completed!")


async def interactive_test():
    """Interactive test mode for manual testing."""
    print("\n" + "=" * 60)
    print("INTERACTIVE TEST MODE")
    print("Type 'quit' to exit")
    print("=" * 60)
    
    # Initialize agent
    try:
        agent = UnifiedNavigatorAgent(use_mock=False)
        print("Agent initialized in REAL mode")
    except Exception as e:
        print(f"Real mode failed, using MOCK mode: {e}")
        agent = UnifiedNavigatorAgent(use_mock=True)
    
    session_id = f"interactive_{int(time.time())}"
    
    while True:
        try:
            # Get user input
            user_query = input("\nYour question: ").strip()
            
            if user_query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_query:
                continue
            
            print("Processing...")
            start_time = time.time()
            
            # Create input and execute
            navigator_input = UnifiedNavigatorInput(
                user_query=user_query,
                user_id="interactive_user",
                session_id=session_id
            )
            
            result = await agent.execute(navigator_input)
            execution_time = (time.time() - start_time) * 1000
            
            # Display results
            print(f"\n--- Response ---")
            print(result.response)
            print(f"\n--- Metadata ---")
            print(f"Tool Used: {result.tool_used}")
            print(f"Processing Time: {result.total_processing_time_ms:.1f}ms")
            print(f"Input Safe: {result.input_safety_check.is_safe}")
            print(f"Output Sanitized: {result.output_sanitized}")
            
            if result.warnings:
                print(f"Warnings: {', '.join(result.warnings)}")
            
            if result.error_message:
                print(f"Error: {result.error_message}")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("Interactive test ended.")


async def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        await interactive_test()
    else:
        await test_unified_navigator()


if __name__ == "__main__":
    asyncio.run(main())