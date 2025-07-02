"""
RAG Pipeline Test Suite

This module provides comprehensive testing for the RAG (Retrieval-Augmented Generation) 
pipeline, including:

1. Document vectorization testing
2. Vector search validation
3. LangGraph workflow testing  
4. Agent integration testing
5. End-to-end pipeline validation
"""

import asyncio
import pytest
import logging
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import json
import uuid

# Import test configuration
from tests.config.rag_test_config import (
    get_active_config, 
    get_rag_test_config,
    create_custom_config,
    DocumentTestConfig,
    RAGTestConfig
)

# Import services
from db.services.document_service import DocumentService
from db.services.embedding_service import EmbeddingService
from agents.common.vector_rag import VectorRAG

# Import LangGraph utilities
from agents.zPrototyping.langgraph_utils import (
    WorkflowBuilder,
    WorkflowState,
    create_agent,
    AgentDiscovery
)

logger = logging.getLogger(__name__)

class TestRAGPipeline:
    """Test suite for RAG pipeline functionality."""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment before each test."""
        self.config = get_active_config()
        self.document_service = DocumentService()
        self.embedding_service = EmbeddingService()
        self.vector_rag = VectorRAG()
        
        # Mock LLM if configured
        if self.config.use_mock_llm:
            self._setup_mock_llm()
        
        logger.info(f"Test setup complete for document: {self.config.primary_document.document_id}")
    
    def _setup_mock_llm(self):
        """Setup mock LLM for testing."""
        self.mock_llm = MagicMock()
        self.mock_llm.invoke = AsyncMock(return_value="Mock LLM response for testing")
        
    async def test_document_exists(self):
        """Test that the configured document exists in the database."""
        config = self.config
        doc_id = config.primary_document.document_id
        user_id = config.primary_document.test_user_id
        
        # Test document existence
        document_status = await self.document_service.get_document_status(doc_id, user_id)
        
        assert document_status is not None, f"Document {doc_id} not found"
        assert document_status.get("status") != "not_found", f"Document {doc_id} not accessible"
        
        logger.info(f"Document {doc_id} exists with status: {document_status.get('status')}")
    
    async def test_document_vectorization(self):
        """Test that the document has been properly vectorized."""
        config = self.config
        doc_id = config.primary_document.document_id
        user_id = config.primary_document.test_user_id
        
        if not config.validate_embeddings:
            pytest.skip("Embedding validation disabled in config")
        
        # Test vector search to verify embeddings exist
        test_query = "insurance policy information"
        results = await self.embedding_service.search_user_documents(
            query=test_query,
            user_id=user_id,
            document_filters={"document_id": doc_id},
            limit=5
        )
        
        assert results is not None, "Vector search returned None"
        assert len(results) > 0, f"No vector chunks found for document {doc_id}"
        
        # Validate embedding structure
        for result in results:
            assert "similarity_score" in result, "Missing similarity score"
            assert "chunk_text" in result, "Missing chunk text"
            assert "chunk_metadata" in result, "Missing chunk metadata"
            assert result["similarity_score"] >= 0, "Invalid similarity score"
        
        logger.info(f"Document {doc_id} has {len(results)} vector chunks")
    
    async def test_vector_search_functionality(self):
        """Test vector search with configured queries."""
        config = self.config
        user_id = config.primary_document.test_user_id
        
        if not config.validate_search_results:
            pytest.skip("Search result validation disabled in config")
        
        for query in config.test_queries:
            logger.info(f"Testing vector search for query: '{query}'")
            
            # Perform vector search
            results = await self.embedding_service.search_user_documents(
                query=query,
                user_id=user_id,
                limit=config.vector_search_limit
            )
            
            assert results is not None, f"Vector search failed for query: {query}"
            
            # Check similarity threshold
            if results:
                top_result = results[0]
                similarity = top_result.get("similarity_score", 0)
                assert similarity >= config.similarity_threshold, \
                    f"Top result similarity {similarity} below threshold {config.similarity_threshold}"
            
            # Check expected results if configured
            if query in config.expected_results:
                expected = config.expected_results[query]
                
                if expected.get("should_find_results", True):
                    assert len(results) > 0, f"Expected results for query '{query}' but found none"
                
                if "min_similarity" in expected and results:
                    min_sim = expected["min_similarity"]
                    top_sim = results[0].get("similarity_score", 0)
                    assert top_sim >= min_sim, \
                        f"Top similarity {top_sim} below expected minimum {min_sim}"
                
                if "expected_keywords" in expected and results:
                    keywords = expected["expected_keywords"]
                    top_text = results[0].get("chunk_text", "").lower()
                    found_keywords = [kw for kw in keywords if kw.lower() in top_text]
                    assert len(found_keywords) > 0, \
                        f"None of expected keywords {keywords} found in top result"
            
            logger.info(f"Query '{query}' returned {len(results)} results")
    
    async def test_policy_facts_extraction(self):
        """Test policy facts extraction for the document."""
        config = self.config
        doc_id = config.primary_document.document_id
        
        # Get policy facts
        policy_facts = await self.document_service.get_policy_facts(doc_id)
        
        assert policy_facts is not None, f"Failed to get policy facts for {doc_id}"
        
        # Check for common insurance fields
        expected_fields = ["deductible", "copay", "annual_max", "plan_type"]
        found_fields = [field for field in expected_fields if field in policy_facts]
        
        # At least some fields should be extracted for insurance documents
        if config.primary_document.document_type == "insurance_policy":
            assert len(found_fields) > 0, \
                f"No insurance fields found in policy facts: {list(policy_facts.keys())}"
        
        logger.info(f"Policy facts for {doc_id}: {len(policy_facts)} fields extracted")
        logger.info(f"Found fields: {found_fields}")
    
    async def test_hybrid_search(self):
        """Test hybrid search combining facts and vector search."""
        config = self.config
        user_id = config.primary_document.test_user_id
        
        # Test queries that should trigger both fact and vector search
        hybrid_queries = [
            "What is my deductible?",
            "Show me copay information",
            "What services are covered?"
        ]
        
        for query in hybrid_queries:
            logger.info(f"Testing hybrid search for: '{query}'")
            
            results = await self.document_service.search_hybrid(
                user_id=user_id,
                query=query,
                limit=config.vector_search_limit
            )
            
            assert results is not None, f"Hybrid search failed for query: {query}"
            assert "results" in results, "Missing results in hybrid search response"
            assert "search_type" in results, "Missing search_type in hybrid search response"
            
            # Should have some results for basic insurance queries
            search_results = results.get("results", [])
            if query.lower() in ["deductible", "copay", "coverage"]:
                assert len(search_results) > 0, \
                    f"Expected results for insurance query '{query}' but found none"
            
            logger.info(f"Hybrid search '{query}': {len(search_results)} results, type: {results.get('search_type')}")
    
    @pytest.mark.skipif(not get_active_config().enable_langgraph, reason="LangGraph disabled in config")
    async def test_langgraph_workflow_setup(self):
        """Test LangGraph workflow setup and basic functionality."""
        config = self.config
        
        # Test workflow builder
        builder = WorkflowBuilder(name="rag_test_workflow")
        
        # Add test nodes
        async def document_retrieval(state: WorkflowState) -> WorkflowState:
            """Mock document retrieval node."""
            state.context["retrieved_docs"] = ["mock_doc_1", "mock_doc_2"]
            state.add_message("Documents retrieved successfully")
            return state
        
        async def response_generation(state: WorkflowState) -> WorkflowState:
            """Mock response generation node."""
            docs = state.context.get("retrieved_docs", [])
            state.context["response"] = f"Generated response based on {len(docs)} documents"
            state.add_message("Response generated")
            return state
        
        # Build workflow
        workflow = (builder
                   .add_node("retrieve", document_retrieval, "Document retrieval node")
                   .add_node("generate", response_generation, "Response generation node")
                   .add_edge("retrieve", "generate")
                   .set_entry_point("retrieve")
                   .build())
        
        assert workflow is not None, "Failed to build LangGraph workflow"
        
        # Test workflow execution
        initial_state = WorkflowState()
        initial_state.add_message("Starting RAG workflow test")
        
        # Execute workflow (this would be async in real LangGraph)
        # For now, just test that it doesn't crash
        logger.info("LangGraph workflow setup successful")
    
    @pytest.mark.skipif(not get_active_config().enable_langgraph, reason="LangGraph disabled in config")
    async def test_agent_integration(self):
        """Test agent integration with RAG pipeline."""
        config = self.config
        
        # Test agent discovery
        discovery = AgentDiscovery()
        agents = discovery.discover_agents()
        
        primary_agent = config.primary_agent
        assert primary_agent in agents, f"Primary agent '{primary_agent}' not found"
        
        # Test agent loading
        agent_info = discovery.get_agent_info(primary_agent)
        assert agent_info is not None, f"Could not get info for agent '{primary_agent}'"
        
        logger.info(f"Agent '{primary_agent}' integration test passed")
        
        # Test fallback agents
        for fallback_agent in config.fallback_agents:
            if fallback_agent in agents:
                fallback_info = discovery.get_agent_info(fallback_agent)
                assert fallback_info is not None, f"Could not get info for fallback agent '{fallback_agent}'"
                logger.info(f"Fallback agent '{fallback_agent}' available")
    
    async def test_end_to_end_rag_pipeline(self):
        """Test complete end-to-end RAG pipeline."""
        config = self.config
        doc_id = config.primary_document.document_id
        user_id = config.primary_document.test_user_id
        
        # Test the complete pipeline for each test query
        for query in config.test_queries[:3]:  # Limit to first 3 for performance
            logger.info(f"Testing end-to-end pipeline for: '{query}'")
            
            # Step 1: Document retrieval
            vector_results = await self.embedding_service.search_user_documents(
                query=query,
                user_id=user_id,
                limit=5
            )
            
            # Step 2: Policy facts retrieval
            policy_facts = await self.document_service.get_policy_facts(doc_id)
            
            # Step 3: Hybrid search
            hybrid_results = await self.document_service.search_hybrid(
                user_id=user_id,
                query=query,
                limit=5
            )
            
            # Validate pipeline components
            assert vector_results is not None, f"Vector search failed for '{query}'"
            assert policy_facts is not None, f"Policy facts retrieval failed for '{query}'"
            assert hybrid_results is not None, f"Hybrid search failed for '{query}'"
            
            # Check for coherent results
            hybrid_result_count = len(hybrid_results.get("results", []))
            logger.info(f"End-to-end pipeline for '{query}': {hybrid_result_count} results")
    
    async def test_performance_benchmarks(self):
        """Test performance benchmarks for RAG operations."""
        import time
        
        config = self.config
        user_id = config.primary_document.test_user_id
        
        # Benchmark vector search
        query = config.test_queries[0] if config.test_queries else "test query"
        
        start_time = time.time()
        results = await self.embedding_service.search_user_documents(
            query=query,
            user_id=user_id,
            limit=10
        )
        search_time = time.time() - start_time
        
        # Performance assertions
        assert search_time < 5.0, f"Vector search took too long: {search_time:.2f}s"
        
        logger.info(f"Vector search performance: {search_time:.3f}s for {len(results or [])} results")

class TestRAGConfiguration:
    """Test suite for RAG configuration management."""
    
    def test_default_config_loading(self):
        """Test loading default configurations."""
        config = get_rag_test_config("current_test")
        
        assert config is not None
        assert config.primary_document.document_id == "d64bfbbe-ff7f-4b51-b220-a0fa20756d9d"
        assert config.primary_document.test_user_id is not None
        assert len(config.test_queries) > 0
    
    def test_custom_config_creation(self):
        """Test creating custom configurations."""
        new_doc_id = str(uuid.uuid4())
        
        custom_config = create_custom_config(
            document_id=new_doc_id,
            config_name="test_custom",
            description="Test custom configuration"
        )
        
        assert custom_config.primary_document.document_id == new_doc_id
        assert custom_config.primary_document.description == "Test custom configuration"
        
        # Should be able to retrieve it
        retrieved_config = get_rag_test_config("test_custom")
        assert retrieved_config.primary_document.document_id == new_doc_id
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid document ID
        with pytest.raises(ValueError):
            DocumentTestConfig(document_id="invalid-uuid-format")
        
        # Test valid document ID
        valid_config = DocumentTestConfig(document_id=str(uuid.uuid4()))
        assert valid_config.test_user_id is not None
    
    def test_config_serialization(self):
        """Test configuration serialization and deserialization."""
        config = get_rag_test_config("current_test")
        
        # Test to_dict
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert "primary_document" in config_dict
        assert "test_queries" in config_dict
        
        # Test from_dict
        restored_config = RAGTestConfig.from_dict(config_dict)
        assert restored_config.primary_document.document_id == config.primary_document.document_id
        assert restored_config.test_queries == config.test_queries

# Utility functions for running tests
async def run_quick_test(document_id: Optional[str] = None) -> Dict[str, Any]:
    """Run a quick test of the RAG pipeline."""
    if document_id:
        config = create_custom_config(document_id, "quick_test", description="Quick validation test")
    else:
        config = get_rag_test_config("minimal_test")
    
    test_instance = TestRAGPipeline()
    await test_instance.setup()
    
    results = {
        "document_exists": False,
        "has_vectors": False,
        "search_works": False,
        "policy_facts": False
    }
    
    try:
        await test_instance.test_document_exists()
        results["document_exists"] = True
    except Exception as e:
        logger.error(f"Document existence test failed: {e}")
    
    try:
        await test_instance.test_document_vectorization()
        results["has_vectors"] = True
    except Exception as e:
        logger.error(f"Vectorization test failed: {e}")
    
    try:
        await test_instance.test_vector_search_functionality()
        results["search_works"] = True
    except Exception as e:
        logger.error(f"Search test failed: {e}")
    
    try:
        await test_instance.test_policy_facts_extraction()
        results["policy_facts"] = True
    except Exception as e:
        logger.error(f"Policy facts test failed: {e}")
    
    return results

if __name__ == "__main__":
    # Quick test runner
    async def main():
        results = await run_quick_test()
        print("RAG Pipeline Quick Test Results:")
        for test, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {test}: {status}")
    
    asyncio.run(main()) 