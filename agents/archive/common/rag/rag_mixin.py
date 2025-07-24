# Modular RAG Mixin - Phase 6
import logging
from typing import Dict, Any, List, Optional, Tuple
from .defaults import default_retriever, default_formatter, default_enhancer

logger = logging.getLogger(__name__)

class RAGMixin:
    """Modular RAG mixin for agents."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rag_enabled = False
        self.context_retriever = None
        self.context_formatter = None
        self.query_enhancer = None
        
    def configure_rag(self, retriever=None, formatter=None, enhancer=None, enabled=True):
        """Configure RAG components."""
        self.context_retriever = retriever or default_retriever
        self.context_formatter = formatter or default_formatter
        self.query_enhancer = enhancer or default_enhancer
        self.rag_enabled = enabled
        if hasattr(self, "logger"):
            self.logger.info("RAG capabilities configured successfully")
    
    async def enhance_query_with_context(self, query: str, user_id: str) -> Tuple[str, Dict[str, Any]]:
        """Enhance query with relevant context."""
        if not self.rag_enabled or not self.context_retriever:
            return query, {"rag_enabled": False}
        
        try:
            # Retrieve context
            context_items = await self.context_retriever.retrieve_context(query, user_id)
            
            if not context_items:
                return query, {"rag_enabled": True, "context_found": False}
            
            # Format context
            formatted_context = self.context_formatter.format_context(context_items)
            
            # Enhance query
            enhanced_query = self.query_enhancer.enhance_query(query, formatted_context)
            
            metadata = {
                "rag_enabled": True,
                "context_found": True,
                "context_items": len(context_items),
                "sources": [item.source_id for item in context_items[:3]]
            }
            
            return enhanced_query, metadata
            
        except Exception as e:
            if hasattr(self, "logger"):
                self.logger.error(f"RAG enhancement error: {e}")
            return query, {"rag_enabled": True, "error": str(e)}
    
    async def process_with_rag(self, query: str, user_id: str, *args, **kwargs):
        """Process query with RAG enhancement."""
        enhanced_query, rag_metadata = await self.enhance_query_with_context(query, user_id)
        
        if hasattr(self, "process"):
            result = self.process(enhanced_query, user_id, *args, **kwargs)
            if isinstance(result, tuple) and len(result) == 2:
                response, metadata = result
                metadata["rag"] = rag_metadata
                return response, metadata
            return result, {"rag": rag_metadata}
        else:
            raise NotImplementedError("Agent must implement process method")
