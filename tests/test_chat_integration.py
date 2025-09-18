#!/usr/bin/env python3
"""
Test script to verify chat endpoint integration with agent workflows.
"""

import asyncio
import aiohttp
import json
import time
import os
from datetime import datetime

# Set minimal environment variables for testing
os.environ['SUPABASE_URL'] = 'http://localhost:54321'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test_key'
os.environ['LLAMAPARSE_API_KEY'] = 'test_key'
os.environ['OPENAI_API_KEY'] = 'test_key'
os.environ['ANTHROPIC_API_KEY'] = 'test_key'

async def test_chat_endpoint_directly():
    """Test the chat endpoint by calling it directly without HTTP."""
    try:
        # Import the chat endpoint function directly
        from main import chat_with_agent
        from fastapi import Request
        from unittest.mock import Mock
        
        # Create a mock request
        mock_request = Mock()
        mock_request.json = lambda: {
            "message": "Hello, I need help with health insurance",
            "conversation_id": f"test_{int(time.time())}"
        }
        
        # Create a mock current user
        current_user = {
            "id": "test_user_123",
            "email": "test@example.com",
            "name": "Test User"
        }
        
        print("🚀 Testing chat endpoint with agent integration...")
        print(f"Message: Hello, I need help with health insurance")
        
        # Call the chat endpoint directly
        response = await chat_with_agent(mock_request, current_user)
        
        print("✅ Chat endpoint response:")
        print(json.dumps(response, indent=2))
        
        # Check if the response has agent workflow indicators
        if 'sources' in response and 'confidence' in response:
            print("✅ Chat endpoint is properly connected to agent workflows!")
            print(f"   Sources: {response['sources']}")
            print(f"   Confidence: {response['confidence']}")
            print(f"   Processing Time: {response.get('processing_time', 'N/A')}")
        else:
            print("❌ Chat endpoint may not be fully connected to agent workflows")
            
        return response
        
    except Exception as e:
        print(f"❌ Error testing chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_agent_workflow_directly():
    """Test the agent workflow directly without the HTTP layer."""
    try:
        from agents.patient_navigator.chat_interface import PatientNavigatorChatInterface, ChatMessage
        
        print("\n🔧 Testing agent workflow directly...")
        
        # Create a test message
        message = ChatMessage(
            user_id="test_user_123",
            content="Hello, I need help with health insurance",
            timestamp=time.time(),
            message_type="text",
            language="en",
            metadata={
                "conversation_id": f"test_{int(time.time())}",
                "user_email": "test@example.com",
                "user_name": "Test User"
            }
        )
        
        # Initialize chat interface
        chat_interface = PatientNavigatorChatInterface()
        
        # Process message
        response = await chat_interface.process_message(message)
        
        print("✅ Agent workflow response:")
        print(f"   Content: {response.content[:200]}...")
        print(f"   Sources: {response.agent_sources}")
        print(f"   Confidence: {response.confidence}")
        print(f"   Processing Time: {response.processing_time:.2f}s")
        
        return response
        
    except Exception as e:
        print(f"❌ Error testing agent workflow: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main test function."""
    print("=" * 60)
    print("CHAT ENDPOINT AGENT INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Agent workflow directly
    print("\n1. Testing Agent Workflow Directly")
    print("-" * 40)
    agent_response = await test_agent_workflow_directly()
    
    # Test 2: Chat endpoint with agent integration
    print("\n2. Testing Chat Endpoint with Agent Integration")
    print("-" * 40)
    chat_response = await test_chat_endpoint_directly()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if agent_response:
        print("✅ Agent workflow is working correctly")
    else:
        print("❌ Agent workflow has issues")
    
    if chat_response and 'sources' in chat_response:
        print("✅ Chat endpoint is connected to agent workflows")
    else:
        print("❌ Chat endpoint is not properly connected to agent workflows")
    
    if agent_response and chat_response and 'sources' in chat_response:
        print("\n🎉 SUCCESS: Chat endpoint is properly integrated with agent workflows!")
        print("   Phase 1 testing can now proceed with meaningful results.")
    else:
        print("\n⚠️  ISSUES: Chat endpoint integration needs attention before Phase 1 testing.")

if __name__ == "__main__":
    asyncio.run(main())
