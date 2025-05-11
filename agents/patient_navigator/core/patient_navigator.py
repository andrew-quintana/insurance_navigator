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
from typing import Dict, List, Any, Tuple, Optional, Union
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models import BaseLanguageModel
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import PydanticOutputParser

from agents.base_agent import BaseAgent
from agents.prompt_security_agent import PromptSecurityAgent
from utils.prompt_loader import load_prompt

# Setup logging
logger = logging.getLogger("patient_navigator_agent")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join("logs", "agents", "patient_navigator.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Ensure logs directory exists
os.makedirs(os.path.join("logs", "agents"), exist_ok=True)

# Define output schema for user query analysis
class UserQueryAnalysis(BaseModel):
    """Schema for analyzing user queries."""
    query_type: str = Field(description="Type of query (e.g., 'information', 'guidance', 'complaint')")
    topics: List[str] = Field(description="Topics mentioned in the query", default_factory=list)
    intent: str = Field(description="User's primary intent")
    entities: Dict[str, Any] = Field(description="Named entities in the query", default_factory=dict)
    sentiment: str = Field(description="Sentiment of the query (positive, negative, neutral)")
    required_info: List[str] = Field(description="Information needed to address the query", default_factory=list)
    missing_info: List[str] = Field(description="Information missing from the query", default_factory=list)
    suggested_response_approach: str = Field(description="Suggested approach for responding")
    confidence: float = Field(description="Confidence in the analysis (0-1)")

# Define output schema for agent response
class NavigatorResponse(BaseModel):
    """Schema for the agent's response."""
    response_text: str = Field(description="Text response to the user")
    needs_followup: bool = Field(description="Whether follow-up is needed")
    followup_questions: List[str] = Field(description="Suggested follow-up questions", default_factory=list)
    agent_actions: List[str] = Field(description="Actions taken by the agent", default_factory=list)
    referenced_info: Dict[str, Any] = Field(description="Information referenced in the response", default_factory=dict)
    confidence: float = Field(description="Confidence in the response (0-1)")

# Define the conversation context model
class ConversationContext(BaseModel):
    """Schema for tracking conversation context."""
    user_id: str = Field(description="User identifier")
    session_id: str = Field(description="Session identifier")
    conversation_history: List[Dict[str, Any]] = Field(description="History of the conversation", default_factory=list)
    user_profile: Dict[str, Any] = Field(description="User profile information", default_factory=dict)
    topics_discussed: List[str] = Field(description="Topics discussed in the conversation", default_factory=list)
    current_focus: Optional[str] = Field(description="Current focus of the conversation", default=None)
    last_update_time: float = Field(description="Timestamp of the last update")

class PatientNavigatorAgent(BaseAgent):
    """Agent responsible for front-facing interactions with users."""
    
    def __init__(self, 
                 llm: Optional[BaseLanguageModel] = None,
                 prompt_security_agent: Optional[PromptSecurityAgent] = None):
        """
        Initialize the Patient Navigator Agent.
        
        Args:
            llm: An optional language model to use
            prompt_security_agent: An optional reference to the Prompt Security Agent
        """
        # Initialize the base agent
        super().__init__(name="patient_navigator", llm=llm or ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0.3))
        
        self.analysis_parser = PydanticOutputParser(pydantic_object=UserQueryAnalysis)
        self.response_parser = PydanticOutputParser(pydantic_object=NavigatorResponse)
        
        # Store reference to other agents
        self.prompt_security_agent = prompt_security_agent
        
        # Active conversations (in a real system, this would be in a database)
        self.active_conversations = {}
        
        # Define system prompt for the navigator
        # Load the self.system_prompt from file
        try:
            self.system_prompt = load_prompt("patient_navigator")
        except FileNotFoundError:
            self.logger.warning("Could not find patient_navigator.md prompt file, using default prompt")
            # Load the self.system_prompt from file
        try:
            self.system_prompt = load_prompt("patient_navigator")
        except FileNotFoundError:
            self.logger.warning("Could not find patient_navigator.md prompt file, using default prompt")
            self.system_prompt = """
            Default prompt for self.system_prompt. Replace with actual prompt if needed.
            """
        
        
        
        # Define the query analysis template
        self.analysis_template = PromptTemplate(
            template="""
            {system_prompt}
            
            USER QUERY: {user_query}
            
            CONVERSATION CONTEXT:
            {conversation_context}
            
            Analyze this user query to understand the user's needs and intent.
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "user_query", "conversation_context"],
            partial_variables={"format_instructions": self.analysis_parser.get_format_instructions()}
        )
        
        # Define the response generation template
        self.response_template = PromptTemplate(
            template="""
            {system_prompt}
            
            USER QUERY: {user_query}
            
            QUERY ANALYSIS:
            {query_analysis}
            
            CONVERSATION CONTEXT:
            {conversation_context}
            
            Generate a helpful and informative response to the user's query.
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "user_query", "query_analysis", "conversation_context"],
            partial_variables={"format_instructions": self.response_parser.get_format_instructions()}
        )
        
        # Create the analysis chain
        self.analysis_chain = (
            {"system_prompt": lambda _: self.system_prompt,
             "user_query": lambda x: x["user_query"],
             "conversation_context": lambda x: json.dumps(x["conversation_context"])}
            | self.analysis_template
            | self.llm
            | self.analysis_parser
        )
        
        # Create the response chain
        self.response_chain = (
            {"system_prompt": lambda _: self.system_prompt,
             "user_query": lambda x: x["user_query"],
             "query_analysis": lambda x: json.dumps(x["query_analysis"]),
             "conversation_context": lambda x: json.dumps(x["conversation_context"])}
            | self.response_template
            | self.llm
            | self.response_parser
        )
        
        logger.info("Patient Navigator Agent initialized")
    
    def _sanitize_input(self, user_query: str) -> str:
        """
        Sanitize user input using the Prompt Security Agent or a basic sanitizer.
        
        Args:
            user_query: The user's query
            
        Returns:
            Sanitized query
        """
        if self.prompt_security_agent:
            # Use the Prompt Security Agent to sanitize the input
            result = self.prompt_security_agent.analyze_prompt(user_query)
            
            if not result["is_safe"]:
                self.logger.warning(f"Potentially unsafe query detected: {user_query}")
                self.logger.warning(f"Safety concerns: {', '.join(result['safety_concerns'])}")
                
                # If the query is unsafe but can be sanitized, use the sanitized version
                if result["sanitized_content"]:
                    return result["sanitized_content"]
                
                # If the query is completely unsafe, return a safety message
                return "I'm unable to process this request as it appears to contain unsafe content."
            
            # Return the original query if it's safe, or the sanitized version if provided
            return result["sanitized_content"] or user_query
        else:
            # Basic sanitization if no security agent is available
            # This is a very simplistic approach and should be replaced with proper sanitization
            return user_query.strip()
    
    def _get_conversation_context(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Get the conversation context for a user.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Conversation context
        """
        context_key = f"{user_id}:{session_id}"
        
        if context_key in self.active_conversations:
            return self.active_conversations[context_key].dict()
        
        # Create a new conversation context
        context = ConversationContext(
            user_id=user_id,
            session_id=session_id,
            conversation_history=[],
            user_profile={},
            topics_discussed=[],
            current_focus=None,
            last_update_time=time.time()
        )
        
        self.active_conversations[context_key] = context
        return context.dict()
    
    def _update_conversation_context(self, user_id: str, session_id: str, 
                                   user_query: str, query_analysis: Dict[str, Any], 
                                   response: Dict[str, Any]) -> None:
        """
        Update the conversation context with the new query and response.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            user_query: User query
            query_analysis: Analysis of the query
            response: Agent response
        """
        context_key = f"{user_id}:{session_id}"
        
        if context_key not in self.active_conversations:
            # Create a new conversation context if it doesn't exist
            self._get_conversation_context(user_id, session_id)
        
        context = self.active_conversations[context_key]
        
        # Add the new exchange to the conversation history
        exchange = {
            "timestamp": time.time(),
            "user_query": user_query,
            "analysis": query_analysis,
            "response": response
        }
        
        context.conversation_history.append(exchange)
        
        # Update topics discussed
        if "topics" in query_analysis:
            for topic in query_analysis["topics"]:
                if topic not in context.topics_discussed:
                    context.topics_discussed.append(topic)
        
        # Update current focus
        if "intent" in query_analysis:
            context.current_focus = query_analysis["intent"]
        
        # Update timestamp
        context.last_update_time = time.time()
        
        # In a real system, we would also persist this to a database
    
    @BaseAgent.track_performance
    def analyze_query(self, user_query: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Analyze a user query to understand the user's needs and intent.
        
        Args:
            user_query: The user's query
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Analysis of the query
        """
        start_time = time.time()
        
        # Log the request
        self.logger.info(f"Analyzing query for user {user_id}: {user_query[:50]}...")
        
        try:
            # Sanitize the input
            sanitized_query = self._sanitize_input(user_query)
            
            # Get the conversation context
            conversation_context = self._get_conversation_context(user_id, session_id)
            
            # Prepare the input for the analysis chain
            input_dict = {
                "user_query": sanitized_query,
                "conversation_context": conversation_context
            }
            
            # Analyze the query
            analysis = self.analysis_chain.invoke(input_dict)
            result = analysis.dict()
            
            # Log the result
            self.logger.info(f"Query analysis complete. Intent: {result['intent']}, Confidence: {result['confidence']}")
            
            # Log execution time
            execution_time = time.time() - start_time
            self.logger.info(f"Query analysis completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in query analysis: {str(e)}")
            
            # Return a basic analysis in case of error
            return {
                "query_type": "unknown",
                "topics": [],
                "intent": "unknown",
                "entities": {},
                "sentiment": "neutral",
                "required_info": [],
                "missing_info": ["Complete analysis due to error"],
                "suggested_response_approach": "Apologize for the error and ask for clarification",
                "confidence": 0.0
            }
    
    @BaseAgent.track_performance
    def generate_response(self, user_query: str, query_analysis: Dict[str, Any], 
                         user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Generate a response to the user's query.
        
        Args:
            user_query: The user's query
            query_analysis: Analysis of the query
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Response to the user
        """
        start_time = time.time()
        
        # Log the request
        self.logger.info(f"Generating response for user {user_id}")
        
        try:
            # Get the conversation context
            conversation_context = self._get_conversation_context(user_id, session_id)
            
            # Prepare the input for the response chain
            input_dict = {
                "user_query": user_query,
                "query_analysis": query_analysis,
                "conversation_context": conversation_context
            }
            
            # Generate the response
            response = self.response_chain.invoke(input_dict)
            result = response.dict()
            
            # Update the conversation context
            self._update_conversation_context(user_id, session_id, user_query, query_analysis, result)
            
            # Log the result
            self.logger.info(f"Response generated. Needs follow-up: {result['needs_followup']}, Confidence: {result['confidence']}")
            
            # Log execution time
            execution_time = time.time() - start_time
            self.logger.info(f"Response generation completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in response generation: {str(e)}")
            
            # Return a basic response in case of error
            return {
                "response_text": "I apologize, but I encountered an error while processing your request. Could you please rephrase your question or try again later?",
                "needs_followup": True,
                "followup_questions": ["Could you please rephrase your question?"],
                "agent_actions": ["Error recovery"],
                "referenced_info": {},
                "confidence": 0.0
            }
    
    def process(self, user_query: str, user_id: str, session_id: str) -> Tuple[str, Dict[str, Any]]:
        """
        Process a user query and generate a response.
        
        Args:
            user_query: The user's query
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Tuple of (response_text, full_result)
        """
        # Analyze the query
        query_analysis = self.analyze_query(user_query, user_id, session_id)
        
        # Generate a response
        response = self.generate_response(user_query, query_analysis, user_id, session_id)
        
        return response["response_text"], response

# Example usage
if __name__ == "__main__":
    # Initialize the agent
    agent = PatientNavigatorAgent()
    
    # Test with a sample query
    user_query = "I'm turning 65 next month and need to sign up for Medicare. Can you help me understand my options?"
    user_id = os.getenv('USER_ID')
    session_id = os.getenv('SESSION_ID')
    # Ensure to set the USER_ID and SESSION_ID environment variables in your environment or .env file
    
    response_text, result = agent.process(user_query, user_id, session_id)
    
    print("User:", user_query)
    print("Navigator:", response_text)
    print("\nFollow-up Questions:")
    for question in result["followup_questions"]:
        print(f"- {question}")
    print(f"\nConfidence: {result['confidence']}") 