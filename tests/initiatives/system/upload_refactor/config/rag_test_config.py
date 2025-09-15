"""
RAG Test Configuration

This module provides flexible configuration for testing RAG (Retrieval-Augmented Generation) 
functionality with LangGraph agents. It includes:

1. Document test configurations
2. LangGraph workflow settings
3. Vector search parameters
4. Agent integration settings
5. Test data management
"""

import os
import uuid
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
from pydantic import BaseModel, Field

@dataclass
class DocumentTestConfig:
    """Configuration for test documents."""
    
    document_id: str
    document_type: str
    test_user_id: str
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

class RAGTestConfig(BaseModel):
    """Configuration for RAG testing."""
    
    # Feature flags
    enable_langgraph: bool = Field(default=False, description="Enable LangGraph integration")
    enable_mock: bool = Field(default=True, description="Enable mock responses")
    enable_logging: bool = Field(default=True, description="Enable test logging")
    
    # Document configuration
    primary_document: Dict[str, Any] = Field(
        default_factory=lambda: DocumentTestConfig(
            document_id="test-doc-1",
            document_type="test",
            test_user_id="test-user-1",
            description="Test document for RAG pipeline validation"
        ).to_dict(),
        description="Primary document for testing",
    )
    additional_documents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Additional test documents",
    )
    
    # Processing configuration
    chunk_size: int = Field(default=1000, description="Document chunk size")
    chunk_overlap: int = Field(default=200, description="Document chunk overlap")
    
    # Search configuration
    vector_search_limit: int = Field(default=10, description="Maximum number of search results")
    similarity_threshold: float = Field(default=0.3, description="Minimum similarity threshold")
    
    # Workflow configuration
    workflow_timeout: int = Field(default=30, description="Workflow timeout in seconds")
    max_iterations: int = Field(default=5, description="Maximum workflow iterations")
    
    # Agent Configuration
    primary_agent: str = Field(default="patient_navigator", description="Primary agent name")
    fallback_agents: List[str] = Field(
        default=["regulatory", "chat_communicator"],
        description="List of fallback agents"
    )
    
    # Test Configuration
    test_queries: List[str] = Field(default_factory=list, description="Test queries")
    expected_results: Dict[str, Any] = Field(default_factory=dict, description="Expected test results")
    
    # Environment Configuration
    use_mock_llm: bool = Field(default=True, description="Use mock LLM")
    mock_response_delay: float = Field(default=0.1, description="Mock response delay")
    
    # Validation Configuration
    validate_embeddings: bool = Field(default=True, description="Validate embeddings")
    validate_chunks: bool = Field(default=True, description="Validate chunks")
    validate_search_results: bool = Field(default=True, description="Validate search results")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "primary_document": self.primary_document,
            "additional_documents": self.additional_documents,
            "vector_search_limit": self.vector_search_limit,
            "similarity_threshold": self.similarity_threshold,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "enable_langgraph": self.enable_langgraph,
            "workflow_timeout": self.workflow_timeout,
            "max_iterations": self.max_iterations,
            "primary_agent": self.primary_agent,
            "fallback_agents": self.fallback_agents,
            "test_queries": self.test_queries,
            "expected_results": self.expected_results,
            "use_mock_llm": self.use_mock_llm,
            "mock_response_delay": self.mock_response_delay,
            "validate_embeddings": self.validate_embeddings,
            "validate_chunks": self.validate_chunks,
            "validate_search_results": self.validate_search_results
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RAGTestConfig':
        """Create configuration from dictionary."""
        return cls(**data)

