"""
LangSmith Configuration

This module provides configuration and helpers for LangSmith integration, including:
1. Client initialization
2. Tracing setup
3. Evaluation configuration
4. Metadata helpers
"""

import os
import subprocess
from typing import Dict, Any, Optional
from langsmith import Client
from langsmith.run_helpers import traceable

# Initialize LangSmith client
def get_langsmith_client() -> Client:
    """Initialize and return a LangSmith client."""
    api_key = os.getenv("LANGCHAIN_API_KEY")
    
    if not api_key:
        raise ValueError("LANGCHAIN_API_KEY environment variable not set")
    
    return Client(api_key=api_key)

def get_git_commit() -> str:
    """Get the current git commit hash."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"]
        ).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        return "unknown"

def get_metadata(
    agent_name: str,
    prompt_version: str,
    dataset_version: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Generate metadata for LangSmith runs."""
    metadata = {
        "agent_name": agent_name,
        "prompt_version": prompt_version,
        "git_commit": get_git_commit(),
        "model": os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
        "temperature": float(os.getenv("ANTHROPIC_TEMPERATURE", "0")),
        "max_tokens": int(os.getenv("ANTHROPIC_MAX_TOKENS", "4096")),
    }
    
    if dataset_version:
        metadata["dataset_version"] = dataset_version
    
    metadata.update(kwargs)
    return metadata

# Default evaluators for different types of agents
DEFAULT_EVALUATORS = {
    "prompt_security": [
        "qa",
        "embedding_distance",
        "cot_criteria"
    ],
    "healthcare_guide": [
        "qa",
        "embedding_distance",
        "cot_criteria",
        "factual_consistency"
    ],
    "patient_navigator": [
        "qa",
        "embedding_distance",
        "cot_criteria",
        "helpfulness"
    ]
}

def get_eval_config(
    agent_name: str,
    prompt_version: str,
    dataset_version: Optional[str] = None
) -> Dict[str, Any]:
    """Get evaluation configuration for an agent."""
    return {
        "evaluators": DEFAULT_EVALUATORS.get(agent_name, ["qa", "embedding_distance"]),
        "metadata": get_metadata(
            agent_name=agent_name,
            prompt_version=prompt_version,
            dataset_version=dataset_version
        )
    } 