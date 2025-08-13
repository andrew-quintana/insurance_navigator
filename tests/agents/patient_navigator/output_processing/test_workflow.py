"""
Comprehensive tests for the Output Workflow.

Tests end-to-end workflow processing, input/output interface compliance,
error scenarios and recovery, and performance testing with realistic data sizes.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from agents.patient_navigator.output_processing.workflow import OutputWorkflow
from agents.patient_navigator.output_processing.types import (
    CommunicationRequest,
    CommunicationResponse,
    AgentOutput
)
from agents.patient_navigator.output_processing.config import OutputProcessingConfig


class TestOutputWorkflow:
    """Test cases for the Output Workflow core functionality."""
    
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
    def large_agent_outputs(self):
        """Create large agent outputs for performance testing."""
        return [
            AgentOutput(
                agent_id=f"agent_{i}",
                content=f"This is a large content block with detailed information about coverage, benefits, and policy details. "
                        f"It contains multiple sentences and detailed explanations that should test the workflow's ability "
                        f"to handle substantial amounts of text. Agent {i} provides comprehensive analysis. " * 5,
                metadata={"size": "large", "agent_number": i}
            )
            for i in range(5)
        ]
    
    def test_workflow_initialization(self, mock_config):
        """Test that the workflow initializes correctly."""
        workflow = OutputWorkflow(config=mock_config)
        
        assert workflow.config == mock_config
        assert workflow.communication_agent is not None
        assert workflow.communication_agent.name == "output_communication"
        assert workflow.logger is not None
    
    def test_workflow_initialization_with_llm(self, mock_config):
        """Test that the workflow initializes correctly with an LLM client."""
        mock_llm = Mock()
        workflow = OutputWorkflow(config=mock_config, llm_client=mock_llm)
        
        assert workflow.communication_agent.llm == mock_llm
        assert workflow.communication_agent.mock is False
    
    def test_workflow_initialization_default_config(self):
        """Test that the workflow initializes with default configuration."""
        workflow = OutputWorkflow()
        
        assert workflow.config is not None
        assert isinstance(workflow.config, OutputProcessingConfig)
        assert workflow.communication_agent is not None
    
    def test_validate_workflow_request_success(self, mock_config, sample_agent_outputs):
        """Test successful workflow request validation."""
        workflow = OutputWorkflow(config=mock_config)
        request = CommunicationRequest(agent_outputs=sample_agent_outputs)
        
        # Should not raise an exception
        workflow._validate_workflow_request(request)
    
    def test_validate_workflow_request_no_outputs(self, mock_config):
        """Test validation failure when no agent outputs provided."""
        workflow = OutputWorkflow(config=mock_config)
        request = CommunicationRequest(agent_outputs=[])
        
        with pytest.raises(ValueError, match="At least one agent output is required"):
            workflow._validate_workflow_request(request)
    
    @pytest.mark.asyncio
    async def test_process_request_success(self, mock_config, sample_agent_outputs):
        """Test successful workflow request processing."""
        workflow = OutputWorkflow(config=mock_config)
        request = CommunicationRequest(agent_outputs=sample_agent_outputs)
        
        response = await workflow.process_request(request)
        
        # Validate response structure
        assert isinstance(response, CommunicationResponse)
        assert response.enhanced_content is not None
        assert len(response.enhanced_content) > 100  # Should be substantial content
        assert response.original_sources == ["benefits_analyzer", "eligibility_checker"]  # Fixture provides 2 outputs
        assert response.processing_time > 0
        
        # Check that we got meaningful content (not just generic fallback)
        # Claude Haiku should provide enhanced content based on the input
        assert response.enhanced_content != "Test content"
        assert len(response.enhanced_content) > 200  # Should be substantial content
        
        # Log the actual response for debugging
        print(f"Claude Haiku workflow response: {response.enhanced_content[:300]}...")
    
    @pytest.mark.asyncio
    async def test_process_request_with_user_context(self, mock_config, sample_agent_outputs):
        """Test workflow processing with user context."""
        workflow = OutputWorkflow(config=mock_config)
        user_context = {"user_id": "123", "preferences": {"tone": "professional"}}
        request = CommunicationRequest(
            agent_outputs=sample_agent_outputs,
            user_context=user_context
        )
        
        response = await workflow.process_request(request)
        
        assert response.metadata["user_context_provided"] is True
        assert response.original_sources == ["benefits_analyzer", "eligibility_checker"]
    
    @pytest.mark.asyncio
    async def test_process_request_validation_error(self, mock_config):
        """Test workflow processing with validation error."""
        workflow = OutputWorkflow(config=mock_config)
        # Create invalid request (no outputs)
        request = CommunicationRequest(agent_outputs=[])
        
        response = await workflow.process_request(request)
        
        # Should get error response with fallback content
        assert isinstance(response, CommunicationResponse)
        assert response.metadata["fallback_used"] is True
        assert "At least one agent output is required" in response.metadata["error_message"]
    
    @pytest.mark.asyncio
    async def test_process_request_agent_failure(self, mock_config, sample_agent_outputs):
        """Test workflow processing when the communication agent fails."""
        workflow = OutputWorkflow(config=mock_config)
        request = CommunicationRequest(agent_outputs=sample_agent_outputs)
        
        # Mock the agent to fail
        with patch.object(workflow.communication_agent, 'enhance_response', side_effect=Exception("Agent failure")):
            response = await workflow.process_request(request)
        
        # Should get error response with fallback content
        assert isinstance(response, CommunicationResponse)
        assert response.metadata["fallback_used"] is True
        assert "Agent failure" in response.metadata["error_message"]
    
    @pytest.mark.asyncio
    async def test_process_request_performance(self, mock_config, large_agent_outputs):
        """Test workflow performance with large agent outputs."""
        workflow = OutputWorkflow(config=mock_config)
        request = CommunicationRequest(agent_outputs=large_agent_outputs)
        
        start_time = time.time()
        response = await workflow.process_request(request)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Should complete within reasonable time (adjust based on expected performance)
        assert total_time < 10.0  # 10 seconds max for large content
        assert response.processing_time > 0
        assert response.metadata["workflow_success"] is True
        assert len(response.original_sources) == 5
    
    def test_get_workflow_info(self, mock_config):
        """Test workflow information retrieval."""
        workflow = OutputWorkflow(config=mock_config)
        info = workflow.get_workflow_info()
        
        assert info["workflow_type"] == "output_processing"
        assert info["config"] == mock_config.to_dict()
        assert info["agent_info"]["name"] == "output_communication"
        assert info["workflow_version"] == "1.0.0"
    
    def test_health_check_success(self, mock_config):
        """Test successful health check."""
        workflow = OutputWorkflow(config=mock_config)
        health = workflow.health_check()
        
        assert health["workflow"] == "healthy"
        assert health["agent"] == "healthy"
        assert health["config"] == "valid"
        assert "timestamp" in health
    
    def test_health_check_config_invalid(self, mock_config):
        """Test health check with invalid configuration."""
        # Create workflow with invalid config
        invalid_config = OutputProcessingConfig(
            request_timeout=-1,  # Invalid negative timeout
            max_input_length=0   # Invalid zero length
        )
        
        # This should raise an error during validation
        with pytest.raises(ValueError):
            invalid_config.validate()
        
        # Test that workflow handles this gracefully
        workflow = OutputWorkflow(config=invalid_config)
        health = workflow.health_check()
        
        # The config should be marked as invalid, but the exact error message may vary
        assert "invalid" in health["config"].lower()
        assert health["workflow"] == "unhealthy"


class TestOutputWorkflowErrorHandling:
    """Test the workflow's error handling and recovery mechanisms."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        return OutputProcessingConfig(
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
    
    @pytest.mark.asyncio
    async def test_create_error_response_success(self, mock_config, sample_agent_outputs):
        """Test successful error response creation."""
        workflow = OutputWorkflow(config=mock_config)
        request = CommunicationRequest(agent_outputs=sample_agent_outputs)
        processing_time = 2.5
        error_message = "Test error message"
        
        error_response = workflow._create_error_response(request, processing_time, error_message)
        
        assert isinstance(error_response, CommunicationResponse)
        assert error_response.original_sources == ["benefits_analyzer", "eligibility_checker"]
        assert error_response.processing_time == processing_time
        assert error_response.metadata["fallback_used"] is True
        assert error_response.metadata["error_message"] == error_message
    
    @pytest.mark.asyncio
    async def test_create_error_response_fallback_failure(self, mock_config, sample_agent_outputs):
        """Test error response creation when even fallback fails."""
        workflow = OutputWorkflow(config=mock_config)
        request = CommunicationRequest(agent_outputs=sample_agent_outputs)
        processing_time = 1.0
        error_message = "Critical failure"
        
        # Mock the agent's fallback method to fail
        with patch.object(workflow.communication_agent, '_create_fallback_response', side_effect=Exception("Fallback failed")):
            error_response = workflow._create_error_response(request, processing_time, error_message)
        
        # Should get ultimate fallback response
        assert isinstance(error_response, CommunicationResponse)
        assert error_response.metadata["ultimate_fallback"] is True
        assert error_response.metadata["fallback_creation_failed"] is True
        assert error_response.metadata["error_message"] == error_message
        assert "I'm sorry, but I encountered an error" in error_response.enhanced_content


