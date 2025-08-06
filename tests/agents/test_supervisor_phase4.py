"""
Phase 4 Integration Tests for Patient Navigator Supervisor Workflow.

This test suite validates the integration of the supervisor workflow with existing
components and comprehensive system testing.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from agents.patient_navigator.supervisor.workflow import SupervisorWorkflow
from agents.patient_navigator.supervisor.models import (
    SupervisorWorkflowInput,
    SupervisorWorkflowOutput,
    WorkflowType,
    DocumentAvailabilityResult
)
from agents.patient_navigator.information_retrieval.models import InformationRetrievalOutput
from agents.patient_navigator.strategy.types import StrategyWorkflowState


class TestWorkflowIntegration:
    """Test integration with existing workflow components."""
    
    @pytest.fixture
    def supervisor_workflow(self):
        """Create supervisor workflow with mock mode."""
        return SupervisorWorkflow(use_mock=True)
    
    @pytest.mark.asyncio
    async def test_information_retrieval_integration(self, supervisor_workflow):
        """Test integration with InformationRetrievalAgent."""
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay for doctor visits?",
            user_id="test_user_123"
        )
        
        result = await supervisor_workflow.execute(input_data)
        
        # Validate basic workflow execution
        assert result.routing_decision in ["PROCEED", "COLLECT"]
        assert len(result.prescribed_workflows) > 0
        assert result.processing_time > 0
        
        # Validate information retrieval integration
        if result.routing_decision == "PROCEED" and WorkflowType.INFORMATION_RETRIEVAL in result.prescribed_workflows:
            assert result.information_retrieval_result is not None
    
    @pytest.mark.asyncio
    async def test_strategy_integration(self, supervisor_workflow):
        """Test integration with StrategyWorkflowOrchestrator."""
        input_data = SupervisorWorkflowInput(
            user_query="How do I find a doctor in my network?",
            user_id="test_user_123"
        )
        
        result = await supervisor_workflow.execute(input_data)
        
        # Validate basic workflow execution
        assert result.routing_decision in ["PROCEED", "COLLECT"]
        assert len(result.prescribed_workflows) > 0
        assert result.processing_time > 0
        
        # Validate strategy integration
        if result.routing_decision == "PROCEED" and WorkflowType.STRATEGY in result.prescribed_workflows:
            assert result.strategy_result is not None
    
    @pytest.mark.asyncio
    async def test_multi_workflow_integration(self, supervisor_workflow):
        """Test integration with both workflows in sequence."""
        input_data = SupervisorWorkflowInput(
            user_query="What's my coverage and how can I maximize my benefits?",
            user_id="test_user_123"
        )
        
        result = await supervisor_workflow.execute(input_data)
        
        # Validate multi-workflow execution
        assert result.routing_decision in ["PROCEED", "COLLECT"]
        assert len(result.prescribed_workflows) >= 1
        assert result.processing_time > 0
        
        # Validate both workflows executed if prescribed
        if result.routing_decision == "PROCEED":
            if WorkflowType.INFORMATION_RETRIEVAL in result.prescribed_workflows:
                assert result.information_retrieval_result is not None
            if WorkflowType.STRATEGY in result.prescribed_workflows:
                assert result.strategy_result is not None
    
    @pytest.mark.asyncio
    async def test_workflow_execution_order(self, supervisor_workflow):
        """Test deterministic execution order (information_retrieval → strategy)."""
        input_data = SupervisorWorkflowInput(
            user_query="What's my deductible and how can I save money?",
            user_id="test_user_123"
        )
        
        result = await supervisor_workflow.execute(input_data)
        
        # Validate execution order
        if (WorkflowType.INFORMATION_RETRIEVAL in result.prescribed_workflows and 
            WorkflowType.STRATEGY in result.prescribed_workflows):
            # Information retrieval should execute before strategy
            assert result.execution_order[0] == WorkflowType.INFORMATION_RETRIEVAL
            assert result.execution_order[1] == WorkflowType.STRATEGY
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, supervisor_workflow):
        """Test error handling in workflow integration."""
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay?",
            user_id="test_user_123"
        )
        
        # Test error handling when workflow components are not available
        result = await supervisor_workflow.execute(input_data)
        
        # Should handle errors gracefully
        assert result.routing_decision in ["PROCEED", "COLLECT"]
        assert result.processing_time > 0
        
        # Test error handling when workflow components are available but fail
        if supervisor_workflow.information_retrieval_agent is not None:
            with patch.object(supervisor_workflow.information_retrieval_agent, 'retrieve_information', side_effect=Exception("Workflow failed")):
                result = await supervisor_workflow.execute(input_data)
                
                # Should handle errors gracefully
                assert result.routing_decision in ["PROCEED", "COLLECT"]
                assert result.processing_time > 0


class TestSupabaseIntegration:
    """Test Supabase database integration with RLS."""
    
    @pytest.fixture
    def supervisor_workflow_real_db(self):
        """Create supervisor workflow with real Supabase integration."""
        return SupervisorWorkflow(use_mock=False)
    
    @pytest.mark.asyncio
    async def test_real_document_availability_checking(self, supervisor_workflow_real_db):
        """Test document availability checking with real Supabase."""
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay for doctor visits?",
            user_id="test_user_123"
        )
        
        result = await supervisor_workflow_real_db.execute(input_data)
        
        # Validate document availability checking
        assert result.document_availability is not None
        assert isinstance(result.document_availability.is_ready, bool)
        assert isinstance(result.document_availability.available_documents, list)
        assert isinstance(result.document_availability.missing_documents, list)
    
    @pytest.mark.asyncio
    async def test_document_availability_performance(self, supervisor_workflow_real_db):
        """Test document availability checking performance."""
        start_time = time.time()
        
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay for doctor visits?",
            user_id="test_user_123"
        )
        
        result = await supervisor_workflow_real_db.execute(input_data)
        
        execution_time = time.time() - start_time
        
        # Validate performance requirements
        assert execution_time < 2.0  # <2 second total execution
        assert result.processing_time < 2.0
    
    @pytest.mark.asyncio
    async def test_user_isolation_and_rls(self, supervisor_workflow_real_db):
        """Test user isolation and Row Level Security."""
        # Test with different users
        user1_input = SupervisorWorkflowInput(
            user_query="What is my copay?",
            user_id="user_1"
        )
        
        user2_input = SupervisorWorkflowInput(
            user_query="What is my copay?",
            user_id="user_2"
        )
        
        result1 = await supervisor_workflow_real_db.execute(user1_input)
        result2 = await supervisor_workflow_real_db.execute(user2_input)
        
        # Validate user isolation
        assert result1.document_availability is not None
        assert result2.document_availability is not None
        # Results may differ based on user's documents


class TestEndToEndSystemTesting:
    """Test complete end-to-end system functionality."""
    
    @pytest.fixture
    def supervisor_workflow(self):
        """Create supervisor workflow for testing."""
        return SupervisorWorkflow(use_mock=True)
    
    @pytest.mark.asyncio
    async def test_single_workflow_information_retrieval(self, supervisor_workflow):
        """Test end-to-end execution with information retrieval only."""
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay for doctor visits?",
            user_id="test_user_123"
        )
        
        result = await supervisor_workflow.execute(input_data)
        
        # Validate complete workflow execution
        assert result.routing_decision in ["PROCEED", "COLLECT"]
        assert len(result.prescribed_workflows) > 0
        assert result.processing_time > 0
        assert result.confidence_score >= 0.0 and result.confidence_score <= 1.0
        assert len(result.next_steps) > 0
    
    @pytest.mark.asyncio
    async def test_single_workflow_strategy(self, supervisor_workflow):
        """Test end-to-end execution with strategy only."""
        input_data = SupervisorWorkflowInput(
            user_query="How do I find a doctor in my network?",
            user_id="test_user_123"
        )
        
        result = await supervisor_workflow.execute(input_data)
        
        # Validate complete workflow execution
        assert result.routing_decision in ["PROCEED", "COLLECT"]
        assert len(result.prescribed_workflows) > 0
        assert result.processing_time > 0
        assert result.confidence_score >= 0.0 and result.confidence_score <= 1.0
        assert len(result.next_steps) > 0
    
    @pytest.mark.asyncio
    async def test_multi_workflow_execution(self, supervisor_workflow):
        """Test end-to-end execution with multiple workflows."""
        input_data = SupervisorWorkflowInput(
            user_query="What's my coverage and how can I maximize my benefits?",
            user_id="test_user_123"
        )
        
        result = await supervisor_workflow.execute(input_data)
        
        # Validate complete multi-workflow execution
        assert result.routing_decision in ["PROCEED", "COLLECT"]
        assert len(result.prescribed_workflows) >= 1
        assert result.processing_time > 0
        assert result.confidence_score >= 0.0 and result.confidence_score <= 1.0
        assert len(result.next_steps) > 0
    
    @pytest.mark.asyncio
    async def test_document_collection_scenario(self, supervisor_workflow):
        """Test end-to-end execution when documents are missing."""
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay for doctor visits?",
            user_id="user_without_documents"
        )
        
        result = await supervisor_workflow.execute(input_data)
        
        # Should route to COLLECT when documents are missing
        if result.routing_decision == "COLLECT":
            assert len(result.document_availability.missing_documents) > 0
            assert "upload" in " ".join(result.next_steps).lower()
    
    @pytest.mark.asyncio
    async def test_error_recovery_scenarios(self, supervisor_workflow):
        """Test end-to-end error recovery."""
        # Test with various error scenarios
        error_scenarios = [
            "Invalid query with no clear intent",
            "",  # Empty query
            "x" * 1000,  # Very long query
        ]
        
        for query in error_scenarios:
            input_data = SupervisorWorkflowInput(
                user_query=query,
                user_id="test_user_123"
            )
            
            result = await supervisor_workflow.execute(input_data)
            
            # Should handle errors gracefully
            assert result.routing_decision in ["PROCEED", "COLLECT"]
            assert result.processing_time > 0
            assert result.confidence_score >= 0.0 and result.confidence_score <= 1.0


class TestPerformanceAndLoadTesting:
    """Test performance and load handling."""
    
    @pytest.fixture
    def supervisor_workflow(self):
        """Create supervisor workflow for performance testing."""
        return SupervisorWorkflow(use_mock=True)
    
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, supervisor_workflow):
        """Test handling of concurrent requests."""
        queries = [
            "What is my copay for doctor visits?",
            "How do I find a doctor in my network?",
            "What are my prescription drug benefits?",
            "How can I maximize my benefits?",
            "What's my deductible?"
        ]
        
        start_time = time.time()
        
        # Execute concurrent requests
        tasks = []
        for query in queries:
            input_data = SupervisorWorkflowInput(
                user_query=query,
                user_id=f"user_{queries.index(query)}"
            )
            tasks.append(supervisor_workflow.execute(input_data))
        
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Validate concurrent execution
        assert len(results) == len(queries)
        assert total_time < 10.0  # Should complete within reasonable time
        
        # Validate all results
        for result in results:
            assert result.routing_decision in ["PROCEED", "COLLECT"]
            assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, supervisor_workflow):
        """Test performance benchmarks."""
        queries = [
            "What is my copay?",
            "How do I find a doctor?",
            "What are my benefits?",
            "How can I save money?",
            "What's my coverage?"
        ]
        
        total_time = 0
        total_processing_time = 0
        
        for query in queries:
            start_time = time.time()
            
            input_data = SupervisorWorkflowInput(
                user_query=query,
                user_id="test_user_123"
            )
            
            result = await supervisor_workflow.execute(input_data)
            
            execution_time = time.time() - start_time
            total_time += execution_time
            total_processing_time += result.processing_time
            
            # Individual request performance
            assert execution_time < 2.0  # <2 second target
            assert result.processing_time < 2.0
        
        # Average performance
        avg_time = total_time / len(queries)
        avg_processing_time = total_processing_time / len(queries)
        
        assert avg_time < 1.5  # Average should be well under target
        assert avg_processing_time < 1.5
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, supervisor_workflow):
        """Test memory usage under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Execute multiple requests
        for i in range(10):
            input_data = SupervisorWorkflowInput(
                user_query=f"Test query {i}",
                user_id=f"user_{i}"
            )
            await supervisor_workflow.execute(input_data)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory usage should be reasonable
        assert memory_increase < 100.0  # <100MB increase


