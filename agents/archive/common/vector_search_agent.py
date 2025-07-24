"""
Vector Search Agent

A specialized agent that provides semantic document search capabilities
to other agents in the insurance navigator system.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

from .vector_retrieval_tool import VectorRetrievalTool, VectorFilter, VectorResult

logger = logging.getLogger(__name__)

@dataclass
class SearchContext:
    """Context object for search results."""
    query: str
    user_id: str
    total_results: int
    max_relevance_score: float
    document_context: List[Dict[str, Any]]
    regulatory_context: List[Dict[str, Any]]
    combined_text: str
    metadata_summary: Dict[str, Any]

class VectorSearchAgent:
    """Agent providing semantic document search capabilities."""
    
    def __init__(self, force_supabase: bool = True):
        """
        Initialize the vector search agent.
        
        Args:
            force_supabase: If True, connect directly to Supabase for production use
        """
        self.vector_tool = VectorRetrievalTool(force_supabase=force_supabase)
        self.name = "vector_search_agent"
        self.description = "Provides semantic document search and retrieval capabilities"
    
    async def search_user_documents(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        document_source_type: str = "user_document"
    ) -> SearchContext:
        """
        Search user's uploaded documents for relevant content.
        
        Args:
            query: Search query (can be natural language)
            user_id: User ID to filter documents
            limit: Maximum number of document chunks to return
            document_source_type: Type of documents to search
            
        Returns:
            SearchContext with results and metadata
        """
        try:
            # Search for documents using a broad filter
            filter_criteria = VectorFilter(
                user_id=user_id,
                document_source_type=document_source_type,
                limit=limit
            )
            
            vectors = await self.vector_tool.get_vectors_by_filter(filter_criteria)
            
            # Convert to context format
            document_context = []
            for vector in vectors:
                document_context.append({
                    "chunk_id": str(vector.id),
                    "content": vector.chunk_text,
                    "metadata": vector.chunk_metadata,
                    "chunk_index": vector.chunk_index,
                    "source_type": vector.document_source_type,
                    "document_id": str(vector.document_record_id) if vector.document_record_id else str(vector.document_id),
                    "relevance_score": 0.8  # Default relevance for now
                })
            
            # Get combined text and metadata
            combined_text = self.vector_tool.get_text_content(vectors)
            metadata_summary = self.vector_tool.get_metadata_summary(vectors)
            
            return SearchContext(
                query=query,
                user_id=user_id,
                total_results=len(vectors),
                max_relevance_score=0.8,
                document_context=document_context,
                regulatory_context=[],
                combined_text=combined_text,
                metadata_summary=metadata_summary
            )
            
        except Exception as e:
            logger.error(f"Error searching user documents: {e}")
            return self._empty_context(query, user_id)
    
    async def search_regulatory_documents(
        self,
        query: str,
        limit: int = 5,
        document_source_type: str = "regulatory_document"
    ) -> SearchContext:
        """
        Search regulatory documents for relevant content.
        
        Args:
            query: Search query
            limit: Maximum number of document chunks to return
            document_source_type: Type of documents to search
            
        Returns:
            SearchContext with regulatory results
        """
        try:
            # Search regulatory documents (no user_id filter)
            filter_criteria = VectorFilter(
                document_source_type=document_source_type,
                limit=limit
            )
            
            vectors = await self.vector_tool.get_vectors_by_filter(filter_criteria)
            
            # Convert to context format
            regulatory_context = []
            for vector in vectors:
                regulatory_context.append({
                    "chunk_id": str(vector.id),
                    "content": vector.chunk_text,
                    "metadata": vector.chunk_metadata,
                    "chunk_index": vector.chunk_index,
                    "source_type": vector.document_source_type,
                    "regulatory_document_id": str(vector.regulatory_document_id) if vector.regulatory_document_id else None,
                    "relevance_score": 0.7  # Default relevance for regulatory content
                })
            
            # Get combined text and metadata
            combined_text = self.vector_tool.get_text_content(vectors)
            metadata_summary = self.vector_tool.get_metadata_summary(vectors)
            
            return SearchContext(
                query=query,
                user_id="",
                total_results=len(vectors),
                max_relevance_score=0.7,
                document_context=[],
                regulatory_context=regulatory_context,
                combined_text=combined_text,
                metadata_summary=metadata_summary
            )
            
        except Exception as e:
            logger.error(f"Error searching regulatory documents: {e}")
            return self._empty_context(query, "")
    
    async def search_combined_context(
        self,
        query: str,
        user_id: str,
        user_doc_limit: int = 5,
        regulatory_limit: int = 3
    ) -> SearchContext:
        """
        Search both user documents and regulatory documents for comprehensive context.
        
        Args:
            query: Search query
            user_id: User ID for user document filtering
            user_doc_limit: Maximum user document chunks
            regulatory_limit: Maximum regulatory document chunks
            
        Returns:
            Combined SearchContext with both user and regulatory content
        """
        try:
            # Search user documents
            user_context = await self.search_user_documents(
                query=query,
                user_id=user_id,
                limit=user_doc_limit
            )
            
            # Search regulatory documents
            regulatory_context = await self.search_regulatory_documents(
                query=query,
                limit=regulatory_limit
            )
            
            # Combine contexts
            combined_text = ""
            if user_context.combined_text:
                combined_text += f"USER DOCUMENTS:\n{user_context.combined_text}\n\n"
            if regulatory_context.combined_text:
                combined_text += f"REGULATORY DOCUMENTS:\n{regulatory_context.combined_text}"
            
            # Combine metadata
            combined_metadata = {
                "user_doc_summary": user_context.metadata_summary,
                "regulatory_summary": regulatory_context.metadata_summary,
                "total_user_chunks": user_context.total_results,
                "total_regulatory_chunks": regulatory_context.total_results
            }
            
            return SearchContext(
                query=query,
                user_id=user_id,
                total_results=user_context.total_results + regulatory_context.total_results,
                max_relevance_score=max(user_context.max_relevance_score, regulatory_context.max_relevance_score),
                document_context=user_context.document_context,
                regulatory_context=regulatory_context.regulatory_context,
                combined_text=combined_text,
                metadata_summary=combined_metadata
            )
            
        except Exception as e:
            logger.error(f"Error in combined search: {e}")
            return self._empty_context(query, user_id)
    
    async def get_document_by_id(
        self,
        document_id: str,
        user_id: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> SearchContext:
        """
        Get all content for a specific document.
        
        Args:
            document_id: Document ID to retrieve
            user_id: User ID for filtering (optional)
            source_type: Document source type (optional)
            
        Returns:
            SearchContext with complete document content
        """
        try:
            vectors = await self.vector_tool.get_vectors_by_document(
                document_id=document_id,
                user_id=user_id,
                source_type=source_type
            )
            
            # Convert to context format
            document_context = []
            for vector in vectors:
                document_context.append({
                    "chunk_id": str(vector.id),
                    "content": vector.chunk_text,
                    "metadata": vector.chunk_metadata,
                    "chunk_index": vector.chunk_index,
                    "source_type": vector.document_source_type,
                    "document_id": document_id,
                    "relevance_score": 1.0  # Perfect relevance for direct document access
                })
            
            combined_text = self.vector_tool.get_text_content(vectors)
            metadata_summary = self.vector_tool.get_metadata_summary(vectors)
            
            return SearchContext(
                query=f"Document ID: {document_id}",
                user_id=user_id or "",
                total_results=len(vectors),
                max_relevance_score=1.0,
                document_context=document_context,
                regulatory_context=[],
                combined_text=combined_text,
                metadata_summary=metadata_summary
            )
            
        except Exception as e:
            logger.error(f"Error retrieving document by ID: {e}")
            return self._empty_context(f"Document ID: {document_id}", user_id or "")
    
    def create_agent_prompt_context(
        self,
        search_context: SearchContext,
        max_context_length: int = 4000
    ) -> str:
        """
        Create formatted context text for agent prompts.
        
        Args:
            search_context: Search results from vector search
            max_context_length: Maximum characters for context
            
        Returns:
            Formatted context string for agent prompts
        """
        if search_context.total_results == 0:
            return "No relevant documents found for this query."
        
        context_parts = []
        
        # Add user document context
        if search_context.document_context:
            context_parts.append("RELEVANT USER DOCUMENTS:")
            for doc in search_context.document_context[:3]:  # Limit to top 3
                content = doc["content"][:500] + "..." if len(doc["content"]) > 500 else doc["content"]
                context_parts.append(f"- {content}")
        
        # Add regulatory context
        if search_context.regulatory_context:
            context_parts.append("\nRELEVANT REGULATIONS:")
            for reg in search_context.regulatory_context[:2]:  # Limit to top 2
                content = reg["content"][:300] + "..." if len(reg["content"]) > 300 else reg["content"]
                context_parts.append(f"- {content}")
        
        # Combine and truncate if needed
        full_context = "\n".join(context_parts)
        if len(full_context) > max_context_length:
            full_context = full_context[:max_context_length-3] + "..."
        
        return full_context
    
    def _empty_context(self, query: str, user_id: str) -> SearchContext:
        """Create an empty search context for error cases."""
        return SearchContext(
            query=query,
            user_id=user_id,
            total_results=0,
            max_relevance_score=0.0,
            document_context=[],
            regulatory_context=[],
            combined_text="",
            metadata_summary={}
        )

# Convenience functions for other agents
async def search_user_documents(query: str, user_id: str, limit: int = 10) -> SearchContext:
    """Quick search for user documents."""
    agent = VectorSearchAgent()
    return await agent.search_user_documents(query, user_id, limit)

async def search_regulatory_documents(query: str, limit: int = 5) -> SearchContext:
    """Quick search for regulatory documents."""
    agent = VectorSearchAgent()
    return await agent.search_regulatory_documents(query, limit)

async def get_agent_context(query: str, user_id: str, max_length: int = 4000) -> str:
    """Get formatted context for agent prompts."""
    agent = VectorSearchAgent()
    search_results = await agent.search_combined_context(query, user_id)
    return agent.create_agent_prompt_context(search_results, max_length) 