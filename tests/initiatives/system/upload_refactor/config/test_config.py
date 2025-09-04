"""Test configuration module."""

import os
from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel, Field
from supabase import create_client, Client

@dataclass
class SupabaseTestConfig:
    """Supabase test configuration."""
    url: str
    anon_key: str
    service_role_key: str
    jwt_secret: str
    storage_bucket: str = "test_documents"

    @classmethod
    def from_env(cls) -> 'SupabaseTestConfig':
        """Create configuration from environment variables."""
        # Try test-specific variables first, then fall back to regular ones
        url = os.getenv('SUPABASE_TEST_URL') or os.getenv('SUPABASE_URL')
        anon_key = os.getenv('SUPABASE_TEST_KEY') or os.getenv('SUPABASE_ANON_KEY')
        service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        jwt_secret = os.getenv('SUPABASE_JWT_SECRET')
        storage_bucket = os.getenv('SUPABASE_STORAGE_BUCKET', 'test_documents')

        if not all([url, anon_key, service_role_key, jwt_secret]):
            missing = []
            if not url:
                missing.append('SUPABASE_TEST_URL/SUPABASE_URL')
            if not anon_key:
                missing.append('SUPABASE_TEST_KEY/SUPABASE_ANON_KEY')
            if not service_role_key:
                missing.append('SUPABASE_SERVICE_ROLE_KEY')
            if not jwt_secret:
                missing.append('SUPABASE_JWT_SECRET')
            
            raise ValueError(
                f'Missing required environment variables: {", ".join(missing)}'
            )

        return cls(
            url=url,
            anon_key=anon_key,
            service_role_key=service_role_key,
            jwt_secret=jwt_secret,
            storage_bucket=storage_bucket
        )

@dataclass
class APITestConfig:
    """API test configuration."""
    openai_key: Optional[str] = None
    llamaparse_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    anthropic_model: str = "claude-3-haiku-20240307"

    @classmethod
    def from_env(cls) -> 'APITestConfig':
        """Create configuration from environment variables."""
        return cls(
            openai_key=os.getenv('OPENAI_API_KEY'),
            llamaparse_key=os.getenv('LLAMAPARSE_API_KEY'),
            anthropic_key=os.getenv('ANTHROPIC_API_KEY'),
            anthropic_model=os.getenv('ANTHROPIC_MODEL', "claude-3-haiku-20240307")
        )

@dataclass
class TestConfig:
    """Main test configuration."""
    supabase: SupabaseTestConfig
    api: APITestConfig
    use_mock_llm: bool = True
    test_mode: bool = True
    test_user_id: Optional[str] = None
    vector_dimension: int = 1536
    similarity_threshold: float = 0.5
    max_results: int = 5

    @classmethod
    def from_env(cls) -> 'TestConfig':
        """Create configuration from environment variables."""
        return cls(
            supabase=SupabaseTestConfig.from_env(),
            api=APITestConfig.from_env(),
            use_mock_llm=os.getenv('USE_MOCK_LLM', 'true').lower() == 'true',
            test_mode=os.getenv('TEST_MODE', 'true').lower() == 'true',
            test_user_id=os.getenv('TEST_USER_ID'),
            vector_dimension=int(os.getenv('VECTOR_DIMENSION', '1536')),
            similarity_threshold=float(os.getenv('SIMILARITY_THRESHOLD', '0.5')),
            max_results=int(os.getenv('MAX_RESULTS', '5'))
        )

    def get_client(self) -> Client:
        """Create a Supabase client instance."""
        return create_client(
            self.supabase.url,
            self.supabase.service_role_key
        )

def get_base_test_config() -> TestConfig:
    """Get base test configuration from environment variables."""
    return TestConfig.from_env()
 