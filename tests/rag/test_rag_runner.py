"""
RAG Test Runner

Simple test runner for validating RAG pipeline functionality.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional

# Test configuration
from tests.config.rag_test_config import get_test_config, update_document_id

# Services  
from db.services.document_service import DocumentService
from agents.common.vector_retrieval_tool import VectorRetrievalTool, get_document_vectors

logger = logging.getLogger(__name__)

class RAGTestRunner:
    """Test runner for RAG pipeline validation."""
    
    def __init__(self, document_id: Optional[str] = None):
        """Initialize test runner with optional document ID override."""
        if document_id:
            self.config = update_document_id(document_id)
        else:
            self.config = get_test_config()
        
        self.document_service = DocumentService()
        self.vector_tool = VectorRetrievalTool()
        
        logger.info(f"RAG Test Runner initialized for document: {self.config.primary_document.document_id}")
    
    async def test_document_exists(self) -> bool:
        """Test that the document exists and is accessible."""
        try:
            doc_id = self.config.primary_document.document_id
            user_id = self.config.primary_document.test_user_id
            
            status = await self.document_service.get_document_status(doc_id, user_id)
            
            if status and status.get("status") != "not_found":
                logger.info(f"✓ Document {doc_id} exists with status: {status.get('status')}")
                return True
            else:
                logger.error(f"✗ Document {doc_id} not found or not accessible")
                return False
                
        except Exception as e:
            logger.error(f"✗ Document existence test failed: {e}")
            return False
    
    async def test_document_vectorization(self) -> bool:
        """Test that the document has been vectorized."""
        try:
            doc_id = self.config.primary_document.document_id
            user_id = self.config.primary_document.test_user_id
            
            # Test vector retrieval to verify embeddings exist
            vectors = await self.vector_tool.get_vectors_by_document(
                document_id=doc_id,
                user_id=user_id,
                source_type="user_document"
            )
            
            if vectors and len(vectors) > 0:
                logger.info(f"✓ Document {doc_id} has {len(vectors)} vector chunks")
                return True
            else:
                logger.error(f"✗ No vector chunks found for document {doc_id}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Vectorization test failed: {e}")
            return False
    
    async def test_vector_retrieval(self) -> bool:
        """Test vector retrieval functionality."""
        try:
            user_id = self.config.primary_document.test_user_id
            doc_id = self.config.primary_document.document_id
            
            start_time = time.time()
            vectors = await self.vector_tool.get_vectors_by_document(
                document_id=doc_id,
                user_id=user_id,
                source_type="user_document"
            )
            retrieval_time = time.time() - start_time
            
            if vectors is not None:
                # Test text extraction
                text_content = self.vector_tool.get_text_content(vectors)
                logger.info(f"✓ Vector retrieval returned {len(vectors)} chunks in {retrieval_time:.3f}s")
                logger.info(f"  Combined text length: {len(text_content)} characters")
                return True
            else:
                logger.error(f"✗ Vector retrieval failed")
                return False
                
        except Exception as e:
            logger.error(f"✗ Vector retrieval test failed: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results."""
        logger.info("="*50)
        logger.info("Starting RAG Pipeline Tests")
        logger.info(f"Document ID: {self.config.primary_document.document_id}")
        logger.info(f"User ID: {self.config.primary_document.test_user_id}")
        logger.info("="*50)
        
        results = {}
        
        # Run tests sequentially
        results["document_exists"] = await self.test_document_exists()
        results["document_vectorized"] = await self.test_document_vectorization()
        results["vector_retrieval"] = await self.test_vector_retrieval()
        
        # Summary
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        logger.info("="*50)
        logger.info(f"Test Results: {passed}/{total} tests passed")
        
        for test_name, passed in results.items():
            status = "PASS" if passed else "FAIL"
            logger.info(f"  {test_name}: {status}")
        
        logger.info("="*50)
        
        return results

# Convenience functions
async def test_current_document() -> Dict[str, bool]:
    """Test the currently configured document."""
    runner = RAGTestRunner()
    return await runner.run_all_tests()

async def test_document(document_id: str) -> Dict[str, bool]:
    """Test a specific document by ID."""
    runner = RAGTestRunner(document_id=document_id)
    return await runner.run_all_tests()

# CLI interface
if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) > 1:
            # Test specific document ID
            doc_id = sys.argv[1]
            results = await test_document(doc_id)
        else:
            # Test current document
            results = await test_current_document()
        
        # Exit with error code if any tests failed
        failed_tests = [name for name, passed in results.items() if not passed]
        if failed_tests:
            print(f"Failed tests: {', '.join(failed_tests)}")
            exit(1)
        else:
            print("All tests passed!")
            exit(0)
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
 