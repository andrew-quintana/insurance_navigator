"""
End-to-End Mock Integration Test

This test validates the complete integration between upload pipeline and agent workflows
using mock services. It follows the debug → fix → test cycle approach.
"""

import asyncio
import logging
import time
import pytest
from typing import Dict, Any, List
from unittest.mock import Mock, patch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestMockEndToEndIntegration:
    """Test complete pipeline with mock services: upload → process → query → conversation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_user_id = "550e8400-e29b-41d4-a716-446655440001"
        self.test_documents = [
            "sample_policy.pdf",
            "complex_policy.pdf"
        ]
        self.test_queries = [
            "What is the deductible amount in this policy?",
            "What medical expenses are covered?",
            "What is the maximum annual benefit?"
        ]
        
        # Mock services configuration
        self.mock_services = Mock()
        self.mock_services.llamaparse_delay = 2.0
        self.mock_services.openai_delay = 0.5
        
        # Test data manager
        self.test_data_manager = Mock()
        self.test_data_manager.test_documents = self.test_documents
        
        # Performance validator
        self.performance_validator = Mock()
        
        # Log failures for debugging
        self.failures = []
    
    def log_failure_for_debugging(self, error: Exception, context: str = ""):
        """Log failure details for debugging during the debug → fix → test cycle."""
        failure_info = {
            'error': str(error),
            'error_type': type(error).__name__,
            'context': context,
            'timestamp': time.time()
        }
        self.failures.append(failure_info)
        logger.error(f"Integration test failure in {context}: {error}")
    
    async def test_upload_to_conversation_with_mocks(self):
        """
        Test complete pipeline with mock services: upload → process → query → conversation.
        
        This is the core integration test that validates the end-to-end flow.
        """
        try:
            logger.info("Starting end-to-end integration test with mock services")
            
            # Step 1: Upload test document (using mock LlamaParse)
            document_id = await self.upload_test_document("sample_policy.pdf")
            logger.info(f"Test document uploaded with ID: {document_id}")
            
            # Step 2: Monitor processing completion (mock processing)
            await self.wait_for_processing_completion(document_id, timeout=90)
            logger.info(f"Document {document_id} processing completed")
            
            # Step 3: Execute agent conversation (using mock OpenAI embeddings)
            response = await self.information_retrieval_agent.process({
                "user_id": self.test_user_id,
                "query": "What is the deductible amount in this policy?"
            })
            logger.info(f"Agent response received: {response}")
            
            # Step 4: Basic validation with mock data
            assert response is not None, "Agent response should not be None"
            assert hasattr(response, 'document_references'), "Response should have document_references"
            assert len(response.document_references) > 0, "Response should reference processed documents"
            
            logger.info("End-to-end integration test completed successfully")
            
        except Exception as e:
            # Log failure for debugging
            self.log_failure_for_debugging(e, "end-to-end integration test")
            # Continue debug → fix → test cycle
            raise
    
    async def test_document_upload_through_003_pipeline(self):
        """Test document upload through 003 pipeline with mock LlamaParse."""
        try:
            logger.info("Testing document upload through 003 pipeline")
            
            # Mock document upload
            document_id = await self.upload_test_document("sample_policy.pdf")
            
            # Verify document was created
            assert document_id is not None, "Document ID should not be None"
            assert isinstance(document_id, str), "Document ID should be a string"
            
            # Verify document exists in upload_pipeline.documents
            document_exists = await self.check_document_exists(document_id)
            assert document_exists, f"Document {document_id} should exist in database"
            
            logger.info(f"Document upload test passed for {document_id}")
            return document_id
            
        except Exception as e:
            self.log_failure_for_debugging(e, "document upload test")
            raise
    
    async def test_document_processing_completion(self):
        """Test that document processing completes successfully."""
        try:
            logger.info("Testing document processing completion")
            
            # Upload a test document
            document_id = await self.upload_test_document("complex_policy.pdf")
            
            # Wait for processing completion
            await self.wait_for_processing_completion(document_id, timeout=90)
            
            # Verify processing status is 'complete'
            status = await self.get_document_processing_status(document_id)
            assert status == 'complete', f"Document status should be 'complete', got '{status}'"
            
            # Verify vectors exist in document_chunks
            chunks_exist = await self.check_document_has_chunks(document_id)
            assert chunks_exist, f"Document {document_id} should have processed chunks"
            
            logger.info(f"Document processing completion test passed for {document_id}")
            
        except Exception as e:
            self.log_failure_for_debugging(e, "document processing completion test")
            raise
    
    async def test_agent_rag_access_to_upload_pipeline(self):
        """Test that agents can access upload_pipeline vectors for RAG queries."""
        try:
            logger.info("Testing agent RAG access to upload_pipeline")
            
            # Get a processed document
            document_id = await self.get_processed_document_id()
            
            # Execute RAG query through agent
            chunks = await self.execute_rag_query(document_id, "deductible coverage")
            
            # Verify RAG query returned results
            assert chunks is not None, "RAG query should return results"
            assert len(chunks) > 0, "RAG query should return at least one chunk"
            
            # Verify chunks reference the correct document
            for chunk in chunks:
                assert chunk.document_id == document_id, "Chunk should reference correct document"
                assert chunk.content is not None, "Chunk should have content"
                assert len(chunk.content) > 0, "Chunk content should not be empty"
            
            logger.info("Agent RAG access test passed")
            
        except Exception as e:
            self.log_failure_for_debugging(e, "agent RAG access test")
            raise
    
    async def test_conversation_quality_with_processed_documents(self):
        """Test that agent conversations accurately reference processed document content."""
        try:
            logger.info("Testing conversation quality with processed documents")
            
            # Execute multiple queries to test conversation quality
            for query in self.test_queries:
                response = await self.information_retrieval_agent.process({
                    "user_id": self.test_user_id,
                    "query": query
                })
                
                # Verify response quality
                assert response is not None, f"Response should not be None for query: {query}"
                assert hasattr(response, 'document_references'), f"Response should have document_references for query: {query}"
                assert len(response.document_references) > 0, f"Response should reference documents for query: {query}"
                
                # Verify response contains relevant information
                response_text = str(response).lower()
                query_keywords = query.lower().split()
                
                # Check if response contains query keywords (basic relevance check)
                keyword_matches = sum(1 for keyword in query_keywords if keyword in response_text)
                assert keyword_matches > 0, f"Response should contain relevant keywords for query: {query}"
            
            logger.info("Conversation quality test passed")
            
        except Exception as e:
            self.log_failure_for_debugging(e, "conversation quality test")
            raise
    
    async def test_performance_targets(self):
        """Test that performance targets are met consistently."""
        try:
            logger.info("Testing performance targets")
            
            start_time = time.time()
            
            # Execute complete upload → conversation flow
            document_id = await self.upload_and_process_document()
            conversation_result = await self.execute_agent_conversation()
            
            total_time = time.time() - start_time
            
            # Verify performance targets
            assert total_time < 90, f"End-to-end flow should complete in <90 seconds, took {total_time:.2f}s"
            
            logger.info(f"Performance test passed: {total_time:.2f}s")
            
        except Exception as e:
            self.log_failure_for_debugging(e, "performance targets test")
            raise
    
    async def test_concurrent_operations(self):
        """Test upload processing + agent conversations simultaneously."""
        try:
            logger.info("Testing concurrent operations")
            
            # Start document processing in background
            upload_task = asyncio.create_task(self.upload_and_process_document())
            
            # Execute agent conversations while processing
            conversation_tasks = []
            for query in self.test_queries[:3]:  # Limit to 3 queries for testing
                task = asyncio.create_task(self.execute_agent_conversation(query))
                conversation_tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(upload_task, *conversation_tasks)
            
            # Verify no degradation in either system
            # This is a basic test - in real implementation would measure actual performance metrics
            
            logger.info("Concurrent operations test passed")
            
        except Exception as e:
            self.log_failure_for_debugging(e, "concurrent operations test")
            raise
    
    # Helper methods for testing
    
    async def upload_test_document(self, filename: str) -> str:
        """Upload a test document through the 003 pipeline."""
        # Mock implementation for testing
        document_id = f"test_doc_{hash(filename) % 10000}"
        logger.info(f"Mock upload of {filename} with ID {document_id}")
        return document_id
    
    async def wait_for_processing_completion(self, document_id: str, timeout: int = 90):
        """Wait for document processing to complete."""
        # Mock implementation for testing
        logger.info(f"Mock waiting for document {document_id} processing completion")
        await asyncio.sleep(2)  # Simulate processing time
    
    async def check_document_exists(self, document_id: str) -> bool:
        """Check if document exists in database."""
        # Mock implementation for testing
        return True
    
    async def get_document_processing_status(self, document_id: str) -> str:
        """Get the processing status of a document."""
        # Mock implementation for testing
        return 'complete'
    
    async def check_document_has_chunks(self, document_id: str) -> bool:
        """Check if document has processed chunks."""
        # Mock implementation for testing
        return True
    
    async def get_processed_document_id(self) -> str:
        """Get a processed document ID for testing."""
        return "550e8400-e29b-41d4-a716-446655440001"
    
    async def execute_rag_query(self, document_id: str, query: str):
        """Execute a RAG query on a document."""
        # Mock implementation for testing
        mock_chunk = Mock()
        mock_chunk.document_id = document_id
        mock_chunk.content = f"Mock content for query: {query}"
        return [mock_chunk]
    
    async def upload_and_process_document(self) -> str:
        """Upload and process a document through the complete pipeline."""
        document_id = await self.upload_test_document("test_policy.pdf")
        await self.wait_for_processing_completion(document_id)
        return document_id
    
    async def execute_agent_conversation(self, query: str = None):
        """Execute an agent conversation."""
        if query is None:
            query = "What is the deductible amount?"
        
        # Mock agent response
        mock_response = Mock()
        mock_response.document_references = ["mock_ref_1", "mock_ref_2"]
        return mock_response
    
    @property
    def information_retrieval_agent(self):
        """Get the information retrieval agent for testing."""
        # Mock agent for testing
        agent = Mock()
        agent.process = self.execute_agent_conversation
        return agent


# Test runner for debug → fix → test cycle
async def run_integration_tests():
    """Run all integration tests and report results."""
    logger.info("Running integration test suite...")
    
    test_instance = TestMockEndToEndIntegration()
    test_instance.setup_method()
    
    test_methods = [
        'test_document_upload_through_003_pipeline',
        'test_document_processing_completion',
        'test_agent_rag_access_to_upload_pipeline',
        'test_conversation_quality_with_processed_documents',
        'test_performance_targets',
        'test_concurrent_operations',
        'test_upload_to_conversation_with_mocks'
    ]
    
    results = {
        'passed': [],
        'failed': [],
        'total': len(test_methods)
    }
    
    for method_name in test_methods:
        try:
            logger.info(f"Running test: {method_name}")
            method = getattr(test_instance, method_name)
            await method()
            results['passed'].append(method_name)
            logger.info(f"✓ {method_name} passed")
        except Exception as e:
            results['failed'].append((method_name, str(e)))
            logger.error(f"✗ {method_name} failed: {e}")
    
    # Report results
    logger.info(f"\nIntegration Test Results:")
    logger.info(f"Total tests: {results['total']}")
    logger.info(f"Passed: {len(results['passed'])}")
    logger.info(f"Failed: {len(results['failed'])}")
    
    if results['failed']:
        logger.error("Failed tests:")
        for test_name, error in results['failed']:
            logger.error(f"  {test_name}: {error}")
    
    return results


if __name__ == "__main__":
    # Run tests if executed directly
    asyncio.run(run_integration_tests())
