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
from dotenv import load_dotenv

# Load environment variables based on ENVIRONMENT variable
environment = os.getenv('ENVIRONMENT', 'development')
if environment == 'development':
    load_dotenv('.env.development')
elif environment == 'production':
    load_dotenv('.env.production')
else:
    load_dotenv('.env')

# Import centralized configuration manager
from config.configuration_manager import get_config_manager, initialize_config
from core.service_manager import get_service_manager, initialize_service_manager
from fastapi import FastAPI, HTTPException, Depends, Request, status, UploadFile, File, Form, Response, Body, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
import json
import time
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib
from utils.cors_config import get_cors_config, get_cors_headers
import re
try:
    import psycopg2
except ImportError:
    print("Warning: psycopg2 not available, using asyncpg for database connections")
    psycopg2 = None
import traceback
from core import initialize_system, close_system, get_database, get_agents

# Database service imports
from config.database import db_pool
from db.services.user_service import get_user_service, UserService
from db.services.auth_adapter import auth_adapter
from db.services.conversation_service import get_conversation_service, ConversationService
from db.services.storage_service import get_storage_service, StorageService
from db.services.document_service import DocumentService

# Resilience imports
from core.resilience import (
    get_system_monitor,
    get_degradation_registry,
    get_circuit_breaker_registry,
    create_rag_degradation_manager,
    create_upload_degradation_manager,
    create_database_degradation_manager,
    time_metric
)

# Set up logging with more detailed format
# Note: Log level will be overridden by environment-specific configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d'
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

# Include webhook router
from api.upload_pipeline.webhooks import router as webhook_router
app.include_router(webhook_router, prefix="/api/upload-pipeline")

# Include upload router
from api.upload_pipeline.endpoints.upload import router as upload_router
app.include_router(upload_router, prefix="/api/upload-pipeline")

# System initialization and shutdown handlers
@app.on_event("startup")
async def startup_event():
    """Initialize the core system on startup."""
    try:
        logger.info("Initializing Insurance Navigator system...")
        
        # Initialize configuration manager
        environment = os.getenv('ENVIRONMENT', 'development')
        config_manager = initialize_config(environment)
        app.state.config_manager = config_manager
        logger.info(f"Configuration manager initialized for {config_manager.get_environment().value}")
        
        # Initialize upload pipeline database
        try:
            from api.upload_pipeline.database import get_database
            await get_database().initialize()
            logger.info("Upload pipeline database initialized successfully")
        except Exception as e:
            logger.warning(f"Upload pipeline database initialization failed: {e}")
            logger.warning("Upload pipeline features may not work properly")
        
        # Configure logging based on environment
        log_level = getattr(logging, config_manager.service.log_level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        logger.info(f"Logging level set to {config_manager.service.log_level}")
        
        # Initialize service manager
        service_manager = initialize_service_manager()
        app.state.service_manager = service_manager
        
        # Register core services
        await _register_core_services(service_manager, config_manager)
        
        # Initialize resilience systems
        await _initialize_resilience_systems()
        
        # Initialize all services
        success = await service_manager.initialize_all_services()
        if not success:
            raise RuntimeError("Failed to initialize core services")
        
        # Initialize core system
        await initialize_system()
        
        # Start monitoring
        system_monitor = get_system_monitor()
        await system_monitor.start()
        
        logger.info("System initialization completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown the core system on shutdown."""
    try:
        logger.info("Shutting down Insurance Navigator system...")
        
        # Stop monitoring
        system_monitor = get_system_monitor()
        await system_monitor.stop()
        
        # Shutdown services
        service_manager = getattr(app.state, 'service_manager', None)
        if service_manager:
            await service_manager.shutdown_all_services()
        
        # Shutdown core system
        await close_system()
        logger.info("System shutdown completed")
    except Exception as e:
        logger.error(f"Error during system shutdown: {e}")

# Custom error handler middleware
class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            logger.warning(f"HTTP Exception: {str(e)} - Path: {request.url.path}")
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}\n{traceback.format_exc()}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )

# Request logging middleware with performance tracking
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Log request details
        logger.info(f"Request {request_id} started - Method: {request.method} Path: {request.url.path}")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response details
            status_code = response.status_code
            logger.info(
                f"Request {request_id} completed - "
                f"Status: {status_code} - "
                f"Time: {process_time:.2f}s"
            )
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request {request_id} failed - "
                f"Error: {str(e)} - "
                f"Time: {process_time:.2f}s"
            )
            raise

# Add middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    **get_cors_config()
)

# Health check cache with type hints
_health_cache: Dict[str, Any] = {"result": None, "timestamp": 0}

@app.head("/")
async def root_head():
    """Root endpoint for HEAD requests."""
    return Response(status_code=200)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Insurance Navigator API v3.0.0"}

