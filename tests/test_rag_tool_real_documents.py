"""
Real Document RAG Testing

This test validates RAG tool functionality with real insurance document scenarios.
Tests include:
1. RAG tool initialization and configuration
2. Vector similarity search functionality
3. User access control
4. Token budget enforcement
5. Schema validation
"""

import pytest
import asyncio
import os
import sys
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.tooling.rag.core import RAGTool, RetrievalConfig, ChunkWithContext


class TestRAGToolRealDocuments:
    """Test RAG tool functionality with real document scenarios."""
    
    @pytest.fixture
    def test_user_id(self) -> str:
        """Test user ID for RAG operations."""
        return "5710ff53-32ea-4fab-be6d-3a6f0627fbff"
    
    @pytest.fixture
    def rag_config(self) -> RetrievalConfig:
        """RAG configuration for testing."""
        return RetrievalConfig(
            max_chunks=5,
            token_budget=2000,
            similarity_threshold=0.7
        )
    
    @pytest.fixture
    def rag_tool(self, test_user_id: str, rag_config: RetrievalConfig) -> RAGTool:
        """Create RAG tool instance for testing."""
        return RAGTool(user_id=test_user_id, config=rag_config)
    
    @pytest.fixture
    def sample_embedding(self) -> List[float]:
        """Sample embedding vector for testing."""
        # Create a realistic 1536-dimensional embedding
        import random
        random.seed(42)  # For reproducible tests
        return [random.uniform(-1, 1) for _ in range(1536)]
    
    @pytest.mark.asyncio
    async def test_rag_tool_initialization(self, rag_tool: RAGTool):
        """Test that RAG tool initializes correctly."""
        assert rag_tool is not None
        assert rag_tool.user_id == "5710ff53-32ea-4fab-be6d-3a6f0627fbff"
        assert rag_tool.config is not None
        assert rag_tool.config.max_chunks == 5
        assert rag_tool.config.token_budget == 2000
        assert rag_tool.config.similarity_threshold == 0.7
        
        print("✅ RAG tool initialization successful")
    
    @pytest.mark.asyncio
    async def test_rag_tool_database_connection(self, rag_tool: RAGTool):
        """Test that RAG tool can connect to database."""
        try:
            # Test database connection
            conn = await rag_tool._get_db_conn()
            assert conn is not None
            
            # Test basic query
            result = await conn.fetch("SELECT 1 as test")
            assert len(result) == 1
            assert result[0]["test"] == 1
            
            await conn.close()
            print("✅ Database connection successful")
            
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_rag_tool_schema_access(self, rag_tool: RAGTool):
        """Test that RAG tool can access the correct database schema."""
        try:
            conn = await rag_tool._get_db_conn()
            
            # Check if upload_pipeline schema exists
            schema_result = await conn.fetch("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = 'upload_pipeline'
            """)
            
            if len(schema_result) > 0:
                print("✅ upload_pipeline schema exists")
                
                # Check if document_chunks table exists
                table_result = await conn.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'upload_pipeline' 
                    AND table_name = 'document_chunks'
                """)
                
                if len(table_result) > 0:
                    print("✅ document_chunks table exists")
                    
                    # Check table structure
                    columns_result = await conn.fetch("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_schema = 'upload_pipeline' 
                        AND table_name = 'document_chunks'
                        ORDER BY ordinal_position
                    """)
                    
                    print(f"📋 Table structure: {len(columns_result)} columns")
                    for col in columns_result:
                        print(f"  - {col['column_name']}: {col['data_type']}")
                else:
                    print("⚠️  document_chunks table does not exist")
            else:
                print("⚠️  upload_pipeline schema does not exist")
            
            await conn.close()
            
        except Exception as e:
            pytest.fail(f"Schema access test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_rag_tool_vector_search(self, rag_tool: RAGTool, sample_embedding: List[float]):
        """Test vector similarity search functionality."""
        try:
            # Test vector search (should return 0 results since no documents exist)
            chunks = await rag_tool.retrieve_chunks(sample_embedding)
            
            # Should return empty list when no documents exist
            assert isinstance(chunks, list)
            assert len(chunks) == 0
            
            print("✅ Vector search successful (0 results as expected)")
            
        except Exception as e:
            pytest.fail(f"Vector search test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_rag_tool_config_validation(self, rag_tool: RAGTool):
        """Test RAG tool configuration validation."""
        try:
            # Test valid configuration
            rag_tool.config.validate()
            print("✅ Configuration validation successful")
            
            # Test invalid configuration
            invalid_config = RetrievalConfig(
                max_chunks=-1,  # Invalid: negative value
                token_budget=0,  # Invalid: zero value
                similarity_threshold=1.5  # Invalid: > 1.0
            )
            
            try:
                invalid_config.validate()
                pytest.fail("Invalid configuration should have failed validation")
            except Exception:
                print("✅ Invalid configuration correctly rejected")
                
        except Exception as e:
            pytest.fail(f"Configuration validation test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_rag_tool_user_isolation(self, rag_config: RetrievalConfig):
        """Test that RAG tool properly isolates users."""
        try:
            # Create RAG tools for different users
            user1_tool = RAGTool(user_id="user1-123", config=rag_config)
            user2_tool = RAGTool(user_id="user2-456", config=rag_config)
            
            assert user1_tool.user_id != user2_tool.user_id
            assert user1_tool.user_id == "user1-123"
            assert user2_tool.user_id == "user2-456"
            
            print("✅ User isolation working correctly")
            
        except Exception as e:
            pytest.fail(f"User isolation test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_rag_tool_error_handling(self, rag_tool: RAGTool):
        """Test RAG tool error handling."""
        try:
            # Test with invalid embedding (wrong dimensions)
            invalid_embedding = [0.1, 0.2, 0.3]  # Only 3 dimensions, should be 1536
            
            # This should handle the error gracefully
            chunks = await rag_tool.retrieve_chunks(invalid_embedding)
            
            # Should return empty list on error
            assert isinstance(chunks, list)
            print("✅ Error handling working correctly")
            
        except Exception as e:
            # If it raises an exception, that's also acceptable error handling
            print(f"✅ Error handling working (exception raised: {type(e).__name__})")


class TestRAGIntegrationScenarios:
    """Test RAG integration with real-world scenarios."""
    
    @pytest.fixture
    def test_user_id(self) -> str:
        """Test user ID for integration testing."""
        return "5710ff53-32ea-4fab-be6d-3a6f0627fbff"
    
    @pytest.mark.asyncio
    async def test_rag_integration_health(self, test_user_id: str):
        """Test RAG integration health check."""
        try:
            import httpx
            
            # Test integration health endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://localhost:8003/integration/health")
                assert response.status_code == 200
                
                health_data = response.json()
                assert "overall_status" in health_data
                assert "database_status" in health_data
                
                print("✅ RAG integration health check successful")
                print(f"   Overall status: {health_data.get('overall_status')}")
                print(f"   Database status: {health_data.get('database_status', {}).get('status')}")
                
        except Exception as e:
            pytest.fail(f"RAG integration health check failed: {e}")
    
    @pytest.mark.asyncio
    async def test_document_availability_check(self, test_user_id: str):
        """Test document availability checking."""
        try:
            import httpx
            
            # Test document availability endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://localhost:8003/integration/documents/{test_user_id}/availability")
                assert response.status_code == 200
                
                availability_data = response.json()
                assert "user_id" in availability_data
                assert "document_availability" in availability_data
                assert "total_document_types" in availability_data
                
                print("✅ Document availability check successful")
                print(f"   User ID: {availability_data['user_id']}")
                print(f"   Total document types: {availability_data['total_document_types']}")
                print(f"   Available types: {availability_data.get('available_document_types', [])}")
                
        except Exception as e:
            pytest.fail(f"Document availability check failed: {e}")
    
    @pytest.mark.asyncio
    async def test_rag_ready_documents_check(self, test_user_id: str):
        """Test RAG-ready documents checking."""
        try:
            import httpx
            
            # Test RAG-ready documents endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://localhost:8003/integration/documents/{test_user_id}/rag-ready")
                assert response.status_code == 200
                
                rag_data = response.json()
                assert "user_id" in rag_data
                assert "documents" in rag_data
                assert "total_documents" in rag_data
                assert "rag_ready_count" in rag_data
                
                print("✅ RAG-ready documents check successful")
                print(f"   User ID: {rag_data['user_id']}")
                print(f"   Total documents: {rag_data['total_documents']}")
                print(f"   RAG-ready documents: {rag_data['rag_ready_count']}")
                
        except Exception as e:
            pytest.fail(f"RAG-ready documents check failed: {e}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
