#!/usr/bin/env python3
"""
Quick test to check what user_ids have documents in the database
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

async def check_user_documents():
    """Check what user_ids have documents in the database"""
    load_dotenv('.env.production')
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return
    
    print(f"🔍 Connecting to database...")
    print(f"📊 Database URL: {database_url[:50]}...")
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Check documents table
        print("\n📄 Documents in database:")
        documents = await conn.fetch("""
            SELECT user_id, document_id, filename, created_at 
            FROM upload_pipeline.documents 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        if documents:
            for doc in documents:
                print(f"  📄 User: {doc['user_id']} | File: {doc['filename']} | Created: {doc['created_at']}")
        else:
            print("  ❌ No documents found")
        
        # Check chunks table
        print("\n🧩 Chunks in database:")
        chunks = await conn.fetch("""
            SELECT d.user_id, COUNT(dc.chunk_id) as chunk_count
            FROM upload_pipeline.document_chunks dc
            JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
            GROUP BY d.user_id
            ORDER BY chunk_count DESC
            LIMIT 10
        """)
        
        if chunks:
            for chunk in chunks:
                print(f"  🧩 User: {chunk['user_id']} | Chunks: {chunk['chunk_count']}")
        else:
            print("  ❌ No chunks found")
        
        # Test RAG query with a known user_id
        if chunks:
            test_user_id = chunks[0]['user_id']
            print(f"\n🔍 Testing RAG query with user_id: {test_user_id}")
            
            # Test similarity search
            test_embedding = [0.1] * 1536  # Dummy embedding
            vector_string = '[' + ','.join(str(x) for x in test_embedding) + ']'
            
            rag_results = await conn.fetch("""
                SELECT dc.chunk_id, dc.document_id, dc.text as content,
                       1 - (dc.embedding <=> $1::vector(1536)) as similarity
                FROM upload_pipeline.document_chunks dc
                JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
                WHERE d.user_id = $2
                  AND dc.embedding IS NOT NULL
                  AND 1 - (dc.embedding <=> $1::vector(1536)) > 0.1
                ORDER BY dc.embedding <=> $1::vector(1536)
                LIMIT 5
            """, vector_string, test_user_id)
            
            if rag_results:
                print(f"  ✅ RAG query successful! Found {len(rag_results)} chunks")
                for i, result in enumerate(rag_results[:3]):
                    print(f"    {i+1}. Similarity: {result['similarity']:.4f} | Content: {result['content'][:100]}...")
            else:
                print("  ❌ RAG query returned no results")
        
        await conn.close()
        print("\n✅ Database check completed")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    asyncio.run(check_user_documents())
