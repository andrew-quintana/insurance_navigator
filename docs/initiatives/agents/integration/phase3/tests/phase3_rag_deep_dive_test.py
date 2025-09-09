#!/usr/bin/env python3
"""
Phase 3 RAG Deep Dive Test
Comprehensive debugging of RAG system to identify why 0 chunks are retrieved
"""

import asyncio
import aiohttp
import json
import time
import uuid
from typing import Dict, Any, List, Optional
import logging
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append('/Users/aq_home/1Projects/accessa/insurance_navigator')

# Load environment variables
load_dotenv('.env.development')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase3RAGDeepDiveTest:
    """Deep dive test to debug RAG system issues."""
    
    def __init__(self):
        self.base_url = "***REMOVED***"
        self.test_user_id = str(uuid.uuid4())
        self.test_email = f"rag_test_{int(time.time())}@example.com"
        self.test_password = "test_password_123"
        self.auth_token = None
        self.results = {
            "test_name": "Phase 3 RAG Deep Dive Test",
            "timestamp": time.time(),
            "test_user_id": self.test_user_id,
            "test_email": self.test_email,
            "tests": {},
            "summary": {}
        }
    
    async def run_test(self, test_name: str, test_func):
        """Run a single test and record results."""
        logger.info(f"Running test: {test_name}")
        start_time = time.time()
        
        try:
            result = await test_func()
            duration = time.time() - start_time
            
            self.results["tests"][test_name] = {
                "status": "PASSED",
                "duration": duration,
                "details": result
            }
            logger.info(f"✅ {test_name} - PASSED ({duration:.2f}s)")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.results["tests"][test_name] = {
                "status": "FAILED",
                "duration": duration,
                "error": str(e)
            }
            logger.error(f"❌ {test_name} - FAILED ({duration:.2f}s): {str(e)}")
            return False
    
    async def test_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity and data availability."""
        try:
            import asyncpg
            
            # Connect to database
            conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:54322/postgres')
            
            # Check upload_pipeline schema
            schemas = await conn.fetch("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'upload_pipeline'")
            schema_exists = len(schemas) > 0
            
            if not schema_exists:
                raise Exception("upload_pipeline schema does not exist")
            
            # Check tables
            tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'upload_pipeline'")
            table_names = [t['table_name'] for t in tables]
            
            # Check document_chunks table
            chunk_count = 0
            chunks_with_embeddings = 0
            if 'document_chunks' in table_names:
                chunk_count = await conn.fetchval('SELECT COUNT(*) FROM upload_pipeline.document_chunks')
                chunks_with_embeddings = await conn.fetchval('SELECT COUNT(*) FROM upload_pipeline.document_chunks WHERE embedding IS NOT NULL')
            
            # Check documents table
            doc_count = 0
            if 'documents' in table_names:
                doc_count = await conn.fetchval('SELECT COUNT(*) FROM upload_pipeline.documents')
            
            # Get sample user_id
            sample_user_id = await conn.fetchval('SELECT user_id FROM upload_pipeline.documents LIMIT 1')
            
            await conn.close()
            
            return {
                "schema_exists": schema_exists,
                "tables": table_names,
                "chunk_count": chunk_count,
                "chunks_with_embeddings": chunks_with_embeddings,
                "doc_count": doc_count,
                "sample_user_id": sample_user_id
            }
            
        except Exception as e:
            raise Exception(f"Database connectivity test failed: {e}")
    
    async def test_embedding_generation(self) -> Dict[str, Any]:
        """Test embedding generation with OpenAI API."""
        try:
            import openai
            
            # Set API key
            openai.api_key = os.getenv('OPENAI_API_KEY')
            if not openai.api_key:
                raise Exception("OPENAI_API_KEY not set")
            
            # Test query
            test_query = "What is the deductible for health insurance?"
            
            # Generate embedding
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=test_query
            )
            
            embedding = response.data[0].embedding
            
            return {
                "query": test_query,
                "embedding_dimensions": len(embedding),
                "embedding_preview": embedding[:5],  # First 5 values
                "api_key_available": True
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "api_key_available": False
            }
    
    async def test_similarity_search_direct(self) -> Dict[str, Any]:
        """Test similarity search directly against database."""
        try:
            import asyncpg
            import openai
            
            # Connect to database
            conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:54322/postgres')
            
            # Get sample user_id
            user_id = await conn.fetchval('SELECT user_id FROM upload_pipeline.documents LIMIT 1')
            
            # Generate embedding
            openai.api_key = os.getenv('OPENAI_API_KEY')
            test_query = "What is the deductible for health insurance?"
            
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=test_query
            )
            query_embedding = response.data[0].embedding
            
            # Convert to PostgreSQL vector format
            vector_string = '[' + ','.join(str(x) for x in query_embedding) + ']'
            
            # Test different similarity thresholds
            thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
            results = {}
            
            for threshold in thresholds:
                sql = f"""
                    SELECT dc.chunk_id, dc.document_id, dc.chunk_ord as chunk_index, dc.text as content,
                           1 - (dc.embedding <=> $1::vector) as similarity
                    FROM upload_pipeline.document_chunks dc
                    JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
                    WHERE d.user_id = $2
                      AND dc.embedding IS NOT NULL
                      AND 1 - (dc.embedding <=> $1::vector) > $3
                    ORDER BY dc.embedding <=> $1::vector
                    LIMIT 5
                """
                
                rows = await conn.fetch(sql, vector_string, user_id, threshold, 5)
                results[f"threshold_{threshold}"] = {
                    "chunks_found": len(rows),
                    "chunks": [
                        {
                            "chunk_id": row["chunk_id"],
                            "similarity": float(row["similarity"]),
                            "content_preview": row["content"][:100]
                        }
                        for row in rows
                    ]
                }
            
            # Also test without user filter
            sql_no_user = f"""
                SELECT dc.chunk_id, dc.document_id, dc.chunk_ord as chunk_index, dc.text as content,
                       1 - (dc.embedding <=> $1::vector) as similarity
                FROM upload_pipeline.document_chunks dc
                WHERE dc.embedding IS NOT NULL
                  AND 1 - (dc.embedding <=> $1::vector) > $2
                ORDER BY dc.embedding <=> $1::vector
                LIMIT 5
            """
            
            no_user_results = {}
            for threshold in [0.1, 0.2, 0.3, 0.4, 0.5]:
                rows = await conn.fetch(sql_no_user, vector_string, threshold, 5)
                no_user_results[f"threshold_{threshold}"] = {
                    "chunks_found": len(rows),
                    "chunks": [
                        {
                            "chunk_id": row["chunk_id"],
                            "similarity": float(row["similarity"]),
                            "content_preview": row["content"][:100]
                        }
                        for row in rows
                    ]
                }
            
            await conn.close()
            
            return {
                "user_id": user_id,
                "query": test_query,
                "embedding_dimensions": len(query_embedding),
                "user_filtered_results": results,
                "no_user_filter_results": no_user_results
            }
            
        except Exception as e:
            raise Exception(f"Similarity search test failed: {e}")
    
    async def test_rag_tool_retrieval(self) -> Dict[str, Any]:
        """Test RAGTool retrieval with different configurations."""
        try:
            from agents.tooling.rag.core import RAGTool, RetrievalConfig
            import openai
            
            # Set API key
            openai.api_key = os.getenv('OPENAI_API_KEY')
            
            # Get sample user_id
            import asyncpg
            conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:54322/postgres')
            user_id = await conn.fetchval('SELECT user_id FROM upload_pipeline.documents LIMIT 1')
            await conn.close()
            
            # Test query
            test_query = "What is the deductible for health insurance?"
            
            # Generate embedding
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=test_query
            )
            query_embedding = response.data[0].embedding
            
            # Test with different similarity thresholds
            thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
            results = {}
            
            for threshold in thresholds:
                config = RetrievalConfig.default()
                config.similarity_threshold = threshold
                config.max_chunks = 5
                
                rag_tool = RAGTool(user_id=user_id, config=config)
                chunks = await rag_tool.retrieve_chunks(query_embedding)
                
                results[f"threshold_{threshold}"] = {
                    "chunks_retrieved": len(chunks),
                    "chunks": [
                        {
                            "chunk_id": chunk.id,
                            "similarity": chunk.similarity,
                            "content_preview": chunk.content[:100] if chunk.content else "No content"
                        }
                        for chunk in chunks
                    ]
                }
            
            return {
                "user_id": user_id,
                "query": test_query,
                "embedding_dimensions": len(query_embedding),
                "rag_tool_results": results
            }
            
        except Exception as e:
            raise Exception(f"RAGTool retrieval test failed: {e}")
    
    async def test_information_retrieval_agent(self) -> Dict[str, Any]:
        """Test InformationRetrievalAgent RAG functionality."""
        try:
            from agents.patient_navigator.information_retrieval.agent import InformationRetrievalAgent
            import openai
            
            # Set API key
            openai.api_key = os.getenv('OPENAI_API_KEY')
            
            # Get sample user_id
            import asyncpg
            conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:54322/postgres')
            user_id = await conn.fetchval('SELECT user_id FROM upload_pipeline.documents LIMIT 1')
            await conn.close()
            
            # Create agent
            agent = InformationRetrievalAgent()
            
            # Test query
            test_query = "What is the deductible for health insurance?"
            
            # Test retrieval
            chunks = await agent._retrieve_chunks(test_query, user_id)
            
            return {
                "user_id": user_id,
                "query": test_query,
                "chunks_retrieved": len(chunks),
                "chunks": [
                    {
                        "chunk_id": chunk.id,
                        "similarity": chunk.similarity,
                        "content_preview": chunk.content[:100] if chunk.content else "No content"
                    }
                    for chunk in chunks
                ]
            }
            
        except Exception as e:
            raise Exception(f"InformationRetrievalAgent test failed: {e}")
    
    async def test_cloud_rag_integration(self) -> Dict[str, Any]:
        """Test RAG integration through cloud API."""
        try:
            # First authenticate
            async with aiohttp.ClientSession() as session:
                # Register user
                registration_data = {
                    "email": self.test_email,
                    "password": self.test_password,
                    "user_id": self.test_user_id
                }
                
                async with session.post(f"{self.base_url}/register", json=registration_data) as response:
                    if response.status != 200:
                        raise Exception(f"Registration failed: {response.status}")
                
                # Login
                login_data = {
                    "email": self.test_email,
                    "password": self.test_password
                }
                
                async with session.post(f"{self.base_url}/login", json=login_data) as response:
                    if response.status != 200:
                        raise Exception(f"Login failed: {response.status}")
                    
                    result = await response.json()
                    self.auth_token = result.get("access_token")
                
                if not self.auth_token:
                    raise Exception("No authentication token received")
                
                # Test chat endpoint with RAG query
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                chat_data = {
                    "message": "What is the deductible for health insurance?",
                    "user_id": self.test_user_id
                }
                
                async with session.post(f"{self.base_url}/chat", json=chat_data, headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"Chat request failed: {response.status}")
                    
                    result = await response.json()
                    response_text = result.get("response", "")
                    
                    return {
                        "query": chat_data["message"],
                        "response_received": True,
                        "response_length": len(response_text),
                        "response_preview": response_text[:200],
                        "contains_insurance_info": any(keyword in response_text.lower() for keyword in [
                            "deductible", "insurance", "coverage", "plan", "benefits"
                        ])
                    }
        
        except Exception as e:
            raise Exception(f"Cloud RAG integration test failed: {e}")
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive RAG deep dive test."""
        logger.info("🔍 Starting Phase 3 RAG Deep Dive Test")
        logger.info("=" * 60)
        
        # Run all tests
        test_functions = [
            ("Database Connectivity", self.test_database_connectivity),
            ("Embedding Generation", self.test_embedding_generation),
            ("Similarity Search Direct", self.test_similarity_search_direct),
            ("RAGTool Retrieval", self.test_rag_tool_retrieval),
            ("Information Retrieval Agent", self.test_information_retrieval_agent),
            ("Cloud RAG Integration", self.test_cloud_rag_integration)
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_func in test_functions:
            success = await self.run_test(test_name, test_func)
            if success:
                passed_tests += 1
        
        # Generate summary
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100,
            "overall_status": "PASSED" if passed_tests == total_tests else "FAILED"
        }
        
        # Log summary
        logger.info("=" * 60)
        logger.info("📊 PHASE 3 RAG DEEP DIVE TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Overall Status: {self.results['summary']['overall_status']}")
        logger.info(f"Total Time: {time.time() - self.results['timestamp']:.2f} seconds")
        logger.info(f"Test User ID: {self.test_user_id}")
        logger.info("")
        logger.info("Test Results:")
        
        for test_name, test_result in self.results["tests"].items():
            status_icon = "✅" if test_result["status"] == "PASSED" else "❌"
            logger.info(f"  {status_icon} {test_name}: {test_result['status']}")
            if test_result["status"] == "FAILED" and "error" in test_result:
                logger.info(f"      Error: {test_result['error']}")
        
        logger.info("")
        logger.info(f"📊 Summary: {passed_tests}/{total_tests} tests passed ({self.results['summary']['success_rate']:.1f}%)")
        
        if self.results['summary']['overall_status'] == "PASSED":
            logger.info("🎉 Phase 3 RAG Deep Dive Test PASSED!")
        else:
            logger.info("❌ Phase 3 RAG Deep Dive Test FAILED!")
        
        # Save results
        results_file = f"phase3_rag_deep_dive_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"📁 Results saved to: {results_file}")
        
        return self.results

async def main():
    """Main function to run the test."""
    test = Phase3RAGDeepDiveTest()
    await test.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
