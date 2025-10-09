#!/usr/bin/env python3
"""
FM-038 Timeout Fix Verification Test

This test verifies that the 120-second timeout issue has been resolved by:
1. Testing the Communication Agent timeout handling
2. Verifying the post-RAG workflow completes within expected time
3. Confirming proper error handling and fallback responses
"""

import asyncio
import time
import logging
import os
import sys
from typing import Dict, Any

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, project_root)

# Set PYTHONPATH to include the project root
os.environ['PYTHONPATH'] = project_root + ':' + os.environ.get('PYTHONPATH', '')

from agents.patient_navigator.chat_interface import PatientNavigatorChatInterface, ChatMessage
from agents.patient_navigator.output_processing.agent import CommunicationAgent
from agents.patient_navigator.output_processing.types import CommunicationRequest, AgentOutput

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FM038TimeoutFixTest:
    """Test class for verifying FM-038 timeout fix."""
    
    def __init__(self):
        self.test_results = []
        self.start_time = None
    
    def log_test_result(self, test_name: str, success: bool, duration: float, details: str = ""):
        """Log test result with timing information."""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name} - Duration: {duration:.2f}s - {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "duration": duration,
            "details": details
        })
    
    async def test_communication_agent_timeout(self):
        """Test Communication Agent timeout handling."""
        test_name = "Communication Agent Timeout Handling"
        start_time = time.time()
        
        try:
            # Create Communication Agent
            comm_agent = CommunicationAgent()
            
            # Create test request with mock agent output
            agent_output = AgentOutput(
                agent_id="test_agent",
                content="Test content for timeout verification",
                metadata={"test": True}
            )
            
            request = CommunicationRequest(
                agent_outputs=[agent_output],
                user_context={"user_id": "test_user"}
            )
            
            # Test with timeout - should complete within 25 seconds or timeout properly
            logger.info("Testing Communication Agent with timeout handling...")
            
            try:
                response = await asyncio.wait_for(
                    comm_agent.enhance_response(request),
                    timeout=30.0  # 30 second test timeout
                )
                
                duration = time.time() - start_time
                self.log_test_result(
                    test_name, 
                    True, 
                    duration, 
                    f"Response received: {len(response.enhanced_content)} chars"
                )
                return True
                
            except asyncio.TimeoutError:
                duration = time.time() - start_time
                self.log_test_result(
                    test_name, 
                    False, 
                    duration, 
                    "Communication Agent timed out after 30 seconds"
                )
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(
                test_name, 
                False, 
                duration, 
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_chat_interface_timeout(self):
        """Test Chat Interface timeout handling."""
        test_name = "Chat Interface Timeout Handling"
        start_time = time.time()
        
        try:
            # Create Chat Interface
            chat_interface = PatientNavigatorChatInterface()
            
            # Create test message
            message = ChatMessage(
                user_id="test_user",
                content="What is my deductible?",
                timestamp=time.time(),
                message_type="text",
                language="en"
            )
            
            logger.info("Testing Chat Interface with timeout handling...")
            
            try:
                # Test with 60-second timeout (should be enough for normal operation)
                response = await asyncio.wait_for(
                    chat_interface.process_message(message),
                    timeout=60.0  # 60 second test timeout
                )
                
                duration = time.time() - start_time
                self.log_test_result(
                    test_name, 
                    True, 
                    duration, 
                    f"Response received: {len(response.content)} chars"
                )
                return True
                
            except asyncio.TimeoutError:
                duration = time.time() - start_time
                self.log_test_result(
                    test_name, 
                    False, 
                    duration, 
                    "Chat Interface timed out after 60 seconds"
                )
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(
                test_name, 
                False, 
                duration, 
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_post_rag_workflow_logging(self):
        """Test that post-RAG workflow logging is working."""
        test_name = "Post-RAG Workflow Logging"
        start_time = time.time()
        
        try:
            # Create Chat Interface
            chat_interface = PatientNavigatorChatInterface()
            
            # Create test message
            message = ChatMessage(
                user_id="test_user",
                content="What is my deductible?",
                timestamp=time.time(),
                message_type="text",
                language="en"
            )
            
            logger.info("Testing post-RAG workflow logging...")
            
            # Capture logs during processing
            with self.capture_logs() as log_capture:
                try:
                    response = await asyncio.wait_for(
                        chat_interface.process_message(message),
                        timeout=60.0
                    )
                    
                    # Check if expected log messages are present
                    log_content = log_capture.getvalue()
                    expected_logs = [
                        "=== POST-RAG WORKFLOW STARTED ===",
                        "=== POST-RAG WORKFLOW: TWO-STAGE SYNTHESIZER STARTED ===",
                        "=== CALLING COMMUNICATION AGENT ENHANCE_RESPONSE ===",
                        "=== COMMUNICATION AGENT ENHANCE_RESPONSE COMPLETED SUCCESSFULLY ==="
                    ]
                    
                    missing_logs = [log for log in expected_logs if log not in log_content]
                    
                    duration = time.time() - start_time
                    
                    if not missing_logs:
                        self.log_test_result(
                            test_name, 
                            True, 
                            duration, 
                            f"All expected logs present, response: {len(response.content)} chars"
                        )
                        return True
                    else:
                        self.log_test_result(
                            test_name, 
                            False, 
                            duration, 
                            f"Missing logs: {missing_logs}"
                        )
                        return False
                        
                except asyncio.TimeoutError:
                    duration = time.time() - start_time
                    self.log_test_result(
                        test_name, 
                        False, 
                        duration, 
                        "Workflow timed out during logging test"
                    )
                    return False
                    
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(
                test_name, 
                False, 
                duration, 
                f"Exception: {str(e)}"
            )
            return False
    
    def capture_logs(self):
        """Context manager to capture logs during testing."""
        import io
        import contextlib
        
        class LogCapture:
            def __init__(self):
                self.log_capture = io.StringIO()
                self.handler = logging.StreamHandler(self.log_capture)
                self.handler.setLevel(logging.INFO)
                
            def __enter__(self):
                # Add handler to root logger
                logging.getLogger().addHandler(self.handler)
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                # Remove handler from root logger
                logging.getLogger().removeHandler(self.handler)
                
            def getvalue(self):
                return self.log_capture.getvalue()
        
        return LogCapture()
    
    async def run_all_tests(self):
        """Run all timeout fix verification tests."""
        logger.info("🚀 Starting FM-038 Timeout Fix Verification Tests")
        logger.info("=" * 60)
        
        self.start_time = time.time()
        
        # Run tests
        tests = [
            self.test_communication_agent_timeout(),
            self.test_chat_interface_timeout(),
            self.test_post_rag_workflow_logging()
        ]
        
        results = await asyncio.gather(*tests, return_exceptions=True)
        
        # Calculate overall results
        total_duration = time.time() - self.start_time
        passed_tests = sum(1 for result in results if result is True)
        total_tests = len(tests)
        
        logger.info("=" * 60)
        logger.info("📊 FM-038 Timeout Fix Test Results")
        logger.info("=" * 60)
        
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            logger.info(f"{status} {result['test']} - {result['duration']:.2f}s - {result['details']}")
        
        logger.info("=" * 60)
        logger.info(f"📈 Overall Results: {passed_tests}/{total_tests} tests passed")
        logger.info(f"⏱️  Total Duration: {total_duration:.2f}s")
        
        if passed_tests == total_tests:
            logger.info("🎉 All tests passed! FM-038 timeout fix is working correctly.")
            return True
        else:
            logger.error(f"❌ {total_tests - passed_tests} tests failed. FM-038 timeout fix needs attention.")
            return False

async def main():
    """Main test execution function."""
    test_runner = FM038TimeoutFixTest()
    success = await test_runner.run_all_tests()
    
    if success:
        print("\n🎉 FM-038 Timeout Fix Verification: SUCCESS")
        sys.exit(0)
    else:
        print("\n❌ FM-038 Timeout Fix Verification: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
