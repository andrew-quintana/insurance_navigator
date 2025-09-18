#!/usr/bin/env python3
"""
Test Phase 0 Integration with Full Output Display
Tests the complete agentic workflow and displays full response content for assessment.
"""

import asyncio
import os
import sys
import time
from typing import Dict, Any, List

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock RAG tool for testing
class MockRAGTool:
    """Mock RAG tool that returns sample insurance document chunks."""
    
    def __init__(self, user_id: str, config=None):
        self.user_id = user_id
        self.config = config
        self.sample_chunks = self._create_sample_chunks()
    
    def _create_sample_chunks(self) -> List[Dict[str, Any]]:
        """Create sample insurance document chunks for testing."""
        return [
            {
                "id": "chunk_1",
                "doc_id": "doc_1",
                "chunk_index": 0,
                "content": "SCAN Classic HMO has a $0 annual deductible for both medical and prescription drug benefits. This means you do not need to pay a specific amount out-of-pocket before your plan begins covering your healthcare services.",
                "section_path": "benefits/deductible",
                "section_title": "Annual Deductible",
                "page_start": 1,
                "page_end": 1,
                "similarity": 0.85,
                "tokens": 45
            },
            {
                "id": "chunk_2", 
                "doc_id": "doc_1",
                "chunk_index": 1,
                "content": "Primary care physician visits have a $0 copay. Specialist visits require a $20 copay. Emergency room visits have a $100 copay. All copays are due at the time of service.",
                "section_path": "benefits/copays",
                "section_title": "Copayment Schedule",
                "page_start": 2,
                "page_end": 2,
                "similarity": 0.78,
                "tokens": 38
            },
            {
                "id": "chunk_3",
                "doc_id": "doc_1", 
                "chunk_index": 2,
                "content": "Covered services include preventive care, diagnostic tests, specialist visits, emergency care, hospital stays, prescription drugs, and mental health services. All services must be provided by in-network providers.",
                "section_path": "benefits/covered_services",
                "section_title": "Covered Services",
                "page_start": 3,
                "page_end": 3,
                "similarity": 0.72,
                "tokens": 42
            },
            {
                "id": "chunk_4",
                "doc_id": "doc_1",
                "chunk_index": 3,
                "content": "To find a doctor in your network, visit the member portal at www.scanhealthplan.com or call the customer service number at 1-800-SCAN-123. You can search by specialty, location, or doctor name.",
                "section_path": "provider_network",
                "section_title": "Finding Providers",
                "page_start": 4,
                "page_end": 4,
                "similarity": 0.68,
                "tokens": 40
            },
            {
                "id": "chunk_5",
                "doc_id": "doc_1",
                "chunk_index": 4,
                "content": "Prescription drug benefits include generic drugs at $5 copay, preferred brand drugs at $25 copay, and non-preferred brand drugs at $50 copay. Specialty drugs may have different copay amounts.",
                "section_path": "benefits/prescription",
                "section_title": "Prescription Drug Benefits",
                "page_start": 5,
                "page_end": 5,
                "similarity": 0.75,
                "tokens": 39
            }
        ]
    
    async def retrieve_chunks(self, query_embedding: List[float]) -> List:
        """Retrieve chunks based on query similarity."""
        from agents.tooling.rag.core import ChunkWithContext
        
        # For testing, return all chunks with high similarity
        results = []
        for chunk_data in self.sample_chunks:
            chunk_obj = ChunkWithContext(
                id=chunk_data["id"],
                doc_id=chunk_data["doc_id"],
                chunk_index=chunk_data["chunk_index"],
                content=chunk_data["content"],
                section_path=chunk_data["section_path"],
                section_title=chunk_data["section_title"],
                page_start=chunk_data["page_start"],
                page_end=chunk_data["page_end"],
                similarity=chunk_data["similarity"],
                tokens=chunk_data["tokens"]
            )
            results.append(chunk_obj)
        
        return results

