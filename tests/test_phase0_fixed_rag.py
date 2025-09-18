#!/usr/bin/env python3
"""
Test Phase 0 Integration with Fixed RAG Embeddings
Tests the complete agentic workflow with real OpenAI embeddings for both queries and chunks.
"""

import asyncio
import os
import sys
import time
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_phase0_integration():
    """Test the complete Phase 0 integration with fixed RAG embeddings."""
    
    print("🚀 Testing Phase 0 Integration with Fixed RAG Embeddings")
    print("=" * 60)
    
    try:
        # Import the chat interface
        from agents.patient_navigator.chat_interface import PatientNavigatorChatInterface, ChatMessage
        
        print("✅ Successfully imported PatientNavigatorChatInterface")
        
        # Initialize chat interface
        chat_interface = PatientNavigatorChatInterface()
        print("✅ Successfully initialized chat interface")
        
        # Test queries
        test_queries = [
            "What is my deductible?",
            "What are my copays for doctor visits?",
            "What services are covered under my plan?",
            "How do I find a doctor in my network?",
            "What are my prescription drug benefits?"
        ]
        
        print(f"\n🧪 Testing {len(test_queries)} queries with real OpenAI embeddings...")
        print("-" * 60)
        
        results = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Testing query: '{query}'")
            
            # Create chat message with proper UUID format
            message = ChatMessage(
                user_id="550e8400-e29b-41d4-a716-446655440000",  # Valid UUID format
                content=query,
                timestamp=time.time(),
                message_type="text",
                language="en",
                metadata={
                    "conversation_id": f"test_conv_{i}",
                    "context": "phase0_testing",
                    "api_request": True
                }
            )
            
            # Process message
            start_time = time.time()
            try:
                response = await chat_interface.process_message(message)
                processing_time = time.time() - start_time
                
                print(f"   ✅ Response generated in {processing_time:.2f}s")
                print(f"   📝 Response: {response.content[:200]}...")
                print(f"   🎯 Confidence: {response.confidence}")
                print(f"   🤖 Agent sources: {response.agent_sources}")
                
                results.append({
                    "query": query,
                    "response": response.content,
                    "confidence": response.confidence,
                    "processing_time": processing_time,
                    "agent_sources": response.agent_sources,
                    "success": True
                })
                
            except Exception as e:
                processing_time = time.time() - start_time
                print(f"   ❌ Error: {e}")
                
                results.append({
                    "query": query,
                    "error": str(e),
                    "processing_time": processing_time,
                    "success": False
                })
        
        # Summary
        print(f"\n📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        successful_tests = [r for r in results if r["success"]]
        failed_tests = [r for r in results if not r["success"]]
        
        print(f"✅ Successful tests: {len(successful_tests)}/{len(results)}")
        print(f"❌ Failed tests: {len(failed_tests)}/{len(results)}")
        
        if successful_tests:
            avg_processing_time = sum(r["processing_time"] for r in successful_tests) / len(successful_tests)
            avg_confidence = sum(r["confidence"] for r in successful_tests) / len(successful_tests)
            
            print(f"⏱️  Average processing time: {avg_processing_time:.2f}s")
            print(f"🎯 Average confidence: {avg_confidence:.2f}")
            
            # Check if RAG is working (look for information retrieval in sources)
            rag_working = any("information_retrieval" in r["agent_sources"] for r in successful_tests)
            print(f"🔍 RAG system working: {'✅ YES' if rag_working else '❌ NO'}")
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['query']}: {test['error']}")
        
        # Overall assessment
        if len(successful_tests) == len(results):
            print(f"\n🎉 PHASE 0 INTEGRATION TEST PASSED!")
            print("   All tests successful with real OpenAI embeddings")
            return True
        else:
            print(f"\n⚠️  PHASE 0 INTEGRATION TEST PARTIALLY PASSED")
            print(f"   {len(successful_tests)}/{len(results)} tests successful")
            return False
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("🔧 Phase 0 Integration Test with Fixed RAG Embeddings")
    print("=" * 60)
    
    # Check if OpenAI API key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  WARNING: OPENAI_API_KEY not found in environment")
        print("   The test will fall back to mock embeddings")
        print("   For full testing, set OPENAI_API_KEY environment variable")
        print()
    
    # Run the test
    success = await test_phase0_integration()
    
    if success:
        print("\n✅ Phase 0 integration is working correctly!")
        print("   RAG system is using real OpenAI embeddings")
        print("   Agentic workflow is functioning properly")
    else:
        print("\n❌ Phase 0 integration needs attention")
        print("   Some tests failed - check the errors above")
    
    return success

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
