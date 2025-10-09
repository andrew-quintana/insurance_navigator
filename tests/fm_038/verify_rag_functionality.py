#!/usr/bin/env python3
"""
FM-038 RAG Functionality Verification

Quick test to verify that the RAG system works correctly with the threading fix.
"""

import asyncio
import logging
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.tooling.rag.core import RAGTool, RetrievalConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rag_functionality():
    """Test RAG functionality with the threading fix."""
    logger.info("=== FM-038 RAG Functionality Verification ===")
    
    try:
        # Check if OpenAI API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.warning("OPENAI_API_KEY not found - using mock test")
            return await test_mock_rag()
        
        logger.info("OpenAI API key found - testing real RAG functionality")
        
        # Create RAG tool
        config = RetrievalConfig.default()
        config.max_chunks = 3  # Limit for testing
        rag_tool = RAGTool(user_id="test_user", config=config)
        
        # Test query
        test_query = "What are the benefits covered under this insurance plan?"
        logger.info(f"Testing RAG with query: {test_query}")
        
        # Measure performance
        start_time = time.time()
        
        try:
            # This will test the fixed threading implementation
            chunks = await rag_tool.retrieve_chunks_from_text(test_query)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            logger.info(f"RAG operation completed in {processing_time:.2f} seconds")
            logger.info(f"Retrieved {len(chunks)} chunks")
            
            if processing_time > 30:
                logger.warning(f"RAG operation took {processing_time:.2f}s - may indicate timeout issues")
                return False
            
            if len(chunks) > 0:
                logger.info("✅ RAG functionality working correctly")
                logger.info(f"First chunk preview: {chunks[0].content[:100]}...")
                return True
            else:
                logger.info("ℹ️ No chunks retrieved (may be normal if no matching documents)")
                return True
                
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            
            if "timed out" in str(e).lower():
                logger.error(f"❌ RAG operation timed out after {processing_time:.2f}s: {e}")
                return False
            else:
                logger.error(f"❌ RAG operation failed after {processing_time:.2f}s: {e}")
                return False
                
    except Exception as e:
        logger.error(f"Test setup failed: {e}")
        return False

async def test_mock_rag():
    """Test RAG with mock data when API key is not available."""
    logger.info("Testing RAG with mock data")
    
    try:
        # Create RAG tool
        config = RetrievalConfig.default()
        rag_tool = RAGTool(user_id="test_user", config=config)
        
        # Test the embedding generation method directly
        test_text = "test insurance query"
        logger.info(f"Testing embedding generation for: {test_text}")
        
        start_time = time.time()
        
        # This will test the threading implementation
        embedding = await rag_tool._generate_embedding(test_text)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        logger.info(f"Embedding generation completed in {processing_time:.2f} seconds")
        logger.info(f"Generated embedding with {len(embedding)} dimensions")
        
        if processing_time > 30:
            logger.warning(f"Embedding generation took {processing_time:.2f}s - may indicate timeout issues")
            return False
        
        if len(embedding) == 1536:
            logger.info("✅ Embedding generation working correctly")
            return True
        else:
            logger.error(f"❌ Wrong embedding dimensions: {len(embedding)}")
            return False
            
    except Exception as e:
        logger.error(f"Mock RAG test failed: {e}")
        return False

async def main():
    """Main test runner."""
    logger.info("Starting FM-038 RAG functionality verification...")
    
    success = await test_rag_functionality()
    
    if success:
        logger.info("\n🎉 FM-038 RAG Verification: SUCCESS")
        logger.info("The threading fix is working correctly for RAG operations.")
        return True
    else:
        logger.error("\n💥 FM-038 RAG Verification: FAILURE")
        logger.error("The threading fix may need further investigation.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
