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
        self.supervisor_workflow = SupervisorWorkflow()
        self.information_retrieval_agent = InformationRetrievalAgent()
        # Strategy agent will be implemented as needed
        
        # Initialize output processing components
        self.communication_agent = CommunicationAgent()
        self.output_workflow = OutputWorkflow()
        
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
            agent_outputs = await self._route_to_workflows(sanitized_input, message)
            
            # Step 3: Output Processing
            response = await self._process_outputs(agent_outputs, message)
            
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
        # For now, use a simple routing logic since the full supervisor workflow is complex
        # This will be enhanced in future iterations
        workflow_prescription = await self._simple_workflow_routing(
            agent_prompt.prompt_text,
            agent_prompt.context
        )
        
        agent_outputs = []
        
        # Execute prescribed workflow
        if workflow_prescription["recommended_workflow"] == "information_retrieval":
            result = await self.information_retrieval_agent.retrieve_information({
                "user_id": message.user_id,
                "query": agent_prompt.prompt_text,
                "context": agent_prompt.context
            })
            agent_outputs.append({
                "agent_id": "information_retrieval",
                "content": str(result),
                "metadata": {"workflow": "information_retrieval"}
            })
            
        elif workflow_prescription["recommended_workflow"] == "strategy":
            # For now, return a mock strategy response
            # This will be implemented with the actual strategy agent in future iterations
            agent_outputs.append({
                "agent_id": "strategy",
                "content": "Strategy workflow is being implemented. For now, focusing on information retrieval.",
                "metadata": {"workflow": "strategy", "status": "mock"}
            })
        
        return agent_outputs
    
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
    
    async def _process_outputs(self, agent_outputs: List[Dict], message: ChatMessage):
        """Process agent outputs through output processing workflow."""
        logger.info("Processing outputs through output processing workflow")
        
        # Create communication request
        from .output_processing.types import CommunicationRequest, AgentOutput
        
        request = CommunicationRequest(
            agent_outputs=[
                AgentOutput(
                    agent_id=output["agent_id"],
                    content=output["content"],
                    metadata=output.get("metadata", {})
                )
                for output in agent_outputs
            ],
            user_context={
                "user_id": message.user_id,
                "language": message.language,
                "conversation_history": self.conversation_history.get(message.user_id, [])
            }
        )
        
        # Process through communication agent
        response = await self.communication_agent.enhance_communication(request)
        
        return ChatResponse(
            content=response.enhanced_content,
            agent_sources=response.original_sources,
            confidence=0.9,  # High confidence for processed outputs
            processing_time=0.0,  # Will be set by caller
            metadata=response.metadata
        )
    
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