@app.head("/health")
async def health_check_head():
    """Quick health check for HEAD requests."""
    return Response(status_code=200)

@app.get("/debug-auth")
async def debug_auth():
    """Debug endpoint to check auth adapter status."""
    try:
        from db.services.auth_adapter import auth_adapter
        return {
            "auth_adapter_loaded": True,
            "backend_type": auth_adapter.backend_type,
            "test_user_info": await auth_adapter.get_user_info("test_id")
        }
    except Exception as e:
        return {
            "auth_adapter_loaded": False,
            "error": str(e)
        }

@app.get("/debug-resilience")
async def debug_resilience():
    """Debug endpoint to check resilience system status."""
    try:
        # Get resilience registries
        degradation_registry = get_degradation_registry()
        circuit_breaker_registry = get_circuit_breaker_registry()
        system_monitor = get_system_monitor()
        
        # Get degradation status
        service_levels = degradation_registry.get_all_levels()
        degraded_services = degradation_registry.get_degraded_services()
        unavailable_services = degradation_registry.get_unavailable_services()
        
        # Get circuit breaker status
        cb_stats = await circuit_breaker_registry.get_all_stats()
        cb_names = circuit_breaker_registry.list_names()
        
        # Get system status
        system_status = await system_monitor.get_system_status()
        
        return {
            "degradation_managers": {
                "registered": list(service_levels.keys()),
                "service_levels": {k: v.value for k, v in service_levels.items()},
                "degraded_services": degraded_services,
                "unavailable_services": unavailable_services
            },
            "circuit_breakers": {
                "registered": cb_names,
                "stats": {
                    name: {
                        "state": stats.state.value,
                        "total_calls": stats.total_calls,
                        "total_failures": stats.total_failures,
                        "success_rate": stats.success_rate()
                    }
                    for name, stats in cb_stats.items()
                }
            },
            "system_monitor": {
                "overall_health": system_status.get("overall_health", 0.0),
                "status": system_status.get("status", "unknown"),
                "active_alerts": system_status.get("active_alerts", 0)
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__
        }

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint with service manager integration."""
    global _health_cache
    current_time = time.time()
    cache_duration = 30  # seconds
    
    # Return cached result if still valid
    if _health_cache["result"] and (current_time - _health_cache["timestamp"]) < cache_duration:
        return _health_cache["result"]
    
    # For HEAD requests, return immediately
    if request.method == "HEAD":
        return Response(status_code=200)
    
    # Perform actual health check
    try:
        # Get service manager
        service_manager = getattr(app.state, 'service_manager', None)
        
        if service_manager:
            # Use service manager for health checks
            services_health = await service_manager.health_check_all()
            
            # Determine overall status
            all_healthy = all(
                service_info.get("healthy", False) 
                for service_info in services_health.values()
            )
            
            result = {
                "status": "healthy" if all_healthy else "degraded",
                "timestamp": datetime.utcnow().isoformat(),
                "services": services_health,
                "version": "3.0.0"
            }
        else:
            # Fallback to basic health check
            db_status = "unavailable"
            if db_pool:
                try:
                    client = await db_pool.get_client()
                    db_status = "healthy" if client else "not_initialized"
                except Exception as e:
                    db_status = f"error: {str(e)[:50]}"
            
            services_status = {
                "database": db_status,
                "supabase_auth": "healthy" if os.getenv("SUPABASE_URL") else "not_configured",
                "llamaparse": "healthy" if os.getenv("LLAMAPARSE_API_KEY") else "not_configured",
                "openai": "healthy" if os.getenv("OPENAI_API_KEY") else "not_configured"
            }

            result = {
                "status": "healthy" if all(s == "healthy" for s in services_status.values()) else "degraded",
                "timestamp": datetime.utcnow().isoformat(),
                "services": services_status,
                "version": "3.0.0"
            }
        
        # Cache the result
        _health_cache["result"] = result
        _health_cache["timestamp"] = current_time
        
        return result
    except Exception as e:
        logger.error(f"Health check failed: {e}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# Global service instances
user_service_instance = None
conversation_service_instance = None
storage_service_instance = None

# Initialize services
storage_service: Optional[StorageService] = None

async def _register_core_services(service_manager, config_manager):
    """Register core services with the service manager."""
    try:
        # Register database service
        async def init_database():
            await db_pool.initialize()
            return db_pool
        
        async def health_check_database(instance):
            try:
                client = await instance.get_client()
                return client is not None
            except Exception:
                return False
        
        service_manager.register_service(
            name="database",
            service_type=type(db_pool),
            init_func=init_database,
            health_check=health_check_database
        )
        
        # Register RAG service
        async def init_rag():
            from agents.tooling.rag.core import RAGTool, RetrievalConfig
            rag_config = RetrievalConfig(
                similarity_threshold=config_manager.get_rag_similarity_threshold(),
                max_chunks=config_manager.get_config("rag.max_chunks", 10),
                token_budget=config_manager.get_config("rag.token_budget", 4000)
            )
            return {"tool": RAGTool, "config": rag_config}
        
        async def health_check_rag(instance):
            try:
                # Test RAG tool instantiation
                test_tool = instance["tool"]("test_user", instance["config"])
                return test_tool is not None
            except Exception:
                return False
        
        service_manager.register_service(
            name="rag",
            service_type=dict,
            dependencies=["database"],
            init_func=init_rag,
            health_check=health_check_rag
        )
        
        # Register user service
        async def init_user_service():
            return await get_user_service()
        
        service_manager.register_service(
            name="user_service",
            service_type=type(None),
            dependencies=["database"],
            init_func=init_user_service
        )
        
        # Register conversation service
        async def init_conversation_service():
            return await get_conversation_service()
        
        service_manager.register_service(
            name="conversation_service",
            service_type=type(None),
            dependencies=["database"],
            init_func=init_conversation_service
        )
        
        # Register storage service
        async def init_storage_service():
            return await get_storage_service()
        
        service_manager.register_service(
            name="storage_service",
            service_type=type(None),
            dependencies=["database"],
            init_func=init_storage_service
        )
        
        logger.info("Core services registered successfully")
        
    except Exception as e:
        logger.error(f"Failed to register core services: {e}")
        raise

async def _initialize_resilience_systems():
    """Initialize resilience systems including degradation managers."""
    try:
        # Get registries
        degradation_registry = get_degradation_registry()
        circuit_breaker_registry = get_circuit_breaker_registry()
        
        # Register degradation managers for key services
        rag_degradation = create_rag_degradation_manager()
        upload_degradation = create_upload_degradation_manager()
        database_degradation = create_database_degradation_manager()
        
        degradation_registry.register("rag", rag_degradation)
        degradation_registry.register("upload", upload_degradation)
        degradation_registry.register("database", database_degradation)
        
        # Create and register circuit breakers
        from core.resilience import (
            create_database_circuit_breaker,
            create_rag_circuit_breaker,
            CircuitBreakerConfig
        )
        
        # Create circuit breakers for expected services
        database_breaker = create_database_circuit_breaker("service_database")
        rag_breaker = create_rag_circuit_breaker("service_rag")
        
        # Register circuit breakers in the registry
        await circuit_breaker_registry.get_or_create("service_database", database_breaker.config)
        await circuit_breaker_registry.get_or_create("service_rag", rag_breaker.config)
        
        logger.info("Resilience systems initialized successfully")
        logger.info(f"Registered degradation managers: {list(degradation_registry.get_all_levels().keys())}")
        logger.info(f"Registered circuit breakers: {circuit_breaker_registry.list_names()}")
        
    except Exception as e:
        logger.error(f"Failed to initialize resilience systems: {e}")
        raise

# Authentication utilities
async def get_current_user(request: Request) -> Dict[str, Any]:
    """Extract and validate user from JWT token."""
    # Get tokens from Authorization header
    auth_header = request.headers.get("authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    access_token = auth_header.split(" ")[1]
    
    try:
        # Use auth adapter for token validation
        user_data = auth_adapter.validate_token(access_token)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@app.get("/documents/{document_id}/status")
async def get_document_status(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get simplified document status."""
    try:
        # Get document service
        from db.services.document_service import get_document_service
        doc_service = await get_document_service()
        
        # Get document status
        status = await doc_service.get_document_status(document_id, str(current_user["id"]))
        
        if not status:
                raise HTTPException(status_code=404, detail="Document not found")
            
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )

