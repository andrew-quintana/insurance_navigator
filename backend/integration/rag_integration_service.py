"""
RAG Integration Service

This service validates that upload pipeline vectors are ready for agent RAG queries.
It provides integration health monitoring and troubleshooting capabilities.
"""

import asyncio
import logging
import time
import os
from typing import List, Optional
import asyncpg
import numpy as np

from .models import DocumentRAGStatus, RAGQueryTestResult
from .health_monitor import IntegrationHealthMonitor


class UploadRAGIntegration:
    """Validates upload pipeline vectors are ready for agent RAG queries."""
    
    def __init__(self, db_config: dict):
        """
        Initialize the RAG integration service.
        
        Args:
            db_config: Database configuration dictionary with connection details
        """
        self.db_config = db_config
        self.logger = logging.getLogger("rag_integration")
        self.health_monitor = IntegrationHealthMonitor()
        self._connection_pool = None
        self._pool_lock = asyncio.Lock()
        
    async def validate_documents_rag_ready(self, user_id: str) -> List[DocumentRAGStatus]:
        """
        Verify completed documents have vectors ready for semantic search.
        
        Args:
            user_id: User identifier to check documents for
            
        Returns:
            List of DocumentRAGStatus objects for each document
        """
        conn = None
        try:
            self.logger.info(f"Starting validate_documents_rag_ready for user: {user_id}")
            conn = await self._get_db_conn()
            self.logger.info("Database connection established successfully")
            
            # Query for completed jobs with corresponding vectors
            result = await conn.fetch("""
                SELECT 
                    d.document_id,
                    d.filename,
                    d.user_id,
                    uj.status,
                    uj.processing_completed_at,
                    COUNT(dc.chunk_id) as chunk_count,
                    AVG(vector_norm(dc.embedding_vector)) as avg_vector_norm
                FROM upload_pipeline.documents d
                JOIN upload_pipeline.upload_jobs uj ON d.document_id = uj.document_id
                LEFT JOIN upload_pipeline.document_chunks dc ON d.document_id = dc.document_id
                WHERE uj.status = 'complete' AND d.user_id = $1
                GROUP BY d.document_id, d.filename, d.user_id, uj.status, uj.processing_completed_at
                HAVING COUNT(dc.chunk_id) > 0
            """, user_id)
            
            documents = []
            for row in result:
                doc_status = DocumentRAGStatus(
                    document_id=str(row['document_id']),
                    filename=row['filename'],
                    user_id=str(row['user_id']),
                    is_rag_ready=row['chunk_count'] > 0 and row['avg_vector_norm'] > 0,
                    chunk_count=row['chunk_count'],
                    vector_quality_score=float(row['avg_vector_norm']) if row['avg_vector_norm'] else 0.0,
                    last_updated=row['processing_completed_at'],
                    processing_status=row['status']
                )
                documents.append(doc_status)
                
            self.logger.info(f"Found {len(documents)} RAG-ready documents for user {user_id}")
            return documents
            
        except Exception as e:
            self.logger.error(f"Error validating documents RAG ready: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            if conn:
                await self._release_db_conn(conn)
    
    async def test_sample_rag_query(self, document_id: str, user_id: str) -> RAGQueryTestResult:
        """
        Execute sample semantic search to validate RAG functionality.
        
        Args:
            document_id: Document to test RAG queries on
            user_id: User identifier for access control
            
        Returns:
            RAGQueryTestResult with query performance and quality metrics
        """
        start_time = time.time()
        
        try:
            conn = await self._get_db_conn()
            
            # Generate a test query vector (mock for now)
            test_query_vector = await self._generate_test_query_vector(document_id)
            
            # Execute similarity search on upload_pipeline.document_chunks
            result = await conn.fetch("""
                SELECT 
                    chunk_id,
                    chunk_text,
                    1 - (embedding_vector <=> $1) AS similarity
                FROM upload_pipeline.document_chunks 
                WHERE document_id = $2 AND user_id = $3
                ORDER BY embedding_vector <=> $1
                LIMIT 3
            """, test_query_vector, document_id, user_id)
            
            response_time = time.time() - start_time
            
            return RAGQueryTestResult(
                document_id=document_id,
                query_successful=len(result) > 0,
                top_similarity=result[0]['similarity'] if result else 0.0,
                chunks_found=len(result),
                response_time=response_time,
                query_vector=test_query_vector
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Error testing RAG query: {e}")
            
            return RAGQueryTestResult(
                document_id=document_id,
                query_successful=False,
                top_similarity=0.0,
                chunks_found=0,
                response_time=response_time,
                error_message=str(e)
            )
        finally:
            if 'conn' in locals():
                await conn.close()
    
    async def _generate_test_query_vector(self, document_id: str) -> List[float]:
        """
        Generate a test query vector for RAG testing.
        
        Args:
            document_id: Document ID to generate vector for
            
        Returns:
            List of floats representing the query embedding vector
        """
        # For mock testing, generate deterministic vector based on document_id
        # In production, this would use actual embedding generation
        seed = hash(document_id) % (2**32)
        np.random.seed(seed)
        return np.random.normal(0, 1, 1536).tolist()
    
    async def _ensure_connection_pool(self):
        """Ensure connection pool is initialized."""
        async with self._pool_lock:
            if self._connection_pool is None:
                try:
                    if 'DATABASE_URL' in os.environ:
                        database_url = os.environ['DATABASE_URL']
                        self._connection_pool = await asyncpg.create_pool(
                            database_url,
                            min_size=1,
                            max_size=5,
                            command_timeout=60
                        )
                    else:
                        self._connection_pool = await asyncpg.create_pool(
                            host=self.db_config.get('host', '127.0.0.1'),
                            port=self.db_config.get('port', 5432),
                            user=self.db_config.get('user', 'postgres'),
                            password=self.db_config.get('password', 'postgres'),
                            database=self.db_config.get('database', 'accessa_dev'),
                            min_size=1,
                            max_size=5,
                            command_timeout=60
                        )
                    self.logger.info("Database connection pool initialized successfully")
                except Exception as e:
                    self.logger.error(f"Failed to create connection pool: {e}")
                    raise

    async def _get_db_conn(self) -> asyncpg.Connection:
        """
        Get database connection using direct connection (bypassing pool for debugging).
        
        Returns:
            asyncpg.Connection object
        """
        database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@postgres:5432/accessa_dev')
        self.logger.info(f"Attempting direct connection to: {database_url}")
        
        return await asyncpg.connect(database_url)
    
    async def _release_db_conn(self, conn: asyncpg.Connection):
        """Release connection (close for direct connections)."""
        if conn:
            await conn.close()
    
    async def check_document_availability(self, user_id: str) -> dict:
        """
        Check for presence of specific document types for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary mapping document_type to availability boolean
        """
        conn = None
        try:
            conn = await self._get_db_conn()
            
            result = await conn.fetch("""
                SELECT DISTINCT document_type, COUNT(*) as doc_count
                FROM upload_pipeline.documents 
                WHERE user_id = $1 
                  AND document_id IN (
                    SELECT document_id FROM upload_pipeline.upload_jobs 
                    WHERE status = 'complete'
                  )
                GROUP BY document_type
            """, user_id)
            
            availability = {}
            for row in result:
                availability[row['document_type']] = row['doc_count'] > 0
                
            return availability
            
        except Exception as e:
            self.logger.error(f"Error checking document availability: {e}")
            return {}
        finally:
            if conn:
                await self._release_db_conn(conn)
    
    async def get_integration_health(self) -> dict:
        """
        Get overall integration health status.
        
        Returns:
            Dictionary with integration health information
        """
        try:
            # Check database connectivity
            conn = await self._get_db_conn()
            await conn.execute("SELECT 1")
            db_healthy = True
            await conn.close()
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            db_healthy = False
        
        # Check upload pipeline schema
        try:
            conn = await self._get_db_conn()
            result = await conn.fetch("""
                SELECT COUNT(*) as table_count
                FROM information_schema.tables 
                WHERE table_schema = 'upload_pipeline'
            """)
            schema_healthy = result[0]['table_count'] > 0
            await conn.close()
        except Exception as e:
            self.logger.error(f"Schema health check failed: {e}")
            schema_healthy = False
        
        return {
            'database_healthy': db_healthy,
            'schema_healthy': schema_healthy,
            'overall_healthy': db_healthy and schema_healthy,
            'timestamp': time.time()
        }
