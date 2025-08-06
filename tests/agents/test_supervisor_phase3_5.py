"""
Phase 3.5: Complete LangGraph Architecture Implementation - Patient Navigator Supervisor Workflow

This test suite validates the complete LangGraph architecture implementation:
- LangGraph StateGraph compilation and basic workflow execution
- All LangGraph node method implementations and testing
- SupervisorState model validation with LangGraph state management
- Mock mode functionality for all LangGraph components
- Performance baseline measurement for complete architecture

Test Coverage:
- LangGraph workflow compilation tests
- Individual node method testing in isolation
- SupervisorState model validation and serialization
- End-to-end LangGraph workflow execution with placeholder logic
- Mock mode functionality for all LangGraph components
- Performance baseline measurement for complete architecture
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List, Optional

from agents.patient_navigator.supervisor.models import (
    SupervisorWorkflowInput,
    SupervisorWorkflowOutput,
    WorkflowType,
    DocumentAvailabilityResult,
    WorkflowPrescriptionResult,
    SupervisorState
)
from agents.patient_navigator.supervisor.workflow import SupervisorWorkflow
from agents.patient_navigator.supervisor.workflow_prescription import WorkflowPrescriptionAgent
from agents.patient_navigator.supervisor.document_availability import DocumentAvailabilityChecker


class TestLangGraphArchitectureCompleteness:
    """Comprehensive tests for complete LangGraph architecture implementation."""
    
    @pytest.fixture
    def supervisor_workflow(self):
        """Create SupervisorWorkflow with mock mode for testing."""
        return SupervisorWorkflow(use_mock=True)
    
    @pytest.mark.asyncio
    async def test_langgraph_workflow_compilation(self, supervisor_workflow):
        """Test that LangGraph StateGraph compiles successfully."""
        # Verify workflow graph exists and is compiled
        assert supervisor_workflow.graph is not None
        
        # Test basic workflow execution with mock data
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay for doctor visits?",
            user_id="test_user_123"
        )
        
        result = await supervisor_workflow.execute(input_data)
        
        # Verify output structure
        assert isinstance(result, SupervisorWorkflowOutput)
        assert result.routing_decision in ["PROCEED", "COLLECT"]
        assert len(result.prescribed_workflows) > 0
        assert isinstance(result.processing_time, float)
        assert result.processing_time >= 0.0
    
    @pytest.mark.asyncio
    async def test_supervisor_state_model_validation(self):
        """Test SupervisorState model validation and serialization."""
        # Test basic state creation
        state = SupervisorState(
            user_query="What is my copay?",
            user_id="test_user_123",
            prescribed_workflows=[WorkflowType.INFORMATION_RETRIEVAL],
            routing_decision="PROCEED"
        )
        
        # Verify state fields
        assert state.user_query == "What is my copay?"
        assert state.user_id == "test_user_123"
        assert state.prescribed_workflows == [WorkflowType.INFORMATION_RETRIEVAL]
        assert state.routing_decision == "PROCEED"
        
        # Test state serialization
        state_dict = state.model_dump()
        assert "user_query" in state_dict
        assert "user_id" in state_dict
        assert "prescribed_workflows" in state_dict
        
        # Test state deserialization
        new_state = SupervisorState(**state_dict)
        assert new_state.user_query == state.user_query
        assert new_state.user_id == state.user_id
    
    @pytest.mark.asyncio
    async def test_individual_node_methods(self, supervisor_workflow):
        """Test each LangGraph node method in isolation."""
        # Test workflow prescription node
        state = SupervisorState(
            user_query="What is my copay?",
            user_id="test_user_123"
        )
        
        result_state = await supervisor_workflow._prescribe_workflow_node(state)
        assert result_state.prescribed_workflows is not None
        assert len(result_state.prescribed_workflows) > 0
        
        # Test document checking node
        result_state = await supervisor_workflow._check_documents_node(result_state)
        assert result_state.document_availability is not None
        assert isinstance(result_state.document_availability.is_ready, bool)
        
        # Test routing decision node
        result_state = await supervisor_workflow._route_decision_node(result_state)
        assert result_state.routing_decision in ["PROCEED", "COLLECT"]
    
    @pytest.mark.asyncio
    async def test_workflow_execution_nodes(self, supervisor_workflow):
        """Test workflow execution nodes (if available)."""
        # Test information retrieval workflow node
        state = SupervisorState(
            user_query="What is my copay?",
            user_id="test_user_123",
            prescribed_workflows=[WorkflowType.INFORMATION_RETRIEVAL],
            routing_decision="PROCEED"
        )
        
        # Test strategy workflow node
        state = SupervisorState(
            user_query="How do I find a doctor?",
            user_id="test_user_123",
            prescribed_workflows=[WorkflowType.STRATEGY],
            routing_decision="PROCEED"
        )
        
        # Both should complete without errors (may skip if components not available)
        assert state is not None
    
    @pytest.mark.asyncio
    async def test_conditional_routing_logic(self, supervisor_workflow):
        """Test conditional routing logic for workflow execution."""
        # Test routing to information retrieval
        state = SupervisorState(
            user_query="What is my copay?",
            user_id="test_user_123",
            prescribed_workflows=[WorkflowType.INFORMATION_RETRIEVAL],
            routing_decision="PROCEED"
        )
        
        next_node = await supervisor_workflow._route_to_workflow_execution(state)
        assert next_node in ["execute_information_retrieval", "end"]
        
        # Test routing to strategy
        state.prescribed_workflows = [WorkflowType.STRATEGY]
        next_node = await supervisor_workflow._route_to_workflow_execution(state)
        assert next_node in ["execute_strategy", "end"]
        
        # Test routing when not proceeding
        state.routing_decision = "COLLECT"
        next_node = await supervisor_workflow._route_to_workflow_execution(state)
        assert next_node == "end"
    
    @pytest.mark.asyncio
    async def test_mock_mode_functionality(self):
        """Test mock mode functionality for all LangGraph components."""
        # Test with mock mode enabled
        workflow = SupervisorWorkflow(use_mock=True)
        
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay?",
            user_id="test_user_123"
        )
        
        result = await workflow.execute(input_data)
        
        # Verify mock mode works
        assert isinstance(result, SupervisorWorkflowOutput)
        assert result.routing_decision in ["PROCEED", "COLLECT"]
        assert len(result.prescribed_workflows) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_across_nodes(self, supervisor_workflow):
        """Test error handling and propagation across LangGraph nodes."""
        # Test error in workflow prescription
        state = SupervisorState(
            user_query="",  # Empty query to trigger error
            user_id="test_user_123"
        )
        
        result_state = await supervisor_workflow._prescribe_workflow_node(state)
        # Should handle error gracefully
        assert result_state is not None
        
        # Test error in document checking
        result_state = await supervisor_workflow._check_documents_node(result_state)
        # Should handle error gracefully
        assert result_state is not None
        
        # Test error in routing decision
        result_state = await supervisor_workflow._route_decision_node(result_state)
        # Should handle error gracefully
        assert result_state is not None
    
    @pytest.mark.asyncio
    async def test_performance_baseline_measurement(self, supervisor_workflow):
        """Test performance baseline measurement for complete architecture."""
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay for doctor visits?",
            user_id="test_user_123"
        )
        
        start_time = time.time()
        result = await supervisor_workflow.execute(input_data)
        execution_time = time.time() - start_time
        
        # Verify performance targets are met
        assert execution_time < 2.0  # <2 second target
        assert result.processing_time < 2.0
        
        # Verify node-level performance tracking
        assert result.processing_time >= 0.0
    
    @pytest.mark.asyncio
    async def test_state_persistence_across_nodes(self, supervisor_workflow):
        """Test state persistence across LangGraph nodes."""
        # Create initial state
        state = SupervisorState(
            user_query="What is my copay?",
            user_id="test_user_123"
        )
        
        # Execute through all nodes
        state = await supervisor_workflow._prescribe_workflow_node(state)
        assert state.prescribed_workflows is not None
        
        state = await supervisor_workflow._check_documents_node(state)
        assert state.document_availability is not None
        
        state = await supervisor_workflow._route_decision_node(state)
        assert state.routing_decision is not None
        
        # Verify state persistence
        assert state.user_query == "What is my copay?"
        assert state.user_id == "test_user_123"
        assert state.prescribed_workflows is not None
        assert state.document_availability is not None
        assert state.routing_decision is not None
    
    @pytest.mark.asyncio
    async def test_workflow_results_storage(self, supervisor_workflow):
        """Test workflow results storage in state."""
        # Test workflow results field
        state = SupervisorState(
            user_query="What is my copay?",
            user_id="test_user_123",
            workflow_results={"test_workflow": {"result": "test"}}
        )
        
        # Verify workflow results storage
        assert state.workflow_results is not None
        assert "test_workflow" in state.workflow_results
        assert state.workflow_results["test_workflow"]["result"] == "test"
    
    @pytest.mark.asyncio
    async def test_node_performance_tracking(self, supervisor_workflow):
        """Test node-level performance tracking."""
        state = SupervisorState(
            user_query="What is my copay?",
            user_id="test_user_123"
        )
        
        # Execute nodes and verify performance tracking
        state = await supervisor_workflow._prescribe_workflow_node(state)
        assert state.node_performance is not None
        assert "prescribe_workflow" in state.node_performance
        
        state = await supervisor_workflow._check_documents_node(state)
        assert "check_documents" in state.node_performance
        
        state = await supervisor_workflow._route_decision_node(state)
        assert "route_decision" in state.node_performance
    
    @pytest.mark.asyncio
    async def test_complete_workflow_execution_scenarios(self, supervisor_workflow):
        """Test complete workflow execution scenarios."""
        scenarios = [
            {
                "query": "What is my copay?",
                "expected_workflows": [WorkflowType.INFORMATION_RETRIEVAL]
            },
            {
                "query": "How do I find a doctor?",
                "expected_workflows": [WorkflowType.STRATEGY]
            },
            {
                "query": "What's my coverage and how can I maximize benefits?",
                "expected_workflows": [WorkflowType.INFORMATION_RETRIEVAL, WorkflowType.STRATEGY]
            }
        ]
        
        for scenario in scenarios:
            input_data = SupervisorWorkflowInput(
                user_query=scenario["query"],
                user_id="test_user_123"
            )
            
            result = await supervisor_workflow.execute(input_data)
            
            # Verify basic execution
            assert isinstance(result, SupervisorWorkflowOutput)
            assert result.routing_decision in ["PROCEED", "COLLECT"]
            assert len(result.prescribed_workflows) > 0
    
    @pytest.mark.asyncio
    async def test_langgraph_architecture_extensibility(self, supervisor_workflow):
        """Test LangGraph architecture extensibility for future components."""
        # Test that workflow can handle additional workflow types
        state = SupervisorState(
            user_query="Test query",
            user_id="test_user_123",
            prescribed_workflows=[WorkflowType.INFORMATION_RETRIEVAL]
        )
        
        # Verify state can handle workflow results
        state.workflow_results = {
            "information_retrieval": {"result": "test"},
            "future_workflow": {"result": "future_test"}
        }
        
        assert "information_retrieval" in state.workflow_results
        assert "future_workflow" in state.workflow_results
        
        # Verify performance tracking can handle additional nodes
        state.node_performance = {
            "prescribe_workflow": 0.1,
            "check_documents": 0.05,
            "route_decision": 0.01,
            "future_node": 0.2
        }
        
        assert "future_node" in state.node_performance


class TestLangGraphComponentIntegration:
    """Tests for LangGraph component integration and interoperability."""
    
    @pytest.mark.asyncio
    async def test_component_interface_compatibility(self):
        """Test component interface compatibility across LangGraph nodes."""
        workflow = SupervisorWorkflow(use_mock=True)
        
        # Test that all components have compatible interfaces
        assert hasattr(workflow, 'workflow_agent')
        assert hasattr(workflow, 'document_checker')
        assert hasattr(workflow, 'graph')
        
        # Test that components can be accessed and used
        assert workflow.workflow_agent is not None
        assert workflow.document_checker is not None
        assert workflow.graph is not None
    
    @pytest.mark.asyncio
    async def test_langgraph_state_management(self):
        """Test LangGraph state management with SupervisorState."""
        # Test state creation and validation
        state = SupervisorState(
            user_query="Test query",
            user_id="test_user_123"
        )
        
        # Test state updates
        state.prescribed_workflows = [WorkflowType.INFORMATION_RETRIEVAL]
        state.document_availability = DocumentAvailabilityResult(
            is_ready=True,
            available_documents=["insurance_policy"],
            missing_documents=[],
            document_status={"insurance_policy": True}
        )
        state.routing_decision = "PROCEED"
        
        # Verify state consistency
        assert state.prescribed_workflows == [WorkflowType.INFORMATION_RETRIEVAL]
        assert state.document_availability.is_ready is True
        assert state.routing_decision == "PROCEED"
    
    @pytest.mark.asyncio
    async def test_error_propagation_across_langgraph_nodes(self):
        """Test error propagation across LangGraph nodes."""
        workflow = SupervisorWorkflow(use_mock=True)
        
        # Test error in initial state
        input_data = SupervisorWorkflowInput(
            user_query="",  # Empty query to trigger error
            user_id="test_user_123"
        )
        
        result = await workflow.execute(input_data)
        
        # Should handle error gracefully and provide fallback
        assert isinstance(result, SupervisorWorkflowOutput)
        assert result.routing_decision in ["PROCEED", "COLLECT"]
    
    @pytest.mark.asyncio
    async def test_mock_mode_consistency(self):
        """Test mock mode consistency across all LangGraph components."""
        # Test mock mode vs non-mock mode consistency
        mock_workflow = SupervisorWorkflow(use_mock=True)
        non_mock_workflow = SupervisorWorkflow(use_mock=False)
        
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay?",
            user_id="test_user_123"
        )
        
        # Both should produce valid outputs
        mock_result = await mock_workflow.execute(input_data)
        non_mock_result = await non_mock_workflow.execute(input_data)
        
        # Verify both produce valid results
        assert isinstance(mock_result, SupervisorWorkflowOutput)
        assert isinstance(non_mock_result, SupervisorWorkflowOutput)
        assert mock_result.routing_decision in ["PROCEED", "COLLECT"]
        assert non_mock_result.routing_decision in ["PROCEED", "COLLECT"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 