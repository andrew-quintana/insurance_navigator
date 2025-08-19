from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class UploadRequest(BaseModel):
    """Upload request model"""
    filename: str = Field(..., max_length=120, description="Document filename")
    bytes_len: int = Field(..., gt=0, le=25*1024*1024, description="File size in bytes (max 25MB)")
    mime: str = Field(..., description="MIME type")
    sha256: str = Field(..., pattern=r'^[a-fA-F0-9]{64}$', description="SHA256 hash of file content")
    ocr: bool = Field(False, description="Whether OCR processing is required")
    
    @validator('filename')
    def validate_filename(cls, v):
        # Remove control characters
        v = ''.join(char for char in v if ord(char) >= 32)
        if not v:
            raise ValueError('Filename cannot be empty after sanitization')
        return v
    
    @validator('mime')
    def validate_mime(cls, v):
        if v != 'application/pdf':
            raise ValueError('Only PDF files are supported')
        return v

class UploadResponse(BaseModel):
    """Upload response model"""
    job_id: UUID
    document_id: UUID
    signed_url: str
    upload_expires_at: datetime

class JobStatusResponse(BaseModel):
    """Job status response model"""
    job_id: UUID
    status: str
    progress: Dict[str, Any] = Field(default_factory=dict)
    retry_count: int = 0
    last_error: Optional[Dict[str, Any]] = None
    correlation_id: UUID
    created_at: datetime
    updated_at: datetime
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None

class JobProgress(BaseModel):
    """Job progress tracking model"""
    chunks_total: int = 0
    chunks_done: int = 0
    embeds_total: int = 0
    embeds_done: int = 0
    
    @property
    def chunks_percent(self) -> float:
        if self.chunks_total == 0:
            return 0.0
        return (self.chunks_done / self.chunks_total) * 100
    
    @property
    def embeds_percent(self) -> float:
        if self.embeds_total == 0:
            return 0.0
        return (self.embeds_done / self.embeds_total) * 100
    
    @property
    def overall_percent(self) -> float:
        if self.chunks_total == 0 and self.embeds_total == 0:
            return 0.0
        
        chunks_weight = 0.6  # Chunking is 60% of processing
        embeds_weight = 0.4  # Embedding is 40% of processing
        
        return (self.chunks_percent * chunks_weight) + (self.embeds_percent * embeds_weight)

class JobRetryRequest(BaseModel):
    """Job retry request model"""
    force: bool = Field(False, description="Force retry even if not in retryable state")

class JobRetryResponse(BaseModel):
    """Job retry response model"""
    job_id: UUID
    new_status: str
    retry_count: int
    message: str