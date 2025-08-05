"""
Workflow Prescription Agent for Patient Navigator Supervisor Workflow.

This agent classifies user requests into appropriate workflows using LLM-based
few-shot learning with confidence scoring and deterministic execution ordering.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from agents.base_agent import BaseAgent
from ..models import WorkflowPrescriptionResult, WorkflowType


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
        super().__init__(
            name="workflow_prescription",
            prompt="",  # Will be loaded from file
            output_schema=WorkflowPrescriptionResult,
            mock=use_mock,
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
    
    def _parse_workflow_response(self, response: str) -> WorkflowPrescriptionResult:
        """
        Parse LLM response into WorkflowPrescriptionResult.
        
        Args:
            response: Raw LLM response string
            
        Returns:
            Parsed WorkflowPrescriptionResult
        """
        try:
            # Try to parse as JSON first
            import json
            parsed = json.loads(response.strip())
            
            # Extract fields from parsed response
            workflows = parsed.get("prescribed_workflows", [])
            confidence = parsed.get("confidence_score", 0.5)
            reasoning = parsed.get("reasoning", "Default reasoning")
            
            # Convert string workflow names to WorkflowType enum
            workflow_types = []
            for workflow in workflows:
                if workflow == "information_retrieval":
                    workflow_types.append(WorkflowType.INFORMATION_RETRIEVAL)
                elif workflow == "strategy":
                    workflow_types.append(WorkflowType.STRATEGY)
                else:
                    self.logger.warning(f"Unknown workflow type: {workflow}")
            
            return WorkflowPrescriptionResult(
                prescribed_workflows=workflow_types,
                confidence_score=confidence,
                reasoning=reasoning,
                execution_order=[]  # Will be set by caller
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.error(f"Failed to parse workflow response: {e}")
            # Fallback to simple parsing
            return self._simple_parse_response(response)
    
    def _simple_parse_response(self, response: str) -> WorkflowPrescriptionResult:
        """
        Simple fallback parsing for malformed responses.
        
        Args:
            response: Raw LLM response string
            
        Returns:
            WorkflowPrescriptionResult with default values
        """
        # Look for workflow keywords in response
        workflows = []
        if "information_retrieval" in response.lower():
            workflows.append(WorkflowType.INFORMATION_RETRIEVAL)
        if "strategy" in response.lower():
            workflows.append(WorkflowType.STRATEGY)
        
        # Default to information_retrieval if no workflows found
        if not workflows:
            workflows = [WorkflowType.INFORMATION_RETRIEVAL]
        
        return WorkflowPrescriptionResult(
            prescribed_workflows=workflows,
            confidence_score=0.5,  # Low confidence for fallback
            reasoning="Fallback parsing due to malformed response",
            execution_order=[]
        )
    
    def _determine_execution_order(self, workflows: List[WorkflowType]) -> List[WorkflowType]:
        """
        Determine deterministic execution order for prescribed workflows.
        
        Args:
            workflows: List of prescribed workflows
            
        Returns:
            Ordered list of workflows for execution
        """
        # MVP: Simple deterministic order - information_retrieval first, then strategy
        ordered_workflows = []
        
        # Always add information_retrieval first if present
        if WorkflowType.INFORMATION_RETRIEVAL in workflows:
            ordered_workflows.append(WorkflowType.INFORMATION_RETRIEVAL)
        
        # Then add strategy if present
        if WorkflowType.STRATEGY in workflows:
            ordered_workflows.append(WorkflowType.STRATEGY)
        
        return ordered_workflows
    
    def _mock_prescribe_workflows(self, user_query: str) -> WorkflowPrescriptionResult:
        """
        Generate mock workflow prescription for testing.
        
        Args:
            user_query: The user's request/question
            
        Returns:
            Mock WorkflowPrescriptionResult
        """
        # Simple mock logic based on query content
        workflows = []
        
        if "coverage" in user_query.lower() or "benefits" in user_query.lower():
            workflows.append(WorkflowType.INFORMATION_RETRIEVAL)
        
        if "find" in user_query.lower() or "provider" in user_query.lower() or "network" in user_query.lower():
            workflows.append(WorkflowType.STRATEGY)
        
        # Default to information_retrieval if no specific patterns
        if not workflows:
            workflows = [WorkflowType.INFORMATION_RETRIEVAL]
        
        execution_order = self._determine_execution_order(workflows)
        
        return WorkflowPrescriptionResult(
            prescribed_workflows=workflows,
            confidence_score=0.8,  # High confidence for mock
            reasoning="Mock prescription based on query keywords",
            execution_order=execution_order
        )
    
    def _fallback_prescription(self, user_query: str) -> WorkflowPrescriptionResult:
        """
        Fallback prescription when LLM fails.
        
        Args:
            user_query: The user's request/question
            
        Returns:
            Fallback WorkflowPrescriptionResult
        """
        self.logger.warning("Using fallback prescription due to LLM failure")
        
        return WorkflowPrescriptionResult(
            prescribed_workflows=[WorkflowType.INFORMATION_RETRIEVAL],
            confidence_score=0.3,  # Low confidence for fallback
            reasoning="Fallback prescription due to system error",
            execution_order=[WorkflowType.INFORMATION_RETRIEVAL]
        )
    
    async def _call_llm(self, prompt: str) -> str:
        """
        Call the LLM with the formatted prompt.
        
        Args:
            prompt: Formatted prompt string
            
        Returns:
            LLM response string
        """
        if self.llm is None:
            raise ValueError("LLM not configured for WorkflowPrescriptionAgent")
        
        try:
            response = await self.llm(prompt)
            return response
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            raise
    
    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Process method for compatibility with existing patterns.
        
        Args:
            input_data: Input data (can be string or dict)
            
        Returns:
            Dictionary with workflow prescription results
        """
        if isinstance(input_data, str):
            user_query = input_data
        elif isinstance(input_data, dict):
            user_query = input_data.get("user_query", "")
        else:
            raise ValueError(f"Unsupported input type: {type(input_data)}")
        
        # Use asyncio to run async method in sync context
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.prescribe_workflows(user_query))
        
        return {
            "prescribed_workflows": [w.value for w in result.prescribed_workflows],
            "confidence_score": result.confidence_score,
            "reasoning": result.reasoning,
            "execution_order": [w.value for w in result.execution_order]
        } 