"""
Configuration management for the upload pipeline.
"""

import os
from typing import Optional
from pydantic import BaseSettings, validator


class UploadPipelineConfig(BaseSettings):
    """Configuration for the upload pipeline."""
    
    # Supabase configuration
    supabase_url: str
    supabase_service_role_key: str
    
    # External service configuration
    llamaparse_api_key: Optional[str] = None
    llamaparse_api_url: str = "https://api.llamaindex.ai"
    openai_api_key: Optional[str] = None
    
    # Processing configuration
    max_file_size_bytes: int = 26214400  # 25MB per CONTEXT.md
    max_pages: int = 200
    max_concurrent_jobs_per_user: int = 2
    max_uploads_per_day_per_user: int = 30
    max_polls_per_minute_per_job: int = 10
    
    # Chunking configuration
    chunker_name: str = "markdown-simple"
    chunker_version: str = "1"
    
    # Embedding configuration
    embed_model: str = "text-embedding-3-small"
    embed_version: str = "1"
    vector_dim: int = 1536
    max_vectors_per_batch: int = 256
    max_concurrent_batches_per_worker: int = 3
    
    # Retry configuration
    max_retries: int = 3
    base_retry_delay_seconds: int = 3
    
    # Parse timeout configuration
    parse_timeout_seconds_per_50_pages: int = 120
    max_parse_timeout_seconds: int = 600  # 10 minutes
    
    # Storage configuration
    raw_bucket: str = "raw"
    parsed_bucket: str = "parsed"
    signed_url_ttl_seconds: int = 300  # 5 minutes
    
    # Database configuration
    database_schema: str = "upload_pipeline"
    
    class Config:
        env_file = ".env"
        env_prefix = "UPLOAD_PIPELINE_"
    
    @validator('supabase_url')
    def validate_supabase_url(cls, v):
        if not v:
            raise ValueError('SUPABASE_URL is required')
        return v
    
    @validator('supabase_service_role_key')
    def validate_service_role_key(cls, v):
        if not v:
            raise ValueError('SUPABASE_SERVICE_ROLE_KEY is required')
        return v
    
    @validator('max_file_size_bytes')
    def validate_max_file_size(cls, v):
        if v <= 0:
            raise ValueError('max_file_size_bytes must be positive')
        if v > 52428800:  # 50MB hard limit
            raise ValueError('max_file_size_bytes cannot exceed 50MB')
        return v
    
    @validator('vector_dim')
    def validate_vector_dim(cls, v):
        if v != 1536:
            raise ValueError('vector_dim must be 1536 for text-embedding-3-small')
        return v


# Global configuration instance
config = UploadPipelineConfig()


def get_config() -> UploadPipelineConfig:
    """Get the global configuration instance."""
    return config
