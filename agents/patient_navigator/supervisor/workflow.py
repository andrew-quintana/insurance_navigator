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
        try:
            self.logger.info("Executing workflow prescription node")
            
            # Use workflow prescription agent
            prescription_result = await self.workflow_agent.prescribe_workflows(state.user_query)
            
            # Update state with prescription results
            state.prescribed_workflows = prescription_result.prescribed_workflows
            
            self.logger.info(f"Prescribed workflows: {state.prescribed_workflows}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in workflow prescription node: {e}")
            state.error_message = f"Workflow prescription failed: {str(e)}"
            # Set default prescription
            state.prescribed_workflows = [WorkflowType.INFORMATION_RETRIEVAL]
            return state
    
    async def _check_documents_node(self, state: SupervisorState) -> SupervisorState:
        """
        LangGraph node for document availability checking.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with document availability results
        """
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
            
            self.logger.info(f"Document availability: ready={availability_result.is_ready}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in document availability check node: {e}")
            state.error_message = f"Document availability check failed: {str(e)}"
            # Set default availability (not ready)
            state.document_availability = DocumentAvailabilityResult(
                is_ready=False,
                available_documents=[],
                missing_documents=[],
                document_status={}
            )
            return state
    
    async def _route_decision_node(self, state: SupervisorState) -> SupervisorState:
        """
        LangGraph node for routing decision.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with routing decision
        """
        try:
            self.logger.info("Executing routing decision node")
            
            # Determine routing decision based on prescription and document availability
            if state.document_availability and state.document_availability.is_ready:
                routing_decision = "PROCEED"
                self.logger.info("Routing decision: PROCEED - documents ready")
            else:
                routing_decision = "COLLECT"
                self.logger.info("Routing decision: COLLECT - documents missing")
            
            # Update state with routing decision
            state.routing_decision = routing_decision
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in routing decision node: {e}")
            state.error_message = f"Routing decision failed: {str(e)}"
            # Default to COLLECT on error
            state.routing_decision = "COLLECT"
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
        # Extract prescription results
        prescribed_workflows = state.prescribed_workflows or []
        workflow_prescription = None
        
        if prescribed_workflows:
            # Create workflow prescription result (simplified for MVP)
            workflow_prescription = {
                "prescribed_workflows": prescribed_workflows,
                "confidence_score": 0.8,  # Default confidence
                "reasoning": "Workflow prescription completed",
                "execution_order": prescribed_workflows  # Simple order for MVP
            }
        
        # Extract document availability
        document_availability = state.document_availability or DocumentAvailabilityResult(
            is_ready=False,
            available_documents=[],
            missing_documents=[],
            document_status={}
        )
        
        # Determine next steps
        next_steps = self._determine_next_steps(state)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(state)
        
        return SupervisorWorkflowOutput(
            routing_decision=state.routing_decision or "COLLECT",
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
        if state.routing_decision == "PROCEED":
            return ["Proceeding with prescribed workflows"]
        else:
            missing_docs = state.document_availability.missing_documents if state.document_availability else []
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
        if state.error_message:
            return 0.3  # Low confidence if there were errors
        
        if state.document_availability and state.document_availability.is_ready:
            return 0.9  # High confidence if documents are ready
        
        return 0.7  # Medium confidence for COLLECT decisions 