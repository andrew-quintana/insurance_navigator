"""
Evaluation Configuration

This module provides configuration for LangSmith evaluations, including:
1. Default evaluators for different agent types
2. Evaluation metadata helpers
3. Dataset versioning support
4. Test environment configuration
"""

import os
from typing import Dict, Any, List, Optional
from config.langsmith_config import get_metadata
from dataclasses import dataclass

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

# Configuration class for test environment - not a test class
@dataclass
class EnvironmentConfig:
    """Configuration for test environment."""
    # Supabase Configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    
    # Database Configuration
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    
    # Test Data Configuration
    test_data_dir: str = "tests/data"
    max_retries: int = 10
    retry_delay: int = 2  # seconds
    
    # HIPAA Compliance Settings
    encryption_enabled: bool = True
    audit_logging_enabled: bool = True
    consent_version: str = "1.0"
    
    # Test User Configuration
    test_user_email: str = "test@example.com"
    test_user_password: str = "SecureTest123!"
    
    # Storage Configuration
    storage_bucket: str = "documents"
    temp_storage_path: str = "temp_test_files"
    
    # Cleanup Configuration
    cleanup_enabled: bool = True
    preserve_audit_logs: bool = True  # Keep audit logs for compliance verification
    
    @classmethod
    def from_env(cls, env_dict: Optional[dict] = None) -> "EnvironmentConfig":
        """Create EnvironmentConfig from environment variables."""
        if env_dict is None:
            env_dict = dict(os.environ)
            
        # Map test-specific variables to standard names
        supabase_url = env_dict.get("SUPABASE_TEST_URL") or env_dict.get("SUPABASE_URL", "http://localhost:54321")
        supabase_anon_key = env_dict.get("SUPABASE_TEST_KEY") or env_dict.get("SUPABASE_ANON_KEY", "")
        supabase_service_role_key = env_dict.get("SUPABASE_SERVICE_ROLE_KEY", "test_service_key")
        
        return cls(
            supabase_url=supabase_url,
            supabase_anon_key=supabase_anon_key,
            supabase_service_role_key=supabase_service_role_key,
            db_host=env_dict.get("DB_HOST", "localhost"),
            db_port=int(env_dict.get("DB_PORT", "54321")),
            db_name=env_dict.get("DB_NAME", "postgres"),
            db_user=env_dict.get("DB_USER", "postgres"),
            db_password=env_dict.get("DB_PASSWORD", "postgres"),
            test_data_dir=env_dict.get("TEST_DATA_DIR", "tests/data"),
            max_retries=int(env_dict.get("MAX_RETRIES", "10")),
            retry_delay=int(env_dict.get("RETRY_DELAY", "2")),
            encryption_enabled=env_dict.get("ENCRYPTION_ENABLED", "true").lower() == "true",
            audit_logging_enabled=env_dict.get("AUDIT_LOGGING_ENABLED", "true").lower() == "true",
            consent_version=env_dict.get("CONSENT_VERSION", "1.0"),
            test_user_email=env_dict.get("TEST_USER_EMAIL", "test@example.com"),
            test_user_password=env_dict.get("TEST_USER_PASSWORD", "SecureTest123!"),
            storage_bucket=env_dict.get("STORAGE_BUCKET", "documents"),
            temp_storage_path=env_dict.get("TEMP_STORAGE_PATH", "temp_test_files"),
            cleanup_enabled=env_dict.get("CLEANUP_ENABLED", "true").lower() == "true",
            preserve_audit_logs=env_dict.get("PRESERVE_AUDIT_LOGS", "true").lower() == "true"
        ) 