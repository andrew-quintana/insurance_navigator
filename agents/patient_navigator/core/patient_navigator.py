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
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional, Union
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models import BaseLanguageModel
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import PydanticOutputParser

from agents.base_agent import BaseAgent
from agents.prompt_security.core.prompt_security import PromptSecurityAgent
from utils.prompt_loader import load_prompt

# Setup logging
logger = logging.getLogger("patient_navigator_agent")
if not logger.handlers:
    # Create logs directory if it doesn't exist
    log_dir = os.path.join("agents", "patient_navigator", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up file handler
    handler = logging.FileHandler(os.path.join(log_dir, "patient_navigator.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Define output schema for patient navigator
class BodyRegion(BaseModel):
    """Schema for body region information."""
    region: Optional[str] = Field(description="Body region mentioned", default=None)
    side: Optional[str] = Field(description="Side of the body (left/right)", default=None)
    subpart: Optional[str] = Field(description="Specific subpart of the region", default=None)

class ClinicalContext(BaseModel):
    """Schema for clinical context."""
    symptom: Optional[str] = Field(description="Reported symptom", default=None)
    body: BodyRegion = Field(description="Body region information", default_factory=BodyRegion)
    onset: Optional[str] = Field(description="When the symptom started", default=None)
    duration: Optional[str] = Field(description="Duration of the symptom", default=None)

class ServiceIntent(BaseModel):
    """Schema for service intent."""
    specialty: Optional[str] = Field(description="Medical specialty", default=None)
    service: Optional[str] = Field(description="Specific service requested", default=None)
    plan_detail_type: Optional[str] = Field(description="Type of plan detail being requested", default=None)

class MetaIntent(BaseModel):
    """Schema for meta intent."""
    request_type: str = Field(description="Type of request (expert_request, service_request, symptom_report, policy_question, security_warning)")
    summary: str = Field(description="Summary of the user's request")
    emergency: Union[bool, str] = Field(description="Whether this is an emergency (true/false/unsure)")

class Metadata(BaseModel):
    """Schema for metadata."""
    raw_user_text: str = Field(description="Original user input")
    user_response_created: str = Field(description="Response created for the user")
    timestamp: str = Field(description="ISO 8601 timestamp")

class NavigatorOutput(BaseModel):
    """Schema for the navigator's output."""
    meta_intent: MetaIntent
    clinical_context: ClinicalContext
    service_intent: ServiceIntent
    metadata: Metadata

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
        
        self.output_parser = PydanticOutputParser(pydantic_object=NavigatorOutput)
        
        # Store reference to other agents
        self.prompt_security_agent = prompt_security_agent
        
        # Active conversations (in a real system, this would be in a database)
        self.active_conversations = {}
        
        # Load the system prompt
        try:
            self.system_prompt = load_prompt("patient_navigator")
        except FileNotFoundError:
            self.logger.warning("Could not find patient_navigator.md prompt file, using default prompt")
            self.system_prompt = """
            You are an expert Patient Navigation Coordinator with deep knowledge in clinical workflows, patient communication, and multi-agent delegation.
            Your task is to interpret and clarify the user's intent based on their input, format it into a structured intent package, and route it to the appropriate internal agent for handling.
            """
        
        # Define the prompt template
        self.prompt_template = PromptTemplate(
            template="""
            {system_prompt}
            
            Follow these examples:
            
            {examples}
            
            Now, apply the same pattern to:
            
            Input:
            {user_query}
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "examples", "user_query"],
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )
        
        # Create the chain
        self.chain = (
            {"system_prompt": lambda _: self.system_prompt,
             "examples": lambda _: self._load_examples(),
             "user_query": lambda x: x["user_query"]}
            | self.prompt_template
            | self.llm
            | self.output_parser
        )
        
        logger.info("Patient Navigator Agent initialized")
    
    def _load_examples(self) -> str:
        """Load the example prompts from the examples file."""
        try:
            with open("agents/patient_navigator/prompts/examples/examples_patient_navigator.json", "r") as f:
                examples = json.load(f)
            
            # Format examples as a string
            examples_str = ""
            for example in examples:
                examples_str += f"Input:\n{example['input']}\nOutput:\n{json.dumps(example['output'], indent=2)}\n\n"
            
            return examples_str
        except Exception as e:
            self.logger.error(f"Error loading examples: {str(e)}")
            return ""
    
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
            return user_query.strip()
    
    @BaseAgent.track_performance
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
        start_time = time.time()
        
        # Log the request
        self.logger.info(f"Processing query for user {user_id}: {user_query[:50]}...")
        
        try:
            # Sanitize the input
            sanitized_query = self._sanitize_input(user_query)
            
            # Prepare the input for the chain
            input_dict = {
                "user_query": sanitized_query
            }
            
            # Process the query
            result = self.chain.invoke(input_dict)
            
            # Add timestamp if not present
            if not result.metadata.timestamp:
                result.metadata.timestamp = datetime.utcnow().isoformat() + "Z"
            
            # Convert to dict for return
            result_dict = result.model_dump()
            
            # Log the result
            self.logger.info(f"Query processed. Request type: {result.meta_intent.request_type}, Emergency: {result.meta_intent.emergency}")
            
            # Log execution time
            execution_time = time.time() - start_time
            self.logger.info(f"Query processing completed in {execution_time:.2f}s")
            
            return result.metadata.user_response_created, result_dict
            
        except Exception as e:
            self.logger.error(f"Error in query processing: {str(e)}")
            
            # Return a basic response in case of error
            error_response = {
                "meta_intent": {
                    "request_type": "error",
                    "summary": "Error processing request",
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
                    "user_response_created": "I apologize, but I encountered an error while processing your request. Could you please rephrase your question or try again later?",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
            
            return error_response["metadata"]["user_response_created"], error_response

# Example usage
if __name__ == "__main__":
    # Initialize the agent
    agent = PatientNavigatorAgent()
    
    # Test with a sample query
    user_query = "I'm turning 65 next month and need to sign up for Medicare. Can you help me understand my options?"
    user_id = os.getenv('USER_ID')
    session_id = os.getenv('SESSION_ID')
    
    response_text, result = agent.process(user_query, user_id, session_id)
    
    print("User:", user_query)
    print("Navigator:", response_text)
    print("\nFull Result:")
    print(json.dumps(result, indent=2)) 