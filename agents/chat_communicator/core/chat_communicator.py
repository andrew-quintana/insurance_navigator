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
- Persistent conversation management with database integration
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

# Import database conversation service
from db.services.conversation_service import get_conversation_service

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
        
        # Initialize conversation service (will be async-initialized)
        self.conversation_service = None
        self._conversation_service_initialized = False
        
        # Initialize the output parser for ChatResponse BEFORE calling super().__init__()
        self.output_parser = PydanticOutputParser(pydantic_object=ChatResponse)
        
        # Set default paths (will be overridden in _initialize_agent if config available)
        self.prompt_path = "agents/chat_communicator/core/prompts/prompt_chat_communicator_v0_1.md"
        self.examples_path = "agents/chat_communicator/core/prompts/examples/chat_examples_v0_1.json"
        
        # Initialize the base agent (this calls _initialize_agent automatically)
        super().__init__(
            name="chat_communicator",
            llm=llm or (None if use_mock else ChatAnthropic(model=model_name, temperature=temperature)),
            use_mock=use_mock
        )
        
        logger.info(f"Chat Communicator Agent initialized with model {model_name}")
    
    async def _ensure_conversation_service(self) -> None:
        """Ensure conversation service is initialized (async operation)."""
        if not self._conversation_service_initialized:
            try:
                self.conversation_service = await get_conversation_service()
                self._conversation_service_initialized = True
                logger.info("Conversation service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize conversation service: {e}")
                # Use in-memory fallback for mock/testing
                self.conversation_service = None
    
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
    async def _process_data(self, input_data: ChatInput) -> ChatResponse:
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
            
            # Ensure conversation service is available
            await self._ensure_conversation_service()
            
            # Get conversation history from database if available
            conversation_history = []
            if self.conversation_service and input_data.user_id and input_data.session_id:
                try:
                    conversation_history = await self.conversation_service.get_conversation_history(
                        input_data.session_id, 
                        limit=10
                    )
                except Exception as e:
                    logger.warning(f"Could not load conversation history: {e}")
            
            # Prepare data for the LLM
            input_dict = {
                "input_data": json.dumps(input_data.data.model_dump() if hasattr(input_data.data, 'model_dump') else input_data.data),
                "user_id": input_data.user_id or "anonymous",
                "session_id": input_data.session_id or "new_session",
                "conversation_history": json.dumps(conversation_history),
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
    
    async def process_navigator_output(
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
            conversation_history: Previous conversation messages (deprecated - loaded from DB)
            
        Returns:
            Conversational response dictionary
        """
        # Create or ensure conversation exists
        if user_id and session_id:
            await self._ensure_conversation_service()
            if self.conversation_service:
                try:
                    await self.conversation_service.create_conversation(
                        user_id=user_id,
                        conversation_id=session_id,
                        metadata={"source": "navigator_output"}
                    )
                except Exception as e:
                    logger.warning(f"Could not create conversation: {e}")
        
        chat_input = ChatInput(
            source_type="navigator_output",
            data=navigator_output,
            user_id=user_id,
            session_id=session_id,
            conversation_history=conversation_history or []
        )
        
        result = await self.process(chat_input.model_dump())
        
        # Store the conversation in database
        if user_id and session_id and self.conversation_service:
            try:
                # Store user message
                await self.conversation_service.add_message(
                    conversation_id=session_id,
                    role="user",
                    content=navigator_output.metadata.raw_user_text if hasattr(navigator_output, 'metadata') else "Navigator input",
                    agent_name="patient_navigator",
                    metadata={"source_type": "navigator_output"}
                )
                
                # Store agent response
                await self.conversation_service.add_message(
                    conversation_id=session_id,
                    role="assistant",
                    content=result["message"],
                    agent_name="chat_communicator",
                    metadata=result.get("metadata", {})
                )
            except Exception as e:
                logger.error(f"Failed to store conversation: {e}")
        
        return result
    
    async def process_service_strategy(
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
            conversation_history: Previous conversation messages (deprecated - loaded from DB)
            
        Returns:
            Conversational response dictionary
        """
        # Create or ensure conversation exists
        if user_id and session_id:
            await self._ensure_conversation_service()
            if self.conversation_service:
                try:
                    await self.conversation_service.create_conversation(
                        user_id=user_id,
                        conversation_id=session_id,
                        metadata={"source": "service_strategy"}
                    )
                except Exception as e:
                    logger.warning(f"Could not create conversation: {e}")
        
        chat_input = ChatInput(
            source_type="service_strategy",
            data=service_strategy,
            user_id=user_id,
            session_id=session_id,
            conversation_history=conversation_history or []
        )
        
        result = await self.process(chat_input.model_dump())
        
        # Store the conversation in database
        if user_id and session_id and self.conversation_service:
            try:
                # Store user request
                await self.conversation_service.add_message(
                    conversation_id=session_id,
                    role="user",
                    content=f"Service strategy request: {service_strategy.patient_need}",
                    agent_name="service_access_strategy",
                    metadata={"source_type": "service_strategy"}
                )
                
                # Store agent response
                await self.conversation_service.add_message(
                    conversation_id=session_id,
                    role="assistant",
                    content=result["message"],
                    agent_name="chat_communicator",
                    metadata=result.get("metadata", {})
                )
            except Exception as e:
                logger.error(f"Failed to store conversation: {e}")
        
        return result
    
    async def get_conversation_history(
        self,
        user_id: str,
        session_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history from persistent storage.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of conversation messages
        """
        await self._ensure_conversation_service()
        
        if self.conversation_service:
            try:
                return await self.conversation_service.get_conversation_history(
                    conversation_id=session_id,
                    limit=limit,
                    include_metadata=True
                )
            except Exception as e:
                logger.error(f"Failed to get conversation history: {e}")
        
        return []
    
    async def clear_conversation(self, user_id: str, session_id: str) -> bool:
        """
        Clear conversation context from persistent storage.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            True if conversation was cleared successfully
        """
        await self._ensure_conversation_service()
        
        if self.conversation_service:
            try:
                return await self.conversation_service.delete_conversation(
                    conversation_id=session_id,
                    user_id=user_id
                )
            except Exception as e:
                logger.error(f"Failed to clear conversation: {e}")
        
        return False
    
    async def save_agent_state(
        self,
        conversation_id: str,
        workflow_step: str,
        state_data: Dict[str, Any]
    ) -> None:
        """
        Save agent state for workflow persistence.
        
        Args:
            conversation_id: Conversation identifier
            workflow_step: Current workflow step
            state_data: State data to save
        """
        await self._ensure_conversation_service()
        
        if self.conversation_service:
            try:
                await self.conversation_service.save_agent_state(
                    conversation_id=conversation_id,
                    agent_name="chat_communicator",
                    state_data=state_data,
                    workflow_step=workflow_step
                )
            except Exception as e:
                logger.error(f"Failed to save agent state: {e}")
    
    async def get_agent_state(
        self,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get agent state from persistent storage.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Agent state data or None if not found
        """
        await self._ensure_conversation_service()
        
        if self.conversation_service:
            try:
                return await self.conversation_service.get_agent_state(
                    conversation_id=conversation_id,
                    agent_name="chat_communicator"
                )
            except Exception as e:
                logger.error(f"Failed to get agent state: {e}")
        
        return None
    
    def reset(self) -> None:
        """Reset the agent's state."""
        # For database-backed persistence, we don't clear everything
        # Only reset the conversation service initialization flag
        self._conversation_service_initialized = False
        self.conversation_service = None
        self.logger.info("Reset Chat Communicator Agent state") 