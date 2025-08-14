"""
Pydantic models for the upload pipeline API.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
import uuid


class UploadRequest(BaseModel):
    """Request model for document upload."""
    
    filename: str = Field(..., max_length=120, description="Document filename")
    bytes_len: int = Field(..., gt=0, le=26214400, description="File size in bytes (max 25MB)")
    mime: str = Field(..., description="MIME type")
    sha256: str = Field(..., regex=r'^[a-f0-9]{64}$', description="SHA256 hash of file content")
    ocr: bool = Field(False, description="Whether OCR processing is requested")
    
    @validator('filename')
    def validate_filename(cls, v):
        # Strip control characters per CONTEXT.md §9
        cleaned = ''.join(char for char in v if ord(char) >= 32)
        if not cleaned:
            raise ValueError('Filename cannot be empty after cleaning')
        return cleaned
    
    @validator('mime')
    def validate_mime(cls, v):
        if v != 'application/pdf':
            raise ValueError('Only application/pdf MIME type is supported')
        return v


class UploadResponse(BaseModel):
    """Response model for document upload."""
    
    job_id: uuid.UUID = Field(..., description="Unique job identifier")
    document_id: uuid.UUID = Field(..., description="Unique document identifier")
    signed_url: str = Field(..., description="Signed URL for file upload")
    upload_expires_at: datetime = Field(..., description="Upload URL expiration time")


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    
    job_id: uuid.UUID = Field(..., description="Unique job identifier")
    stage: str = Field(..., description="Current processing stage")
    state: str = Field(..., description="Current job state")
    retry_count: int = Field(..., ge=0, description="Number of retry attempts")
    progress: Dict[str, float] = Field(..., description="Processing progress")
    cost_cents: int = Field(..., ge=0, description="Processing cost in cents")
    document_id: uuid.UUID = Field(..., description="Associated document ID")
    last_error: Optional[Dict[str, Any]] = Field(None, description="Last error details")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    @validator('stage')
    def validate_stage(cls, v):
        valid_stages = {'queued', 'job_validated', 'parsing', 'parsed', 'parse_validated', 'chunking', 'chunks_buffered', 'chunked', 'embedding', 'embeddings_buffered', 'embedded'}
        if v not in valid_stages:
            raise ValueError(f'Invalid stage: {v}')
        return v
    
    @validator('state')
    def validate_state(cls, v):
        valid_states = {'queued', 'working', 'retryable', 'done', 'deadletter'}
        if v not in valid_states:
            raise ValueError(f'Invalid state: {v}')
        return v


class JobPayloadJobValidated(BaseModel):
    """Job payload for job_validated stage."""
    
    user_id: uuid.UUID = Field(..., description="User ID")
    document_id: uuid.UUID = Field(..., description="Document ID")
    file_sha256: str = Field(..., description="File SHA256 hash")
    bytes_len: int = Field(..., description="File size in bytes")
    mime: str = Field(..., description="MIME type")
    storage_path: str = Field(..., description="Storage path for raw file")


class JobPayloadParsing(BaseModel):
    """Job payload for parsing stage."""
    
    parser_name: str = Field(..., description="Parser name")
    parser_version: str = Field(..., description="Parser version")
    source_path: str = Field(..., description="Source file path")
    parsed_path: str = Field(..., description="Parsed file path")
    parsed_sha256: str = Field(..., description="Parsed content SHA256")


class JobPayloadChunking(BaseModel):
    """Job payload for chunking stage."""
    
    chunker_name: str = Field(..., description="Chunker name")
    chunker_version: str = Field(..., description="Chunker version")
    num_chunks: int = Field(..., gt=0, description="Number of chunks generated")


class JobPayloadEmbedding(BaseModel):
    """Job payload for embedding stage."""
    
    embed_model: str = Field(..., description="Embedding model name")
    embed_version: str = Field(..., description="Embedding model version")
    vector_dim: int = Field(..., description="Vector dimension")
    num_vectors: int = Field(..., gt=0, description="Number of vectors to generate")


class JobPayload(BaseModel):
    """Union type for job payloads by stage."""
    
    job_validated: Optional[JobPayloadJobValidated] = None
    parsing: Optional[JobPayloadParsing] = None
    chunking: Optional[JobPayloadChunking] = None
    embedding: Optional[JobPayloadEmbedding] = None


class ErrorDetails(BaseModel):
    """Model for error details."""
    
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class EventLog(BaseModel):
    """Model for event logging."""
    
    job_id: uuid.UUID = Field(..., description="Job ID")
    document_id: uuid.UUID = Field(..., description="Document ID")
    type: str = Field(..., description="Event type")
    severity: str = Field(..., description="Event severity")
    code: str = Field(..., description="Event code")
    payload: Optional[Dict[str, Any]] = Field(None, description="Event payload")
    correlation_id: Optional[uuid.UUID] = Field(None, description="Correlation ID")


class ProcessingLimits(BaseModel):
    """Model for processing limits validation."""
    
    max_file_size_bytes: int = Field(26214400, description="Maximum file size in bytes")
    max_pages: int = Field(200, description="Maximum number of pages")
    max_concurrent_jobs_per_user: int = Field(2, description="Max concurrent jobs per user")
    max_uploads_per_day_per_user: int = Field(30, description="Max uploads per day per user")
    max_polls_per_minute_per_job: int = Field(10, description="Max polls per minute per job")
