#!/usr/bin/env python3
"""
Simple test of unified navigator components without LangGraph.

This script tests the individual components to isolate any issues
before dealing with the full LangGraph workflow.
"""

import asyncio
import logging
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables using centralized loader
from config import ensure_environment_loaded
ensure_environment_loaded()

from agents.unified_navigator.guardrails.input_sanitizer import InputSanitizer
from agents.unified_navigator.guardrails.output_sanitizer import OutputSanitizer
from agents.unified_navigator.tools.web_search import WebSearchTool
from agents.unified_navigator.tools.rag_search import RAGSearchTool
from agents.unified_navigator.models import UnifiedNavigatorState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_components():
    """Test individual components without LangGraph."""
    
    print("=" * 60)
    print("SIMPLE COMPONENT TEST")
    print("=" * 60)
    
    test_query = "What does my insurance cover for doctor visits?"
    test_user_id = "test_user_123"
    
    # Create simple state dict
    state = {
        "user_query": test_query,
        "user_id": test_user_id,
        "node_timings": {},
        "processing_start_time": None
    }
    
    print(f"\nTesting with query: '{test_query}'")
    
    # Test 1: Input Sanitizer
    print("\n1. Testing Input Sanitizer...")
    try:
        sanitizer = InputSanitizer()
        
        # Test fast check
        fast_result = sanitizer._fast_safety_check(test_query)
        print(f"   Fast check: safe={fast_result.is_safe}, domain={fast_result.is_insurance_domain}")
        
        await sanitizer.cleanup()
        print("   ✓ Input sanitizer works")
    except Exception as e:
        print(f"   ❌ Input sanitizer failed: {e}")
    
    # Test 2: Web Search Tool  
    print("\n2. Testing Web Search Tool...")
    try:
        web_tool = WebSearchTool()
        result = await web_tool.search(test_query, max_results=3)
        print(f"   Results: {result.total_results} found")
        print(f"   Processing time: {result.processing_time_ms:.1f}ms")
        await web_tool.cleanup()
        print("   ✓ Web search tool works")
    except Exception as e:
        print(f"   ❌ Web search tool failed: {e}")
    
    # Test 3: RAG Search Tool
    print("\n3. Testing RAG Search Tool...")
    try:
        rag_tool = RAGSearchTool(test_user_id)
        result = await rag_tool.search(test_query)
        print(f"   Results: {result.total_chunks} chunks found")
        print(f"   Processing time: {result.processing_time_ms:.1f}ms")
        print("   ✓ RAG search tool works")
    except Exception as e:
        print(f"   ❌ RAG search tool failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Output Sanitizer
    print("\n4. Testing Output Sanitizer...")
    try:
        output_sanitizer = OutputSanitizer()
        test_response = "Your insurance policy covers doctor visits with a $30 copay."
        
        template_result = output_sanitizer._apply_template_sanitization(test_response)
        print(f"   Template check: needs_replacement={template_result['needs_replacement']}")
        
        await output_sanitizer.cleanup()
        print("   ✓ Output sanitizer works")
    except Exception as e:
        print(f"   ❌ Output sanitizer failed: {e}")
    
    print("\n" + "=" * 60)
    print("COMPONENT TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_components())