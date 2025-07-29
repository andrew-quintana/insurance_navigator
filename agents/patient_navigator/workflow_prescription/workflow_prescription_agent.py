"""
Workflow Prescription Agent

Classifies user requests into appropriate workflows for healthcare navigation.
"""

import logging
import json
from typing import List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class WorkflowPrescriptionOutput(BaseModel):
    """Output model for workflow prescription - requires a simple list of workflow names."""
    workflows: List[str] = Field(
        description="List of required workflows for the user request. Must be one or more of: 'information_retrieval', 'service_access_strategy', 'determine_eligibility', 'form_preparation'",
        examples=[
            ["information_retrieval"],
            ["service_access_strategy", "form_preparation"],
            ["determine_eligibility", "information_retrieval"]
        ],
        min_items=1,
        max_items=4
    )
    
    @field_validator('workflows')
    @classmethod
    def validate_workflows(cls, v):
        """Validate that all workflows are from the allowed set."""
        allowed_workflows = {
            'information_retrieval',
            'service_access_strategy', 
            'determine_eligibility',
            'form_preparation'
        }
        
        for workflow in v:
            if workflow not in allowed_workflows:
                raise ValueError(f"Invalid workflow '{workflow}'. Must be one of: {', '.join(allowed_workflows)}")
        
        return v
    
    @classmethod
    def from_list(cls, workflow_list: List[str]) -> 'WorkflowPrescriptionOutput':
        """Create WorkflowPrescriptionOutput from a simple list of workflows."""
        return cls(workflows=workflow_list)
    
    @classmethod
    def parse_output(cls, output: Union[str, List[str], Dict]) -> 'WorkflowPrescriptionOutput':
        """Parse various output formats into WorkflowPrescriptionOutput."""
        if isinstance(output, list):
            # Direct list format like ["information_retrieval"]
            return cls.from_list(output)
        elif isinstance(output, str):
            # Try to parse as JSON
            try:
                parsed = json.loads(output.strip())
                if isinstance(parsed, list):
                    return cls.from_list(parsed)
                elif isinstance(parsed, dict) and 'workflows' in parsed:
                    return cls(**parsed)
                else:
                    raise ValueError("String output must be a JSON list or dict with 'workflows' key")
            except json.JSONDecodeError:
                raise ValueError("String output must be valid JSON")
        elif isinstance(output, dict):
            # Dictionary format
            return cls(**output)
        else:
            raise ValueError(f"Unsupported output format: {type(output)}")


class WorkflowPrescriptionAgent(BaseAgent):
    """Agent that classifies user requests into appropriate workflows."""
    
    def __init__(self, use_mock: bool = True, **kwargs):
        super().__init__(use_mock=use_mock, **kwargs)
        self.agent_name = "workflow_prescription"
    
    def prescribe_workflows(self, user_input: str) -> WorkflowPrescriptionOutput:
        """
        Classify user input into appropriate workflows.
        
        Args:
            user_input: The user's request/question
            
        Returns:
            WorkflowPrescriptionOutput containing the prescribed workflows
        """
        if self.use_mock:
            return self._mock_prescribe_workflows(user_input)
        
        try:
            # Load prompts
            system_prompt = self._load_prompt("prompt_system_workflow_prescription_v0_1.md")
            human_prompt = self._load_prompt("prompt_human_workflow_prescription_v0_1.md")
            
            # Format the human prompt
            formatted_prompt = human_prompt.replace("{{input}}", user_input)
            
            # Call LLM
            response = self._call_llm(
                system_prompt=system_prompt,
                human_prompt=formatted_prompt,
                temperature=0.1,
                max_tokens=100
            )
            
            # Parse the response
            return self._parse_workflow_response(response)
            
        except Exception as e:
            logger.error(f"Error in workflow prescription: {str(e)}")
            # Fallback to mock for safety
            return self._mock_prescribe_workflows(user_input)
    
    def _parse_workflow_response(self, response: str) -> WorkflowPrescriptionOutput:
        """Parse the LLM response into WorkflowPrescriptionOutput."""
        try:
            # The response should be a simple list like ["information_retrieval"]
            response = response.strip()
            
            # Try to parse as JSON list
            try:
                workflows = json.loads(response)
                if isinstance(workflows, list):
                    return WorkflowPrescriptionOutput.from_list(workflows)
                else:
                    raise ValueError("Response is not a list")
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract from text
                # Look for patterns like ["workflow_name"] in the response
                import re
                list_pattern = r'\[([^\]]+)\]'
                match = re.search(list_pattern, response)
                if match:
                    # Extract items from the list
                    items_str = match.group(1)
                    # Split by comma and clean up
                    items = [item.strip().strip('"').strip("'") for item in items_str.split(',')]
                    return WorkflowPrescriptionOutput.from_list(items)
                else:
                    raise ValueError("Could not parse response as workflow list")
                    
        except Exception as e:
            logger.error(f"Error parsing workflow response: {str(e)}")
            logger.error(f"Response was: {response}")
            # Default fallback
            return WorkflowPrescriptionOutput.from_list(["information_retrieval"])
    
    def _mock_prescribe_workflows(self, user_input: str) -> WorkflowPrescriptionOutput:
        """Mock implementation for testing."""
        user_input_lower = user_input.lower()
        
        workflows = []
        
        # Simple keyword-based classification
        if any(word in user_input_lower for word in ["what", "define", "explain", "information", "learn", "understand"]):
            workflows.append("information_retrieval")
            
        if any(word in user_input_lower for word in ["find", "access", "get", "need", "want", "steps", "how"]):
            workflows.append("service_access_strategy")
            
        if any(word in user_input_lower for word in ["eligible", "qualify", "can i", "am i", "do i qualify"]):
            workflows.append("determine_eligibility")
            
        if any(word in user_input_lower for word in ["form", "application", "apply", "fill out", "submit"]):
            workflows.append("form_preparation")
        
        # Default to information retrieval if no matches
        if not workflows:
            workflows = ["information_retrieval"]
        
        # Remove duplicates while preserving order
        workflows = list(dict.fromkeys(workflows))
        
        return WorkflowPrescriptionOutput.from_list(workflows)
    
    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Process input and return workflow prescription.
        
        Args:
            input_data: User input (string or dict)
            
        Returns:
            Dict containing the prescribed workflows
        """
        try:
            # Extract user input
            if isinstance(input_data, str):
                user_input = input_data
            elif isinstance(input_data, dict):
                user_input = input_data.get('message', input_data.get('input', str(input_data)))
            else:
                user_input = str(input_data)
            
            # Get workflow prescription
            result = self.prescribe_workflows(user_input)
            
            return {
                "success": True,
                "workflows": result.workflows,
                "result": result.model_dump(),
                "agent_name": self.agent_name
            }
            
        except Exception as e:
            logger.error(f"Error processing workflow prescription request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "workflows": ["information_retrieval"],  # Safe fallback
                "agent_name": self.agent_name
            } 