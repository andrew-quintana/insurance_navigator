"""
Policy Compliance Evaluator Agent

This agent is responsible for:
1. Analyzing plan rules and service requirements to determine user eligibility
2. Acting as the regulatory mind in the Service + Matching layer
3. Evaluating policy compliance for insurance plans
4. Detecting outdated rules and keeping up with regulatory changes
5. Coordinating with the Service Access Strategy Agent

Based on FMEA analysis, this agent implements controls for:
- Missing key terms in policy evaluation
- Document parsing failures including OCR issues
- Outdated rules that could lead to false compliance
- Regulatory changes monitoring
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Tuple, Optional, Union
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.language_models import BaseLanguageModel
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.retrievers import BaseRetriever

from agents.base_agent import BaseAgent
from utils.prompt_loader import load_prompt

# Ensure logs directory exists
os.makedirs(os.path.join("logs", "agents"), exist_ok=True)

# Setup logging
logger = logging.getLogger("policy_compliance_agent")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join("logs", "agents", "policy_compliance.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Define output schema
class ComplianceAnalysis(BaseModel):
    """Output schema for the policy compliance evaluator agent."""
    is_compliant: bool = Field(description="Whether the service/request is compliant with the policy")
    compliance_score: float = Field(description="Compliance score (0-1)")
    non_compliant_reasons: List[str] = Field(description="List of reasons for non-compliance", default_factory=list)
    rules_applied: List[str] = Field(description="List of policy rules applied in the evaluation", default_factory=list)
    recommendations: List[str] = Field(description="Recommendations to achieve compliance", default_factory=list)
    confidence: float = Field(description="Confidence in the assessment (0-1)")
    reasoning: str = Field(description="Step-by-step reasoning behind the compliance assessment")

class PolicyComplianceAgent(BaseAgent):
    """Agent responsible for evaluating policy compliance and determining eligibility."""
    
    def __init__(self, 
                 llm: Optional[BaseLanguageModel] = None,
                 retriever: Optional[BaseRetriever] = None):
        """
        Initialize the Policy Compliance Evaluator Agent.
        
        Args:
            llm: An optional language model to use
            retriever: An optional retriever for RAG capabilities
        """
        # Initialize the base agent
        super().__init__(name="policy_compliance", llm=llm or ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0))
        
        self.parser = PydanticOutputParser(pydantic_object=ComplianceAnalysis)
        self.retriever = retriever
        
        # Known policy rules database (to be expanded)
        self.policy_rules = {
            "medicare": [
                "Medicare Part A covers inpatient hospital care",
                "Medicare Part B covers outpatient medical services",
                "Medicare Part D covers prescription drugs",
                "Medicare Advantage (Part C) offers combined coverage through private insurers"
            ],
            "medicaid": [
                "Eligibility varies by state",
                "Income must be below threshold for qualification",
                "Covers essential health benefits defined by ACA",
                "States may have work requirements for certain beneficiaries"
            ]
        }
        
        # Define self-consistency system prompt
        # Load the self.system_prompt from file
        try:
            self.system_prompt = load_prompt("policy_compliance")
        except FileNotFoundError:
            self.logger.warning("Could not find policy_compliance.md prompt file, using default prompt")
            # Load the self.system_prompt from file
        try:
            self.system_prompt = load_prompt("policy_compliance")
        except FileNotFoundError:
            self.logger.warning("Could not find policy_compliance.md prompt file, using default prompt")
            self.system_prompt = """
            Default prompt for self.system_prompt. Replace with actual prompt if needed.
            """
        
        
        
        # Define the prompt template
        self.prompt_template = PromptTemplate(
            template="""
            {system_prompt}
            
            POLICY INFORMATION:
            {policy_info}
            
            SERVICE REQUEST:
            {service_request}
            
            ADDITIONAL CONTEXT:
            {context}
            
            Analyze this request for compliance with the policy and provide your assessment.
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "policy_info", "service_request", "context"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        # Create the ReAct chain (simplified version)
        self.logger.info("Policy Compliance Evaluator Agent initialized")
    
    def get_policy_info(self, policy_type: str) -> str:
        """
        Retrieve policy information based on policy type.
        
        Args:
            policy_type: The type of policy (e.g., 'medicare', 'medicaid')
            
        Returns:
            Policy information as a string
        """
        if policy_type.lower() in self.policy_rules:
            return "\n".join([f"- {rule}" for rule in self.policy_rules[policy_type.lower()]])
        
        return "Policy information not found. Please provide policy details."
    
    def retrieve_context(self, query: str) -> str:
        """
        Retrieve relevant context using the RAG retriever.
        
        Args:
            query: The query to retrieve context for
            
        Returns:
            Retrieved context as a string
        """
        if not self.retriever:
            return "No retriever configured. Using default policy rules only."
        
        try:
            documents = self.retriever.get_relevant_documents(query)
            return "\n\n".join([doc.page_content for doc in documents])
        except Exception as e:
            self.logger.error(f"Error retrieving context: {str(e)}")
            return f"Error retrieving context: {str(e)}"
    
    @BaseAgent.track_performance
    def evaluate_compliance(self, 
                           policy_type: str, 
                           service_request: str,
                           user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluate compliance of a service request with a policy.
        
        Args:
            policy_type: The type of policy to evaluate against
            service_request: Description of the service being requested
            user_context: Optional additional context about the user
            
        Returns:
            Compliance analysis results
        """
        start_time = time.time()
        
        # Log the request
        self.logger.info(f"Evaluating compliance for policy type: {policy_type}")
        
        # Get policy information
        policy_info = self.get_policy_info(policy_type)
        
        # Retrieve relevant context using RAG
        retrieved_context = self.retrieve_context(f"{policy_type} {service_request}")
        
        # Combine user-provided context with retrieved context
        context = f"{retrieved_context}\n\n"
        if user_context:
            context += "USER CONTEXT:\n"
            context += "\n".join([f"- {k}: {v}" for k, v in user_context.items()])
        
        try:
            # Prepare the input for the prompt
            input_dict = {
                "system_prompt": self.system_prompt,
                "policy_info": policy_info,
                "service_request": service_request,
                "context": context
            }
            
            # Format the prompt
            prompt = self.prompt_template.format(**input_dict)
            
            # Call the language model
            message = HumanMessage(content=prompt)
            response = self.llm.invoke([SystemMessage(content=self.system_prompt), message])
            
            # Parse the response
            parsed_response = self.parser.parse(response.content)
            result = parsed_response.dict()
            
            # Log the result
            if result["is_compliant"]:
                self.logger.info(f"Service request compliant with score: {result['compliance_score']}")
            else:
                self.logger.warning(f"Service request non-compliant. Reasons: {', '.join(result['non_compliant_reasons'])}")
            
            # Log execution time
            execution_time = time.time() - start_time
            self.logger.info(f"Compliance evaluation completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in compliance evaluation: {str(e)}")
            
            # Return a conservative result in case of error
            return {
                "is_compliant": False,
                "compliance_score": 0.0,
                "non_compliant_reasons": [f"Processing error: {str(e)}"],
                "rules_applied": [],
                "recommendations": ["Retry with more complete information"],
                "confidence": 0.0,
                "reasoning": f"Error during evaluation: {str(e)}"
            }
    
    def process(self, policy_type: str, service_request: str, 
               user_context: Optional[Dict[str, Any]] = None) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Process a compliance evaluation request.
        
        Args:
            policy_type: The type of policy to evaluate against
            service_request: Description of the service being requested
            user_context: Optional additional context about the user
            
        Returns:
            Tuple of (is_compliant, compliance_score, full_result)
        """
        result = self.evaluate_compliance(policy_type, service_request, user_context)
        return result["is_compliant"], result["compliance_score"], result

# Example usage
if __name__ == "__main__":
    # Initialize the agent
    agent = PolicyComplianceAgent()
    
    # Test with a simple request
    policy_type = "medicare"
    service_request = "Requesting coverage for annual wellness visit"
    
    is_compliant, score, result = agent.process(policy_type, service_request)
    
    print(f"Is compliant: {is_compliant}")
    print(f"Compliance score: {score}")
    print(f"Reasoning: {result['reasoning']}")
    if not is_compliant:
        print(f"Non-compliant reasons: {', '.join(result['non_compliant_reasons'])}")
        print(f"Recommendations: {', '.join(result['recommendations'])}") 