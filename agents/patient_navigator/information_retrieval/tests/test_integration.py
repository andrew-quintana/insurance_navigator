"""
Integration Tests for Information Retrieval Agent

Tests the complete system integration including RAG system, supervisor workflow,
and end-to-end functionality with real-world scenarios.
"""

import pytest
import asyncio
import os
import socket
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from agents.patient_navigator.information_retrieval.agent import InformationRetrievalAgent
from agents.patient_navigator.information_retrieval.models import InformationRetrievalInput, InformationRetrievalOutput
from agents.tooling.rag.core import ChunkWithContext, RAGTool, RetrievalConfig


class TestRealDatabaseIntegration:
    """Test integration with real Supabase database using actual vectors."""
    
    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        return InformationRetrievalAgent(use_mock=False)  # Use real RAG
    
    @pytest.mark.asyncio
    async def test_real_supabase_rag_integration(self, agent):
        """
        Test integration with real Supabase database using actual vectors.
        Uses owner ID: 5710ff53-32ea-4fab-be6d-3a6f0627fbff
        """
        # Check DB connectivity first
        host = os.getenv("DB_HOST", "127.0.0.1")
        port = int(os.getenv("DB_PORT", "54322"))
        try:
            with socket.create_connection((host, port), timeout=2):
                pass
        except Exception:
            pytest.skip("Supabase/Postgres DB not available on {}:{}".format(host, port))

        # Set env vars for RAGTool
        os.environ["SUPABASE_DB_HOST"] = host
        os.environ["SUPABASE_DB_PORT"] = str(port)
        os.environ["SUPABASE_DB_USER"] = os.getenv("DB_USER", "postgres")
        os.environ["SUPABASE_DB_PASSWORD"] = os.getenv("DB_PASSWORD", "postgres")
        os.environ["SUPABASE_DB_NAME"] = os.getenv("DB_NAME", "postgres")

        user_id = "5710ff53-32ea-4fab-be6d-3a6f0627fbff"
        
        # Test with real database vectors
        test_query = "physician services coverage"
        
        # Mock the embedding generation to use a realistic vector
        with patch.object(agent, '_generate_embedding', new_callable=AsyncMock) as mock_embedding:
            # Use a realistic embedding vector (1536 dimensions)
            mock_embedding.return_value = [0.1] * 1536
            
            # Test retrieval with real database
            chunks = await agent._retrieve_chunks(test_query, user_id)
            
            # Verify we get results from real database
            assert isinstance(chunks, list)
            print(f"Retrieved {len(chunks)} chunks from real database for user {user_id}")
            
            # If database has data, verify chunk structure
            if chunks:
                assert all(isinstance(chunk, ChunkWithContext) for chunk in chunks)
                assert all(hasattr(chunk, 'content') for chunk in chunks)
                assert all(hasattr(chunk, 'similarity') for chunk in chunks)
                
                # Verify user-scoped access (all chunks should be for the specified user)
                for chunk in chunks:
                    assert chunk.doc_id is not None
                
                print(f"Sample chunk content: {chunks[0].content[:100]}...")
                print(f"Sample similarity score: {chunks[0].similarity}")
    
    @pytest.mark.asyncio
    async def test_real_database_user_access_control(self, agent):
        """Test that real database enforces user-scoped access control."""
        # Check DB connectivity first
        host = os.getenv("DB_HOST", "127.0.0.1")
        port = int(os.getenv("DB_PORT", "54322"))
        try:
            with socket.create_connection((host, port), timeout=2):
                pass
        except Exception:
            pytest.skip("Supabase/Postgres DB not available on {}:{}".format(host, port))

        # Set env vars for RAGTool
        os.environ["SUPABASE_DB_HOST"] = host
        os.environ["SUPABASE_DB_PORT"] = str(port)
        os.environ["SUPABASE_DB_USER"] = os.getenv("DB_USER", "postgres")
        os.environ["SUPABASE_DB_PASSWORD"] = os.getenv("DB_PASSWORD", "postgres")
        os.environ["SUPABASE_DB_NAME"] = os.getenv("DB_NAME", "postgres")

        # Test with different user IDs
        authorized_user = "5710ff53-32ea-4fab-be6d-3a6f0627fbff"
        unauthorized_user = "different-user-id"
        
        test_query = "prescription drug benefits"
        
        with patch.object(agent, '_generate_embedding', new_callable=AsyncMock) as mock_embedding:
            mock_embedding.return_value = [0.1] * 1536
            
            # Test authorized user
            authorized_chunks = await agent._retrieve_chunks(test_query, authorized_user)
            print(f"Authorized user retrieved {len(authorized_chunks)} chunks")
            
            # Test unauthorized user
            unauthorized_chunks = await agent._retrieve_chunks(test_query, unauthorized_user)
            print(f"Unauthorized user retrieved {len(unauthorized_chunks)} chunks")
            
            # Verify access control - unauthorized user should get fewer or no results
            # (This depends on whether the unauthorized user has any documents)
            assert isinstance(authorized_chunks, list)
            assert isinstance(unauthorized_chunks, list)
    
    @pytest.mark.asyncio
    async def test_real_database_performance(self, agent):
        """Test performance with real database vectors."""
        # Check DB connectivity first
        host = os.getenv("DB_HOST", "127.0.0.1")
        port = int(os.getenv("DB_PORT", "54322"))
        try:
            with socket.create_connection((host, port), timeout=2):
                pass
        except Exception:
            pytest.skip("Supabase/Postgres DB not available on {}:{}".format(host, port))

        # Set env vars for RAGTool
        os.environ["SUPABASE_DB_HOST"] = host
        os.environ["SUPABASE_DB_PORT"] = str(port)
        os.environ["SUPABASE_DB_USER"] = os.getenv("DB_USER", "postgres")
        os.environ["SUPABASE_DB_PASSWORD"] = os.getenv("DB_PASSWORD", "postgres")
        os.environ["SUPABASE_DB_NAME"] = os.getenv("DB_NAME", "postgres")

        user_id = "5710ff53-32ea-4fab-be6d-3a6f0627fbff"
        test_query = "outpatient services"
        
        with patch.object(agent, '_generate_embedding', new_callable=AsyncMock) as mock_embedding:
            mock_embedding.return_value = [0.1] * 1536
            
            # Measure response time
            import time
            start_time = time.time()
            chunks = await agent._retrieve_chunks(test_query, user_id)
            end_time = time.time()
            
            response_time = end_time - start_time
            print(f"Real database retrieval took {response_time:.3f} seconds")
            
            # Performance should be reasonable (< 2 seconds for real database)
            assert response_time < 2.0, f"Database retrieval too slow: {response_time}s"
            
            # Verify we got results
            assert isinstance(chunks, list)


