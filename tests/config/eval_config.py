"""
Evaluation Configuration

This module provides configuration for LangSmith evaluations, including:
1. Default evaluators for different agent types
2. Evaluation metadata helpers
3. Dataset versioning support
"""

import os
from typing import Dict, Any, List, Optional
from config.langsmith_config import get_metadata

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

# Evaluation criteria for different evaluators
EVALUATOR_CRITERIA = {
    "qa": {
        "correctness": "How accurate and complete is the response?",
        "relevance": "How well does the response address the query?",
        "completeness": "Does the response cover all necessary information?"
    },
    "embedding_distance": {
        "semantic_similarity": "How similar is the response to the expected output?",
        "intent_preservation": "Does the response maintain the original intent?"
    },
    "cot_criteria": {
        "reasoning_quality": "How clear and logical is the reasoning process?",
        "step_completeness": "Are all necessary steps included?",
        "conclusion_validity": "Does the conclusion follow from the reasoning?"
    },
    "factual_consistency": {
        "accuracy": "Are the facts presented accurate?",
        "consistency": "Is the information consistent throughout?",
        "source_reliability": "Are the sources reliable?"
    },
    "helpfulness": {
        "clarity": "Is the response clear and easy to understand?",
        "actionability": "Can the user take action based on the response?",
        "comprehensiveness": "Does it cover all necessary aspects?"
    }
}

def get_eval_config(
    agent_name: str,
    prompt_version: str,
    dataset_version: Optional[str] = None,
    custom_evaluators: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get evaluation configuration for an agent."""
    # Get base evaluators for the agent type
    evaluators = DEFAULT_EVALUATORS.get(agent_name, ["qa", "embedding_distance"])
    
    # Add any custom evaluators
    if custom_evaluators:
        evaluators.extend(custom_evaluators)
    
    # Get criteria for each evaluator
    criteria = {
        evaluator: EVALUATOR_CRITERIA.get(evaluator, {})
        for evaluator in evaluators
    }
    
    return {
        "evaluators": evaluators,
        "criteria": criteria,
        "metadata": get_metadata(
            agent_name=agent_name,
            prompt_version=prompt_version,
            dataset_version=dataset_version
        )
    }

def get_dataset_path(agent_name: str, version: str) -> str:
    """Get the path to a dataset file."""
    return os.path.join(
        "datasets",
        agent_name,
        f"dataset_v{version}.json"
    )

def get_evaluation_path(agent_name: str, prompt_version: str, dataset_version: str) -> str:
    """Get the path to store evaluation results."""
    return os.path.join(
        "evaluations",
        agent_name,
        f"eval_prompt_v{prompt_version}_dataset_v{dataset_version}.json"
    ) 