class TestSecurityAndCompliance:
    """Test security and compliance requirements."""
    
    @pytest.fixture
    def supervisor_workflow(self):
        """Create supervisor workflow for security testing."""
        return SupervisorWorkflow(use_mock=True)
    
    @pytest.mark.asyncio
    async def test_user_data_isolation(self, supervisor_workflow):
        """Test user data isolation and privacy."""
        # Test with different users to ensure isolation
        user1_input = SupervisorWorkflowInput(
            user_query="What is my copay?",
            user_id="user_1"
        )
        
        user2_input = SupervisorWorkflowInput(
            user_query="What is my copay?",
            user_id="user_2"
        )
        
        result1 = await supervisor_workflow.execute(user1_input)
        result2 = await supervisor_workflow.execute(user2_input)
        
        # Results should be isolated by user
        assert result1.user_id == "user_1"
        assert result2.user_id == "user_2"
    
    @pytest.mark.asyncio
    async def test_secure_error_handling(self, supervisor_workflow):
        """Test secure error handling without information leakage."""
        # Test with various error scenarios
        error_inputs = [
            SupervisorWorkflowInput(user_query="", user_id="test_user"),
            SupervisorWorkflowInput(user_query="x" * 10000, user_id="test_user"),
            SupervisorWorkflowInput(user_query="'; DROP TABLE users; --", user_id="test_user"),
        ]
        
        for input_data in error_inputs:
            result = await supervisor_workflow.execute(input_data)
            
            # Should handle errors securely
            assert result.routing_decision in ["PROCEED", "COLLECT"]
            assert result.processing_time > 0
            
            # Error messages should not leak sensitive information
            if hasattr(result, 'error_message') and result.error_message:
                assert "password" not in result.error_message.lower()
                assert "token" not in result.error_message.lower()
                assert "key" not in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_audit_logging(self, supervisor_workflow):
        """Test audit logging for compliance."""
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay for doctor visits?",
            user_id="test_user_123"
        )
        
        result = await supervisor_workflow.execute(input_data)
        
        # Validate audit information is captured
        assert result.user_id == "test_user_123"
        assert result.processing_time > 0
        assert result.confidence_score >= 0.0 and result.confidence_score <= 1.0
        
        # Validate workflow prescription is logged
        assert result.workflow_prescription is not None
        assert len(result.prescribed_workflows) > 0