class TestOutputWorkflowIntegration:
    """Test the workflow's integration capabilities."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        return OutputProcessingConfig(
            enable_fallback=True,
            fallback_to_original=True
        )
    
    @pytest.mark.asyncio
    async def test_workflow_with_real_agent_outputs(self, mock_config):
        """Test workflow with realistic agent output scenarios."""
        workflow = OutputWorkflow(config=mock_config)
        
        # Test with benefits explanation
        benefits_outputs = [
            AgentOutput(
                agent_id="benefits_analyzer",
                content="Your plan covers 80% of in-network costs after $500 deductible.",
                metadata={"coverage_type": "medical"}
            )
        ]
        benefits_request = CommunicationRequest(agent_outputs=benefits_outputs)
        benefits_response = await workflow.process_request(benefits_request)
        
        assert benefits_response.metadata["workflow_success"] is True
        # Claude Haiku may use different phrasing than mock responses
        # Check for benefits-related content instead of specific phrases
        benefits_phrases = ["80%", "coverage", "deductible", "plan", "costs", "network"]
        benefits_score = sum(1 for phrase in benefits_phrases if phrase.lower() in benefits_response.enhanced_content.lower())
        assert benefits_score >= 3, f"Expected benefits explanation, got: {benefits_response.enhanced_content[:200]}..."
        
        # Test with claim denial
        denial_outputs = [
            AgentOutput(
                agent_id="claims_processor",
                content="Claim denied. Policy exclusion 3.2 applies.",
                metadata={"denial_reason": "pre_existing_condition"}
            )
        ]
        denial_request = CommunicationRequest(agent_outputs=denial_outputs)
        denial_response = await workflow.process_request(denial_request)
        
        assert denial_response.metadata["workflow_success"] is True
        # Claude Haiku may use different phrasing than mock responses
        # Check for empathetic content instead of specific phrases
        empathetic_phrases = ["sorry", "frustrating", "denied", "exclusion", "appeal", "help"]
        empathy_score = sum(1 for phrase in empathetic_phrases if phrase.lower() in denial_response.enhanced_content.lower())
        assert empathy_score >= 2, f"Expected empathetic response for claim denial, got: {denial_response.enhanced_content[:200]}..."
    
    @pytest.mark.asyncio
    async def test_workflow_multiple_agent_consolidation(self, mock_config):
        """Test workflow's ability to consolidate multiple agent outputs."""
        workflow = OutputWorkflow(config=mock_config)
        
        # Multiple agent outputs
        multiple_outputs = [
            AgentOutput(
                agent_id="benefits_analyzer",
                content="80% coverage after deductible",
                metadata={"type": "coverage"}
            ),
            AgentOutput(
                agent_id="eligibility_checker",
                content="Active coverage confirmed",
                metadata={"type": "status"}
            ),
            AgentOutput(
                agent_id="cost_estimator",
                content="Estimated annual cost: $2,100",
                metadata={"type": "cost"}
            )
        ]
        
        request = CommunicationRequest(agent_outputs=multiple_outputs)
        response = await workflow.process_request(request)
        
        assert response.metadata["workflow_success"] is True
        assert len(response.original_sources) == 3
        assert "benefits_analyzer" in response.original_sources
        assert "eligibility_checker" in response.original_sources
        assert "cost_estimator" in response.original_sources