# Upload Pipeline Models
class UploadRequest(BaseModel):
    filename: str = Field(..., description="Name of the file to upload")
    bytes_len: int = Field(..., description="Size of the file in bytes")
    mime: str = Field(..., description="MIME type of the file")
    sha256: str = Field(..., description="SHA256 hash of the file content")
    ocr: bool = Field(default=False, description="Whether to perform OCR on the file")

class UploadResponse(BaseModel):
    job_id: str = Field(..., description="Unique identifier for the upload job")
    document_id: str = Field(..., description="Unique identifier for the document")
    signed_url: str = Field(..., description="Signed URL for uploading the file")
    upload_expires_at: datetime = Field(..., description="When the signed URL expires")

# Upload Pipeline Database Functions
async def get_upload_pipeline_db():
    """Get database connection for upload pipeline operations."""
    import asyncpg
    from dotenv import load_dotenv
    
    load_dotenv('.env.production')
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        raise HTTPException(status_code=500, detail="Database configuration missing")
    
    return await asyncpg.connect(database_url, statement_cache_size=0)

async def generate_signed_url(storage_path: str, ttl_seconds: int = 3600) -> str:
    """Generate a signed URL for file upload."""
    # Use the upload pipeline's signed URL generation logic
    from api.upload_pipeline.endpoints.upload import _generate_signed_url
    return await _generate_signed_url(storage_path, ttl_seconds)

