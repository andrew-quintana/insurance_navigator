#!/usr/bin/env python3
"""
Phase 2 - Comprehensive UUID Test with Real Document Upload and RAG
Tests complete workflow: user creation → document upload → RAG testing with proper UUIDs
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
import aiohttp
import hashlib
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from agents.patient_navigator.chat_interface import PatientNavigatorChatInterface, ChatMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase2ComprehensiveUUIDTest:
    """Comprehensive Phase 2 test with proper UUID handling and real document upload."""
    
    def __init__(self):
        self.test_user_id = str(uuid.uuid4())  # Generate proper UUID
        self.test_user_email = f"test_user_{int(time.time())}@example.com"
        self.test_user_password = "TestPassword123!"
        self.chat_interface = None
        self.supabase_url = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.api_base_url = "http://localhost:8000"
        self.test_results = []
        self.uploaded_document_id = None
        
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive Phase 2 test with UUID handling."""
        print("🚀 Starting Phase 2 Comprehensive UUID Test")
        print("=" * 60)
        print(f"Test User ID: {self.test_user_id}")
        print(f"Test User Email: {self.test_user_email}")
        
        start_time = time.time()
        results = {
            "test_name": "Phase 2 Comprehensive UUID Test",
            "timestamp": time.time(),
            "test_user_id": self.test_user_id,
            "test_user_email": self.test_user_email,
            "tests": {},
            "overall_status": "PENDING",
            "total_time": 0
        }
        
        try:
            # Test 1: User Creation and Authentication
            print("\n1️⃣ Testing User Creation and Authentication...")
            user_test = await self._test_user_creation_and_auth()
            results["tests"]["user_creation_auth"] = user_test
            
            # Test 2: Document Upload
            print("\n2️⃣ Testing Document Upload...")
            upload_test = await self._test_document_upload()
            results["tests"]["document_upload"] = upload_test
            
            # Test 3: Chat Interface Initialization
            print("\n3️⃣ Testing Chat Interface Initialization...")
            init_test = await self._test_chat_interface_initialization()
            results["tests"]["chat_interface_initialization"] = init_test
            
            # Test 4: RAG Query Processing with Real Data
            print("\n4️⃣ Testing RAG Query Processing with Real Data...")
            rag_test = await self._test_rag_query_processing()
            results["tests"]["rag_query_processing"] = rag_test
            
            # Test 5: Insurance Content Retrieval
            print("\n5️⃣ Testing Insurance Content Retrieval...")
            content_test = await self._test_insurance_content_retrieval()
            results["tests"]["insurance_content_retrieval"] = content_test
            
            # Test 6: Response Quality Assessment
            print("\n6️⃣ Testing Response Quality Assessment...")
            quality_test = await self._test_response_quality_assessment()
            results["tests"]["response_quality_assessment"] = quality_test
            
            # Test 7: Multilingual RAG Support
            print("\n7️⃣ Testing Multilingual RAG Support...")
            multilingual_test = await self._test_multilingual_rag_support()
            results["tests"]["multilingual_rag_support"] = multilingual_test
            
            # Test 8: RAG Performance
            print("\n8️⃣ Testing RAG Performance...")
            performance_test = await self._test_rag_performance()
            results["tests"]["rag_performance"] = performance_test
            
            # Calculate overall results
            total_time = time.time() - start_time
            results["total_time"] = total_time
            
            # Determine overall status
            all_tests_passed = all(
                test.get("status") == "PASS" 
                for test in results["tests"].values()
            )
            results["overall_status"] = "PASS" if all_tests_passed else "FAIL"
            
            # Generate summary
            self._generate_summary(results)
            
        except Exception as e:
            results["overall_status"] = "ERROR"
            results["error"] = str(e)
            print(f"❌ Test failed with error: {e}")
            
        return results
    
    async def _test_user_creation_and_auth(self) -> Dict[str, Any]:
        """Test user creation and authentication."""
        try:
            print("   Creating test user...")
            
            # Create user via Supabase auth
            async with aiohttp.ClientSession() as session:
                # Try to sign up user
                signup_data = {
                    "email": self.test_user_email,
                    "password": self.test_user_password
                }
                
                signup_url = f"{self.supabase_url}/auth/v1/signup"
                headers = {
                    "apikey": self.supabase_service_key,
                    "Content-Type": "application/json"
                }
                
                async with session.post(signup_url, json=signup_data, headers=headers) as response:
                    if response.status == 200:
                        print("   ✅ User created successfully")
                        user_created = True
                    else:
                        # User might already exist, try to sign in
                        print("   User might already exist, attempting sign in...")
                        user_created = False
                
                # Try to sign in
                signin_data = {
                    "email": self.test_user_email,
                    "password": self.test_user_password
                }
                
                signin_url = f"{self.supabase_url}/auth/v1/token?grant_type=password"
                async with session.post(signin_url, json=signin_data, headers=headers) as response:
                    if response.status == 200:
                        auth_data = await response.json()
                        self.access_token = auth_data.get("access_token")
                        print("   ✅ User authenticated successfully")
                        return {
                            "status": "PASS",
                            "message": "User creation and authentication successful",
                            "user_created": user_created,
                            "user_id": self.test_user_id,
                            "user_email": self.test_user_email
                        }
                    else:
                        return {
                            "status": "FAIL",
                            "message": f"User authentication failed: {response.status}",
                            "error": await response.text()
                        }
                        
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"User creation and authentication failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_document_upload(self) -> Dict[str, Any]:
        """Test document upload using test_insurance_document.pdf."""
        try:
            print("   Uploading test insurance document...")
            
            # Read test document
            test_doc_path = "examples/test_insurance_document.pdf"
            if not os.path.exists(test_doc_path):
                return {
                    "status": "FAIL",
                    "message": f"Test document not found: {test_doc_path}",
                    "error": "Test document missing"
                }
            
            with open(test_doc_path, "rb") as f:
                file_content = f.read()
            
            # Upload document via API
            async with aiohttp.ClientSession() as session:
                # Create form data
                form_data = aiohttp.FormData()
                form_data.add_field('file', file_content, filename='test_insurance_document.pdf', content_type='application/pdf')
                form_data.add_field('user_id', self.test_user_id)
                
                # Upload headers
                upload_headers = {
                    "Authorization": f"Bearer {getattr(self, 'access_token', '')}"
                }
                
                upload_url = f"{self.api_base_url}/api/upload-pipeline/upload"
                async with session.post(upload_url, data=form_data, headers=upload_headers) as response:
                    if response.status == 200:
                        upload_data = await response.json()
                        self.uploaded_document_id = upload_data.get("document_id")
                        print(f"   ✅ Document uploaded successfully: {self.uploaded_document_id}")
                        
                        # Wait for document processing
                        print("   Waiting for document processing...")
                        processing_complete = await self._wait_for_document_processing()
                        
                        return {
                            "status": "PASS" if processing_complete else "FAIL",
                            "message": "Document upload successful" if processing_complete else "Document processing incomplete",
                            "document_id": self.uploaded_document_id,
                            "processing_complete": processing_complete
                        }
                    else:
                        return {
                            "status": "FAIL",
                            "message": f"Document upload failed: {response.status}",
                            "error": await response.text()
                        }
                        
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Document upload failed: {str(e)}",
                "error": str(e)
            }
    
    async def _wait_for_document_processing(self, max_wait_time: int = 300) -> bool:
        """Wait for document processing to complete."""
        try:
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                # Check processing status
                async with aiohttp.ClientSession() as session:
                    status_url = f"{self.api_base_url}/api/upload-pipeline/upload/status/{self.uploaded_document_id}"
                    headers = {
                        "Authorization": f"Bearer {getattr(self, 'access_token', '')}"
                    }
                    
                    async with session.get(status_url, headers=headers) as response:
                        if response.status == 200:
                            status_data = await response.json()
                            status = status_data.get("status", "processing")
                            
                            if status == "completed":
                                print("   ✅ Document processing completed")
                                return True
                            elif status == "failed":
                                print("   ❌ Document processing failed")
                                return False
                            else:
                                print(f"   ⏳ Document processing status: {status}")
                                await asyncio.sleep(5)
                        else:
                            print(f"   ⚠️ Status check failed: {response.status}")
                            await asyncio.sleep(5)
            
            print("   ⏰ Document processing timeout")
            return False
            
        except Exception as e:
            print(f"   ❌ Error waiting for document processing: {e}")
            return False
    
    async def _test_chat_interface_initialization(self) -> Dict[str, Any]:
        """Test chat interface initialization."""
        try:
            print("   Initializing PatientNavigatorChatInterface...")
            self.chat_interface = PatientNavigatorChatInterface()
            print("   ✅ Chat interface initialized successfully")
            
            return {
                "status": "PASS",
                "message": "Chat interface initialized successfully",
                "interface_type": type(self.chat_interface).__name__
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Chat interface initialization failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_rag_query_processing(self) -> Dict[str, Any]:
        """Test RAG query processing with real uploaded documents."""
        try:
            if not self.chat_interface:
                return {
                    "status": "FAIL",
                    "message": "Chat interface not initialized"
                }
            
            # Test queries that should retrieve from uploaded document
            test_queries = [
                "What is my deductible?",
                "What are my copays for doctor visits?",
                "What services are covered under my plan?",
                "How do I find a doctor in my network?",
                "What are my prescription drug benefits?"
            ]
            
            query_results = []
            for i, query in enumerate(test_queries):
                print(f"   Testing query {i+1}/{len(test_queries)}: {query}")
                
                message = ChatMessage(
                    user_id=self.test_user_id,  # Use proper UUID
                    content=query,
                    timestamp=time.time(),
                    message_type="text",
                    language="en"
                )
                
                start_time = time.time()
                response = await self.chat_interface.process_message(message)
                processing_time = time.time() - start_time
                
                # Analyze response
                analysis = self._analyze_rag_response(response.content, query)
                
                query_results.append({
                    "query": query,
                    "status": "PASS",
                    "processing_time": processing_time,
                    "response_length": len(response.content),
                    "analysis": analysis,
                    "response": response.content[:200] + "..." if len(response.content) > 200 else response.content
                })
                
                print(f"   ✅ Query processed in {processing_time:.2f}s")
            
            # Calculate success metrics
            successful_queries = [r for r in query_results if r["status"] == "PASS"]
            success_rate = len(successful_queries) / len(test_queries)
            avg_processing_time = sum(r["processing_time"] for r in successful_queries) / len(successful_queries) if successful_queries else 0
            
            return {
                "status": "PASS" if success_rate >= 0.8 else "FAIL",
                "message": f"RAG query processing completed with {success_rate:.1%} success rate",
                "success_rate": success_rate,
                "average_processing_time": avg_processing_time,
                "total_queries": len(test_queries),
                "successful_queries": len(successful_queries),
                "query_results": query_results
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"RAG query processing test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_insurance_content_retrieval(self) -> Dict[str, Any]:
        """Test retrieval of insurance-specific content from uploaded document."""
        try:
            if not self.chat_interface:
                return {
                    "status": "FAIL",
                    "message": "Chat interface not initialized"
                }
            
            # Test queries designed to retrieve specific insurance content
            insurance_queries = [
                {
                    "query": "What is my deductible amount?",
                    "expected_keywords": ["deductible", "amount", "dollar", "$"],
                    "content_type": "specific_value"
                },
                {
                    "query": "What are my copays for different types of visits?",
                    "expected_keywords": ["copay", "visit", "doctor", "specialist"],
                    "content_type": "comparative"
                },
                {
                    "query": "What services are covered under my plan?",
                    "expected_keywords": ["covered", "services", "benefits", "plan"],
                    "content_type": "comprehensive"
                },
                {
                    "query": "How do I find a doctor in my network?",
                    "expected_keywords": ["network", "doctor", "find", "search"],
                    "content_type": "procedural"
                }
            ]
            
            content_results = []
            for i, test_case in enumerate(insurance_queries):
                print(f"   Testing insurance content {i+1}/{len(insurance_queries)}: {test_case['query']}")
                
                message = ChatMessage(
                    user_id=self.test_user_id,  # Use proper UUID
                    content=test_case["query"],
                    timestamp=time.time(),
                    message_type="text",
                    language="en"
                )
                
                response = await self.chat_interface.process_message(message)
                
                # Analyze content retrieval
                content_analysis = self._analyze_insurance_content_retrieval(
                    response.content, 
                    test_case["query"], 
                    test_case["expected_keywords"],
                    test_case["content_type"]
                )
                
                content_results.append({
                    "query": test_case["query"],
                    "content_type": test_case["content_type"],
                    "status": "PASS" if content_analysis["content_score"] >= 0.5 else "FAIL",
                    "content_score": content_analysis["content_score"],
                    "keyword_matches": content_analysis["keyword_matches"],
                    "response_length": len(response.content),
                    "response": response.content[:200] + "..." if len(response.content) > 200 else response.content
                })
                
                print(f"   ✅ Content analysis completed")
            
            # Calculate content retrieval metrics
            successful_content = [r for r in content_results if r["status"] == "PASS"]
            content_success_rate = len(successful_content) / len(insurance_queries)
            avg_content_score = sum(r["content_score"] for r in content_results) / len(content_results)
            
            return {
                "status": "PASS" if content_success_rate >= 0.7 else "FAIL",
                "message": f"Insurance content retrieval completed with {content_success_rate:.1%} success rate",
                "content_success_rate": content_success_rate,
                "average_content_score": avg_content_score,
                "total_tests": len(insurance_queries),
                "successful_tests": len(successful_content),
                "content_results": content_results
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Insurance content retrieval test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_response_quality_assessment(self) -> Dict[str, Any]:
        """Test response quality with detailed assessment."""
        try:
            if not self.chat_interface:
                return {
                    "status": "FAIL",
                    "message": "Chat interface not initialized"
                }
            
            # Test queries for quality assessment
            quality_queries = [
                "Can you explain my insurance benefits in simple terms?",
                "What should I do if I need to see a specialist?",
                "How much will I pay for a routine checkup?",
                "What happens if I go to an out-of-network doctor?"
            ]
            
            quality_results = []
            for i, query in enumerate(quality_queries):
                print(f"   Testing response quality {i+1}/{len(quality_queries)}: {query}")
                
                message = ChatMessage(
                    user_id=self.test_user_id,  # Use proper UUID
                    content=query,
                    timestamp=time.time(),
                    message_type="text",
                    language="en"
                )
                
                response = await self.chat_interface.process_message(message)
                
                # Assess response quality
                quality_assessment = self._assess_response_quality(response.content, query)
                
                quality_results.append({
                    "query": query,
                    "quality_score": quality_assessment["overall_score"],
                    "clarity": quality_assessment["clarity"],
                    "completeness": quality_assessment["completeness"],
                    "relevance": quality_assessment["relevance"],
                    "empathy": quality_assessment["empathy"],
                    "response_length": len(response.content),
                    "response": response.content[:300] + "..." if len(response.content) > 300 else response.content
                })
                
                print(f"   ✅ Quality assessment completed")
            
            # Calculate quality metrics
            avg_quality_score = sum(r["quality_score"] for r in quality_results) / len(quality_results)
            avg_clarity = sum(r["clarity"] for r in quality_results) / len(quality_results)
            avg_completeness = sum(r["completeness"] for r in quality_results) / len(quality_results)
            avg_relevance = sum(r["relevance"] for r in quality_results) / len(quality_results)
            avg_empathy = sum(r["empathy"] for r in quality_results) / len(quality_results)
            
            return {
                "status": "PASS" if avg_quality_score >= 0.7 else "FAIL",
                "message": f"Response quality assessment completed with {avg_quality_score:.2f} average quality score",
                "average_quality_score": avg_quality_score,
                "average_clarity": avg_clarity,
                "average_completeness": avg_completeness,
                "average_relevance": avg_relevance,
                "average_empathy": avg_empathy,
                "total_tests": len(quality_queries),
                "quality_results": quality_results
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Response quality assessment test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_multilingual_rag_support(self) -> Dict[str, Any]:
        """Test RAG support for multilingual queries."""
        try:
            if not self.chat_interface:
                return {
                    "status": "FAIL",
                    "message": "Chat interface not initialized"
                }
            
            # Test multilingual queries
            multilingual_queries = [
                {
                    "query": "¿Cuáles son mis beneficios de seguro?",
                    "language": "es",
                    "expected_english_keywords": ["benefits", "insurance", "coverage"]
                },
                {
                    "query": "Quel est mon montant de franchise?",
                    "language": "fr",
                    "expected_english_keywords": ["deductible", "amount", "dollar"]
                },
                {
                    "query": "Was sind meine Zuzahlungen?",
                    "language": "de",
                    "expected_english_keywords": ["copay", "payment", "visit"]
                }
            ]
            
            multilingual_results = []
            for i, test_case in enumerate(multilingual_queries):
                print(f"   Testing multilingual query {i+1}/{len(multilingual_queries)}: {test_case['query']}")
                
                message = ChatMessage(
                    user_id=self.test_user_id,  # Use proper UUID
                    content=test_case["query"],
                    timestamp=time.time(),
                    message_type="text",
                    language=test_case["language"]
                )
                
                response = await self.chat_interface.process_message(message)
                
                # Analyze multilingual response
                multilingual_analysis = self._analyze_multilingual_response(
                    response.content, 
                    test_case["query"], 
                    test_case["expected_english_keywords"]
                )
                
                multilingual_results.append({
                    "query": test_case["query"],
                    "language": test_case["language"],
                    "status": "PASS" if multilingual_analysis["translation_success"] else "FAIL",
                    "translation_success": multilingual_analysis["translation_success"],
                    "english_content_found": multilingual_analysis["english_content_found"],
                    "response_length": len(response.content),
                    "response": response.content[:200] + "..." if len(response.content) > 200 else response.content
                })
                
                print(f"   ✅ Multilingual analysis completed")
            
            # Calculate multilingual metrics
            successful_translations = [r for r in multilingual_results if r["status"] == "PASS"]
            translation_success_rate = len(successful_translations) / len(multilingual_queries)
            
            return {
                "status": "PASS" if translation_success_rate >= 0.6 else "FAIL",
                "message": f"Multilingual RAG support completed with {translation_success_rate:.1%} success rate",
                "translation_success_rate": translation_success_rate,
                "total_tests": len(multilingual_queries),
                "successful_translations": len(successful_translations),
                "multilingual_results": multilingual_results
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Multilingual RAG support test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_rag_performance(self) -> Dict[str, Any]:
        """Test RAG performance with concurrent queries."""
        try:
            if not self.chat_interface:
                return {
                    "status": "FAIL",
                    "message": "Chat interface not initialized"
                }
            
            # Test concurrent queries
            concurrent_queries = [
                "What is my deductible?",
                "What are my copays?",
                "What services are covered?",
                "How do I find a doctor?",
                "What are my prescription benefits?"
            ]
            
            print(f"   Testing {len(concurrent_queries)} concurrent queries...")
            
            # Execute queries concurrently
            start_time = time.time()
            tasks = []
            for i, query in enumerate(concurrent_queries):
                task = self._execute_single_query(query, i)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Analyze results
            successful_queries = [r for r in results if isinstance(r, dict) and r.get("status") == "PASS"]
            failed_queries = [r for r in results if isinstance(r, dict) and r.get("status") == "FAIL"]
            exceptions = [r for r in results if isinstance(r, Exception)]
            
            # Calculate performance metrics
            query_times = [r.get("processing_time", 0) for r in successful_queries if "processing_time" in r]
            avg_query_time = sum(query_times) / len(query_times) if query_times else 0
            max_query_time = max(query_times) if query_times else 0
            min_query_time = min(query_times) if query_times else 0
            
            return {
                "status": "PASS" if len(successful_queries) >= len(concurrent_queries) * 0.8 else "FAIL",
                "message": f"RAG performance test completed with {len(successful_queries)}/{len(concurrent_queries)} successful queries",
                "total_time": total_time,
                "concurrent_queries": len(concurrent_queries),
                "successful_queries": len(successful_queries),
                "failed_queries": len(failed_queries),
                "exceptions": len(exceptions),
                "average_query_time": avg_query_time,
                "max_query_time": max_query_time,
                "min_query_time": min_query_time,
                "throughput": len(successful_queries) / total_time if total_time > 0 else 0,
                "query_results": results
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"RAG performance test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_single_query(self, query: str, query_index: int) -> Dict[str, Any]:
        """Execute a single query for performance testing."""
        try:
            message = ChatMessage(
                user_id=self.test_user_id,  # Use proper UUID
                content=query,
                timestamp=time.time(),
                message_type="text",
                language="en"
            )
            
            start_time = time.time()
            response = await self.chat_interface.process_message(message)
            processing_time = time.time() - start_time
            
            return {
                "query_index": query_index,
                "query": query,
                "status": "PASS",
                "processing_time": processing_time,
                "response_length": len(response.content),
                "response": response.content[:100] + "..." if len(response.content) > 100 else response.content
            }
        except Exception as e:
            return {
                "query_index": query_index,
                "query": query,
                "status": "FAIL",
                "processing_time": 0,
                "error": str(e)
            }
    
    def _analyze_rag_response(self, response: str, query: str) -> Dict[str, Any]:
        """Analyze RAG response quality."""
        response_lower = response.lower()
        query_lower = query.lower()
        
        # Check for insurance content
        insurance_keywords = [
            "deductible", "copay", "coverage", "benefits", "premium",
            "network", "prescription", "doctor", "visit", "plan"
        ]
        insurance_content = sum(1 for keyword in insurance_keywords if keyword in response_lower)
        
        # Check for query relevance
        query_words = set(query_lower.split())
        response_words = set(response_lower.split())
        common_words = query_words.intersection(response_words)
        relevance_score = len(common_words) / len(query_words) if query_words else 0
        
        # Check response completeness
        completeness_score = min(1.0, len(response) / 200)  # Assume 200 chars is complete
        
        return {
            "insurance_content_count": insurance_content,
            "relevance_score": relevance_score,
            "completeness_score": completeness_score,
            "response_length": len(response)
        }
    
    def _analyze_insurance_content_retrieval(self, response: str, query: str, expected_keywords: list, content_type: str) -> Dict[str, Any]:
        """Analyze insurance content retrieval quality."""
        response_lower = response.lower()
        
        # Check for expected keywords
        keyword_matches = sum(1 for keyword in expected_keywords if keyword in response_lower)
        keyword_score = keyword_matches / len(expected_keywords) if expected_keywords else 0
        
        # Check for content type specific indicators
        content_indicators = {
            "specific_value": ["$", "amount", "dollar", "cost", "price"],
            "comparative": ["different", "various", "compare", "versus", "vs"],
            "comprehensive": ["all", "complete", "full", "entire", "comprehensive"],
            "procedural": ["how", "step", "process", "procedure", "guide"]
        }
        
        type_indicators = content_indicators.get(content_type, [])
        type_matches = sum(1 for indicator in type_indicators if indicator in response_lower)
        type_score = type_matches / len(type_indicators) if type_indicators else 0
        
        # Overall content score
        content_score = (keyword_score * 0.7 + type_score * 0.3)
        
        return {
            "keyword_matches": keyword_matches,
            "keyword_score": keyword_score,
            "type_matches": type_matches,
            "type_score": type_score,
            "content_score": content_score
        }
    
    def _assess_response_quality(self, response: str, query: str) -> Dict[str, Any]:
        """Assess overall response quality."""
        response_lower = response.lower()
        
        # Clarity (sentence structure and readability)
        sentences = response.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        clarity = 1.0 - min(1.0, (avg_sentence_length - 15) / 20)  # Optimal around 15 words per sentence
        
        # Completeness (response length and detail)
        completeness = min(1.0, len(response) / 300)  # Assume 300 chars is complete
        
        # Relevance (query-response alignment)
        query_words = set(query.lower().split())
        response_words = set(response_lower.split())
        common_words = query_words.intersection(response_words)
        relevance = len(common_words) / len(query_words) if query_words else 0
        
        # Empathy (warm, supportive language)
        empathy_indicators = ["help", "support", "understand", "care", "assist", "guide", "please", "thank"]
        empathy_score = sum(1 for indicator in empathy_indicators if indicator in response_lower) / len(empathy_indicators)
        
        # Overall score
        overall_score = (clarity * 0.25 + completeness * 0.25 + relevance * 0.25 + empathy_score * 0.25)
        
        return {
            "clarity": clarity,
            "completeness": completeness,
            "relevance": relevance,
            "empathy": empathy_score,
            "overall_score": overall_score
        }
    
    def _analyze_multilingual_response(self, response: str, original_query: str, expected_english_keywords: list) -> Dict[str, Any]:
        """Analyze multilingual response quality."""
        response_lower = response.lower()
        
        # Check if response is in English (translation success)
        english_indicators = ["the", "and", "or", "is", "are", "will", "can", "should"]
        english_score = sum(1 for indicator in english_indicators if indicator in response_lower) / len(english_indicators)
        translation_success = english_score > 0.3
        
        # Check for expected English keywords
        english_content_found = sum(1 for keyword in expected_english_keywords if keyword in response_lower)
        
        return {
            "translation_success": translation_success,
            "english_score": english_score,
            "english_content_found": english_content_found,
            "expected_keywords_found": english_content_found / len(expected_english_keywords) if expected_english_keywords else 0
        }
    
    def _generate_summary(self, results: Dict[str, Any]):
        """Generate test summary."""
        print("\n" + "=" * 60)
        print("📊 PHASE 2 COMPREHENSIVE UUID TEST SUMMARY")
        print("=" * 60)
        
        print(f"Overall Status: {results['overall_status']}")
        print(f"Total Time: {results['total_time']:.2f} seconds")
        print(f"Test User ID: {results['test_user_id']}")
        print(f"Test User Email: {results['test_user_email']}")
        
        print("\nTest Results:")
        for test_name, test_result in results["tests"].items():
            status_icon = "✅" if test_result["status"] == "PASS" else "❌"
            print(f"  {status_icon} {test_name}: {test_result['status']}")
            if "message" in test_result:
                print(f"      {test_result['message']}")
        
        # Show specific metrics
        if "rag_query_processing" in results["tests"]:
            rag_result = results["tests"]["rag_query_processing"]
            if "success_rate" in rag_result:
                print(f"\nRAG Success Rate: {rag_result['success_rate']:.1%}")
            if "average_processing_time" in rag_result:
                print(f"Average Processing Time: {rag_result['average_processing_time']:.2f}s")
        
        if "response_quality_assessment" in results["tests"]:
            quality_result = results["tests"]["response_quality_assessment"]
            if "average_quality_score" in quality_result:
                print(f"Average Quality Score: {quality_result['average_quality_score']:.2f}")
        
        if "rag_performance" in results["tests"]:
            perf_result = results["tests"]["rag_performance"]
            if "throughput" in perf_result:
                print(f"RAG Throughput: {perf_result['throughput']:.2f} queries/second")
        
        if results["overall_status"] == "PASS":
            print("\n🎉 Phase 2 Comprehensive UUID Test PASSED!")
        else:
            print("\n❌ Phase 2 Comprehensive UUID Test FAILED!")

async def main():
    """Run Phase 2 comprehensive UUID test."""
    tester = Phase2ComprehensiveUUIDTest()
    results = await tester.run_comprehensive_test()
    
    # Save results
    results_file = f"phase2_comprehensive_uuid_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: {results_file}")
    return results

if __name__ == "__main__":
    asyncio.run(main())
