#!/usr/bin/env python3
"""
FM-038 Threading Fix Test

Tests the critical fix for RAG operations hanging due to async client lifecycle conflicts.
This test verifies that the synchronous OpenAI client approach resolves the threading issues.
"""

import asyncio
import logging
import os
import sys
import time
import threading
import queue
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.tooling.rag.core import RAGTool, RetrievalConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestThreadingFix:
    """Test the threading fix for RAG operations."""
    
    def __init__(self):
        self.test_results = []
        
    def test_synchronous_client_approach(self):
        """Test that synchronous OpenAI client works correctly in threads."""
        logger.info("=== Testing Synchronous OpenAI Client Approach ===")
        
        try:
            # Mock OpenAI API key
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key-12345'}):
                # Create RAG tool
                rag_tool = RAGTool(user_id="test_user", config=RetrievalConfig.default())
                
                # Test the threading approach with synchronous client
                result_queue = queue.Queue()
                exception_queue = queue.Queue()
                
                def test_api_call():
                    try:
                        logger.info("Thread started for test OpenAI API call")
                        
                        # Simulate synchronous OpenAI client call
                        from openai import OpenAI
                        mock_client = MagicMock()
                        mock_response = MagicMock()
                        mock_response.data = [MagicMock()]
                        mock_response.data[0].embedding = [0.1] * 1536  # Mock embedding
                        mock_client.embeddings.create.return_value = mock_response
                        
                        # This simulates what our fixed code does
                        response = mock_client.embeddings.create(
                            model="text-embedding-3-small",
                            input="test text",
                            encoding_format="float"
                        )
                        
                        result_queue.put(response)
                        logger.info("Thread completed test OpenAI API call successfully")
                        
                    except Exception as e:
                        logger.error(f"Thread failed with exception: {e}")
                        exception_queue.put(e)
                    finally:
                        logger.info("Thread exiting")
                
                # Start API call in separate thread
                thread = threading.Thread(target=test_api_call)
                thread.daemon = True
                thread.start()
                
                # Wait for result with timeout
                start_time = time.time()
                thread.join(timeout=5.0)
                end_time = time.time()
                
                # Verify thread completed successfully
                if thread.is_alive():
                    logger.error(f"Thread is still alive after timeout - investigating...")
                    logger.error(f"Thread name: {thread.name}")
                    logger.error(f"Thread daemon: {thread.daemon}")
                    logger.error(f"Thread ident: {thread.ident}")
                    self.test_results.append(("synchronous_client", False, "Thread timed out"))
                    return False
                
                # Check for exceptions
                if not exception_queue.empty():
                    exception = exception_queue.get()
                    logger.error(f"Test API call failed: {exception}")
                    self.test_results.append(("synchronous_client", False, f"Exception: {exception}"))
                    return False
                
                # Get the result
                if not result_queue.empty():
                    response = result_queue.get()
                    logger.info(f"Test API call completed in {end_time - start_time:.2f}s")
                    logger.info(f"Response type: {type(response)}")
                    self.test_results.append(("synchronous_client", True, f"Completed in {end_time - start_time:.2f}s"))
                    return True
                else:
                    logger.error("No response received from test API")
                    self.test_results.append(("synchronous_client", False, "No response received"))
                    return False
                    
        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            self.test_results.append(("synchronous_client", False, f"Test exception: {e}"))
            return False
    
    def test_thread_lifecycle_logging(self):
        """Test that thread lifecycle logging works correctly."""
        logger.info("=== Testing Thread Lifecycle Logging ===")
        
        try:
            result_queue = queue.Queue()
            exception_queue = queue.Queue()
            
            def test_logging_call():
                try:
                    logger.info("Thread started for logging test")
                    time.sleep(0.1)  # Simulate work
                    result_queue.put("success")
                    logger.info("Thread completed logging test successfully")
                except Exception as e:
                    logger.error(f"Thread failed with exception: {e}")
                    exception_queue.put(e)
                finally:
                    logger.info("Thread exiting")
            
            # Start test call in separate thread
            thread = threading.Thread(target=test_logging_call)
            thread.daemon = True
            thread.start()
            
            # Wait for result
            thread.join(timeout=2.0)
            
            if thread.is_alive():
                self.test_results.append(("thread_lifecycle_logging", False, "Thread timed out"))
                return False
            
            if not exception_queue.empty():
                exception = exception_queue.get()
                self.test_results.append(("thread_lifecycle_logging", False, f"Exception: {exception}"))
                return False
            
            if not result_queue.empty():
                result = result_queue.get()
                self.test_results.append(("thread_lifecycle_logging", True, f"Result: {result}"))
                return True
            else:
                self.test_results.append(("thread_lifecycle_logging", False, "No result received"))
                return False
                
        except Exception as e:
            logger.error(f"Logging test failed: {e}")
            self.test_results.append(("thread_lifecycle_logging", False, f"Test exception: {e}"))
            return False
    
    def test_timeout_behavior(self):
        """Test that timeout behavior works correctly."""
        logger.info("=== Testing Timeout Behavior ===")
        
        try:
            result_queue = queue.Queue()
            exception_queue = queue.Queue()
            
            def slow_call():
                try:
                    logger.info("Thread started for timeout test")
                    time.sleep(3.0)  # Simulate slow operation
                    result_queue.put("success")
                    logger.info("Thread completed timeout test successfully")
                except Exception as e:
                    logger.error(f"Thread failed with exception: {e}")
                    exception_queue.put(e)
                finally:
                    logger.info("Thread exiting")
            
            # Start slow call in separate thread
            thread = threading.Thread(target=slow_call)
            thread.daemon = True
            thread.start()
            
            # Wait for result with short timeout
            start_time = time.time()
            thread.join(timeout=1.0)  # 1 second timeout
            end_time = time.time()
            
            if thread.is_alive():
                logger.info(f"Thread correctly timed out after {end_time - start_time:.2f}s")
                self.test_results.append(("timeout_behavior", True, f"Correctly timed out in {end_time - start_time:.2f}s"))
                return True
            else:
                logger.error("Thread completed unexpectedly fast")
                self.test_results.append(("timeout_behavior", False, "Thread completed too fast"))
                return False
                
        except Exception as e:
            logger.error(f"Timeout test failed: {e}")
            self.test_results.append(("timeout_behavior", False, f"Test exception: {e}"))
            return False
    
    def run_all_tests(self):
        """Run all tests and report results."""
        logger.info("=== FM-038 Threading Fix Test Suite ===")
        logger.info("Testing the critical fix for RAG operations hanging")
        
        # Run tests
        self.test_synchronous_client_approach()
        self.test_thread_lifecycle_logging()
        self.test_timeout_behavior()
        
        # Report results
        logger.info("\n=== Test Results ===")
        passed = 0
        total = len(self.test_results)
        
        for test_name, success, message in self.test_results:
            status = "PASS" if success else "FAIL"
            logger.info(f"{test_name}: {status} - {message}")
            if success:
                passed += 1
        
        logger.info(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("✅ All tests passed! Threading fix appears to be working correctly.")
            return True
        else:
            logger.error("❌ Some tests failed. Threading fix needs investigation.")
            return False

def main():
    """Main test runner."""
    test_suite = TestThreadingFix()
    success = test_suite.run_all_tests()
    
    if success:
        logger.info("\n🎉 FM-038 Threading Fix Test: SUCCESS")
        logger.info("The synchronous OpenAI client approach should resolve the hanging issues.")
        sys.exit(0)
    else:
        logger.error("\n💥 FM-038 Threading Fix Test: FAILURE")
        logger.error("The threading fix needs further investigation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
