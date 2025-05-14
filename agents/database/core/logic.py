"""
Core logic for the Database Guard Agent.
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent

class DatabaseGuardAgent(BaseAgent):
    """Agent responsible for database security and access control."""

    def validate_query(self, query: str) -> Dict[str, Any]:
        """Validate and sanitize a database query."""
        prompt = self.prompt_loader.load("validate_query")
        response = self.llm.generate(prompt, {"query": query})
        return response

    def check_data_access(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a data access request is permitted."""
        prompt = self.prompt_loader.load("check_data_access")
        response = self.llm.generate(prompt, request)
        return response

    def audit_query(self, query: str) -> Dict[str, Any]:
        """Audit a database query for compliance and logging."""
        prompt = self.prompt_loader.load("audit_query")
        response = self.llm.generate(prompt, {"query": query})
        return response 