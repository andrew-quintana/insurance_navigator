#!/usr/bin/env python3
"""
Minimal test to understand LangGraph workflow issues.
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ensure_environment_loaded
ensure_environment_loaded()

from langgraph.graph import StateGraph, END
from typing import TypedDict


class SimpleState(TypedDict):
    message: str
    step: int


def step1(state: SimpleState) -> SimpleState:
    print(f"Step 1: {state['message']}")
    state["step"] = 1
    return state


def step2(state: SimpleState) -> SimpleState:
    print(f"Step 2: {state['message']}")
    state["step"] = 2
    return state


async def test_minimal_workflow():
    """Test minimal LangGraph workflow."""
    
    print("Testing minimal LangGraph workflow...")
    
    # Create workflow
    workflow = StateGraph(SimpleState)
    
    # Add nodes
    workflow.add_node("step1", step1)
    workflow.add_node("step2", step2)
    
    # Set flow
    workflow.set_entry_point("step1")
    workflow.add_edge("step1", "step2")
    workflow.set_finish_point("step2")
    
    # Compile
    graph = workflow.compile(debug=False)
    
    # Test execution
    initial_state = {"message": "Hello World", "step": 0}
    
    print(f"Initial state: {initial_state}")
    
    try:
        # Try synchronous invoke instead
        final_state = graph.invoke(initial_state)
        print(f"Final state: {final_state}")
        print("✓ Minimal workflow succeeded!")
    except Exception as e:
        print(f"❌ Sync workflow failed: {e}")
        
    try:
        # Try async stream approach
        print("Trying async stream...")
        final_state = None
        async for chunk in graph.astream(initial_state):
            print(f"Chunk: {chunk}")
            final_state = chunk
        print(f"Final state via stream: {final_state}")
        print("✓ Stream workflow succeeded!")
    except Exception as e:
        print(f"❌ Stream workflow failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_minimal_workflow())