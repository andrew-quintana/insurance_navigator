#!/usr/bin/env python3
"""
Quick test script for the vector retrieval tool with the specified document ID.
"""

import asyncio
import logging
from agents.common.vector_retrieval_tool import VectorRetrievalTool, VectorFilter, get_document_vectors, get_document_text
from tests.config.rag_test_config import get_test_config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_vector_tool():
    """Test the vector retrieval tool with the configured document ID."""
    
    # Get test configuration
    config = get_test_config()
    doc_id = config.primary_document.document_id
    user_id = config.primary_document.test_user_id
    
    logger.info(f"Testing vector tool with document: {doc_id}")
    logger.info(f"User ID: {user_id}")
    
    # Initialize the tool
    vector_tool = VectorRetrievalTool()
    
    try:
        # Test 1: Get vectors for the document
        logger.info("\n=== Test 1: Get document vectors ===")
        vectors = await vector_tool.get_vectors_by_document(
            document_id=doc_id,
            user_id=user_id,
            source_type="user_document"
        )
        
        if vectors:
            logger.info(f"✓ Found {len(vectors)} vector chunks")
            
            # Show sample vector info
            if len(vectors) > 0:
                sample = vectors[0]
                logger.info(f"  Sample chunk text length: {len(sample.chunk_text)}")
                logger.info(f"  Sample embedding dimensions: {len(sample.content_embedding)}")
                logger.info(f"  Sample chunk index: {sample.chunk_index}")
        else:
            logger.info("✗ No vectors found")
        
        # Test 2: Get combined text content
        logger.info("\n=== Test 2: Get combined text content ===")
        text_content = vector_tool.get_text_content(vectors)
        logger.info(f"Combined text length: {len(text_content)} characters")
        
        if text_content:
            # Show first 200 characters
            preview = text_content[:200] + "..." if len(text_content) > 200 else text_content
            logger.info(f"Text preview: {preview}")
        
        # Test 3: Custom filtering
        logger.info("\n=== Test 3: Custom filtering ===")
        custom_filter = VectorFilter(
            user_id=user_id,
            document_source_type="user_document",
            limit=5
        )
        
        filtered_vectors = await vector_tool.get_vectors_by_filter(custom_filter)
        logger.info(f"Filtered vectors (limit 5): {len(filtered_vectors)}")
        
        # Test 4: Convenience functions
        logger.info("\n=== Test 4: Convenience functions ===")
        
        # Test get_document_vectors function
        convenience_vectors = await get_document_vectors(
            document_id=doc_id,
            user_id=user_id,
            source_type="user_document"
        )
        logger.info(f"Convenience function vectors: {len(convenience_vectors)}")
        
        # Test get_document_text function
        convenience_text = await get_document_text(
            document_id=doc_id,
            user_id=user_id,
            source_type="user_document"
        )
        logger.info(f"Convenience function text length: {len(convenience_text)}")
        
        # Summary
        logger.info("\n=== Summary ===")
        logger.info(f"Document ID: {doc_id}")
        logger.info(f"Total vector chunks: {len(vectors)}")
        logger.info(f"Total text length: {len(text_content)} characters")
        logger.info(f"Tool working: {'✓ YES' if vectors else '✗ NO'}")
        
        return len(vectors) > 0
        
    except Exception as e:
        logger.error(f"Error testing vector tool: {e}")
        return False

if __name__ == "__main__":
    async def main():
        success = await test_vector_tool()
        exit(0 if success else 1)
    
    asyncio.run(main())
