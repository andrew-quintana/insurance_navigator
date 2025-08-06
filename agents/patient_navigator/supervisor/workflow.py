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

# Import existing workflow components for integration
try:
    from agents.patient_navigator.information_retrieval.agent import InformationRetrievalAgent
    from agents.patient_navigator.strategy.workflow.orchestrator import StrategyWorkflowOrchestrator
    WORKFLOW_COMPONENTS_AVAILABLE = True
except ImportError:
    WORKFLOW_COMPONENTS_AVAILABLE = False
    InformationRetrievalAgent = None
    StrategyWorkflowOrchestrator = None


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
        
        # Initialize workflow execution components if available
        if WORKFLOW_COMPONENTS_AVAILABLE and not use_mock:
            self.information_retrieval_agent = InformationRetrievalAgent(use_mock=use_mock)
            self.strategy_orchestrator = StrategyWorkflowOrchestrator(use_mock=use_mock)
        else:
            self.information_retrieval_agent = None
            self.strategy_orchestrator = None
        
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
        
        # Add workflow execution nodes if components are available
        if WORKFLOW_COMPONENTS_AVAILABLE:
            self.logger.info("Adding workflow execution nodes to graph")
            workflow.add_node("execute_information_retrieval", self._execute_information_retrieval_node)
            workflow.add_node("execute_strategy", self._execute_strategy_node)
        else:
            self.logger.warning("Workflow components not available, but adding mock workflow execution nodes for testing")
            workflow.add_node("execute_information_retrieval", self._execute_information_retrieval_node)
            workflow.add_node("execute_strategy", self._execute_strategy_node)
        
        # Add end node
        workflow.add_node("end", self._end_node)
        
        # Add edges for sequential flow
        workflow.add_edge("prescribe_workflow", "check_documents")
        workflow.add_edge("check_documents", "route_decision")
        
        # Add conditional edges for workflow execution
        if WORKFLOW_COMPONENTS_AVAILABLE:
            self.logger.info("Adding conditional edges for workflow execution")
        else:
            self.logger.warning("Adding conditional edges for workflow execution with mock components")
        
        # Route to workflow execution based on routing decision
        workflow.add_conditional_edges(
            "route_decision",
            self._route_to_workflow_execution,
            {
                "execute_information_retrieval": "execute_information_retrieval",
                "execute_strategy": "execute_strategy",
                "end": "end"
            }
        )
        
        # Add edges from workflow execution nodes back to route_decision for multi-workflow execution
        workflow.add_edge("execute_information_retrieval", "route_decision")
        workflow.add_edge("execute_strategy", "route_decision")
        
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
    
    async def _route_to_workflow_execution(self, state: SupervisorState) -> str:
        """
        Route to appropriate workflow execution based on routing decision and prescribed workflows.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node name or "end" to terminate
        """
        self.logger.info(f"Routing to workflow execution - decision: {state.routing_decision}, workflows: {state.prescribed_workflows}")
        
        if state.routing_decision != "PROCEED":
            self.logger.info("Not proceeding - routing decision is not PROCEED")
            return "end"
        
        if not state.prescribed_workflows:
            self.logger.info("Not proceeding - no prescribed workflows")
            return "end"
        
        # Check if we've already executed all workflows
        executed_workflows = getattr(state, 'executed_workflows', [])
        if executed_workflows is None:
            executed_workflows = []
        
        if len(executed_workflows) >= len(state.prescribed_workflows):
            self.logger.info("All workflows already executed, ending")
            return "end"
        
        # Execute workflows in deterministic order (information_retrieval → strategy)
        # Check if we've already executed information_retrieval
        if WorkflowType.INFORMATION_RETRIEVAL in state.prescribed_workflows and WorkflowType.INFORMATION_RETRIEVAL not in executed_workflows:
            self.logger.info("Executing information retrieval workflow")
            return "execute_information_retrieval"
        
        # Check if we've already executed strategy
        if WorkflowType.STRATEGY in state.prescribed_workflows and WorkflowType.STRATEGY not in executed_workflows:
            self.logger.info("Executing strategy workflow")
            return "execute_strategy"
        
        # All workflows executed
        self.logger.info("All workflows executed, ending")
        return "end"
    
    async def _execute_information_retrieval_node(self, state: SupervisorState) -> SupervisorState:
        """
        LangGraph node for InformationRetrievalAgent workflow execution.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with workflow execution results
        """
        node_start_time = time.time()
        
        try:
            self.logger.info("Executing information retrieval workflow node")
            
            if not self.information_retrieval_agent:
                self.logger.warning("InformationRetrievalAgent not available, skipping execution")
                # Create mock result for testing
                workflow_result = {
                    'status': 'skipped',
                    'reason': 'InformationRetrievalAgent not available',
                    'data': {},
                    'errors': []
                }
            else:
                # Execute real InformationRetrievalAgent
                workflow_result = await self.information_retrieval_agent.execute(
                    user_query=state.user_query,
                    user_id=state.user_id,
                    workflow_context=state.workflow_context
                )
                workflow_result = workflow_result.model_dump()
            
            # Store workflow results
            if not hasattr(state, 'workflow_results') or state.workflow_results is None:
                state.workflow_results = {}
            state.workflow_results['information_retrieval'] = workflow_result
            
            # Mark information_retrieval as executed
            if not hasattr(state, 'executed_workflows') or state.executed_workflows is None:
                state.executed_workflows = []
            if WorkflowType.INFORMATION_RETRIEVAL not in state.executed_workflows:
                state.executed_workflows.append(WorkflowType.INFORMATION_RETRIEVAL)
            
            node_time = time.time() - node_start_time
            if not hasattr(state, 'node_performance'):
                state.node_performance = {}
            state.node_performance['execute_information_retrieval'] = node_time
            
            return state
            
        except Exception as e:
            self.logger.error(f"Information retrieval workflow execution failed: {e}")
            # Mark as executed even on error to prevent infinite loops
            if not hasattr(state, 'executed_workflows') or state.executed_workflows is None:
                state.executed_workflows = []
            if WorkflowType.INFORMATION_RETRIEVAL not in state.executed_workflows:
                state.executed_workflows.append(WorkflowType.INFORMATION_RETRIEVAL)
            
            # Store error result
            if not hasattr(state, 'workflow_results'):
                state.workflow_results = {}
            state.workflow_results['information_retrieval'] = {
                'status': 'error',
                'error': str(e),
                'data': {},
                'errors': [str(e)]
            }
            
            return state
    
    async def _execute_strategy_node(self, state: SupervisorState) -> SupervisorState:
        """
        LangGraph node for StrategyWorkflowOrchestrator workflow execution.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with workflow execution results
        """
        node_start_time = time.time()
        
        try:
            self.logger.info("Executing strategy workflow node")
            
            if not self.strategy_orchestrator:
                self.logger.warning("StrategyWorkflowOrchestrator not available, skipping execution")
                # Create mock result for testing
                workflow_result = {
                    'status': 'skipped',
                    'reason': 'StrategyWorkflowOrchestrator not available',
                    'data': {},
                    'errors': []
                }
            else:
                # Execute real StrategyWorkflowOrchestrator
                workflow_result = await self.strategy_orchestrator.execute(
                    user_query=state.user_query,
                    user_id=state.user_id,
                    workflow_context=state.workflow_context
                )
                workflow_result = workflow_result.model_dump()
            
            # Store workflow results
            if not hasattr(state, 'workflow_results') or state.workflow_results is None:
                state.workflow_results = {}
            state.workflow_results['strategy'] = workflow_result
            
            # Mark strategy as executed
            if not hasattr(state, 'executed_workflows') or state.executed_workflows is None:
                state.executed_workflows = []
            if WorkflowType.STRATEGY not in state.executed_workflows:
                state.executed_workflows.append(WorkflowType.STRATEGY)
            
            node_time = time.time() - node_start_time
            if not hasattr(state, 'node_performance'):
                state.node_performance = {}
            state.node_performance['execute_strategy'] = node_time
            
            return state
            
        except Exception as e:
            self.logger.error(f"Strategy workflow execution failed: {e}")
            # Mark as executed even on error to prevent infinite loops
            if not hasattr(state, 'executed_workflows') or state.executed_workflows is None:
                state.executed_workflows = []
            if WorkflowType.STRATEGY not in state.executed_workflows:
                state.executed_workflows.append(WorkflowType.STRATEGY)
            
            # Store error result
            if not hasattr(state, 'workflow_results'):
                state.workflow_results = {}
            state.workflow_results['strategy'] = {
                'status': 'error',
                'error': str(e),
                'data': {},
                'errors': [str(e)]
            }
            
            return state
    
    async def _end_node(self, state: SupervisorState) -> SupervisorState:
        """
        LangGraph node for ending the workflow.
        
        Args:
            state: Current workflow state
            
        Returns:
            Final state
        """
        self.logger.info("Workflow ended.")
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
                routing_decision="COLLECT",  # Default to COLLECT on error
                document_availability=DocumentAvailabilityResult(
                    is_ready=False,
                    available_documents=[],
                    missing_documents=[],
                    document_status={}
                )
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
        
        # Ensure prescribed_workflows is not None
        if prescribed_workflows is None:
            prescribed_workflows = [WorkflowType.INFORMATION_RETRIEVAL]
        
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
        
        # Ensure document_availability is not None
        if document_availability is None:
            document_availability = DocumentAvailabilityResult(
                is_ready=False,
                available_documents=[],
                missing_documents=[],
                document_status={}
            )
        
        # Extract routing decision - handle both SupervisorState and AddableValuesDict
        if hasattr(state, 'routing_decision'):
            routing_decision = state.routing_decision or "COLLECT"
        else:
            # Handle AddableValuesDict case
            routing_decision = state.get('routing_decision', "COLLECT")
        
        # Ensure routing_decision is not None
        if routing_decision is None:
            routing_decision = "COLLECT"
        
        # Determine next steps
        next_steps = self._determine_next_steps(state)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(state)
        
        # Extract workflow results
        workflow_results = None
        information_retrieval_result = None
        strategy_result = None
        
        if hasattr(state, 'workflow_results'):
            workflow_results = state.workflow_results
            if workflow_results:
                information_retrieval_result = workflow_results.get('information_retrieval')
                strategy_result = workflow_results.get('strategy')
        else:
            # Handle AddableValuesDict case
            workflow_results = state.get('workflow_results')
            if workflow_results:
                information_retrieval_result = workflow_results.get('information_retrieval')
                strategy_result = workflow_results.get('strategy')
        
        # Extract user_id - handle both SupervisorState and AddableValuesDict
        if hasattr(state, 'user_id'):
            user_id = state.user_id
        else:
            # Handle AddableValuesDict case
            user_id = state.get('user_id', 'unknown_user')
        
        # Ensure user_id is not None
        if user_id is None:
            user_id = 'unknown_user'
        
        return SupervisorWorkflowOutput(
            routing_decision=routing_decision,
            prescribed_workflows=prescribed_workflows,
            execution_order=prescribed_workflows,  # Same as prescribed for MVP
            document_availability=document_availability,
            workflow_prescription=workflow_prescription,
            next_steps=next_steps,
            confidence_score=confidence_score,
            processing_time=processing_time,
            information_retrieval_result=information_retrieval_result,
            strategy_result=strategy_result,
            workflow_results=workflow_results,
            user_id=user_id
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