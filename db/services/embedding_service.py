"""
Embedding service for generating and managing document vectors.
Handles text chunking, embedding generation, and vector storage.
"""

import asyncio
import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import os

# Vector and ML imports
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Database imports
import asyncpg
from .db_pool import get_db_pool

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings and managing vector storage."""
    
    def __init__(self):
        # Initialize embedding model (sentence-transformers for local processing)
        # Note: Using all-MiniLM-L6-v2 which produces 384 dimensions
        # For production, consider switching to 1536-dimension model or OpenAI embeddings
        self.embedding_model = None  # Will be loaded lazily
        self.embedding_dimension = 384  # Dimension for all-MiniLM-L6-v2
        
        # For 1536 dimensions (OpenAI compatible), uncomment below:
        # self.embedding_model_name = 'sentence-transformers/all-mpnet-base-v2'
        # self.embedding_dimension = 768
        
        # Or use OpenAI embeddings:
        # self.use_openai = os.getenv('USE_OPENAI_EMBEDDINGS', 'false').lower() == 'true'
        # self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    async def _get_embedding_model(self):
        """Lazy load the embedding model to avoid blocking startup."""
        if self.embedding_model is None:
            # Load in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.embedding_model = await loop.run_in_executor(
                None, 
                lambda: SentenceTransformer('all-MiniLM-L6-v2')
            )
            logger.info("Embedding model loaded successfully")
        return self.embedding_model
        
    async def process_policy_document(
        self,
        policy_id: str,
        user_id: str,
        content_text: str,
        policy_metadata: Dict[str, Any],
        document_metadata: Dict[str, Any]
    ) -> str:
        """
        Process a policy document: generate embedding and store in policy_content_vectors.
        
        Args:
            policy_id: UUID of the policy
            user_id: UUID of the user
            content_text: Full text content of the policy
            policy_metadata: Structured policy information
            document_metadata: Document-specific metadata
            
        Returns:
            UUID of the created vector record
        """
        try:
            # Generate embedding for the full content
            embedding = await self._generate_embedding(content_text)
            
            # Pad or truncate embedding to match expected dimension (1536 for migration schema)
            embedding = await self._normalize_embedding_dimension(embedding)
            
            # Store in database
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                record_id = await conn.fetchval("""
                    INSERT INTO policy_content_vectors 
                    (policy_id, user_id, content_embedding, content_text, 
                     policy_metadata, document_metadata)
                    VALUES ($1, $2, $3::vector, $4, $5, $6)
                    RETURNING id
                """, 
                policy_id, user_id, str(embedding), content_text,
                json.dumps(policy_metadata), json.dumps(document_metadata))
                
            logger.info(f"Stored policy vector for policy {policy_id}: {record_id}")
            return str(record_id)
            
        except Exception as e:
            logger.error(f"Error processing policy document: {str(e)}")
            raise
    
    async def process_user_document(
        self,
        user_id: str,
        document_id: str,
        content_text: str,
        document_metadata: Dict[str, Any]
    ) -> List[str]:
        """
        Process a user document: chunk, generate embeddings, and store vectors.
        
        Args:
            user_id: UUID of the user
            document_id: UUID of the document
            content_text: Full text content
            document_metadata: Document metadata
            
        Returns:
            List of UUIDs for created vector records
        """
        try:
            # Split document into chunks
            documents = [Document(page_content=content_text, metadata=document_metadata)]
            chunks = self.text_splitter.split_documents(documents)
            
            if not chunks:
                logger.warning(f"No chunks generated for document {document_id}")
                return []
            
            # Generate embeddings for all chunks
            chunk_texts = [chunk.page_content for chunk in chunks]
            embeddings = await self._generate_embeddings_batch(chunk_texts)
            
            # Store chunks and embeddings
            pool = await get_db_pool()
            record_ids = []
            
            async with pool.get_connection() as conn:
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    # Normalize embedding dimension
                    embedding = await self._normalize_embedding_dimension(embedding)
                    
                    chunk_metadata = {
                        **document_metadata,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "chunk_size": len(chunk.page_content)
                    }
                    
                    record_id = await conn.fetchval("""
                        INSERT INTO user_document_vectors 
                        (user_id, document_id, chunk_index, content_embedding, 
                         chunk_text, chunk_metadata)
                        VALUES ($1, $2, $3, $4::vector, $5, $6)
                        RETURNING id
                    """,
                    user_id, document_id, i, str(embedding), 
                    chunk.page_content, json.dumps(chunk_metadata))
                    
                    record_ids.append(str(record_id))
            
            logger.info(f"Stored {len(record_ids)} chunks for document {document_id}")
            return record_ids
            
        except Exception as e:
            logger.error(f"Error processing user document: {str(e)}")
            raise
    
    async def search_policy_content(
        self,
        query: str,
        user_id: str,
        policy_filters: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search policy content using semantic similarity.
        
        Args:
            query: Search query
            user_id: User ID for filtering
            policy_filters: Additional filters for policy_metadata
            limit: Maximum number of results
            
        Returns:
            List of matching policy content with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            query_embedding = await self._normalize_embedding_dimension(query_embedding)
            
            # Build SQL query with filters
            where_conditions = ["user_id = $2", "is_active = true"]
            params = [query_embedding, user_id]
            param_count = 2
            
            if policy_filters:
                for key, value in policy_filters.items():
                    param_count += 1
                    where_conditions.append(f"policy_metadata->>'{key}' = ${param_count}")
                    params.append(str(value))
            
            sql = f"""
                SELECT id, policy_id, content_text, policy_metadata, document_metadata,
                       content_embedding <=> $1::vector as similarity_score
                FROM policy_content_vectors
                WHERE {' AND '.join(where_conditions)}
                ORDER BY content_embedding <=> $1::vector
                LIMIT {limit}
            """
            
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                rows = await conn.fetch(sql, str(query_embedding), *params[1:])
                
                results = []
                for row in rows:
                    results.append({
                        'id': str(row['id']),
                        'policy_id': str(row['policy_id']),
                        'content_text': row['content_text'],
                        'policy_metadata': json.loads(row['policy_metadata']),
                        'document_metadata': json.loads(row['document_metadata']),
                        'similarity_score': float(row['similarity_score'])
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Error searching policy content: {str(e)}")
            raise
    
    async def search_user_documents(
        self,
        query: str,
        user_id: str,
        document_filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search user document chunks using semantic similarity.
        
        Args:
            query: Search query
            user_id: User ID for filtering
            document_filters: Additional filters for chunk_metadata
            limit: Maximum number of results
            
        Returns:
            List of matching document chunks with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            query_embedding = await self._normalize_embedding_dimension(query_embedding)
            
            # Build SQL query with filters
            where_conditions = ["user_id = $2", "is_active = true"]
            params = [query_embedding, user_id]
            param_count = 2
            
            if document_filters:
                for key, value in document_filters.items():
                    param_count += 1
                    where_conditions.append(f"chunk_metadata->>'{key}' = ${param_count}")
                    params.append(str(value))
            
            sql = f"""
                SELECT id, document_id, chunk_index, chunk_text, chunk_metadata,
                       content_embedding <=> $1::vector as similarity_score
                FROM user_document_vectors
                WHERE {' AND '.join(where_conditions)}
                ORDER BY content_embedding <=> $1::vector
                LIMIT {limit}
            """
            
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                rows = await conn.fetch(sql, str(query_embedding), *params[1:])
                
                results = []
                for row in rows:
                    results.append({
                        'id': str(row['id']),
                        'document_id': str(row['document_id']),
                        'chunk_index': row['chunk_index'],
                        'chunk_text': row['chunk_text'],
                        'chunk_metadata': json.loads(row['chunk_metadata']),
                        'similarity_score': float(row['similarity_score'])
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Error searching user documents: {str(e)}")
            raise
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.embedding_dimension
            
        # Run in thread pool to avoid blocking
        model = await self._get_embedding_model()
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, 
            lambda: model.encode(text).tolist()
        )
        return embedding
    
    async def _generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently."""
        if not texts:
            return []
            
        # Filter out empty texts
        non_empty_texts = [text if text.strip() else " " for text in texts]
        
        model = await self._get_embedding_model()
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: model.encode(non_empty_texts).tolist()
        )
        return embeddings
    
    async def _normalize_embedding_dimension(self, embedding: List[float]) -> List[float]:
        """
        Normalize embedding dimension to match database schema.
        
        The migration schema expects 1536 dimensions, but our model produces 384.
        This function pads or truncates as needed.
        """
        target_dimension = 1536  # From migration schema
        current_dimension = len(embedding)
        
        if current_dimension == target_dimension:
            return embedding
        elif current_dimension < target_dimension:
            # Pad with zeros
            padding = [0.0] * (target_dimension - current_dimension)
            return embedding + padding
        else:
            # Truncate
            return embedding[:target_dimension]
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector storage."""
        try:
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                policy_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM policy_content_vectors WHERE is_active = true"
                )
                user_doc_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM user_document_vectors WHERE is_active = true"
                )
                
                # Get sample embedding dimension - handle vector type properly
                sample_embedding = await conn.fetchval(
                    "SELECT vector_dims(content_embedding) FROM policy_content_vectors LIMIT 1"
                )
                
                # Fallback if no policy vectors exist
                if sample_embedding is None and user_doc_count > 0:
                    sample_embedding = await conn.fetchval(
                        "SELECT vector_dims(content_embedding) FROM user_document_vectors LIMIT 1"
                    )
                
                return {
                    "policy_vectors": policy_count,
                    "user_document_vectors": user_doc_count,
                    "total_vectors": policy_count + user_doc_count,
                    "embedding_dimension": sample_embedding or self.embedding_dimension,
                    "model_dimension": self.embedding_dimension
                }
        except Exception as e:
            logger.error(f"Error getting embedding stats: {str(e)}")
            return {
                "error": str(e),
                "model_dimension": self.embedding_dimension
            }

# Global service instance
_embedding_service = None

async def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service 