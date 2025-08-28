"""
Workflow Prescription Agent for Patient Navigator Supervisor Workflow.

This agent classifies user requests into appropriate workflows using LLM-based
few-shot learning with confidence scoring and deterministic execution ordering.
"""

import logging
import asyncio
import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from agents.base_agent import BaseAgent
from ..models import WorkflowPrescriptionResult, WorkflowType


def _get_claude_haiku_llm():
    """
    Return a callable that invokes Claude Haiku, or None for mock mode.
    
    We prefer to avoid hard dependency; if Anthropic client isn't available,
    we return None and the agent will run in mock mode.
    """
    try:
        from anthropic import Anthropic
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        
        client = Anthropic(api_key=api_key)
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        
        def call_llm(prompt: str) -> str:
            """Call Claude Haiku with the given prompt."""
            try:
                # Add explicit JSON formatting instruction to the prompt
                json_prompt = prompt + "\n\nIMPORTANT: You must respond with ONLY valid JSON. Do not include any other text, explanations, or formatting outside the JSON object."
                
                resp = client.messages.create(
                    model=model,
                    max_tokens=4000,
                    temperature=0.2,
                    messages=[{"role": "user", "content": json_prompt}],
                )
                
                content = resp.content[0].text if getattr(resp, "content", None) else ""
                
                if not content:
                    raise ValueError("Empty response from Claude Haiku")
                
                # Try to extract JSON from the response
                content = content.strip()
                
                # If the response starts with a backtick, extract the JSON from within
                if content.startswith("```json"):
                    content = content.split("```json")[1].split("```")[0].strip()
                elif content.startswith("```"):
                    content = content.split("```")[1].split("```")[0].strip()
                
                # Validate that we have valid JSON
                try:
                    import json
                    json.loads(content)  # Validate JSON
                    return content
                except json.JSONDecodeError:
                    # Fallback to a basic response if JSON parsing fails
                    fallback_response = {
                        "prescribed_workflows": ["information_retrieval"],
                        "confidence_score": 0.7,
                        "reasoning": "Default fallback due to JSON parsing error",
                        "execution_order": ["information_retrieval"]
                    }
                    return json.dumps(fallback_response)
                
            except Exception as e:
                logging.error(f"Claude Haiku API call failed: {e}")
                raise
        
        return call_llm
        
    except Exception as e:
        logging.warning(f"Failed to initialize Anthropic client: {e}")
        return None