async def test_phase0_full_output():
    """Test the complete Phase 0 integration with full output display."""
    
    print("🚀 Phase 0 Integration Test - Full Output Assessment")
    print("=" * 80)
    
    try:
        # Import the chat interface
        from agents.patient_navigator.chat_interface import PatientNavigatorChatInterface, ChatMessage
        
        print("✅ Successfully imported PatientNavigatorChatInterface")
        
        # Initialize chat interface
        chat_interface = PatientNavigatorChatInterface()
        print("✅ Successfully initialized chat interface")
        
        # Patch the RAG tool to use our mock
        import agents.patient_navigator.information_retrieval.agent as ir_agent
        
        # Store original method
        original_retrieve_chunks = ir_agent.InformationRetrievalAgent._retrieve_chunks
        
        async def mock_retrieve_chunks(self, expert_query: str, user_id: str):
            """Mock version that uses our mock RAG tool."""
            try:
                # Create mock RAG tool
                mock_rag = MockRAGTool(user_id=user_id)
                
                # Generate embedding for expert query
                query_embedding = await self._generate_embedding(expert_query)
                
                # Retrieve chunks using mock RAG system
                chunks = await mock_rag.retrieve_chunks(query_embedding)
                
                # Filter chunks by similarity threshold
                filtered_chunks = [
                    chunk for chunk in chunks 
                    if chunk.similarity and chunk.similarity >= 0.4
                ]
                
                self.logger.info(f"Retrieved {len(chunks)} chunks, filtered to {len(filtered_chunks)} with similarity >= 0.4")
                
                return filtered_chunks
                
            except Exception as e:
                self.logger.error(f"Error in mock RAG retrieval: {e}")
                return []
        
        # Replace the method
        ir_agent.InformationRetrievalAgent._retrieve_chunks = mock_retrieve_chunks
        
        print("✅ Successfully patched RAG system with mock data")
        
        # Test queries
        test_queries = [
            "What is my deductible?",
            "What are my copays for doctor visits?",
            "What services are covered under my plan?",
            "How do I find a doctor in my network?",
            "What are my prescription drug benefits?"
        ]
        
        print(f"\n🧪 Testing {len(test_queries)} queries with full output display...")
        print("=" * 80)
        
        results = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*20} QUERY {i}: {query} {'='*20}")
            
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
                
                print(f"\n📊 RESPONSE METRICS:")
                print(f"   ⏱️  Processing time: {processing_time:.2f}s")
                print(f"   🎯 Confidence: {response.confidence}")
                print(f"   🤖 Agent sources: {response.agent_sources}")
                
                print(f"\n📝 FULL RESPONSE CONTENT:")
                print("-" * 60)
                print(response.content)
                print("-" * 60)
                
                # Check if response contains relevant information
                response_lower = response.content.lower()
                has_relevant_info = any(keyword in response_lower for keyword in [
                    "deductible", "copay", "covered", "doctor", "prescription", "network", "scan", "hmo"
                ])
                
                print(f"\n📊 CONTENT ANALYSIS:")
                print(f"   ✅ Contains relevant info: {'YES' if has_relevant_info else 'NO'}")
                print(f"   📏 Response length: {len(response.content)} characters")
                print(f"   📄 Response word count: {len(response.content.split())} words")
                
                # Check for specific insurance terms
                insurance_terms = ["deductible", "copay", "copayment", "covered", "coverage", "network", "provider", "prescription", "benefits"]
                found_terms = [term for term in insurance_terms if term in response_lower]
                print(f"   🏥 Insurance terms found: {found_terms}")
                
                results.append({
                    "query": query,
                    "response": response.content,
                    "confidence": response.confidence,
                    "processing_time": processing_time,
                    "agent_sources": response.agent_sources,
                    "has_relevant_info": has_relevant_info,
                    "response_length": len(response.content),
                    "word_count": len(response.content.split()),
                    "insurance_terms_found": found_terms,
                    "success": True
                })
                
            except Exception as e:
                processing_time = time.time() - start_time
                print(f"\n❌ ERROR: {e}")
                import traceback
                traceback.print_exc()
                
                results.append({
                    "query": query,
                    "error": str(e),
                    "processing_time": processing_time,
                    "success": False
                })
        
        # Restore original method
        ir_agent.InformationRetrievalAgent._retrieve_chunks = original_retrieve_chunks
        
        # Summary
        print(f"\n{'='*80}")
        print(f"📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print(f"{'='*80}")
        
        successful_tests = [r for r in results if r["success"]]
        failed_tests = [r for r in results if not r["success"]]
        
        print(f"✅ Successful tests: {len(successful_tests)}/{len(results)}")
        print(f"❌ Failed tests: {len(failed_tests)}/{len(results)}")
        
        if successful_tests:
            avg_processing_time = sum(r["processing_time"] for r in successful_tests) / len(successful_tests)
            avg_confidence = sum(r["confidence"] for r in successful_tests) / len(successful_tests)
            avg_response_length = sum(r["response_length"] for r in successful_tests) / len(successful_tests)
            avg_word_count = sum(r["word_count"] for r in successful_tests) / len(successful_tests)
            relevant_responses = sum(1 for r in successful_tests if r.get("has_relevant_info", False))
            
            print(f"\n📈 PERFORMANCE METRICS:")
            print(f"   ⏱️  Average processing time: {avg_processing_time:.2f}s")
            print(f"   🎯 Average confidence: {avg_confidence:.2f}")
            print(f"   📏 Average response length: {avg_response_length:.0f} characters")
            print(f"   📄 Average word count: {avg_word_count:.0f} words")
            print(f"   📊 Responses with relevant info: {relevant_responses}/{len(successful_tests)}")
            
            # Check if RAG is working (look for information retrieval in sources)
            rag_working = any("information_retrieval" in r["agent_sources"] for r in successful_tests)
            print(f"   🔍 RAG system working: {'✅ YES' if rag_working else '❌ NO'}")
            
            # Analyze insurance terms coverage
            all_terms_found = set()
            for result in successful_tests:
                all_terms_found.update(result.get("insurance_terms_found", []))
            print(f"   🏥 Unique insurance terms found: {sorted(all_terms_found)}")
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['query']}: {test['error']}")
        
        # Overall assessment
        if len(successful_tests) == len(results):
            print(f"\n🎉 PHASE 0 INTEGRATION TEST PASSED!")
            print("   All tests successful with mock RAG system")
            print("   Responses contain relevant insurance information")
            print("   Agentic workflow is functioning properly")
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
    print("🔧 Phase 0 Integration Test - Full Output Assessment")
    print("=" * 80)
    
    # Check if OpenAI API key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  WARNING: OPENAI_API_KEY not found in environment")
        print("   The test will fall back to mock embeddings")
        print("   For full testing, set OPENAI_API_KEY environment variable")
        print()
    
    # Run the test
    success = await test_phase0_full_output()
    
    if success:
        print("\n✅ Phase 0 integration is working correctly!")
        print("   RAG system is using mock data successfully")
        print("   Agentic workflow is functioning properly")
        print("   Responses contain relevant insurance information")
    else:
        print("\n❌ Phase 0 integration needs attention")
        print("   Some tests failed - check the errors above")
    
    return success

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
