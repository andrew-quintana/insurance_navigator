#!/usr/bin/env python3
"""
Isolated RAG System Test

This script tests the updated RAG system with real document chunks
to verify that the embedding generation and similarity calculation work correctly.
"""

import asyncio
import os
import sys
from pathlib import Path
import asyncpg
import logging
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test database connection and get sample chunks."""
    print("🔍 Testing Database Connection")
    print("-" * 50)
    
    # Use production database URL
    database_url = "postgresql://postgres.znvwzkdblknkkztqyfnu:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    
    try:
        conn = await asyncpg.connect(database_url, statement_cache_size=0)
        print("✅ Database connected successfully")
        
        # Get sample document chunks
        user_id = "0905435f-50e2-428a-9a59-0c92f27f5097"
        
        sql = """
            SELECT dc.chunk_id, dc.text as content, dc.embedding,
                   d.document_id, d.filename as doc_title
            FROM upload_pipeline.document_chunks dc
            JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
            WHERE d.user_id = $1
              AND dc.embedding IS NOT NULL
            ORDER BY dc.chunk_id
            LIMIT 5
        """
        
        rows = await conn.fetch(sql, user_id)
        print(f"✅ Found {len(rows)} document chunks")
        
        if not rows:
            print("❌ No document chunks found")
            return None, None
        
        # Display sample chunks
        for i, row in enumerate(rows):
            print(f"\n   Chunk {i+1}:")
            print(f"     ID: {row['chunk_id']}")
            print(f"     Document: {row['doc_title']}")
            print(f"     Content: {row['content'][:100]}...")
            print(f"     Embedding: {len(row['embedding'])} dimensions")
        
        await conn.close()
        return database_url, rows
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None, None

async def test_embedding_generation():
    """Test the updated embedding generation."""
    print("\n🔍 Testing Embedding Generation")
    print("-" * 50)
    
    # Test query text
    query_text = "Expert Query Reframe:\n\nThe member is inquiring about coverage for diagnostic imaging services, specifically radiographic (x-ray) examinations. This would fall under the plan's physician services benefit, which typically requires the member to obtain a referral or prior authorization from their primary care provider before receiving the service. The member may be subject to applicable cost-sharing, such as a copayment or coinsurance, depending on the terms of their health insurance plan. Coverage would also be contingent on receiving services from an in-network radiology provider."
    
    try:
        from openai import AsyncOpenAI
        
        # Get OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment")
            print("   Please set OPENAI_API_KEY environment variable")
            return None
        
        print(f"✅ OpenAI API key found: {api_key[:10]}...")
        
        # Initialize OpenAI client with the same configuration as the updated RAG tool
        client = AsyncOpenAI(
            api_key=api_key,
            max_retries=5,
            timeout=60.0
        )
        
        # Generate query embedding
        print("Generating query embedding...")
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=query_text,
            encoding_format="float"
        )
        query_embedding = response.data[0].embedding
        
        print(f"✅ Query embedding generated: {len(query_embedding)} dimensions")
        print(f"   First 5 values: {query_embedding[:5]}")
        print(f"   Min: {min(query_embedding):.6f}, Max: {max(query_embedding):.6f}")
        
        # Validate embedding
        if len(query_embedding) != 1536:
            print(f"❌ Wrong embedding dimension: {len(query_embedding)} (expected 1536)")
            return None
        
        if all(abs(x) < 1e-6 for x in query_embedding):
            print("❌ Mock embedding detected (all values near zero)")
            return None
        
        print("✅ Embedding validation passed")
        return query_embedding
        
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return None

async def test_similarity_calculation(query_embedding: List[float], database_url: str):
    """Test similarity calculation with real document chunks."""
    print("\n🔍 Testing Similarity Calculation")
    print("-" * 50)
    
    try:
        conn = await asyncpg.connect(database_url, statement_cache_size=0)
        
        user_id = "0905435f-50e2-428a-9a59-0c92f27f5097"
        vector_string = '[' + ','.join(str(x) for x in query_embedding) + ']'
        
        # Test the exact query from the RAG tool
        sql = """
            SELECT dc.chunk_id, dc.text as content,
                   1 - (dc.embedding <=> $1::vector(1536)) as similarity
            FROM upload_pipeline.document_chunks dc
            JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
            WHERE d.user_id = $2
              AND dc.embedding IS NOT NULL
            ORDER BY dc.embedding <=> $1::vector(1536)
            LIMIT 10
        """
        
        rows = await conn.fetch(sql, vector_string, user_id)
        print(f"✅ Database similarity query returned {len(rows)} results")
        
        similarities = []
        for i, row in enumerate(rows):
            similarity = float(row['similarity'])
            similarities.append(similarity)
            print(f"   Result {i+1}: similarity = {similarity:.6f}")
            print(f"      Content: {row['content'][:80]}...")
        
        if similarities:
            print(f"\n📊 Similarity Statistics:")
            print(f"   Average: {sum(similarities)/len(similarities):.6f}")
            print(f"   Min: {min(similarities):.6f}")
            print(f"   Max: {max(similarities):.6f}")
            print(f"   Above 0.3 threshold: {sum(1 for s in similarities if s > 0.3)}/{len(similarities)}")
            
            if any(s > 0.3 for s in similarities):
                print("✅ SUCCESS: Found chunks above similarity threshold!")
            else:
                print("⚠️  WARNING: No chunks above 0.3 threshold, but this might be expected depending on content")
        
        await conn.close()
        return similarities
        
    except Exception as e:
        print(f"❌ Database similarity query failed: {e}")
        return None

async def test_rag_tool_integration():
    """Test the actual RAG tool with the updated code."""
    print("\n🔍 Testing RAG Tool Integration")
    print("-" * 50)
    
    try:
        # Import the updated RAG tool
        from agents.tooling.rag.core import RAGTool, RetrievalConfig
        
        # Create RAG tool instance
        user_id = "0905435f-50e2-428a-9a59-0c92f27f5097"
        config = RetrievalConfig(
            similarity_threshold=0.3,
            max_chunks=10,
            token_budget=4000
        )
        
        rag_tool = RAGTool(user_id=user_id, config=config)
        print("✅ RAG tool initialized")
        
        # Test query
        query_text = "diagnostic imaging services radiographic x-ray examinations coverage"
        
        print(f"Testing query: {query_text}")
        chunks = await rag_tool.retrieve_chunks_from_text(query_text)
        
        print(f"✅ RAG tool returned {len(chunks)} chunks")
        
        if chunks:
            print("   Top chunks:")
            for i, chunk in enumerate(chunks[:3]):
                print(f"     {i+1}. Similarity: {chunk.similarity:.6f}")
                print(f"        Content: {chunk.content[:80]}...")
        else:
            print("   No chunks returned (this might indicate an issue)")
        
        return len(chunks) > 0
        
    except Exception as e:
        print(f"❌ RAG tool integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("🚨 ISOLATED RAG SYSTEM TEST")
    print("=" * 60)
    
    # Test 1: Database connection
    database_url, sample_chunks = await test_database_connection()
    if not database_url:
        print("\n❌ Cannot proceed without database connection")
        return False
    
    # Test 2: Embedding generation
    query_embedding = await test_embedding_generation()
    if not query_embedding:
        print("\n❌ Cannot proceed without query embedding")
        return False
    
    # Test 3: Similarity calculation
    similarities = await test_similarity_calculation(query_embedding, database_url)
    if similarities is None:
        print("\n❌ Similarity calculation failed")
        return False
    
    # Test 4: RAG tool integration
    rag_success = await test_rag_tool_integration()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Database Connection: {'✅ SUCCESS' if database_url else '❌ FAILED'}")
    print(f"Embedding Generation: {'✅ SUCCESS' if query_embedding else '❌ FAILED'}")
    print(f"Similarity Calculation: {'✅ SUCCESS' if similarities else '❌ FAILED'}")
    print(f"RAG Tool Integration: {'✅ SUCCESS' if rag_success else '❌ FAILED'}")
    
    if similarities:
        above_threshold = sum(1 for s in similarities if s > 0.3)
        print(f"Chunks Above Threshold: {above_threshold}/{len(similarities)}")
    
    overall_success = all([database_url, query_embedding, similarities is not None, rag_success])
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED - RAG system is working correctly!")
        print("   The updated system should work in production.")
    else:
        print("\n❌ SOME TESTS FAILED - Issues need to be resolved before deployment.")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
