"""
Agent API Service for Integration Testing

This service provides API endpoints for testing the integration between
upload pipeline and agent workflows.
"""

import asyncio
import logging
import os
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .rag_integration_service import UploadRAGIntegration
from .health_monitor import IntegrationHealthMonitor
from .models import RAGQueryTestRequest, DocumentRAGStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Agent Integration API",
    description="API for testing upload pipeline + agent workflow integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instances
rag_integration: UploadRAGIntegration = None
health_monitor: IntegrationHealthMonitor = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global rag_integration, health_monitor
    
    # Get database configuration from environment
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@127.0.0.1:5432/accessa_dev')
    
    # Parse DATABASE_URL into individual components for backward compatibility
    from urllib.parse import urlparse
    parsed_url = urlparse(database_url)
    
    db_config = {
        'host': parsed_url.hostname or '127.0.0.1',
        'port': parsed_url.port or 5432,
        'user': parsed_url.username or 'postgres',
        'password': parsed_url.password or 'postgres',
        'database': parsed_url.path.lstrip('/') or 'accessa_dev'
    }
    
    # Initialize services
    logger.info(f"Initializing RAG integration with db_config: {db_config}")
    rag_integration = UploadRAGIntegration(db_config)
    health_monitor = IntegrationHealthMonitor()
    
    logger.info(f"Agent Integration API started successfully. RAG integration: {rag_integration}")
    logger.info(f"RAG integration type: {type(rag_integration)}")


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "agent_integration_api"
    }


@app.get("/integration/health")
async def get_integration_health():
    """Get comprehensive integration health status."""
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not initialized")
    
    try:
        health_status = await health_monitor.check_integration_health()
        return {
            "overall_status": health_status.overall_status.value,
            "upload_pipeline_status": {
                "status": health_status.upload_pipeline_status.status.value,
                "message": health_status.upload_pipeline_status.message,
                "response_time": health_status.upload_pipeline_status.response_time
            },
            "agent_system_status": {
                "status": health_status.agent_system_status.status.value,
                "message": health_status.agent_system_status.message,
                "response_time": health_status.agent_system_status.response_time
            },
            "database_status": {
                "status": health_status.database_status.status.value,
                "message": health_status.database_status.message,
                "response_time": health_status.database_status.response_time
            },
            "mock_services_status": {
                "status": health_status.mock_services_status.status.value,
                "message": health_status.mock_services_status.message,
                "response_time": health_status.mock_services_status.response_time
            },
            "performance_metrics": health_status.performance_metrics,
            "recommendations": health_status.recommendations,
            "last_check": health_status.last_check.isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting integration health: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/integration/documents/{user_id}/rag-ready")
async def check_documents_rag_ready(user_id: str):
    """Check which documents are ready for RAG queries for a specific user."""
    logger.info(f"RAG endpoint called for user: {user_id}")
    logger.info(f"RAG integration instance: {rag_integration}")
    
    if not rag_integration:
        logger.error("RAG integration service not initialized")
        raise HTTPException(status_code=503, detail="RAG integration service not initialized")
    
    try:
        logger.info("Calling rag_integration.validate_documents_rag_ready")
        documents = await rag_integration.validate_documents_rag_ready(user_id)
        logger.info(f"Received documents: {len(documents) if documents else 0}")
        return {
            "user_id": user_id,
            "documents": [
                {
                    "document_id": doc.document_id,
                    "filename": doc.filename,
                    "is_rag_ready": doc.is_rag_ready,
                    "chunk_count": doc.chunk_count,
                    "vector_quality_score": doc.vector_quality_score,
                    "last_updated": doc.last_updated.isoformat() if doc.last_updated else None,
                    "processing_status": doc.processing_status
                }
                for doc in documents
            ],
            "total_documents": len(documents),
            "rag_ready_count": len([d for d in documents if d.is_rag_ready])
        }
    except Exception as e:
        logger.error(f"Error checking documents RAG ready: {e}")
        raise HTTPException(status_code=500, detail=f"Document check failed: {str(e)}")


@app.post("/integration/test-rag-query")
async def test_rag_query(request: RAGQueryTestRequest):
    """Execute a test RAG query for integration validation."""
    if not rag_integration:
        raise HTTPException(status_code=503, detail="RAG integration service not initialized")
    
    try:
        result = await rag_integration.test_sample_rag_query(
            request.document_id,
            request.user_id
        )
        
        return {
            "document_id": result.document_id,
            "query_successful": result.query_successful,
            "top_similarity": result.top_similarity,
            "chunks_found": result.chunks_found,
            "response_time": result.response_time,
            "error_message": result.error_message,
            "test_query": request.test_query,
            "similarity_threshold": request.similarity_threshold,
            "max_chunks": request.max_chunks
        }
    except Exception as e:
        logger.error(f"Error testing RAG query: {e}")
        raise HTTPException(status_code=500, detail=f"RAG query test failed: {str(e)}")


@app.get("/integration/documents/{user_id}/availability")
async def check_document_availability(user_id: str):
    """Check document availability by type for a specific user."""
    if not rag_integration:
        raise HTTPException(status_code=503, detail="RAG integration service not initialized")
    
    try:
        availability = await rag_integration.check_document_availability(user_id)
        return {
            "user_id": user_id,
            "document_availability": availability,
            "total_document_types": len(availability),
            "available_document_types": [doc_type for doc_type, available in availability.items() if available]
        }
    except Exception as e:
        logger.error(f"Error checking document availability: {e}")
        raise HTTPException(status_code=500, detail=f"Document availability check failed: {str(e)}")


@app.get("/integration/overview")
async def get_integration_overview():
    """Get an overview of the integration system."""
    return {
        "service_name": "Agent Integration API",
        "version": "1.0.0",
        "description": "API for testing upload pipeline + agent workflow integration",
        "endpoints": {
            "health": "/health",
            "integration_health": "/integration/health",
            "documents_rag_ready": "/integration/documents/{user_id}/rag-ready",
            "test_rag_query": "/integration/test-rag-query",
            "document_availability": "/integration/documents/{user_id}/availability",
            "integration_overview": "/integration/overview"
        },
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Run the API server
    uvicorn.run(
        "backend.integration.agent_api:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