async def create_document_record(conn, document_id: str, user_id: str, filename: str, 
                               mime: str, bytes_len: int, file_sha256: str, raw_path: str):
    """Create a document record in the upload_pipeline.documents table."""
    try:
        await conn.execute("""
            INSERT INTO upload_pipeline.documents (
                document_id, user_id, filename, mime, bytes_len, 
                file_sha256, raw_path, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
        """, document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path)
    except Exception as e:
        if "duplicate key value violates unique constraint" in str(e):
            # Document already exists for this user (same user uploading same content)
            logger.info(f"📄 Document already exists for user {user_id}: {document_id}")
            # Update the existing document with new metadata if needed
            await conn.execute("""
                UPDATE upload_pipeline.documents 
                SET filename = $3, mime = $4, bytes_len = $5, 
                    file_sha256 = $6, raw_path = $7, updated_at = NOW()
                WHERE document_id = $1 AND user_id = $2
            """, document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path)
        else:
            raise e

async def create_document_with_content_deduplication(conn, document_id: str, user_id: str, filename: str, 
                                                   mime: str, bytes_len: int, file_sha256: str, raw_path: str):
    """Create a document record with content deduplication - copies processed data from existing documents."""
    
    # Check if the same content (file_sha256) already exists for other users
    existing_docs = await conn.fetch("""
        SELECT document_id, user_id, processing_status, created_at
        FROM upload_pipeline.documents 
        WHERE file_sha256 = $1 AND user_id != $2
        ORDER BY created_at ASC
        LIMIT 1
    """, file_sha256, user_id)
    
    if existing_docs:
        # Content already exists for another user - copy processed data
        source_doc = existing_docs[0]
        logger.info(f"🔄 Content deduplication: Copying processed data from document {source_doc['document_id']} (user {source_doc['user_id']}) to new document {document_id} (user {user_id})")
        
        # Create the new document record
        await conn.execute("""
            INSERT INTO upload_pipeline.documents (
                document_id, user_id, filename, mime, bytes_len, 
                file_sha256, raw_path, processing_status, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
        """, document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path, source_doc['processing_status'])
        
        # Copy all chunks from the source document to the new document
        await conn.execute("""
            INSERT INTO upload_pipeline.document_chunks (
                chunk_id, document_id, chunk_ord, text, embedding, created_at
            )
            SELECT 
                gen_random_uuid() as chunk_id,
                $1 as document_id,
                chunk_ord,
                text,
                embedding,
                NOW() as created_at
            FROM upload_pipeline.document_chunks 
            WHERE document_id = $2
        """, document_id, source_doc['document_id'])
        
        # Get the count of copied chunks
        chunk_count = await conn.fetchval("""
            SELECT COUNT(*) FROM upload_pipeline.document_chunks WHERE document_id = $1
        """, document_id)
        
        logger.info(f"✅ Content deduplication complete: Copied {chunk_count} chunks from document {source_doc['document_id']} to {document_id}")
        
    else:
        # No existing content found - create new document normally
        try:
            await conn.execute("""
                INSERT INTO upload_pipeline.documents (
                    document_id, user_id, filename, mime, bytes_len, 
                    file_sha256, raw_path, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
            """, document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path)
            
            logger.info(f"✅ New document created: {document_id} for user {user_id}")
            
        except Exception as e:
            if "duplicate key value violates unique constraint" in str(e):
                # Document already exists for this user (same user uploading same content)
                logger.info(f"📄 Document already exists for user {user_id}: {document_id}")
                # Update the existing document with new metadata if needed
                await conn.execute("""
                    UPDATE upload_pipeline.documents 
                    SET filename = $3, mime = $4, bytes_len = $5, 
                        file_sha256 = $6, raw_path = $7, updated_at = NOW()
                    WHERE document_id = $1 AND user_id = $2
                """, document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path)
            else:
                raise e

