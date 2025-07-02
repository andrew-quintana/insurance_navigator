"""
Embedding service for vector operations.
"""

from typing import List, Optional, Dict, Any
import numpy as np
from langchain_openai import OpenAIEmbeddings

class EmbeddingService:
    """Service for managing embeddings."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize embedding service.
        
        Args:
            api_key: Optional API key
        """
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key,
        )
    
    async def get_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Get embeddings for texts.
        
        Args:
            texts: List of texts
            
        Returns:
            List of embeddings
        """
        embeddings = await self.embeddings.aembed_documents(texts)
        return [np.array(embedding) for embedding in embeddings]
    
    async def get_query_embedding(self, query: str) -> np.ndarray:
        """
        Get embedding for query.
        
        Args:
            query: Query text
            
        Returns:
            Query embedding
        """
        embedding = await self.embeddings.aembed_query(query)
        return np.array(embedding)
    
    async def compute_similarity(
        self,
        query_embedding: np.ndarray,
        document_embeddings: List[np.ndarray],
    ) -> List[float]:
        """
        Compute cosine similarity between query and documents.
        
        Args:
            query_embedding: Query embedding
            document_embeddings: List of document embeddings
            
        Returns:
            List of similarity scores
        """
        # Normalize embeddings
        query_norm = np.linalg.norm(query_embedding)
        doc_norms = [np.linalg.norm(doc) for doc in document_embeddings]
        
        # Compute cosine similarity
        similarities = []
        for doc_embedding, doc_norm in zip(document_embeddings, doc_norms):
            if query_norm == 0 or doc_norm == 0:
                similarities.append(0.0)
            else:
                similarity = np.dot(query_embedding, doc_embedding) / (query_norm * doc_norm)
                similarities.append(float(similarity))
        
        return similarities 