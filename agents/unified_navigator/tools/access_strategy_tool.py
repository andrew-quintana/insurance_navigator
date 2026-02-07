"""
Access Strategizing Tool with Tavily Integration.

This tool generates comprehensive strategies for complex insurance scenarios
by combining Tavily research API with RAG validation for accurate, actionable advice.
"""

import asyncio
import logging
import time
import os
from typing import Any, Dict, List, Optional
import httpx

from ..models import AccessStrategyResult, ToolExecutionResult, ToolType, UnifiedNavigatorState
from ..logging import get_workflow_logger, LLMInteraction
from .rag_search import RAGSearchTool

logger = logging.getLogger(__name__)


class TavilyClient:
    """
    Client for Tavily research API.
    
    Provides web research capabilities for generating insurance strategy hypotheses.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Tavily client.
        
        Args:
            api_key: Tavily API key (if None, gets from environment)
        """
        self.api_key = api_key or os.getenv('TAVILY_API_KEY')
        self.base_url = "https://api.tavily.com"
        self.logger = logger
        
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")
    
    async def research(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
        include_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform research using Tavily API.
        
        Args:
            query: Research query
            search_depth: "basic" or "advanced"
            max_results: Maximum number of results
            include_domains: Optional list of domains to include
            
        Returns:
            Research results from Tavily
        """
        start_time = time.time()
        
        try:
            # Prepare request payload
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results,
                "include_answer": True,
                "include_raw_content": False,
                "include_images": False
            }
            
            if include_domains:
                payload["include_domains"] = include_domains
            
            # Make API request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    raise Exception(f"Tavily API error: {response.status_code} - {response.text}")
                
                result = response.json()
                processing_time = (time.time() - start_time) * 1000
                
                self.logger.info(f"Tavily research completed in {processing_time:.1f}ms")
                
                return {
                    "query": query,
                    "answer": result.get("answer", ""),
                    "results": result.get("results", []),
                    "processing_time_ms": processing_time,
                    "sources_count": len(result.get("results", []))
                }
                
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.logger.error(f"Tavily research failed: {e}")
            
            return {
                "query": query,
                "answer": "",
                "results": [],
                "processing_time_ms": processing_time,
                "error": str(e),
                "sources_count": 0
            }


class AccessStrategyTool:
    """
    Access strategizing tool for complex insurance scenarios.
    
    Combines Tavily research with RAG validation to provide comprehensive
    strategies for maximizing insurance coverage and benefits.
    """
    
    def __init__(self):
        """Initialize the access strategy tool."""
        self.logger = logger
        self.workflow_logger = get_workflow_logger()
        self.tavily_client = None
        self.strategy_cache: Dict[str, AccessStrategyResult] = {}
        
        # Try to initialize Tavily client
        try:
            self.tavily_client = TavilyClient()
        except ValueError as e:
            self.logger.warning(f"Tavily client not available: {e}")
    
    async def strategize(self, query: str, user_id: str) -> AccessStrategyResult:
        """
        Generate access strategy for complex insurance question.
        
        Args:
            query: User query requiring strategic analysis
            user_id: User identifier
            
        Returns:
            AccessStrategyResult with strategy and validation
        """
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = f"strategy_{user_id}_{hash(query)}"
            if cache_key in self.strategy_cache:
                self.workflow_logger.log_cache_event(cache_key, hit=True, context="access_strategy")
                return self.strategy_cache[cache_key]
            
            self.workflow_logger.log_cache_event(cache_key, hit=False, context="access_strategy")
            
            # Step 1: Generate research hypothesis using Tavily
            tavily_research = None
            if self.tavily_client:
                research_query = self._create_research_query(query)
                tavily_research = await self.tavily_client.research(
                    query=research_query,
                    search_depth="advanced",
                    max_results=5,
                    include_domains=["healthcare.gov", "cms.gov", "kff.org", "naic.org"]
                )
            
            # Step 2: Generate strategy hypothesis
            strategy_hypothesis = await self._generate_strategy_hypothesis(query, tavily_research)
            
            # Step 3: Validate strategy using RAG
            rag_validation = await self._validate_with_rag(query, strategy_hypothesis, user_id)
            
            # Step 4: Calculate confidence score
            confidence_score = self._calculate_strategy_confidence(tavily_research, rag_validation)
            
            processing_time = (time.time() - start_time) * 1000
            
            result = AccessStrategyResult(
                query=query,
                strategy_hypothesis=strategy_hypothesis,
                tavily_research=tavily_research,
                rag_validation=rag_validation,
                confidence_score=confidence_score,
                processing_time_ms=processing_time,
                source="access_strategy"
            )
            
            # Cache result
            self.strategy_cache[cache_key] = result
            
            self.logger.info(f"Access strategy generated in {processing_time:.1f}ms")
            
            return result
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.logger.error(f"Access strategy generation failed: {e}")
            
            return AccessStrategyResult(
                query=query,
                strategy_hypothesis=f"I apologize, but I encountered an error while developing a strategy for your question: {str(e)}",
                tavily_research=None,
                rag_validation=None,
                confidence_score=0.0,
                processing_time_ms=processing_time,
                source="access_strategy"
            )
    
    def _create_research_query(self, user_query: str) -> str:
        """
        Create optimized research query for Tavily.
        
        Args:
            user_query: Original user query
            
        Returns:
            Optimized research query
        """
        # Add insurance context and strategy keywords
        research_query = f"insurance strategy {user_query} healthcare coverage maximize benefits 2025"
        
        # Add specific context based on query content
        query_lower = user_query.lower()
        
        if "compare" in query_lower or "option" in query_lower:
            research_query += " comparison analysis best practices"
        
        if "maximize" in query_lower or "most" in query_lower:
            research_query += " optimization strategies tips"
        
        if "claim" in query_lower:
            research_query += " claims process approval strategies"
        
        if "network" in query_lower or "provider" in query_lower:
            research_query += " provider network selection strategies"
        
        return research_query
    
    async def _generate_strategy_hypothesis(
        self,
        query: str,
        tavily_research: Optional[Dict[str, Any]]
    ) -> str:
        """
        Generate strategy hypothesis using available research.
        
        Args:
            query: Original user query
            tavily_research: Research results from Tavily
            
        Returns:
            Strategy hypothesis text
        """
        # Base strategy components
        strategy_parts = []
        
        # Add research-based insights if available
        if tavily_research and tavily_research.get("answer"):
            strategy_parts.append("Based on current industry research:")
            strategy_parts.append(tavily_research["answer"])
        
        # Add general strategic framework
        strategy_parts.append("\nStrategic approach:")
        
        # Analyze query for strategy type
        query_lower = query.lower()
        
        if "compare" in query_lower:
            strategy_parts.append(
                "1. Analyze your specific needs and priorities\n"
                "2. Compare key features: coverage, network, costs\n"
                "3. Consider total cost of ownership, not just premiums\n"
                "4. Review provider networks for your preferred doctors\n"
                "5. Evaluate coverage for your specific conditions or medications"
            )
        
        elif "maximize" in query_lower or "best" in query_lower:
            strategy_parts.append(
                "1. Understand your policy's full benefits and services\n"
                "2. Use preventive care to avoid larger costs later\n"
                "3. Stay within network when possible\n"
                "4. Keep detailed records of all healthcare interactions\n"
                "5. Review and appeal denied claims when appropriate"
            )
        
        elif "claim" in query_lower:
            strategy_parts.append(
                "1. Document everything thoroughly before submitting\n"
                "2. Submit claims promptly within required timeframes\n"
                "3. Follow up on pending claims regularly\n"
                "4. Understand your appeal rights if denied\n"
                "5. Consider working with your provider's billing department"
            )
        
        else:
            # General insurance strategy
            strategy_parts.append(
                "1. Review your current coverage and identify gaps\n"
                "2. Understand your policy terms, limits, and exclusions\n"
                "3. Maintain organized records of all insurance communications\n"
                "4. Consider timing for any coverage changes\n"
                "5. Seek clarification on unclear policy language"
            )
        
        return "\n".join(strategy_parts)
    
    async def _validate_with_rag(
        self,
        query: str,
        strategy: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Validate strategy against user's specific policy using RAG.
        
        Args:
            query: Original query
            strategy: Generated strategy
            user_id: User identifier
            
        Returns:
            RAG validation results
        """
        try:
            # Create validation query
            validation_query = f"Based on my policy documents, validate this strategy: {strategy[:200]}..."
            
            # Use RAG tool for validation
            rag_tool = RAGSearchTool(user_id)
            rag_result = await rag_tool.search(validation_query)
            
            if rag_result and rag_result.chunks:
                return {
                    "validation_query": validation_query,
                    "relevant_chunks": len(rag_result.chunks),
                    "top_chunk_content": rag_result.chunks[0].get('content', '')[:300] if rag_result.chunks else "",
                    "processing_time_ms": rag_result.processing_time_ms
                }
            
        except Exception as e:
            self.logger.error(f"RAG validation failed: {e}")
        
        return None
    
    def _calculate_strategy_confidence(
        self,
        tavily_research: Optional[Dict[str, Any]],
        rag_validation: Optional[Dict[str, Any]]
    ) -> float:
        """
        Calculate confidence score for the generated strategy.
        
        Args:
            tavily_research: Tavily research results
            rag_validation: RAG validation results
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.5  # Base confidence
        
        # Boost for successful Tavily research
        if tavily_research and tavily_research.get("sources_count", 0) > 0:
            confidence += 0.2
            
            # Extra boost for quality answer
            if tavily_research.get("answer") and len(tavily_research["answer"]) > 100:
                confidence += 0.1
        
        # Boost for successful RAG validation
        if rag_validation and rag_validation.get("relevant_chunks", 0) > 0:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    async def cleanup(self):
        """Clean up resources."""
        self.strategy_cache.clear()


async def access_strategy_node(state: UnifiedNavigatorState) -> UnifiedNavigatorState:
    """
    LangGraph node for access strategy generation.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with access strategy results
    """
    workflow_logger = get_workflow_logger()
    logger.info("Starting access strategy generation")
    
    try:
        # Initialize access strategy tool
        strategy_tool = AccessStrategyTool()
        
        # Generate strategy
        result = await strategy_tool.strategize(
            query=state["user_query"],
            user_id=state["user_id"]
        )
        
        # Create tool execution result
        tool_result = ToolExecutionResult(
            tool_type=ToolType.ACCESS_STRATEGY,
            success=True,
            result=result,
            processing_time_ms=result.processing_time_ms
        )
        
        # Add to state
        if not state["tool_results"]:
            state["tool_results"] = []
        state["tool_results"].append(tool_result)
        
        # Update timing
        state["node_timings"]["access_strategy"] = result.processing_time_ms
        
        # Log tool execution
        workflow_logger.log_tool_execution(
            tool_result=tool_result,
            context_data={
                "has_tavily_research": result.tavily_research is not None,
                "has_rag_validation": result.rag_validation is not None,
                "confidence_score": result.confidence_score
            }
        )
        
        logger.info(f"Access strategy generated: confidence={result.confidence_score:.2f}")
        
        return state
        
    except Exception as e:
        logger.error(f"Access strategy generation failed: {e}")
        
        # Create error result
        error_result = ToolExecutionResult(
            tool_type=ToolType.ACCESS_STRATEGY,
            success=False,
            error_message=str(e),
            processing_time_ms=0.0
        )
        
        if not state["tool_results"]:
            state["tool_results"] = []
        state["tool_results"].append(error_result)
        
        workflow_logger.log_tool_execution(tool_result=error_result)
        
        return state