"""
Unit tests for the Communication Agent.

Tests the agent's ability to transform technical agent outputs into
warm, empathetic, user-friendly responses.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from agents.patient_navigator.output_processing.agent import CommunicationAgent
from agents.patient_navigator.output_processing.types import (
    CommunicationRequest,
    CommunicationResponse,
    AgentOutput
)
from agents.patient_navigator.output_processing.config import OutputProcessingConfig


class TestCommunicationAgent:
    """Test cases for the Communication Agent."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        return OutputProcessingConfig(
            llm_model="claude-3-haiku",
            request_timeout=30.0,
            max_input_length=10000,
            max_agent_outputs=5,
            enable_fallback=True,
            fallback_to_original=True
        )
    
    @pytest.fixture
    def sample_agent_outputs(self):
        """Create sample agent outputs for testing."""
        return [
            AgentOutput(
                agent_id="benefits_analyzer",
                content="Your plan covers 80% of in-network costs after $500 deductible. Out-of-network coverage is 60% after $1000 deductible.",
                metadata={"coverage_type": "medical", "deductible_met": False}
            ),
            AgentOutput(
                agent_id="eligibility_checker",
                content="Eligibility confirmed. Active coverage until 12/31/2024. No pre-existing condition exclusions apply.",
                metadata={"status": "active", "effective_date": "2024-01-01"}
            )
        ]
    
    @pytest.fixture
    def claim_denial_output(self):
        """Create a claim denial output for testing sensitive content handling."""
        return [
            AgentOutput(
                agent_id="claims_processor",
                content="Claim denied. Policy exclusion 3.2 applies. Coverage not available for pre-existing conditions.",
                metadata={"denial_reason": "pre_existing_condition", "exclusion_code": "3.2"}
            )
        ]
    
    @pytest.fixture
    def form_assistance_output(self):
        """Create a form assistance output for testing guidance content."""
        return [
            AgentOutput(
                agent_id="form_assistant",
                content="Complete sections 1-3, attach supporting documents, submit within 30 days. Missing information will delay processing.",
                metadata={"form_type": "appeal", "deadline": "30_days"}
            )
        ]
    
    def test_agent_initialization(self, mock_config):
        """Test that the agent initializes correctly."""
        agent = CommunicationAgent(config=mock_config)
        
        assert agent.name == "output_communication"
        assert agent.config == mock_config
        assert agent.mock is True  # No LLM client provided
        assert "prompts/system_prompt.md" in agent.prompt
    
    def test_agent_initialization_with_llm(self, mock_config):
        """Test that the agent initializes correctly with an LLM client."""
        mock_llm = Mock()
        agent = CommunicationAgent(llm_client=mock_llm, config=mock_config)
        
        assert agent.llm == mock_llm
        assert agent.mock is False
    
    def test_validate_request_success(self, mock_config, sample_agent_outputs):
        """Test successful request validation."""
        agent = CommunicationAgent(config=mock_config)
        request = CommunicationRequest(agent_outputs=sample_agent_outputs)
        
        # Should not raise an exception
        agent._validate_request(request)
    
    def test_validate_request_no_outputs(self, mock_config):
        """Test validation failure when no agent outputs provided."""
        agent = CommunicationAgent(config=mock_config)
        request = CommunicationRequest(agent_outputs=[])
        
        with pytest.raises(ValueError, match="At least one agent output is required"):
            agent._validate_request(request)
    
    def test_validate_request_too_many_outputs(self, mock_config):
        """Test validation failure when too many agent outputs provided."""
        config = OutputProcessingConfig(max_agent_outputs=2)
        agent = CommunicationAgent(config=config)
        
        # Create 3 outputs (exceeding limit of 2)
        outputs = [
            AgentOutput(agent_id=f"agent_{i}", content=f"content {i}")
            for i in range(3)
        ]
        request = CommunicationRequest(agent_outputs=outputs)
        
        with pytest.raises(ValueError, match="Too many agent outputs"):
            agent._validate_request(request)
    
    def test_validate_request_content_too_long(self, mock_config):
        """Test validation failure when content is too long."""
        config = OutputProcessingConfig(max_input_length=10)
        agent = CommunicationAgent(config=config)
        
        outputs = [
            AgentOutput(agent_id="agent_1", content="This content is way too long and should fail validation")
        ]
        request = CommunicationRequest(agent_outputs=outputs)
        
        with pytest.raises(ValueError, match="Total content length too long"):
            agent._validate_request(request)
    
    def test_format_agent_outputs(self, mock_config, sample_agent_outputs):
        """Test formatting of agent outputs for LLM input."""
        agent = CommunicationAgent(config=mock_config)
        request = CommunicationRequest(agent_outputs=sample_agent_outputs)
        
        formatted = agent._format_agent_outputs(request)
        
        assert "Agent 1 (benefits_analyzer):" in formatted
        assert "Your plan covers 80% of in-network costs" in formatted
        assert "Agent 2 (eligibility_checker):" in formatted
        assert "Eligibility confirmed" in formatted
        assert "Metadata: {'coverage_type': 'medical'" in formatted
    
    def test_format_agent_outputs_with_user_context(self, mock_config, sample_agent_outputs):
        """Test formatting with user context included."""
        agent = CommunicationAgent(config=mock_config)
        user_context = {"user_id": "123", "preferences": {"language": "en"}}
        request = CommunicationRequest(
            agent_outputs=sample_agent_outputs,
            user_context=user_context
        )
        
        formatted = agent._format_agent_outputs(request)
        
        assert "User Context:" in formatted
        assert "user_id" in formatted
        assert "language" in formatted
    
    def test_create_fallback_response(self, mock_config, sample_agent_outputs):
        """Test creation of fallback response when enhancement fails."""
        agent = CommunicationAgent(config=mock_config)
        request = CommunicationRequest(agent_outputs=sample_agent_outputs)
        processing_time = 1.5
        error_message = "LLM call failed"
        
        fallback = agent._create_fallback_response(request, processing_time, error_message)
        
        assert isinstance(fallback, CommunicationResponse)
        assert fallback.original_sources == ["benefits_analyzer", "eligibility_checker"]
        assert fallback.processing_time == processing_time
        assert fallback.metadata["fallback_used"] is True
        assert fallback.metadata["error_message"] == error_message
        assert "Based on the information provided:" in fallback.enhanced_content
    
    def test_create_fallback_response_single_output(self, mock_config):
        """Test fallback response creation with single agent output."""
        agent = CommunicationAgent(config=mock_config)
        outputs = [AgentOutput(agent_id="single_agent", content="Simple content")]
        request = CommunicationRequest(agent_outputs=outputs)
        
        fallback = agent._create_fallback_response(request, 1.0, "Test error")
        
        assert fallback.enhanced_content == "Simple content"
        assert fallback.original_sources == ["single_agent"]
    
    def test_consolidate_original_outputs(self, mock_config, sample_agent_outputs):
        """Test consolidation of original agent outputs."""
        agent = CommunicationAgent(config=mock_config)
        
        consolidated = agent._consolidate_original_outputs(sample_agent_outputs)
        
        assert "Based on the information provided:" in consolidated
        assert "1. Your plan covers 80%" in consolidated
        assert "2. Eligibility confirmed" in consolidated
        assert "Note: This is a basic consolidation" in consolidated
    
    def test_consolidate_original_outputs_single(self, mock_config):
        """Test consolidation with single output."""
        agent = CommunicationAgent(config=mock_config)
        outputs = [AgentOutput(agent_id="single", content="Single content")]
        
        consolidated = agent._consolidate_original_outputs(outputs)
        
        assert consolidated == "Single content"
    
    def test_get_agent_info(self, mock_config):
        """Test agent info retrieval."""
        agent = CommunicationAgent(config=mock_config)
        info = agent.get_agent_info()
        
        assert info["name"] == "output_communication"
        assert info["config"] == mock_config.to_dict()
        assert info["mock_mode"] is True
        assert info["llm_available"] is False
        assert "prompt_length" in info
    
    @pytest.mark.asyncio
    async def test_enhance_response_mock_mode(self, mock_config, sample_agent_outputs):
        """Test response enhancement in mock mode."""
        agent = CommunicationAgent(config=mock_config)
        request = CommunicationRequest(agent_outputs=sample_agent_outputs)
        
        response = await agent.enhance_response(request)
        
        assert isinstance(response, CommunicationResponse)
        assert response.original_sources == ["benefits_analyzer", "eligibility_checker"]
        assert response.processing_time > 0
        assert response.metadata["input_agent_count"] == 2
        assert response.metadata["user_context_provided"] is False
    
    @pytest.mark.asyncio
    async def test_enhance_response_with_user_context(self, mock_config, sample_agent_outputs):
        """Test response enhancement with user context."""
        agent = CommunicationAgent(config=mock_config)
        user_context = {"user_id": "123", "preferences": {"tone": "professional"}}
        request = CommunicationRequest(
            agent_outputs=sample_agent_outputs,
            user_context=user_context
        )
        
        response = await agent.enhance_response(request)
        
        assert response.metadata["user_context_provided"] is True
        assert response.original_sources == ["benefits_analyzer", "eligibility_checker"]
    
    @pytest.mark.asyncio
    async def test_enhance_response_validation_error(self, mock_config):
        """Test response enhancement with validation error."""
        agent = CommunicationAgent(config=mock_config)
        # Create invalid request (no outputs)
        request = CommunicationRequest(agent_outputs=[])
        
        # With fallback enabled, should return fallback response instead of raising exception
        response = await agent.enhance_response(request)
        
        assert isinstance(response, CommunicationResponse)
        assert response.metadata["fallback_used"] is True
        assert "At least one agent output is required" in response.metadata["error_message"]
        assert "Based on the information provided:" in response.enhanced_content
    
    @pytest.mark.asyncio
    async def test_enhance_response_fallback_on_error(self, mock_config, sample_agent_outputs):
        """Test fallback response creation when enhancement fails."""
        config = OutputProcessingConfig(
            enable_fallback=True,
            fallback_to_original=True
        )
        agent = CommunicationAgent(config=config)
        request = CommunicationRequest(agent_outputs=sample_agent_outputs)
        
        # Mock the mock_output method to fail to test fallback
        with patch.object(agent, 'mock_output', side_effect=Exception("Mock error")):
            response = await agent.enhance_response(request)
        
        # Should get fallback response
        assert response.metadata["fallback_used"] is True
        assert "Mock error" in response.metadata["error_message"]
        assert "Based on the information provided:" in response.enhanced_content
        assert response.original_sources == ["benefits_analyzer", "eligibility_checker"]