class WorkflowPrescriptionAgent(BaseAgent):
    """
    Agent that classifies user requests into appropriate workflows.
    
    Inherits from BaseAgent following established patterns.
    Uses LLM-based few-shot learning for workflow classification.
    """
    
    def __init__(self, use_mock: bool = False, **kwargs):
        """
        Initialize the Workflow Prescription Agent.
        
        Args:
            use_mock: If True, use mock responses for testing
            **kwargs: Additional arguments passed to BaseAgent
        """
        # Load prompt and examples from files
        prompt_path = "agents/patient_navigator/supervisor/workflow_prescription/prompts/system_prompt.md"
        examples_path = "agents/patient_navigator/supervisor/workflow_prescription/prompts/examples.md"
        
        # Auto-detect LLM client if not provided
        llm_client = kwargs.get('llm')
        if llm_client is None and not use_mock:
            llm_client = _get_claude_haiku_llm()
            if llm_client:
                logging.info("Auto-detected Claude Haiku LLM client for WorkflowPrescriptionAgent")
            else:
                logging.info("No Claude Haiku client available for WorkflowPrescriptionAgent, using mock mode")
        
        super().__init__(
            name="workflow_prescription",
            prompt=prompt_path,
            output_schema=WorkflowPrescriptionResult,
            llm=llm_client,
            mock=use_mock or llm_client is None,
            examples=examples_path,
            **kwargs
        )
        
        self.logger = logging.getLogger(f"agent.{self.name}")
        
    async def prescribe_workflows(self, user_query: str) -> WorkflowPrescriptionResult:
        """
        Classify user input into appropriate workflows.
        
        Args:
            user_query: The user's request/question
            
        Returns:
            WorkflowPrescriptionResult containing the prescribed workflows
        """
        try:
            self.logger.info(f"Prescribing workflows for query: {user_query[:100]}...")
            
            if self.mock:
                return self._mock_prescribe_workflows(user_query)
            
            # Format prompt with user query
            formatted_prompt = self.format_prompt(user_query)
            
            # Call LLM for workflow classification
            response = await self._call_llm(formatted_prompt)
            
            # Parse and validate response
            prescription_result = self._parse_workflow_response(response)
            
            # Apply deterministic execution ordering
            prescription_result.execution_order = self._determine_execution_order(
                prescription_result.prescribed_workflows
            )
            
            self.logger.info(f"Prescribed workflows: {prescription_result.prescribed_workflows}")
            return prescription_result
            
        except Exception as e:
            self.logger.error(f"Error in workflow prescription: {e}")
            # Fallback to default prescription
            return self._fallback_prescription(user_query)
    
    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM with the given prompt."""
        if self.llm is None:
            raise RuntimeError("No LLM provided.")
        
        # Handle both sync and async LLM calls
        if asyncio.iscoroutinefunction(self.llm):
            return await self.llm(prompt)
        else:
            return self.llm(prompt)
    
    def _parse_workflow_response(self, response: str) -> WorkflowPrescriptionResult:
        """Parse the LLM response into a WorkflowPrescriptionResult."""
        try:
            import json
            data = json.loads(response)
            
            # Extract prescribed workflows
            workflows = []
            for workflow_name in data.get("prescribed_workflows", []):
                try:
                    workflow_type = WorkflowType(workflow_name)
                    workflows.append(workflow_type)
                except ValueError:
                    self.logger.warning(f"Unknown workflow type: {workflow_name}")
                    continue
            
            # Create result object
            result = WorkflowPrescriptionResult(
                prescribed_workflows=workflows,
                confidence_score=data.get("confidence_score", 0.8),
                reasoning=data.get("reasoning", "LLM-based workflow prescription"),
                execution_order=[]  # Will be set later
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to parse LLM response: {e}")
            raise
    
    def _determine_execution_order(self, workflows: List[WorkflowType]) -> List[WorkflowType]:
        """Determine the optimal execution order for workflows."""
        # Simple priority-based ordering
        priority_order = [
            WorkflowType.INFORMATION_RETRIEVAL,
            WorkflowType.STRATEGY
        ]
        
        # Sort workflows by priority
        ordered_workflows = []
        for priority_workflow in priority_order:
            if priority_workflow in workflows:
                ordered_workflows.append(priority_workflow)
        
        # Add any remaining workflows
        for workflow in workflows:
            if workflow not in ordered_workflows:
                ordered_workflows.append(workflow)
        
        return ordered_workflows
    
    def _mock_prescribe_workflows(self, user_query: str) -> WorkflowPrescriptionResult:
        """Generate mock workflow prescription for testing."""
        # Simple keyword-based mock prescription
        query_lower = user_query.lower()
        
        if any(word in query_lower for word in ["strategy", "plan", "approach", "how to"]):
            workflows = [WorkflowType.STRATEGY]
            reasoning = "Mock: Query appears to request strategic guidance"
        else:
            workflows = [WorkflowType.INFORMATION_RETRIEVAL]
            reasoning = "Mock: Default to information retrieval for general queries"
        
        result = WorkflowPrescriptionResult(
            prescribed_workflows=workflows,
            confidence_score=0.8,
            reasoning=reasoning,
            execution_order=workflows
        )
        
        return result
    
    def _fallback_prescription(self, user_query: str) -> WorkflowPrescriptionResult:
        """Fallback prescription when LLM fails."""
        self.logger.warning("Using fallback prescription due to LLM failure")
        
        result = WorkflowPrescriptionResult(
            prescribed_workflows=[WorkflowType.INFORMATION_RETRIEVAL],
            confidence_score=0.6,
            reasoning="Fallback: Default to information retrieval due to processing error",
            execution_order=[WorkflowType.INFORMATION_RETRIEVAL]
        )
        
        return result 