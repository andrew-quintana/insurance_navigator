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
import platform
from typing import Dict, Any, Optional

# Optional imports - gracefully handle missing dependencies
try:
    from langsmith import Client
    from langsmith.run_helpers import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    # Create dummy decorators if langsmith is not available
    def traceable(run_type: str = "chain"):
        def decorator(func):
            return func
        return decorator
    
    class Client:
        def __init__(self, *args, **kwargs):
            pass

# Initialize LangSmith client
def get_langsmith_client() -> Optional[Client]:
    """Initialize and return a LangSmith client if available."""
    if not LANGSMITH_AVAILABLE:
        return None
        
    api_key = os.getenv("LANGCHAIN_API_KEY")
    
    if not api_key:
        return None  # Return None instead of raising error for optional dependency
    
    project_name = os.getenv("LANGCHAIN_PROJECT", "default")
    
    return Client(api_key=api_key, project_name=project_name)

def get_git_commit() -> str:
    """Get the current git commit hash."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"]
        ).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        return "unknown"

def get_git_branch() -> str:
    """Get the current git branch name."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        ).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        return "unknown"

def get_system_info() -> Dict[str, str]:
    """Get basic system information for trace metadata."""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": platform.python_version(),
    }

def get_metadata(
    agent_name: str,
    prompt_version: str,
    run_type: str = "test",
    dataset_version: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Generate metadata for LangSmith runs.
    
    Args:
        agent_name: Name of the agent being traced
        prompt_version: Version of the prompt being used
        run_type: Type of run (e.g., test, production, development)
        dataset_version: Optional version of the dataset being used
        **kwargs: Additional metadata key-value pairs
        
    Returns:
        Dictionary of metadata
    """
    metadata = {
        "agent_name": agent_name,
        "prompt_version": prompt_version,
        "git_commit": get_git_commit(),
        "git_branch": get_git_branch(),
        "run_type": run_type,
        "model": os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
        "temperature": float(os.getenv("ANTHROPIC_TEMPERATURE", "0")),
        "max_tokens": int(os.getenv("ANTHROPIC_MAX_TOKENS", "4096")),
        **get_system_info(),
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
    run_type: str = "evaluation",
    dataset_version: Optional[str] = None
) -> Dict[str, Any]:
    """Get evaluation configuration for an agent."""
    return {
        "evaluators": DEFAULT_EVALUATORS.get(agent_name, ["qa", "embedding_distance"]),
        "metadata": get_metadata(
            agent_name=agent_name,
            prompt_version=prompt_version,
            run_type=run_type,
            dataset_version=dataset_version
        )
    } 