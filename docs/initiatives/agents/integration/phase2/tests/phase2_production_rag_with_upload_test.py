#!/usr/bin/env python3
"""
Phase 2 - Production RAG with Real Uploaded Documents Test
Tests RAG functionality with real uploaded documents in production database
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, List
import aiohttp
import os
from pathlib import Path

# Test configuration
UPLOAD_PIPELINE_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = "/api/upload-pipeline/upload"
JOBS_ENDPOINT = "/api/v2/jobs"
CHAT_ENDPOINT = "/chat"
AUTH_ENDPOINT = "/auth/v1/signup"
TOKEN_ENDPOINT = "/auth/v1/token"

class Phase2ProductionRAGWithUploadTest:
    """Test production RAG with real uploaded documents."""
    
    def __init__(self):
        self.test_user_id = str(uuid.uuid4())
        self.test_email = f"production_rag_{self.test_user_id}@example.com"
        self.test_password = "ProductionRAG123!"
        self.jwt_token = None
        self.uploaded_documents = []
        self.test_document_path = "examples/test_insurance_document.pdf"
        
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive Phase 2 production RAG with upload test."""
        print("🚀 Starting Phase 2 Production RAG with Real Uploaded Documents Test")
        print("=" * 75)
        
        start_time = time.time()
        results = {
            "test_name": "Phase 2 Production RAG with Real Uploaded Documents",
            "timestamp": time.time(),
            "test_user_id": self.test_user_id,
            "test_email": self.test_email,
            "tests": {},
            "overall_status": "PENDING",
            "total_time": 0
        }
        
        try:
            # Test 1: Setup User and Authentication
            print("\n1️⃣ Setting up User and Authentication...")
            setup_test = await self._test_user_setup()
            results["tests"]["user_setup"] = setup_test
            
            # Test 2: Upload Multiple Documents
            print("\n2️⃣ Testing Multiple Document Upload...")
            upload_test = await self._test_multiple_document_upload()
            results["tests"]["multiple_document_upload"] = upload_test
            
            # Test 3: Wait for All Document Processing
            print("\n3️⃣ Waiting for All Document Processing...")
            processing_test = await self._test_all_document_processing()
            results["tests"]["all_document_processing"] = processing_test
            
            # Test 4: Production RAG Retrieval
            print("\n4️⃣ Testing Production RAG Retrieval...")
            rag_retrieval_test = await self._test_production_rag_retrieval()
            results["tests"]["production_rag_retrieval"] = rag_retrieval_test
            
            # Test 5: RAG Quality Assessment
            print("\n5️⃣ Testing RAG Quality Assessment...")
            quality_test = await self._test_rag_quality_assessment()
            results["tests"]["rag_quality_assessment"] = quality_test
            
            # Test 6: Cross-Document RAG
            print("\n6️⃣ Testing Cross-Document RAG...")
            cross_doc_test = await self._test_cross_document_rag()
            results["tests"]["cross_document_rag"] = cross_doc_test
            
            # Test 7: Performance Testing
            print("\n7️⃣ Testing RAG Performance...")
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
    
    async def _test_user_setup(self) -> Dict[str, Any]:
        """Setup test user and authentication."""
        try:
            # Create user
            user_data = {
                "email": self.test_email,
                "password": self.test_password,
                "user_metadata": {
                    "test_user": True,
                    "phase": "phase2_production_rag",
                    "created_at": time.time()
                }
            }
            
            async with aiohttp.ClientSession() as session:
                # Create user
                url = f"{UPLOAD_PIPELINE_URL}{AUTH_ENDPOINT}"
                async with session.post(url, json=user_data) as response:
                    if response.status not in [200, 201, 409]:
                        return {
                            "status": "FAIL",
                            "message": f"User creation failed: {response.status}",
                            "response_status": response.status
                        }
                
                # Authenticate user
                auth_data = {
                    "email": self.test_email,
                    "password": self.test_password
                }
                
                url = f"{UPLOAD_PIPELINE_URL}{TOKEN_ENDPOINT}?grant_type=password"
                async with session.post(url, json=auth_data) as response:
                    if response.status == 200:
                        auth_response = await response.json()
                        self.jwt_token = auth_response.get('access_token')
                        
                        return {
                            "status": "PASS",
                            "message": "User setup and authentication successful",
                            "user_id": self.test_user_id,
                            "has_jwt_token": bool(self.jwt_token),
                            "response_status": response.status
                        }
                    else:
                        return {
                            "status": "FAIL",
                            "message": f"User authentication failed: {response.status}",
                            "response_status": response.status
                        }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"User setup test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_multiple_document_upload(self) -> Dict[str, Any]:
        """Test uploading multiple documents for RAG testing."""
        try:
            if not self.jwt_token:
                return {
                    "status": "FAIL",
                    "message": "No JWT token available for document upload"
                }
            
            if not os.path.exists(self.test_document_path):
                return {
                    "status": "FAIL",
                    "message": f"Test document not found: {self.test_document_path}",
                    "document_path": self.test_document_path
                }
            
            # Upload the same document multiple times to simulate multiple documents
            upload_results = []
            num_documents = 3
            
            async with aiohttp.ClientSession() as session:
                for i in range(num_documents):
                    with open(self.test_document_path, 'rb') as f:
                        file_data = f.read()
                    
                    # Create multipart form data
                    data = aiohttp.FormData()
                    data.add_field('file', file_data, filename=f'test_insurance_document_{i+1}.pdf', content_type='application/pdf')
                    data.add_field('user_id', self.test_user_id)
                    
                    # Set authorization header
                    headers = {
                        'Authorization': f'Bearer {self.jwt_token}'
                    }
                    
                    # Upload document
                    url = f"{UPLOAD_PIPELINE_URL}{UPLOAD_ENDPOINT}"
                    async with session.post(url, data=data, headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            document_info = {
                                "document_id": result.get('document_id'),
                                "job_id": result.get('job_id'),
                                "filename": f'test_insurance_document_{i+1}.pdf',
                                "upload_time": time.time()
                            }
                            self.uploaded_documents.append(document_info)
                            upload_results.append({
                                "document_index": i + 1,
                                "status": "PASS",
                                "document_id": document_info["document_id"],
                                "job_id": document_info["job_id"]
                            })
                        else:
                            error_text = await response.text()
                            upload_results.append({
                                "document_index": i + 1,
                                "status": "FAIL",
                                "response_status": response.status,
                                "error": error_text
                            })
            
            successful_uploads = [r for r in upload_results if r["status"] == "PASS"]
            success_rate = len(successful_uploads) / num_documents
            
            return {
                "status": "PASS" if success_rate >= 0.8 else "FAIL",
                "message": f"Multiple document upload completed with {success_rate:.1%} success rate",
                "total_documents": num_documents,
                "successful_uploads": len(successful_uploads),
                "success_rate": success_rate,
                "upload_results": upload_results,
                "uploaded_documents": self.uploaded_documents
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Multiple document upload test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_all_document_processing(self) -> Dict[str, Any]:
        """Wait for all uploaded documents to be processed."""
        try:
            if not self.uploaded_documents:
                return {
                    "status": "FAIL",
                    "message": "No uploaded documents available for processing test"
                }
            
            max_wait_time = 600  # 10 minutes for multiple documents
            start_time = time.time()
            processing_results = []
            
            async with aiohttp.ClientSession() as session:
                while time.time() - start_time < max_wait_time:
                    all_completed = True
                    all_failed = True
                    
                    for doc in self.uploaded_documents:
                        job_id = doc["job_id"]
                        url = f"{UPLOAD_PIPELINE_URL}{JOBS_ENDPOINT}/{job_id}"
                        async with session.get(url) as response:
                            if response.status == 200:
                                job_data = await response.json()
                                status = job_data.get('status', 'unknown')
                                
                                if status == 'completed':
                                    processing_results.append({
                                        "document_id": doc["document_id"],
                                        "job_id": job_id,
                                        "status": "completed",
                                        "processing_time": time.time() - start_time,
                                        "chunks_created": job_data.get('processing_details', {}).get('chunks_created', 0)
                                    })
                                elif status == 'failed':
                                    processing_results.append({
                                        "document_id": doc["document_id"],
                                        "job_id": job_id,
                                        "status": "failed",
                                        "error": job_data.get('error', 'Unknown error')
                                    })
                                    all_failed = False
                                else:
                                    all_completed = False
                                    all_failed = False
                            else:
                                all_completed = False
                                all_failed = False
                    
                    if all_completed:
                        return {
                            "status": "PASS",
                            "message": "All documents processed successfully",
                            "total_processing_time": time.time() - start_time,
                            "documents_processed": len(processing_results),
                            "processing_results": processing_results
                        }
                    elif all_failed:
                        return {
                            "status": "FAIL",
                            "message": "All document processing failed",
                            "processing_results": processing_results
                        }
                    else:
                        print(f"   Processing documents... ({len(processing_results)} completed so far)")
                        await asyncio.sleep(15)
                
                return {
                    "status": "FAIL",
                    "message": f"Document processing timed out after {max_wait_time} seconds",
                    "processing_results": processing_results
                }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"All document processing test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_production_rag_retrieval(self) -> Dict[str, Any]:
        """Test RAG retrieval with production database and uploaded documents."""
        try:
            # Test queries that should retrieve from uploaded documents
            test_queries = [
                "What is my deductible?",
                "What are my copays for doctor visits?",
                "What services are covered under my plan?",
                "How do I find a doctor in my network?",
                "What are my prescription drug benefits?",
                "What is my out-of-pocket maximum?",
                "Are mental health services covered?",
                "What is my emergency room copay?"
            ]
            
            results = []
            async with aiohttp.ClientSession() as session:
                for query in test_queries:
                    chat_data = {
                        "message": query,
                        "conversation_id": f"production_rag_{int(time.time())}",
                        "user_id": self.test_user_id,
                        "context": {
                            "user_authenticated": True,
                            "has_uploaded_documents": True,
                            "document_count": len(self.uploaded_documents),
                            "document_ids": [doc["document_id"] for doc in self.uploaded_documents]
                        }
                    }
                    
                    headers = {'Authorization': f'Bearer {self.jwt_token}'}
                    url = f"{UPLOAD_PIPELINE_URL}{CHAT_ENDPOINT}"
                    async with session.post(url, json=chat_data, headers=headers) as response:
                        if response.status == 200:
                            chat_response = await response.json()
                            response_text = chat_response.get('response', '')
                            
                            # Analyze response quality
                            analysis = self._analyze_rag_response(response_text, query)
                            
                            results.append({
                                "query": query,
                                "status": "PASS",
                                "response_length": len(response_text),
                                "analysis": analysis,
                                "response": response_text[:300] + "..." if len(response_text) > 300 else response_text
                            })
                        else:
                            error_text = await response.text()
                            results.append({
                                "query": query,
                                "status": "FAIL",
                                "response_status": response.status,
                                "error": error_text
                            })
            
            # Calculate success metrics
            successful_queries = [r for r in results if r["status"] == "PASS"]
            success_rate = len(successful_queries) / len(test_queries)
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(successful_queries)
            
            return {
                "status": "PASS" if success_rate >= 0.8 else "FAIL",
                "message": f"Production RAG retrieval completed with {success_rate:.1%} success rate",
                "success_rate": success_rate,
                "quality_metrics": quality_metrics,
                "total_queries": len(test_queries),
                "successful_queries": len(successful_queries),
                "query_results": results
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Production RAG retrieval test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_rag_quality_assessment(self) -> Dict[str, Any]:
        """Test RAG response quality with detailed assessment."""
        try:
            # Use specific queries designed to test different aspects of RAG quality
            quality_test_queries = [
                {
                    "query": "What is my deductible amount?",
                    "expected_content": ["deductible", "amount", "dollar", "$"],
                    "expected_type": "specific_value"
                },
                {
                    "query": "What are my copays for different types of visits?",
                    "expected_content": ["copay", "visit", "doctor", "specialist"],
                    "expected_type": "comparative"
                },
                {
                    "query": "How do I find a doctor in my network?",
                    "expected_content": ["network", "doctor", "find", "search"],
                    "expected_type": "procedural"
                },
                {
                    "query": "What services are covered under my plan?",
                    "expected_content": ["covered", "services", "benefits", "plan"],
                    "expected_type": "comprehensive"
                }
            ]
            
            quality_results = []
            async with aiohttp.ClientSession() as session:
                for test_case in quality_test_queries:
                    query = test_case["query"]
                    expected_content = test_case["expected_content"]
                    expected_type = test_case["expected_type"]
                    
                    chat_data = {
                        "message": query,
                        "conversation_id": f"quality_test_{int(time.time())}",
                        "user_id": self.test_user_id,
                        "context": {
                            "user_authenticated": True,
                            "has_uploaded_documents": True,
                            "quality_test": True
                        }
                    }
                    
                    headers = {'Authorization': f'Bearer {self.jwt_token}'}
                    url = f"{UPLOAD_PIPELINE_URL}{CHAT_ENDPOINT}"
                    async with session.post(url, json=chat_data, headers=headers) as response:
                        if response.status == 200:
                            chat_response = await response.json()
                            response_text = chat_response.get('response', '')
                            
                            # Assess response quality
                            quality_assessment = self._assess_response_quality(
                                response_text, query, expected_content, expected_type
                            )
                            
                            quality_results.append({
                                "query": query,
                                "expected_type": expected_type,
                                "quality_score": quality_assessment["overall_score"],
                                "content_relevance": quality_assessment["content_relevance"],
                                "completeness": quality_assessment["completeness"],
                                "clarity": quality_assessment["clarity"],
                                "response": response_text[:200] + "..." if len(response_text) > 200 else response_text
                            })
                        else:
                            quality_results.append({
                                "query": query,
                                "quality_score": 0,
                                "error": f"Query failed with status {response.status}"
                            })
            
            # Calculate overall quality metrics
            valid_results = [r for r in quality_results if "quality_score" in r and r["quality_score"] > 0]
            if valid_results:
                avg_quality_score = sum(r["quality_score"] for r in valid_results) / len(valid_results)
                avg_content_relevance = sum(r["content_relevance"] for r in valid_results) / len(valid_results)
                avg_completeness = sum(r["completeness"] for r in valid_results) / len(valid_results)
                avg_clarity = sum(r["clarity"] for r in valid_results) / len(valid_results)
            else:
                avg_quality_score = 0
                avg_content_relevance = 0
                avg_completeness = 0
                avg_clarity = 0
            
            return {
                "status": "PASS" if avg_quality_score >= 0.7 else "FAIL",
                "message": f"RAG quality assessment completed with {avg_quality_score:.2f} average quality score",
                "average_quality_score": avg_quality_score,
                "average_content_relevance": avg_content_relevance,
                "average_completeness": avg_completeness,
                "average_clarity": avg_clarity,
                "total_tests": len(quality_test_queries),
                "valid_results": len(valid_results),
                "quality_results": quality_results
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"RAG quality assessment test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_cross_document_rag(self) -> Dict[str, Any]:
        """Test RAG retrieval across multiple uploaded documents."""
        try:
            # Test queries that might require information from multiple documents
            cross_doc_queries = [
                "Compare my copays for different types of visits",
                "What are all my out-of-pocket costs?",
                "Summarize my complete benefits package",
                "What are my options for finding healthcare providers?",
                "What is my total annual coverage limit?"
            ]
            
            cross_doc_results = []
            async with aiohttp.ClientSession() as session:
                for query in cross_doc_queries:
                    chat_data = {
                        "message": query,
                        "conversation_id": f"cross_doc_{int(time.time())}",
                        "user_id": self.test_user_id,
                        "context": {
                            "user_authenticated": True,
                            "has_uploaded_documents": True,
                            "document_count": len(self.uploaded_documents),
                            "cross_document_query": True
                        }
                    }
                    
                    headers = {'Authorization': f'Bearer {self.jwt_token}'}
                    url = f"{UPLOAD_PIPELINE_URL}{CHAT_ENDPOINT}"
                    async with session.post(url, json=chat_data, headers=headers) as response:
                        if response.status == 200:
                            chat_response = await response.json()
                            response_text = chat_response.get('response', '')
                            
                            # Check if response shows evidence of cross-document synthesis
                            cross_doc_analysis = self._analyze_cross_document_synthesis(response_text, query)
                            
                            cross_doc_results.append({
                                "query": query,
                                "status": "PASS",
                                "response_length": len(response_text),
                                "cross_document_indicators": cross_doc_analysis["indicators"],
                                "synthesis_quality": cross_doc_analysis["synthesis_quality"],
                                "response": response_text[:300] + "..." if len(response_text) > 300 else response_text
                            })
                        else:
                            cross_doc_results.append({
                                "query": query,
                                "status": "FAIL",
                                "response_status": response.status,
                                "error": await response.text()
                            })
            
            # Calculate cross-document metrics
            successful_queries = [r for r in cross_doc_results if r["status"] == "PASS"]
            synthesis_scores = [r["synthesis_quality"] for r in successful_queries if "synthesis_quality" in r]
            avg_synthesis_quality = sum(synthesis_scores) / len(synthesis_scores) if synthesis_scores else 0
            
            return {
                "status": "PASS" if avg_synthesis_quality >= 0.6 else "FAIL",
                "message": f"Cross-document RAG completed with {avg_synthesis_quality:.2f} average synthesis quality",
                "average_synthesis_quality": avg_synthesis_quality,
                "total_queries": len(cross_doc_queries),
                "successful_queries": len(successful_queries),
                "cross_doc_results": cross_doc_results
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Cross-document RAG test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_rag_performance(self) -> Dict[str, Any]:
        """Test RAG performance with multiple concurrent queries."""
        try:
            # Test concurrent queries to assess performance
            concurrent_queries = [
                "What is my deductible?",
                "What are my copays?",
                "What services are covered?",
                "How do I find a doctor?",
                "What are my prescription benefits?"
            ]
            
            performance_results = []
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                # Execute queries concurrently
                tasks = []
                for i, query in enumerate(concurrent_queries):
                    task = self._execute_single_query(session, query, i)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        performance_results.append({
                            "query": concurrent_queries[i],
                            "status": "FAIL",
                            "error": str(result),
                            "response_time": 0
                        })
                    else:
                        performance_results.append(result)
            
            total_time = time.time() - start_time
            
            # Calculate performance metrics
            successful_queries = [r for r in performance_results if r["status"] == "PASS"]
            response_times = [r["response_time"] for r in successful_queries if "response_time" in r]
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)
            else:
                avg_response_time = 0
                max_response_time = 0
                min_response_time = 0
            
            return {
                "status": "PASS" if avg_response_time <= 5.0 else "FAIL",
                "message": f"RAG performance test completed with {avg_response_time:.2f}s average response time",
                "total_time": total_time,
                "average_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "min_response_time": min_response_time,
                "total_queries": len(concurrent_queries),
                "successful_queries": len(successful_queries),
                "performance_results": performance_results
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"RAG performance test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_single_query(self, session: aiohttp.ClientSession, query: str, query_index: int) -> Dict[str, Any]:
        """Execute a single query and measure performance."""
        start_time = time.time()
        
        chat_data = {
            "message": query,
            "conversation_id": f"perf_test_{query_index}_{int(time.time())}",
            "user_id": self.test_user_id,
            "context": {
                "user_authenticated": True,
                "has_uploaded_documents": True,
                "performance_test": True
            }
        }
        
        headers = {'Authorization': f'Bearer {self.jwt_token}'}
        url = f"{UPLOAD_PIPELINE_URL}{CHAT_ENDPOINT}"
        
        try:
            async with session.post(url, json=chat_data, headers=headers) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    chat_response = await response.json()
                    response_text = chat_response.get('response', '')
                    
                    return {
                        "query": query,
                        "status": "PASS",
                        "response_time": response_time,
                        "response_length": len(response_text),
                        "response": response_text[:100] + "..." if len(response_text) > 100 else response_text
                    }
                else:
                    return {
                        "query": query,
                        "status": "FAIL",
                        "response_time": response_time,
                        "response_status": response.status,
                        "error": await response.text()
                    }
        except Exception as e:
            return {
                "query": query,
                "status": "FAIL",
                "response_time": time.time() - start_time,
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
    
    def _calculate_quality_metrics(self, successful_queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall quality metrics from successful queries."""
        if not successful_queries:
            return {
                "average_insurance_content": 0,
                "average_relevance": 0,
                "average_completeness": 0,
                "total_responses": 0
            }
        
        total_insurance_content = sum(r["analysis"]["insurance_content_count"] for r in successful_queries)
        total_relevance = sum(r["analysis"]["relevance_score"] for r in successful_queries)
        total_completeness = sum(r["analysis"]["completeness_score"] for r in successful_queries)
        
        return {
            "average_insurance_content": total_insurance_content / len(successful_queries),
            "average_relevance": total_relevance / len(successful_queries),
            "average_completeness": total_completeness / len(successful_queries),
            "total_responses": len(successful_queries)
        }
    
    def _assess_response_quality(self, response: str, query: str, expected_content: List[str], expected_type: str) -> Dict[str, Any]:
        """Assess response quality based on query type and expected content."""
        response_lower = response.lower()
        
        # Content relevance (how many expected content items are present)
        content_matches = sum(1 for item in expected_content if item in response_lower)
        content_relevance = content_matches / len(expected_content) if expected_content else 0
        
        # Completeness (response length and detail)
        completeness = min(1.0, len(response) / 300)  # Assume 300 chars is complete
        
        # Clarity (sentence structure and readability)
        sentences = response.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        clarity = 1.0 - min(1.0, (avg_sentence_length - 15) / 20)  # Optimal around 15 words per sentence
        
        # Overall score
        overall_score = (content_relevance * 0.4 + completeness * 0.3 + clarity * 0.3)
        
        return {
            "content_relevance": content_relevance,
            "completeness": completeness,
            "clarity": clarity,
            "overall_score": overall_score
        }
    
    def _analyze_cross_document_synthesis(self, response: str, query: str) -> Dict[str, Any]:
        """Analyze if response shows evidence of cross-document synthesis."""
        response_lower = response.lower()
        
        # Indicators of cross-document synthesis
        synthesis_indicators = [
            "compare", "comparison", "different", "various", "multiple",
            "both", "all", "each", "respectively", "similarly",
            "however", "while", "whereas", "in contrast"
        ]
        
        indicators_found = [indicator for indicator in synthesis_indicators if indicator in response_lower]
        
        # Synthesis quality based on indicators and response structure
        synthesis_quality = min(1.0, len(indicators_found) / 3)  # Normalize to 0-1
        
        return {
            "indicators": indicators_found,
            "synthesis_quality": synthesis_quality
        }
    
    def _generate_summary(self, results: Dict[str, Any]):
        """Generate test summary."""
        print("\n" + "=" * 75)
        print("📊 PHASE 2 PRODUCTION RAG WITH UPLOADED DOCUMENTS TEST SUMMARY")
        print("=" * 75)
        
        print(f"Overall Status: {results['overall_status']}")
        print(f"Total Time: {results['total_time']:.2f} seconds")
        print(f"Test User ID: {results['test_user_id']}")
        print(f"Documents Uploaded: {len(self.uploaded_documents)}")
        
        print("\nTest Results:")
        for test_name, test_result in results["tests"].items():
            status_icon = "✅" if test_result["status"] == "PASS" else "❌"
            print(f"  {status_icon} {test_name}: {test_result['status']}")
            if "message" in test_result:
                print(f"      {test_result['message']}")
        
        # Show specific metrics
        if "production_rag_retrieval" in results["tests"]:
            rag_result = results["tests"]["production_rag_retrieval"]
            if "success_rate" in rag_result:
                print(f"\nRAG Success Rate: {rag_result['success_rate']:.1%}")
            if "quality_metrics" in rag_result:
                metrics = rag_result["quality_metrics"]
                print(f"Average Insurance Content: {metrics.get('average_insurance_content', 0):.1f}")
                print(f"Average Relevance: {metrics.get('average_relevance', 0):.2f}")
        
        if "rag_performance" in results["tests"]:
            perf_result = results["tests"]["rag_performance"]
            if "average_response_time" in perf_result:
                print(f"Average Response Time: {perf_result['average_response_time']:.2f}s")
        
        if results["overall_status"] == "PASS":
            print("\n🎉 Phase 2 Production RAG with Uploaded Documents Test PASSED!")
        else:
            print("\n❌ Phase 2 Production RAG with Uploaded Documents Test FAILED!")

async def main():
    """Run Phase 2 production RAG with upload test."""
    tester = Phase2ProductionRAGWithUploadTest()
    results = await tester.run_comprehensive_test()
    
    # Save results
    results_file = f"phase2_production_rag_upload_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: {results_file}")
    return results

if __name__ == "__main__":
    asyncio.run(main())
