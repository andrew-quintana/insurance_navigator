"""
Chat Interface for Patient Navigator

This module provides a complete chat interface that integrates:
1. Input Processing - handles user input (text/voice), translation, sanitization
2. Agent Workflows - routes to appropriate agents (information retrieval, strategy, supervisor)
3. Output Processing - transforms technical outputs into user-friendly responses

This creates the interface that users interact with through chat windows.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .input_processing.workflow import InputProcessingWorkflow
from .output_processing import CommunicationAgent, OutputWorkflow
from .output_processing.two_stage_synthesizer import TwoStageOutputSynthesizer
from .output_processing.types import CommunicationRequest, AgentOutput
from .shared.workflow_output import WorkflowOutput, WorkflowOutputType
from .supervisor import SupervisorWorkflow
from .information_retrieval import InformationRetrievalAgent
# Strategy agent will be implemented as needed

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Represents a chat message in the conversation."""
    user_id: str
    content: str
    timestamp: float
    message_type: str = "text"  # "text" or "voice"
    language: str = "en"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ChatResponse:
    """Response from the chat system."""
    content: str
    agent_sources: List[str]
    confidence: float
    processing_time: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PatientNavigatorChatInterface:
    """
    Complete chat interface for the Patient Navigator system.
    
    This class orchestrates the entire conversation flow:
    1. Receives user input (text or voice)
    2. Processes input through input processing workflow
    3. Routes to appropriate agent workflows
    4. Processes outputs through output processing workflow
    5. Returns user-friendly responses
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the chat interface with all required components."""
        self.config = config or {}
        
        # Initialize input processing components
        self.input_processing_workflow = InputProcessingWorkflow()
        
        # Initialize agent workflows
        self.supervisor_workflow = SupervisorWorkflow(use_mock=False)  # Use real supervisor workflow
        self.information_retrieval_agent = InformationRetrievalAgent(use_mock=False)  # Use real agent
        # Strategy agent will be implemented as needed - for now use the strategy creator
        try:
            from .strategy.creator.agent import StrategyCreatorAgent
            self.strategy_agent = StrategyCreatorAgent(use_mock=False)
        except ImportError:
            self.strategy_agent = None
            logger.warning("Strategy agent not available, using mock responses")
        
        # Initialize output processing components
        self.communication_agent = CommunicationAgent()
        self.output_workflow = OutputWorkflow()
        self.two_stage_synthesizer = TwoStageOutputSynthesizer()
        
        # Conversation state
        self.conversation_history: Dict[str, List[ChatMessage]] = {}
        
        logger.info("Patient Navigator Chat Interface initialized")
    
    async def process_message(self, message: ChatMessage) -> ChatResponse:
        """
        Process a user message through the complete workflow.
        
        Args:
            message: User's chat message
            
        Returns:
            Processed response ready for user display
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing message from user {message.user_id}")
            
            # Step 1: Input Processing
            sanitized_input = await self._process_input(message)
            
            # Step 2: Workflow Routing
            workflow_outputs = await self._route_to_workflows(sanitized_input, message)
            
            # Step 3: Output Processing
            response = await self._process_outputs(workflow_outputs, message)
            
            # Step 4: Update conversation history
            await self._update_conversation_history(message, response)
            
            processing_time = time.time() - start_time
            response.processing_time = processing_time
            
            logger.info(f"Message processed successfully in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Return error response
            return ChatResponse(
                content="I apologize, but I encountered an error processing your request. Please try again.",
                agent_sources=["system"],
                confidence=0.0,
                processing_time=time.time() - start_time,
                metadata={"error": str(e), "error_type": "processing_error"}
            )
    
    async def _process_input(self, message: ChatMessage):
        """Process user input through input processing workflow."""
        logger.info("Processing input through input processing workflow")
        
        # Create user context
        user_context = self._create_user_context(message)
        
        # Process input through the complete workflow
        agent_prompt = await self.input_processing_workflow.process_input(
            text=message.content,
            user_context=user_context
        )
        
        return agent_prompt
    
    async def _route_to_workflows(self, agent_prompt, message: ChatMessage):
        """Route processed input to appropriate agent workflows."""
        logger.info("Routing to agent workflows")
        
        # Use supervisor workflow to determine workflow
        try:
            # Try to use the real supervisor workflow
            logger.info("=== ATTEMPTING TO USE SUPERVISOR WORKFLOW ===")
            workflow_prescription = await self._use_supervisor_workflow(
                agent_prompt.prompt_text,
                agent_prompt.context,
                message.user_id
            )
            logger.info(f"=== SUPERVISOR WORKFLOW SUCCEEDED: {workflow_prescription} ===")
        except Exception as e:
            logger.error(f"=== SUPERVISOR WORKFLOW FAILED, FALLING BACK TO SIMPLE ROUTING: {e} ===")
            logger.error(f"=== SUPERVISOR WORKFLOW ERROR TYPE: {type(e).__name__} ===")
            logger.error(f"=== SUPERVISOR WORKFLOW ERROR DETAILS: {str(e)} ===")
            # Fallback to simple routing if supervisor workflow fails
            workflow_prescription = await self._simple_workflow_routing(
                agent_prompt.prompt_text,
                agent_prompt.context
            )
            logger.info(f"=== USING SIMPLE ROUTING FALLBACK: {workflow_prescription} ===")
        
        workflow_outputs = []
        
        # Execute prescribed workflow using agnostic approach
        if workflow_prescription["recommended_workflow"] == "information_retrieval":
            try:
                logger.info("=== CALLING INFORMATION RETRIEVAL AGENT ===")
                # Create proper input format for information retrieval agent
                from .information_retrieval.models import InformationRetrievalInput
                
                input_data = InformationRetrievalInput(
                    user_id=message.user_id,
                    user_query=agent_prompt.prompt_text,
                    workflow_context=agent_prompt.context,
                    document_requirements=[]
                )
                
                logger.info(f"=== CALLING retrieve_information with query: {agent_prompt.prompt_text[:100]}... ===")
                result = await self.information_retrieval_agent.retrieve_information(input_data)
                logger.info("=== INFORMATION RETRIEVAL AGENT COMPLETED ===")
                
                # Convert to agnostic workflow output
                from .shared.workflow_output import create_workflow_output
                metadata = {"processing_steps": result.processing_steps}
                if result.error_message:
                    metadata["error_message"] = result.error_message
                workflow_output = create_workflow_output(
                    WorkflowOutputType.INFORMATION_RETRIEVAL,
                    result.model_dump(),
                    confidence_score=result.confidence_score,
                    metadata=metadata
                )
                workflow_outputs.append(workflow_output)
                
            except Exception as e:
                logger.error(f"Information retrieval agent execution failed: {e}")
                # Create error workflow output
                from .shared.workflow_output import create_workflow_output
                error_output = create_workflow_output(
                    WorkflowOutputType.INFORMATION_RETRIEVAL,
                    {"error": str(e), "message": "Information retrieval encountered an error. Please try again."},
                    confidence_score=0.0,
                    metadata={"status": "error", "workflow": "information_retrieval"}
                )
                workflow_outputs.append(error_output)
            
        elif workflow_prescription["recommended_workflow"] == "strategy":
            if self.strategy_agent:
                try:
                    # Use real strategy agent
                    from .strategy.types import PlanConstraints, ContextRetrievalResult
                    
                    # Create mock context and constraints for now
                    # TODO: Implement real context retrieval
                    context = ContextRetrievalResult(
                        user_id=message.user_id,
                        relevant_documents=[],
                        user_preferences={},
                        insurance_context={}
                    )
                    
                    plan_constraints = PlanConstraints(
                        time_horizon="short_term",
                        budget_constraints="moderate",
                        risk_tolerance="balanced"
                    )
                    
                    strategies = await self.strategy_agent.generate_strategies(context, plan_constraints)
                    
                    # Convert to agnostic workflow output
                    from .shared.workflow_output import create_workflow_output
                    avg_confidence = sum(s.llm_scores.overall_score for s in strategies) / len(strategies) if strategies else 0.0
                    workflow_output = create_workflow_output(
                        WorkflowOutputType.STRATEGY,
                        {"strategies": [s.model_dump() for s in strategies]},
                        confidence_score=avg_confidence,
                        metadata={"strategies_count": len(strategies)}
                    )
                    workflow_outputs.append(workflow_output)
                    
                except Exception as e:
                    logger.error(f"Strategy agent execution failed: {e}")
                    # Create error workflow output
                    from .shared.workflow_output import create_workflow_output
                    error_output = create_workflow_output(
                        WorkflowOutputType.STRATEGY,
                        {"error": str(e), "message": "Strategy generation encountered an error. Please try again."},
                        confidence_score=0.0,
                        metadata={"status": "error", "workflow": "strategy"}
                    )
                    workflow_outputs.append(error_output)
            else:
                # Fallback to mock response
                from .shared.workflow_output import create_workflow_output
                mock_output = create_workflow_output(
                    WorkflowOutputType.STRATEGY,
                    {"message": "Strategy workflow is being implemented. For now, focusing on information retrieval."},
                    confidence_score=0.5,
                    metadata={"status": "mock", "workflow": "strategy"}
                )
                workflow_outputs.append(mock_output)
        
        return workflow_outputs
    
    async def _use_supervisor_workflow(self, prompt_text: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Use the real supervisor workflow to determine routing.
        
        This method attempts to use the full supervisor workflow for intelligent routing.
        """
        try:
            # Create supervisor workflow input
            from .supervisor.models import SupervisorWorkflowInput
            
            workflow_input = SupervisorWorkflowInput(
                user_id=user_id,
                user_query=prompt_text,
                context=context,
                workflow_type="information_retrieval"  # Default type
            )
            
            # Execute the supervisor workflow with timeout
            result = await asyncio.wait_for(
                self.supervisor_workflow.execute(workflow_input),
                timeout=120.0  # 120 second timeout for complex queries
            )
            
            # Extract routing decision from result
            if hasattr(result, 'prescribed_workflows') and result.prescribed_workflows:
                # Use the first prescribed workflow as the recommended workflow
                recommended_workflow = result.prescribed_workflows[0].value
                return {
                    "recommended_workflow": recommended_workflow,
                    "confidence": getattr(result, 'confidence_score', 0.8),
                    "reasoning": f"Supervisor workflow prescribed: {recommended_workflow}"
                }
            elif hasattr(result, 'routing_decision'):
                # Fallback to routing decision (which is just a string)
                return {
                    "recommended_workflow": "information_retrieval",  # Default workflow
                    "confidence": 0.8,
                    "reasoning": f"Supervisor workflow routing decision: {result.routing_decision}"
                }
            else:
                # Fallback if no workflow information available
                return {
                    "recommended_workflow": "information_retrieval",
                    "confidence": 0.8,
                    "reasoning": "Supervisor workflow completed but no workflow information available"
                }
                
        except asyncio.TimeoutError:
            logger.error("Supervisor workflow timed out after 30 seconds")
            raise
        except Exception as e:
            logger.error(f"Supervisor workflow execution failed: {e}")
            raise
    
    async def _simple_workflow_routing(self, prompt_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simple workflow routing logic for MVP.
        
        This is a simplified version that will be enhanced with the full supervisor workflow
        in future iterations.
        """
        # Simple keyword-based routing for MVP
        prompt_lower = prompt_text.lower()
        
        # Check for strategy-related keywords
        strategy_keywords = [
            "strategy", "plan", "approach", "recommend", "suggestion", "option",
            "compare", "choice", "decision", "best", "optimal"
        ]
        
        # Check for information retrieval keywords
        info_keywords = [
            "what", "how", "when", "where", "why", "explain", "describe",
            "deductible", "copay", "coverage", "benefits", "policy", "insurance"
        ]
        
        # Count matches
        strategy_score = sum(1 for keyword in strategy_keywords if keyword in prompt_lower)
        info_score = sum(1 for keyword in info_keywords if keyword in prompt_lower)
        
        # Route based on highest score, default to information retrieval
        if strategy_score > info_score:
            return {
                "recommended_workflow": "strategy",
                "confidence": min(0.9, 0.5 + (strategy_score * 0.1)),
                "reasoning": f"Strategy keywords detected: {strategy_score} matches"
            }
        else:
            return {
                "recommended_workflow": "information_retrieval",
                "confidence": min(0.9, 0.5 + (info_score * 0.1)),
                "reasoning": f"Information retrieval keywords detected: {info_score} matches"
            }
    
    async def _process_outputs(self, workflow_outputs: List[WorkflowOutput], message: ChatMessage):
        """Process workflow outputs through two-stage synthesizer for human-readable responses."""
        logger.info("Processing workflow outputs through two-stage synthesizer")
        logger.info(f"Number of workflow outputs to process: {len(workflow_outputs)}")
        
        try:
            # Convert workflow outputs to agent outputs for two-stage synthesizer
            logger.info("Step 1: Converting workflow outputs to agent outputs")
            agent_outputs = []
            for i, workflow_output in enumerate(workflow_outputs):
                logger.info(f"Processing workflow output {i+1}/{len(workflow_outputs)}: {workflow_output.workflow_type.value}")
                
                # Extract meaningful content from workflow output
                content = self._extract_workflow_content(workflow_output)
                logger.info(f"Extracted content length: {len(content)} characters")
                
                agent_outputs.append(AgentOutput(
                    agent_id=workflow_output.workflow_type.value,
                    content=content,
                    metadata={
                        "workflow_type": workflow_output.workflow_type.value,
                        "confidence_score": workflow_output.confidence_score,
                        **workflow_output.metadata
                    }
                ))
            
            logger.info(f"Successfully converted {len(agent_outputs)} workflow outputs to agent outputs")
            logger.info("=== WORKFLOW OUTPUTS PROCESSING COMPLETED ===")
            
            # Process through two-stage synthesizer
            logger.info("Step 2: Calling two-stage synthesizer")
            logger.info("=== POST-RAG WORKFLOW: TWO-STAGE SYNTHESIZER STARTED ===")
            user_context = {
                "user_id": message.user_id,
                "language": message.language,
                "conversation_history": self.conversation_history.get(message.user_id, [])
            }
            logger.info(f"User context: {user_context}")
            
            logger.info("=== CALLING TWO-STAGE SYNTHESIZER SYNTHESIZE_OUTPUTS ===")
            response = await self.two_stage_synthesizer.synthesize_outputs(
                agent_outputs=agent_outputs,
                user_context=user_context
            )
            logger.info("=== TWO-STAGE SYNTHESIZER COMPLETED SUCCESSFULLY ===")
            logger.info("=== CREATING CHAT RESPONSE ===")
            
            chat_response = ChatResponse(
                content=response.enhanced_content,
                agent_sources=response.original_sources,
                confidence=response.metadata.get("confidence", 0.0),
                processing_time=response.processing_time,
                metadata=response.metadata
            )
            logger.info("=== CHAT RESPONSE CREATED SUCCESSFULLY ===")
            return chat_response
            
        except Exception as e:
            logger.error(f"Two-stage synthesizer failed: {e}")
            # Create fallback response
            fallback_content = "I encountered an error while processing your request. Please try again."
            return ChatResponse(
                content=fallback_content,
                agent_sources=[output.workflow_type.value for output in workflow_outputs],
                confidence=0.0,
                processing_time=0.0,
                metadata={"error": str(e), "fallback": True}
            )
    
    def _extract_workflow_content(self, workflow_output: WorkflowOutput) -> str:
        """Extract meaningful content from workflow output for communication agent."""
        if workflow_output.workflow_type == WorkflowOutputType.INFORMATION_RETRIEVAL:
            # For information retrieval, use the direct answer and key points
            direct_answer = workflow_output.content.get("direct_answer", "")
            key_points = workflow_output.content.get("key_points", [])
            
            content_parts = [direct_answer]
            if key_points:
                content_parts.append("\nKey information:")
                for i, point in enumerate(key_points, 1):
                    content_parts.append(f"{i}. {point}")
            
            return "\n".join(content_parts)
        
        elif workflow_output.workflow_type == WorkflowOutputType.STRATEGY:
            # For strategy, extract strategies and actionable steps
            strategies = workflow_output.content.get("strategies", [])
            if not strategies:
                return "No strategies generated."
            
            content_parts = []
            for i, strategy in enumerate(strategies, 1):
                title = strategy.get("title", f"Strategy {i}")
                approach = strategy.get("approach", "")
                actionable_steps = strategy.get("actionable_steps", [])
                
                content_parts.append(f"**{title}**")
                if approach:
                    content_parts.append(f"{approach}")
                if actionable_steps:
                    content_parts.append("Steps to take:")
                    for j, step in enumerate(actionable_steps, 1):
                        content_parts.append(f"  {j}. {step}")
                content_parts.append("")  # Add spacing between strategies
            
            return "\n".join(content_parts)
        
        else:
            # For other workflow types, use the summary
            return workflow_output.get_summary()
    
    async def _check_available_documents(self, user_id: str) -> List[str]:
        """Check what documents are available for the user."""
        # This would query the upload pipeline to see what documents are available
        # For now, return a mock list
        return ["policy_document_1", "policy_document_2"]
    
    def _create_user_context(self, message: ChatMessage):
        """Create user context for input processing."""
        from .input_processing.types import UserContext
        
        return UserContext(
            user_id=message.user_id,
            conversation_history=[msg.content for msg in self.conversation_history.get(message.user_id, [])],
            language_preference=message.language,
            domain_context="insurance",
            session_metadata={
                "timestamp": message.timestamp,
                "message_type": message.message_type
            }
        )
    
    async def _update_conversation_history(self, message: ChatMessage, response: ChatResponse):
        """Update conversation history for context."""
        if message.user_id not in self.conversation_history:
            self.conversation_history[message.user_id] = []
        
        # Add user message
        self.conversation_history[message.user_id].append(message)
        
        # Add system response
        response_message = ChatMessage(
            user_id="system",
            content=response.content,
            timestamp=time.time(),
            message_type="text",
            language="en",
            metadata={"agent_sources": response.agent_sources}
        )
        self.conversation_history[message.user_id].append(response_message)
        
        # Keep only last 20 messages for context
        if len(self.conversation_history[message.user_id]) > 20:
            self.conversation_history[message.user_id] = self.conversation_history[message.user_id][-20:]
    
    def _create_fallback_response(self, agent_outputs: List[Dict]) -> Any:
        """Create a fallback response when communication agent fails."""
        from .output_processing.types import CommunicationResponse
        
        # Combine agent outputs into a simple response
        combined_content = "\n\n".join([
            f"From {output['agent_id']}: {output['content']}"
            for output in agent_outputs
        ])
        
        return CommunicationResponse(
            enhanced_content=combined_content,
            original_sources=[output['agent_id'] for output in agent_outputs],
            processing_time=0.0,
            metadata={"fallback": True, "error": "Communication agent failed"}
        )
    
    async def get_conversation_history(self, user_id: str) -> List[ChatMessage]:
        """Get conversation history for a user."""
        return self.conversation_history.get(user_id, [])
    
    async def clear_conversation_history(self, user_id: str):
        """Clear conversation history for a user."""
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
            logger.info(f"Cleared conversation history for user {user_id}")


# Convenience function for easy integration
async def create_chat_interface(config: Dict[str, Any] = None) -> PatientNavigatorChatInterface:
    """Create and return a configured chat interface."""
    return PatientNavigatorChatInterface(config)


# Example usage
async def example_chat_flow():
    """Example of how to use the chat interface."""
    chat_interface = await create_chat_interface()
    
    # Simulate user message
    message = ChatMessage(
        user_id="user123",
        content="What is the deductible for my insurance policy?",
        timestamp=time.time(),
        message_type="text",
        language="en"
    )
    
    # Process message
    response = await chat_interface.process_message(message)
    
    print(f"User: {message.content}")
    print(f"System: {response.content}")
    print(f"Sources: {response.agent_sources}")
    print(f"Processing time: {response.processing_time:.2f}s")


if __name__ == "__main__":
    # Run example if called directly
    asyncio.run(example_chat_flow())
