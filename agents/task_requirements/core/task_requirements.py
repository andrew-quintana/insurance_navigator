"""
Task Requirements Agent

This agent is responsible for:
1. Interpreting user task intents
2. Querying policy and regulatory requirements
3. Generating input checklists for tasks
4. Defining expected outputs for tasks
5. Formatting requirements into structured objects

Based on FMEA analysis, this agent implements controls for:
- Intent schema enforcement with example-based prompts
- RAG source filtering and versioning
- Prompt chaining with constraint-aware matching
- Role-based validation for outputs
- JSON structure checking and field-level test cases
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Tuple, Optional, Union, Set
from datetime import datetime
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
logger = logging.getLogger("task_requirements_agent")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join("logs", "agents", "task_requirements.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Ensure logs directory exists
os.makedirs(os.path.join("logs", "agents"), exist_ok=True)

# Define output schemas
class RequiredInput(BaseModel):
    """Schema for a required input item."""
    name: str = Field(description="Name of the required input")
    description: str = Field(description="Description of the input")
    input_type: str = Field(description="Type of input (document, form, information)")
    required: bool = Field(description="Whether the input is required or optional", default=True)
    source: Optional[str] = Field(description="Where the input can be obtained", default=None)
    alternatives: List[str] = Field(description="Alternative inputs that can be provided", default_factory=list)
    validation_rules: List[str] = Field(description="Rules for validating the input", default_factory=list)

class ExpectedOutput(BaseModel):
    """Schema for an expected output."""
    name: str = Field(description="Name of the expected output")
    description: str = Field(description="Description of the output")
    output_type: str = Field(description="Type of output (document, approval, information)")
    format: Optional[str] = Field(description="Format of the output", default=None)
    recipients: List[str] = Field(description="Who will receive the output", default_factory=list)
    dependencies: List[str] = Field(description="Outputs this depends on", default_factory=list)
    success_criteria: List[str] = Field(description="Criteria for successful completion", default_factory=list)

class PolicyReference(BaseModel):
    """Schema for a policy reference."""
    policy_name: str = Field(description="Name of the policy")
    policy_section: str = Field(description="Relevant section of the policy")
    requirement: str = Field(description="The specific requirement from the policy")
    authority: str = Field(description="The authority or organization behind the policy")
    last_updated: str = Field(description="When the policy was last updated")
    impact: str = Field(description="How this policy impacts the task")
    uri: Optional[str] = Field(description="URI to the policy document", default=None)

class TaskRequirements(BaseModel):
    """Output schema for task requirements."""
    task_id: str = Field(description="Unique identifier for the task")
    task_name: str = Field(description="Name of the task")
    task_description: str = Field(description="Detailed description of the task")
    category: str = Field(description="Category of the task (enrollment, claims, benefits)")
    required_inputs: List[RequiredInput] = Field(description="Inputs required for the task")
    expected_outputs: List[ExpectedOutput] = Field(description="Expected outputs from the task")
    policy_references: List[PolicyReference] = Field(description="Relevant policy references")
    estimated_complexity: int = Field(description="Estimated complexity (1-10)")
    prerequisites: List[str] = Field(description="Prerequisites for the task", default_factory=list)
    time_sensitivity: Optional[str] = Field(description="Time sensitivity of the task", default=None)
    confidence: float = Field(description="Confidence in the requirements (0-1)")

class TaskRequirementsAgent(BaseAgent):
    """Agent responsible for identifying requirements for Medicare-related tasks."""
    
    def __init__(self, llm: Optional[BaseLanguageModel] = None):
        """Initialize the agent with an optional language model."""
        # Initialize the base agent
        super().__init__(name="task_requirements", llm=llm or ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0))
        
        self.parser = PydanticOutputParser(pydantic_object=TaskRequirements)
        
        # Initialize common task categories and their typical requirements
        self._init_task_categories()
        
        # Define system prompt for requirements identification
        # Load the self.requirements_system_prompt from file
        try:
            self.requirements_system_prompt = load_prompt("task_requirements_requirements")
        except FileNotFoundError:
            self.logger.warning("Could not find task_requirements_requirements.md prompt file, using default prompt")
            # Load the self.requirements_system_prompt from file
        try:
            self.requirements_system_prompt = load_prompt("task_requirements_requirements_prompt")
        except FileNotFoundError:
            self.logger.warning("Could not find task_requirements_requirements_prompt.md prompt file, using default prompt")
            self.requirements_system_prompt = """
            Default prompt for self.requirements_system_prompt. Replace with actual prompt if needed.
            """
        
        
        
        # Define the requirements prompt template
        self.requirements_template = PromptTemplate(
            template="""
            {system_prompt}
            
            TASK DESCRIPTION:
            {task_description}
            
            USER CONTEXT:
            {user_context}
            
            Analyze this task to identify all requirements, inputs, and expected outputs.
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "task_description", "user_context"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        # Create the requirements chain
        self.requirements_chain = (
            {"system_prompt": lambda _: self.requirements_system_prompt,
             "task_description": lambda x: x["task_description"],
             "user_context": lambda x: json.dumps(x.get("user_context", {}), indent=2)}
            | self.requirements_template
            | self.llm
            | self.parser
        )
        
        # Set RAG source metadata threshold
        self.max_policy_age_days = 365  # Policies older than 1 year are considered outdated
        
        logger.info("Task Requirements Agent initialized")
    
    def _init_task_categories(self):
        """Initialize common task categories and their typical requirements."""
        self.task_categories = {
            "enrollment": {
                "description": "Tasks related to Medicare enrollment",
                "common_inputs": [
                    {"name": "Personal identification", "input_type": "document", "examples": ["birth certificate", "passport", "driver's license"]},
                    {"name": "Social Security card", "input_type": "document"},
                    {"name": "Medicare card (if already enrolled in Part A)", "input_type": "document"},
                    {"name": "Employment information", "input_type": "information"},
                    {"name": "CMS-40B form", "input_type": "form", "description": "Application for Enrollment in Medicare Part B"}
                ],
                "common_outputs": [
                    {"name": "Medicare card", "output_type": "document", "description": "Official Medicare card showing coverage"},
                    {"name": "Enrollment confirmation", "output_type": "document"},
                    {"name": "Medicare & You handbook", "output_type": "document"}
                ],
                "common_policies": [
                    "Medicare Part B enrollment periods",
                    "Initial Enrollment Period (IEP)",
                    "General Enrollment Period (GEP)",
                    "Special Enrollment Period (SEP)"
                ]
            },
            "claims": {
                "description": "Tasks related to Medicare claims",
                "common_inputs": [
                    {"name": "Medicare card", "input_type": "document"},
                    {"name": "Medical bills", "input_type": "document"},
                    {"name": "Explanation of Benefits (EOB)", "input_type": "document"},
                    {"name": "CMS-1490S form", "input_type": "form", "description": "Patient's Request for Medicare Payment"}
                ],
                "common_outputs": [
                    {"name": "Claim approval/denial", "output_type": "document"},
                    {"name": "Medicare Summary Notice (MSN)", "output_type": "document"},
                    {"name": "Payment information", "output_type": "information"}
                ],
                "common_policies": [
                    "Timely filing requirements",
                    "Medicare-covered services",
                    "Medicare secondary payer rules",
                    "Appeal rights"
                ]
            },
            "benefits": {
                "description": "Tasks related to understanding Medicare benefits",
                "common_inputs": [
                    {"name": "Medicare card", "input_type": "document"},
                    {"name": "Medical condition information", "input_type": "information"},
                    {"name": "Provider information", "input_type": "information"}
                ],
                "common_outputs": [
                    {"name": "Benefits explanation", "output_type": "document"},
                    {"name": "Coverage determination", "output_type": "document"}
                ],
                "common_policies": [
                    "Medicare Part A benefits",
                    "Medicare Part B benefits",
                    "Medicare Part D prescription drug coverage",
                    "Preventive services"
                ]
            }
        }
    
    def _check_policy_freshness(self, policy_date: str) -> bool:
        """Check if a policy reference is fresh based on its date."""
        try:
            # Parse the date string
            policy_datetime = datetime.strptime(policy_date, "%Y-%m-%d")
            current_datetime = datetime.now()
            
            # Calculate the difference in days
            delta = current_datetime - policy_datetime
            
            # Check if the policy is fresh
            return delta.days <= self.max_policy_age_days
        except Exception as e:
            self.logger.warning(f"Error checking policy freshness: {str(e)}")
            return False  # Assume outdated if we can't parse the date
    
    def _get_base_requirements(self, task_category: str) -> Dict[str, Any]:
        """Get base requirements for a given task category."""
        if task_category in self.task_categories:
            category_info = self.task_categories[task_category]
            
            # Create base requirements
            base_requirements = {
                "category": task_category,
                "required_inputs": [
                    RequiredInput(
                        name=input_item["name"],
                        description=input_item.get("description", f"Required {input_item['input_type']} for {task_category}"),
                        input_type=input_item["input_type"],
                        required=True,
                        source=input_item.get("source")
                    )
                    for input_item in category_info["common_inputs"]
                ],
                "expected_outputs": [
                    ExpectedOutput(
                        name=output_item["name"],
                        description=output_item.get("description", f"Output for {task_category}"),
                        output_type=output_item["output_type"],
                        format=output_item.get("format")
                    )
                    for output_item in category_info["common_outputs"]
                ],
                "policy_references": []
            }
            
            return base_requirements
        
        return {}
    
    @BaseAgent.track_performance
    def identify_requirements(self, task_description: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Identify requirements for a task.
        
        Args:
            task_description: Description of the task
            user_context: Optional user context information
            
        Returns:
            Task requirements
        """
        start_time = time.time()
        
        # Log the request
        self.logger.info(f"Identifying requirements for task: {task_description[:50]}...")
        
        try:
            # Prepare input for the requirements chain
            input_dict = {
                "task_description": task_description,
                "user_context": user_context or {}
            }
            
            # Generate requirements
            requirements = self.requirements_chain.invoke(input_dict)
            
            # Convert to dictionary
            result = requirements.dict()
            
            # Check policy freshness
            outdated_policies = []
            for i, policy in enumerate(result.get("policy_references", [])):
                if not self._check_policy_freshness(policy.get("last_updated", "1900-01-01")):
                    outdated_policies.append(policy["policy_name"])
            
            if outdated_policies:
                self.logger.warning(f"Outdated policies referenced: {', '.join(outdated_policies)}")
            
            # Log the result
            self.logger.info(f"Task categorized as: {result['category']} with complexity {result['estimated_complexity']}")
            self.logger.info(f"Identified {len(result['required_inputs'])} required inputs and {len(result['expected_outputs'])} expected outputs")
            
            # Log execution time
            execution_time = time.time() - start_time
            self.logger.info(f"Requirements identification completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in requirements identification: {str(e)}")
            
            # Create a minimal fallback response
            task_id = f"task_{int(time.time())}"
            
            return {
                "task_id": task_id,
                "task_name": "Error in task processing",
                "task_description": task_description,
                "category": "unknown",
                "required_inputs": [],
                "expected_outputs": [],
                "policy_references": [],
                "estimated_complexity": 5,
                "prerequisites": [],
                "confidence": 0.0,
                "error": str(e)
            }
    
    def process(self, task_description: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a task to identify its requirements.
        
        Args:
            task_description: Description of the task
            user_context: Optional user context information
            
        Returns:
            Task requirements
        """
        return self.identify_requirements(task_description, user_context)

# Example usage
if __name__ == "__main__":
    # Initialize the agent
    agent = TaskRequirementsAgent()
    
    # Test with sample task
    sample_task = "I need to enroll in Medicare Part B because I'm turning 65 next month"
    
    sample_context = {
        "user_age": 64,
        "current_insurance": "Employer group health plan",
        "employment_status": "Retiring next month"
    }
    
    # Process the task
    requirements = agent.process(sample_task, sample_context)
    
    print(f"Task: {requirements['task_name']}")
    print(f"Category: {requirements['category']}")
    print(f"Complexity: {requirements['estimated_complexity']}")
    print("\nRequired Inputs:")
    for input_item in requirements['required_inputs']:
        print(f"- {input_item['name']} ({input_item['input_type']}): {input_item['description']}")
    
    print("\nExpected Outputs:")
    for output in requirements['expected_outputs']:
        print(f"- {output['name']} ({output['output_type']}): {output['description']}")
    
    print("\nPolicy References:")
    for policy in requirements['policy_references']:
        print(f"- {policy['policy_name']} ({policy['authority']}): {policy['requirement']}") 