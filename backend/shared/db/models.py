from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import VECTOR
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class UploadJob(Base):
    """Upload job model with enhanced monitoring"""
    __tablename__ = 'upload_jobs'
    __table_args__ = {'schema': 'upload_pipeline'}
    
    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    document_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String, nullable=False)
    raw_path = Column(Text, nullable=False)
    parsed_path = Column(Text)
    parsed_sha256 = Column(String)
    chunks_version = Column(String, nullable=False, default='markdown-simple@1')
    embed_model = Column(String, default='text-embedding-3-small')
    embed_version = Column(String, default='1')
    progress = Column(JSON, default={})
    retry_count = Column(Integer, default=0)
    last_error = Column(JSON)
    webhook_secret = Column(String)
    correlation_id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    processing_started_at = Column(DateTime(timezone=True))
    processing_completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint(
            status.in_([
                'uploaded', 'parse_queued', 'parsed', 'parse_validated',
                'chunking', 'chunks_stored', 'embedding_queued',
                'embedding_in_progress', 'embeddings_stored', 'complete',
                'failed_parse', 'failed_chunking', 'failed_embedding'
            ]),
            name='valid_status'
        ),
    )

# Buffer models removed in Phase 3.7 direct-write architecture optimization
# Chunks and embeddings now written directly to document_chunks table
# See architecture_notes view in database for technical debt documentation

class Event(Base):
    """Event logging for comprehensive monitoring"""
    __tablename__ = 'events'
    __table_args__ = {'schema': 'upload_pipeline'}
    
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey('upload_pipeline.upload_jobs.job_id'), nullable=False)
    document_id = Column(UUID(as_uuid=True), nullable=False)
    ts = Column(DateTime(timezone=True), server_default=func.now())
    type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    code = Column(String, nullable=False)
    payload = Column(JSON)
    correlation_id = Column(UUID(as_uuid=True))
    
    __table_args__ = (
        CheckConstraint(
            type.in_(['stage_started', 'stage_done', 'retry', 'error', 'finalized']),
            name='valid_event_type'
        ),
        CheckConstraint(
            severity.in_(['info', 'warn', 'error']),
            name='valid_severity'
        ),
    )