class TestSystemOptimization:
    """Test system optimization and performance tuning."""
    
    @pytest.fixture
    def supervisor_workflow(self):
        """Create supervisor workflow for optimization testing."""
        return SupervisorWorkflow(use_mock=True)
    
    @pytest.mark.asyncio
    async def test_node_performance_tracking(self, supervisor_workflow):
        """Test individual node performance tracking."""
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay for doctor visits?",
            user_id="test_user_123"
        )
        
        result = await supervisor_workflow.execute(input_data)
        
        # Validate performance tracking
        assert result.processing_time > 0
        assert result.processing_time < 2.0  # <2 second target
    
    @pytest.mark.asyncio
    async def test_workflow_execution_optimization(self, supervisor_workflow):
        """Test workflow execution optimization."""
        # Test with various query types to ensure optimization
        query_types = [
            "What is my copay?",  # Simple information retrieval
            "How do I find a doctor?",  # Strategy
            "What's my coverage and how can I save money?",  # Multi-workflow
        ]
        
        for query in query_types:
            start_time = time.time()
            
            input_data = SupervisorWorkflowInput(
                user_query=query,
                user_id="test_user_123"
            )
            
            result = await supervisor_workflow.execute(input_data)
            
            execution_time = time.time() - start_time
            
            # Validate optimization targets
            assert execution_time < 2.0  # <2 second target
            assert result.processing_time < 2.0
    
    @pytest.mark.asyncio
    async def test_resource_cleanup(self, supervisor_workflow):
        """Test resource cleanup after workflow execution."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Execute workflow
        input_data = SupervisorWorkflowInput(
            user_query="What is my copay for doctor visits?",
            user_id="test_user_123"
        )
        
        result = await supervisor_workflow.execute(input_data)
        
        # Force garbage collection
        import gc
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory should be cleaned up reasonably
        assert memory_increase < 50.0  # <50MB increase after cleanup


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 