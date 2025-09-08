#!/usr/bin/env python3
"""
Test Single Query with Real Insurance Document
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_single_query():
    """Test a single query to see what chunks are retrieved."""
    print("🔍 Testing Single Query with Real Insurance Document")
    print("=" * 60)
    
    try:
        # Import the chat interface
        from agents.patient_navigator.chat_interface import PatientNavigatorChatInterface, ChatMessage
        
        # Patch the RAGTool to use our real document
        import agents.patient_navigator.information_retrieval.agent as info_agent
        from process_real_insurance_doc import MockRAGTool
        original_rag_tool = info_agent.RAGTool
        info_agent.RAGTool = MockRAGTool
        
        # Initialize chat interface
        print("1️⃣ Initializing chat interface...")
        chat_interface = PatientNavigatorChatInterface()
        print("   ✅ Chat interface initialized")
        
        # Test a single query
        query = "What is my deductible?"
        print(f"\n2️⃣ Testing query: '{query}'")
        
        # Create ChatMessage
        chat_message = ChatMessage(
            user_id="test_user_hmo",
            content=query,
            timestamp=asyncio.get_event_loop().time(),
            message_type="text",
            language="en",
            metadata={"test_scenario": "single_query", "document": "scan_classic_hmo.pdf"}
        )
        
        # Process message
        start_time = asyncio.get_event_loop().time()
        response = await chat_interface.process_message(chat_message)
        processing_time = asyncio.get_event_loop().time() - start_time
        
        print(f"\n3️⃣ Response received in {processing_time:.2f}s")
        print(f"📝 Response: {response.content}")
        print(f"📊 Confidence: {response.confidence}")
        print(f"🤖 Sources: {response.agent_sources}")
        
        # Restore original RAGTool
        info_agent.RAGTool = original_rag_tool
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_single_query())
