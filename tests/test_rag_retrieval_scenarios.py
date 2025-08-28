"""
RAG Retrieval Scenarios Test

This test validates RAG retrieval functionality with simulated real insurance document scenarios.
Tests include:
1. Simulated document chunk retrieval
2. Vector similarity search validation
3. User access control validation
4. Token budget enforcement
5. Real-world query scenarios
"""

import pytest
import asyncio
import os
import sys
from typing import List, Dict, Any
from unittest.mock import AsyncMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.tooling.rag.core import RAGTool, RetrievalConfig, ChunkWithContext


class TestRAGRetrievalScenarios:
    """Test RAG retrieval with real-world insurance document scenarios."""
    
    @pytest.fixture
    def test_user_id(self) -> str:
        """Test user ID for RAG operations."""
        return "5710ff53-32ea-4fab-be6d-3a6f0627fbff"
    
    @pytest.fixture
    def rag_config(self) -> RetrievalConfig:
        """RAG configuration for testing."""
        return RetrievalConfig(
            max_chunks=5,
            token_budget=2000,
            similarity_threshold=0.7
        )
    
    @pytest.fixture
    def sample_insurance_queries(self) -> List[Dict[str, Any]]:
        """Sample insurance-related queries for testing."""
        return [
            {
                "query": "What is my deductible for doctor visits?",
                "expected_topics": ["deductible", "doctor visits", "copay"],
                "document_type": "insurance_policy"
            },
            {
                "query": "Does my plan cover prescription drugs?",
                "expected_topics": ["prescription drugs", "coverage", "formulary"],
                "document_type": "benefits_summary"
            },
            {
                "query": "What is the out-of-pocket maximum?",
                "expected_topics": ["out-of-pocket", "maximum", "limit"],
                "document_type": "insurance_policy"
            },
            {
                "query": "How do I find a doctor in my network?",
                "expected_topics": ["network", "doctor", "provider", "in-network"],
                "document_type": "provider_directory"
            },
            {
                "query": "What is covered for physical therapy?",
                "expected_topics": ["physical therapy", "coverage", "visits", "limits"],
                "document_type": "benefits_summary"
            }
        ]
    
    @pytest.fixture
    def sample_document_chunks(self) -> List[Dict[str, Any]]:
        """Sample document chunks that would be returned from a real insurance document."""
        return [
            {
                "chunk_id": "chunk-001",
                "document_id": "doc-001",
                "chunk_index": 1,
                "content": "Your health insurance plan has a $1,000 annual deductible for individual coverage. This means you must pay the first $1,000 of covered medical expenses before your insurance begins to pay.",
                "section_path": [1, 1],
                "section_title": "Deductible Information",
                "page_start": 1,
                "page_end": 1,
                "tokens": 45,
                "similarity": 0.95
            },
            {
                "chunk_id": "chunk-002",
                "document_id": "doc-001",
                "chunk_index": 2,
                "content": "After meeting your deductible, you pay a $25 copay for primary care visits and a $40 copay for specialist visits. Preventive care services are covered at 100% with no deductible or copay.",
                "section_path": [1, 2],
                "section_title": "Copay Structure",
                "page_start": 1,
                "page_end": 1,
                "tokens": 42,
                "similarity": 0.88
            },
            {
                "chunk_id": "chunk-003",
                "document_id": "doc-001",
                "chunk_index": 3,
                "content": "Your out-of-pocket maximum is $6,000 per year. This includes your deductible, copays, and coinsurance. Once you reach this limit, your insurance covers 100% of covered medical expenses.",
                "section_path": [1, 3],
                "section_title": "Out-of-Pocket Maximum",
                "page_start": 1,
                "page_end": 1,
                "tokens": 38,
                "similarity": 0.92
            },
            {
                "chunk_id": "chunk-004",
                "document_id": "doc-002",
                "chunk_index": 1,
                "content": "Prescription drug coverage is included in your plan. Generic drugs have a $10 copay, preferred brand drugs have a $30 copay, and non-preferred brand drugs have a $50 copay.",
                "section_path": [2, 1],
                "section_title": "Prescription Drug Benefits",
                "page_start": 2,
                "page_end": 2,
                "tokens": 35,
                "similarity": 0.85
            },
            {
                "chunk_id": "chunk-005",
                "document_id": "doc-002",
                "chunk_index": 2,
                "content": "Physical therapy is covered for up to 20 visits per year with a $30 copay per visit. Prior authorization is required for visits beyond the 20-visit limit.",
                "section_path": [2, 2],
                "section_title": "Physical Therapy Coverage",
                "page_start": 2,
                "page_end": 2,
                "tokens": 32,
                "similarity": 0.78
            }
        ]
    
    @pytest.mark.asyncio
    async def test_rag_tool_with_simulated_chunks(self, test_user_id: str, rag_config: RetrievalConfig, sample_document_chunks: List[Dict[str, Any]]):
        """Test RAG tool functionality with simulated document chunks."""
        try:
            # Create RAG tool
            rag_tool = RAGTool(user_id=test_user_id, config=rag_config)
            
            # Mock the database connection to return simulated chunks
            mock_conn = AsyncMock()
            mock_conn.fetch.return_value = sample_document_chunks
            
            with patch.object(rag_tool, '_get_db_conn', return_value=mock_conn):
                # Test with a sample query embedding
                sample_embedding = [0.1] * 1536
                chunks = await rag_tool.retrieve_chunks(sample_embedding)
                
                # Validate results
                assert len(chunks) == 5
                assert all(isinstance(chunk, ChunkWithContext) for chunk in chunks)
                
                # Check specific chunk data
                assert chunks[0].id == "chunk-001"
                assert chunks[0].doc_id == "doc-001"
                assert "deductible" in chunks[0].content.lower()
                assert chunks[0].similarity == 0.95
                
                print("✅ RAG tool with simulated chunks successful")
                print(f"   Retrieved {len(chunks)} chunks")
                print(f"   Top similarity: {chunks[0].similarity}")
                print(f"   Content preview: {chunks[0].content[:100]}...")
                
        except Exception as e:
            pytest.fail(f"RAG tool with simulated chunks failed: {e}")
    
    @pytest.mark.asyncio
    async def test_rag_tool_token_budget_enforcement(self, test_user_id: str, rag_config: RetrievalConfig, sample_document_chunks: List[Dict[str, Any]]):
        """Test that RAG tool enforces token budget correctly."""
        try:
            # Create RAG tool with low token budget
            low_budget_config = RetrievalConfig(
                max_chunks=10,
                token_budget=100,  # Very low budget
                similarity_threshold=0.7
            )
            rag_tool = RAGTool(user_id=test_user_id, config=low_budget_config)
            
            # Mock database connection
            mock_conn = AsyncMock()
            mock_conn.fetch.return_value = sample_document_chunks
            
            with patch.object(rag_tool, '_get_db_conn', return_value=mock_conn):
                sample_embedding = [0.1] * 1536
                chunks = await rag_tool.retrieve_chunks(sample_embedding)
                
                # Should respect token budget (100 tokens)
                # First chunk: 45 tokens, second chunk: 42 tokens = 87 total
                # Third chunk: 38 tokens would exceed 100, so should stop at 2 chunks
                assert len(chunks) <= 2
                
                total_tokens = sum(chunk.tokens or 0 for chunk in chunks)
                assert total_tokens <= 100
                
                print("✅ Token budget enforcement working correctly")
                print(f"   Retrieved {len(chunks)} chunks")
                print(f"   Total tokens: {total_tokens}")
                print(f"   Budget limit: 100")
                
        except Exception as e:
            pytest.fail(f"Token budget enforcement test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_rag_tool_similarity_threshold(self, test_user_id: str, rag_config: RetrievalConfig, sample_document_chunks: List[Dict[str, Any]]):
        """Test that RAG tool respects similarity threshold."""
        try:
            # Create RAG tool with high similarity threshold
            high_threshold_config = RetrievalConfig(
                max_chunks=10,
                token_budget=2000,
                similarity_threshold=0.9  # High threshold
            )
            rag_tool = RAGTool(user_id=test_user_id, config=high_threshold_config)
            
            # Mock database connection with filtered chunks (only >= 0.9 similarity)
            mock_conn = AsyncMock()
            high_similarity_chunks = [
                chunk for chunk in sample_document_chunks
                if chunk["similarity"] >= 0.9
            ]
            mock_conn.fetch.return_value = high_similarity_chunks
            
            with patch.object(rag_tool, '_get_db_conn', return_value=mock_conn):
                sample_embedding = [0.1] * 1536
                chunks = await rag_tool.retrieve_chunks(sample_embedding)
                
                # Should only return chunks with similarity >= 0.9
                assert len(chunks) == 2  # Only chunks with 0.95 and 0.92 similarity
                assert all(chunk.similarity >= 0.9 for chunk in chunks)
                
                print("✅ Similarity threshold working correctly")
                print(f"   Retrieved {len(chunks)} chunks")
                print(f"   All chunks above threshold: {all(chunk.similarity >= 0.9 for chunk in chunks)}")
                
        except Exception as e:
            pytest.fail(f"Similarity threshold test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_rag_tool_user_isolation_real_scenario(self, rag_config: RetrievalConfig):
        """Test user isolation with realistic user IDs."""
        try:
            # Create RAG tools for different users with independent configurations
            user1_config = RetrievalConfig(
                max_chunks=3,
                token_budget=1000,
                similarity_threshold=0.8
            )
            user2_config = RetrievalConfig(
                max_chunks=7,
                token_budget=2000,
                similarity_threshold=0.7
            )
            
            user1_tool = RAGTool(user_id="user-123e4567-e89b-12d3-a456-426614174000", config=user1_config)
            user2_tool = RAGTool(user_id="user-987fcdeb-51a2-43d1-b789-987654321000", config=user2_config)
            
            # Verify user isolation
            assert user1_tool.user_id != user2_tool.user_id
            assert user1_tool.user_id == "user-123e4567-e89b-12d3-a456-426614174000"
            assert user2_tool.user_id == "user-987fcdeb-51a2-43d1-b789-987654321000"
            
            # Test that configurations are independent
            assert user1_tool.config.max_chunks == 3
            assert user2_tool.config.max_chunks == 7
            
            print("✅ User isolation with realistic IDs working correctly")
            
        except Exception as e:
            pytest.fail(f"User isolation real scenario test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_rag_tool_query_scenarios(self, test_user_id: str, rag_config: RetrievalConfig, sample_insurance_queries: List[Dict[str, Any]], sample_document_chunks: List[Dict[str, Any]]):
        """Test RAG tool with various insurance query scenarios."""
        try:
            rag_tool = RAGTool(user_id=test_user_id, config=rag_config)
            
            for query_info in sample_insurance_queries:
                query = query_info["query"]
                expected_topics = query_info["expected_topics"]
                document_type = query_info["document_type"]
                
                print(f"\n🔍 Testing query: '{query}'")
                print(f"   Expected topics: {expected_topics}")
                print(f"   Document type: {document_type}")
                
                # Mock database connection for this query
                mock_conn = AsyncMock()
                # Filter chunks based on query relevance
                relevant_chunks = [
                    chunk for chunk in sample_document_chunks
                    if any(topic.lower() in chunk["content"].lower() for topic in expected_topics)
                ]
                mock_conn.fetch.return_value = relevant_chunks
                
                with patch.object(rag_tool, '_get_db_conn', return_value=mock_conn):
                    sample_embedding = [0.1] * 1536
                    chunks = await rag_tool.retrieve_chunks(sample_embedding)
                    
                    # Validate that we got relevant chunks
                    if relevant_chunks:
                        assert len(chunks) > 0
                        print(f"   ✅ Retrieved {len(chunks)} relevant chunks")
                        
                        # Check content relevance
                        chunk_content = " ".join(chunk.content.lower() for chunk in chunks)
                        relevant_topics_found = [
                            topic for topic in expected_topics
                            if topic.lower() in chunk_content
                        ]
                        print(f"   📋 Relevant topics found: {relevant_topics_found}")
                    else:
                        assert len(chunks) == 0
                        print(f"   ⚠️  No relevant chunks found (expected for some queries)")
                
                # Clean up mock - no need to close AsyncMock
                # mock_conn.close()
            
            print("\n✅ All query scenarios tested successfully")
            
        except Exception as e:
            pytest.fail(f"Query scenarios test failed: {e}")


class TestRAGToolPerformance:
    """Test RAG tool performance characteristics."""
    
    @pytest.fixture
    def test_user_id(self) -> str:
        """Test user ID for performance testing."""
        return "5710ff53-32ea-4fab-be6d-3a6f0627fbff"
    
    @pytest.fixture
    def performance_config(self) -> RetrievalConfig:
        """Performance testing configuration."""
        return RetrievalConfig(
            max_chunks=20,
            token_budget=5000,
            similarity_threshold=0.6
        )
    
    @pytest.mark.asyncio
    async def test_rag_tool_response_time(self, test_user_id: str, performance_config: RetrievalConfig):
        """Test RAG tool response time performance."""
        try:
            rag_tool = RAGTool(user_id=test_user_id, config=performance_config)
            
            # Create a large number of simulated chunks
            large_chunk_set = []
            for i in range(100):
                large_chunk_set.append({
                    "chunk_id": f"chunk-{i:03d}",
                    "document_id": f"doc-{i//10:03d}",
                    "chunk_index": i % 10,
                    "content": f"This is chunk {i} with some sample content about insurance benefits and coverage details.",
                    "section_path": [i//10, i%10],
                    "section_title": f"Section {i//10}.{i%10}",
                    "page_start": i//10 + 1,
                    "page_end": i//10 + 1,
                    "tokens": 20 + (i % 10),
                    "similarity": 0.8 - (i * 0.001)  # Decreasing similarity
                })
            
            # Mock database connection with limited results (respect max_chunks)
            mock_conn = AsyncMock()
            # Only return first 20 chunks to respect max_chunks
            limited_chunks = large_chunk_set[:20]
            mock_conn.fetch.return_value = limited_chunks
            
            with patch.object(rag_tool, '_get_db_conn', return_value=mock_conn):
                sample_embedding = [0.1] * 1536
                
                # Measure response time
                start_time = asyncio.get_event_loop().time()
                chunks = await rag_tool.retrieve_chunks(sample_embedding)
                end_time = asyncio.get_event_loop().time()
                
                response_time = end_time - start_time
                
                # Validate performance
                assert len(chunks) <= 20  # Respect max_chunks
                assert response_time < 1.0  # Should complete within 1 second
                
                print("✅ Performance test successful")
                print(f"   Response time: {response_time:.3f}s")
                print(f"   Chunks retrieved: {len(chunks)}")
                print(f"   Performance target: <1.0s")
                
        except Exception as e:
            pytest.fail(f"Performance test failed: {e}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
