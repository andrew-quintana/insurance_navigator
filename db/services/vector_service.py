import logging
import asyncio
from typing import Dict, List, Optional, Any
import aiohttp
import backoff
import json
import uuid
from db.services.encryption_service import EncryptionServiceFactory
from db.services.db_pool import get_db_pool

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.encryption_service = EncryptionServiceFactory.create_service()

    async def store_document_vectors(
        self,
        document_id: str,
        user_id: str,
        chunks: List[Dict[str, Any]],
        encryption_key_id: Optional[str] = None
    ) -> bool:
        """Store document vectors with optional encryption."""
        try:
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                async with conn.transaction():
                    for idx, chunk in enumerate(chunks):
                        # Encrypt chunk text if encryption key provided
                        encrypted_text = None
                        encrypted_metadata = None
                        if encryption_key_id:
                            encrypted_text = await self.encryption_service.encrypt_text(
                                chunk['text'], encryption_key_id
                            )
                            encrypted_metadata = await self.encryption_service.encrypt_text(
                                json.dumps(chunk.get('metadata', {})), encryption_key_id
                            )

                        await conn.execute("""
                            INSERT INTO document_vectors (
                                document_record_id, user_id, chunk_index,
                                content_embedding, encrypted_chunk_text,
                                encrypted_chunk_metadata, encryption_key_id
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                        uuid.UUID(document_id), uuid.UUID(user_id), idx,
                        chunk['embedding'], encrypted_text, encrypted_metadata,
                        uuid.UUID(encryption_key_id) if encryption_key_id else None
                        )
                    
                    return True
        except Exception as e:
            self.logger.error(f"Failed to store document vectors: {e}")
            return False

    async def search_similar_chunks(
        self,
        query_embedding: List[float],
        user_id: Optional[str] = None,
        document_type: Optional[str] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar document chunks."""
        try:
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                where_clauses = ["dv.is_active = true"]
                params = [query_embedding]
                param_idx = 2  # Start from $2 since $1 is query_embedding

                if user_id:
                    where_clauses.append(f"d.user_id = ${param_idx}")
                    params.append(uuid.UUID(user_id))
                    param_idx += 1

                if document_type:
                    where_clauses.append(f"d.document_type = ${param_idx}")
                    params.append(document_type)
                    param_idx += 1

                where_clause = " AND ".join(where_clauses)

                results = await conn.fetch(f"""
                    SELECT 
                        d.id as document_id,
                        d.original_filename,
                        d.document_type,
                        d.metadata,
                        dv.encrypted_chunk_text,
                        dv.encrypted_chunk_metadata,
                        dv.encryption_key_id,
                        1 - (dv.content_embedding <=> $1) as similarity
                    FROM document_vectors dv
                    JOIN documents d ON d.id = dv.document_record_id
                    WHERE {where_clause}
                    AND 1 - (dv.content_embedding <=> $1) >= {similarity_threshold}
                    ORDER BY dv.content_embedding <=> $1
                    LIMIT {limit}
                """, *params)

                chunks = []
                for row in results:
                    chunk_text = row['encrypted_chunk_text']
                    chunk_metadata = row['encrypted_chunk_metadata']
                    
                    if row['encryption_key_id']:
                        chunk_text = await self.encryption_service.decrypt_text(
                            chunk_text, str(row['encryption_key_id'])
                        )
                        chunk_metadata = json.loads(await self.encryption_service.decrypt_text(
                            chunk_metadata, str(row['encryption_key_id'])
                        ))

                    chunks.append({
                        'document_id': str(row['document_id']),
                        'filename': row['original_filename'],
                        'document_type': row['document_type'],
                        'metadata': row['metadata'],
                        'chunk_text': chunk_text,
                        'chunk_metadata': chunk_metadata,
                        'similarity': row['similarity']
                    })

                return chunks
        except Exception as e:
            self.logger.error(f"Failed to search similar chunks: {e}")
            return []

    async def delete_document_vectors(self, document_id: str) -> bool:
        """Delete all vectors for a document."""
        try:
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                result = await conn.execute("""
                    DELETE FROM document_vectors
                    WHERE document_record_id = $1
                """, uuid.UUID(document_id))
                return "DELETE" in result
        except Exception as e:
            self.logger.error(f"Failed to delete document vectors: {e}")
            return False

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
        return self.session
        
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=5,
        max_time=30
    )
    async def generate_embeddings(
        self,
        texts: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for a batch of texts using OpenAI API.
        """
        try:
            # Wait for rate limit slot
            await self._wait_for_rate_limit()
            
            session = await self.get_session()
            
            self.active_requests += 1
            self.last_request_time = asyncio.get_event_loop().time()
            
            async with session.post(
                "https://api.openai.com/v1/embeddings",
                json={
                    "input": texts,
                    "model": "text-embedding-3-small"
                },
                timeout=30
            ) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', '5'))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    raise aiohttp.ClientError("Rate limited")
                    
                response.raise_for_status()
                result = await response.json()
                
                embeddings = []
                for i, embedding_data in enumerate(result.get("data", [])):
                    embeddings.append({
                        "text": texts[i],
                        "embedding": embedding_data.get("embedding", []),
                        "metadata": metadata or {}
                    })
                    
                return embeddings
                
        except Exception as e:
            logger.error(f"OpenAI embeddings error: {str(e)}")
            return []
            
        finally:
            self.active_requests -= 1
            
    async def store_embeddings(
        self,
        document_id: str,
        embeddings: List[Dict[str, Any]],
        user_id: str
    ) -> List[str]:
        """
        Store embeddings in the database.
        """
        stored_ids = []
        
        try:
            async with self.pool.get_connection() as conn:
                for embedding_data in embeddings:
                    # Generate unique ID for this vector
                    vector_id = await conn.fetchval("""
                        INSERT INTO document_vectors (
                            document_id, user_id, chunk_text,
                            chunk_embedding, chunk_metadata,
                            created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                        RETURNING id
                    """,
                    document_id,
                    user_id,
                    embedding_data["text"],
                    embedding_data["embedding"],
                    json.dumps(embedding_data["metadata"])
                    )
                    
                    stored_ids.append(str(vector_id))
                    
            return stored_ids
            
        except Exception as e:
            logger.error(f"Error storing embeddings: {str(e)}")
            return []
            
    async def _wait_for_rate_limit(self):
        """Wait if we're at the rate limit."""
        while self.active_requests >= self.max_concurrent_requests:
            await asyncio.sleep(0.1)
            
        # Ensure minimum interval between requests
        time_since_last = asyncio.get_event_loop().time() - self.last_request_time
        if time_since_last < self.request_interval:
            await asyncio.sleep(self.request_interval - time_since_last) 