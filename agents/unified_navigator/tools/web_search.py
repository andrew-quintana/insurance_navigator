"""
Web Search Tool with Brave API Integration.

This module provides web search capabilities using the Brave Search API
with connection pooling, caching, and low-latency optimization.
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional
import httpx
from datetime import datetime, timedelta

from ..models import WebSearchResult, UnifiedNavigatorState


class WebSearchCache:
    """Simple in-memory cache for web search results."""
    
    def __init__(self, ttl_minutes: int = 60, max_size: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_minutes = ttl_minutes
        self.max_size = max_size
    
    def _get_key(self, query: str) -> str:
        """Generate cache key from query."""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached result if valid."""
        key = self._get_key(query)
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() - entry["timestamp"] < timedelta(minutes=self.ttl_minutes):
                return entry["data"]
            else:
                del self.cache[key]
        return None
    
    def put(self, query: str, data: Dict[str, Any]):
        """Cache search result."""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
        
        key = self._get_key(query)
        self.cache[key] = {
            "data": data,
            "timestamp": datetime.now()
        }


class WebSearchTool:
    """
    Web search tool using Brave Search API with optimization for low latency.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("unified_navigator.web_search")
        self.api_key = os.getenv("BRAVE_API_KEY")
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.cache = WebSearchCache()
        
        if not self.api_key:
            self.logger.warning("BRAVE_API_KEY not found - web search will not work")
        
        # Setup HTTP client with connection pooling
        self.http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            timeout=httpx.Timeout(5.0, connect=2.0)
        )
        
        # Insurance-specific search optimization
        self.insurance_modifiers = [
            "insurance", "healthcare", "medical", "coverage", "policy"
        ]
    
    async def search(self, query: str, max_results: int = 10) -> WebSearchResult:
        """
        Perform web search with caching and optimization.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            WebSearchResult with search results
        """
        start_time = time.time()
        
        try:
            # Check cache first
            cached_result = self.cache.get(query)
            if cached_result:
                self.logger.info(f"Cache hit for query: {query[:50]}...")
                return WebSearchResult(
                    query=query,
                    results=cached_result["results"][:max_results],
                    total_results=cached_result["total_results"],
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            if not self.api_key:
                return WebSearchResult(
                    query=query,
                    results=[],
                    total_results=0,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Optimize query for insurance domain
            optimized_query = self._optimize_query(query)
            
            # Perform search
            params = {
                "q": optimized_query,
                "count": min(max_results, 20),  # API limit
                "search_lang": "en",
                "country": "US",
                "safesearch": "strict",
                "freshness": "py"  # Past year for current info
            }
            
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.api_key
            }
            
            response = await self.http_client.get(
                self.base_url,
                params=params,
                headers=headers
            )
            
            if response.status_code != 200:
                self.logger.error(f"Brave API error: {response.status_code} - {response.text}")
                return WebSearchResult(
                    query=query,
                    results=[],
                    total_results=0,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            data = response.json()
            
            # Process results
            results = []
            web_results = data.get("web", {}).get("results", [])
            
            for result in web_results:
                processed_result = {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "description": result.get("description", ""),
                    "published": result.get("age", ""),
                    "snippet": result.get("extra_snippets", [])
                }
                results.append(processed_result)
            
            total_results = len(web_results)
            
            # Cache result
            cache_data = {
                "results": results,
                "total_results": total_results
            }
            self.cache.put(query, cache_data)
            
            processing_time = (time.time() - start_time) * 1000
            self.logger.info(f"Web search completed: {total_results} results in {processing_time:.1f}ms")
            
            return WebSearchResult(
                query=query,
                results=results[:max_results],
                total_results=total_results,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"Web search error: {e}")
            return WebSearchResult(
                query=query,
                results=[],
                total_results=0,
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    def _optimize_query(self, query: str) -> str:
        """
        Optimize search query for insurance domain.
        
        Args:
            query: Original query
            
        Returns:
            Optimized query string
        """
        query_lower = query.lower()
        
        # Add insurance context if not present
        has_insurance_terms = any(term in query_lower for term in self.insurance_modifiers)
        
        if not has_insurance_terms:
            # Add relevant insurance context
            if any(term in query_lower for term in ["doctor", "physician", "hospital", "clinic"]):
                query = f"{query} insurance healthcare"
            elif any(term in query_lower for term in ["cost", "price", "expensive", "afford"]):
                query = f"{query} insurance coverage"
            elif any(term in query_lower for term in ["medication", "prescription", "drug", "pharmacy"]):
                query = f"{query} insurance formulary"
            else:
                query = f"{query} insurance"
        
        return query
    
    async def cleanup(self):
        """Clean up HTTP client resources."""
        if self.http_client:
            await self.http_client.aclose()


# LangGraph node function
async def web_search_node(state: UnifiedNavigatorState) -> UnifiedNavigatorState:
    """
    LangGraph node for web search execution.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with web search results
    """
    web_search = WebSearchTool()
    
    try:
        if not state["tool_results"]:
            state["tool_results"] = []
        
        # Perform web search
        search_result = await web_search.search(state["user_query"])
        
        # Add to tool results
        from ..models import ToolExecutionResult, ToolType
        
        tool_result = ToolExecutionResult(
            tool_type=ToolType.WEB_SEARCH,
            success=search_result.total_results > 0,
            result=search_result,
            processing_time_ms=search_result.processing_time_ms
        )
        
        state["tool_results"].append(tool_result)
        
        # Record timing
        state["node_timings"]["web_search"] = search_result.processing_time_ms
        
        return state
        
    except Exception as e:
        logging.getLogger("unified_navigator.web_search").error(f"Web search node error: {e}")
        
        # Add error result
        if not state["tool_results"]:
            state["tool_results"] = []
        
        from ..models import ToolExecutionResult, ToolType
        
        error_result = ToolExecutionResult(
            tool_type=ToolType.WEB_SEARCH,
            success=False,
            error_message=str(e),
            processing_time_ms=0
        )
        
        state["tool_results"].append(error_result)
        return state
        
    finally:
        await web_search.cleanup()