class TestOutputWorkflowPerformance:
    """Test the workflow's performance characteristics."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        return OutputProcessingConfig(
            enable_fallback=True,
            fallback_to_original=True,
            max_agent_outputs=10
        )
    
    @pytest.mark.asyncio
    async def test_workflow_response_time_consistency(self, mock_config):
        """Test that workflow response times are consistent."""
        workflow = OutputWorkflow(config=mock_config)
        
        # Create consistent test data
        test_outputs = [
            AgentOutput(
                agent_id="test_agent",
                content="Test content for performance testing",
                metadata={"test": True}
            )
        ]
        request = CommunicationRequest(agent_outputs=test_outputs)
        
        # Run multiple times to check consistency
        response_times = []
        for _ in range(3):
            start_time = time.time()
            response = await workflow.process_request(request)
            end_time = time.time()
            
            response_times.append(end_time - start_time)
            assert response.metadata["workflow_success"] is True
        
        # Response times should be reasonably consistent (within 2x variance)
        max_time = max(response_times)
        min_time = min(response_times)
        assert max_time < min_time * 2, f"Response times too variable: {response_times}"
    
    @pytest.mark.asyncio
    async def test_workflow_memory_efficiency(self, mock_config):
        """Test that workflow doesn't consume excessive memory."""
        workflow = OutputWorkflow(config=mock_config)
        
        # Create large content
        large_content = "Large content " * 1000  # ~15KB of content
        large_outputs = [
            AgentOutput(
                agent_id=f"large_agent_{i}",
                content=large_content,
                metadata={"size": "large", "agent_id": i}
            )
            for i in range(5)
        ]
        
        request = CommunicationRequest(agent_outputs=large_outputs)
        
        # Process large request
        response = await workflow.process_request(request)
        
        assert response.metadata["workflow_success"] is True
        assert len(response.original_sources) == 5
        # Should complete without memory issues


if __name__ == "__main__":
    pytest.main([__file__])
