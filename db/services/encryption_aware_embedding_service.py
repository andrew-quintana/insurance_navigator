"""
Encryption-aware embedding service for generating and managing document vectors.
Handles text chunking, embedding generation, vector storage, and encryption.
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
from sentence_transformers import SentenceTransformer  # TEMPORARY - will be removed
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Database imports
import asyncpg
from .db_pool import get_db_pool
from .encryption_manager import EncryptionKeyManager

logger = logging.getLogger(__name__)

class EncryptionAwareEmbeddingService:
    """Enhanced embedding service with encryption support and proper access control."""
    
    def __init__(self):
        # Initialize embedding model (sentence-transformers for local processing)
        self.embedding_model = None  # Will be loaded lazily
        self.embedding_dimension = 384  # Dimension for all-MiniLM-L6-v2
        
        # Initialize encryption manager
        self.encryption_manager = None  # Will be initialized lazily
        
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
    
    async def _get_encryption_manager(self):
        """Lazy load the encryption manager."""
        if self.encryption_manager is None:
            # This would be properly initialized with the database session
            # For now, we'll create a mock implementation
            self.encryption_manager = MockEncryptionManager()
        return self.encryption_manager
        
    async def process_policy_document(
        self,
        policy_id: str,
        content_text: str,
        policy_metadata: Dict[str, Any],
        document_metadata: Dict[str, Any],
        encrypt_content: bool = True
    ) -> str:
        """
        Process a policy document with encryption support.
        
        Args:
            policy_id: UUID of the policy
            content_text: Full text content of the policy
            policy_metadata: Structured policy information
            document_metadata: Document-specific metadata
            encrypt_content: Whether to encrypt sensitive content
            
        Returns:
            UUID of the created vector record
        """
        try:
            # Generate embedding from plaintext (embeddings are not encrypted for search performance)
            embedding = await self._generate_embedding(content_text)
            embedding = await self._normalize_embedding_dimension(embedding)
            
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                if encrypt_content:
                    # Encrypt sensitive content
                    encryption_manager = await self._get_encryption_manager()
                    active_key = await encryption_manager.get_active_key()
                    
                    encrypted_content = await encryption_manager.encrypt_data(content_text.encode())
                    encrypted_policy_metadata = await encryption_manager.encrypt_data(
                        json.dumps(policy_metadata).encode()
                    )
                    encrypted_doc_metadata = await encryption_manager.encrypt_data(
                        json.dumps(document_metadata).encode()
                    )
                    
                    # Store encrypted version
                    record_id = await conn.fetchval("""
                        INSERT INTO policy_content_vectors 
                        (policy_id, content_embedding, encrypted_content_text, 
                         encrypted_policy_metadata, encrypted_document_metadata, encryption_key_id)
                        VALUES ($1, $2::vector, $3, $4, $5, $6)
                        RETURNING id
                    """, 
                    policy_id, str(embedding), encrypted_content, 
                    encrypted_policy_metadata, encrypted_doc_metadata, active_key['id'])
                else:
                    # Store plaintext version (for development/testing)
                    record_id = await conn.fetchval("""
                        INSERT INTO policy_content_vectors 
                        (policy_id, content_embedding, content_text, policy_metadata, document_metadata)
                        VALUES ($1, $2::vector, $3, $4, $5)
                        RETURNING id
                    """, 
                    policy_id, str(embedding), content_text,
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
        document_metadata: Dict[str, Any],
        encrypt_content: bool = True
    ) -> List[str]:
        """
        Process a user document with encryption support.
        
        Args:
            user_id: UUID of the user
            document_id: UUID of the document
            content_text: Full text content
            document_metadata: Document metadata
            encrypt_content: Whether to encrypt sensitive content
            
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
            
            encryption_manager = None
            active_key = None
            if encrypt_content:
                encryption_manager = await self._get_encryption_manager()
                active_key = await encryption_manager.get_active_key()
            
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
                    
                    if encrypt_content:
                        # Encrypt chunk content and metadata
                        encrypted_chunk_text = await encryption_manager.encrypt_data(
                            chunk.page_content.encode()
                        )
                        encrypted_chunk_metadata = await encryption_manager.encrypt_data(
                            json.dumps(chunk_metadata).encode()
                        )
                        
                        record_id = await conn.fetchval("""
                            INSERT INTO user_document_vectors 
                            (user_id, document_id, chunk_index, content_embedding, 
                             encrypted_chunk_text, encrypted_chunk_metadata, encryption_key_id)
                            VALUES ($1, $2, $3, $4::vector, $5, $6, $7)
                            RETURNING id
                        """,
                        user_id, document_id, i, str(embedding), 
                        encrypted_chunk_text, encrypted_chunk_metadata, active_key['id'])
                    else:
                        # Store plaintext version
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
        Search policy content using semantic similarity with automatic decryption.
        Uses RLS policies based on user_policy_links for proper access control.
        
        Args:
            query: Search query
            user_id: User ID for filtering (used by RLS policies)
            policy_filters: Additional filters for policy_metadata
            limit: Maximum number of results
            
        Returns:
            List of matching policy content with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            query_embedding = await self._normalize_embedding_dimension(query_embedding)
            
            # Build SQL query - RLS policies will automatically filter by user access via user_policy_links
            where_conditions = ["is_active = true"]
            params = [str(query_embedding)]
            param_count = 1
            
            if policy_filters:
                for key, value in policy_filters.items():
                    param_count += 1
                    # Handle both encrypted and plaintext metadata
                    where_conditions.append(f"""
                        (policy_metadata->>'{key}' = ${param_count} OR 
                         encrypted_policy_metadata IS NOT NULL)
                    """)
                    params.append(str(value))
            
            sql = f"""
                SELECT id, policy_id, content_embedding <=> $1::vector as similarity_score,
                       content_text, encrypted_content_text, 
                       policy_metadata, encrypted_policy_metadata,
                       document_metadata, encrypted_document_metadata,
                       encryption_key_id
                FROM policy_content_vectors
                WHERE {' AND '.join(where_conditions)}
                ORDER BY content_embedding <=> $1::vector
                LIMIT {limit}
            """
            
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                # Set the user context for RLS
                await conn.execute("SELECT set_config('app.current_user_id', $1, true)", user_id)
                
                rows = await conn.fetch(sql, *params)
                
                results = []
                encryption_manager = None
                
                for row in rows:
                    # Decrypt content if encrypted
                    if row['encrypted_content_text']:
                        if not encryption_manager:
                            encryption_manager = await self._get_encryption_manager()
                        
                        content_text = await encryption_manager.decrypt_data(
                            row['encrypted_content_text'], row['encryption_key_id']
                        )
                        content_text = content_text.decode()
                        
                        policy_metadata = await encryption_manager.decrypt_data(
                            row['encrypted_policy_metadata'], row['encryption_key_id']
                        )
                        policy_metadata = json.loads(policy_metadata.decode())
                        
                        document_metadata = await encryption_manager.decrypt_data(
                            row['encrypted_document_metadata'], row['encryption_key_id']
                        )
                        document_metadata = json.loads(document_metadata.decode())
                    else:
                        # Use plaintext content
                        content_text = row['content_text']
                        policy_metadata = json.loads(row['policy_metadata']) if row['policy_metadata'] else {}
                        document_metadata = json.loads(row['document_metadata']) if row['document_metadata'] else {}
                    
                    results.append({
                        'id': str(row['id']),
                        'policy_id': str(row['policy_id']),
                        'content_text': content_text,
                        'policy_metadata': policy_metadata,
                        'document_metadata': document_metadata,
                        'similarity_score': float(row['similarity_score'])
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Error searching policy content: {str(e)}")
            raise
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not text.strip():
            return [0.0] * self.embedding_dimension
            
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
            
        non_empty_texts = [text if text.strip() else " " for text in texts]
        
        model = await self._get_embedding_model()
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: model.encode(non_empty_texts).tolist()
        )
        return embeddings
    
    async def _normalize_embedding_dimension(self, embedding: List[float]) -> List[float]:
        """Normalize embedding dimension to match database schema."""
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

    async def process_chunk(self, chunk_text: str) -> Dict[str, Any]:
        """Process a single chunk of text into vector with encryption."""
        try:
            # Generate embedding
            embedding = await self._generate_embedding(chunk_text)
            embedding = await self._normalize_embedding_dimension(embedding)
            
            # Get encryption manager
            encryption_manager = await self._get_encryption_manager()
            active_key = await encryption_manager.get_active_key()
            
            # Encrypt chunk text
            encrypted_text = await encryption_manager.encrypt_data(chunk_text.encode())
            
            # Encrypt metadata
            metadata = {
                "chunk_size": len(chunk_text),
                "processed_at": datetime.utcnow().isoformat()
            }
            encrypted_metadata = await encryption_manager.encrypt_data(json.dumps(metadata).encode())
            
            return {
                "embedding": embedding,
                "encrypted_text": encrypted_text,
                "encrypted_metadata": encrypted_metadata,
                "key_id": active_key["id"]
            }
            
        except Exception as e:
            logger.error(f"Error processing chunk: {str(e)}")
            raise


class MockEncryptionManager:
    """Mock encryption manager for development/testing."""
    
    async def get_active_key(self):
        """Get mock active encryption key."""
        return {
            'id': '6b892ba1-091b-468c-98a8-692fdb384588',  # Real UUID from database
            'key_version': 1,
            'key_status': 'active'
        }
    
    async def encrypt_data(self, data: bytes) -> str:
        """Mock encryption - just base64 encode."""
        import base64
        return base64.b64encode(data).decode()
    
    async def decrypt_data(self, encrypted_data: str, key_id: str) -> bytes:
        """Mock decryption - just base64 decode."""
        import base64
        return base64.b64decode(encrypted_data.encode())


# Global service instance
_encryption_aware_embedding_service = None

async def get_encryption_aware_embedding_service() -> EncryptionAwareEmbeddingService:
    """Get or create the global encryption-aware embedding service instance."""
    global _encryption_aware_embedding_service
    if _encryption_aware_embedding_service is None:
        _encryption_aware_embedding_service = EncryptionAwareEmbeddingService()
    return _encryption_aware_embedding_service 