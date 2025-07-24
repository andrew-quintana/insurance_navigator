"""
Vector Retrieval Tool for accessing document vectors from the database.

This tool provides structured access to vectorized document chunks stored in the
document_vectors table, allowing agents to retrieve and process vector data
based on various filtering criteria.
"""

import logging
import os
import asyncio
import asyncpg
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field
from langchain_openai import OpenAIEmbeddings
import numpy as np

from db.services.db_pool import get_db_pool

logger = logging.getLogger(__name__)

@dataclass
class VectorFilter:
    """Filter criteria for vector retrieval."""
    user_id: Optional[Union[str, UUID]] = None
    document_id: Optional[Union[str, UUID]] = None
    document_record_id: Optional[Union[str, UUID]] = None
    regulatory_document_id: Optional[Union[str, UUID]] = None
    document_source_type: Optional[str] = None
    is_active: bool = True
    limit: int = 1000

@dataclass
class VectorResult:
    """Result object containing vector data and metadata."""
    id: Union[str, UUID]
    chunk_text: str
    chunk_metadata: Dict[str, Any]
    content_embedding: List[float]
    chunk_index: int
    document_source_type: str
    user_id: Optional[Union[str, UUID]]
    document_record_id: Optional[Union[str, UUID]]
    regulatory_document_id: Optional[Union[str, UUID]]
    encryption_key_id: Optional[Union[str, UUID]]

