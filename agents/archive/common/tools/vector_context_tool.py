from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from agents.common.vector_retrieval_tool import VectorRetrievalTool, VectorFilter, VectorResult
import numpy as np

@dataclass
class VectorContext:
    """A vector with its metadata for context"""
    embedding: List[float]
    document_id: str
    document_source_type: str
    vector_id: str
    chunk_index: int
    metadata: Dict[str, Any]

    def compute_similarity(self, other_embedding: List[float]) -> float:
        """Compute cosine similarity with another embedding"""
        # Convert embeddings to numpy arrays
        vec1 = np.array(self.embedding)
        vec2 = np.array(other_embedding)
        
        # Compute cosine similarity
        similarity = np.dot(vec1, vec2) / (
            np.linalg.norm(vec1) * np.linalg.norm(vec2)
        )
        return float(similarity)

class VectorContextTool:
    """Tool for retrieving vector embeddings and metadata"""
    
    def __init__(self):
        self.vector_tool = VectorRetrievalTool(force_supabase=True)

    async def get_user_vectors(
        self,
        user_id: str,
        document_ids: Optional[List[str]] = None,
        max_vectors: int = 50
    ) -> List[VectorContext]:
        """Get vector embeddings and metadata for a user's documents"""
        try:
            # Get vectors with filtering
            filter_params = VectorFilter(
                user_id=user_id,
                document_ids=document_ids,
                is_active=True,
                limit=max_vectors
            )
            
            vectors = await self.vector_tool.get_vectors_by_filter(filter_params)
            print(f"✓ Retrieved {len(vectors)} vectors for user {user_id}")
            
            # Convert vectors to context objects
            contexts = []
            for vector in vectors:
                if vector.content_embedding:  # Only include vectors with embeddings
                    context = VectorContext(
                        embedding=vector.content_embedding,
                        document_id=vector.document_id,
                        document_source_type=vector.document_source_type,
                        vector_id=vector.id,
                        chunk_index=vector.chunk_index,
                        metadata={
                            'created_at': vector.created_at,
                            'embedding_model': vector.embedding_model,
                            'content_hash': vector.content_hash
                        }
                    )
                    contexts.append(context)
            
            print(f"✓ Processed {len(contexts)} vectors with valid embeddings")
            return contexts
            
        except Exception as e:
            print(f"❌ Error retrieving vectors: {str(e)}")
            raise

    async def find_similar_vectors(
        self,
        user_id: str,
        query_embedding: List[float],
        similarity_threshold: float = 0.7,
        max_results: int = 5,
        document_ids: Optional[List[str]] = None
    ) -> List[tuple[VectorContext, float]]:
        """Find vectors similar to the query embedding"""
        try:
            # Get user vectors
            vectors = await self.get_user_vectors(
                user_id=user_id,
                document_ids=document_ids
            )
            
            # Compute similarities
            results = []
            for vector in vectors:
                similarity = vector.compute_similarity(query_embedding)
                if similarity >= similarity_threshold:
                    results.append((vector, similarity))
            
            # Sort by similarity and return top results
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:max_results]
            
        except Exception as e:
            print(f"❌ Error finding similar vectors: {str(e)}")
            raise 