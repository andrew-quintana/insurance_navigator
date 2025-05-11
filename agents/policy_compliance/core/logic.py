"""
Core logic for the Policy Compliance Agent.
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent

class PolicyComplianceAgent(BaseAgent):
    """Agent responsible for ensuring policy compliance in healthcare data operations."""

    def check_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if an operation complies with healthcare policies."""
        prompt = self.prompt_loader.load("check_compliance")
        response = self.llm.generate(prompt, data)
        return response

    def validate_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Validate if an action is compliant with policies."""
        prompt = self.prompt_loader.load("validate_action")
        response = self.llm.generate(prompt, action)
        return response

    def get_policy_requirements(self, scenario: str) -> Dict[str, Any]:
        """Get policy requirements for a given scenario."""
        prompt = self.prompt_loader.load("get_policy_requirements")
        response = self.llm.generate(prompt, {"scenario": scenario})
        return response 