# Default configurations for different test scenarios
DEFAULT_TEST_CONFIGS = {
    "current_test": RAGTestConfig(
        primary_document=DocumentTestConfig(
            document_id="d64bfbbe-ff7f-4b51-b220-a0fa20756d9d",
            document_type="insurance_policy",
            test_user_id="27b30e9d-0d06-4325-910f-20fe9d686f14",
            description="Current test document for RAG pipeline validation"
        ).to_dict(),
        test_queries=[
            "What is the deductible amount?",
            "What are the copay requirements?",
            "What services are covered?",
            "What is the out-of-pocket maximum?",
            "Are there network restrictions?"
        ],
        expected_results={
            "deductible_query": {
                "should_find_results": True,
                "min_similarity": 0.8,
                "expected_keywords": ["deductible", "amount", "annual"]
            },
            "copay_query": {
                "should_find_results": True,
                "min_similarity": 0.7,
                "expected_keywords": ["copay", "co-pay", "payment"]
            }
        }
    ),
    
    "minimal_test": RAGTestConfig(
        primary_document=DocumentTestConfig(
            document_id="d64bfbbe-ff7f-4b51-b220-a0fa20756d9d",
            document_type="insurance_policy",
            test_user_id="27b30e9d-0d06-4325-910f-20fe9d686f14",
            description="Minimal test configuration"
        ).to_dict(),
        test_queries=["What is covered by this policy?"],
        vector_search_limit=5,
        use_mock_llm=True
    ),
    
    "comprehensive_test": RAGTestConfig(
        primary_document=DocumentTestConfig(
            document_id="d64bfbbe-ff7f-4b51-b220-a0fa20756d9d",
            document_type="insurance_policy",
            test_user_id="27b30e9d-0d06-4325-910f-20fe9d686f14",
            description="Comprehensive test with multiple scenarios"
        ).to_dict(),
        test_queries=[
            "What is the deductible amount?",
            "What are the copay requirements?",
            "What services are covered?",
            "What is the out-of-pocket maximum?",
            "Are there network restrictions?",
            "What are the prescription drug benefits?",
            "What is the process for pre-authorization?",
            "What are the emergency care provisions?"
        ],
        vector_search_limit=15,
        similarity_threshold=0.6,
        enable_langgraph=True,
        use_mock_llm=False,  # Use real LLM for comprehensive testing
        validate_embeddings=True,
        validate_chunks=True,
        validate_search_results=True
    )
}

# Initialize current test configuration
CURRENT_TEST_CONFIG = DEFAULT_TEST_CONFIGS["current_test"]

_test_config = RAGTestConfig()

def get_rag_test_config(test_name: Optional[str] = None) -> RAGTestConfig:
    """
    Get RAG test configuration.
    
    Args:
        test_name: Optional test name to get specific configuration
        
    Returns:
        Test configuration
    """
    if test_name is None:
        return _test_config
    
    if test_name not in DEFAULT_TEST_CONFIGS:
        raise ValueError(f"Unknown test configuration: {test_name}")
    
    return DEFAULT_TEST_CONFIGS[test_name]

def get_active_config() -> RAGTestConfig:
    """
    Get active test configuration.
    
    Returns:
        Active test configuration
    """
    return get_rag_test_config()

