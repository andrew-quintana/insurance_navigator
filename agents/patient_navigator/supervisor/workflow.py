"""
LangGraph Supervisor Workflow for Patient Navigator.

This module implements the supervisor workflow using LangGraph for orchestration,
coordinating workflow prescription and document availability checking.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from langgraph.graph import StateGraph

from .models import (
    SupervisorState, 
    SupervisorWorkflowInput, 
    SupervisorWorkflowOutput,
    WorkflowType,
    DocumentAvailabilityResult
)
from .workflow_prescription import WorkflowPrescriptionAgent
from .document_availability import DocumentAvailabilityChecker





class SupervisorWorkflow:
    """
    LangGraph supervisor workflow for patient navigator orchestration.
    
    This workflow coordinates workflow prescription and document availability
    checking to make routing decisions for user requests.
    """
    
    def __init__(self, use_mock: bool = False):
        """
        Initialize the supervisor workflow.
        
        Args:
            use_mock: If True, use mock responses for testing
        """
        self.use_mock = use_mock
        self.logger = logging.getLogger("supervisor_workflow")
        
        # Initialize components
        self.workflow_agent = WorkflowPrescriptionAgent(use_mock=use_mock)
        self.document_checker = DocumentAvailabilityChecker(use_mock=use_mock)
        
        # Build LangGraph workflow
        self.graph = self._build_workflow_graph()
    
    def _build_workflow_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow with nodes and edges.
        
        Returns:
            Compiled StateGraph for workflow execution
        """
        # Create state graph with SupervisorState
        workflow = StateGraph(SupervisorState)
        
        # Add nodes
        workflow.add_node("prescribe_workflow", self._prescribe_workflow_node)
        workflow.add_node("check_documents", self._check_documents_node)
        workflow.add_node("route_decision", self._route_decision_node)
        
        # Add edges for sequential flow
        workflow.add_edge("prescribe_workflow", "check_documents")
        workflow.add_edge("check_documents", "route_decision")
        
        # Set entry point
        workflow.set_entry_point("prescribe_workflow")
        
        # Compile the workflow
        return workflow.compile()
    
    async def _prescribe_workflow_node(self, state: SupervisorState) -> SupervisorState:
        """
        LangGraph node for workflow prescription.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with prescribed workflows
        """
        node_start_time = time.time()
        
        try:
            self.logger.info("Executing workflow prescription node")
            
            # Use workflow prescription agent
            prescription_result = await self.workflow_agent.prescribe_workflows(state.user_query)
            
            # Update state with prescription results
            state.prescribed_workflows = prescription_result.prescribed_workflows
            
            node_time = time.time() - node_start_time
            self.logger.info(f"Prescribed workflows: {state.prescribed_workflows} (took {node_time:.2f}s)")
            
            # Track performance
            if state.node_performance is None:
                state.node_performance = {}
            state.node_performance['prescribe_workflow'] = node_time
            
            return state
            
        except Exception as e:
            node_time = time.time() - node_start_time
            self.logger.error(f"Error in workflow prescription node after {node_time:.2f}s: {e}")
            state.error_message = f"Workflow prescription failed: {str(e)}"
            # Set default prescription with low confidence
            state.prescribed_workflows = [WorkflowType.INFORMATION_RETRIEVAL]
            
            # Track error performance
            if state.node_performance is None:
                state.node_performance = {}
            state.node_performance['prescribe_workflow'] = node_time
            
            return state
    
    async def _check_documents_node(self, state: SupervisorState) -> SupervisorState:
        """
        LangGraph node for document availability checking.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with document availability results
        """
        node_start_time = time.time()
        
        try:
            self.logger.info("Executing document availability check node")
            
            if not state.prescribed_workflows:
                self.logger.warning("No prescribed workflows for document checking")
                state.document_availability = DocumentAvailabilityResult(
                    is_ready=False,
                    available_documents=[],
                    missing_documents=[],
                    document_status={}
                )
                return state
            
            # Check document availability for prescribed workflows
            availability_result = await self.document_checker.check_availability(
                state.prescribed_workflows, 
                state.user_id
            )
            
            # Update state with availability results
            state.document_availability = availability_result
            
            node_time = time.time() - node_start_time
            self.logger.info(f"Document availability: ready={availability_result.is_ready} (took {node_time:.2f}s)")
            
            # Track performance
            if state.node_performance is None:
                state.node_performance = {}
            state.node_performance['check_documents'] = node_time
            
            return state
            
        except Exception as e:
            node_time = time.time() - node_start_time
            self.logger.error(f"Error in document availability check node after {node_time:.2f}s: {e}")
            state.error_message = f"Document availability check failed: {str(e)}"
            # Set default availability (not ready)
            state.document_availability = DocumentAvailabilityResult(
                is_ready=False,
                available_documents=[],
                missing_documents=[],
                document_status={}
            )
            
            # Track error performance
            if state.node_performance is None:
                state.node_performance = {}
            state.node_performance['check_documents'] = node_time
            
            return state
    
    async def _route_decision_node(self, state: SupervisorState) -> SupervisorState:
        """
        LangGraph node for routing decision.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with routing decision
        """
        node_start_time = time.time()
        
        try:
            self.logger.info("Executing routing decision node")
            
            # Check for error state first - default to COLLECT on any error
            if state.error_message:
                routing_decision = "COLLECT"
                self.logger.info(f"Routing decision: COLLECT - error occurred: {state.error_message}")
            # Determine routing decision based on prescription and document availability
            elif state.document_availability and state.document_availability.is_ready:
                routing_decision = "PROCEED"
                self.logger.info("Routing decision: PROCEED - documents ready")
            else:
                routing_decision = "COLLECT"
                missing_docs = state.document_availability.missing_documents if state.document_availability else []
                self.logger.info(f"Routing decision: COLLECT - documents missing: {missing_docs}")
            
            # Update state with routing decision
            state.routing_decision = routing_decision
            
            node_time = time.time() - node_start_time
            self.logger.info(f"Routing decision completed in {node_time:.2f}s")
            
            # Track performance
            if state.node_performance is None:
                state.node_performance = {}
            state.node_performance['route_decision'] = node_time
            
            return state
            
        except Exception as e:
            node_time = time.time() - node_start_time
            self.logger.error(f"Error in routing decision node after {node_time:.2f}s: {e}")
            state.error_message = f"Routing decision failed: {str(e)}"
            # Default to COLLECT on error
            state.routing_decision = "COLLECT"
            
            # Track error performance
            if state.node_performance is None:
                state.node_performance = {}
            state.node_performance['route_decision'] = node_time
            
            return state
    
    async def execute(self, input_data: SupervisorWorkflowInput) -> SupervisorWorkflowOutput:
        """
        Execute the supervisor workflow.
        
        Args:
            input_data: Structured input for the workflow
            
        Returns:
            SupervisorWorkflowOutput with routing decision and results
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting supervisor workflow for user {input_data.user_id}")
            
            # Initialize workflow state
            initial_state = SupervisorState(
                user_query=input_data.user_query,
                user_id=input_data.user_id,
                workflow_context=input_data.workflow_context
            )
            
            # Execute LangGraph workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create output
            output = self._create_output(final_state, processing_time)
            
            self.logger.info(f"Supervisor workflow completed in {processing_time:.2f}s")
            return output
            
        except Exception as e:
            self.logger.error(f"Supervisor workflow execution failed: {e}")
            processing_time = time.time() - start_time
            
            # Create error output
            error_state = SupervisorState(
                user_query=input_data.user_query,
                user_id=input_data.user_id,
                workflow_context=input_data.workflow_context,
                error_message=str(e),
                routing_decision="COLLECT"  # Default to COLLECT on error
            )
            
            return self._create_output(error_state, processing_time)
    
    def _create_output(self, state: SupervisorState, processing_time: float) -> SupervisorWorkflowOutput:
        """
        Create SupervisorWorkflowOutput from workflow state.
        
        Args:
            state: Final workflow state
            processing_time: Total processing time
            
        Returns:
            SupervisorWorkflowOutput with results
        """
        # Extract prescription results - handle both SupervisorState and AddableValuesDict
        if hasattr(state, 'prescribed_workflows'):
            prescribed_workflows = state.prescribed_workflows or [WorkflowType.INFORMATION_RETRIEVAL]
        else:
            # Handle AddableValuesDict case
            prescribed_workflows = state.get('prescribed_workflows', [WorkflowType.INFORMATION_RETRIEVAL])
        
        # Create workflow prescription result
        from .models import WorkflowPrescriptionResult
        workflow_prescription = WorkflowPrescriptionResult(
            prescribed_workflows=prescribed_workflows,
            confidence_score=0.8,  # Default confidence
            reasoning="Workflow prescription completed",
            execution_order=prescribed_workflows  # Simple order for MVP
        )
        
        # Extract document availability - handle both SupervisorState and AddableValuesDict
        if hasattr(state, 'document_availability'):
            document_availability = state.document_availability
        else:
            # Handle AddableValuesDict case
            doc_avail = state.get('document_availability')
            if doc_avail is None:
                document_availability = DocumentAvailabilityResult(
                    is_ready=False,
                    available_documents=[],
                    missing_documents=[],
                    document_status={}
                )
            else:
                document_availability = doc_avail
        
        # Extract routing decision - handle both SupervisorState and AddableValuesDict
        if hasattr(state, 'routing_decision'):
            routing_decision = state.routing_decision or "COLLECT"
        else:
            # Handle AddableValuesDict case
            routing_decision = state.get('routing_decision', "COLLECT")
        
        # Determine next steps
        next_steps = self._determine_next_steps(state)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(state)
        
        return SupervisorWorkflowOutput(
            routing_decision=routing_decision,
            prescribed_workflows=prescribed_workflows,
            execution_order=prescribed_workflows,  # Same as prescribed for MVP
            document_availability=document_availability,
            workflow_prescription=workflow_prescription,
            next_steps=next_steps,
            confidence_score=confidence_score,
            processing_time=processing_time
        )
    
    def _determine_next_steps(self, state: SupervisorState) -> List[str]:
        """
        Determine next steps based on routing decision.
        
        Args:
            state: Workflow state
            
        Returns:
            List of next steps for the user
        """
        # Extract routing decision - handle both SupervisorState and AddableValuesDict
        if hasattr(state, 'routing_decision'):
            routing_decision = state.routing_decision
        else:
            routing_decision = state.get('routing_decision', "COLLECT")
        
        if routing_decision == "PROCEED":
            return ["Proceeding with prescribed workflows"]
        else:
            # Extract document availability - handle both SupervisorState and AddableValuesDict
            if hasattr(state, 'document_availability'):
                doc_avail = state.document_availability
            else:
                doc_avail = state.get('document_availability')
            
            missing_docs = doc_avail.missing_documents if doc_avail else []
            if missing_docs:
                return [f"Please upload the following documents: {', '.join(missing_docs)}"]
            else:
                return ["Please upload required documents before proceeding"]
    
    def _calculate_confidence_score(self, state: SupervisorState) -> float:
        """
        Calculate overall confidence score for the routing decision.
        
        Args:
            state: Workflow state
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # Simple confidence calculation for MVP
        if hasattr(state, 'error_message') and state.error_message:
            return 0.3  # Low confidence if there were errors
        elif not hasattr(state, 'error_message') and state.get('error_message'):
            return 0.3  # Low confidence if there were errors
        
        # Extract document availability - handle both SupervisorState and AddableValuesDict
        if hasattr(state, 'document_availability'):
            doc_avail = state.document_availability
        else:
            doc_avail = state.get('document_availability')
        
        if doc_avail and doc_avail.is_ready:
            return 0.9  # High confidence if documents are ready
        
        return 0.7  # Medium confidence for COLLECT decisions 