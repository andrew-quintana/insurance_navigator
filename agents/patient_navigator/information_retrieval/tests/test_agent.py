"""
Tests for Information Retrieval Agent

Tests the ReAct pattern implementation, LLM integration, RAG system integration,
and self-consistency methodology.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from agents.patient_navigator.information_retrieval.agent import InformationRetrievalAgent
from agents.patient_navigator.information_retrieval.models import InformationRetrievalInput, InformationRetrievalOutput
from agents.tooling.rag.core import ChunkWithContext


class TestInformationRetrievalAgent:
    """Test the Information Retrieval Agent implementation."""
    
    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        return InformationRetrievalAgent(use_mock=True)
    
    @pytest.fixture
    def sample_input(self):
        """Create sample input data."""
        return InformationRetrievalInput(
            user_query="What does my insurance cover for doctor visits?",
            user_id="test_user_123",
            workflow_context={"session_id": "test_session"},
            document_requirements=["benefit_documents"]
        )
    
    @pytest.fixture
    def mock_chunks(self):
        """Create mock document chunks."""
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
            )
        ]
    
    def test_agent_initialization(self, agent):
        """Test agent initialization and inheritance."""
        assert isinstance(agent, InformationRetrievalAgent)
        assert agent.name == "information_retrieval"
        assert agent.terminology_translator is not None
        assert agent.consistency_checker is not None
        assert agent.rag_tool is None  # Will be initialized with user context
    
    def test_agent_inheritance(self, agent):
        """Test that agent properly inherits from BaseAgent."""
        # Test that agent has BaseAgent methods
        assert hasattr(agent, '__call__')
        assert hasattr(agent, 'format_prompt')
        assert hasattr(agent, 'validate_output')
        assert hasattr(agent, 'mock_output')
    
    @pytest.mark.asyncio
    async def test_reframe_query_llm_integration(self, agent):
        """Test LLM-based query reframing."""
        user_query = "What does my insurance cover for doctor visits?"
        
        # Mock LLM response
        mock_response = "outpatient physician services benefit coverage"
        with patch.object(agent, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            
            expert_query = await agent._reframe_query(user_query)
            
            # Verify LLM was called
            mock_llm.assert_called_once()
            
            # Verify response contains insurance terminology
            assert "physician" in expert_query.lower()
            assert "services" in expert_query.lower()
    
    @pytest.mark.asyncio
    async def test_reframe_query_fallback(self, agent):
        """Test fallback translation when LLM fails."""
        user_query = "What does my insurance cover for doctor visits?"
        
        # Mock LLM failure
        with patch.object(agent, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("LLM error")
            
            expert_query = await agent._reframe_query(user_query)
            
            # Should use fallback translation
            assert "physician" in expert_query.lower()
            assert "services" in expert_query.lower()
    
    @pytest.mark.asyncio
    async def test_retrieve_chunks_rag_integration(self, agent, mock_chunks):
        """Test RAG system integration."""
        expert_query = "outpatient physician services benefit coverage"
        user_id = "test_user_123"
        
        # Mock RAG tool
        mock_rag_tool = Mock()
        mock_rag_tool.retrieve_chunks.return_value = mock_chunks
        
        with patch('agents.patient_navigator.information_retrieval.agent.RAGTool') as mock_rag_class:
            mock_rag_class.return_value = mock_rag_tool
            
            chunks = await agent._retrieve_chunks(expert_query, user_id)
            
            # Verify RAG tool was initialized correctly
            mock_rag_class.assert_called_once_with(
                user_id=user_id,
                config=agent.rag_tool.config if agent.rag_tool else None
            )
            
            # Verify chunks were retrieved
            assert len(chunks) == 2
            assert chunks[0].similarity == 0.85
            assert chunks[1].similarity == 0.78
    
    @pytest.mark.asyncio
    async def test_generate_response_variants(self, agent, mock_chunks):
        """Test response variant generation."""
        user_query = "What does my insurance cover for doctor visits?"
        expert_query = "outpatient physician services benefit coverage"
        
        # Mock LLM responses for variants
        mock_variants = [
            "Your plan covers doctor visits with a $25 copay for primary care.",
            "Primary care physician visits are covered with a $25 copayment.",
            "You have a $25 copay for outpatient physician services."
        ]
        
        with patch.object(agent, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = mock_variants
            
            variants = await agent._generate_response_variants(mock_chunks, user_query, expert_query)
            
            # Verify variants were generated
            assert len(variants) == 3
            assert all("copay" in variant.lower() or "copayment" in variant.lower() for variant in variants)
    
    @pytest.mark.asyncio
    async def test_generate_response_variants_no_chunks(self, agent):
        """Test response generation when no chunks are available."""
        user_query = "What does my insurance cover for doctor visits?"
        expert_query = "outpatient physician services benefit coverage"
        
        variants = await agent._generate_response_variants([], user_query, expert_query)
        
        # Should return fallback message
        assert len(variants) == 1
        assert "No relevant information found" in variants[0]
    
    def test_prepare_document_context(self, agent, mock_chunks):
        """Test document context preparation."""
        context = agent._prepare_document_context(mock_chunks)
        
        # Verify context includes chunk information
        assert "Chunk 1" in context
        assert "Chunk 2" in context
        assert "0.850" in context  # Similarity score
        assert "Physician Services" in context
        assert "Specialist Services" in context
        assert "copay" in context.lower()
    
    def test_create_variant_prompt(self, agent):
        """Test variant prompt creation."""
        user_query = "What does my insurance cover for doctor visits?"
        expert_query = "outpatient physician services benefit coverage"
        document_context = "Test document context"
        variant_num = 1
        
        prompt = agent._create_variant_prompt(user_query, expert_query, document_context, variant_num)
        
        # Verify prompt structure
        assert "variant 1 of 3" in prompt
        assert user_query in prompt
        assert expert_query in prompt
        assert document_context in prompt
        assert "comprehensive answer" in prompt
    
    def test_clean_response_variant(self, agent):
        """Test response variant cleaning."""
        # Test normal response
        clean_response = agent._clean_response_variant("Your plan covers doctor visits with a $25 copay.")
        assert clean_response == "Your plan covers doctor visits with a $25 copay."
        
        # Test response with markdown
        markdown_response = agent._clean_response_variant("```Your plan covers doctor visits with a $25 copay.```")
        assert "```" not in clean_response
        
        # Test response with system instructions
        system_response = agent._clean_response_variant(
            "You are generating response variant 1 of 3. Generate a detailed response. Your plan covers doctor visits."
        )
        assert "You are generating response variant" not in system_response
        assert "Your plan covers doctor visits" in system_response
    
    def test_convert_to_source_chunks(self, agent, mock_chunks):
        """Test conversion of RAG chunks to source chunks."""
        source_chunks = agent._convert_to_source_chunks(mock_chunks)
        
        assert len(source_chunks) == 2
        assert source_chunks[0].chunk_id == "chunk_1"
        assert source_chunks[0].doc_id == "doc_1"
        assert source_chunks[0].similarity == 0.85
        assert source_chunks[1].chunk_id == "chunk_2"
        assert source_chunks[1].similarity == 0.78
    
    @pytest.mark.asyncio
    async def test_retrieve_information_full_flow(self, agent, sample_input):
        """Test the complete information retrieval flow."""
        # Mock all the dependencies
        with patch.object(agent, '_reframe_query', new_callable=AsyncMock) as mock_reframe, \
             patch.object(agent, '_retrieve_chunks', new_callable=AsyncMock) as mock_retrieve, \
             patch.object(agent, '_generate_response_variants', new_callable=AsyncMock) as mock_variants, \
             patch.object(agent.consistency_checker, 'calculate_consistency') as mock_consistency, \
             patch.object(agent.consistency_checker, 'synthesize_final_response') as mock_synthesize, \
             patch.object(agent.consistency_checker, 'extract_key_points') as mock_key_points, \
             patch.object(agent.consistency_checker, 'calculate_confidence_score') as mock_confidence:
            
            # Set up mock returns
            mock_reframe.return_value = "outpatient physician services benefit coverage"
            mock_retrieve.return_value = [Mock(), Mock()]  # Mock chunks
            mock_variants.return_value = ["Response 1", "Response 2", "Response 3"]
            mock_consistency.return_value = 0.85
            mock_synthesize.return_value = "Your plan covers doctor visits with a $25 copay."
            mock_key_points.return_value = ["$25 copay for primary care", "Prior authorization may be required"]
            mock_confidence.return_value = 0.88
            
            # Execute the full flow
            result = await agent.retrieve_information(sample_input)
            
            # Verify the result structure
            assert isinstance(result, InformationRetrievalOutput)
            assert result.expert_reframe == "outpatient physician services benefit coverage"
            assert result.direct_answer == "Your plan covers doctor visits with a $25 copay."
            assert len(result.key_points) == 2
            assert result.confidence_score == 0.88
            assert len(result.processing_steps) == 5
            
            # Verify all methods were called
            mock_reframe.assert_called_once_with(sample_input.user_query)
            mock_retrieve.assert_called_once()
            mock_variants.assert_called_once()
            mock_consistency.assert_called_once()
            mock_synthesize.assert_called_once()
            mock_key_points.assert_called_once()
            mock_confidence.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_information_error_handling(self, agent, sample_input):
        """Test error handling in information retrieval."""
        # Mock an exception
        with patch.object(agent, '_reframe_query', new_callable=AsyncMock) as mock_reframe:
            mock_reframe.side_effect = Exception("Test error")
            
            result = await agent.retrieve_information(sample_input)
            
            # Verify error response
            assert isinstance(result, InformationRetrievalOutput)
            assert "error" in result.direct_answer.lower()
            assert result.confidence_score == 0.0
            assert result.error_message == "Test error"
    
    def test_process_method(self, agent, sample_input):
        """Test the process method for supervisor workflow integration."""
        # Test with dictionary input
        input_dict = sample_input.model_dump()
        
        with patch.object(agent, 'retrieve_information', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = InformationRetrievalOutput(
                expert_reframe="test reframe",
                direct_answer="test answer",
                key_points=["test point"],
                confidence_score=0.8,
                source_chunks=[]
            )
            
            result = agent.process(input_dict)
            
            # Verify result is dictionary
            assert isinstance(result, dict)
            assert "expert_reframe" in result
            assert "direct_answer" in result
            assert "confidence_score" in result
    
    def test_process_method_error_handling(self, agent):
        """Test process method error handling."""
        # Test with invalid input
        with patch.object(agent, 'retrieve_information', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.side_effect = Exception("Test error")
            
            result = agent.process({"invalid": "input"})
            
            # Verify error response
            assert isinstance(result, dict)
            assert "error" in result
            assert result["status"] == "error"
            assert "error occurred" in result["direct_answer"].lower()


class TestAgentIntegration:
    """Integration tests for the Information Retrieval Agent."""
    
    @pytest.mark.asyncio
    async def test_rag_system_integration(self):
        """Test integration with actual RAG system (requires database)."""
        # This test would require a real database connection
        # For now, we'll test the integration pattern
        agent = InformationRetrievalAgent(use_mock=True)
        
        # Test that RAG tool can be initialized
        assert agent.rag_tool is None  # Not initialized yet
        
        # Test that the agent can handle RAG integration
        # (This would be tested with real database in integration tests)
        pass
    
    @pytest.mark.asyncio
    async def test_llm_integration(self):
        """Test integration with actual LLM (requires API access)."""
        # This test would require real LLM API access
        # For now, we'll test the integration pattern
        agent = InformationRetrievalAgent(use_mock=True)
        
        # Test that LLM can be called (with mock)
        # (This would be tested with real LLM in integration tests)
        pass


if __name__ == "__main__":
    pytest.main([__file__]) 