def create_custom_config(
    document_id: str,
    config_name: str = "custom",
    **kwargs
) -> RAGTestConfig:
    """
    Create a custom test configuration with a specific document ID.
    
    Args:
        document_id: The document ID to use for testing
        config_name: Name for the custom configuration
        **kwargs: Additional configuration parameters
        
    Returns:
        RAGTestConfig instance
    """
    # Start with default configuration
    base_config = DEFAULT_TEST_CONFIGS["current_test"]
    
    # Create new document config
    doc_config = DocumentTestConfig(
        document_id=document_id,
        document_type=kwargs.get("document_type", "insurance_policy"),
        description=kwargs.get("description", f"Custom test for document {document_id}")
    )
    
    # Create new RAG config
    config = RAGTestConfig(
        primary_document=doc_config.to_dict(),
        vector_search_limit=kwargs.get("vector_search_limit", base_config.vector_search_limit),
        similarity_threshold=kwargs.get("similarity_threshold", base_config.similarity_threshold),
        chunk_size=kwargs.get("chunk_size", base_config.chunk_size),
        chunk_overlap=kwargs.get("chunk_overlap", base_config.chunk_overlap),
        enable_langgraph=kwargs.get("enable_langgraph", base_config.enable_langgraph),
        workflow_timeout=kwargs.get("workflow_timeout", base_config.workflow_timeout),
        max_iterations=kwargs.get("max_iterations", base_config.max_iterations),
        primary_agent=kwargs.get("primary_agent", base_config.primary_agent),
        fallback_agents=kwargs.get("fallback_agents", base_config.fallback_agents),
        test_queries=kwargs.get("test_queries", base_config.test_queries),
        expected_results=kwargs.get("expected_results", base_config.expected_results),
        use_mock_llm=kwargs.get("use_mock_llm", base_config.use_mock_llm),
        mock_response_delay=kwargs.get("mock_response_delay", base_config.mock_response_delay),
        validate_embeddings=kwargs.get("validate_embeddings", base_config.validate_embeddings),
        validate_chunks=kwargs.get("validate_chunks", base_config.validate_chunks),
        validate_search_results=kwargs.get("validate_search_results", base_config.validate_search_results)
    )
    
    # Add to available configurations
    DEFAULT_TEST_CONFIGS[config_name] = config
    
    return config

def save_config(config: RAGTestConfig, filepath: str) -> None:
    """Save configuration to JSON file."""
    config_data = config.to_dict()
    config_data["created_at"] = datetime.utcnow().isoformat()
    config_data["version"] = "1.0.0"
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(config_data, f, indent=2)

def load_config(filepath: str) -> RAGTestConfig:
    """Load configuration from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Remove metadata
    data.pop("created_at", None)
    data.pop("version", None)
    
    return RAGTestConfig.from_dict(data)

def update_current_document_id(new_document_id: str) -> RAGTestConfig:
    """
    Update the current test configuration with a new document ID.
    
    Args:
        new_document_id: The new document ID to use
        
    Returns:
        Updated RAGTestConfig instance
    """
    return create_custom_config(
        document_id=new_document_id,
        config_name="current_test",
        description=f"Updated test document for RAG pipeline validation: {new_document_id}"
    )

# Environment variable support
def get_document_id_from_env(env_var: str = "RAG_TEST_DOCUMENT_ID") -> Optional[str]:
    """Get document ID from environment variable."""
    return os.getenv(env_var)

def get_active_config() -> RAGTestConfig:
    """
    Get the active test configuration.
    
    Checks environment variables first, then falls back to default.
    """
    # Check if document ID is set via environment
    env_doc_id = get_document_id_from_env()
    if env_doc_id:
        return create_custom_config(
            document_id=env_doc_id,
            config_name="env_config",
            description=f"Configuration from environment: {env_doc_id}"
        )
    
    # Fall back to current test config
    return get_rag_test_config("current_test")

# Quick access functions
def get_current_document_id() -> str:
    """Get the current test document ID."""
    return get_active_config().primary_document["document_id"]

def get_current_user_id() -> str:
    """Get the current test user ID."""
    return get_active_config().primary_document["test_user_id"]

def get_test_queries() -> List[str]:
    """Get the current test queries."""
    return get_active_config().test_queries

def get_rag_test_config() -> RAGTestConfig:
    """Get current RAG test configuration."""
    return _test_config

def update_document_id(new_document_id: str) -> RAGTestConfig:
    """Update configuration with new document ID."""
    global CURRENT_TEST_CONFIG
    CURRENT_TEST_CONFIG.primary_document["document_id"] = new_document_id
    CURRENT_TEST_CONFIG.primary_document["test_user_id"] = str(
        uuid.uuid5(uuid.NAMESPACE_DNS, f"test-user-{new_document_id}")
    )
    return CURRENT_TEST_CONFIG 