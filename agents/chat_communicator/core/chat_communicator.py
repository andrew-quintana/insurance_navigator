"""
Chat Communicator Agent

This agent is responsible for:
1. Receiving structured data from other agents (Patient Navigator, Service Access Strategy)
2. Converting technical/structured information into clear, conversational language
3. Providing empathetic, user-friendly responses
4. Ensuring users understand next steps and feel supported
5. Handling emergency situations with appropriate urgency

Based on healthcare communication best practices, this agent implements:
- Clear, jargon-free communication
- Empathetic tone and user-centered approach
- Structured responses with actionable next steps
- Emergency detection and appropriate escalation
- Consistent formatting and accessibility
"""

import os
import json
import logging
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models import BaseLanguageModel
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import SystemMessage, HumanMessage

# Import base agent and exceptions
from agents.base_agent import BaseAgent
from agents.common.exceptions import AgentException

# Import configuration handling
from utils.config_manager import ConfigManager

# Import models
from agents.chat_communicator.core.models.chat_models import (
    ChatInput, ChatResponse, ConversationContext, CommunicationPreferences
)
from agents.patient_navigator.core.models.navigator_models import NavigatorOutput
from agents.service_access_strategy.core.models.strategy_models import ServiceAccessStrategy

# Setup logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Create logs directory if it doesn't exist
    log_dir = os.path.join("logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up file handler
    handler = logging.FileHandler(os.path.join(log_dir, "chat_communicator.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class ChatCommunicatorException(AgentException):
    """Exception raised for Chat Communicator Agent errors."""
    pass


class ChatCommunicatorAgent(BaseAgent):
    """Agent responsible for communicating with users in conversational language."""
    
    def __init__(
        self,
        llm: Optional[BaseLanguageModel] = None,
        config_manager: Optional[ConfigManager] = None,
        use_mock: bool = False
    ):
        """
        Initialize the Chat Communicator Agent.
        
        Args:
            llm: Language model to use for generating responses
            config_manager: Configuration manager instance
            use_mock: Whether to use mock responses for testing
        """
        # Get configuration manager if not provided
        self.config_manager = config_manager or ConfigManager()
        
        # Get agent configuration
        try:
            agent_config = self.config_manager.get_agent_config("chat_communicator")
            model_config = agent_config.get("model", {})
            model_name = model_config.get("name", "claude-3-sonnet-20240229-v1h")
            temperature = model_config.get("temperature", 0.2)  # Slightly higher for more natural conversation
        except Exception as e:
            logger.warning(f"Could not load agent config: {e}. Using defaults.")
            model_name = "claude-3-sonnet-20240229-v1h"
            temperature = 0.2
        
        # Initialize the base agent
        super().__init__(
            name="chat_communicator",
            llm=llm or (None if use_mock else ChatAnthropic(model=model_name, temperature=temperature)),
            use_mock=use_mock
        )
        
        # Initialize conversation tracking
        self.active_conversations = {}
        
        # Initialize output parser
        self.output_parser = PydanticOutputParser(pydantic_object=ChatResponse)
        
        # Set default paths (will be overridden in _initialize_agent if config available)
        self.prompt_path = "agents/chat_communicator/core/prompts/prompt_chat_communicator_v0_1.md"
        self.examples_path = "agents/chat_communicator/core/prompts/examples/chat_examples_v0_1.json"
        
        # Initialize agent-specific components
        self._initialize_agent()
        
        logger.info(f"Chat Communicator Agent initialized with model {model_name}")
    
    def _initialize_agent(self) -> None:
        """Initialize agent-specific components."""
        # Load system prompt
        try:
            self.system_prompt = self._load_prompt(self.prompt_path)
        except Exception as e:
            self.logger.error(f"Failed to load system prompt: {e}")
            # Fallback prompt
            self.system_prompt = """You are a Healthcare Navigation Communication Specialist. 
            Convert technical healthcare information into clear, conversational language for users."""
        
        # Load examples
        try:
            self.examples = self._load_examples(self.examples_path)
        except Exception as e:
            self.logger.warning(f"Failed to load examples: {e}")
            self.examples = []
        
        # Create prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content="""
Input Data:
{input_data}

User Context:
- User ID: {user_id}
- Session ID: {session_id}
- Previous Messages: {conversation_history}

Please provide a conversational response in the specified JSON format.

{format_instructions}
""")
        ])
        
        # Create processing chain
        if not self.use_mock:
            self.processing_chain = (
                self.prompt_template
                | self.llm
                | self.output_parser
            )
        else:
            self.processing_chain = None
    
    def _validate_input(self, input_data: Dict[str, Any]) -> ChatInput:
        """
        Validate input data before processing.
        
        Args:
            input_data: The input data to validate
            
        Returns:
            Validated ChatInput object
            
        Raises:
            ChatCommunicatorException: If validation fails
        """
        try:
            # Handle different input formats
            if isinstance(input_data, dict):
                if "source_type" in input_data:
                    # Already in ChatInput format
                    return ChatInput(**input_data)
                elif "meta_intent" in input_data:
                    # NavigatorOutput format
                    navigator_output = NavigatorOutput(**input_data)
                    return ChatInput(
                        source_type="navigator_output",
                        data=navigator_output
                    )
                elif "patient_need" in input_data:
                    # ServiceAccessStrategy format
                    strategy_output = ServiceAccessStrategy(**input_data)
                    return ChatInput(
                        source_type="service_strategy",
                        data=strategy_output
                    )
                else:
                    raise ValueError("Unknown input format")
            elif hasattr(input_data, 'meta_intent'):
                # NavigatorOutput object
                return ChatInput(
                    source_type="navigator_output",
                    data=input_data
                )
            elif hasattr(input_data, 'patient_need'):
                # ServiceAccessStrategy object
                return ChatInput(
                    source_type="service_strategy",
                    data=input_data
                )
            else:
                raise ValueError("Invalid input type")
                
        except Exception as e:
            self.logger.error(f"Input validation failed: {str(e)}")
            raise ChatCommunicatorException(f"Invalid input data: {str(e)}")
    
    @BaseAgent.track_performance
    def _process_data(self, input_data: ChatInput) -> ChatResponse:
        """
        Process the validated input data.
        
        Args:
            input_data: Validated ChatInput object
            
        Returns:
            ChatResponse object
            
        Raises:
            ChatCommunicatorException: If processing fails
        """
        try:
            if self.use_mock:
                return self._generate_mock_response(input_data)
            
            # Prepare data for the LLM
            input_dict = {
                "input_data": json.dumps(input_data.data.model_dump() if hasattr(input_data.data, 'model_dump') else input_data.data),
                "user_id": input_data.user_id or "anonymous",
                "session_id": input_data.session_id or "new_session",
                "conversation_history": json.dumps(input_data.conversation_history or []),
                "format_instructions": self.output_parser.get_format_instructions()
            }
            
            # Generate response
            response = self.processing_chain.invoke(input_dict)
            
            # Add timestamp to metadata
            if not response.metadata:
                response.metadata = {}
            response.metadata["timestamp"] = datetime.utcnow().isoformat() + "Z"
            response.metadata["source_type"] = input_data.source_type
            
            return response
            
        except Exception as e:
            self.logger.error(f"Processing error: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise ChatCommunicatorException(f"Failed to process input: {str(e)}")
    
    def _generate_mock_response(self, input_data: ChatInput) -> ChatResponse:
        """Generate a mock response for testing."""
        if input_data.source_type == "navigator_output":
            data = input_data.data
            if hasattr(data, 'meta_intent') and data.meta_intent.emergency:
                return ChatResponse(
                    message="🚨 This appears to be an emergency situation. Please seek immediate medical attention.",
                    response_type="emergency",
                    next_steps=["Call 911", "Go to nearest emergency room"],
                    requires_action=True,
                    urgency_level="emergency",
                    confidence=1.0
                )
            else:
                return ChatResponse(
                    message="I understand your question about healthcare coverage. Let me help you with that information.",
                    response_type="informational",
                    next_steps=["Review your insurance benefits", "Contact your provider if needed"],
                    requires_action=False,
                    urgency_level="normal",
                    confidence=0.9
                )
        else:  # service_strategy
            return ChatResponse(
                message="I have a comprehensive plan for your healthcare needs. Here are the recommended next steps.",
                response_type="guidance",
                next_steps=["Follow the action plan", "Contact providers as recommended"],
                requires_action=True,
                urgency_level="normal",
                confidence=0.85
            )
    
    def _format_output(self, processed_data: ChatResponse) -> Dict[str, Any]:
        """
        Format the processed data for output.
        
        Args:
            processed_data: Processed ChatResponse object
            
        Returns:
            Formatted output dictionary
        """
        return processed_data.model_dump()
    
    def process_navigator_output(
        self,
        navigator_output: NavigatorOutput,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process Navigator Output and generate conversational response.
        
        Args:
            navigator_output: NavigatorOutput from Patient Navigator Agent
            user_id: User identifier
            session_id: Session identifier
            conversation_history: Previous conversation messages
            
        Returns:
            Conversational response dictionary
        """
        chat_input = ChatInput(
            source_type="navigator_output",
            data=navigator_output,
            user_id=user_id,
            session_id=session_id,
            conversation_history=conversation_history or []
        )
        
        return self.process(chat_input.model_dump())
    
    def process_service_strategy(
        self,
        service_strategy: ServiceAccessStrategy,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process Service Access Strategy and generate conversational response.
        
        Args:
            service_strategy: ServiceAccessStrategy from Service Access Strategy Agent
            user_id: User identifier
            session_id: Session identifier
            conversation_history: Previous conversation messages
            
        Returns:
            Conversational response dictionary
        """
        chat_input = ChatInput(
            source_type="service_strategy",
            data=service_strategy,
            user_id=user_id,
            session_id=session_id,
            conversation_history=conversation_history or []
        )
        
        return self.process(chat_input.model_dump())
    
    def update_conversation_context(
        self,
        user_id: str,
        session_id: str,
        message: str,
        response: str
    ) -> None:
        """
        Update conversation context for future interactions.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            message: User's message
            response: Agent's response
        """
        conversation_key = f"{user_id}_{session_id}"
        
        if conversation_key not in self.active_conversations:
            self.active_conversations[conversation_key] = ConversationContext(
                user_id=user_id,
                session_id=session_id,
                conversation_start=datetime.utcnow(),
                last_interaction=datetime.utcnow(),
                interaction_count=0
            )
        
        context = self.active_conversations[conversation_key]
        context.last_interaction = datetime.utcnow()
        context.interaction_count += 1
        
        # Update conversation summary if needed
        if context.interaction_count > 5:  # Summarize after 5 interactions
            summary = f"User has had {context.interaction_count} interactions about healthcare navigation."
            context.conversation_summary = summary
    
    def get_conversation_history(
        self,
        user_id: str,
        session_id: str
    ) -> List[Dict[str, str]]:
        """
        Get conversation history for a user session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            List of conversation messages
        """
        conversation_key = f"{user_id}_{session_id}"
        
        if conversation_key in self.active_conversations:
            context = self.active_conversations[conversation_key]
            return [
                {
                    "summary": context.conversation_summary or "New conversation",
                    "interaction_count": str(context.interaction_count),
                    "last_interaction": context.last_interaction.isoformat()
                }
            ]
        
        return []
    
    def clear_conversation(self, user_id: str, session_id: str) -> None:
        """
        Clear conversation context for a user session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
        """
        conversation_key = f"{user_id}_{session_id}"
        if conversation_key in self.active_conversations:
            del self.active_conversations[conversation_key]
            self.logger.info(f"Cleared conversation context for {conversation_key}")
    
    def reset(self) -> None:
        """Reset the agent's state."""
        self.active_conversations.clear()
        self.logger.info("Reset Chat Communicator Agent state") 