async def create_upload_job(conn, job_id: str, document_id: str, user_id: str, 
                          request: UploadRequest, raw_path: str):
    """Create an upload job in the upload_pipeline.upload_jobs table."""
    payload = {
        "user_id": user_id,
        "document_id": document_id,
        "file_sha256": request.sha256,
        "bytes_len": request.bytes_len,
        "mime": request.mime,
        "storage_path": raw_path
    }
    
    try:
        await conn.execute("""
            INSERT INTO upload_pipeline.upload_jobs (
                job_id, document_id, status, state, progress, 
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
        """, job_id, document_id, "uploaded", "queued", json.dumps(payload))
    except Exception as e:
        if "duplicate key value violates unique constraint" in str(e):
            # Job already exists, update it
            logger.info(f"📄 Upload job already exists: {job_id}")
            await conn.execute("""
                UPDATE upload_pipeline.upload_jobs 
                SET status = $2, state = $3, progress = $4, updated_at = NOW()
                WHERE job_id = $1
            """, job_id, "uploaded", "queued", json.dumps(payload))
        else:
            raise e

# New Upload Pipeline Endpoint
# Upload Pipeline Endpoint moved to router at /api/upload-pipeline/upload

# Upload pipeline endpoints are now handled by the router at /api/upload-pipeline/*

