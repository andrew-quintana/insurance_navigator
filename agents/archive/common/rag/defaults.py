# RAG Default Implementations
import logging
from typing import List, Dict, Any
from datetime import datetime
from .interfaces import ContextRetriever, ContextItem
from ..vector_rag import get_vector_rag

logger = logging.getLogger(__name__)

class VectorStoreRetriever:
    async def retrieve_context(self, query: str, user_id: str) -> List[ContextItem]:
        try:
            vector_rag = await get_vector_rag()
            results = await vector_rag.get_combined_context(query, user_id, policy_limit=3, document_limit=5)
            items = []
            for doc in results.get("document_context", []):
                items.append(ContextItem(
                    content=doc.get("content", ""),
                    source_id=doc.get("document_name", "unknown"),
                    relevance_score=doc.get("relevance_score", 0.0)
                ))
            return items
        except Exception as e:
            logger.error(f"Vector retrieval error: {e}")
            return []

class StandardFormatter:
    def format_context(self, items: List[ContextItem]) -> str:
        if not items:
            return ""
        parts = []
        for i, item in enumerate(items, 1):
            parts.append(f"Document {i} ({item.relevance_score:.2f}): {item.content}")
        return "\n\n".join(parts)

class BeforeQueryEnhancer:
    def enhance_query(self, query: str, context: str) -> str:
        if not context:
            return query
        return f"RELEVANT CONTEXT:\n{context}\n\nUSER QUERY: {query}\n\nPlease use the context above to provide an informed response."

# Default instances
default_retriever = VectorStoreRetriever()
default_formatter = StandardFormatter()
default_enhancer = BeforeQueryEnhancer()
