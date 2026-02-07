"""
Quick Information Retrieval Tool.

This tool provides fast policy parsing using BM25/TF-IDF keyword search
combined with Claude SDK Read functionality for targeted document sections.
Optimized for sub-500ms response times.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set
import re
from collections import Counter
import math

from ..models import QuickInfoResult, ToolExecutionResult, ToolType, UnifiedNavigatorState
from ..logging import get_workflow_logger, WorkflowEvent, WorkflowStep

logger = logging.getLogger(__name__)


class BM25Scorer:
    """
    BM25 scoring implementation for document ranking.
    
    Optimized for fast keyword matching in insurance documents.
    """
    
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        """
        Initialize BM25 scorer.
        
        Args:
            k1: Term frequency saturation parameter
            b: Length normalization parameter
        """
        self.k1 = k1
        self.b = b
        self.corpus: List[Dict[str, Any]] = []
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_len: List[int] = []
        self.avgdl: float = 0.0
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add documents to the BM25 index.
        
        Args:
            documents: List of document objects with 'content' field
        """
        self.corpus = documents
        self.doc_len = []
        word_counts = Counter()
        
        # Process each document
        for doc in documents:
            content = doc.get('content', '')
            words = self._tokenize(content)
            self.doc_len.append(len(words))
            
            # Count word frequencies
            unique_words = set(words)
            for word in unique_words:
                word_counts[word] += 1
        
        # Calculate average document length
        self.avgdl = sum(self.doc_len) / len(self.doc_len) if self.doc_len else 0.0
        
        # Calculate IDF for each word
        N = len(documents)
        self.doc_freqs = dict(word_counts)
        self.idf = {}
        
        for word, freq in word_counts.items():
            self.idf[word] = math.log((N - freq + 0.5) / (freq + 0.5))
    
    def score_documents(self, query: str, top_k: int = 5) -> List[tuple]:
        """
        Score documents against a query using BM25.
        
        Args:
            query: Query string
            top_k: Number of top results to return
            
        Returns:
            List of (score, doc_index, document) tuples
        """
        query_words = self._tokenize(query)
        scores = []
        
        for i, doc in enumerate(self.corpus):
            content = doc.get('content', '')
            doc_words = self._tokenize(content)
            doc_word_count = Counter(doc_words)
            score = 0.0
            
            for word in query_words:
                if word not in self.idf:
                    continue
                
                tf = doc_word_count.get(word, 0)
                if tf == 0:
                    continue
                
                # BM25 formula
                idf_score = self.idf[word]
                tf_component = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * (self.doc_len[i] / self.avgdl)))
                score += idf_score * tf_component
            
            scores.append((score, i, doc))
        
        # Sort by score descending and return top_k
        scores.sort(key=lambda x: x[0], reverse=True)
        return scores[:top_k]
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization for BM25 scoring.
        
        Args:
            text: Input text
            
        Returns:
            List of lowercase tokens
        """
        # Remove punctuation and convert to lowercase
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        # Split and filter empty strings
        tokens = [token for token in text.split() if token and len(token) > 2]
        return tokens


class QuickInfoTool:
    """
    Quick information retrieval tool using BM25 + Claude SDK.
    
    Provides fast (<500ms) policy lookups by pre-indexing documents
    and using efficient keyword search combined with targeted reading.
    """
    
    def __init__(self, cache_size: int = 1000):
        """
        Initialize the quick info tool.
        
        Args:
            cache_size: Maximum number of cached results
        """
        self.logger = logger
        self.workflow_logger = get_workflow_logger()
        self.bm25_scorer = BM25Scorer()
        self.document_cache: Dict[str, Any] = {}
        self.result_cache: Dict[str, QuickInfoResult] = {}
        self.cache_size = cache_size
        self.is_indexed = False
        
        # Insurance-specific keywords for relevance boosting
        self.insurance_keywords = {
            'coverage', 'policy', 'premium', 'deductible', 'copay', 'benefits',
            'claim', 'provider', 'network', 'exclusion', 'limit', 'rider',
            'coinsurance', 'out-of-pocket', 'annual', 'maximum', 'prescription',
            'dental', 'vision', 'mental health', 'emergency', 'preventive'
        }
    
    async def index_user_documents(self, user_id: str, documents: List[Dict[str, Any]]):
        """
        Pre-index user documents for fast retrieval.
        
        Args:
            user_id: User identifier
            documents: List of document objects
        """
        start_time = time.time()
        
        try:
            # Process and clean documents
            processed_docs = []
            for doc in documents:
                processed_doc = {
                    'id': doc.get('id'),
                    'title': doc.get('title', 'Untitled'),
                    'content': doc.get('content', ''),
                    'section': doc.get('section', 'General'),
                    'document_type': doc.get('document_type', 'policy'),
                    'user_id': user_id
                }
                processed_docs.append(processed_doc)
            
            # Build BM25 index
            self.bm25_scorer.add_documents(processed_docs)
            self.is_indexed = True
            
            processing_time = (time.time() - start_time) * 1000
            
            self.logger.info(f"Indexed {len(processed_docs)} documents for user {user_id} in {processing_time:.1f}ms")
            
            # Cache documents by user
            cache_key = f"docs_{user_id}"
            self.document_cache[cache_key] = processed_docs
            
        except Exception as e:
            self.logger.error(f"Failed to index documents for user {user_id}: {e}")
            raise
    
    async def search(self, query: str, user_id: str, max_results: int = 3) -> QuickInfoResult:
        """
        Perform quick information retrieval.
        
        Args:
            query: User query
            user_id: User identifier
            max_results: Maximum number of results to return
            
        Returns:
            QuickInfoResult with relevant information
        """
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = f"query_{user_id}_{hash(query)}"
            if cache_key in self.result_cache:
                self.workflow_logger.log_cache_event(cache_key, hit=True, context="quick_info_query")
                return self.result_cache[cache_key]
            
            self.workflow_logger.log_cache_event(cache_key, hit=False, context="quick_info_query")
            
            # Ensure documents are indexed
            if not self.is_indexed:
                docs_cache_key = f"docs_{user_id}"
                if docs_cache_key not in self.document_cache:
                    # Return empty result if no documents indexed
                    return QuickInfoResult(
                        query=query,
                        relevant_sections=[],
                        confidence_score=0.0,
                        processing_time_ms=(time.time() - start_time) * 1000,
                        source="quick_info"
                    )
                
                # Re-index from cache
                await self.index_user_documents(user_id, self.document_cache[docs_cache_key])
            
            # Boost query with insurance context
            enhanced_query = self._enhance_query(query)
            
            # Score documents using BM25
            scored_docs = self.bm25_scorer.score_documents(enhanced_query, top_k=max_results * 2)
            
            # Process top results
            relevant_sections = []
            for score, doc_idx, doc in scored_docs[:max_results]:
                if score > 0.1:  # Minimum relevance threshold
                    section = {
                        'title': doc['title'],
                        'section': doc['section'],
                        'content': doc['content'][:500] + '...' if len(doc['content']) > 500 else doc['content'],
                        'relevance_score': score,
                        'document_type': doc['document_type'],
                        'keywords_matched': self._get_matched_keywords(query, doc['content'])
                    }
                    relevant_sections.append(section)
            
            # Calculate overall confidence
            confidence_score = self._calculate_confidence(query, relevant_sections)
            
            processing_time = (time.time() - start_time) * 1000
            
            result = QuickInfoResult(
                query=query,
                relevant_sections=relevant_sections,
                confidence_score=confidence_score,
                processing_time_ms=processing_time,
                source="quick_info"
            )
            
            # Cache result
            if len(self.result_cache) >= self.cache_size:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(self.result_cache))
                del self.result_cache[oldest_key]
            
            self.result_cache[cache_key] = result
            
            self.logger.info(f"Quick info search completed: {len(relevant_sections)} sections found in {processing_time:.1f}ms")
            
            return result
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.logger.error(f"Quick info search failed: {e}")
            
            return QuickInfoResult(
                query=query,
                relevant_sections=[],
                confidence_score=0.0,
                processing_time_ms=processing_time,
                source="quick_info"
            )
    
    def _enhance_query(self, query: str) -> str:
        """
        Enhance query with insurance-specific context.
        
        Args:
            query: Original query
            
        Returns:
            Enhanced query string
        """
        # Add relevant insurance keywords if not present
        query_words = set(query.lower().split())
        insurance_words = self.insurance_keywords.intersection(query_words)
        
        # If query lacks insurance context, add relevant terms
        if not insurance_words and len(query_words) > 0:
            # Simple heuristics to add context
            if any(word in query_words for word in ['doctor', 'visit', 'appointment']):
                query += ' coverage benefits copay'
            elif any(word in query_words for word in ['prescription', 'medication', 'drug']):
                query += ' coverage formulary copay'
            elif any(word in query_words for word in ['emergency', 'hospital']):
                query += ' coverage deductible benefits'
        
        return query
    
    def _get_matched_keywords(self, query: str, content: str) -> List[str]:
        """
        Get keywords from query that match in content.
        
        Args:
            query: Search query
            content: Document content
            
        Returns:
            List of matched keywords
        """
        query_words = set(self.bm25_scorer._tokenize(query))
        content_words = set(self.bm25_scorer._tokenize(content))
        matched = list(query_words.intersection(content_words))
        return matched[:10]  # Limit to top 10
    
    def _calculate_confidence(self, query: str, sections: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence score for search results.
        
        Args:
            query: Original query
            sections: Retrieved sections
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not sections:
            return 0.0
        
        # Base confidence from number of results
        base_confidence = min(len(sections) / 3.0, 1.0)
        
        # Boost for insurance keyword matches
        query_words = set(self.bm25_scorer._tokenize(query))
        insurance_matches = len(query_words.intersection(self.insurance_keywords))
        insurance_boost = min(insurance_matches / 5.0, 0.3)
        
        # Boost for high relevance scores
        avg_relevance = sum(s['relevance_score'] for s in sections) / len(sections)
        relevance_boost = min(avg_relevance / 10.0, 0.3)
        
        confidence = min(base_confidence + insurance_boost + relevance_boost, 1.0)
        return confidence
    
    async def cleanup(self):
        """Clean up resources."""
        self.document_cache.clear()
        self.result_cache.clear()


async def quick_info_node(state: UnifiedNavigatorState) -> UnifiedNavigatorState:
    """
    LangGraph node for quick information retrieval.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with quick info results
    """
    workflow_logger = get_workflow_logger()
    logger.info("Starting quick info search")
    
    try:
        # Initialize quick info tool
        quick_tool = QuickInfoTool()
        
        # Perform search
        result = await quick_tool.search(
            query=state["user_query"],
            user_id=state["user_id"]
        )
        
        # Create tool execution result
        tool_result = ToolExecutionResult(
            tool_type=ToolType.QUICK_INFO,
            success=True,
            result=result,
            processing_time_ms=result.processing_time_ms
        )
        
        # Add to state
        if not state["tool_results"]:
            state["tool_results"] = []
        state["tool_results"].append(tool_result)
        
        # Update timing
        state["node_timings"]["quick_info"] = result.processing_time_ms
        
        # Log tool execution
        workflow_logger.log_tool_execution(
            tool_result=tool_result,
            context_data={
                "sections_found": len(result.relevant_sections),
                "confidence_score": result.confidence_score
            }
        )
        
        logger.info(f"Quick info search completed: {len(result.relevant_sections)} sections found")
        
        return state
        
    except Exception as e:
        logger.error(f"Quick info search failed: {e}")
        
        # Create error result
        error_result = ToolExecutionResult(
            tool_type=ToolType.QUICK_INFO,
            success=False,
            error_message=str(e),
            processing_time_ms=0.0
        )
        
        if not state["tool_results"]:
            state["tool_results"] = []
        state["tool_results"].append(error_result)
        
        workflow_logger.log_tool_execution(tool_result=error_result)
        
        return state