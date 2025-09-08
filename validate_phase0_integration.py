#!/usr/bin/env python3
"""
Phase 0 Integration Validation
Quick validation script to test the integration without external dependencies
"""

import asyncio
import sys
import os
import time
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def validate_integration():
    """Validate that the Phase 0 integration is working correctly."""
    print("🔍 Phase 0 Integration Validation")
    print("=" * 50)
    
    try:
        # Test 1: Import the chat interface
        print("1️⃣ Testing imports...")
        from agents.patient_navigator.chat_interface import PatientNavigatorChatInterface, ChatMessage
        print("   ✅ Chat interface imports successful")
        
        # Test 2: Initialize chat interface
        print("2️⃣ Testing chat interface initialization...")
        chat_interface = PatientNavigatorChatInterface()
        print("   ✅ Chat interface initialized successfully")
        
        # Test 3: Create a test message
        print("3️⃣ Testing message creation...")
        test_message = ChatMessage(
            user_id="test_user",
            content="What is my insurance deductible?",
            timestamp=time.time(),
            message_type="text",
            language="en"
        )
        print("   ✅ Test message created successfully")
        
        # Test 4: Process message (this will test the full workflow)
        print("4️⃣ Testing message processing...")
        print("   ⏳ Processing message through agentic workflow...")
        
        start_time = time.time()
        response = await chat_interface.process_message(test_message)
        processing_time = time.time() - start_time
        
        print(f"   ✅ Message processed successfully in {processing_time:.2f}s")
        print(f"   📝 Response: {response.content[:100]}...")
        print(f"   🤖 Agent Sources: {response.agent_sources}")
        print(f"   📊 Confidence: {response.confidence}")
        
        # Test 5: Validate response structure
        print("5️⃣ Testing response structure...")
        required_fields = ["content", "agent_sources", "confidence", "processing_time"]
        for field in required_fields:
            if hasattr(response, field):
                print(f"   ✅ {field}: {getattr(response, field)}")
            else:
                print(f"   ❌ Missing field: {field}")
                return False
        
        print("\n🎉 Phase 0 Integration Validation SUCCESSFUL!")
        print("   All components are working correctly.")
        print("   The agentic workflows are properly integrated.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   Please ensure all required modules are available.")
        return False
        
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        print("   Please check the integration implementation.")
        return False

async def main():
    """Run the validation."""
    success = await validate_integration()
    
    if success:
        print("\n✅ Phase 0 Integration is READY!")
        print("   You can now test the /chat endpoint with the integrated agentic workflows.")
        sys.exit(0)
    else:
        print("\n❌ Phase 0 Integration needs attention.")
        print("   Please fix the issues before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
