"""
Tests for Information Retrieval Agent.

This module contains unit tests for the InformationRetrievalAgent class.
"""

import pytest
from unittest.mock import Mock, patch
from agents.patient_navigator.information_retrieval.agent import InformationRetrievalAgent
from agents.patient_navigator.information_retrieval.models import InformationRetrievalInput, InformationRetrievalOutput


class TestInformationRetrievalAgent:
    """Test cases for InformationRetrievalAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        return InformationRetrievalAgent(use_mock=True)
    
    def test_agent_initialization(self, agent):
        """Test that the agent initializes correctly."""
        assert agent.name == "information_retrieval"
        assert agent.terminology_translator is not None
        assert agent.consistency_checker is not None
        assert agent.rag_tool is None  # Should be initialized with user context
    
    def test_retrieve_information_placeholder(self, agent):
        """Test the placeholder implementation of retrieve_information."""
        result = agent.retrieve_information("What does my insurance cover?", "user123")
        
        assert isinstance(result, InformationRetrievalOutput)
        assert result.expert_reframe == "placeholder_expert_query"
        assert result.direct_answer == "placeholder_direct_answer"
        assert len(result.key_points) == 2
        assert result.confidence_score == 0.8
        assert result.source_chunks == []
    
    def test_process_method_placeholder(self, agent):
        """Test the placeholder implementation of process method."""
        input_data = {"user_query": "Test query", "user_id": "user123"}
        result = agent.process(input_data)
        
        assert isinstance(result, dict)
        assert result["status"] == "not_implemented"
        assert "Phase 1 placeholder" in result["message"]
    
    def test_agent_inheritance(self, agent):
        """Test that the agent properly inherits from BaseAgent."""
        from agents.base_agent import BaseAgent
        assert isinstance(agent, BaseAgent)
    
    def test_agent_has_required_methods(self, agent):
        """Test that the agent has all required methods."""
        assert hasattr(agent, "retrieve_information")
        assert hasattr(agent, "process")
        assert callable(agent.retrieve_information)
        assert callable(agent.process)


class TestInformationRetrievalModels:
    """Test cases for Pydantic models."""
    
    def test_information_retrieval_input_validation(self):
        """Test InformationRetrievalInput validation."""
        # Valid input
        valid_input = InformationRetrievalInput(
            user_query="What does my insurance cover?",
            user_id="user123"
        )
        assert valid_input.user_query == "What does my insurance cover?"
        assert valid_input.user_id == "user123"
        
        # Test with optional fields
        input_with_context = InformationRetrievalInput(
            user_query="Test query",
            user_id="user123",
            workflow_context={"key": "value"},
            document_requirements=["policy_document"]
        )
        assert input_with_context.workflow_context == {"key": "value"}
        assert input_with_context.document_requirements == ["policy_document"]
    
    def test_information_retrieval_output_validation(self):
        """Test InformationRetrievalOutput validation."""
        # Valid output
        valid_output = InformationRetrievalOutput(
            expert_reframe="coverage analysis for outpatient services",
            direct_answer="Your plan covers doctor visits with a $25 copay.",
            key_points=["Primary care visits: $25 copay", "Specialist visits: $40 copay"],
            confidence_score=0.85
        )
        assert valid_output.expert_reframe == "coverage analysis for outpatient services"
        assert valid_output.confidence_score == 0.85
        assert len(valid_output.key_points) == 2
        
        # Test confidence score bounds
        with pytest.raises(ValueError):
            InformationRetrievalOutput(
                expert_reframe="test",
                direct_answer="test",
                key_points=["test"],
                confidence_score=1.5  # Should be <= 1.0
            )
        
        with pytest.raises(ValueError):
            InformationRetrievalOutput(
                expert_reframe="test",
                direct_answer="test",
                key_points=["test"],
                confidence_score=-0.1  # Should be >= 0.0
            )
    
    def test_source_chunk_model(self):
        """Test SourceChunk model validation."""
        from agents.patient_navigator.information_retrieval.models import SourceChunk
        
        chunk = SourceChunk(
            chunk_id="chunk_123",
            doc_id="doc_456",
            content="This is the chunk content.",
            section_title="Benefits",
            page_start=1,
            page_end=2,
            similarity=0.85,
            tokens=150
        )
        
        assert chunk.chunk_id == "chunk_123"
        assert chunk.similarity == 0.85
        assert chunk.tokens == 150 