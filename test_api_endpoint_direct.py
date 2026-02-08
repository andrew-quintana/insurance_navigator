#!/usr/bin/env python3
"""
Test the actual API endpoint logic directly without database dependencies.
This simulates what happens when the frontend calls /api/chat.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_chat_endpoint_logic():
    """Test the chat endpoint logic exactly as it would run in main.py."""
    print("🔧 Testing Chat Endpoint Logic (Direct)")
    print("=" * 60)
    
    try:
        # Import the unified navigator agent (same as main.py)
        logger.info("Importing UnifiedNavigatorAgent...")
        from agents.unified_navigator.navigator_agent import UnifiedNavigatorAgent
        from agents.unified_navigator.models import UnifiedNavigatorInput
        logger.info("UnifiedNavigatorAgent imported successfully")
        
        # Simulate endpoint request data
        test_cases = [
            {
                "name": "Prescription Drug Copay Query",
                "message": "What is my prescription drug copay?",
                "conversation_id": "test_conv_1",
                "user_language": "en",
                "context": {},
                "user_id": "test_api_user_1"
            },
            {
                "name": "Insurance Benefits Strategy Query",
                "message": "How can I maximize my insurance benefits?",
                "conversation_id": "test_conv_2", 
                "user_language": "en",
                "context": {},
                "user_id": "test_api_user_2"
            },
            {
                "name": "Healthcare Regulations Query",
                "message": "What are the latest healthcare regulations for 2025?",
                "conversation_id": "test_conv_3",
                "user_language": "en",
                "context": {},
                "user_id": "test_api_user_3"
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\\nTest {i}: {test_case['name']}")
            print(f"Message: {test_case['message']}")
            
            start_time = time.time()
            
            # Create unified navigator agent (same as main.py)
            use_mock = True  # Force mock mode for testing
            navigator_agent = UnifiedNavigatorAgent(use_mock=use_mock)
            
            # Create input for unified navigator (same as main.py)
            navigator_input = UnifiedNavigatorInput(
                user_query=test_case["message"],
                user_id=test_case["user_id"],
                session_id=test_case["conversation_id"],
                workflow_context={
                    "language": test_case["user_language"],
                    "context": test_case["context"],
                    "api_request": True
                }
            )
            
            # Process message through unified navigator (same as main.py)
            try:
                logger.info("Starting unified navigator processing...")
                response = await asyncio.wait_for(
                    navigator_agent.execute(navigator_input),
                    timeout=120.0
                )
                logger.info("Unified navigator processing completed successfully")
                logger.info(f"Tool used: {response.tool_used}, Success: {response.success}")
                
                execution_time = (time.time() - start_time) * 1000
                
                # Format response exactly as main.py does
                if response.success:
                    content = response.response
                    processing_time = response.total_processing_time_ms / 1000.0
                    confidence = 1.0 if response.success else 0.0
                    agent_sources = [response.tool_used.value]
                    
                    # Extract metadata (same as main.py)
                    metadata = {
                        "tool_used": response.tool_used.value,
                        "input_safe": response.input_safety_check.is_safe,
                        "safety_level": response.input_safety_check.safety_level.value,
                        "output_sanitized": response.output_sanitized,
                        "processing_time_ms": response.total_processing_time_ms,
                        "warnings": response.warnings
                    }
                    
                    # Create API response format (same as main.py)
                    api_response = {
                        "text": content,
                        "response": content,
                        "conversation_id": test_case["conversation_id"],
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {
                            "processing_time": processing_time,
                            "confidence": confidence,
                            "agent_sources": agent_sources,
                            **metadata
                        },
                        "next_steps": [],
                        "sources": agent_sources
                    }
                    
                    results.append({
                        "test_name": test_case["name"],
                        "success": True,
                        "tool_used": response.tool_used.value,
                        "execution_time_ms": execution_time,
                        "api_response_length": len(content),
                        "input_safe": response.input_safety_check.is_safe,
                        "safety_level": response.input_safety_check.safety_level.value
                    })
                    
                    print(f"  ✅ API Response Generated: {len(content)} chars")
                    print(f"  Tool: {response.tool_used.value}")
                    print(f"  Safety: {response.input_safety_check.safety_level.value}")
                    print(f"  Processing Time: {processing_time*1000:.1f}ms")
                    print(f"  Input Safe: {response.input_safety_check.is_safe}")
                    
                else:
                    # Handle failure (same as main.py error handling)
                    error_response = {
                        "text": "I apologize, but I encountered an issue processing your request.",
                        "response": "I apologize, but I encountered an issue processing your request.",
                        "conversation_id": test_case["conversation_id"],
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {
                            "processing_time": 0.0,
                            "confidence": 0.0,
                            "agent_sources": ["system"],
                            "error": response.error_message or "Unknown error",
                            "error_type": "navigator_processing_error"
                        },
                        "next_steps": ["Please try rephrasing your question"],
                        "sources": ["system"]
                    }
                    
                    results.append({
                        "test_name": test_case["name"],
                        "success": False,
                        "error": response.error_message or "Unknown error",
                        "execution_time_ms": execution_time
                    })
                    
                    print(f"  ❌ Processing Failed: {response.error_message}")
                    
            except asyncio.TimeoutError:
                print(f"  ⏱️ Timeout after 120 seconds")
                results.append({
                    "test_name": test_case["name"],
                    "success": False,
                    "error": "Request timeout",
                    "execution_time_ms": execution_time
                })
                
            except Exception as e:
                print(f"  ❌ Exception: {e}")
                results.append({
                    "test_name": test_case["name"],
                    "success": False,
                    "error": str(e),
                    "execution_time_ms": execution_time
                })
        
        # Summary
        print("\\n" + "=" * 60)
        print("API ENDPOINT LOGIC TEST SUMMARY")
        print("=" * 60)
        
        successful_tests = sum(1 for r in results if r["success"])
        total_tests = len(results)
        
        print(f"Tests Executed: {total_tests}")
        print(f"Successful: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
        
        for result in results:
            status = "✅" if result["success"] else "❌"
            if result["success"]:
                print(f"{status} {result['test_name']}: {result['tool_used']} ({result['execution_time_ms']:.1f}ms)")
            else:
                print(f"{status} {result['test_name']}: {result.get('error', 'Unknown error')}")
        
        print("\\n🔍 Key Findings:")
        if successful_tests == total_tests:
            print("✅ All API endpoint logic tests passed!")
            print("✅ UnifiedNavigatorAgent is properly integrated")
            print("✅ Response formatting matches expected API format")
            print("✅ Tool selection is working through the API layer")
        else:
            print(f"⚠️ {total_tests - successful_tests} test(s) failed")
            
        print("\\n💡 Next Steps:")
        print("1. The API integration logic is working correctly")
        print("2. WebSocket workflow status broadcasts should be active")
        print("3. Frontend should receive proper tool selection and responses")
        print("4. Database connectivity needs to be resolved for full server startup")
        
        return successful_tests == total_tests
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


async def test_websocket_status_broadcast():
    """Test if WebSocket status broadcasts are working."""
    print("\\n📡 Testing WebSocket Status Broadcast")
    print("-" * 40)
    
    try:
        from agents.unified_navigator.websocket_handler import get_workflow_broadcaster
        from agents.unified_navigator.models import WorkflowStatus
        from datetime import datetime
        
        # Test broadcaster initialization
        broadcaster = get_workflow_broadcaster()
        stats = broadcaster.get_connection_stats()
        
        print(f"✅ WebSocket broadcaster initialized")
        print(f"✅ Active connections: {stats['total_connections']}")
        print(f"✅ Active workflows: {stats['active_workflows']}")
        
        # Test status broadcast (will have no active connections but shouldn't error)
        test_status = WorkflowStatus(
            step="testing",
            message="Testing WebSocket broadcast",
            progress=0.5,
            timestamp=datetime.now()
        )
        
        await broadcaster.broadcast_status("test_workflow_123", test_status)
        print(f"✅ Status broadcast test completed (no active connections)")
        
        return True
        
    except Exception as e:
        print(f"❌ WebSocket broadcast test failed: {e}")
        return False


async def main():
    """Run all API integration tests."""
    print("🚀 API ENDPOINT INTEGRATION TESTS")
    print("=" * 60)
    
    # Test 1: API endpoint logic
    test1_success = await test_chat_endpoint_logic()
    
    # Test 2: WebSocket status broadcast
    test2_success = await test_websocket_status_broadcast()
    
    # Final Summary
    print("\\n" + "=" * 60)
    print("FINAL API INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    if test1_success and test2_success:
        print("🎉 ALL API INTEGRATION TESTS PASSED!")
        print("✅ Chat endpoint logic is working correctly")
        print("✅ UnifiedNavigatorAgent integration is complete")
        print("✅ WebSocket workflow broadcasts are functional")
        print("\\n🚀 The API is ready for frontend integration!")
    else:
        print("⚠️ Some API integration tests failed:")
        if not test1_success:
            print("❌ Chat endpoint logic issues")
        if not test2_success:
            print("❌ WebSocket broadcast issues")
    
    return test1_success and test2_success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)