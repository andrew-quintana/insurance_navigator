"""
Integration tests for LangGraph agent workflows in Medicare Navigator
Tests the complete agent orchestration flows
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

# Import the orchestrator and related classes
from graph.agent_orchestrator import AgentOrchestrator, run_workflow
from agents.common.exceptions import AgentException


class TestAgentWorkflows:
    """Test class for agent workflow integration tests"""

    @pytest.fixture
    async def orchestrator(self):
        """Create an orchestrator instance for testing"""
        # Mock the agent initialization to avoid dependencies
        with patch('graph.agent_orchestrator.PromptSecurityAgent') as mock_security, \
             patch('graph.agent_orchestrator.PatientNavigatorAgent') as mock_navigator, \
             patch('graph.agent_orchestrator.TaskRequirementsAgent') as mock_task, \
             patch('graph.agent_orchestrator.ServiceAccessStrategyAgent') as mock_strategy, \
             patch('graph.agent_orchestrator.RegulatoryAgent') as mock_regulatory, \
             patch('graph.agent_orchestrator.ChatCommunicatorAgent') as mock_chat, \
             patch('graph.agent_orchestrator.ConfigManager'):
            
            # Setup mock agents
            mock_security.return_value = AsyncMock()
            mock_navigator.return_value = AsyncMock()
            mock_task.return_value = AsyncMock()
            mock_strategy.return_value = AsyncMock()
            mock_regulatory.return_value = AsyncMock()
            mock_chat.return_value = AsyncMock()
            
            # Create orchestrator
            orchestrator = AgentOrchestrator()
            
            # Setup mock responses
            orchestrator.prompt_security_agent.check_prompt_security.return_value = AsyncMock(is_safe=True)
            orchestrator.patient_navigator_agent.analyze_request.return_value = AsyncMock(
                intent_type="find_provider",
                confidence_score=0.9
            )
            orchestrator.patient_navigator_agent.answer_question.return_value = AsyncMock(
                answer="A copay is a fixed amount you pay for healthcare services.",
                question_type="definition",
                confidence_score=0.95
            )
            orchestrator.task_requirements_agent.analyze_requirements.return_value = AsyncMock(
                requirements_count=3,
                documents_needed=["insurance_card", "referral"]
            )
            orchestrator.service_access_strategy_agent.develop_strategy.return_value = AsyncMock(
                strategy_type="provider_search",
                action_steps=["verify_coverage", "find_providers", "schedule_appointment"]
            )
            orchestrator.regulatory_agent.check_compliance.return_value = AsyncMock(
                status="compliant",
                regulations_count=2
            )
            orchestrator.chat_communicator_agent.generate_response.return_value = AsyncMock(
                response_text="To access care, follow these steps: 1. Check coverage 2. Find providers",
                response_type="strategy_guidance",
                confidence_score=0.9
            )
            
            return orchestrator

    @pytest.mark.asyncio
    async def test_strategy_request_workflow(self, orchestrator):
        """Test full strategy workflow: Navigator → Task → Strategy → Regulatory → Chat"""
        
        # Test data
        input_message = "I need to find a doctor who takes my insurance"
        user_id = "test_user_123"
        
        # Execute workflow
        response = await orchestrator.process_message(input_message, user_id)
        
        # Assertions
        assert response["workflow_type"] == "strategy_request"
        assert "text" in response
        assert "metadata" in response
        assert "conversation_id" in response
        
        # Verify the response contains expected elements
        assert "access care" in response["text"].lower() or "follow these steps" in response["text"].lower()
        
        # Verify metadata contains workflow information
        metadata = response["metadata"]
        assert "security_check" in metadata
        assert "navigator_analysis" in metadata
        assert "task_requirements" in metadata
        assert "service_strategy" in metadata
        assert "regulatory_check" in metadata
        assert "chat_response" in metadata
        
        # Verify all agents were called in correct order
        orchestrator.prompt_security_agent.check_prompt_security.assert_called_once()
        orchestrator.patient_navigator_agent.analyze_request.assert_called_once()
        orchestrator.task_requirements_agent.analyze_requirements.assert_called_once()
        orchestrator.service_access_strategy_agent.develop_strategy.assert_called_once()
        orchestrator.regulatory_agent.check_compliance.assert_called_once()
        orchestrator.chat_communicator_agent.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_navigator_only_workflow(self, orchestrator):
        """Test simple Q&A workflow: Navigator → Chat"""
        
        # Test data
        input_message = "What's a copay?"
        user_id = "test_user_456"
        
        # Execute workflow
        response = await orchestrator.process_message(input_message, user_id)
        
        # Assertions
        assert response["workflow_type"] == "navigator_only"
        assert "text" in response
        assert "metadata" in response
        assert "conversation_id" in response
        
        # Verify the response contains expected content
        assert "copay" in response["text"].lower()
        
        # Verify metadata contains appropriate workflow information
        metadata = response["metadata"]
        assert "security_check" in metadata
        assert "navigator_qa" in metadata
        assert "chat_response" in metadata
        
        # Verify only appropriate agents were called (not task/strategy/regulatory)
        orchestrator.prompt_security_agent.check_prompt_security.assert_called_once()
        orchestrator.patient_navigator_agent.answer_question.assert_called_once()
        orchestrator.chat_communicator_agent.generate_response.assert_called_once()
        
        # Verify task/strategy/regulatory agents were NOT called
        orchestrator.task_requirements_agent.analyze_requirements.assert_not_called()
        orchestrator.service_access_strategy_agent.develop_strategy.assert_not_called()
        orchestrator.regulatory_agent.check_compliance.assert_not_called()

    @pytest.mark.asyncio
    async def test_workflow_type_determination(self, orchestrator):
        """Test that the orchestrator correctly determines workflow types"""
        
        # Strategy request keywords
        strategy_messages = [
            "I need to find a doctor",
            "Help me locate a specialist",
            "How do I access care?",
            "Find me a provider",
            "I need an appointment",
            "Search for physicians"
        ]
        
        for message in strategy_messages:
            workflow_type = orchestrator._determine_workflow_type(message)
            assert workflow_type == "strategy_request", f"Message '{message}' should trigger strategy workflow"
        
        # Navigator-only (Q&A) messages
        qa_messages = [
            "What is Medicare?",
            "Explain copays to me",
            "What's the difference between Part A and Part B?",
            "Define deductible",
            "Tell me about Medicare Advantage"
        ]
        
        for message in qa_messages:
            workflow_type = orchestrator._determine_workflow_type(message)
            assert workflow_type == "navigator_only", f"Message '{message}' should trigger navigator-only workflow"

    @pytest.mark.asyncio
    async def test_security_check_failure(self, orchestrator):
        """Test workflow behavior when security check fails"""
        
        # Setup security failure
        orchestrator.prompt_security_agent.check_prompt_security.return_value = AsyncMock(is_safe=False)
        
        # Test data
        input_message = "Some potentially unsafe message"
        user_id = "test_user_789"
        
        # Execute workflow
        response = await orchestrator.process_message(input_message, user_id)
        
        # Should return error response
        assert response["workflow_type"] == "error"
        assert "technical difficulties" in response["text"].lower()
        
        # Only security agent should have been called
        orchestrator.prompt_security_agent.check_prompt_security.assert_called_once()
        orchestrator.patient_navigator_agent.analyze_request.assert_not_called()
        orchestrator.patient_navigator_agent.answer_question.assert_not_called()

    @pytest.mark.asyncio
    async def test_agent_error_handling(self, orchestrator):
        """Test workflow behavior when an agent throws an exception"""
        
        # Setup navigator agent to throw exception
        orchestrator.patient_navigator_agent.analyze_request.side_effect = Exception("Navigator agent error")
        
        # Test data
        input_message = "Find me a doctor"
        user_id = "test_user_error"
        
        # Execute workflow
        response = await orchestrator.process_message(input_message, user_id)
        
        # Should return error response
        assert response["workflow_type"] == "error"
        assert "technical difficulties" in response["text"].lower()

    @pytest.mark.asyncio
    async def test_conversation_id_persistence(self, orchestrator):
        """Test that conversation ID is handled correctly"""
        
        # Test without conversation ID (should generate one)
        response1 = await orchestrator.process_message("What is Medicare?", "user_123")
        assert response1["conversation_id"] is not None
        assert response1["conversation_id"].startswith("conv_")
        
        # Test with existing conversation ID (should preserve it)
        existing_conv_id = "conv_existing_123"
        response2 = await orchestrator.process_message(
            "Tell me more", "user_123", existing_conv_id
        )
        assert response2["conversation_id"] == existing_conv_id

    @pytest.mark.asyncio
    async def test_metadata_structure(self, orchestrator):
        """Test that response metadata has the expected structure"""
        
        # Test strategy workflow metadata
        response = await orchestrator.process_message("Find me a doctor", "user_123")
        
        metadata = response["metadata"]
        
        # Check security metadata
        assert metadata["security_check"] == "passed"
        
        # Check navigator analysis metadata
        nav_analysis = metadata["navigator_analysis"]
        assert "intent" in nav_analysis
        assert "confidence" in nav_analysis
        
        # Check task requirements metadata
        task_req = metadata["task_requirements"]
        assert "requirements_identified" in task_req
        assert "documents_needed" in task_req
        
        # Check service strategy metadata
        service_strat = metadata["service_strategy"]
        assert "strategy_type" in service_strat
        assert "action_steps" in service_strat
        
        # Check regulatory metadata
        regulatory = metadata["regulatory_check"]
        assert "compliance_status" in regulatory
        assert "regulations_checked" in regulatory
        
        # Check chat response metadata
        chat_resp = metadata["chat_response"]
        assert "response_type" in chat_resp
        assert "confidence" in chat_resp


class TestWorkflowConvenienceFunctions:
    """Test the convenience functions for running workflows"""

    @pytest.mark.asyncio
    @patch('graph.agent_orchestrator.get_orchestrator')
    async def test_run_workflow_function(self, mock_get_orchestrator):
        """Test the run_workflow convenience function"""
        
        # Setup mock orchestrator
        mock_orchestrator = AsyncMock()
        mock_orchestrator.process_message.return_value = {
            "text": "Test response",
            "metadata": {"test": True},
            "conversation_id": "conv_123",
            "workflow_type": "navigator_only"
        }
        mock_get_orchestrator.return_value = mock_orchestrator
        
        # Test the function
        result = await run_workflow("Test message", "user_123", "conv_123")
        
        # Verify orchestrator was called correctly
        mock_orchestrator.process_message.assert_called_once_with(
            "Test message", "user_123", "conv_123"
        )
        
        # Verify result
        assert result["text"] == "Test response"
        assert result["workflow_type"] == "navigator_only"


# Performance and load testing
class TestWorkflowPerformance:
    """Test workflow performance characteristics"""

    @pytest.mark.asyncio
    async def test_concurrent_workflows(self, orchestrator):
        """Test multiple concurrent workflow executions"""
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(5):
            task = orchestrator.process_message(f"Test message {i}", f"user_{i}")
            tasks.append(task)
        
        # Execute all concurrently
        results = await asyncio.gather(*tasks)
        
        # Verify all completed successfully
        assert len(results) == 5
        for result in results:
            assert "text" in result
            assert "workflow_type" in result
            assert "conversation_id" in result

    @pytest.mark.asyncio
    async def test_workflow_timeout_handling(self, orchestrator):
        """Test workflow behavior under timeout conditions"""
        
        # Setup slow agent response
        slow_response = AsyncMock()
        slow_response.side_effect = lambda *args: asyncio.sleep(10)  # 10 second delay
        orchestrator.patient_navigator_agent.analyze_request = slow_response
        
        # Test with timeout (this should complete quickly due to error handling)
        start_time = asyncio.get_event_loop().time()
        result = await orchestrator.process_message("Find doctor", "user_timeout")
        end_time = asyncio.get_event_loop().time()
        
        # Should fail gracefully and return error response
        assert result["workflow_type"] == "error"
        assert (end_time - start_time) < 5  # Should not take 10+ seconds


if __name__ == "__main__":
    # Run specific tests for debugging
    pytest.main([__file__, "-v", "-s"]) 