# Legacy endpoint for backward compatibility
@app.post("/upload-document-backend")
async def upload_document_backend(
    file: UploadFile = File(...),
    policy_id: str = Form(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Legacy upload endpoint - redirects to new upload pipeline."""
    logger.info(f"📄 Legacy upload request received - File: {file.filename}, User: {current_user.get('email', 'unknown')}")
    
    try:
        # Read file content
        contents = await file.read()
        file_size = len(contents)
        file_sha256 = hashlib.sha256(contents).hexdigest()
        
        # Create upload request
        upload_request = UploadRequest(
            filename=file.filename,
            bytes_len=file_size,
            mime=file.content_type or "application/octet-stream",
            sha256=file_sha256,
            ocr=False
        )
        
        # Call the new upload pipeline endpoint
        from api.upload_pipeline.endpoints.upload import upload_document
        return await upload_document(upload_request)
        
    except Exception as e:
        logger.error(f"❌ Legacy upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Alternative legacy endpoint without authentication for frontend compatibility
@app.post("/upload-document-backend-no-auth")
async def upload_document_backend_no_auth(
    file: UploadFile = File(...),
    policy_id: str = Form(...)
):
    """Legacy upload endpoint without authentication - for frontend compatibility."""
    logger.info(f"📄 Legacy upload request received (no auth) - File: {file.filename}")
    
    try:
        # Read file content
        contents = await file.read()
        file_size = len(contents)
        file_sha256 = hashlib.sha256(contents).hexdigest()
        
        # Create upload request
        upload_request = UploadRequest(
            filename=file.filename,
            bytes_len=file_size,
            mime=file.content_type or "application/octet-stream",
            sha256=file_sha256,
            ocr=False
        )
        
        # Create a mock user for the upload
        mock_user = {
            "id": "00000000-0000-0000-0000-000000000000",
            "email": "anonymous@example.com"
        }
        
        # Call the new upload pipeline endpoint
        from api.upload_pipeline.endpoints.upload import upload_document
        return await upload_document(upload_request)
        
    except Exception as e:
        logger.error(f"❌ Legacy upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def notify_document_status(
    user_id: str,
    document_id: str,
    status: str,
    message: str
):
    """Send document status notification via WebSocket."""
    try:
        # Get Supabase client
        supabase = await get_supabase_client()
        
        # Send realtime notification
        await supabase.realtime.send({
            "type": "broadcast",
            "event": "document_status",
            "topic": f"user_documents:{user_id}",
            "payload": {
                "document_id": document_id,
                "status": status,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to send WebSocket notification: {e}")
        # Don't re-raise the exception as this is a non-critical operation

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application services"""
    logger.info("🚀 Starting Insurance Navigator API v3.0.0")
    logger.info("🔧 Backend-orchestrated processing enabled")
    logger.info("🔄 Service initialization starting...")
    
    try:
        # Initialize database pool
        await db_pool.initialize()
        logger.info("✅ Database pool initialized")
        
        # Initialize other services
        user_service_instance = await get_user_service()
        logger.info("✅ User service initialized")
        
        conversation_service_instance = await get_conversation_service()
        logger.info("✅ Conversation service initialized")
        
        storage_service_instance = await get_storage_service()
        logger.info("✅ Storage service initialized")
        
        # Initialize RAG tool and chat interface
        try:
            from agents.tooling.rag.core import RAGTool, RetrievalConfig
            from agents.patient_navigator.chat_interface import PatientNavigatorChatInterface
            logger.info("✅ RAG tool and chat interface imports successful")
            
            # Get configuration manager
            config_manager = getattr(app.state, 'config_manager', None)
            if not config_manager:
                logger.warning("Configuration manager not available, using defaults")
                config_manager = get_config_manager()
            
            # Initialize RAG tool with configuration from manager
            rag_config = RetrievalConfig(
                similarity_threshold=config_manager.get_rag_similarity_threshold(),
                max_chunks=config_manager.get_config("rag.max_chunks", 10),
                token_budget=config_manager.get_config("rag.token_budget", 4000)
            )
            
            # Store RAG tool globally for use in chat endpoints
            app.state.rag_tool = RAGTool
            app.state.rag_config = rag_config
            logger.info(f"✅ RAG tool initialized with similarity threshold: {rag_config.similarity_threshold}")
            
        except ImportError as e:
            logger.warning(f"⚠️ RAG tool or chat interface import failed: {e}")
            app.state.rag_tool = None
            app.state.rag_config = None
        
        # Verify environment variables
        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
            "LLAMAPARSE_API_KEY",
            "OPENAI_API_KEY"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.warning(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
        
        logger.info("✅ Core services initialized")
        
    except Exception as e:
        logger.error(f"⚠️ Service initialization failed: {str(e)}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup application resources"""
    logger.info("🛑 Shutting down Insurance Navigator API")
    try:
        # Cleanup database pool
        await db_pool.cleanup()
        logger.info("✅ Database pool cleaned up")
        
        # Cleanup other services
        # ... existing cleanup code ...
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

@app.post("/login")
async def login(request: Request, response: Response):
    """Login endpoint with validation and proper error handling."""
    try:
        # Get request body
        body = await request.json()
        email = body.get("email", "").strip()
        password = body.get("password", "")
        
        if not email or not password:
            logger.warning("Login attempt failed: Missing email or password")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        
        # Use auth adapter for authentication
        auth_result = await auth_adapter.authenticate_user(email, password)
        if not auth_result:
            logger.warning(f"❌ Authentication failed for user: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        logger.info(f"✅ User logged in successfully: {email}")
        return {
            "access_token": auth_result["access_token"],
            "token_type": "bearer",
            "user": auth_result["user"]
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Login failed - Invalid JSON: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

# Add /me endpoint for session validation
@app.post("/chat")
@time_metric("chat.request_duration", {"endpoint": "chat"})
async def chat_with_agent(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Chat endpoint for AI agent interaction with full agentic workflow integration."""
    try:
        data = await request.json()
        message = data.get("message", "")
        conversation_id = data.get("conversation_id", "")
        user_language = data.get("user_language", "auto")
        context = data.get("context", {})
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message is required"
            )
        
        # Get RAG service from service manager
        service_manager = getattr(app.state, 'service_manager', None)
        if not service_manager:
            logger.error("Service manager not available")
            raise HTTPException(
                status_code=500,
                detail="Service manager not available"
            )
        
        rag_service = service_manager.get_service("rag")
        if not rag_service:
            logger.error("RAG service not available")
            raise HTTPException(
                status_code=500,
                detail="RAG service not available"
            )
        
        # Import the chat interface using safe imports
        from utils.import_utilities import (
            safe_import_patient_navigator_chat_interface,
            safe_import_chat_message
        )
        
        PatientNavigatorChatInterface = safe_import_patient_navigator_chat_interface()
        ChatMessage = safe_import_chat_message()
        
        if not PatientNavigatorChatInterface or not ChatMessage:
            logger.error("Failed to import required chat interface classes")
            raise HTTPException(
                status_code=500, 
                detail="Chat service temporarily unavailable - missing required components"
            )
        
        # Initialize chat interface (singleton pattern for efficiency)
        if not hasattr(chat_with_agent, '_chat_interface'):
            chat_with_agent._chat_interface = PatientNavigatorChatInterface()
        
        chat_interface = chat_with_agent._chat_interface
        
        # Create ChatMessage object
        # Temporary fix: Map minimal_ prefixed IDs to known UUID with documents
        # TODO: Remove this once proper UUID generation is deployed
        raw_user_id = current_user.get("id", "anonymous")
        if raw_user_id.startswith("minimal_"):
            user_id = "936551b6-b7a4-4d3d-9fe0-a491794fd66b"  # Known user with documents
        else:
            user_id = raw_user_id
            
        chat_message = ChatMessage(
            user_id=user_id,
            content=message,
            timestamp=time.time(),
            message_type="text",
            language=user_language if user_language != "auto" else "en",
            metadata={
                "conversation_id": conversation_id,
                "context": context,
                "api_request": True
            }
        )
        
        # Process message through the complete agentic workflow with graceful degradation
        degradation_registry = get_degradation_registry()
        rag_degradation = degradation_registry.get("rag")
        
        if rag_degradation:
            # Use graceful degradation for RAG processing
            async def process_with_rag():
                return await chat_interface.process_message(chat_message)
            
            degradation_result = await rag_degradation.execute_with_fallback(process_with_rag)
            
            if degradation_result.success:
                response = degradation_result.result
                # Add degradation metadata
                if degradation_result.service_level.value != "full":
                    logger.info(f"Chat processed with degraded service level: {degradation_result.service_level.value}")
            else:
                # All fallbacks failed, return error response
                logger.error(f"Chat processing failed completely: {degradation_result.error}")
                raise HTTPException(
                    status_code=500,
                    detail="Chat service is temporarily unavailable. Please try again later."
                )
        else:
            # Fallback to direct processing if degradation manager not available
            response = await chat_interface.process_message(chat_message)
        
        # Return enhanced response with metadata
        return {
            "text": response.content,
            "response": response.content,  # For backward compatibility
            "conversation_id": conversation_id or f"conv_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "processing_time": response.processing_time,
                "confidence": response.confidence,
                "agent_sources": response.agent_sources,
                "input_processing": {
                    "original_language": user_language,
                    "translation_applied": user_language != "en" and user_language != "auto"
                },
                "agent_processing": {
                    "agents_used": response.agent_sources,
                    "processing_time_ms": int(response.processing_time * 1000)
                },
                "output_formatting": {
                    "tone_applied": "empathetic",
                    "readability_level": "8th_grade",
                    "next_steps_included": "next_steps" in response.metadata
                }
            },
            "next_steps": response.metadata.get("next_steps", []),
            "sources": response.agent_sources
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        # Return graceful error response
        return {
            "text": "I apologize, but I encountered an error processing your request. Please try again in a moment.",
            "response": "I apologize, but I encountered an error processing your request. Please try again in a moment.",
            "conversation_id": conversation_id or f"conv_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "processing_time": 0.0,
                "confidence": 0.0,
                "agent_sources": ["system"],
                "error": str(e),
                "error_type": "processing_error"
            },
            "next_steps": ["Please try rephrasing your question", "Contact support if the issue persists"],
            "sources": ["system"]
        }

@app.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information."""
    try:
        # For minimal auth, return the user data from token validation directly
        # This avoids the database lookup that causes UUID errors
        # Updated: 2025-09-05 - Force deployment
        if current_user.get("id", "").startswith("minimal_"):
            return {
                "id": current_user["id"],
                "email": current_user["email"],
                "name": current_user.get("name", current_user["email"].split("@")[0]),
                "created_at": current_user.get("iat", "2025-01-01T00:00:00Z"),
                "auth_method": "minimal_auth"
            }
        
        # For other auth methods, use auth adapter
        try:
            user_data = await auth_adapter.get_user_info(current_user["id"])
            if user_data:
                return user_data
        except Exception as e:
            logger.warning(f"Auth adapter failed, falling back to token data: {e}")
        
        # Fallback to token data
        return {
            "id": current_user["id"],
            "email": current_user["email"],
            "name": current_user.get("name", current_user["email"].split("@")[0]),
            "created_at": current_user.get("iat", "2025-01-01T00:00:00Z"),
            "auth_method": "token_fallback"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

# Add OPTIONS route handler for explicit preflight handling
@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request, rest_of_path: str):
    """Handle preflight requests explicitly"""
    try:
        origin = request.headers.get("Origin")
        if not origin:
            return Response(status_code=400, content="Origin header is required")
            
        # Return CORS headers for the specific origin
        headers = get_cors_headers(origin)
        if not headers:
            return Response(status_code=400, content="Origin not allowed")
            
        return Response(status_code=200, headers=headers)
    except Exception as e:
        logger.error(f"Error in preflight handler: {str(e)}")
        return Response(status_code=500, content="Internal server error")

# Add middleware to ensure CORS headers on all responses
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    """Add CORS headers to all responses"""
    try:
        response = await call_next(request)
        
        # Add CORS headers based on origin
        origin = request.headers.get("Origin")
        if origin:
            headers = get_cors_headers(origin)
            for key, value in headers.items():
                response.headers[key] = value
        
        return response
    except Exception as e:
        logger.error(f"Error in CORS middleware: {str(e)}")
        return Response(status_code=500, content="Internal server error")

@app.post("/register", response_model=Dict[str, Any])
async def register(request: Dict[str, Any]):
    """Register a new user with validation and duplicate checking."""
    try:
        # Extract and validate required fields
        email = request.get("email", "").strip()
        password = request.get("password", "")
        name = request.get("name", "").strip() or request.get("full_name", "").strip()
        
        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        
        logger.info(f"🚀 Starting registration for: {email}")
        
        # Use auth adapter for user creation
        auth_result = await auth_adapter.create_user(
            email=email,
            password=password,
            name=name or email.split("@")[0]
        )
        
        logger.info(f"✅ User registered successfully: {email}")
        return auth_result
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Registration validation failed for {request.get('email', 'unknown')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Registration error for {request.get('email', 'unknown')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )

@app.get("/api/v1/status")
async def detailed_status():
    """Detailed status check including database connectivity"""
    try:
        # Check database connection
        conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"))
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "database": db_status,
        "environment": os.getenv("NODE_ENV", "development")
    }

# Authentication models
class SignupRequest(BaseModel):
    """Request model for user signup."""
    email: str
    password: str
    consent_version: str
    consent_timestamp: str

class LoginRequest(BaseModel):
    """Request model for user login."""
    email: str
    password: str

@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):
    """
    Sign up a new user with HIPAA consent tracking.
    
    Args:
        request: SignupRequest containing user data
        
    Returns:
        Dict containing user data and access token
    """
    try:
        # Use auth adapter for user creation
        user_data = await auth_adapter.create_user(
            email=request.email,
            password=request.password,
            name=request.email.split("@")[0]  # Use email prefix as name if not provided
        )
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/auth/login")
async def login(request: LoginRequest):
    """
    Authenticate a user and return session data.
    
    Args:
        request: LoginRequest containing user credentials
        
    Returns:
        Dict containing user data and session info
    """
    try:
        # Use auth adapter for authentication
        auth_data = await auth_adapter.authenticate_user(
            email=request.email,
            password=request.password
        )
        
        if not auth_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        return auth_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@app.get("/auth/user")
async def get_auth_user(request: Request):
    """
    Get current user data from auth token.
    
    Args:
        request: Request object containing authorization header
        
    Returns:
        Dict containing user data
    """
    try:
        # Get authorization header
        authorization = request.headers.get("Authorization")
        
        # Validate token
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header"
            )
            
        token = authorization.split(" ")[1]
        
        # Use auth adapter for token validation
        user_data = auth_adapter.validate_token(token)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/health")
async def health_check():
    """
    Health check endpoint using the new core system.
    
    Returns:
        Dict containing system health status
    """
    try:
        from core import get_system_manager
        system = await get_system_manager()
        health_status = await system.health_check()
        
        return {
            "status": health_status["status"],
            "timestamp": datetime.utcnow().isoformat(),
            "services": health_status.get("services", {}),
            "version": "3.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "version": "3.0.0"
        }

@app.get("/debug/rag-similarity/{user_id}")
async def debug_rag_similarity(
    user_id: str,
    query: str = "What is my deductible?",
    threshold: float = 0.4,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Debug endpoint to analyze RAG similarity scores with histogram.
    
    This endpoint helps understand why RAG retrieval might be returning 0 chunks
    by showing the distribution of similarity scores.
    """
    try:
        from utils.import_utilities import (
            safe_import_rag_tool,
            safe_import_retrieval_config
        )
        from utils.similarity_histogram import get_similarity_statistics
        
        RAGTool = safe_import_rag_tool()
        RetrievalConfig = safe_import_retrieval_config()
        
        if not RAGTool or not RetrievalConfig:
            raise HTTPException(
                status_code=500,
                detail="RAG tool not available"
            )
        
        # Initialize RAG tool with lower threshold for debugging
        config = RetrievalConfig(similarity_threshold=0.0, max_chunks=50)
        rag_tool = RAGTool(user_id, config)
        
        # Retrieve chunks with no threshold filtering
        chunks = await rag_tool.retrieve_chunks_from_text(query)
        
        # Extract similarity scores
        similarities = [chunk.similarity for chunk in chunks if chunk.similarity is not None]
        
        # Generate histogram data
        histogram_data = get_similarity_statistics(similarities, threshold)
        
        # Filter chunks by threshold
        filtered_chunks = [
            chunk for chunk in chunks 
            if chunk.similarity and chunk.similarity >= threshold
        ]
        
        # Prepare response
        response = {
            "query": query,
            "user_id": user_id,
            "threshold": threshold,
            "total_chunks": len(chunks),
            "filtered_chunks": len(filtered_chunks),
            "similarity_statistics": histogram_data["statistics"],
            "histogram_buckets": [
                {
                    "range": f"[{bucket.min_similarity:.3f}-{bucket.max_similarity:.3f}]",
                    "count": bucket.count,
                    "percentage": bucket.percentage
                }
                for bucket in histogram_data["buckets"]
            ],
            "above_threshold": histogram_data["above_threshold"],
            "below_threshold": histogram_data["below_threshold"],
            "threshold_percentage": histogram_data["threshold_percentage"],
            "chunk_details": [
                {
                    "chunk_id": str(chunk.id)[:8],
                    "similarity": chunk.similarity,
                    "content_preview": chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content,
                    "above_threshold": chunk.similarity >= threshold if chunk.similarity else False
                }
                for chunk in chunks[:10]  # Limit to first 10 chunks for response size
            ]
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Debug RAG similarity error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Debug analysis failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
