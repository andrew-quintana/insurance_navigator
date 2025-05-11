"""
Service Access Strategy Agent

This agent is responsible for:
1. Identifying matching healthcare services based on patient needs
2. Building action plans for accessing services efficiently
3. Coordinating with the Policy Compliance Evaluator Agent
4. Collaborating with the Service Provider Agent
5. Creating comprehensive service access strategies

Based on FMEA analysis, this agent implements controls for:
- Service matching accuracy
- Action plan feasibility
- Policy compliance verification
- Coordination with other agents
- Handling complex medical needs
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
from agents.policy_compliance import PolicyComplianceAgent
from agents.service_provider import ServiceProviderAgent
from utils.prompt_loader import load_prompt

# Setup logging
logger = logging.getLogger("service_access_strategy_agent")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join("logs", "agents", "service_access_strategy.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Ensure logs directory exists
os.makedirs(os.path.join("logs", "agents"), exist_ok=True)

# Define the output schema for service matching
class ServiceMatch(BaseModel):
    """Schema for a matched healthcare service."""
    service_name: str = Field(description="Name of the healthcare service")
    service_type: str = Field(description="Type/category of service")
    service_description: str = Field(description="Description of the service")
    is_covered: bool = Field(description="Whether the service is covered by insurance")
    coverage_details: Dict[str, Any] = Field(description="Details about coverage", default_factory=dict)
    estimated_cost: Optional[str] = Field(description="Estimated cost of the service", default=None)
    required_documentation: List[str] = Field(description="Documents required for the service", default_factory=list)
    prerequisites: List[str] = Field(description="Prerequisites for accessing the service", default_factory=list)
    alternatives: List[str] = Field(description="Alternative services", default_factory=list)
    compliance_score: float = Field(description="Compliance score from 0-1")

# Define the output schema for action steps
class ActionStep(BaseModel):
    """Schema for an action step in the service access plan."""
    step_number: int = Field(description="Number of the step in sequence")
    step_description: str = Field(description="Description of the action step")
    expected_timeline: str = Field(description="Expected timeline for completing the step")
    required_resources: List[str] = Field(description="Resources required for the step", default_factory=list)
    potential_obstacles: List[str] = Field(description="Potential obstacles for this step", default_factory=list)
    contingency_plan: Optional[str] = Field(description="Contingency plan if step encounters issues", default=None)

# Define the output schema for service access strategy
class ServiceAccessStrategy(BaseModel):
    """Output schema for the service access strategy."""
    patient_need: str = Field(description="Description of the patient's medical need")
    matched_services: List[ServiceMatch] = Field(description="List of matched services", default_factory=list)
    recommended_service: str = Field(description="The recommended service option")
    action_plan: List[ActionStep] = Field(description="Step-by-step action plan", default_factory=list)
    estimated_timeline: str = Field(description="Estimated overall timeline")
    provider_options: List[Dict[str, Any]] = Field(description="Provider options", default_factory=list)
    compliance_assessment: Dict[str, Any] = Field(description="Policy compliance assessment", default_factory=dict)
    guidance_notes: List[str] = Field(description="Additional guidance notes", default_factory=list)
    confidence: float = Field(description="Overall confidence in the strategy (0-1)")

class ServiceAccessStrategyAgent(BaseAgent):
    """Agent responsible for developing access strategies for healthcare services."""
    
    def __init__(self, 
                 llm: Optional[BaseLanguageModel] = None,
                 policy_compliance_agent: Optional[PolicyComplianceAgent] = None,
                 service_provider_agent: Optional[ServiceProviderAgent] = None):
        """
        Initialize the Service Access Strategy Agent.
        
        Args:
            llm: An optional language model to use
            policy_compliance_agent: An optional reference to the Policy Compliance Agent
            service_provider_agent: An optional reference to the Service Provider Agent
        """
        # Initialize the base agent
        super().__init__(name="service_access_strategy", llm=llm or ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0))
        
        self.strategy_parser = PydanticOutputParser(pydantic_object=ServiceAccessStrategy)
        
        # Store references to other agents
        self.policy_compliance_agent = policy_compliance_agent
        self.service_provider_agent = service_provider_agent
        
        # Define system prompt for strategy development
        # Load the self.system_prompt from file
        try:
            self.system_prompt = load_prompt("service_access_strategy")
        except FileNotFoundError:
            self.logger.warning("Could not find service_access_strategy.md prompt file, using default prompt")
            # Load the self.system_prompt from file
        try:
            self.system_prompt = load_prompt("service_access_strategy")
        except FileNotFoundError:
            self.logger.warning("Could not find service_access_strategy.md prompt file, using default prompt")
            self.system_prompt = """
            Default prompt for self.system_prompt. Replace with actual prompt if needed.
            """
        
        
        
        # Define the strategy development prompt template
        self.strategy_template = PromptTemplate(
            template="""
            {system_prompt}
            
            PATIENT INFORMATION:
            {patient_info}
            
            MEDICAL NEED:
            {medical_need}
            
            POLICY INFORMATION:
            {policy_info}
            
            COMPLIANCE ASSESSMENT:
            {compliance_info}
            
            PROVIDER OPTIONS:
            {provider_info}
            
            ADDITIONAL CONSTRAINTS:
            {constraints}
            
            Based on this information, develop a comprehensive service access strategy.
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "patient_info", "medical_need", "policy_info", 
                           "compliance_info", "provider_info", "constraints"],
            partial_variables={"format_instructions": self.strategy_parser.get_format_instructions()}
        )
        
        # Create the strategy development chain
        self.strategy_chain = (
            {"system_prompt": lambda _: self.system_prompt,
             "patient_info": lambda x: x["patient_info"],
             "medical_need": lambda x: x["medical_need"],
             "policy_info": lambda x: x["policy_info"],
             "compliance_info": lambda x: x["compliance_info"],
             "provider_info": lambda x: x["provider_info"],
             "constraints": lambda x: x["constraints"]}
            | self.strategy_template
            | self.llm
            | self.strategy_parser
        )
        
        logger.info("Service Access Strategy Agent initialized")
    
    def check_compliance(self, policy_type: str, service_type: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check policy compliance for a service.
        
        Args:
            policy_type: Type of policy to check
            service_type: Type of service to check
            user_context: User context information
            
        Returns:
            Compliance assessment
        """
        if not self.policy_compliance_agent:
            self.logger.warning("Policy Compliance Agent not available. Using placeholder data.")
            # Return placeholder data
            return {
                "is_compliant": True,
                "compliance_score": 0.8,
                "non_compliant_reasons": [],
                "rules_applied": [f"Assumed coverage for {service_type}"],
                "recommendations": ["Verify exact coverage with insurer"],
                "confidence": 0.5
            }
        
        try:
            # Call the Policy Compliance Agent to check compliance
            _, _, result = self.policy_compliance_agent.process(policy_type, service_type, user_context)
            return result
        except Exception as e:
            self.logger.error(f"Error checking compliance: {str(e)}")
            return {
                "is_compliant": False,
                "compliance_score": 0.0,
                "non_compliant_reasons": [f"Error checking compliance: {str(e)}"],
                "rules_applied": [],
                "recommendations": ["Contact customer support for assistance"],
                "confidence": 0.0
            }
    
    def find_providers(self, service_type: str, location: str) -> List[Dict[str, Any]]:
        """
        Find providers for a service.
        
        Args:
            service_type: Type of service
            location: User's location
            
        Returns:
            List of providers
        """
        if not self.service_provider_agent:
            self.logger.warning("Service Provider Agent not available. Using placeholder data.")
            # Return placeholder data
            return [{
                "name": "Example Provider",
                "address": "123 Healthcare St, Example City",
                "distance": 5.0,
                "in_network": True,
                "specialties": [service_type]
            }]
        
        try:
            # Call the Service Provider Agent to find providers
            providers, _ = self.service_provider_agent.process(service_type, location)
            return providers
        except Exception as e:
            self.logger.error(f"Error finding providers: {str(e)}")
            return []
    
    @BaseAgent.track_performance
    def develop_strategy(self, 
                        patient_info: Dict[str, Any],
                        medical_need: str,
                        policy_info: Dict[str, Any],
                        location: str,
                        constraints: str = "") -> Dict[str, Any]:
        """
        Develop a service access strategy.
        
        Args:
            patient_info: Patient information
            medical_need: Description of the medical need
            policy_info: Policy information
            location: Patient's location
            constraints: Additional constraints
            
        Returns:
            Service access strategy
        """
        start_time = time.time()
        
        # Log the request
        self.logger.info(f"Developing strategy for: {medical_need}")
        
        try:
            # Extract policy type and service type
            policy_type = policy_info.get("policy_type", "Medicare")
            service_type = medical_need.split()[0]  # Simple extraction of first word as service type
            
            # Check policy compliance
            compliance_info = self.check_compliance(policy_type, service_type, patient_info)
            
            # Find providers
            providers = self.find_providers(service_type, location)
            
            # Prepare input for the strategy chain
            input_dict = {
                "patient_info": json.dumps(patient_info),
                "medical_need": medical_need,
                "policy_info": json.dumps(policy_info),
                "compliance_info": json.dumps(compliance_info),
                "provider_info": json.dumps(providers),
                "constraints": constraints
            }
            
            # Generate the strategy
            strategy = self.strategy_chain.invoke(input_dict)
            result = strategy.dict()
            
            # Log the result
            self.logger.info(f"Strategy developed with {len(result['matched_services'])} matched services and {len(result['action_plan'])} action steps")
            
            # Log execution time
            execution_time = time.time() - start_time
            self.logger.info(f"Strategy development completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in strategy development: {str(e)}")
            
            # Return a basic strategy in case of error
            return {
                "patient_need": medical_need,
                "matched_services": [],
                "recommended_service": "Unable to determine due to error",
                "action_plan": [
                    {
                        "step_number": 1,
                        "step_description": "Contact customer support for assistance",
                        "expected_timeline": "Immediately",
                        "required_resources": ["Phone or email"],
                        "potential_obstacles": ["Extended wait times"],
                        "contingency_plan": "Try alternative contact methods"
                    }
                ],
                "estimated_timeline": "Unknown due to error",
                "provider_options": [],
                "compliance_assessment": {"error": str(e)},
                "guidance_notes": ["Strategy development encountered an error. Please try again or contact support."],
                "confidence": 0.0,
                "error": str(e)
            }
    
    def process(self, 
               patient_info: Dict[str, Any],
               medical_need: str,
               policy_info: Dict[str, Any],
               location: str,
               constraints: str = "") -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Process a strategy development request.
        
        Args:
            patient_info: Patient information
            medical_need: Description of the medical need
            policy_info: Policy information
            location: Patient's location
            constraints: Additional constraints
            
        Returns:
            Tuple of (strategy, provider_options)
        """
        strategy = self.develop_strategy(patient_info, medical_need, policy_info, location, constraints)
        return strategy, strategy.get("provider_options", [])

# Example usage
if __name__ == "__main__":
    # Initialize the agent
    agent = ServiceAccessStrategyAgent()
    
    # Test with sample data
    patient_info = {
        "name": "John Doe",
        "age": 67,
        "gender": "Male",
        "medical_conditions": ["type 2 diabetes", "hypertension"],
        "medication_allergies": ["penicillin"]
    }
    
    medical_need = "endocrinology consultation for diabetes management"
    
    policy_info = {
        "policy_type": "Medicare",
        "plan_name": "Medicare Advantage Plan",
        "member_id": "MA123456789",
        "group_number": "GRP987654",
        "effective_date": "2025-01-01"
    }
    
    location = "Boston, MA"
    
    strategy, providers = agent.process(patient_info, medical_need, policy_info, location)
    
    print(f"Recommended Service: {strategy['recommended_service']}")
    print(f"Number of Action Steps: {len(strategy['action_plan'])}")
    print("Action Plan:")
    for step in strategy["action_plan"]:
        print(f"  {step['step_number']}. {step['step_description']} ({step['expected_timeline']})")
    print(f"Estimated Timeline: {strategy['estimated_timeline']}")
    print(f"Provider Options: {len(providers)}")
    print(f"Confidence: {strategy['confidence']}") 