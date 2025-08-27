"""
Unified Mock Service Configuration

This module provides coordinated mock service configuration for development and testing phases.
It ensures consistent, deterministic responses across upload pipeline and agent systems.

NOTE: Mock services used only for development and testing - production uses real APIs.
"""

import hashlib
import numpy as np
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class MockServiceConfig:
    """Configuration for unified mock services."""
    
    # LlamaParse mock configuration
    llamaparse_delay: float = 2.0  # seconds
    llamaparse_failure_rate: float = 0.0  # for testing error scenarios
    llamaparse_deterministic: bool = True
    
    # OpenAI mock configuration
    openai_delay: float = 0.5  # seconds
    openai_failure_rate: float = 0.0  # for testing error scenarios
    openai_deterministic: bool = True
    
    # Mock service behavior
    enable_logging: bool = True
    log_responses: bool = False  # Don't log sensitive test data


class UnifiedMockServices:
    """Coordinated mock services for development and testing phases only."""
    
    def __init__(self, config: MockServiceConfig):
        """
        Initialize unified mock services.
        
        Args:
            config: MockServiceConfig instance
        """
        self.config = config
        self.shared_state: Dict[str, Any] = {}
        
        # NOTE: Production uses real API services
        if self.config.enable_logging:
            print("WARNING: Using mock services for development/testing only")
            print("Production will use real LlamaParse and OpenAI APIs")
    
    def generate_consistent_content(self, document_id: str) -> str:
        """
        Ensure same document_id produces same content for testing.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Deterministic mock content for testing
        """
        if not self.config.llamaparse_deterministic:
            return f"Mock content for document {document_id}"
        
        # Generate consistent content based on document_id hash
        seed = hashlib.md5(document_id.encode()).hexdigest()
        np.random.seed(int(seed[:8], 16))
        
        # Generate mock insurance policy content
        content_sections = [
            "This insurance policy provides comprehensive coverage for medical expenses.",
            "The deductible is $500 per individual or $1,000 per family.",
            "Coverage includes hospitalization, outpatient services, and prescription drugs.",
            "Preventive care is covered at 100% with no deductible.",
            "The policy has a maximum annual benefit of $10,000.",
            "Network providers offer discounted rates for covered services.",
            "Prior authorization is required for certain procedures.",
            "Claims must be submitted within 90 days of service.",
            "Appeals can be filed within 60 days of claim denial.",
            "This policy is renewable annually subject to underwriting approval."
        ]
        
        # Select sections based on document_id hash
        num_sections = (int(seed[8:12], 16) % 5) + 3  # 3-7 sections
        selected_sections = []
        
        for i in range(num_sections):
            section_idx = (int(seed[12 + i*2:14 + i*2], 16) % len(content_sections))
            selected_sections.append(content_sections[section_idx])
        
        return "\n\n".join(selected_sections)
    
    def generate_consistent_embeddings(self, text: str) -> List[float]:
        """
        Ensure same text produces same embeddings for testing.
        
        Args:
            text: Text to generate embeddings for
            
        Returns:
            Deterministic mock embedding vector
        """
        if not self.config.openai_deterministic:
            return np.random.normal(0, 1, 1536).tolist()
        
        # Generate consistent embeddings based on text hash
        text_hash = hashlib.md5(text.encode()).hexdigest()
        np.random.seed(int(text_hash[:8], 16))
        
        # Generate mock embedding vector (1536 dimensions for OpenAI text-embedding-3-small)
        embedding = np.random.normal(0, 1, 1536)
        
        # Normalize to unit vector for cosine similarity calculations
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.tolist()
    
    def generate_mock_llamaparse_response(self, document_id: str, filename: str) -> Dict[str, Any]:
        """
        Generate consistent LlamaParse mock response.
        
        Args:
            document_id: Document identifier
            filename: Document filename
            
        Returns:
            Mock LlamaParse API response
        """
        content = self.generate_consistent_content(document_id)
        
        return {
            "id": f"mock_parse_{document_id}",
            "status": "completed",
            "result": {
                "content": content,
                "metadata": {
                    "filename": filename,
                    "document_type": "policy",
                    "pages": len(content.split('\n\n')),
                    "confidence": 0.95,
                    "processing_time": self.config.llamaparse_delay
                }
            },
            "created_at": "2025-01-18T10:00:00Z",
            "completed_at": "2025-01-18T10:00:02Z"
        }
    
    def generate_mock_openai_embeddings(self, texts: List[str]) -> Dict[str, Any]:
        """
        Generate consistent OpenAI embeddings mock response.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Mock OpenAI embeddings API response
        """
        embeddings = []
        for text in texts:
            embedding = self.generate_consistent_embeddings(text)
            embeddings.append({
                "object": "embedding",
                "embedding": embedding,
                "index": len(embeddings)
            })
        
        return {
            "object": "list",
            "data": embeddings,
            "model": "text-embedding-3-small",
            "usage": {
                "prompt_tokens": sum(len(text.split()) for text in texts),
                "total_tokens": sum(len(text.split()) for text in texts)
            }
        }
    
    def simulate_processing_delay(self, service_type: str) -> float:
        """
        Simulate processing delay for mock services.
        
        Args:
            service_type: Type of service ('llamaparse' or 'openai')
            
        Returns:
            Simulated delay in seconds
        """
        if service_type == 'llamaparse':
            return self.config.llamaparse_delay
        elif service_type == 'openai':
            return self.config.openai_delay
        else:
            return 0.0
    
    def should_fail_request(self, service_type: str) -> bool:
        """
        Determine if a request should fail for testing error scenarios.
        
        Args:
            service_type: Type of service ('llamaparse' or 'openai')
            
        Returns:
            True if request should fail
        """
        if service_type == 'llamaparse':
            return np.random.random() < self.config.llamaparse_failure_rate
        elif service_type == 'openai':
            return np.random.random() < self.config.openai_failure_rate
        else:
            return False
    
    def get_mock_error_response(self, service_type: str, error_type: str = "rate_limit") -> Dict[str, Any]:
        """
        Generate mock error responses for testing error handling.
        
        Args:
            service_type: Type of service ('llamaparse' or 'openai')
            error_type: Type of error to simulate
            
        Returns:
            Mock error response
        """
        if service_type == 'llamaparse':
            if error_type == "rate_limit":
                return {
                    "error": "rate_limit_exceeded",
                    "message": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60
                }
            elif error_type == "invalid_document":
                return {
                    "error": "invalid_document",
                    "message": "Document format not supported or corrupted.",
                    "supported_formats": ["pdf", "docx", "txt"]
                }
            else:
                return {
                    "error": "processing_failed",
                    "message": "Document processing failed. Please try again.",
                    "retry_after": 30
                }
        
        elif service_type == 'openai':
            if error_type == "rate_limit":
                return {
                    "error": {
                        "message": "Rate limit exceeded for requests",
                        "type": "rate_limit_exceeded",
                        "code": "rate_limit_exceeded"
                    }
                }
            elif error_type == "quota_exceeded":
                return {
                    "error": {
                        "message": "You exceeded your current quota",
                        "type": "quota_exceeded",
                        "code": "quota_exceeded"
                    }
                }
            else:
                return {
                    "error": {
                        "message": "An error occurred during your request",
                        "type": "server_error",
                        "code": "internal_error"
                    }
                }
        
        return {"error": "unknown_service", "message": "Unknown service type"}


# Global mock service instance for consistent behavior
mock_services = UnifiedMockServices(MockServiceConfig())


def get_mock_services() -> UnifiedMockServices:
    """Get the global mock services instance."""
    return mock_services


def configure_mock_services(config: MockServiceConfig):
    """Configure the global mock services with custom settings."""
    global mock_services
    mock_services = UnifiedMockServices(config)