class VectorRetrievalTool:
    """Tool for retrieving document vectors from the database."""
    
    def __init__(self, force_supabase: bool = False, api_key: Optional[str] = None):
        """
        Initialize the vector retrieval tool.
        
        Args:
            force_supabase: If True, connect directly to Supabase instead of using local database
            api_key: API key for OpenAI embeddings
        """
        self.force_supabase = force_supabase
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key,
        )
        
    async def _get_connection(self):
        """Get database connection, either from pool or direct to Supabase."""
        if self.force_supabase:
            supabase_url = os.getenv('DATABASE_URL')
            if not supabase_url:
                raise ValueError("DATABASE_URL not set for Supabase connection")
            # Disable statement cache for Supabase/pgbouncer compatibility
            return await asyncpg.connect(supabase_url, statement_cache_size=0)
        else:
            pool = await get_db_pool()
            return await pool.acquire()
    
    async def _release_connection(self, conn, is_direct: bool = False):
        """Release database connection."""
        if is_direct or self.force_supabase:
            await conn.close()
        else:
            pool = await get_db_pool()
            await pool.release(conn)

    async def get_vectors_by_filter(self, filter_criteria: VectorFilter) -> List[VectorResult]:
        """
        Retrieve vectors based on filter criteria.
        
        Args:
            filter_criteria: Filter criteria for vector retrieval
            
        Returns:
            List of VectorResult objects matching the criteria
        """
        # Build query based on filter criteria
        conditions = ["is_active = $1"]
        params = [filter_criteria.is_active]
        param_index = 2
        
        # Add filter conditions
        if filter_criteria.user_id is not None:
            conditions.append(f"user_id = ${param_index}")
            params.append(UUID(str(filter_criteria.user_id)))
            param_index += 1
            
        if filter_criteria.document_id is not None:
            conditions.append(f"document_id = ${param_index}")
            params.append(UUID(str(filter_criteria.document_id)))
            param_index += 1
            
        if filter_criteria.document_record_id is not None:
            conditions.append(f"document_record_id = ${param_index}")
            params.append(UUID(str(filter_criteria.document_record_id)))
            param_index += 1
            
        if filter_criteria.regulatory_document_id is not None:
            conditions.append(f"regulatory_document_id = ${param_index}")
            params.append(UUID(str(filter_criteria.regulatory_document_id)))
            param_index += 1
            
        if filter_criteria.document_source_type is not None:
            conditions.append(f"document_source_type = ${param_index}")
            params.append(filter_criteria.document_source_type)
            param_index += 1
        
        # Add limit parameter
        params.append(filter_criteria.limit)
        
        query = f"""
                SELECT 
                    id,
                    encrypted_chunk_text,
                    encrypted_chunk_metadata,
                    content_embedding,
                    chunk_index,
                    document_source_type,
                    user_id,
                    document_record_id,
                    regulatory_document_id,
                    encryption_key_id
                FROM document_vectors
                WHERE {' AND '.join(conditions)}
                ORDER BY chunk_index ASC
                LIMIT ${param_index}
            """
        
        logger.info(f"Executing query: {query}")
        logger.info(f"With parameters: {params}")
        
        conn = None
        try:
            conn = await self._get_connection()
            rows = await conn.fetch(query, *params)
            
            results = []
            for row in rows:
                # Pass through encrypted data as-is for external decryption
                chunk_text = "[Encrypted content]" if row['encrypted_chunk_text'] else ""
                chunk_metadata = {"encrypted": True} if row['encrypted_chunk_metadata'] else {}
                
                result = VectorResult(
                    id=row['id'],
                    chunk_text=chunk_text,
                    chunk_metadata=chunk_metadata,
                    content_embedding=row['content_embedding'] or [],
                    chunk_index=row['chunk_index'],
                    document_source_type=row['document_source_type'],
                    user_id=row['user_id'],
                    document_record_id=row['document_record_id'],
                    regulatory_document_id=row['regulatory_document_id'],
                    encryption_key_id=row['encryption_key_id']
                )
                
                # Store raw encrypted data for external decryption
                result.encrypted_chunk_text = row['encrypted_chunk_text']
                result.encrypted_chunk_metadata = row['encrypted_chunk_metadata']
                
                results.append(result)
            
            logger.info(f"Retrieved {len(results)} vector results")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving vectors: {e}")
            raise
        finally:
            if conn:
                await self._release_connection(conn, self.force_supabase)

    async def get_vectors_by_document(
        self, 
        document_id: str, 
        user_id: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> List[VectorResult]:
        """
        Convenience method to get all vectors for a specific document.
        
        Args:
            document_id: Document ID to retrieve vectors for
            user_id: Optional user ID for additional filtering
            source_type: Optional source type ('user_document' or 'regulatory_document')
            
        Returns:
            List of VectorResult objects
        """
        filter_criteria = VectorFilter(
            user_id=user_id,
            document_source_type=source_type,
            limit=1000  # High limit for complete document
        )
        
        # Determine which document field to use based on source type
        if source_type == "regulatory_document":
            filter_criteria.regulatory_document_id = document_id
        else:
            filter_criteria.document_id = document_id
        
        return await self.get_vectors_by_filter(filter_criteria)
    
    def _parse_vector_string(self, vector_str: str) -> List[float]:
        """
        Parse vector string representation into list of floats.
        
        Args:
            vector_str: String representation of vector
            
        Returns:
            List of float values
        """
        try:
            # Remove any brackets and split by comma
            cleaned = vector_str.strip('[]() ')
            if not cleaned:
                return []
            
            # Split and convert to floats
            values = [float(x.strip()) for x in cleaned.split(',') if x.strip()]
            return values
            
        except Exception as e:
            logger.warning(f"Error parsing vector string '{vector_str}': {e}")
            return []
    
    def get_text_content(self, vectors: List[VectorResult]) -> str:
        """
        Extract and combine text content from vector results.
        
        Args:
            vectors: List of VectorResult objects
            
        Returns:
            Combined text content
        """
        if not vectors:
            return ""
        
        # Sort by chunk_index to maintain order
        sorted_vectors = sorted(vectors, key=lambda v: v.chunk_index)
        
        # Combine text content
        text_chunks = [v.chunk_text for v in sorted_vectors if v.chunk_text]
        return "\n\n".join(text_chunks)
    
    def get_metadata_summary(self, vectors: List[VectorResult]) -> Dict[str, Any]:
        """
        Get summary of metadata from vector results.
        
        Args:
            vectors: List of VectorResult objects
            
        Returns:
            Dictionary with metadata summary
        """
        if not vectors:
            return {}
        
        summary = {
            "total_chunks": len(vectors),
            "chunk_indices": [v.chunk_index for v in vectors],
            "document_source_types": list(set(v.document_source_type for v in vectors)),
            "embedding_dimensions": len(vectors[0].content_embedding) if vectors and vectors[0].content_embedding else 0,
            "encrypted_chunks": sum(1 for v in vectors if v.chunk_text == "[Encrypted content]"),
            "user_ids": list(set(str(v.user_id) for v in vectors if v.user_id)),
            "document_record_ids": list(set(str(v.document_record_id) for v in vectors if v.document_record_id)),
            "regulatory_document_ids": list(set(str(v.regulatory_document_id) for v in vectors if v.regulatory_document_id))
        }
        
        return summary

    async def get_document_vectors(self, documents: List[str]) -> List[np.ndarray]:
        """
        Get vector embeddings for documents.
        
        Args:
            documents: List of document texts
            
        Returns:
            List of vector embeddings
        """
        embeddings = await self.embeddings.aembed_documents(documents)
        return [np.array(embedding) for embedding in embeddings]
    
    async def get_document_text(self, document_id: str) -> str:
        """
        Get document text by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document text
        """
        # TODO: Implement document storage and retrieval
        raise NotImplementedError("Document storage not implemented")
    
    async def search(
        self,
        query: str,
        filters: Optional[VectorFilter] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for documents similar to query.
        
        Args:
            query: Search query
            filters: Search filters
            
        Returns:
            List of search results
        """
        if filters is None:
            filters = VectorFilter()
        
        query_vector = await self.embeddings.aembed_query(query)
        
        # TODO: Implement vector search
        raise NotImplementedError("Vector search not implemented")

# Convenience functions for agents
async def get_document_vectors(
    document_id: str, 
    user_id: Optional[str] = None,
    source_type: Optional[str] = None
) -> List[VectorResult]:
    """
    Get all vectors for a specific document.
    
    Args:
        document_id: Document ID
        user_id: Optional user ID for filtering
        source_type: Optional source type
        
    Returns:
        List of VectorResult objects
    """
    tool = VectorRetrievalTool()
    return await tool.get_vectors_by_document(document_id, user_id, source_type)

async def get_document_text(
    document_id: str, 
    user_id: Optional[str] = None,
    source_type: Optional[str] = None
) -> str:
    """
    Get combined text content for a document.
    
    Args:
        document_id: Document ID
        user_id: Optional user ID for filtering
        source_type: Optional source type
        
    Returns:
        Combined text content
    """
    tool = VectorRetrievalTool()
    vectors = await tool.get_vectors_by_document(document_id, user_id, source_type)
    return tool.get_text_content(vectors)
 