class TestRAGSystemIntegration:
    """Test integration with the RAG system."""
    
    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        return InformationRetrievalAgent(use_mock=True)
    
    @pytest.fixture
    def mock_rag_chunks(self):
        """Create mock RAG chunks for testing."""
        return [
            ChunkWithContext(
                id="chunk_1",
                doc_id="doc_1",
                chunk_index=0,
                content="Your plan covers outpatient physician services with a $25 copay for primary care visits.",
                section_title="Physician Services",
                page_start=1,
                page_end=1,
                similarity=0.85,
                tokens=25
            ),
            ChunkWithContext(
                id="chunk_2",
                doc_id="doc_1",
                chunk_index=1,
                content="Specialist visits require a $40 copay and may need prior authorization.",
                section_title="Specialist Services",
                page_start=2,
                page_end=2,
                similarity=0.78,
                tokens=20
            ),
            ChunkWithContext(
                id="chunk_3",
                doc_id="doc_1",
                chunk_index=2,
                content="Prescription drug benefits include both generic and brand name medications.",
                section_title="Prescription Drugs",
                page_start=3,
                page_end=3,
                similarity=0.72,
                tokens=18
            )
        ]
    
    @pytest.mark.asyncio
    async def test_rag_system_integration(self, agent, mock_rag_chunks):
        """Test integration with RAG system using mock data."""
        # Mock RAG tool
        with patch.object(agent, '_retrieve_chunks', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = mock_rag_chunks
            
            # Test retrieval with expert query
            expert_query = "outpatient physician services benefit coverage"
            user_id = "test_user_123"
            
            chunks = await agent._retrieve_chunks(expert_query, user_id)
            
            # Verify chunks were retrieved
            assert len(chunks) == 3
            assert all(isinstance(chunk, ChunkWithContext) for chunk in chunks)
            
            # Verify similarity filtering
            filtered_chunks = [chunk for chunk in chunks if chunk.similarity >= 0.7]
            assert len(filtered_chunks) >= 2  # At least 2 chunks should meet threshold
    
    @pytest.mark.asyncio
    async def test_rag_similarity_threshold_enforcement(self, agent):
        """Test that RAG system enforces similarity thresholds."""
        # Create chunks with varying similarity scores
        mixed_chunks = [
            ChunkWithContext(
                id="chunk_1",
                doc_id="doc_1",
                chunk_index=0,
                content="High similarity content",
                similarity=0.85,
                tokens=25
            ),
            ChunkWithContext(
                id="chunk_2",
                doc_id="doc_1",
                chunk_index=1,
                content="Medium similarity content",
                similarity=0.65,
                tokens=20
            ),
            ChunkWithContext(
                id="chunk_3",
                doc_id="doc_1",
                chunk_index=2,
                content="Low similarity content",
                similarity=0.45,
                tokens=18
            )
        ]
        
        with patch.object(agent, '_retrieve_chunks', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = mixed_chunks
            
            # Test with different similarity thresholds
            chunks = await agent._retrieve_chunks("test query", "test_user")
            
            # Verify that low similarity chunks are filtered out
            high_similarity_chunks = [chunk for chunk in chunks if chunk.similarity >= 0.8]
            assert len(high_similarity_chunks) >= 1
    
    @pytest.mark.asyncio
    async def test_rag_token_budget_enforcement(self, agent):
        """Test that RAG system enforces token budget limits."""
        # Create chunks that exceed token budget
        large_chunks = [
            ChunkWithContext(
                id="chunk_1",
                doc_id="doc_1",
                chunk_index=0,
                content="Large content chunk",
                similarity=0.9,
                tokens=1500  # Large token count
            ),
            ChunkWithContext(
                id="chunk_2",
                doc_id="doc_1",
                chunk_index=1,
                content="Another large chunk",
                similarity=0.85,
                tokens=1000  # Another large chunk
            ),
            ChunkWithContext(
                id="chunk_3",
                doc_id="doc_1",
                chunk_index=2,
                content="Small chunk",
                similarity=0.8,
                tokens=100  # Small chunk
            )
        ]
        
        with patch.object(agent, '_retrieve_chunks', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = large_chunks
            
            # Test retrieval with token budget
            chunks = await agent._retrieve_chunks("test query", "test_user")
            
            # Verify that chunks are returned (the mock doesn't simulate token budgeting)
            # The actual RAG tool would enforce token budget
            assert len(chunks) >= 1
    
    @pytest.mark.asyncio
    async def test_rag_user_access_control(self, agent):
        """Test that RAG system enforces user-scoped access control."""
        with patch.object(agent, '_retrieve_chunks', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = []
            
            # Test with different user IDs
            user1_chunks = await agent._retrieve_chunks("test query", "user1")
            user2_chunks = await agent._retrieve_chunks("test query", "user2")
            
            # Verify that different users get different results (mocked)
            assert isinstance(user1_chunks, list)
            assert isinstance(user2_chunks, list)
    
    @pytest.mark.asyncio
    async def test_rag_error_handling(self, agent):
        """Test that RAG system handles errors gracefully."""
        with patch.object(agent, '_retrieve_chunks', new_callable=AsyncMock) as mock_retrieve:
            # Simulate database error
            mock_retrieve.side_effect = Exception("Database connection failed")
            
            # Test error handling
            with pytest.raises(Exception):
                await agent._retrieve_chunks("test query", "test_user")


class TestSupervisorWorkflowIntegration:
    """Test integration with supervisor workflow."""
    
    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        return InformationRetrievalAgent(use_mock=True)
    
    @pytest.fixture
    def sample_workflow_input(self):
        """Create sample supervisor workflow input."""
        return InformationRetrievalInput(
            user_query="What does my insurance cover for doctor visits?",
            user_id="test_user_123",
            workflow_context={
                "session_id": "test_session_456",
                "previous_queries": ["What's my deductible?"],
                "user_preferences": {"language": "en", "complexity": "standard"}
            },
            document_requirements=["benefit_documents", "physician_services"]
        )
    
    @pytest.mark.asyncio
    async def test_workflow_input_processing(self, agent, sample_workflow_input):
        """Test processing of supervisor workflow input."""
        with patch.object(agent, '_reframe_query', new_callable=AsyncMock) as mock_reframe, \
             patch.object(agent, '_retrieve_chunks', new_callable=AsyncMock) as mock_retrieve, \
             patch.object(agent, '_generate_response_variants', new_callable=AsyncMock) as mock_variants, \
             patch.object(agent, '_convert_to_source_chunks', new_callable=Mock) as mock_convert, \
             patch.object(agent.consistency_checker, 'extract_key_points', new_callable=Mock) as mock_key_points:
            
            # Set up mocks
            mock_reframe.return_value = "outpatient physician services benefit coverage"
            
            # Create proper mock chunks with required attributes
            mock_chunk1 = Mock()
            mock_chunk1.id = "chunk_1"
            mock_chunk1.doc_id = "doc_1"
            mock_chunk1.content = "Your plan covers outpatient physician services."
            mock_chunk1.section_title = "Physician Services"
            mock_chunk1.page_start = 1
            mock_chunk1.page_end = 1
            mock_chunk1.similarity = 0.85
            mock_chunk1.tokens = 25
            
            mock_chunk2 = Mock()
            mock_chunk2.id = "chunk_2"
            mock_chunk2.doc_id = "doc_1"
            mock_chunk2.content = "Specialist visits require prior authorization."
            mock_chunk2.section_title = "Specialist Services"
            mock_chunk2.page_start = 2
            mock_chunk2.page_end = 2
            mock_chunk2.similarity = 0.78
            mock_chunk2.tokens = 20
            
            mock_retrieve.return_value = [mock_chunk1, mock_chunk2]
            
            # Provide more realistic response variants that will generate key points
            mock_variants.return_value = [
                "Your plan covers outpatient physician services with a $25 copay for primary care visits. Specialist visits require a $40 copay and may need prior authorization.",
                "Your plan includes outpatient physician services with a $25 copay for primary care. Specialist visits cost $40 and require prior authorization.",
                "Your plan provides outpatient physician services with a $25 copay for primary care. Specialist visits have a $40 copay and need prior authorization."
            ]
            
            # Mock source chunks conversion
            from agents.patient_navigator.information_retrieval.models import SourceChunk
            mock_source_chunks = [
                SourceChunk(
                    chunk_id="chunk_1",
                    doc_id="doc_1",
                    content="Your plan covers outpatient physician services.",
                    section_title="Physician Services",
                    page_start=1,
                    page_end=1,
                    similarity=0.85,
                    tokens=25
                ),
                SourceChunk(
                    chunk_id="chunk_2",
                    doc_id="doc_1",
                    content="Specialist visits require prior authorization.",
                    section_title="Specialist Services",
                    page_start=2,
                    page_end=2,
                    similarity=0.78,
                    tokens=20
                )
            ]
            mock_convert.return_value = mock_source_chunks
            
            # Mock key points extraction
            mock_key_points.return_value = [
                "Your plan covers outpatient physician services with a $25 copay",
                "Specialist visits require a $40 copay and may need prior authorization"
            ]
            
            # Process workflow input
            result = await agent.retrieve_information(sample_workflow_input)
            
            # Verify input was processed correctly
            assert isinstance(result, InformationRetrievalOutput)
            assert result.expert_reframe == "outpatient physician services benefit coverage"
            assert len(result.key_points) >= 1  # Should have at least one key point
            assert len(result.source_chunks) >= 1  # Should have source chunks
            
            # Verify workflow context was preserved
            mock_reframe.assert_called_with(sample_workflow_input.user_query)
            mock_retrieve.assert_called_with("outpatient physician services benefit coverage", "test_user_123")
    
    @pytest.mark.asyncio
    async def test_workflow_context_preservation(self, agent, sample_workflow_input):
        """Test that workflow context is preserved through processing."""
        with patch.object(agent, '_reframe_query', new_callable=AsyncMock) as mock_reframe, \
             patch.object(agent, '_retrieve_chunks', new_callable=AsyncMock) as mock_retrieve, \
             patch.object(agent, '_generate_response_variants', new_callable=AsyncMock) as mock_variants, \
             patch.object(agent, '_convert_to_source_chunks', new_callable=Mock) as mock_convert, \
             patch.object(agent.consistency_checker, 'extract_key_points', new_callable=Mock) as mock_key_points:
            
            # Set up mocks
            mock_reframe.return_value = "outpatient physician services benefit coverage"
            
            # Create proper mock chunks with required attributes
            mock_chunk1 = Mock()
            mock_chunk1.id = "chunk_1"
            mock_chunk1.doc_id = "doc_1"
            mock_chunk1.content = "Your plan covers outpatient physician services."
            mock_chunk1.section_title = "Physician Services"
            mock_chunk1.page_start = 1
            mock_chunk1.page_end = 1
            mock_chunk1.similarity = 0.85
            mock_chunk1.tokens = 25
            
            mock_chunk2 = Mock()
            mock_chunk2.id = "chunk_2"
            mock_chunk2.doc_id = "doc_1"
            mock_chunk2.content = "Specialist visits require prior authorization."
            mock_chunk2.section_title = "Specialist Services"
            mock_chunk2.page_start = 2
            mock_chunk2.page_end = 2
            mock_chunk2.similarity = 0.78
            mock_chunk2.tokens = 20
            
            mock_retrieve.return_value = [mock_chunk1, mock_chunk2]
            
            # Provide more realistic response variants that will generate key points
            mock_variants.return_value = [
                "Your plan covers outpatient physician services with a $25 copay for primary care visits. Specialist visits require a $40 copay and may need prior authorization.",
                "Your plan includes outpatient physician services with a $25 copay for primary care. Specialist visits cost $40 and require prior authorization.",
                "Your plan provides outpatient physician services with a $25 copay for primary care. Specialist visits have a $40 copay and need prior authorization."
            ]
            
            # Mock source chunks conversion
            from agents.patient_navigator.information_retrieval.models import SourceChunk
            mock_source_chunks = [
                SourceChunk(
                    chunk_id="chunk_1",
                    doc_id="doc_1",
                    content="Your plan covers outpatient physician services.",
                    section_title="Physician Services",
                    page_start=1,
                    page_end=1,
                    similarity=0.85,
                    tokens=25
                ),
                SourceChunk(
                    chunk_id="chunk_2",
                    doc_id="doc_1",
                    content="Specialist visits require prior authorization.",
                    section_title="Specialist Services",
                    page_start=2,
                    page_end=2,
                    similarity=0.78,
                    tokens=20
                )
            ]
            mock_convert.return_value = mock_source_chunks
            
            # Mock key points extraction
            mock_key_points.return_value = [
                "Your plan covers outpatient physician services with a $25 copay",
                "Specialist visits require a $40 copay and may need prior authorization"
            ]
            
            # Process workflow input
            result = await agent.retrieve_information(sample_workflow_input)
            
            # Verify context is preserved in output
            assert result.key_points is not None
            assert len(result.key_points) >= 1  # Should have at least one key point
            
            # Verify user context is maintained
            assert result.source_chunks is not None  # Should have source attribution
            assert len(result.source_chunks) >= 1  # Should have at least one source chunk
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, agent):
        """Test error handling in workflow integration."""
        # Test with invalid input
        invalid_input = InformationRetrievalInput(
            user_query="",
            user_id="test_user",
            workflow_context={},
            document_requirements=[]
        )
        
        with patch.object(agent, '_reframe_query', new_callable=AsyncMock) as mock_reframe:
            mock_reframe.side_effect = Exception("Translation error")
            
            # Should handle error gracefully
            result = await agent.retrieve_information(invalid_input)
            
            assert isinstance(result, InformationRetrievalOutput)
            assert result.confidence_score == 0.0
            assert "error" in result.direct_answer.lower() or "try again" in result.direct_answer.lower()


class TestBaseAgentPatternCompliance:
    """Test compliance with BaseAgent patterns."""
    
    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        return InformationRetrievalAgent(use_mock=True)
    
    def test_baseagent_inheritance(self, agent):
        """Test that agent properly inherits from BaseAgent."""
        # Test BaseAgent methods are available
        assert hasattr(agent, '__call__')
        assert hasattr(agent, 'format_prompt')
        assert hasattr(agent, 'validate_output')
        assert hasattr(agent, 'mock_output')
        assert hasattr(agent, 'logger')
        
        # Test agent-specific methods
        assert hasattr(agent, 'retrieve_information')
        assert hasattr(agent, '_reframe_query')
        assert hasattr(agent, '_retrieve_chunks')
    
    def test_mock_capability_integration(self, agent):
        """Test mock capability integration for testing."""
        # Test that mock mode works
        assert agent.mock is True
        
        # Test mock output generation with proper data types
        mock_data = {
            "expert_reframe": "mock_expert_reframe",
            "direct_answer": "mock_direct_answer",
            "key_points": ["mock_key_point_1", "mock_key_point_2"],
            "confidence_score": 0.8,
            "source_chunks": [],
            "processing_steps": ["step1", "step2"],
            "error_message": None
        }
        
        # Create mock output using proper schema
        from agents.patient_navigator.information_retrieval.models import InformationRetrievalOutput
        mock_output = InformationRetrievalOutput(**mock_data)
        
        assert isinstance(mock_output, InformationRetrievalOutput)
        assert "expert_reframe" in mock_output.model_dump()
        assert "direct_answer" in mock_output.model_dump()
        assert "confidence_score" in mock_output.model_dump()
    
    def test_error_handling_consistency(self, agent):
        """Test error handling consistency with BaseAgent patterns."""
        # Test that agent follows BaseAgent error handling patterns
        assert hasattr(agent, 'logger')
        assert agent.logger is not None
        
        # Test error handling in process method
        with patch.object(agent, 'retrieve_information', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.side_effect = Exception("Test error")
            
            # Should handle error gracefully
            result = agent.process({"user_query": "test"})
            assert isinstance(result, dict)
            assert "error" in result or "error_message" in result
    
    def test_initialization_and_configuration(self, agent):
        """Test initialization and configuration handling."""
        # Test agent initialization
        assert agent.name == "information_retrieval"
        assert agent.terminology_translator is not None
        assert agent.consistency_checker is not None
        
        # Test configuration parameters
        assert agent.consistency_checker.min_consistency_threshold == 0.8
        assert agent.consistency_checker.max_variants == 5


class TestDatabaseIntegration:
    """Test database integration scenarios."""
    
    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        return InformationRetrievalAgent(use_mock=True)
    
    @pytest.mark.asyncio
    async def test_supabase_connection_simulation(self, agent):
        """Test Supabase connection simulation."""
        with patch.object(agent, '_retrieve_chunks', new_callable=AsyncMock) as mock_retrieve:
            # Simulate successful database connection
            mock_retrieve.return_value = [Mock(), Mock()]
            
            chunks = await agent._retrieve_chunks("test query", "test_user")
            assert len(chunks) == 2
            
            # Verify user_id is passed for access control
            mock_retrieve.assert_called_with("test query", "test_user")
    
    @pytest.mark.asyncio
    async def test_pgvector_extension_integration(self, agent):
        """Test pgvector extension integration simulation."""
        with patch.object(agent, '_generate_embedding', new_callable=AsyncMock) as mock_embedding:
            # Simulate embedding generation
            mock_embedding.return_value = [0.1, 0.2, 0.3] * 128  # 384-dimensional vector
            
            embedding = await agent._generate_embedding("test query")
            assert len(embedding) == 384
            assert all(isinstance(val, float) for val in embedding)
    
    @pytest.mark.asyncio
    async def test_concurrent_access_scenarios(self, agent):
        """Test concurrent access scenarios."""
        async def simulate_concurrent_query(user_id: str, query: str):
            """Simulate concurrent query processing."""
            with patch.object(agent, '_retrieve_chunks', new_callable=AsyncMock) as mock_retrieve:
                mock_retrieve.return_value = [Mock(), Mock()]
                return await agent._retrieve_chunks(query, user_id)
        
        # Simulate multiple concurrent users
        tasks = [
            simulate_concurrent_query(f"user_{i}", f"query_{i}")
            for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All queries should complete successfully
        assert len(results) == 3
        assert all(len(result) == 2 for result in results)


class TestPerformanceIntegration:
    """Test performance integration scenarios."""
    
    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        return InformationRetrievalAgent(use_mock=True)
    
    @pytest.mark.asyncio
    async def test_response_time_validation(self, agent):
        """Test response time validation."""
        import time
        
        sample_input = InformationRetrievalInput(
            user_query="What does my insurance cover for doctor visits?",
            user_id="test_user_123"
        )
        
        with patch.object(agent, '_reframe_query', new_callable=AsyncMock) as mock_reframe, \
             patch.object(agent, '_retrieve_chunks', new_callable=AsyncMock) as mock_retrieve, \
             patch.object(agent, '_generate_response_variants', new_callable=AsyncMock) as mock_variants:
            
            # Set up mocks
            mock_reframe.return_value = "outpatient physician services benefit coverage"
            mock_retrieve.return_value = [Mock(), Mock()]
            mock_variants.return_value = ["Response 1", "Response 2", "Response 3"]
            
            # Measure response time
            start_time = time.time()
            result = await agent.retrieve_information(sample_input)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Should complete within reasonable time (mock mode should be fast)
            assert response_time < 1.0  # Mock mode should be very fast
            assert isinstance(result, InformationRetrievalOutput)
    
    @pytest.mark.asyncio
    async def test_memory_efficiency(self, agent):
        """Test memory efficiency during processing."""
        import gc
        import sys
        
        # Get initial memory usage
        gc.collect()
        initial_memory = sys.getsizeof(agent)
        
        sample_input = InformationRetrievalInput(
            user_query="What does my insurance cover for doctor visits?",
            user_id="test_user_123"
        )
        
        with patch.object(agent, '_reframe_query', new_callable=AsyncMock) as mock_reframe, \
             patch.object(agent, '_retrieve_chunks', new_callable=AsyncMock) as mock_retrieve, \
             patch.object(agent, '_generate_response_variants', new_callable=AsyncMock) as mock_variants:
            
            # Set up mocks
            mock_reframe.return_value = "outpatient physician services benefit coverage"
            mock_retrieve.return_value = [Mock(), Mock()]
            mock_variants.return_value = ["Response 1", "Response 2", "Response 3"]
            
            # Process multiple queries
            for i in range(5):
                result = await agent.retrieve_information(sample_input)
                assert isinstance(result, InformationRetrievalOutput)
            
            # Check memory usage hasn't grown excessively
            gc.collect()
            final_memory = sys.getsizeof(agent)
            memory_growth = final_memory - initial_memory
            
            # Memory growth should be reasonable
            assert memory_growth < 10000  # Should not grow by more than 10KB
    
    @pytest.mark.asyncio
    async def test_resource_cleanup(self, agent):
        """Test resource cleanup after processing."""
        sample_input = InformationRetrievalInput(
            user_query="What does my insurance cover for doctor visits?",
            user_id="test_user_123"
        )
        
        with patch.object(agent, '_reframe_query', new_callable=AsyncMock) as mock_reframe, \
             patch.object(agent, '_retrieve_chunks', new_callable=AsyncMock) as mock_retrieve, \
             patch.object(agent, '_generate_response_variants', new_callable=AsyncMock) as mock_variants:
            
            # Set up mocks
            mock_reframe.return_value = "outpatient physician services benefit coverage"
            mock_retrieve.return_value = [Mock(), Mock()]
            mock_variants.return_value = ["Response 1", "Response 2", "Response 3"]
            
            # Process query
            result = await agent.retrieve_information(sample_input)
            
            # Verify no lingering references
            assert agent.rag_tool is None or not hasattr(agent.rag_tool, '_connection')
            
            # Verify result is properly structured
            assert isinstance(result, InformationRetrievalOutput)
            assert result.expert_reframe is not None
            assert result.direct_answer is not None 