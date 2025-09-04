"""
Test Phase 2 implementation of Patient Navigator Supervisor Workflow.

This test suite validates the core functionality implemented in Phase 2:
- WorkflowPrescriptionAgent with LLM integration
- DocumentAvailabilityChecker with Supabase integration
- LangGraph workflow orchestration with performance tracking
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from agents.patient_navigator.supervisor.models import (
    SupervisorWorkflowInput,
    WorkflowType,
    DocumentAvailabilityResult
)
from agents.patient_navigator.supervisor.workflow import SupervisorWorkflow
from agents.patient_navigator.supervisor.workflow_prescription import WorkflowPrescriptionAgent
from agents.patient_navigator.supervisor.document_availability import DocumentAvailabilityChecker


class TestWorkflowPrescriptionAgent:
    """Test WorkflowPrescriptionAgent LLM integration."""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM that returns structured responses."""
        async def mock_llm_call(prompt: str) -> str:
            print(f"Mock LLM called with prompt: {prompt[:200]}...")
            
            # Extract user query from the prompt (it should be at the end)
            if "## User Query" in prompt:
                user_query = prompt.split("## User Query")[-1].strip()
            else:
                user_query = prompt
            print(f"Extracted user query: {user_query}")
            
            if "copay" in user_query.lower():
                response = '''{
                    "prescribed_workflows": ["information_retrieval"],
                    "confidence_score": 0.95,
                    "reasoning": "User needs specific information about insurance benefits and costs.",
                    "execution_order": ["information_retrieval"]
                }'''
            elif "find" in user_query.lower() and "doctor" in user_query.lower():
                print(f"Matched strategy condition for query: {user_query}")
                response = '''{
                    "prescribed_workflows": ["strategy"],
                    "confidence_score": 0.9,
                    "reasoning": "User needs guidance on finding providers in network.",
                    "execution_order": ["strategy"]
                }'''
            elif "confused" in user_query.lower():
                response = '''{
                    "prescribed_workflows": ["information_retrieval"],
                    "confidence_score": 0.7,
                    "reasoning": "Default to information retrieval for unclear queries.",
                    "execution_order": ["information_retrieval"]
                }'''
            else:
                response = '''{
                    "prescribed_workflows": ["information_retrieval"],
                    "confidence_score": 0.8,
                    "reasoning": "Default to information retrieval for unclear queries.",
                    "execution_order": ["information_retrieval"]
                }'''
            print(f"Mock LLM returning: {response}")
            return response
        
        return mock_llm_call
    
    @pytest.fixture
    def agent(self, mock_llm):
        """Create WorkflowPrescriptionAgent with mock LLM."""
        agent = WorkflowPrescriptionAgent(
            use_mock=False,
            llm=mock_llm
        )
        # Ensure mock mode is disabled
        agent.mock = False
        return agent
    
    @pytest.mark.asyncio
    async def test_prescribe_workflows_information_retrieval(self, agent):
        """Test workflow prescription for information retrieval queries."""
        result = await agent.prescribe_workflows("What is my copay for doctor visits?")
        
        assert result.prescribed_workflows == [WorkflowType.INFORMATION_RETRIEVAL]
        assert result.confidence_score == 0.95
        assert "insurance benefits" in result.reasoning.lower()
        assert result.execution_order == [WorkflowType.INFORMATION_RETRIEVAL]
    
    @pytest.mark.asyncio
    async def test_prescribe_workflows_strategy(self, agent):
        """Test workflow prescription for strategy queries."""
        result = await agent.prescribe_workflows("How do I find a doctor in my network?")
        
        assert result.prescribed_workflows == [WorkflowType.STRATEGY]
        assert result.confidence_score == 0.9
        assert "guidance" in result.reasoning.lower()
        assert result.execution_order == [WorkflowType.STRATEGY]
    
    @pytest.mark.asyncio
    async def test_prescribe_workflows_fallback(self, agent):
        """Test workflow prescription fallback for unclear queries."""
        result = await agent.prescribe_workflows("I'm confused about my insurance")
        
        assert result.prescribed_workflows == [WorkflowType.INFORMATION_RETRIEVAL]
        assert result.confidence_score == 0.7
        assert "default" in result.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_mock_mode(self):
        """Test mock mode functionality."""
        agent = WorkflowPrescriptionAgent(use_mock=True)
        result = await agent.prescribe_workflows("Test query")
        
        assert result.prescribed_workflows
        assert result.confidence_score > 0
        assert result.reasoning
        assert result.execution_order


