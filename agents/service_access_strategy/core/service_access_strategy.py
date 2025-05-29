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

# TODO: Add web search capability to find access strategies already outlined on service websites and other up-to-date reputable resources

import os
import json
import logging
import time
from typing import Dict, List, Any, Tuple, Optional, Union
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models import BaseLanguageModel
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

# Import base agent and exceptions
from agents.base_agent import BaseAgent
from agents.common.exceptions import (
    ServiceAccessStrategyException,
    StrategyDevelopmentError,
    PolicyComplianceError,
    ProviderLookupError
)

# Import configuration handling
from utils.config_manager import ConfigManager

# Import models
from agents.service_access_strategy.core.models.strategy_models import (
    ServiceAccessStrategy, ServiceMatch, ActionStep
)

# Setup logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Create logs directory if it doesn't exist
    log_dir = os.path.join("logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up file handler
    handler = logging.FileHandler(os.path.join(log_dir, "service_access_strategy.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class ServiceAccessStrategyAgent(BaseAgent):
    """Agent responsible for developing access strategies for healthcare services."""
    
    def __init__(
        self, 
                 llm: Optional[BaseLanguageModel] = None,
        policy_compliance_agent = None,
        service_provider_agent = None,
        config_manager: Optional[ConfigManager] = None
    ):
        """
        Initialize the Service Access Strategy Agent.
        
        Args:
            llm: Language model to use for generating strategies
            policy_compliance_agent: Optional PolicyComplianceAgent to check compliance
            service_provider_agent: Optional ServiceProviderAgent to find providers
            config_manager: Optional ConfigManager for configuration
        """
        # Store ConfigManager
        self.config_manager = config_manager
        
        # Initialize base agent
        super().__init__(
            name="service_access_strategy", 
            llm=llm,
            logger=logger
        )
        
        # Store references to other agents
        self.policy_compliance_agent = policy_compliance_agent
        self.service_provider_agent = service_provider_agent
        
        # Set up chain components in _initialize_agent
        self.strategy_parser = None
        self.prompt_template = None
        self.strategy_chain = None
        self.system_prompt = None
        
        # Initialize agent-specific components
        self._initialize_agent()
    
    def check_compliance(self, policy_type: str, service_type: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check policy compliance for a service.
        
        Args:
            policy_type: Type of policy to check
            service_type: Type of service to check
            user_context: User context information
            
        Returns:
            Compliance assessment
            
        Raises:
            PolicyComplianceError: If there's an error checking policy compliance
        """
        if not self.policy_compliance_agent:
            logger.warning("Policy Compliance Agent not available. Using placeholder data.")
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
            logger.error(f"Error checking compliance: {str(e)}")
            raise PolicyComplianceError(f"Failed to check policy compliance: {str(e)}") from e
    
    def find_providers(self, service_type: str, location: str) -> List[Dict[str, Any]]:
        """
        Find providers for a service.
        
        Args:
            service_type: Type of service
            location: User's location
            
        Returns:
            List of providers
            
        Raises:
            ProviderLookupError: If there's an error finding providers
        """
        if not self.service_provider_agent:
            logger.warning("Service Provider Agent not available. Using placeholder data.")
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
            logger.error(f"Error finding providers: {str(e)}")
            raise ProviderLookupError(f"Failed to find providers: {str(e)}") from e
    
    @BaseAgent.track_performance
    def develop_strategy(self, 
                        patient_info: Dict[str, Any],
                        medical_need: str,
                        policy_info: Dict[str, Any],
                        location: str = None,
                        constraints: str = "") -> Dict[str, Any]:
        """
        Develop a service access strategy.
        
        Args:
            patient_info: Patient information
            medical_need: Description of the medical need
            policy_info: Policy information
            location: Patient's location (optional - for policy navigation focus)
            constraints: Additional constraints
            
        Returns:
            Service access strategy
            
        Raises:
            StrategyDevelopmentError: If there's an error developing the strategy
            PolicyComplianceError: If there's an error checking policy compliance
            ProviderLookupError: If there's an error finding providers
        """
        start_time = time.time()
        
        # Log the request
        logger.info(f"Developing strategy for: {medical_need}")
        
        try:
            # Extract policy type and service type
            policy_type = policy_info.get("policy_type", "Medicare")
            service_type = medical_need.split()[0]  # Simple extraction of first word as service type
            
            # Check policy compliance
            try:
                compliance_info = self.check_compliance(policy_type, service_type, patient_info)
            except PolicyComplianceError as e:
                # Handle compliance check error but continue with development
                logger.warning(f"Compliance check error: {str(e)}")
                compliance_info = {
                    "is_compliant": None,
                    "compliance_score": 0.0,
                    "non_compliant_reasons": [f"Error checking compliance: {str(e)}"],
                    "rules_applied": [],
                    "recommendations": ["Contact customer support for assistance with compliance verification"],
                    "confidence": 0.0
                }
            
            # Find providers only if location is provided
            providers = []
            if location:
                try:
                    providers = self.find_providers(service_type, location)
                except ProviderLookupError as e:
                    # Handle provider lookup error but continue with development
                    logger.warning(f"Provider lookup error: {str(e)}")
                    providers = []
            else:
                # Focus on policy navigation without specific providers
                logger.info("No location provided - focusing on policy navigation guidance")
            
            # Prepare input for the strategy chain
            input_dict = {
                "patient_info": json.dumps(patient_info),
                "medical_need": medical_need,
                "policy_info": json.dumps(policy_info),
                "compliance_info": json.dumps(compliance_info),
                "provider_info": json.dumps(providers) if providers else "[]",
                "location": location or "Not specified - focus on policy guidance",
                "constraints": constraints
            }
            
            # Generate the strategy
            try:
                strategy_response = self.strategy_chain.invoke(input_dict)
                
                # Handle different response formats
                if hasattr(strategy_response, 'content'):
                    # AIMessage object - extract content
                    content = strategy_response.content
                    try:
                        raw_result = json.loads(content)
                    except json.JSONDecodeError:
                        # If content isn't valid JSON, create a fallback response
                        logger.warning(f"Could not parse LLM response as JSON: {content[:200]}...")
                        raw_result = {
                            "access_strategy": {
                                "summary": {
                                    "primary_approach": "Information gathering required before service search",
                                    "confidence_score": 0.3,
                                    "estimated_timeline": "Additional information needed",
                                    "key_benefits": ["Targeted search once details provided", "Better insurance coverage verification", "Location-specific recommendations"]
                                },
                                "coverage_details": {
                                    "service_type": "healthcare consultation", 
                                    "is_covered": None,
                                    "coverage_details": {
                                        "copay": "Cannot determine without insurance details",
                                        "requires_referral": "Unknown - depends on plan type",
                                        "prior_authorization": "Unknown - depends on plan type",
                                        "coverage_notes": ["Insurance plan information required", "Location needed for network verification"]
                                    }
                                },
                                "action_plan": [
                                    {
                                        "step_number": 1,
                                        "step_description": "Please provide your insurance plan details (Medicare, Medicaid, private insurance name)",
                                        "expected_timeline": "Immediate",
                                        "required_resources": ["Insurance card", "Plan documentation"],
                                        "potential_obstacles": ["Don't have insurance card available"],
                                        "contingency_plan": "Contact insurance provider for member portal access"
                                    },
                                    {
                                        "step_number": 2,
                                        "step_description": "Please specify your location (city, state, or ZIP code)",
                                        "expected_timeline": "Immediate",
                                        "required_resources": ["Current address or preferred search area"],
                                        "potential_obstacles": ["Unsure of preferred location"],
                                        "contingency_plan": "Use current residence address as starting point"
                                    }
                                ],
                                "provider_options": []
                            }
                        }
                elif isinstance(strategy_response, str):
                    # Parse string response
                    raw_result = json.loads(strategy_response)
                elif hasattr(strategy_response, 'model_dump'):
                    # Handle Pydantic model response
                    raw_result = strategy_response.model_dump()
                else:
                    # Direct dict response
                    raw_result = strategy_response
                
                # Convert nested LLM response to ServiceAccessStrategy format
                if "access_strategy" in raw_result:
                    # Extract from nested structure
                    nested_data = raw_result["access_strategy"]
                    summary = nested_data.get("summary", {})
                    coverage = nested_data.get("coverage_details", {})
                    action_plan = nested_data.get("action_plan", [])
                    provider_options = nested_data.get("provider_options", [])
                    
                    # Create properly formatted result
                    result = {
                        "patient_need": medical_need,
                        "matched_services": [
                            {
                                "service_name": coverage.get("service_type", "Healthcare Service"),
                                "service_type": coverage.get("service_type", "general"),
                                "service_description": summary.get("primary_approach", "Healthcare service"),
                                "is_covered": coverage.get("is_covered", True),
                                "coverage_details": coverage.get("coverage_details", {}),
                                "estimated_cost": coverage.get("coverage_details", {}).get("copay", "Contact insurance"),
                                "required_documentation": [],
                                "prerequisites": [],
                                "alternatives": [],
                                "compliance_score": summary.get("confidence_score", 0.8)
                            }
                        ],
                        "recommended_service": summary.get("primary_approach", "Service access strategy"),
                        "action_plan": [
                            {
                                "step_number": step.get("step_number", i+1),
                                "step_description": step.get("step_description", "Action required"),
                                "expected_timeline": step.get("expected_timeline", "TBD"),
                                "required_resources": step.get("required_resources", []),
                                "potential_obstacles": step.get("potential_obstacles", []),
                                "contingency_plan": step.get("contingency_plan", "Review and adjust approach")
                            } for i, step in enumerate(action_plan)
                        ],
                        "estimated_timeline": summary.get("estimated_timeline", "TBD"),
                        "provider_options": provider_options,
                        "compliance_assessment": {
                            "is_compliant": coverage.get("is_covered", True),
                            "compliance_notes": coverage.get("coverage_details", {}).get("coverage_notes", [])
                        },
                        "guidance_notes": summary.get("key_benefits", []),
                        "confidence": summary.get("confidence_score", 0.8)
                    }
                else:
                    # Direct format - use as is
                    result = raw_result
                    
            except Exception as e:
                logger.error(f"Strategy generation error: {str(e)}")
                raise StrategyDevelopmentError(f"Failed to generate strategy: {str(e)}") from e
            
            # Log the result
            logger.info(f"Strategy developed with {len(result['matched_services'])} matched services and {len(result['action_plan'])} action steps")
            
            # Log execution time
            execution_time = time.time() - start_time
            logger.info(f"Strategy development completed in {execution_time:.2f}s")
            
            return result
            
        except (PolicyComplianceError, ProviderLookupError):
            # Re-raise these exceptions as they've already been logged
            raise
        except StrategyDevelopmentError:
            # Re-raise strategy development error
            raise
        except Exception as e:
            logger.error(f"Error in strategy development: {str(e)}")
            raise StrategyDevelopmentError(f"Failed to develop strategy: {str(e)}") from e
    
    def process(self, 
               patient_info: Dict[str, Any],
               medical_need: str,
               policy_info: Dict[str, Any],
               location: str = None,
               constraints: str = "") -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Process a strategy development request.
        
        Args:
            patient_info: Patient information
            medical_need: Description of the medical need
            policy_info: Policy information
            location: Patient's location (optional - for policy navigation focus)
            constraints: Additional constraints
            
        Returns:
            Tuple of (strategy, provider_options)
            
        Raises:
            ServiceAccessStrategyException: If there's an error processing the request
        """
        try:
            strategy = self.develop_strategy(patient_info, medical_need, policy_info, location, constraints)
            return strategy, strategy.get("provider_options", [])
        except ServiceAccessStrategyException:
            # Re-raise specific exceptions without wrapping
            raise
        except Exception as e:
            logger.error(f"Unexpected error in process: {str(e)}")
            raise ServiceAccessStrategyException(f"Error processing service access strategy request: {str(e)}") from e

    def reset(self) -> None:
        """Reset the agent's state."""
        logger.info("Reset ServiceAccessStrategyAgent state")

    def _initialize_agent(self):
        """Initialize agent-specific components."""
        # Get paths from configuration
        try:
            prompt_path = self.prompt_path
            examples_path = self.examples_path
        except AttributeError:
            # Use default paths if not available
            prompt_path = "agents/service_access_strategy/prompts/prompt_service_access_strategy_v0_2.md"
            examples_path = "agents/service_access_strategy/prompts/examples/strategy_examples_v0_1.json"
                
        # Load prompt from file using BaseAgent's method
        try:
            self.system_prompt = self._load_prompt(prompt_path)
        except Exception as e:
            self.logger.error(f"Failed to load prompt: {e}")
            # Use minimal fallback to prevent system crash, but log an error
            self.system_prompt = "Service Access Strategy Agent: Error loading prompt"
        
        # Create output parser for strategy
        self.strategy_parser = PydanticOutputParser(pydantic_object=ServiceAccessStrategy)
        
        # Create prompt template
        system_prompt_template = SystemMessage(content=self.system_prompt)
        human_template = HumanMessage(content="""
        Patient Information: {patient_info}
        
        Medical Need: {medical_need}
        
        Policy Information: {policy_info}
        
        Compliance Information: {compliance_info}
        
        Provider Information: {provider_info}
        
        Location: {location}
        
        Additional Constraints: {constraints}
        
        Please provide a comprehensive service access strategy in JSON format according to the schema provided.
        """)
        
        self.prompt_template = ChatPromptTemplate.from_messages([
            system_prompt_template,
            human_template
        ])
        
        # Create strategy chain without parser (we'll handle parsing manually)
        self.strategy_chain = (
            self.prompt_template
            | self.llm
        )
        
        logger.info(f"Service Access Strategy Agent initialized with model {self.llm.model if hasattr(self.llm, 'model') else 'unknown'}")

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