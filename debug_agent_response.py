#!/usr/bin/env python3
"""
Debug Agent Response Generation
Test the agent processing pipeline to understand why we're getting generic responses
"""

import asyncio
import sys
import os
import time
import logging
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging to see detailed error messages
logging.basicConfig(level=logging.DEBUG)

async def debug_agent_response():
    """Debug the agent response generation process."""
    print("🔍 Debugging Agent Response Generation")
    print("=" * 50)
    
    try:
        # Import the chat interface
        from agents.patient_navigator.chat_interface import PatientNavigatorChatInterface, ChatMessage
        
        # Initialize chat interface
        print("1️⃣ Initializing chat interface...")
        chat_interface = PatientNavigatorChatInterface()
        print("   ✅ Chat interface initialized")
        
        # Create a test message
        print("2️⃣ Creating test message...")
        test_message = ChatMessage(
            user_id="test_user_12345",  # Use a valid UUID format
            content="What is my insurance deductible?",
            timestamp=time.time(),
            message_type="text",
            language="en"
        )
        print("   ✅ Test message created")
        
        # Test input processing
        print("3️⃣ Testing input processing...")
        try:
            sanitized_input = await chat_interface._process_input(test_message)
            print(f"   ✅ Input processed: {sanitized_input}")
        except Exception as e:
            print(f"   ❌ Input processing failed: {e}")
            return False
        
        # Test workflow routing
        print("4️⃣ Testing workflow routing...")
        try:
            agent_outputs = await chat_interface._route_to_workflows(sanitized_input, test_message)
            print(f"   ✅ Workflow routing completed: {len(agent_outputs)} outputs")
            for i, output in enumerate(agent_outputs):
                print(f"      Output {i+1}: {output['agent_id']} - {output['content'][:100]}...")
        except Exception as e:
            print(f"   ❌ Workflow routing failed: {e}")
            return False
        
        # Test output processing
        print("5️⃣ Testing output processing...")
        try:
            response = await chat_interface._process_outputs(agent_outputs, test_message)
            print(f"   ✅ Output processed: {response.content[:100]}...")
            print(f"   📊 Confidence: {response.confidence}")
            print(f"   🤖 Sources: {response.agent_sources}")
        except Exception as e:
            print(f"   ❌ Output processing failed: {e}")
            return False
        
        # Test complete message processing
        print("6️⃣ Testing complete message processing...")
        try:
            start_time = time.time()
            response = await chat_interface.process_message(test_message)
            processing_time = time.time() - start_time
            
            print(f"   ✅ Complete processing successful in {processing_time:.2f}s")
            print(f"   📝 Response: {response.content}")
            print(f"   📊 Confidence: {response.confidence}")
            print(f"   🤖 Sources: {response.agent_sources}")
            
            # Check if response is generic error message
            if "I'm sorry, but it looks like there was an issue processing your request" in response.content:
                print("   ⚠️  WARNING: Response is generic error message")
                return False
            else:
                print("   ✅ Response appears to be meaningful content")
                return True
                
        except Exception as e:
            print(f"   ❌ Complete processing failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        return False

async def test_with_mock_agent():
    """Test with mock agent to see if we get better responses."""
    print("\n🧪 Testing with Mock Agent")
    print("=" * 30)
    
    try:
        from agents.patient_navigator.chat_interface import PatientNavigatorChatInterface, ChatMessage
        
        # Initialize with mock agent
        print("1️⃣ Initializing with mock agent...")
        chat_interface = PatientNavigatorChatInterface(config={"use_mock": True})
        print("   ✅ Mock chat interface initialized")
        
        # Create test message
        test_message = ChatMessage(
            user_id="test_user_12345",
            content="What is my insurance deductible?",
            timestamp=time.time(),
            message_type="text",
            language="en"
        )
        
        # Process message
        print("2️⃣ Processing message with mock agent...")
        start_time = time.time()
        response = await chat_interface.process_message(test_message)
        processing_time = time.time() - start_time
        
        print(f"   ✅ Mock processing completed in {processing_time:.2f}s")
        print(f"   📝 Response: {response.content}")
        print(f"   📊 Confidence: {response.confidence}")
        print(f"   🤖 Sources: {response.agent_sources}")
        
        return True
        
    except Exception as e:
        print(f"❌ Mock test failed: {e}")
        return False

async def main():
    """Run the debug process."""
    print("🚀 Starting Agent Response Debug")
    print()
    
    # Test 1: Debug real agent
    success1 = await debug_agent_response()
    
    # Test 2: Test with mock agent
    success2 = await test_with_mock_agent()
    
    print("\n" + "=" * 50)
    print("📊 DEBUG RESULTS")
    print("=" * 50)
    print(f"Real Agent Test: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Mock Agent Test: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if not success1 and not success2:
        print("\n❌ Both tests failed - there's a fundamental issue")
    elif not success1 and success2:
        print("\n⚠️  Real agent has issues, but mock agent works")
        print("   This suggests configuration or dependency issues")
    elif success1 and not success2:
        print("\n⚠️  Mock agent has issues, but real agent works")
        print("   This is unexpected - investigate mock implementation")
    else:
        print("\n✅ Both tests passed - agent processing is working")
    
    return success1 or success2

if __name__ == "__main__":
    asyncio.run(main())
