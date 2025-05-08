"""
Healthcare Guide Developer Agent

This agent is responsible for:
1. Developing personalized healthcare navigation guides
2. Synthesizing information from policy analysis and provider data
3. Creating actionable instructions for accessing approved services
4. Coordinating with the Service Provider Agent for specific information
5. Developing prompts for the Guide to PDF Agent

Based on FMEA analysis, this agent implements controls for:
- Ensuring guides are accurate and up-to-date
- Validating information before inclusion in guides
- Providing clear and actionable instructions
- Redundant guide checks for quality assurance
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Tuple, Optional, Union
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableSequence
from langchain_core.language_models import BaseLanguageModel
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.tools import BaseTool

from agents.base_agent import BaseAgent
from utils.prompt_loader import load_prompt

# Setup logging
logger = logging.getLogger("healthcare_guide_agent")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join("logs", "agents", "healthcare_guide.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Ensure logs directory exists
os.makedirs(os.path.join("logs", "agents"), exist_ok=True)

# Define output schema for the guide content
class GuideSection(BaseModel):
    """Schema for a section in the healthcare guide."""
    title: str = Field(description="Title of the section")
    content: str = Field(description="Content of the section")
    order: int = Field(description="Order of the section in the guide")

class HealthcareGuide(BaseModel):
    """Output schema for the healthcare guide."""
    title: str = Field(description="Title of the guide")
    user_name: str = Field(description="Name of the user")
    summary: str = Field(description="Brief summary of the guide's purpose")
    sections: List[GuideSection] = Field(description="Sections of the guide", default_factory=list)
    action_items: List[str] = Field(description="List of specific action items for the user", default_factory=list)
    provider_details: Dict[str, Any] = Field(description="Details about recommended providers", default_factory=dict)
    important_contacts: Dict[str, str] = Field(description="Important contact information", default_factory=dict)
    next_steps: List[str] = Field(description="Suggested next steps for the user", default_factory=list)
    last_updated: str = Field(description="Timestamp of when the guide was last updated")

class HealthcareGuidePrompt(BaseModel):
    """Schema for the prompt to be sent to the Guide to PDF Agent."""
    guide_title: str = Field(description="Title for the guide")
    guide_purpose: str = Field(description="Purpose of the guide")
    user_info: Dict[str, Any] = Field(description="User information", default_factory=dict)
    policy_info: Dict[str, Any] = Field(description="Policy information", default_factory=dict)
    service_info: Dict[str, Any] = Field(description="Service information", default_factory=dict)
    provider_info: Dict[str, Any] = Field(description="Provider information", default_factory=dict)
    special_instructions: List[str] = Field(description="Special instructions for guide creation", default_factory=list)
    formatting_preferences: Dict[str, Any] = Field(description="Formatting preferences", default_factory=dict)

class HealthcareGuideAgent(BaseAgent):
    """Agent responsible for developing personalized healthcare navigation guides."""
    
    def __init__(self, 
                 llm: Optional[BaseLanguageModel] = None,
                 service_provider_agent: Optional[Any] = None):
        """
        Initialize the Healthcare Guide Developer Agent.
        
        Args:
            llm: An optional language model to use
            service_provider_agent: An optional reference to the Service Provider Agent
        """
        # Initialize the base agent
        super().__init__(name="healthcare_guide", llm=llm or ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0))
        
        self.guide_parser = PydanticOutputParser(pydantic_object=HealthcareGuide)
        self.prompt_parser = PydanticOutputParser(pydantic_object=HealthcareGuidePrompt)
        
        # Store reference to service provider agent for coordination
        self.service_provider_agent = service_provider_agent
        
        # Define system prompt for guide development
        # Load the self.system_prompt from file
        try:
            self.system_prompt = load_prompt("healthcare_guide")
        except FileNotFoundError:
            self.logger.warning("Could not find healthcare_guide.md prompt file, using default prompt")
            # Load the self.system_prompt from file
        try:
            self.system_prompt = load_prompt("healthcare_guide")
        except FileNotFoundError:
            self.logger.warning("Could not find healthcare_guide.md prompt file, using default prompt")
            self.system_prompt = """
            Default prompt for self.system_prompt. Replace with actual prompt if needed.
            """
        
        
        
        # Define the guide development prompt template
        self.guide_template = PromptTemplate(
            template="""
            {system_prompt}
            
            USER INFORMATION:
            {user_info}
            
            POLICY INFORMATION:
            {policy_info}
            
            SERVICE REQUIREMENTS:
            {service_info}
            
            PROVIDER INFORMATION:
            {provider_info}
            
            Based on this information, develop a comprehensive healthcare navigation guide.
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "user_info", "policy_info", "service_info", "provider_info"],
            partial_variables={"format_instructions": self.guide_parser.get_format_instructions()}
        )
        
        # Define the prompt development template
        self.prompt_template = PromptTemplate(
            template="""
            {system_prompt}
            
            GUIDE CONTENT:
            {guide_content}
            
            Based on this guide content, create a structured prompt for the Guide to PDF Agent.
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "guide_content"],
            partial_variables={"format_instructions": self.prompt_parser.get_format_instructions()}
        )
        
        # Create the guide development chain
        self.guide_chain = (
            {"system_prompt": lambda _: self.system_prompt,
             "user_info": lambda x: x["user_info"],
             "policy_info": lambda x: x["policy_info"],
             "service_info": lambda x: x["service_info"],
             "provider_info": lambda x: x["provider_info"]}
            | self.guide_template
            | self.llm
            | self.guide_parser
        )
        
        # Create the prompt development chain
        self.prompt_chain = (
            {"system_prompt": lambda _: "You are creating a prompt for the Guide to PDF Agent.",
             "guide_content": lambda x: json.dumps(x.dict())}
            | self.prompt_template
            | self.llm
            | self.prompt_parser
        )
        
        logger.info("Healthcare Guide Developer Agent initialized")
    
    def get_provider_info(self, service_type: str, location: str) -> Dict[str, Any]:
        """
        Get provider information from the Service Provider Agent.
        
        Args:
            service_type: Type of service needed
            location: User's location
            
        Returns:
            Dictionary with provider information
        """
        if not self.service_provider_agent:
            self.logger.warning("Service Provider Agent not available. Using placeholder data.")
            # Return placeholder data
            return {
                "providers": [
                    {
                        "name": "Example Medical Center",
                        "address": "123 Healthcare St, Example City",
                        "phone": "555-123-4567",
                        "specialties": [service_type],
                        "in_network": True,
                        "distance": "5 miles"
                    }
                ],
                "service_type": service_type,
                "location": location
            }
        
        try:
            # Call the Service Provider Agent to get real provider data
            return self.service_provider_agent.find_providers(service_type, location)
        except Exception as e:
            self.logger.error(f"Error getting provider information: {str(e)}")
            return {
                "providers": [],
                "error": str(e),
                "service_type": service_type,
                "location": location
            }
    
    @BaseAgent.track_performance
    def develop_guide(self, 
                     user_info: Dict[str, Any],
                     policy_info: Dict[str, Any],
                     service_info: Dict[str, Any],
                     location: str = "") -> Dict[str, Any]:
        """
        Develop a personalized healthcare guide.
        
        Args:
            user_info: User information
            policy_info: Policy information
            service_info: Service requirements
            location: User's location
            
        Returns:
            Healthcare guide content
        """
        start_time = time.time()
        
        # Log the request
        self.logger.info(f"Developing guide for user: {user_info.get('name', 'Unknown')}")
        
        # Get provider information if service type is provided
        provider_info = {}
        if 'service_type' in service_info and location:
            provider_info = self.get_provider_info(service_info['service_type'], location)
        
        try:
            # Prepare the input for the guide chain
            input_dict = {
                "user_info": json.dumps(user_info),
                "policy_info": json.dumps(policy_info),
                "service_info": json.dumps(service_info),
                "provider_info": json.dumps(provider_info)
            }
            
            # Generate the guide content
            guide = self.guide_chain.invoke(input_dict)
            result = guide.dict()
            
            # Log the result
            self.logger.info(f"Guide developed: {result['title']} with {len(result['sections'])} sections")
            
            # Log execution time
            execution_time = time.time() - start_time
            self.logger.info(f"Guide development completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in guide development: {str(e)}")
            
            # Return a basic guide in case of error
            return {
                "title": f"Healthcare Guide for {user_info.get('name', 'User')}",
                "user_name": user_info.get('name', 'User'),
                "summary": "This guide could not be fully generated due to an error.",
                "sections": [
                    {
                        "title": "Error Information",
                        "content": f"We encountered an error while generating your guide: {str(e)}. Please try again later.",
                        "order": 1
                    }
                ],
                "action_items": ["Contact customer support for assistance"],
                "provider_details": {},
                "important_contacts": {"customer_support": "555-HELP-123"},
                "next_steps": ["Try again later"],
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e)
            }
    
    @BaseAgent.track_performance
    def create_pdf_prompt(self, guide_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a prompt for the Guide to PDF Agent.
        
        Args:
            guide_content: The guide content
            
        Returns:
            Prompt for the Guide to PDF Agent
        """
        try:
            # Convert guide content to HealthcareGuide if it's a dict
            if isinstance(guide_content, dict):
                guide = HealthcareGuide(**guide_content)
            else:
                guide = guide_content
            
            # Generate the prompt for PDF creation
            prompt = self.prompt_chain.invoke(guide)
            result = prompt.dict()
            
            self.logger.info(f"PDF prompt created for guide: {result['guide_title']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating PDF prompt: {str(e)}")
            
            # Return a basic prompt in case of error
            return {
                "guide_title": guide_content.get("title", "Healthcare Guide"),
                "guide_purpose": guide_content.get("summary", "To assist with healthcare navigation"),
                "user_info": {"name": guide_content.get("user_name", "User")},
                "policy_info": {},
                "service_info": {},
                "provider_info": guide_content.get("provider_details", {}),
                "special_instructions": ["Handle with care due to processing error"],
                "formatting_preferences": {"simple_layout": True},
                "error": str(e)
            }
    
    def process(self, 
               user_info: Dict[str, Any],
               policy_info: Dict[str, Any],
               service_info: Dict[str, Any],
               location: str = "") -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Process a request to create a healthcare guide and PDF prompt.
        
        Args:
            user_info: User information
            policy_info: Policy information
            service_info: Service requirements
            location: User's location
            
        Returns:
            Tuple of (guide_content, pdf_prompt)
        """
        # Develop the guide
        guide_content = self.develop_guide(user_info, policy_info, service_info, location)
        
        # Create the PDF prompt
        pdf_prompt = self.create_pdf_prompt(guide_content)
        
        return guide_content, pdf_prompt

# Example usage
if __name__ == "__main__":
    # Initialize the agent
    agent = HealthcareGuideAgent()
    
    # Test with sample data
    user_info = {
        "name": "John Doe",
        "age": 65,
        "gender": "Male",
        "medical_conditions": ["hypertension", "type 2 diabetes"]
    }
    
    policy_info = {
        "insurer": "Medicare",
        "policy_type": "Medicare Advantage",
        "policy_number": "MA123456789",
        "effective_date": "2025-01-01"
    }
    
    service_info = {
        "service_type": "endocrinology",
        "needed_for": "diabetes management",
        "urgency": "routine",
        "frequency": "quarterly"
    }
    
    location = "Boston, MA"
    
    guide, pdf_prompt = agent.process(user_info, policy_info, service_info, location)
    
    print(f"Guide Title: {guide['title']}")
    print(f"Number of Sections: {len(guide['sections'])}")
    print(f"Action Items: {', '.join(guide['action_items'])}")
    print()
    print(f"PDF Prompt Title: {pdf_prompt['guide_title']}")
    print(f"PDF Purpose: {pdf_prompt['guide_purpose']}") 