#!/usr/bin/env python3
"""
FastAPI Insurance Navigator API - Backend-Orchestrated Upload Pipeline

Key Features:
- Backend orchestrates Supabase Edge Function pipeline
- Ensures LlamaParse processing for PDFs
- Webhook handlers for edge function status updates
- Reliable user and regulatory document uploads
"""

import os
import sys
import uuid
import aiohttp
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Request, status, UploadFile, File, Form, Response, Body, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import json
import time
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib

# Database service imports
from db.services.user_service import get_user_service, UserService
from db.services.conversation_service import get_conversation_service, ConversationService
from db.services.storage_service import get_storage_service, StorageService
from db.services.document_service import DocumentService
from db.services.db_pool import get_db_pool
from db.services.document_processing_service import DocumentProcessingService
from db.services.queue_service import QueueService
from db.services.llamaparse_service import LlamaParseService
from db.services.vector_service import VectorService

# Centralized CORS configuration
from utils.cors_config import cors_config, create_preflight_response, add_cors_headers

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Insurance Navigator API",
    description="Backend-orchestrated document processing with LlamaParse",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(CORSMiddleware)

# Pydantic models
class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: Optional[datetime] = None
    is_active: bool = True
    roles: List[str] = []

# Global service instances
user_service_instance: Optional[UserService] = None
conversation_service_instance: Optional[ConversationService] = None
storage_service_instance: Optional[StorageService] = None

# Initialize services
storage_service: Optional[StorageService] = None
queue_service: Optional[QueueService] = None
llamaparse_service: Optional[LlamaParseService] = None
vector_service: Optional[VectorService] = None
document_processing_service: Optional[DocumentProcessingService] = None

async def get_services():
    """Initialize all required services."""
    global storage_service, queue_service, llamaparse_service, vector_service, document_processing_service
    
    if not storage_service:
        storage_service = await get_storage_service()
        
    if not queue_service:
        pool = await get_db_pool()
        queue_service = QueueService(pool)
        
    if not llamaparse_service:
        llamaparse_service = LlamaParseService(
            api_key=os.getenv("LLAMAPARSE_API_KEY")
        )
        
    if not vector_service:
        pool = await get_db_pool()
        vector_service = VectorService(
            api_key=os.getenv("OPENAI_API_KEY"),
            pool=pool
        )
        
    if not document_processing_service:
        document_processing_service = DocumentProcessingService(
            storage_service=storage_service,
            queue_service=queue_service,
            llamaparse_service=llamaparse_service,
            vector_service=vector_service
        )
        
    return {
        "storage": storage_service,
        "queue": queue_service,
        "llamaparse": llamaparse_service,
        "vector": vector_service,
        "document_processing": document_processing_service
    }

# Authentication utilities
async def get_current_user(request: Request) -> UserResponse:
    """Extract and validate user from JWT token."""
    global user_service_instance
    
    if not user_service_instance:
        user_service_instance = await get_user_service()
    
    # Get token from Authorization header
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        # Validate token and get user
        user_data = await user_service_instance.get_user_from_token(token)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return UserResponse(**user_data)
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

@app.get("/documents/{document_id}/status")
async def get_document_status(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get document processing status."""
    try:
        # Get services
        services = await get_services()
        
        # Get document record
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            doc = await conn.fetchrow("""
                SELECT * FROM documents
                WHERE id = $1 AND user_id = $2
            """, document_id, current_user.id)
            
            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Get latest job status
            latest_job = await conn.fetchrow("""
                SELECT * FROM processing_jobs
                WHERE payload->>'document_id' = $1
                ORDER BY created_at DESC
                LIMIT 1
            """, document_id)
        
            # Combine status information
            return {
                "document_id": str(doc["id"]),
                "filename": doc["original_filename"],
                "status": doc["status"],
                "progress_percentage": doc["progress_percentage"],
                "created_at": doc["created_at"].isoformat(),
                "updated_at": doc["updated_at"].isoformat(),
                "job_status": latest_job["status"] if latest_job else None,
                "job_error": latest_job["error"] if latest_job else None,
                "processing_complete": doc["status"] in ["completed", "ready"]
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )

# Startup event - OPTIMIZED for fast Render deployment
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup - non-blocking for faster deployment."""
    logger.info("🚀 Starting Insurance Navigator API v3.0.0 - FAST MODE")
    logger.info("🔧 Backend-orchestrated processing enabled")
    logger.info("🦙 LlamaParse integration active")
    
    # Schedule background initialization to avoid blocking startup
    asyncio.create_task(initialize_services_background())

async def initialize_services_background():
    """Initialize services in background after app starts."""
    global user_service_instance, conversation_service_instance, storage_service_instance
    
    try:
        logger.info("🔄 Background service initialization starting...")
        
        # Initialize services with faster timeouts
        user_service_instance = await get_user_service()
        conversation_service_instance = await get_conversation_service()
        storage_service_instance = await get_storage_service()
        
        logger.info("✅ All services initialized in background")
        
    except Exception as e:
        logger.error(f"⚠️ Background service initialization failed: {e}")
        # Don't crash the app, let it start and handle errors per-request

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("🛑 Shutting down Insurance Navigator API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
