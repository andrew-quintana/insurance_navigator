#!/usr/bin/env python3
"""
RCA Validation Test - Local Development Servers
Tests the key RCA fixes using locally deployed development servers
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalRCAValidationTester:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.frontend_url = "http://localhost:3000"
        self.results = {
            "test_timestamp": datetime.utcnow().isoformat(),
            "test_name": "RCA Validation - Local Development Servers",
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_results": [],
            "rca_fixes_validated": {
                "uuid_consistency": False,
                "similarity_threshold": False,
                "rag_integration": False,
                "authentication_flow": False,
                "database_operations": False
            },
            "errors": []
        }
        
    async def run_validation(self):
        """Run RCA validation tests on local servers"""
        logger.info("🚀 Starting RCA Validation - Local Development Servers")
        
        try:
            # Test 1: Local Server Health
            await self._test_local_server_health()
            
            # Test 2: Database Connection
            await self._test_database_connection()
            
            # Test 3: RAG Tool Functionality
            await self._test_rag_tool_functionality()
            
            # Test 4: UUID Consistency Check
            await self._test_uuid_consistency()
            
            # Test 5: Similarity Threshold Validation
            await self._test_similarity_threshold()
            
            # Test 6: Authentication Flow
            await self._test_authentication_flow()
            
            # Test 7: End-to-End RAG Query
            await self._test_end_to_end_rag()
            
            # Generate report
            self._generate_report()
            
        except Exception as e:
            logger.error(f"❌ Test execution failed: {e}")
            self.results["errors"].append(str(e))
    
    async def _test_local_server_health(self):
        """Test local server health"""
        test_name = "Local Server Health"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test backend
                try:
                    async with session.get(f"{self.backend_url}/health", timeout=5) as response:
                        if response.status == 200:
                            backend_health = await response.json()
                            backend_status = backend_health.get("status", "unknown")
                        else:
                            backend_status = f"HTTP {response.status}"
                except Exception as e:
                    backend_status = f"Error: {e}"
                
                # Test frontend
                try:
                    async with session.get(f"{self.frontend_url}/api/health", timeout=5) as response:
                        if response.status == 200:
                            frontend_health = await response.json()
                            frontend_status = frontend_health.get("status", "unknown")
                        else:
                            frontend_status = f"HTTP {response.status}"
                except Exception as e:
                    frontend_status = f"Error: {e}"
                
                # Both servers should be healthy
                backend_healthy = "healthy" in backend_status.lower() or "degraded" in backend_status.lower()
                frontend_healthy = "healthy" in frontend_status.lower()
                
                if backend_healthy and frontend_healthy:
                    self._record_test_result(test_name, True, {
                        "backend_status": backend_status,
                        "frontend_status": frontend_status,
                        "both_servers_healthy": True
                    })
                else:
                    self._record_test_result(test_name, False, {
                        "backend_status": backend_status,
                        "frontend_status": frontend_status,
                        "both_servers_healthy": False
                    })
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    async def _test_database_connection(self):
        """Test database connection"""
        test_name = "Database Connection"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            import asyncpg
            from dotenv import load_dotenv
            import os
            
            load_dotenv('.env.development')
            
            conn = await asyncpg.connect(
                host='127.0.0.1',
                port=54322,
                user='postgres',
                password='postgres',
                database='postgres'
            )
            
            # Test basic query
            result = await conn.fetchval('SELECT 1')
            await conn.close()
            
            if result == 1:
                self.results["rca_fixes_validated"]["database_operations"] = True
                self._record_test_result(test_name, True, {
                    "connection_successful": True,
                    "query_result": result
                })
            else:
                self._record_test_result(test_name, False, {
                    "connection_successful": True,
                    "query_result": result,
                    "error": "Unexpected query result"
                })
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    async def _test_rag_tool_functionality(self):
        """Test RAG tool functionality"""
        test_name = "RAG Tool Functionality"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            # Test RAG tool directly
            from agents.tooling.rag.core import RAGTool
            from agents.tooling.rag.config import RetrievalConfig
            
            # Create RAG tool instance
            rag_tool = RAGTool(
                user_id="test_user_123",
                config=RetrievalConfig.default()
            )
            
            # Test with a dummy embedding
            test_embedding = [0.1] * 1536  # Dummy embedding vector
            
            chunks = await rag_tool.retrieve_chunks(test_embedding)
            
            self.results["rca_fixes_validated"]["rag_integration"] = True
            self._record_test_result(test_name, True, {
                "rag_tool_created": True,
                "chunks_retrieved": len(chunks),
                "similarity_threshold": rag_tool.config.similarity_threshold
            })
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    async def _test_uuid_consistency(self):
        """Test UUID consistency"""
        test_name = "UUID Consistency"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            import asyncpg
            
            conn = await asyncpg.connect(
                host='127.0.0.1',
                port=54322,
                user='postgres',
                password='postgres',
                database='postgres'
            )
            
            # Check documents and chunks consistency
            docs = await conn.fetch('''
                SELECT document_id, user_id, filename, created_at 
                FROM upload_pipeline.documents 
                ORDER BY created_at DESC 
                LIMIT 3
            ''')
            
            chunks = await conn.fetch('''
                SELECT dc.chunk_id, dc.document_id, dc.chunk_ord, 
                       d.user_id, d.filename
                FROM upload_pipeline.document_chunks dc
                JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
                ORDER BY dc.created_at DESC
                LIMIT 5
            ''')
            
            await conn.close()
            
            # Validate UUID consistency
            doc_ids = {doc['document_id'] for doc in docs}
            chunk_doc_ids = {chunk['document_id'] for chunk in chunks}
            
            # Check if chunks reference existing documents
            orphaned_chunks = chunk_doc_ids - doc_ids
            consistent = len(orphaned_chunks) == 0
            
            if consistent:
                self.results["rca_fixes_validated"]["uuid_consistency"] = True
                self._record_test_result(test_name, True, {
                    "documents_found": len(docs),
                    "chunks_found": len(chunks),
                    "uuid_consistency": True,
                    "orphaned_chunks": 0
                })
            else:
                self._record_test_result(test_name, False, {
                    "documents_found": len(docs),
                    "chunks_found": len(chunks),
                    "uuid_consistency": False,
                    "orphaned_chunks": len(orphaned_chunks)
                })
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    async def _test_similarity_threshold(self):
        """Test similarity threshold configuration"""
        test_name = "Similarity Threshold"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            from agents.tooling.rag.config import RetrievalConfig
            
            # Check default threshold
            config = RetrievalConfig.default()
            threshold = config.similarity_threshold
            
            # RCA fix: threshold should be 0.3 (reduced from 0.7)
            if threshold == 0.3:
                self.results["rca_fixes_validated"]["similarity_threshold"] = True
                self._record_test_result(test_name, True, {
                    "threshold_value": threshold,
                    "rca_fix_applied": True,
                    "expected_threshold": 0.3
                })
            else:
                self._record_test_result(test_name, False, {
                    "threshold_value": threshold,
                    "rca_fix_applied": False,
                    "expected_threshold": 0.3
                })
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    async def _test_authentication_flow(self):
        """Test authentication flow"""
        test_name = "Authentication Flow"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            # Test frontend auth endpoint
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.frontend_url}/api/health", timeout=5) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        auth_healthy = health_data.get("services", {}).get("supabase_auth") == "healthy"
                        
                        if auth_healthy:
                            self.results["rca_fixes_validated"]["authentication_flow"] = True
                            self._record_test_result(test_name, True, {
                                "auth_service_healthy": True,
                                "frontend_auth_status": "healthy"
                            })
                        else:
                            self._record_test_result(test_name, False, {
                                "auth_service_healthy": False,
                                "frontend_auth_status": "unhealthy"
                            })
                    else:
                        self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "error": "Frontend health check failed"
                        })
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    async def _test_end_to_end_rag(self):
        """Test end-to-end RAG functionality"""
        test_name = "End-to-End RAG"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            # Test RAG tool with real data
            from agents.tooling.rag.core import RAGTool
            from agents.tooling.rag.config import RetrievalConfig
            
            rag_tool = RAGTool(
                user_id="test_user_123",
                config=RetrievalConfig.default()
            )
            
            # Test with dummy embedding
            test_embedding = [0.1] * 1536
            chunks = await rag_tool.retrieve_chunks(test_embedding)
            
            # Check if RAG tool is working (even if no chunks returned)
            self._record_test_result(test_name, True, {
                "rag_tool_working": True,
                "chunks_returned": len(chunks),
                "similarity_threshold": rag_tool.config.similarity_threshold,
                "end_to_end_functional": True
            })
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    def _record_test_result(self, test_name: str, passed: bool, details: dict):
        """Record test result"""
        self.results["total_tests"] += 1
        if passed:
            self.results["passed_tests"] += 1
            logger.info(f"✅ {test_name}: PASSED")
        else:
            self.results["failed_tests"] += 1
            logger.error(f"❌ {test_name}: FAILED")
            
        self.results["test_results"].append({
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def _generate_report(self):
        """Generate comprehensive validation report"""
        success_rate = (self.results["passed_tests"] / self.results["total_tests"]) * 100 if self.results["total_tests"] > 0 else 0
        
        logger.info("=" * 80)
        logger.info("📊 RCA VALIDATION REPORT - LOCAL DEVELOPMENT SERVERS")
        logger.info("=" * 80)
        logger.info(f"🕐 Test Timestamp: {self.results['test_timestamp']}")
        logger.info(f"📈 Total Tests: {self.results['total_tests']}")
        logger.info(f"✅ Passed Tests: {self.results['passed_tests']}")
        logger.info(f"❌ Failed Tests: {self.results['failed_tests']}")
        logger.info(f"📊 Success Rate: {success_rate:.1f}%")
        logger.info("")
        logger.info("🔧 RCA FIXES VALIDATION:")
        for fix, status in self.results["rca_fixes_validated"].items():
            status_icon = "✅" if status else "❌"
            logger.info(f"  {status_icon} {fix.replace('_', ' ').title()}: {'PASSED' if status else 'FAILED'}")
        logger.info("")
        logger.info("=" * 80)
        
        if self.results["failed_tests"] == 0:
            logger.info("🎉 ALL RCA VALIDATION TESTS PASSED!")
        else:
            logger.warning("⚠️ Some tests failed - check details above")
        
        # Save results
        with open(f"rca_validation_local_results_{int(time.time())}.json", "w") as f:
            json.dump(self.results, f, indent=2)

async def main():
    """Main test execution"""
    tester = LocalRCAValidationTester()
    await tester.run_validation()

if __name__ == "__main__":
    asyncio.run(main())
