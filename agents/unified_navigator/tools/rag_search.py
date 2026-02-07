"""
RAG Search Tool Integration.

This module provides integration with the existing RAG system
for document search within the unified navigator workflow.
"""

import logging
import time
from typing import Dict, Any

from agents.tooling.rag.core import RAGTool, RetrievalConfig
from ..models import RAGSearchResult, UnifiedNavigatorState, ToolExecutionResult, ToolType


class RAGSearchTool:
    """
    RAG search tool wrapper for unified navigator.
    Integrates with existing RAG system from agents.tooling.rag.core
    """
    
    def __init__(self, user_id: str):
        self.logger = logging.getLogger("unified_navigator.rag_search")
        self.user_id = user_id
        
        # Use default retrieval config optimized for low latency
        self.config = RetrievalConfig(
            similarity_threshold=0.25,
            max_chunks=5,
            token_budget=4000
        )
        
        self.rag_tool = RAGTool(
            user_id=user_id,
            config=self.config,
            context="unified_navigator"
        )
    
    async def search(self, query: str) -> RAGSearchResult:
        """
        Perform RAG search using existing system.
        
        Args:
            query: Search query
            
        Returns:
            RAGSearchResult with document chunks
        """
        start_time = time.time()
        
        try:
            # Use existing RAG system
            chunks = await self.rag_tool.retrieve_chunks_from_text(query)
            
            # Convert chunks to serializable format
            chunk_results = []
            for chunk in chunks:
                chunk_dict = {
                    "id": chunk.id,
                    "doc_id": chunk.doc_id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "similarity": chunk.similarity,
                    "section_title": chunk.section_title,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "tokens": chunk.tokens
                }
                chunk_results.append(chunk_dict)
            
            processing_time = (time.time() - start_time) * 1000
            
            self.logger.info(f"RAG search completed: {len(chunks)} chunks in {processing_time:.1f}ms")
            
            return RAGSearchResult(
                query=query,
                chunks=chunk_results,
                total_chunks=len(chunks),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"RAG search error: {e}")
            return RAGSearchResult(
                query=query,
                chunks=[],
                total_chunks=0,
                processing_time_ms=(time.time() - start_time) * 1000
            )


# LangGraph node function
async def rag_search_node(state: UnifiedNavigatorState) -> UnifiedNavigatorState:
    """
    LangGraph node for RAG search execution.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with RAG search results
    """
    try:
        if not state["tool_results"]:
            state["tool_results"] = []
        
        # Initialize RAG search tool
        rag_search = RAGSearchTool(state["user_id"])
        
        # Perform RAG search
        search_result = await rag_search.search(state["user_query"])
        
        # Add to tool results
        tool_result = ToolExecutionResult(
            tool_type=ToolType.RAG_SEARCH,
            success=search_result.total_chunks > 0,
            result=search_result,
            processing_time_ms=search_result.processing_time_ms
        )
        
        state["tool_results"].append(tool_result)
        
        # Record timing
        state["node_timings"]["rag_search"] = search_result.processing_time_ms
        
        return state
        
    except Exception as e:
        logging.getLogger("unified_navigator.rag_search").error(f"RAG search node error: {e}")
        
        # Add error result
        if not state["tool_results"]:
            state["tool_results"] = []
        
        error_result = ToolExecutionResult(
            tool_type=ToolType.RAG_SEARCH,
            success=False,
            error_message=str(e),
            processing_time_ms=0
        )
        
        state["tool_results"].append(error_result)
        return state


# Combined search node for parallel execution
async def combined_search_node(state: UnifiedNavigatorState) -> UnifiedNavigatorState:
    """
    LangGraph node for parallel web + RAG search execution.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with both search results
    """
    import asyncio
    from .web_search import WebSearchTool
    
    try:
        if not state["tool_results"]:
            state["tool_results"] = []
        
        # Initialize both tools
        web_search = WebSearchTool()
        rag_search = RAGSearchTool(state["user_id"])
        
        # Execute searches in parallel
        start_time = time.time()
        
        web_task = asyncio.create_task(web_search.search(state["user_query"]))
        rag_task = asyncio.create_task(rag_search.search(state["user_query"]))
        
        web_result, rag_result = await asyncio.gather(web_task, rag_task)
        
        total_time = (time.time() - start_time) * 1000
        
        # Add web search result
        web_tool_result = ToolExecutionResult(
            tool_type=ToolType.WEB_SEARCH,
            success=web_result.total_results > 0,
            result=web_result,
            processing_time_ms=web_result.processing_time_ms
        )
        state["tool_results"].append(web_tool_result)
        
        # Add RAG search result
        rag_tool_result = ToolExecutionResult(
            tool_type=ToolType.RAG_SEARCH,
            success=rag_result.total_chunks > 0,
            result=rag_result,
            processing_time_ms=rag_result.processing_time_ms
        )
        state["tool_results"].append(rag_tool_result)
        
        # Record timing
        state["node_timings"]["combined_search"] = total_time
        
        logging.getLogger("unified_navigator.combined_search").info(
            f"Combined search completed in {total_time:.1f}ms"
        )
        
        # Clean up
        await web_search.cleanup()
        
        return state
        
    except Exception as e:
        logging.getLogger("unified_navigator.combined_search").error(f"Combined search error: {e}")
        
        # Add error result
        if not state["tool_results"]:
            state["tool_results"] = []
        
        error_result = ToolExecutionResult(
            tool_type=ToolType.COMBINED,
            success=False,
            error_message=str(e),
            processing_time_ms=0
        )
        
        state["tool_results"].append(error_result)
        return state