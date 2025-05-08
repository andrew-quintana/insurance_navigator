"""
Intent Structuring Agent

This agent is responsible for:
1. Identifying and categorizing user intents from natural language queries
2. Converting unstructured requests into structured, actionable intents
3. Identifying key parameters and constraints in user requests
4. Mapping intents to appropriate system capabilities
5. Supporting consistent intent resolution across the system

Based on FMEA analysis, this agent implements controls for:
- Intent misclassification
- Missing or ambiguous parameters
- Handling edge cases and unusual requests
- Tracking intent resolution confidence
- Supporting contextual intent refinement
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Tuple, Optional, Union
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models import BaseLanguageModel
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser

from agents.base_agent import BaseAgent
from utils.prompt_loader import load_prompt

# Setup logging
logger = logging.getLogger("intent_structuring_agent")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join("logs", "agents", "intent_structuring.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Ensure logs directory exists
os.makedirs(os.path.join("logs", "agents"), exist_ok=True)

# Define output schema for structured intent
class IntentParameter(BaseModel):
    """Schema for a parameter in a structured intent."""
    name: str = Field(description="Name of the parameter")
    value: Optional[Any] = Field(description="Value of the parameter", default=None)
    required: bool = Field(description="Whether the parameter is required for the intent", default=False)
    confidence: float = Field(description="Confidence in the parameter value (0-1)", default=1.0)
    description: Optional[str] = Field(description="Description of the parameter", default=None)

class StructuredIntent(BaseModel):
    """Output schema for the structured intent."""
    intent_type: str = Field(description="Type of intent (e.g., 'find_provider', 'check_coverage')")
    intent_category: str = Field(description="Category of intent (e.g., 'information', 'service', 'complaint')")
    parameters: List[IntentParameter] = Field(description="Parameters for the intent", default_factory=list)
    description: str = Field(description="Description of the intent")
    constraints: List[str] = Field(description="Constraints on the intent", default_factory=list)
    related_intents: List[str] = Field(description="Related intents", default_factory=list)
    confidence: float = Field(description="Confidence in the intent classification (0-1)")
    context_required: bool = Field(description="Whether additional context is required", default=False)
    followup_questions: List[str] = Field(description="Follow-up questions to refine the intent", default_factory=list)
    needs_clarification: bool = Field(description="Whether clarification is needed", default=False)

class IntentStructuringAgent(BaseAgent):
    """Agent responsible for identifying and structuring user intents."""
    
    def __init__(self, llm: Optional[BaseLanguageModel] = None):
        """Initialize the agent with an optional language model."""
        # Initialize the base agent
        super().__init__(name="intent_structuring", llm=llm or ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0.2))
        
        self.intent_parser = PydanticOutputParser(pydantic_object=StructuredIntent)
        
        # Define system prompt for intent structuring
        # Load the self.system_prompt from file
        try:
            self.system_prompt = load_prompt("intent_structuring")
        except FileNotFoundError:
            self.logger.warning("Could not find intent_structuring.md prompt file, using default prompt")
            # Load the self.system_prompt from file
        try:
            self.system_prompt = load_prompt("intent_structuring")
        except FileNotFoundError:
            self.logger.warning("Could not find intent_structuring.md prompt file, using default prompt")
            self.system_prompt = """
            Default prompt for self.system_prompt. Replace with actual prompt if needed.
            """
        
        
        
        # Define the intent structuring prompt template
        self.intent_template = PromptTemplate(
            template="""
            {system_prompt}
            
            USER QUERY: {user_query}
            
            CONVERSATION CONTEXT:
            {conversation_context}
            
            Analyze this query to identify and structure the user's intent.
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "user_query", "conversation_context"],
            partial_variables={"format_instructions": self.intent_parser.get_format_instructions()}
        )
        
        # Create the intent structuring chain
        self.intent_chain = (
            {"system_prompt": lambda _: self.system_prompt,
             "user_query": lambda x: x["user_query"],
             "conversation_context": lambda x: x.get("conversation_context", "{}")}
            | self.intent_template
            | self.llm
            | self.intent_parser
        )
        
        # Initialize common intents and parameters for reference
        self._init_intent_references()
        
        logger.info("Intent Structuring Agent initialized")
    
    def _init_intent_references(self):
        """Initialize reference data for common intents and parameters."""
        # Common intent types and their parameters
        self.common_intents = {
            "find_provider": {
                "category": "service",
                "parameters": [
                    {"name": "specialty", "required": True, "description": "Medical specialty needed"},
                    {"name": "location", "required": True, "description": "Geographic location"},
                    {"name": "network_status", "required": False, "description": "In-network or out-of-network"},
                    {"name": "provider_type", "required": False, "description": "Type of provider (doctor, facility, etc.)"}
                ]
            },
            "check_coverage": {
                "category": "information",
                "parameters": [
                    {"name": "service_type", "required": True, "description": "Type of service or item"},
                    {"name": "plan_type", "required": False, "description": "Medicare plan type"},
                    {"name": "condition", "required": False, "description": "Medical condition"}
                ]
            },
            "explain_benefits": {
                "category": "information",
                "parameters": [
                    {"name": "benefit_type", "required": True, "description": "Type of benefit"},
                    {"name": "plan_type", "required": False, "description": "Medicare plan type"}
                ]
            },
            "enrollment_assistance": {
                "category": "service",
                "parameters": [
                    {"name": "plan_type", "required": True, "description": "Medicare plan type"},
                    {"name": "enrollment_period", "required": False, "description": "Enrollment period"},
                    {"name": "current_coverage", "required": False, "description": "Current insurance coverage"}
                ]
            },
            "claims_assistance": {
                "category": "service",
                "parameters": [
                    {"name": "claim_type", "required": True, "description": "Type of claim"},
                    {"name": "claim_status", "required": False, "description": "Status of the claim"},
                    {"name": "service_date", "required": False, "description": "Date of service"}
                ]
            },
            "compare_plans": {
                "category": "information",
                "parameters": [
                    {"name": "plan_types", "required": True, "description": "Types of plans to compare"},
                    {"name": "coverage_needs", "required": False, "description": "Specific coverage needs"},
                    {"name": "budget", "required": False, "description": "Budget constraints"},
                    {"name": "location", "required": False, "description": "Geographic location"}
                ]
            },
            "service_location": {
                "category": "service",
                "parameters": [
                    {"name": "service_type", "required": True, "description": "Type of service needed"},
                    {"name": "location", "required": True, "description": "Geographic location"}
                ]
            },
            "cost_information": {
                "category": "information",
                "parameters": [
                    {"name": "cost_type", "required": True, "description": "Type of cost (premium, deductible, etc.)"},
                    {"name": "service_type", "required": False, "description": "Type of service"},
                    {"name": "plan_type", "required": False, "description": "Medicare plan type"}
                ]
            },
            "eligibility_check": {
                "category": "information",
                "parameters": [
                    {"name": "benefit_type", "required": True, "description": "Type of benefit"},
                    {"name": "age", "required": False, "description": "User's age"},
                    {"name": "disability_status", "required": False, "description": "Disability status"}
                ]
            },
            "complaint_submission": {
                "category": "complaint",
                "parameters": [
                    {"name": "complaint_type", "required": True, "description": "Type of complaint"},
                    {"name": "provider_name", "required": False, "description": "Name of provider"},
                    {"name": "service_date", "required": False, "description": "Date of service"}
                ]
            }
        }
    
    def _enrich_intent(self, structured_intent: StructuredIntent) -> StructuredIntent:
        """
        Enrich the structured intent with additional information.
        
        Args:
            structured_intent: The structured intent to enrich
            
        Returns:
            Enriched structured intent
        """
        intent_type = structured_intent.intent_type
        
        # Check if we have reference information for this intent type
        if intent_type in self.common_intents:
            reference = self.common_intents[intent_type]
            
            # Add any missing parameters from the reference
            existing_param_names = [p.name for p in structured_intent.parameters]
            for ref_param in reference["parameters"]:
                if ref_param["name"] not in existing_param_names:
                    # Only add required parameters that are missing
                    if ref_param["required"]:
                        structured_intent.parameters.append(
                            IntentParameter(
                                name=ref_param["name"],
                                required=True,
                                confidence=0.0,
                                description=ref_param["description"]
                            )
                        )
            
            # Update the needs_clarification flag if required parameters are missing values
            for param in structured_intent.parameters:
                if param.required and param.value is None:
                    structured_intent.needs_clarification = True
                    
                    # Add follow-up question for this parameter if not already present
                    question = f"Could you please provide information about {param.name}?"
                    if question not in structured_intent.followup_questions:
                        structured_intent.followup_questions.append(question)
        
        return structured_intent
    
    @BaseAgent.track_performance
    def structure_intent(self, user_query: str, conversation_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Structure the user's intent from a natural language query.
        
        Args:
            user_query: The user's query
            conversation_context: Optional conversation context
            
        Returns:
            Structured intent
        """
        start_time = time.time()
        
        # Log the request
        self.logger.info(f"Structuring intent from query: {user_query[:50]}...")
        
        try:
            # Prepare input for the intent chain
            input_dict = {
                "user_query": user_query,
                "conversation_context": json.dumps(conversation_context or {})
            }
            
            # Structure the intent
            structured_intent = self.intent_chain.invoke(input_dict)
            
            # Enrich the structured intent
            enriched_intent = self._enrich_intent(structured_intent)
            
            # Convert to dictionary
            result = enriched_intent.dict()
            
            # Log the result
            self.logger.info(f"Intent structured as {result['intent_type']} with confidence {result['confidence']}")
            if result['needs_clarification']:
                self.logger.info(f"Clarification needed for intent: {', '.join([q for q in result['followup_questions']])}")
            
            # Log execution time
            execution_time = time.time() - start_time
            self.logger.info(f"Intent structuring completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in intent structuring: {str(e)}")
            
            # Return a basic intent in case of error
            return {
                "intent_type": "unknown",
                "intent_category": "unknown",
                "parameters": [],
                "description": "Failed to structure intent due to an error",
                "constraints": [],
                "related_intents": [],
                "confidence": 0.0,
                "context_required": True,
                "followup_questions": ["Could you please rephrase your question?"],
                "needs_clarification": True,
                "error": str(e)
            }
    
    def get_missing_parameters(self, structured_intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get a list of missing required parameters from a structured intent.
        
        Args:
            structured_intent: The structured intent
            
        Returns:
            List of missing parameters
        """
        missing_parameters = []
        
        for param in structured_intent.get("parameters", []):
            if param.get("required", False) and param.get("value") is None:
                missing_parameters.append({
                    "name": param.get("name"),
                    "description": param.get("description")
                })
        
        return missing_parameters
    
    def process(self, user_query: str, conversation_context: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], bool, List[str]]:
        """
        Process a user query to structure the intent.
        
        Args:
            user_query: The user's query
            conversation_context: Optional conversation context
            
        Returns:
            Tuple of (structured_intent, needs_clarification, followup_questions)
        """
        # Structure the intent
        structured_intent = self.structure_intent(user_query, conversation_context)
        
        needs_clarification = structured_intent.get("needs_clarification", False)
        followup_questions = structured_intent.get("followup_questions", [])
        
        return structured_intent, needs_clarification, followup_questions

# Example usage
if __name__ == "__main__":
    # Initialize the agent
    agent = IntentStructuringAgent()
    
    # Test with sample queries
    test_queries = [
        "I need to find a cardiologist in Boston who accepts Medicare",
        "Is my diabetes medication covered under my Medicare plan?",
        "Can you help me understand the different Medicare plans?",
        "I'm turning 65 next month and need to sign up for Medicare"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        intent, needs_clarification, followup_questions = agent.process(query)
        
        print(f"Intent Type: {intent['intent_type']}")
        print(f"Category: {intent['intent_category']}")
        print(f"Confidence: {intent['confidence']}")
        print("Parameters:")
        for param in intent['parameters']:
            value = param.get('value', 'Not provided')
            required = "Required" if param.get('required', False) else "Optional"
            print(f"  - {param['name']}: {value} ({required})")
        
        if needs_clarification:
            print("Clarification needed:")
            for question in followup_questions:
                print(f"  - {question}")
        
        print("---") 