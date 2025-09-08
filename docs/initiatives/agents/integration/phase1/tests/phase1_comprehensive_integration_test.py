#!/usr/bin/env python3
"""
Phase 1 Comprehensive Integration Test
Tests the complete agentic workflow with real LLMs and embeddings using test insurance document.

This test validates:
1. Chat endpoint functionality with full output
2. Agent RAG integration with real document
3. End-to-end workflow: input → agents → output
4. Performance meets Phase 1 success criteria
5. Quality assessment of responses

Uses test_insurance_document.pdf for realistic testing.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import traceback

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from agents.patient_navigator.chat_interface import PatientNavigatorChatInterface, ChatMessage, ChatResponse
from agents.patient_navigator.input_processing.workflow import InputProcessingWorkflow
from agents.patient_navigator.output_processing.workflow import OutputWorkflow
from agents.patient_navigator.supervisor.workflow import SupervisorWorkflow
from agents.patient_navigator.information_retrieval.agent import InformationRetrievalAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase1IntegrationTester:
    """Comprehensive Phase 1 integration testing with real services."""
    
    def __init__(self):
        self.test_results = []
        self.performance_metrics = {}
        self.quality_metrics = {}
        self.test_document_path = "examples/test_insurance_document.pdf"
        
        # Test queries designed to test different aspects
        self.test_queries = [
            {
                "query": "What does my insurance cover for doctor visits?",
                "expected_workflows": ["information_retrieval"],
                "language": "en",
                "test_type": "basic_coverage"
            },
            {
                "query": "¿Cuáles son mis beneficios de medicamentos recetados?",
                "expected_workflows": ["information_retrieval"],
                "language": "es", 
                "test_type": "multilingual_coverage"
            },
            {
                "query": "How can I optimize my healthcare costs with my current plan?",
                "expected_workflows": ["information_retrieval", "strategy"],
                "language": "en",
                "test_type": "strategy_planning"
            },
            {
                "query": "What specialists are covered under my plan?",
                "expected_workflows": ["information_retrieval"],
                "language": "en",
                "test_type": "specialist_coverage"
            },
            {
                "query": "I need help understanding my deductible and out-of-pocket maximum",
                "expected_workflows": ["information_retrieval"],
                "language": "en",
                "test_type": "financial_terms"
            }
        ]
        
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all Phase 1 integration tests."""
        logger.info("🚀 Starting Phase 1 Comprehensive Integration Testing")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        try:
            # Test 1: Chat Interface Initialization
            await self._test_chat_interface_initialization()
            
            # Test 2: Individual Component Testing
            await self._test_individual_components()
            
            # Test 3: End-to-End Workflow Testing
            await self._test_end_to_end_workflows()
            
            # Test 4: Performance Testing
            await self._test_performance_requirements()
            
            # Test 5: Quality Assessment
            await self._test_response_quality()
            
            # Test 6: Error Handling
            await self._test_error_handling()
            
            # Test 7: Multilingual Support
            await self._test_multilingual_support()
            
            total_time = time.time() - start_time
            
            # Generate comprehensive report
            report = self._generate_comprehensive_report(total_time)
            
            logger.info("✅ Phase 1 Integration Testing Complete")
            logger.info(f"Total testing time: {total_time:.2f} seconds")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Phase 1 Integration Testing Failed: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "test_results": self.test_results
            }
    
    async def _test_chat_interface_initialization(self):
        """Test 1: Chat Interface Initialization with Real Services."""
        logger.info("🔧 Test 1: Chat Interface Initialization")
        
        start_time = time.time()
        
        try:
            # Initialize chat interface with real services (no mocks)
            chat_interface = PatientNavigatorChatInterface()
            
            # Verify all components are initialized
            assert chat_interface.input_processing_workflow is not None
            assert chat_interface.supervisor_workflow is not None
            assert chat_interface.information_retrieval_agent is not None
            assert chat_interface.communication_agent is not None
            assert chat_interface.output_workflow is not None
            
            init_time = time.time() - start_time
            
            self.test_results.append({
                "test_name": "chat_interface_initialization",
                "status": "passed",
                "duration": init_time,
                "details": {
                    "components_initialized": 5,
                    "mock_mode": False
                }
            })
            
            logger.info(f"✅ Chat interface initialized successfully in {init_time:.2f}s")
            
        except Exception as e:
            self.test_results.append({
                "test_name": "chat_interface_initialization",
                "status": "failed",
                "duration": time.time() - start_time,
                "error": str(e)
            })
            logger.error(f"❌ Chat interface initialization failed: {str(e)}")
            raise
    
    async def _test_individual_components(self):
        """Test 2: Individual Component Testing."""
        logger.info("🔧 Test 2: Individual Component Testing")
        
        # Test Input Processing Workflow
        await self._test_input_processing()
        
        # Test Supervisor Workflow
        await self._test_supervisor_workflow()
        
        # Test Information Retrieval Agent
        await self._test_information_retrieval_agent()
        
        # Test Output Processing Workflow
        await self._test_output_processing()
    
    async def _test_input_processing(self):
        """Test input processing workflow."""
        logger.info("  📝 Testing Input Processing Workflow")
        
        start_time = time.time()
        
        try:
            from agents.patient_navigator.input_processing.types import UserContext
            
            workflow = InputProcessingWorkflow()
            
            # Test with English text
            user_context = UserContext(
                user_id="test_user_001",
                conversation_history=[],
                language_preference="en",
                domain_context="insurance"
            )
            
            result = await workflow.process_input(
                "What does my insurance cover for doctor visits?",
                user_context
            )
            
            assert result is not None
            assert hasattr(result, 'prompt_text')
            assert len(result.prompt_text) > 0
            
            processing_time = time.time() - start_time
            
            self.test_results.append({
                "test_name": "input_processing_workflow",
                "status": "passed",
                "duration": processing_time,
                "details": {
                    "prompt_generated": True,
                    "prompt_length": len(result.prompt_text)
                }
            })
            
            logger.info(f"  ✅ Input processing completed in {processing_time:.2f}s")
            
        except Exception as e:
            self.test_results.append({
                "test_name": "input_processing_workflow",
                "status": "failed",
                "duration": time.time() - start_time,
                "error": str(e)
            })
            logger.error(f"  ❌ Input processing failed: {str(e)}")
            raise
    
    async def _test_supervisor_workflow(self):
        """Test supervisor workflow."""
        logger.info("  🎯 Testing Supervisor Workflow")
        
        start_time = time.time()
        
        try:
            from agents.patient_navigator.supervisor.models import SupervisorWorkflowInput
            
            workflow = SupervisorWorkflow(use_mock=False)
            
            input_data = SupervisorWorkflowInput(
                user_query="What does my insurance cover for doctor visits?",
                user_id="test_user_001",
                workflow_context={"test": True}
            )
            
            result = await workflow.execute(input_data)
            
            assert result is not None
            assert hasattr(result, 'routing_decision')
            assert hasattr(result, 'prescribed_workflows')
            assert len(result.prescribed_workflows) > 0
            
            processing_time = time.time() - start_time
            
            self.test_results.append({
                "test_name": "supervisor_workflow",
                "status": "passed",
                "duration": processing_time,
                "details": {
                    "routing_decision": result.routing_decision,
                    "prescribed_workflows": [w.value for w in result.prescribed_workflows],
                    "confidence_score": result.confidence_score
                }
            })
            
            logger.info(f"  ✅ Supervisor workflow completed in {processing_time:.2f}s")
            
        except Exception as e:
            self.test_results.append({
                "test_name": "supervisor_workflow",
                "status": "failed",
                "duration": time.time() - start_time,
                "error": str(e)
            })
            logger.error(f"  ❌ Supervisor workflow failed: {str(e)}")
            raise
    
    async def _test_information_retrieval_agent(self):
        """Test information retrieval agent with real RAG."""
        logger.info("  🔍 Testing Information Retrieval Agent")
        
        start_time = time.time()
        
        try:
            from agents.patient_navigator.information_retrieval.models import InformationRetrievalInput
            
            agent = InformationRetrievalAgent(use_mock=False)
            
            input_data = InformationRetrievalInput(
                user_query="What does my insurance cover for doctor visits?",
                user_id="test_user_001",
                workflow_context={"test": True}
            )
            
            result = await agent.retrieve_information(input_data)
            
            assert result is not None
            assert hasattr(result, 'direct_answer')
            assert hasattr(result, 'expert_reframe')
            assert hasattr(result, 'key_points')
            assert hasattr(result, 'confidence_score')
            assert hasattr(result, 'source_chunks')
            
            # Ensure we have a meaningful response
            assert len(result.direct_answer) > 10
            assert len(result.key_points) > 0
            assert 0.0 <= result.confidence_score <= 1.0
            
            processing_time = time.time() - start_time
            
            self.test_results.append({
                "test_name": "information_retrieval_agent",
                "status": "passed",
                "duration": processing_time,
                "details": {
                    "response_length": len(result.direct_answer),
                    "key_points_count": len(result.key_points),
                    "confidence_score": result.confidence_score,
                    "source_chunks_count": len(result.source_chunks)
                }
            })
            
            logger.info(f"  ✅ Information retrieval completed in {processing_time:.2f}s")
            logger.info(f"  📊 Response: {result.direct_answer[:100]}...")
            
        except Exception as e:
            self.test_results.append({
                "test_name": "information_retrieval_agent",
                "status": "failed",
                "duration": time.time() - start_time,
                "error": str(e)
            })
            logger.error(f"  ❌ Information retrieval failed: {str(e)}")
            raise
    
    async def _test_output_processing(self):
        """Test output processing workflow."""
        logger.info("  📤 Testing Output Processing Workflow")
        
        start_time = time.time()
        
        try:
            from agents.patient_navigator.output_processing.types import CommunicationRequest, AgentOutput
            
            workflow = OutputWorkflow()
            
            # Create mock agent output
            agent_output = AgentOutput(
                agent_id="information_retrieval",
                content="Your insurance covers doctor visits with a $25 copay for primary care.",
                metadata={"confidence": 0.85}
            )
            
            request = CommunicationRequest(
                agent_outputs=[agent_output],
                user_context={"user_id": "test_user_001"}
            )
            
            result = await workflow.process_request(request)
            
            assert result is not None
            assert hasattr(result, 'enhanced_content')
            assert hasattr(result, 'processing_time')
            assert len(result.enhanced_content) > 0
            
            processing_time = time.time() - start_time
            
            self.test_results.append({
                "test_name": "output_processing_workflow",
                "status": "passed",
                "duration": processing_time,
                "details": {
                    "enhanced_content_length": len(result.enhanced_content),
                    "processing_time": result.processing_time
                }
            })
            
            logger.info(f"  ✅ Output processing completed in {processing_time:.2f}s")
            
        except Exception as e:
            self.test_results.append({
                "test_name": "output_processing_workflow",
                "status": "failed",
                "duration": time.time() - start_time,
                "error": str(e)
            })
            logger.error(f"  ❌ Output processing failed: {str(e)}")
            raise
    
    async def _test_end_to_end_workflows(self):
        """Test 3: End-to-End Workflow Testing."""
        logger.info("🔧 Test 3: End-to-End Workflow Testing")
        
        for i, test_case in enumerate(self.test_queries):
            logger.info(f"  🧪 Test Case {i+1}: {test_case['test_type']}")
            
            start_time = time.time()
            
            try:
                # Create chat message
                message = ChatMessage(
                    user_id="test_user_001",
                    content=test_case["query"],
                    timestamp=time.time(),
                    message_type="text",
                    language=test_case["language"],
                    metadata={"test_case": test_case["test_type"]}
                )
                
                # Initialize chat interface
                chat_interface = PatientNavigatorChatInterface()
                
                # Process message through complete workflow
                response = await chat_interface.process_message(message)
                
                # Validate response
                assert response is not None
                assert hasattr(response, 'content')
                assert hasattr(response, 'agent_sources')
                assert hasattr(response, 'confidence')
                assert hasattr(response, 'processing_time')
                
                # Ensure we have meaningful content
                assert len(response.content) > 20, f"Response too short: {response.content}"
                assert response.confidence > 0.0
                assert response.processing_time > 0.0
                
                processing_time = time.time() - start_time
                
                # Log full response for analysis
                logger.info(f"  📝 Full Response: {response.content}")
                logger.info(f"  🎯 Agent Sources: {response.agent_sources}")
                logger.info(f"  📊 Confidence: {response.confidence:.2f}")
                logger.info(f"  ⏱️ Processing Time: {response.processing_time:.2f}s")
                
                self.test_results.append({
                    "test_name": f"end_to_end_{test_case['test_type']}",
                    "status": "passed",
                    "duration": processing_time,
                    "details": {
                        "query": test_case["query"],
                        "response_length": len(response.content),
                        "confidence": response.confidence,
                        "processing_time": response.processing_time,
                        "agent_sources": response.agent_sources,
                        "full_response": response.content
                    }
                })
                
                logger.info(f"  ✅ End-to-end test {i+1} completed in {processing_time:.2f}s")
                
            except Exception as e:
                self.test_results.append({
                    "test_name": f"end_to_end_{test_case['test_type']}",
                    "status": "failed",
                    "duration": time.time() - start_time,
                    "error": str(e),
                    "query": test_case["query"]
                })
                logger.error(f"  ❌ End-to-end test {i+1} failed: {str(e)}")
                # Continue with other tests
                continue
    
    async def _test_performance_requirements(self):
        """Test 4: Performance Requirements Testing."""
        logger.info("🔧 Test 4: Performance Requirements Testing")
        
        # Test response time requirements
        await self._test_response_time_requirements()
        
        # Test throughput requirements
        await self._test_throughput_requirements()
    
    async def _test_response_time_requirements(self):
        """Test response time meets Phase 1 requirements."""
        logger.info("  ⏱️ Testing Response Time Requirements")
        
        start_time = time.time()
        
        try:
            # Run multiple queries to get average response time
            response_times = []
            chat_interface = PatientNavigatorChatInterface()
            
            for i in range(5):  # Test with 5 queries
                query_start = time.time()
                
                message = ChatMessage(
                    user_id=f"perf_test_user_{i}",
                    content="What does my insurance cover for doctor visits?",
                    timestamp=time.time(),
                    message_type="text",
                    language="en"
                )
                
                response = await chat_interface.process_message(message)
                query_time = time.time() - query_start
                response_times.append(query_time)
                
                logger.info(f"    Query {i+1} response time: {query_time:.2f}s")
            
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            # Phase 1 success criteria: < 5 seconds for typical queries
            meets_requirements = avg_response_time < 5.0 and max_response_time < 10.0
            
            self.test_results.append({
                "test_name": "response_time_requirements",
                "status": "passed" if meets_requirements else "failed",
                "duration": time.time() - start_time,
                "details": {
                    "avg_response_time": avg_response_time,
                    "max_response_time": max_response_time,
                    "meets_5s_requirement": avg_response_time < 5.0,
                    "meets_10s_max": max_response_time < 10.0,
                    "individual_times": response_times
                }
            })
            
            if meets_requirements:
                logger.info(f"  ✅ Response time requirements met: avg={avg_response_time:.2f}s, max={max_response_time:.2f}s")
            else:
                logger.warning(f"  ⚠️ Response time requirements not met: avg={avg_response_time:.2f}s, max={max_response_time:.2f}s")
            
        except Exception as e:
            self.test_results.append({
                "test_name": "response_time_requirements",
                "status": "failed",
                "duration": time.time() - start_time,
                "error": str(e)
            })
            logger.error(f"  ❌ Response time testing failed: {str(e)}")
    
    async def _test_throughput_requirements(self):
        """Test throughput requirements."""
        logger.info("  🔄 Testing Throughput Requirements")
        
        start_time = time.time()
        
        try:
            # Test concurrent requests
            chat_interface = PatientNavigatorChatInterface()
            
            async def single_request(user_id: str):
                message = ChatMessage(
                    user_id=user_id,
                    content="What does my insurance cover for doctor visits?",
                    timestamp=time.time(),
                    message_type="text",
                    language="en"
                )
                return await chat_interface.process_message(message)
            
            # Run 3 concurrent requests
            concurrent_start = time.time()
            tasks = [single_request(f"concurrent_user_{i}") for i in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            concurrent_time = time.time() - concurrent_start
            
            successful_requests = sum(1 for r in results if not isinstance(r, Exception))
            
            self.test_results.append({
                "test_name": "throughput_requirements",
                "status": "passed" if successful_requests >= 2 else "failed",
                "duration": time.time() - start_time,
                "details": {
                    "concurrent_requests": 3,
                    "successful_requests": successful_requests,
                    "concurrent_time": concurrent_time,
                    "requests_per_second": 3 / concurrent_time
                }
            })
            
            logger.info(f"  ✅ Throughput test: {successful_requests}/3 requests successful in {concurrent_time:.2f}s")
            
        except Exception as e:
            self.test_results.append({
                "test_name": "throughput_requirements",
                "status": "failed",
                "duration": time.time() - start_time,
                "error": str(e)
            })
            logger.error(f"  ❌ Throughput testing failed: {str(e)}")
    
    async def _test_response_quality(self):
        """Test 5: Response Quality Assessment."""
        logger.info("🔧 Test 5: Response Quality Assessment")
        
        start_time = time.time()
        
        try:
            chat_interface = PatientNavigatorChatInterface()
            
            # Test with a complex query that should generate high-quality response
            message = ChatMessage(
                user_id="quality_test_user",
                content="I need help understanding my insurance benefits for both primary care and specialist visits, including copays and deductibles",
                timestamp=time.time(),
                message_type="text",
                language="en"
            )
            
            response = await chat_interface.process_message(message)
            
            # Assess response quality
            quality_metrics = self._assess_response_quality(response)
            
            self.test_results.append({
                "test_name": "response_quality_assessment",
                "status": "passed" if quality_metrics["overall_score"] > 0.7 else "failed",
                "duration": time.time() - start_time,
                "details": quality_metrics
            })
            
            logger.info(f"  📊 Quality Assessment: {quality_metrics['overall_score']:.2f}/1.0")
            logger.info(f"  📝 Response: {response.content[:200]}...")
            
        except Exception as e:
            self.test_results.append({
                "test_name": "response_quality_assessment",
                "status": "failed",
                "duration": time.time() - start_time,
                "error": str(e)
            })
            logger.error(f"  ❌ Quality assessment failed: {str(e)}")
    
    def _assess_response_quality(self, response: ChatResponse) -> Dict[str, Any]:
        """Assess the quality of a response."""
        content = response.content
        
        # Length assessment (should be substantial)
        length_score = min(len(content) / 100, 1.0)  # Normalize to 0-1
        
        # Confidence assessment
        confidence_score = response.confidence
        
        # Completeness assessment (look for key elements)
        completeness_indicators = [
            "insurance", "coverage", "copay", "deductible", "benefits", "plan"
        ]
        completeness_score = sum(1 for indicator in completeness_indicators if indicator.lower() in content.lower()) / len(completeness_indicators)
        
        # Clarity assessment (sentence structure)
        sentences = content.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        clarity_score = min(avg_sentence_length / 15, 1.0)  # Optimal around 15 words per sentence
        
        # Overall score
        overall_score = (length_score + confidence_score + completeness_score + clarity_score) / 4
        
        return {
            "overall_score": overall_score,
            "length_score": length_score,
            "confidence_score": confidence_score,
            "completeness_score": completeness_score,
            "clarity_score": clarity_score,
            "response_length": len(content),
            "sentence_count": len(sentences),
            "avg_sentence_length": avg_sentence_length
        }
    
    async def _test_error_handling(self):
        """Test 6: Error Handling."""
        logger.info("🔧 Test 6: Error Handling")
        
        start_time = time.time()
        
        try:
            chat_interface = PatientNavigatorChatInterface()
            
            # Test with empty message
            empty_message = ChatMessage(
                user_id="error_test_user",
                content="",
                timestamp=time.time(),
                message_type="text",
                language="en"
            )
            
            try:
                response = await chat_interface.process_message(empty_message)
                # Should handle gracefully
                assert response is not None
                error_handled = True
            except Exception:
                error_handled = False
            
            # Test with very long message
            long_message = ChatMessage(
                user_id="error_test_user",
                content="A" * 10000,  # Very long message
                timestamp=time.time(),
                message_type="text",
                language="en"
            )
            
            try:
                response = await chat_interface.process_message(long_message)
                # Should handle gracefully
                assert response is not None
                long_message_handled = True
            except Exception:
                long_message_handled = False
            
            self.test_results.append({
                "test_name": "error_handling",
                "status": "passed" if error_handled and long_message_handled else "failed",
                "duration": time.time() - start_time,
                "details": {
                    "empty_message_handled": error_handled,
                    "long_message_handled": long_message_handled
                }
            })
            
            logger.info(f"  ✅ Error handling: empty={error_handled}, long={long_message_handled}")
            
        except Exception as e:
            self.test_results.append({
                "test_name": "error_handling",
                "status": "failed",
                "duration": time.time() - start_time,
                "error": str(e)
            })
            logger.error(f"  ❌ Error handling test failed: {str(e)}")
    
    async def _test_multilingual_support(self):
        """Test 7: Multilingual Support."""
        logger.info("🔧 Test 7: Multilingual Support")
        
        start_time = time.time()
        
        try:
            chat_interface = PatientNavigatorChatInterface()
            
            # Test Spanish query
            spanish_message = ChatMessage(
                user_id="multilingual_test_user",
                content="¿Cuáles son mis beneficios de medicamentos recetados?",
                timestamp=time.time(),
                message_type="text",
                language="es"
            )
            
            response = await chat_interface.process_message(spanish_message)
            
            # Should get a meaningful response
            assert response is not None
            assert len(response.content) > 20
            
            self.test_results.append({
                "test_name": "multilingual_support",
                "status": "passed",
                "duration": time.time() - start_time,
                "details": {
                    "spanish_query_handled": True,
                    "response_length": len(response.content),
                    "confidence": response.confidence
                }
            })
            
            logger.info(f"  ✅ Multilingual support: Spanish query handled")
            logger.info(f"  📝 Spanish Response: {response.content[:200]}...")
            
        except Exception as e:
            self.test_results.append({
                "test_name": "multilingual_support",
                "status": "failed",
                "duration": time.time() - start_time,
                "error": str(e)
            })
            logger.error(f"  ❌ Multilingual support test failed: {str(e)}")
    
    def _generate_comprehensive_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        
        # Calculate summary statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["status"] == "passed")
        failed_tests = total_tests - passed_tests
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        # Calculate performance metrics
        avg_response_time = sum(r["duration"] for r in self.test_results if "duration" in r) / len([r for r in self.test_results if "duration" in r]) if self.test_results else 0
        
        # Phase 1 Success Criteria Assessment
        meets_performance = avg_response_time < 5.0
        meets_quality = success_rate >= 0.8
        meets_functionality = passed_tests >= 5  # At least 5 core tests must pass
        
        overall_status = "PASSED" if meets_performance and meets_quality and meets_functionality else "FAILED"
        
        report = {
            "phase1_integration_test_report": {
                "timestamp": datetime.now().isoformat(),
                "overall_status": overall_status,
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": success_rate,
                    "total_testing_time": total_time
                },
                "performance_metrics": {
                    "avg_response_time": avg_response_time,
                    "meets_5s_requirement": meets_performance,
                    "performance_status": "PASSED" if meets_performance else "FAILED"
                },
                "quality_metrics": {
                    "success_rate": success_rate,
                    "meets_80pct_requirement": meets_quality,
                    "quality_status": "PASSED" if meets_quality else "FAILED"
                },
                "functionality_metrics": {
                    "core_tests_passed": passed_tests,
                    "meets_minimum_requirement": meets_functionality,
                    "functionality_status": "PASSED" if meets_functionality else "FAILED"
                },
                "phase1_success_criteria": {
                    "chat_endpoint_functional": any(r["test_name"].startswith("end_to_end") and r["status"] == "passed" for r in self.test_results),
                    "agent_communication": any(r["test_name"] == "supervisor_workflow" and r["status"] == "passed" for r in self.test_results),
                    "rag_integration": any(r["test_name"] == "information_retrieval_agent" and r["status"] == "passed" for r in self.test_results),
                    "end_to_end_flow": any(r["test_name"].startswith("end_to_end") and r["status"] == "passed" for r in self.test_results),
                    "response_time_under_5s": meets_performance,
                    "error_rate_under_5pct": (1 - success_rate) < 0.05,
                    "response_relevance": any(r["test_name"] == "response_quality_assessment" and r["status"] == "passed" for r in self.test_results),
                    "rag_integration_working": any(r["test_name"] == "information_retrieval_agent" and r["status"] == "passed" for r in self.test_results),
                    "context_preservation": any(r["test_name"].startswith("end_to_end") and r["status"] == "passed" for r in self.test_results),
                    "error_handling": any(r["test_name"] == "error_handling" and r["status"] == "passed" for r in self.test_results)
                },
                "detailed_results": self.test_results,
                "recommendations": self._generate_recommendations(overall_status, success_rate, avg_response_time)
            }
        }
        
        return report
    
    def _generate_recommendations(self, overall_status: str, success_rate: float, avg_response_time: float) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if overall_status == "FAILED":
            if success_rate < 0.8:
                recommendations.append("Improve test success rate by addressing failed test cases")
            
            if avg_response_time >= 5.0:
                recommendations.append("Optimize response time to meet <5s requirement")
            
            recommendations.append("Review error logs and fix underlying issues")
        
        if success_rate >= 0.9 and avg_response_time < 3.0:
            recommendations.append("Excellent performance! Consider proceeding to Phase 2")
        
        if avg_response_time > 3.0 and avg_response_time < 5.0:
            recommendations.append("Good performance, but consider optimization for better user experience")
        
        return recommendations


async def main():
    """Main function to run Phase 1 integration testing."""
    print("🚀 Starting Phase 1 Comprehensive Integration Testing")
    print("=" * 80)
    
    tester = Phase1IntegrationTester()
    report = await tester.run_comprehensive_tests()
    
    # Save report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"docs/initiatives/agents/integration/phase1/results/phase1_comprehensive_test_results_{timestamp}.json"
    
    os.makedirs(os.path.dirname(report_filename), exist_ok=True)
    
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📊 Test Report saved to: {report_filename}")
    print(f"🎯 Overall Status: {report['phase1_integration_test_report']['overall_status']}")
    print(f"📈 Success Rate: {report['phase1_integration_test_report']['summary']['success_rate']:.1%}")
    print(f"⏱️ Avg Response Time: {report['phase1_integration_test_report']['performance_metrics']['avg_response_time']:.2f}s")
    
    return report


if __name__ == "__main__":
    asyncio.run(main())
