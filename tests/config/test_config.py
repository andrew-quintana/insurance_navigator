"""Test configuration module."""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class TestConfig:
    """Test configuration settings."""
    supabase_url: str
    supabase_key: str
    test_user_id: Optional[str] = None
    test_document_bucket: str = "documents"  # Use main documents bucket
    vector_dimension: int = 1536
    similarity_threshold: float = 0.5
    max_results: int = 5

def get_test_config() -> TestConfig:
    """Get test configuration from environment variables.
    Uses the main .env configuration.
    
    Returns:
        TestConfig: Test configuration object
        
    Raises:
        ValueError: If required environment variables are not set
    """
    # Use the main Supabase configuration
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")  # Use the anon key for regular operations
    
    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_ANON_KEY environment variables must be set"
        )
    
    return TestConfig(
        supabase_url=url,
        supabase_key=key,
        test_document_bucket=os.getenv("SUPABASE_STORAGE_BUCKET", "documents"),
        vector_dimension=1536,  # OpenAI's default
        similarity_threshold=0.5,
        max_results=5
    )
 