class TestDocumentAvailabilityChecker:
    """Test DocumentAvailabilityChecker Supabase integration."""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client with document data."""
        mock_client = Mock()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.data = [
            {"document_type": "insurance_policy", "status": "processed"},
            {"document_type": "benefits_summary", "status": "available"}
        ]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        return mock_client
    
    @pytest.fixture
    def checker(self, mock_supabase_client):
        """Create DocumentAvailabilityChecker with mock Supabase client."""
        checker = DocumentAvailabilityChecker(use_mock=False)
        checker.supabase_client = mock_supabase_client
        return checker
    
    @pytest.mark.asyncio
    async def test_check_availability_with_documents(self, checker):
        """Test document availability checking when documents are available."""
        result = await checker.check_availability(
            [WorkflowType.INFORMATION_RETRIEVAL],
            "test_user_id"
        )
        
        assert result.is_ready is True
        assert "insurance_policy" in result.available_documents
        assert "benefits_summary" in result.available_documents
        assert len(result.missing_documents) == 0
        assert result.document_status["insurance_policy"] is True
        assert result.document_status["benefits_summary"] is True
    
    @pytest.mark.asyncio
    async def test_check_availability_missing_documents(self, checker):
        """Test document availability checking when documents are missing."""
        # Override mock to return no documents
        checker.supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        result = await checker.check_availability(
            [WorkflowType.INFORMATION_RETRIEVAL],
            "test_user_id"
        )
        
        assert result.is_ready is False
        assert len(result.available_documents) == 0
        assert "insurance_policy" in result.missing_documents
        assert "benefits_summary" in result.missing_documents
    
    @pytest.mark.asyncio
    async def test_check_availability_mock_mode(self):
        """Test mock mode functionality."""
        checker = DocumentAvailabilityChecker(use_mock=True)
        result = await checker.check_availability(
            [WorkflowType.INFORMATION_RETRIEVAL],
            "test_user_id"
        )
        
        assert result.is_ready is True  # Mock assumes some docs are available
        assert len(result.available_documents) > 0
        assert len(result.missing_documents) == 0


class TestSupervisorWorkflow:
    """Test SupervisorWorkflow orchestration."""
    
    @pytest.fixture
    def mock_workflow_agent(self):
        """Mock WorkflowPrescriptionAgent."""
        agent = Mock()
        agent.prescribe_workflows = AsyncMock()
        
        # Mock successful prescription
        from agents.patient_navigator.supervisor.models import WorkflowPrescriptionResult
        agent.prescribe_workflows.return_value = WorkflowPrescriptionResult(
            prescribed_workflows=[WorkflowType.INFORMATION_RETRIEVAL],
            confidence_score=0.9,
            reasoning="Test prescription",
            execution_order=[WorkflowType.INFORMATION_RETRIEVAL]
        )
        
        return agent
    
    @pytest.fixture
    def mock_document_checker(self):
        """Mock DocumentAvailabilityChecker."""
        checker = Mock()
        checker.check_availability = AsyncMock()
        
        # Mock successful document check
        checker.check_availability.return_value = DocumentAvailabilityResult(
            is_ready=True,
            available_documents=["insurance_policy", "benefits_summary"],
            missing_documents=[],
            document_status={"insurance_policy": True, "benefits_summary": True}
        )
        
        return checker
    
    @pytest.fixture
    def workflow(self, mock_workflow_agent, mock_document_checker):
        """Create SupervisorWorkflow with mocked components."""
        workflow = SupervisorWorkflow(use_mock=True)
        workflow.workflow_agent = mock_workflow_agent
        workflow.document_checker = mock_document_checker
        return workflow
    
    @pytest.mark.asyncio
    async def test_execute_workflow_proceed(self, workflow):
        """Test workflow execution with PROCEED routing."""
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay for doctor visits?",
            user_id="test_user"
        )
        
        result = await workflow.execute(input_data)
        
        assert result.routing_decision == "PROCEED"
        assert result.prescribed_workflows == [WorkflowType.INFORMATION_RETRIEVAL]
        assert result.document_availability.is_ready is True
        assert result.confidence_score > 0
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_execute_workflow_collect(self, workflow, mock_document_checker):
        """Test workflow execution with COLLECT routing."""
        # Mock document checker to return not ready
        mock_document_checker.check_availability.return_value = DocumentAvailabilityResult(
            is_ready=False,
            available_documents=[],
            missing_documents=["insurance_policy", "benefits_summary"],
            document_status={"insurance_policy": False, "benefits_summary": False}
        )
        
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay for doctor visits?",
            user_id="test_user"
        )
        
        result = await workflow.execute(input_data)
        
        assert result.routing_decision == "COLLECT"
        assert result.prescribed_workflows == [WorkflowType.INFORMATION_RETRIEVAL]
        assert result.document_availability.is_ready is False
        assert len(result.document_availability.missing_documents) > 0
    
    @pytest.mark.asyncio
    async def test_execute_workflow_error_handling(self, workflow, mock_workflow_agent):
        """Test workflow execution with error handling."""
        # Mock workflow agent to raise exception
        mock_workflow_agent.prescribe_workflows.side_effect = Exception("Test error")
        
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay for doctor visits?",
            user_id="test_user"
        )
        
        result = await workflow.execute(input_data)
        
        # Should still return a result with fallback values
        assert result.routing_decision == "COLLECT"  # Default on error
        assert result.prescribed_workflows == [WorkflowType.INFORMATION_RETRIEVAL]  # Fallback
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_performance_tracking(self, workflow):
        """Test performance tracking in workflow execution."""
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay for doctor visits?",
            user_id="test_user"
        )
        
        result = await workflow.execute(input_data)
        
        # Verify performance tracking
        assert result.processing_time > 0
        assert result.processing_time < 5.0  # Should complete quickly in test
    
    @pytest.mark.asyncio
    async def test_mock_mode_execution(self):
        """Test workflow execution in mock mode."""
        workflow = SupervisorWorkflow(use_mock=True)
        
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay for doctor visits?",
            user_id="test_user"
        )
        
        result = await workflow.execute(input_data)
        
        # Should complete successfully with mock responses
        assert result.routing_decision in ["PROCEED", "COLLECT"]
        assert len(result.prescribed_workflows) > 0
        assert result.processing_time > 0


class TestIntegration:
    """Integration tests for Phase 2 components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_mock_execution(self):
        """Test end-to-end execution with all components in mock mode."""
        workflow = SupervisorWorkflow(use_mock=True)
        
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay for doctor visits?",
            user_id="test_user"
        )
        
        result = await workflow.execute(input_data)
        
        # Verify complete workflow execution
        assert result.routing_decision in ["PROCEED", "COLLECT"]
        assert result.prescribed_workflows
        assert result.document_availability
        assert result.workflow_prescription
        assert result.next_steps
        assert result.confidence_score >= 0
        assert result.processing_time > 0
        
        # Verify performance requirements
        assert result.processing_time < 2.0  # <2 second requirement
    
    @pytest.mark.asyncio
    async def test_various_query_types(self):
        """Test workflow with various query types."""
        workflow = SupervisorWorkflow(use_mock=True)
        
        test_queries = [
            "What is my copay for doctor visits?",
            "How do I find a doctor in my network?",
            "What's my deductible and how can I save money?",
            "I'm confused about my insurance"
        ]
        
        for query in test_queries:
            input_data = SupervisorWorkflowInput(
                user_query=query,
                user_id="test_user"
            )
            
            result = await workflow.execute(input_data)
            
            # Verify basic requirements
            assert result.routing_decision in ["PROCEED", "COLLECT"]
            assert result.prescribed_workflows
            assert result.processing_time < 2.0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 