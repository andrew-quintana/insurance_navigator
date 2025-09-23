#!/usr/bin/env python3
"""
Debug RAG Embeddings Issue

This script investigates the RAG similarity issue by testing
embedding generation and similarity calculation.
"""

import asyncio
import os
import sys
from pathlib import Path
import asyncpg
import numpy as np
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_embedding_generation():
    """Test embedding generation for both query and document chunks."""
    print("🔍 Testing Embedding Generation")
    print("-" * 50)
    
    # Test query embedding generation
    query_text = "Expert Query Reframe:\n\nThe member is inquiring about coverage for diagnostic imaging services, specifically radiographic (x-ray) examinations. This would fall under the plan's physician services benefit, which typically requires the member to obtain a referral or prior authorization from their primary care provider before receiving the service. The member may be subject to applicable cost-sharing, such as a copayment or coinsurance, depending on the terms of their health insurance plan. Coverage would also be contingent on receiving services from an in-network radiology provider."
    
    try:
        from openai import AsyncOpenAI
        
        # Get OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY not found")
            return False
        
        print(f"✅ OpenAI API key found: {api_key[:10]}...")
        
        # Initialize OpenAI client
        client = AsyncOpenAI(
            api_key=api_key,
            max_retries=3,
            timeout=30.0
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
        
        return query_embedding
        
    except Exception as e:
        print(f"❌ Query embedding generation failed: {e}")
        return None

async def test_database_embeddings():
    """Test database embeddings and similarity calculation."""
    print("\n🔍 Testing Database Embeddings")
    print("-" * 50)
    
    # Database connection
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found")
        return None
    
    try:
        conn = await asyncpg.connect(database_url)
        print("✅ Database connected")
        
        # Get sample document embeddings
        user_id = "0905435f-50e2-428a-9a59-0c92f27f5097"
        
        sql = """
            SELECT dc.chunk_id, dc.text as content, dc.embedding
            FROM public.document_chunks dc
            JOIN public.documents d ON dc.document_id = d.document_id
            WHERE d.user_id = $1
              AND dc.embedding IS NOT NULL
            LIMIT 5
        """
        
        rows = await conn.fetch(sql, user_id)
        print(f"✅ Found {len(rows)} document chunks")
        
        if not rows:
            print("❌ No document chunks found")
            return None
        
        # Analyze document embeddings
        doc_embeddings = []
        for i, row in enumerate(rows):
            embedding = row['embedding']
            if embedding:
                # Convert from string representation to list
                if isinstance(embedding, str):
                    embedding = eval(embedding)  # Convert string to list
                
                doc_embeddings.append(embedding)
                print(f"   Chunk {i+1}: {len(embedding)} dimensions, first 5: {embedding[:5]}")
        
        await conn.close()
        return doc_embeddings
        
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        return None

async def test_similarity_calculation(query_embedding: List[float], doc_embeddings: List[List[float]]):
    """Test similarity calculation between query and document embeddings."""
    print("\n🔍 Testing Similarity Calculation")
    print("-" * 50)
    
    if not query_embedding or not doc_embeddings:
        print("❌ Missing embeddings for similarity test")
        return
    
    # Convert to numpy arrays for easier calculation
    query_vec = np.array(query_embedding)
    
    similarities = []
    for i, doc_embedding in enumerate(doc_embeddings):
        doc_vec = np.array(doc_embedding)
        
        # Calculate cosine similarity
        dot_product = np.dot(query_vec, doc_vec)
        norm_query = np.linalg.norm(query_vec)
        norm_doc = np.linalg.norm(doc_vec)
        
        if norm_query == 0 or norm_doc == 0:
            similarity = 0.0
        else:
            similarity = dot_product / (norm_query * norm_doc)
        
        similarities.append(similarity)
        print(f"   Chunk {i+1}: similarity = {similarity:.6f}")
    
    print(f"\n📊 Similarity Statistics:")
    print(f"   Average: {np.mean(similarities):.6f}")
    print(f"   Min: {np.min(similarities):.6f}")
    print(f"   Max: {np.max(similarities):.6f}")
    print(f"   Above 0.3 threshold: {sum(1 for s in similarities if s > 0.3)}/{len(similarities)}")

async def test_database_similarity_query(query_embedding: List[float]):
    """Test the actual database similarity query."""
    print("\n🔍 Testing Database Similarity Query")
    print("-" * 50)
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found")
        return
    
    try:
        conn = await asyncpg.connect(database_url)
        
        user_id = "0905435f-50e2-428a-9a59-0c92f27f5097"
        vector_string = '[' + ','.join(str(x) for x in query_embedding) + ']'
        
        # Test the exact query from the RAG tool
        sql = """
            SELECT dc.chunk_id, dc.text as content,
                   1 - (dc.embedding <=> $1::vector(1536)) as similarity
            FROM public.document_chunks dc
            JOIN public.documents d ON dc.document_id = d.document_id
            WHERE d.user_id = $2
              AND dc.embedding IS NOT NULL
            ORDER BY dc.embedding <=> $1::vector(1536)
            LIMIT 10
        """
        
        rows = await conn.fetch(sql, vector_string, user_id)
        print(f"✅ Database similarity query returned {len(rows)} results")
        
        for i, row in enumerate(rows):
            print(f"   Result {i+1}: similarity = {row['similarity']:.6f}")
            print(f"      Content: {row['content'][:100]}...")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Database similarity query failed: {e}")

async def main():
    """Main debugging function."""
    print("🚨 RAG EMBEDDINGS DEBUG")
    print("=" * 60)
    
    # Test query embedding generation
    query_embedding = await test_embedding_generation()
    
    # Test database embeddings
    doc_embeddings = await test_database_embeddings()
    
    # Test similarity calculation
    if query_embedding and doc_embeddings:
        await test_similarity_calculation(query_embedding, doc_embeddings)
    
    # Test database similarity query
    if query_embedding:
        await test_database_similarity_query(query_embedding)
    
    print("\n" + "=" * 60)
    print("📊 DEBUG SUMMARY")
    print("=" * 60)
    
    if query_embedding and doc_embeddings:
        print("✅ Both query and document embeddings generated successfully")
        print("🔍 Check similarity calculation and database query results above")
    else:
        print("❌ Embedding generation failed - check API keys and database connection")

if __name__ == "__main__":
    asyncio.run(main())