class TestCommunicationAgentContentTypes:
    """Test the agent's handling of different content types."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        return OutputProcessingConfig(
            enable_fallback=True,
            fallback_to_original=True
        )
    
    @pytest.mark.asyncio
    async def test_claim_denial_handling(self, mock_config):
        """Test handling of claim denial content (sensitive topic)."""
        agent = CommunicationAgent(config=mock_config)
        outputs = [
            AgentOutput(
                agent_id="claims_processor",
                content="Claim denied. Policy exclusion 3.2 applies. Coverage not available for pre-existing conditions.",
                metadata={"denial_reason": "pre_existing_condition"}
            )
        ]
        request = CommunicationRequest(agent_outputs=outputs)
        
        response = await agent.enhance_response(request)
        
        # In mock mode, should get enhanced content for claim denials
        assert "I understand this is frustrating news" in response.enhanced_content
        assert "Your claim was denied due to a policy exclusion" in response.enhanced_content
        assert "Next steps you can take:" in response.enhanced_content
        assert "appealing" in response.enhanced_content
        assert response.original_sources == ["claims_processor"]
    
    @pytest.mark.asyncio
    async def test_form_assistance_handling(self, mock_config):
        """Test handling of form assistance content."""
        agent = CommunicationAgent(config=mock_config)
        outputs = [
            AgentOutput(
                agent_id="form_assistant",
                content="Complete sections 1-3, attach supporting documents, submit within 30 days.",
                metadata={"form_type": "appeal", "deadline": "30_days"}
            )
        ]
        request = CommunicationRequest(agent_outputs=outputs)
        
        response = await agent.enhance_response(request)
        
        # In mock mode, should get enhanced content for form assistance
        assert "Based on the information provided" in response.enhanced_content
        assert "Your coverage status has been confirmed" in response.enhanced_content
        assert "Next Steps:" in response.enhanced_content
        assert response.original_sources == ["form_assistant"]
    
    @pytest.mark.asyncio
    async def test_benefits_explanation_handling(self, mock_config):
        """Test handling of benefits explanation content."""
        agent = CommunicationAgent(config=mock_config)
        outputs = [
            AgentOutput(
                agent_id="benefits_analyzer",
                content="Your plan covers 80% of in-network costs after $500 deductible.",
                metadata={"coverage_type": "medical"}
            )
        ]
        request = CommunicationRequest(agent_outputs=outputs)
        
        response = await agent.enhance_response(request)
        
        # In mock mode, should get enhanced content for benefits
        assert "Great news! Here's what your insurance plan covers" in response.enhanced_content
        assert "80% coverage after meeting your deductible" in response.enhanced_content
        assert "$500 for in-network" in response.enhanced_content
        assert "Next steps:" in response.enhanced_content
        assert response.original_sources == ["benefits_analyzer"]


if __name__ == "__main__":
    pytest.main([__file__])
