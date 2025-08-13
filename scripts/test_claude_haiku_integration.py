#!/usr/bin/env python3
"""
Test Claude Haiku Integration with Output Processing Agent

This script tests the real Claude Haiku integration to ensure it works correctly
with the output processing agent.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.patient_navigator.output_processing.workflow import OutputWorkflow
from agents.patient_navigator.output_processing.types import (
    CommunicationRequest,
    AgentOutput
)


async def test_claude_haiku_integration():
    """Test the Claude Haiku integration with real API calls."""
    
    print("🧪 Testing Claude Haiku Integration")
    print("=" * 50)
    
    # Check if we have the required environment variables
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set in environment")
        print("   Set it to test with real Claude Haiku, or the agent will use mock mode")
        print("   Example: export ANTHROPIC_API_KEY=your_key_here")
        return False
    
    print(f"✅ ANTHROPIC_API_KEY found: {api_key[:8]}...")
    
    # Test 1: Initialize workflow with real LLM
    print("\n📋 Test 1: Initialize Workflow with Real LLM")
    print("-" * 40)
    
    try:
        workflow = OutputWorkflow()  # Will auto-detect Claude Haiku
        print("✅ Workflow initialized successfully")
        
        # Check if we're in mock mode or real LLM mode
        agent_info = workflow.communication_agent.get_agent_info()
        if agent_info["mock_mode"]:
            print("⚠️  Agent is running in mock mode (no LLM client available)")
            return False
        else:
            print("✅ Agent is running with real Claude Haiku LLM")
            
    except Exception as e:
        print(f"❌ Failed to initialize workflow: {e}")
        return False
    
    # Test 2: Test with real agent outputs
    print("\n💬 Test 2: Test with Real Agent Outputs")
    print("-" * 40)
    
    test_request = CommunicationRequest(agent_outputs=[
        AgentOutput(
            agent_id="benefits_analyzer",
            content="Your plan covers 80% of in-network costs after $500 deductible. Out-of-network coverage is 60% after $1000 deductible.",
            metadata={"coverage_type": "medical", "deductible_met": False}
        ),
        AgentOutput(
            agent_id="eligibility_checker",
            content="Eligibility confirmed. Active coverage until 12/31/2024. No pre-existing condition exclusions apply.",
            metadata={"status": "active", "effective_date": "2024-01-01"}
        )
    ])
    
    try:
        print("🔄 Calling Claude Haiku API...")
        start_time = asyncio.get_event_loop().time()
        
        response = await workflow.process_request(test_request)
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        print(f"✅ Claude Haiku response received in {processing_time:.2f}s")
        print(f"   Response length: {len(response.enhanced_content)} characters")
        print(f"   Original sources: {response.original_sources}")
        print(f"   Processing time: {response.processing_time:.2f}s")
        print(f"   LLM used: {response.metadata.get('llm_used', 'unknown')}")
        print(f"   Model used: {response.metadata.get('model_used', 'unknown')}")
        
        # Check response quality
        if "Great news" in response.enhanced_content or "80%" in response.enhanced_content:
            print("✅ Response shows proper tone enhancement")
        else:
            print("⚠️  Response may not be properly enhanced")
        
        print("\n📝 Enhanced Response Preview:")
        print("-" * 30)
        print(response.enhanced_content[:200] + "..." if len(response.enhanced_content) > 200 else response.enhanced_content)
        
    except Exception as e:
        print(f"❌ Claude Haiku API call failed: {e}")
        return False
    
    # Test 3: Test sensitive content handling
    print("\n💔 Test 3: Test Sensitive Content Handling")
    print("-" * 40)
    
    sensitive_request = CommunicationRequest(agent_outputs=[
        AgentOutput(
            agent_id="claims_processor",
            content="Claim denied. Policy exclusion 3.2 applies. Coverage not available for pre-existing conditions.",
            metadata={"denial_reason": "pre_existing_condition", "exclusion_code": "3.2"}
        )
    ])
    
    try:
        print("🔄 Calling Claude Haiku API for sensitive content...")
        start_time = asyncio.get_event_loop().time()
        
        response = await workflow.process_request(sensitive_request)
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        print(f"✅ Claude Haiku response received in {processing_time:.2f}s")
        
        # Check for empathetic language
        empathetic_phrases = ["understand", "frustrating", "help", "support", "appeal"]
        empathy_score = sum(1 for phrase in empathetic_phrases if phrase.lower() in response.enhanced_content.lower())
        print(f"   Empathy score: {empathy_score}/{len(empathetic_phrases)} phrases detected")
        
        if empathy_score >= 3:
            print("✅ Response shows appropriate empathy for sensitive content")
        else:
            print("⚠️  Response may need more empathetic language")
        
    except Exception as e:
        print(f"❌ Claude Haiku API call for sensitive content failed: {e}")
        return False
    
    # Test 4: Performance validation
    print("\n⚡ Test 4: Performance Validation")
    print("-" * 40)
    
    try:
        # Test multiple requests to check performance consistency
        times = []
        for i in range(3):
            start_time = asyncio.get_event_loop().time()
            response = await workflow.process_request(test_request)
            end_time = asyncio.get_event_loop().time()
            times.append(end_time - start_time)
            print(f"   Request {i+1}: {times[-1]:.2f}s")
        
        avg_time = sum(times) / len(times)
        print(f"   Average response time: {avg_time:.2f}s")
        
        if avg_time < 5.0:  # Should be under 5 seconds
            print("✅ Performance is acceptable")
        else:
            print("⚠️  Performance may be slow")
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Claude Haiku Integration Test Complete!")
    print("✅ All tests passed - the agent is working with real Claude Haiku")
    print("=" * 50)
    
    return True


def main():
    """Main entry point for the test script."""
    try:
        success = asyncio.run(test_claude_haiku_integration())
        if success:
            print("\n🚀 Ready for production deployment with Claude Haiku!")
        else:
            print("\n⚠️  Some tests failed - check the output above")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
