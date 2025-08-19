from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

class LlamaParseArtifact(BaseModel):
    """LlamaParse artifact model"""
    type: str = Field(..., description="Artifact type (e.g., 'markdown')")
    content: str = Field(..., description="Parsed content")
    sha256: str = Field(..., pattern=r'^[a-fA-F0-9]{64}$', description="SHA256 hash of content")
    bytes: int = Field(..., gt=0, description="Content size in bytes")

class LlamaParseMeta(BaseModel):
    """LlamaParse metadata model"""
    parser_name: str = Field(..., description="Parser name (e.g., 'llamaparse')")
    parser_version: str = Field(..., description="Parser version")

class LlamaParseWebhookRequest(BaseModel):
    """LlamaParse webhook request model"""
    job_id: UUID = Field(..., description="Job ID for tracking")
    document_id: UUID = Field(..., description="Document ID")
    status: str = Field(..., description="Parse status")
    artifacts: List[LlamaParseArtifact] = Field(..., description="Parsed artifacts")
    meta: LlamaParseMeta = Field(..., description="Parser metadata")
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['parsed', 'failed', 'processing']
        if v not in valid_statuses:
            raise ValueError(f'Invalid status: {v}. Must be one of {valid_statuses}')
        return v

class LlamaParseWebhookResponse(BaseModel):
    """LlamaParse webhook response model"""
    success: bool
    message: str
    job_id: UUID
    document_id: UUID
    processed_at: datetime = Field(default_factory=datetime.utcnow)

class WebhookValidationError(BaseModel):
    """Webhook validation error model"""
    error: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)