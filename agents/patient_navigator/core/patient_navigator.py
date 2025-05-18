"""
Patient Navigator Agent

This agent is responsible for:
1. Serving as the front-facing chatbot for users
2. Understanding user needs and questions
3. Providing clear and accessible information about Medicare
4. Coordinating with other specialized agents 
5. Maintaining a conversational and helpful tone

Based on FMEA analysis, this agent implements controls for:
- Misinterpreting user queries
- Providing outdated or incorrect information
- Maintaining context across conversation turns
- Handling sensitive personal information appropriately
- Managing handoffs to other agents
"""

import os
import json
import logging
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional, Union
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models import BaseLanguageModel
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import PydanticOutputParser

# Import base agent and exceptions
from agents.base_agent import BaseAgent
from agents.common.exceptions import (
    PatientNavigatorException, 
    PatientNavigatorProcessingError,
    PatientNavigatorOutputParsingError, 
    PatientNavigatorSessionError
)

# Import configuration handling
from utils.config_manager import ConfigManager

# Import models
from agents.patient_navigator.models.navigator_models import (
    NavigatorOutput, MetaIntent, ClinicalContext, 
    ServiceIntent, Metadata, BodyLocation
)

# Setup logger
logger = logging.getLogger(__name__)


class PatientNavigatorAgent(BaseAgent):
    """Agent responsible for front-facing interactions with users."""
    
    def __init__(self, 
                 llm: Optional[BaseLanguageModel] = None,
                 prompt_security_agent = None,
                 config_manager: Optional[ConfigManager] = None):
        """
        Initialize the Patient Navigator Agent.
        
        Args:
            llm: An optional language model to use
            prompt_security_agent: An optional reference to the Prompt Security Agent
            config_manager: Configuration manager instance
        """
        # Get configuration manager if not provided
        self.config_manager = config_manager or ConfigManager()
        
        # Get agent configuration
        agent_config = self.config_manager.get_agent_config("patient_navigator")
        
        # Get model configuration
        model_config = agent_config.get("model", {})
        model_name = model_config.get("name", "claude-3-sonnet-20240229-v1h")
        temperature = model_config.get("temperature", 0.0)
        
        # Get prompt configuration
        prompt_path = agent_config.get("prompt", {}).get("path")
        examples_path = agent_config.get("examples", {}).get("path")
        
        # Initialize the base agent
        super().__init__(
            name="patient_navigator", 
            llm=llm or ChatAnthropic(model=model_name, temperature=temperature),
            config_manager=self.config_manager
        )
        
        # Initialize the output parser
        self.output_parser = PydanticOutputParser(pydantic_object=NavigatorOutput)
        
        # Store reference to the prompt security agent
        self.prompt_security_agent = prompt_security_agent
        
        # Active conversations (in a real system, this would be in a database)
        self.active_conversations = {}
        
        # Load prompt template and examples
        self.system_prompt = self._load_prompt(prompt_path, examples_path)
        
        # Define the prompt template
        self.prompt_template = PromptTemplate(
            template="""
            {system_prompt}
            
            Input:
            {user_query}
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "user_query"],
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )
        
        # Create the chain
        self.chain = (
            {"system_prompt": lambda _: self.system_prompt,
             "user_query": lambda x: x["user_query"]}
            | self.prompt_template
            | self.llm
            | self.output_parser
        )
        
        logger.info(f"Patient Navigator Agent initialized with model {model_name}")

    # Using BaseAgent's _load_prompt method instead of a custom implementation
    
    def _check_security(self, user_query: str) -> Tuple[bool, Optional[str]]:
        """
        Check if the user query passes security checks.
        
        Args:
            user_query: The user's query to check
            
        Returns:
            Tuple of (passed, reason) where passed is a boolean and reason is 
            a string explaining why it didn't pass (if applicable)
        """
        if not self.prompt_security_agent:
            # No security agent available, assume safe
            return True, None
            
        try:
            # Check security using the prompt security agent
            is_safe, confidence, issues = self.prompt_security_agent.validate_prompt(user_query)
            
            if not is_safe:
                issues_str = ", ".join(issues) if issues else "Unknown security issues"
                return False, f"Security check failed: {issues_str}"
                
            return True, None
            
        except Exception as e:
            logger.warning(f"Error in security check: {str(e)}")
            # On error, allow the query but log the issue
            return True, f"Security check error: {str(e)}"
            
    def _handle_context(self, user_id: str, session_id: str, result: Dict[str, Any]) -> None:
        """
        Handle conversation context updates.
        
        Args:
            user_id: The ID of the user
            session_id: The ID of the session
            result: The result of processing the query
        """
        conversation_key = f"{user_id}:{session_id}"
        
        if conversation_key not in self.active_conversations:
            self.active_conversations[conversation_key] = {
                "history": [],
                "session_start": datetime.utcnow().isoformat() + "Z",
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
            
        # Update conversation history
        self.active_conversations[conversation_key]["history"].append({
            "timestamp": result.get("metadata", {}).get("timestamp") or (datetime.utcnow().isoformat() + "Z"),
            "meta_intent": result.get("meta_intent", {}),
            "raw_user_text": result.get("metadata", {}).get("raw_user_text", ""),
            "response": result.get("metadata", {}).get("user_response_created", "")
        })
        
        # Update last updated timestamp
        self.active_conversations[conversation_key]["last_updated"] = datetime.utcnow().isoformat() + "Z"

    @BaseAgent.track_performance
    def process(self, user_query: str, user_id: str, session_id: str) -> Tuple[str, Dict[str, Any]]:
        """
        Process a user query and return a response.
        
        Args:
            user_query: The user's query
            user_id: The ID of the user
            session_id: The ID of the session
            
        Returns:
            Tuple of (response_text, structured_output) where response_text is the text to 
            show to the user and structured_output is the full structured output
            
        Raises:
            PatientNavigatorProcessingError: If there is an error processing the query
            PatientNavigatorOutputParsingError: If there is an error parsing the output
            PatientNavigatorSessionError: If there is an error managing the session
        """
        start_time = time.time()
        
        try:
            # Log the incoming query (sanitized)
            logger.info(f"Processing query from user {user_id} - Length: {len(user_query)} chars")
            
            # Security check
            passed_security, security_reason = self._check_security(user_query)
            if not passed_security:
                logger.warning(f"Security check failed for user {user_id}: {security_reason}")
                error_response = {
                    "meta_intent": {
                        "request_type": "security_issue",
                        "summary": "Security issue detected",
                        "emergency": False
                    },
                    "clinical_context": {
                        "symptom": None,
                        "body": {"region": None, "side": None, "subpart": None},
                        "onset": None,
                        "duration": None
                    },
                    "service_intent": {
                        "specialty": None,
                        "service": None,
                        "plan_detail_type": None
                    },
                    "metadata": {
                        "raw_user_text": user_query,
                        "user_response_created": f"I apologize, but I cannot process this request. {security_reason}. Please rephrase your question.",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                }
                return error_response["metadata"]["user_response_created"], error_response
            
            # Process the query
            logger.info("Calling language model...")
            raw_response = self.llm.invoke(self.prompt_template.format(
                system_prompt=self.system_prompt,
                user_query=user_query,
                format_instructions=self.output_parser.get_format_instructions()
            ))
            
            # Try to parse the response
            try:
                logger.info("Parsing response with output parser...")
                result = self.output_parser.parse(str(raw_response))
                logger.info("Successfully parsed LLM response to NavigatorOutput")
                
                # Convert to dict for return
                result_dict = result.model_dump()
                
            except Exception as e:
                logger.error(f"Parser error: {str(e)}")
                logger.error(f"Failed to parse text: {str(raw_response)[:500]}")
                raise PatientNavigatorOutputParsingError(f"Failed to parse model output: {str(e)}")
            
            # Add timestamp if not present
            if not result_dict.get("metadata", {}).get("timestamp"):
                result_dict["metadata"]["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
            # Update conversation context
            try:
                self._handle_context(user_id, session_id, result_dict)
            except Exception as e:
                logger.error(f"Error updating conversation context: {str(e)}")
                logger.error(traceback.format_exc())
                raise PatientNavigatorSessionError(f"Failed to update session: {str(e)}")
            
            # Log the result
            logger.info(f"Query processed. Request type: {result_dict['meta_intent']['request_type']}, Emergency: {result_dict['meta_intent']['emergency']}")
            
            # Log execution time
            execution_time = time.time() - start_time
            logger.info(f"Query processing completed in {execution_time:.2f}s")
            
            return result_dict["metadata"]["user_response_created"], result_dict
            
        except PatientNavigatorException:
            # Re-raise specific exceptions without wrapping
            raise
            
        except Exception as e:
            logger.error(f"Error in query processing: {str(e)}")
            logger.error(f"Error details:\n{traceback.format_exc()}")
            
            # Wrap in a PatientNavigatorProcessingError
            raise PatientNavigatorProcessingError(f"Error processing query: {str(e)}") from e

    def get_conversation_history(self, user_id: str, session_id: str) -> List[Dict[str, Any]]:
        """
        Get the conversation history for a user session.
        
        Args:
            user_id: The ID of the user
            session_id: The ID of the session
            
        Returns:
            The conversation history as a list of interactions
            
        Raises:
            PatientNavigatorSessionError: If the session doesn't exist
        """
        conversation_key = f"{user_id}:{session_id}"
        
        if conversation_key not in self.active_conversations:
            raise PatientNavigatorSessionError(f"No active conversation found for session {session_id}")
            
        return self.active_conversations[conversation_key]["history"]

    def end_conversation(self, user_id: str, session_id: str) -> None:
        """
        End a conversation and clean up resources.
        
        Args:
            user_id: The ID of the user
            session_id: The ID of the session
            
        Raises:
            PatientNavigatorSessionError: If the session doesn't exist
        """
        conversation_key = f"{user_id}:{session_id}"
        
        if conversation_key not in self.active_conversations:
            raise PatientNavigatorSessionError(f"No active conversation found for session {session_id}")
            
        # In a real system, this might archive the conversation to a database
        del self.active_conversations[conversation_key]
        logger.info(f"Ended conversation for user {user_id}, session {session_id}")

    def reset(self) -> None:
        """Reset the agent's state."""
        self.active_conversations = {}
        logger.info("Reset PatientNavigatorAgent state - all conversations cleared")

    def _initialize_agent(self):
        """Initialize agent-specific components."""
        # Get paths from configuration
        try:
            prompt_path = self.prompt_path
            examples_path = self.examples_path
        except AttributeError:
            # Use default paths if not available
            prompt_path = "agents/patient_navigator/prompts/prompt_navigator_v0_1.md"
            examples_path = "agents/patient_navigator/prompts/examples/navigator_examples_v0_1.json"
            
        # Default prompt if path is not found
        default_prompt = """
        You are an expert Patient Navigation Coordinator with deep knowledge in clinical workflows, 
        patient communication, and multi-agent delegation.
        
        Your task is to interpret and clarify the user's intent based on their input, 
        format it into a structured intent package, and route it to the appropriate 
        internal agent for handling.
        """
        
        # Load examples if available
        examples = []
        try:
            examples = self._load_examples(examples_path, default_examples=[])
            if examples:
                examples_text = "\n\nExamples:\n\n" + json.dumps(examples, indent=2)
                default_prompt += examples_text
        except Exception as e:
            self.logger.warning(f"Failed to load examples: {e}")
        
        # Load prompt from file
        self.system_prompt = self._load_prompt(prompt_path, default_prompt=default_prompt)
        
        # Create output parser for navigator response
        self.output_parser = PydanticOutputParser(pydantic_object=NavigatorOutput)
        
        # Create prompt template
        self.prompt_template = """
        {system_prompt}
        
        USER QUERY: {user_query}
        
        {format_instructions}
        """
        
        # Initialize conversation tracking
        self.active_conversations = {}

# Example usage
if __name__ == "__main__":
    # Initialize the agent
    agent = PatientNavigatorAgent()
    
    # Test with a sample query
    user_query = "I'm turning 65 next month and need to sign up for Medicare. Can you help me understand my options?"
    user_id = os.getenv('USER_ID', 'default_user')
    session_id = os.getenv('SESSION_ID', 'default_session')
    
    response_text, result = agent.process(user_query, user_id, session_id)
    
    print("User:", user_query)
    print("Navigator:", response_text)
    print("\nFull Result:")
    print(json.dumps(result, indent=2)) 