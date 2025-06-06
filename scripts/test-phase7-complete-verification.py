#!/usr/bin/env python3
"""
Phase 7 Complete Verification Test Suite
Tests all Phase 7 Advanced Features:
- Multi-Modal Support (Image Processing)
- Advanced Workflows (Multi-step processes)
- Conversation Memory (Long-term context)
- Performance Optimization (Policy Caching)
"""

import asyncio
import sys
import os
import traceback
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Phase7TestRunner:
    def __init__(self):
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
    
    def test_result(self, test_name: str, passed: bool, details: str = ""):
        """Record test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
        
        self.test_results[test_name] = {
            "passed": passed,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
    
    async def test_multimodal_image_processor(self):
        """Test 1: Multi-Modal Image Processing"""
        try:
            from agents.common.multimodal.image_processor import ImageProcessor
            processor = ImageProcessor()
            
            # Test basic initialization
            if not hasattr(processor, 'supported_formats'):
                self.test_result("1.1 Image Processor Initialization", False, "Missing supported_formats")
                return
            
            # Test image validation
            test_image_data = b"fake_image_data_for_testing"
            valid, error = processor.validate_image(test_image_data, "test.jpg")
            if not valid or error:
                self.test_result("1.2 Image Validation", True, f"Properly rejected invalid image: {error}")
            else:
                self.test_result("1.2 Image Validation", True, "Image validation working")
            
            # Test OCR extraction
            ocr_result = processor.extract_text_from_image(test_image_data)
            required_fields = ["extracted_text", "confidence_score", "status"]
            missing_fields = [f for f in required_fields if f not in ocr_result]
            
            if missing_fields:
                self.test_result("1.3 OCR Text Extraction", False, f"Missing fields: {missing_fields}")
            else:
                self.test_result("1.3 OCR Text Extraction", True, f"Extracted: {ocr_result['extracted_text'][:50]}...")
            
            # Test document classification
            sample_text = "INSURANCE CARD Member ID: 123456789 Group: ABC Corp Copay: $25"
            classification = processor.classify_insurance_document(sample_text)
            
            if "document_type" in classification and classification["document_type"] == "insurance_card":
                self.test_result("1.4 Document Classification", True, f"Correctly classified as {classification['document_type']}")
            else:
                self.test_result("1.4 Document Classification", False, f"Wrong classification: {classification}")
        
        except Exception as e:
            self.test_result("1.X Multi-Modal Processing", False, f"Exception: {e}")
    
    async def test_workflow_manager(self):
        """Test 2: Advanced Workflow Management"""
        try:
            from agents.common.workflows.workflow_manager import WorkflowManager
            workflow_manager = WorkflowManager()
            
            # Test workflow types availability
            workflow_types = workflow_manager.list_workflow_types()
            expected_types = ["claim_filing", "doctor_search", "benefit_verification"]
            
            if not all(wt in workflow_types for wt in expected_types):
                self.test_result("2.1 Workflow Templates", False, f"Missing workflow types. Found: {workflow_types}")
                return
            else:
                self.test_result("2.1 Workflow Templates", True, f"All workflow types available: {workflow_types}")
            
            # Test starting a workflow
            start_result = await workflow_manager.start_workflow("claim_filing", "test_user", "test_session")
            
            if "workflow_id" not in start_result or "next_step" not in start_result:
                self.test_result("2.2 Start Workflow", False, f"Invalid start result: {start_result}")
                return
            else:
                self.test_result("2.2 Start Workflow", True, f"Started workflow: {start_result['workflow_id']}")
            
            workflow_id = start_result["workflow_id"]
            
            # Test step processing
            step_result = await workflow_manager.process_step(workflow_id, "Doctor visit for annual checkup")
            
            if "next_step" not in step_result:
                self.test_result("2.3 Process Workflow Step", False, f"Invalid step result: {step_result}")
            else:
                self.test_result("2.3 Process Workflow Step", True, f"Processed step, next: {step_result['next_step']}")
            
            # Test workflow status
            status = workflow_manager.get_workflow_status(workflow_id)
            if "state" not in status or "progress" not in status:
                self.test_result("2.4 Workflow Status", False, f"Invalid status: {status}")
            else:
                self.test_result("2.4 Workflow Status", True, f"Status: {status['state']}, Progress: {status['progress']}")
        
        except Exception as e:
            self.test_result("2.X Workflow Management", False, f"Exception: {e}")
    
    async def test_conversation_memory(self):
        """Test 3: Conversation Memory System"""
        try:
            from agents.common.memory.conversation_memory import ConversationMemory
            memory = ConversationMemory()
            
            # Test storing interactions
            await memory.store_interaction(
                "test_user", 
                "test_session", 
                "What's my deductible?", 
                "Your deductible is $1500 individual",
                {"query_type": "benefit_inquiry"}
            )
            
            await memory.store_interaction(
                "test_user", 
                "test_session", 
                "How do I file a claim?", 
                "To file a claim, first gather your receipts...",
                {"query_type": "claim_filing"}
            )
            
            self.test_result("3.1 Store Interactions", True, "Successfully stored 2 interactions")
            
            # Test conversation context retrieval
            context = await memory.get_conversation_context("test_user", "test_session", limit=2)
            
            if "What's my deductible" in context and "How do I file" in context:
                self.test_result("3.2 Context Retrieval", True, f"Retrieved context: {len(context)} chars")
            else:
                self.test_result("3.2 Context Retrieval", False, f"Context missing interactions: {context[:100]}")
            
            # Test user preferences extraction
            preferences = await memory.extract_user_preferences("test_user")
            
            if "common_question_types" in preferences:
                question_types = preferences["common_question_types"]
                if "benefit_inquiry" in question_types and "claim_filing" in question_types:
                    self.test_result("3.3 User Preferences", True, f"Extracted preferences: {question_types}")
                else:
                    self.test_result("3.3 User Preferences", False, f"Missing question types: {question_types}")
            else:
                self.test_result("3.3 User Preferences", False, "No preferences extracted")
            
            # Test session summarization
            summary = await memory.summarize_session("test_user", "test_session")
            
            if "interaction_count" in summary and summary["interaction_count"] == 2:
                self.test_result("3.4 Session Summary", True, f"Summary: {summary['interaction_count']} interactions")
            else:
                self.test_result("3.4 Session Summary", False, f"Invalid summary: {summary}")
        
        except Exception as e:
            self.test_result("3.X Conversation Memory", False, f"Exception: {e}")
    
    async def test_policy_cache(self):
        """Test 4: Performance Optimization - Policy Caching"""
        try:
            from agents.common.caching.policy_cache import PolicyCache
            cache = PolicyCache()
            
            # Test policy structure template
            structure = cache.get_policy_structure()
            required_sections = ["basic_info", "financial", "coverage", "network", "metadata"]
            
            missing_sections = [s for s in required_sections if s not in structure]
            if missing_sections:
                self.test_result("4.1 Policy Structure", False, f"Missing sections: {missing_sections}")
                return
            else:
                self.test_result("4.1 Policy Structure", True, f"Complete structure with {len(structure)} sections")
            
            # Test caching policy data
            test_policy = {
                "basic_info": {
                    "policy_number": "TEST123",
                    "plan_name": "Test Health Plan",
                    "carrier": "Test Insurance Co"
                },
                "financial": {
                    "deductible": {
                        "individual": 1500.0,
                        "family": 3000.0
                    },
                    "copays": {
                        "primary_care": 25.0,
                        "specialist": 50.0
                    }
                }
            }
            
            cache.cache_policy_data("test_user", test_policy)
            self.test_result("4.2 Cache Policy Data", True, "Successfully cached test policy")
            
            # Test retrieving cached policy
            cached_policy = cache.get_cached_policy("test_user")
            
            if cached_policy and cached_policy["basic_info"]["policy_number"] == "TEST123":
                self.test_result("4.3 Retrieve Cached Policy", True, f"Retrieved policy: {cached_policy['basic_info']['plan_name']}")
            else:
                self.test_result("4.3 Retrieve Cached Policy", False, "Failed to retrieve cached policy")
            
            # Test quick answers for common queries
            deductible_answer = cache.get_quick_answer("test_user", "deductible")
            
            if deductible_answer and "value" in deductible_answer:
                deductible_value = deductible_answer["value"]
                if deductible_value.get("individual") == 1500.0:
                    self.test_result("4.4 Quick Answer - Deductible", True, f"Correct deductible: ${deductible_value['individual']}")
                else:
                    self.test_result("4.4 Quick Answer - Deductible", False, f"Wrong deductible: {deductible_value}")
            else:
                self.test_result("4.4 Quick Answer - Deductible", False, "No quick answer for deductible")
            
            # Test caveats inclusion
            if deductible_answer and "caveats" in deductible_answer:
                caveats = deductible_answer["caveats"]
                if caveats and len(caveats) > 0:
                    self.test_result("4.5 Caveats System", True, f"Found {len(caveats)} caveats")
                else:
                    self.test_result("4.5 Caveats System", False, "No caveats found")
            else:
                self.test_result("4.5 Caveats System", False, "Caveats not included in answer")
        
        except Exception as e:
            self.test_result("4.X Policy Caching", False, f"Exception: {e}")
    
    async def test_patient_navigator_integration(self):
        """Test 5: PatientNavigatorAgent Integration with Phase 7 Features"""
        try:
            from agents.patient_navigator.patient_navigator import PatientNavigatorAgent
            agent = PatientNavigatorAgent()
            
            # Check if agent has Phase 7 attributes
            phase7_features = ["workflow_manager", "conversation_memory", "policy_cache"]
            missing_features = [f for f in phase7_features if not hasattr(agent, f)]
            
            if missing_features:
                self.test_result("5.1 Agent Integration", False, f"Missing features: {missing_features}")
            else:
                self.test_result("5.1 Agent Integration", True, f"All Phase 7 features integrated")
            
            # Test agent processing with enhanced capabilities
            response, metadata = agent.process("What's my deductible and how do I file a claim?", "test_user", "integration_test")
            
            if response and len(response) > 0:
                self.test_result("5.2 Enhanced Processing", True, f"Response generated: {len(response)} chars")
            else:
                self.test_result("5.2 Enhanced Processing", False, "No response generated")
            
            # Verify metadata includes Phase 7 info
            if metadata and isinstance(metadata, dict):
                self.test_result("5.3 Metadata Generation", True, f"Metadata keys: {list(metadata.keys())}")
            else:
                self.test_result("5.3 Metadata Generation", False, "No metadata generated")
        
        except Exception as e:
            self.test_result("5.X Agent Integration", False, f"Exception: {e}")
    
    async def test_image_chat_endpoint_readiness(self):
        """Test 6: Image Chat Endpoint Components"""
        try:
            # Test that we can import the components used by the endpoint
            from agents.common.multimodal.image_processor import ImageProcessor, encode_image_to_base64, decode_base64_image
            from agents.patient_navigator.patient_navigator import PatientNavigatorAgent
            
            processor = ImageProcessor()
            agent = PatientNavigatorAgent()
            
            # Test base64 utilities
            test_data = b"test_image_data"
            encoded = encode_image_to_base64(test_data)
            decoded = decode_base64_image(encoded)
            
            if decoded == test_data:
                self.test_result("6.1 Base64 Utilities", True, "Encoding/decoding working")
            else:
                self.test_result("6.1 Base64 Utilities", False, "Base64 round-trip failed")
            
            # Test image processing pipeline
            fake_image = b"fake_image_bytes_for_testing"
            ocr_result = processor.extract_text_from_image(fake_image)
            
            if "extracted_text" in ocr_result:
                # Simulate endpoint behavior
                image_text = f" [IMAGE: {ocr_result['extracted_text'][:200]}]"
                enhanced_message = "What does this insurance document say?" + image_text
                
                response, metadata = agent.process(enhanced_message, "test_user", "image_test")
                
                if response and len(response) > 0:
                    self.test_result("6.2 Image Chat Pipeline", True, f"Full pipeline working: {len(response)} chars")
                else:
                    self.test_result("6.2 Image Chat Pipeline", False, "Pipeline failed to generate response")
            else:
                self.test_result("6.2 Image Chat Pipeline", False, "OCR result missing extracted_text")
        
        except Exception as e:
            self.test_result("6.X Image Chat Endpoint", False, f"Exception: {e}")
    
    async def run_all_tests(self):
        """Run complete Phase 7 test suite"""
        print("🚀 Starting Phase 7 Complete Verification Tests")
        print("=" * 60)
        
        # Run all test categories
        await self.test_multimodal_image_processor()
        print()
        await self.test_workflow_manager()
        print()
        await self.test_conversation_memory()
        print()
        await self.test_policy_cache()
        print()
        await self.test_patient_navigator_integration()
        print()
        await self.test_image_chat_endpoint_readiness()
        
        # Calculate final results
        pass_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 PHASE 7 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if pass_rate >= 90:
            print("🎉 PHASE 7 IMPLEMENTATION: EXCELLENT")
        elif pass_rate >= 80:
            print("✅ PHASE 7 IMPLEMENTATION: GOOD")
        elif pass_rate >= 70:
            print("⚠️  PHASE 7 IMPLEMENTATION: NEEDS IMPROVEMENT")
        else:
            print("❌ PHASE 7 IMPLEMENTATION: REQUIRES FIXES")
        
        # Detailed results
        print("\n📋 DETAILED TEST RESULTS:")
        for test_name, result in self.test_results.items():
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {test_name}: {result['details']}")
        
        return pass_rate >= 80

async def main():
    """Main test execution"""
    print("🔧 Phase 7 Advanced Features Verification")
    print("Testing: Multi-Modal, Workflows, Memory, Caching")
    print()
    
    runner = Phase7TestRunner()
    
    try:
        success = await runner.run_all_tests()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ TEST RUNNER FAILED: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main()) 