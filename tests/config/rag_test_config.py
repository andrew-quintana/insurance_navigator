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
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class DocumentTestConfig:
    """Configuration for testing with specific documents."""
    document_id: str
    document_type: str = "insurance_policy"
    expected_content_type: str = "policy_document"
    test_user_id: Optional[str] = None
    description: str = ""
    
    def __post_init__(self):
        """Validate document ID format."""
        try:
            uuid.UUID(self.document_id)
        except ValueError:
            raise ValueError(f"Invalid document_id format: {self.document_id}")
        
        if self.test_user_id is None:
            # Generate a consistent test user ID based on document ID
            self.test_user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"test-user-{self.document_id}"))

@dataclass
class RAGTestConfig:
    """Main configuration for RAG testing."""
    
    # Document Configuration
    primary_document: DocumentTestConfig
    additional_documents: List[DocumentTestConfig] = field(default_factory=list)
    
    # Search Configuration
    vector_search_limit: int = 10
    similarity_threshold: float = 0.7
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # LangGraph Configuration
    enable_langgraph: bool = True
    workflow_timeout: int = 30  # seconds
    max_iterations: int = 5
    
    # Agent Configuration
    primary_agent: str = "patient_navigator"
    fallback_agents: List[str] = field(default_factory=lambda: ["regulatory", "chat_communicator"])
    
    # Test Configuration
    test_queries: List[str] = field(default_factory=list)
    expected_results: Dict[str, Any] = field(default_factory=dict)
    
    # Environment Configuration
    use_mock_llm: bool = True
    mock_response_delay: float = 0.1
    
    # Validation Configuration
    validate_embeddings: bool = True
    validate_chunks: bool = True
    validate_search_results: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "primary_document": {
                "document_id": self.primary_document.document_id,
                "document_type": self.primary_document.document_type,
                "test_user_id": self.primary_document.test_user_id,
                "description": self.primary_document.description
            },
            "additional_documents": [
                {
                    "document_id": doc.document_id,
                    "document_type": doc.document_type,
                    "test_user_id": doc.test_user_id,
                    "description": doc.description
                }
                for doc in self.additional_documents
            ],
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
        primary_doc = DocumentTestConfig(**data["primary_document"])
        additional_docs = [
            DocumentTestConfig(**doc_data)
            for doc_data in data.get("additional_documents", [])
        ]
        
        return cls(
            primary_document=primary_doc,
            additional_documents=additional_docs,
            vector_search_limit=data.get("vector_search_limit", 10),
            similarity_threshold=data.get("similarity_threshold", 0.7),
            chunk_size=data.get("chunk_size", 1000),
            chunk_overlap=data.get("chunk_overlap", 200),
            enable_langgraph=data.get("enable_langgraph", True),
            workflow_timeout=data.get("workflow_timeout", 30),
            max_iterations=data.get("max_iterations", 5),
            primary_agent=data.get("primary_agent", "patient_navigator"),
            fallback_agents=data.get("fallback_agents", ["regulatory", "chat_communicator"]),
            test_queries=data.get("test_queries", []),
            expected_results=data.get("expected_results", {}),
            use_mock_llm=data.get("use_mock_llm", True),
            mock_response_delay=data.get("mock_response_delay", 0.1),
            validate_embeddings=data.get("validate_embeddings", True),
            validate_chunks=data.get("validate_chunks", True),
            validate_search_results=data.get("validate_search_results", True)
        )

# Default configurations for different test scenarios
DEFAULT_TEST_CONFIGS = {
    "current_test": RAGTestConfig(
        primary_document=DocumentTestConfig(
            document_id="d64bfbbe-ff7f-4b51-b220-a0fa20756d9d",
            document_type="insurance_policy",
            test_user_id="27b30e9d-0d06-4325-910f-20fe9d686f14",  # Correct user ID for this test data
            description="Current test document for RAG pipeline validation"
        ),
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
            test_user_id="27b30e9d-0d06-4325-910f-20fe9d686f14",  # Correct user ID for this test data
            description="Minimal test configuration"
        ),
        test_queries=["What is covered by this policy?"],
        vector_search_limit=5,
        use_mock_llm=True
    ),
    
    "comprehensive_test": RAGTestConfig(
        primary_document=DocumentTestConfig(
            document_id="d64bfbbe-ff7f-4b51-b220-a0fa20756d9d",
            document_type="insurance_policy",
            test_user_id="27b30e9d-0d06-4325-910f-20fe9d686f14",  # Correct user ID for this test data
            description="Comprehensive test with multiple scenarios"
        ),
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

def get_test_config(config_name: str = "current_test") -> RAGTestConfig:
    """
    Get a test configuration by name.
    
    Args:
        config_name: Name of the configuration to retrieve
        
    Returns:
        RAGTestConfig instance
        
    Raises:
        KeyError: If configuration name not found
    """
    if config_name not in DEFAULT_TEST_CONFIGS:
        available = list(DEFAULT_TEST_CONFIGS.keys())
        raise KeyError(f"Unknown config '{config_name}'. Available: {available}")
    
    return DEFAULT_TEST_CONFIGS[config_name]

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
        primary_document=doc_config,
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
    return get_test_config("current_test")

# Quick access functions
def get_current_document_id() -> str:
    """Get the current test document ID."""
    return get_active_config().primary_document.document_id

def get_current_user_id() -> str:
    """Get the current test user ID."""
    return get_active_config().primary_document.test_user_id

def get_test_queries() -> List[str]:
    """Get the current test queries."""
    return get_active_config().test_queries

# Current test configuration - easily changeable
CURRENT_TEST_CONFIG = RAGTestConfig(
    primary_document=DocumentTestConfig(
        document_id="d64bfbbe-ff7f-4b51-b220-a0fa20756d9d",
        description="Current test document for RAG pipeline validation"
    ),
    test_queries=[
        "What is the deductible amount?",
        "What are the copay requirements?", 
        "What services are covered?",
        "What is the out-of-pocket maximum?"
    ]
)

def get_test_config() -> RAGTestConfig:
    """Get current test configuration."""
    return CURRENT_TEST_CONFIG

def update_document_id(new_document_id: str) -> RAGTestConfig:
    """Update configuration with new document ID."""
    global CURRENT_TEST_CONFIG
    CURRENT_TEST_CONFIG.primary_document.document_id = new_document_id
    CURRENT_TEST_CONFIG.primary_document.test_user_id = str(
        uuid.uuid5(uuid.NAMESPACE_DNS, f"test-user-{new_document_id}")
    )
    return CURRENT_TEST_CONFIG 