#!/usr/bin/env python3
"""
Debug similarity search issues in RAG system.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

class SimilaritySearchDebugger:
    def __init__(self):
        self.user_id = "936551b6-b7a4-4d3d-9fe0-a491794fd66b"
        
        # Load environment variables explicitly
        try:
            from dotenv import load_dotenv
            load_dotenv('.env.production')
            print("✅ Loaded .env.production")
        except Exception as e:
            print(f"⚠️  Could not load .env.production: {e}")
        
    async def run_debug(self):
        """Debug similarity search issues."""
        print("🔍 Similarity Search Debugging")
        print("=" * 60)
        
        # Set environment variables
        os.environ["DATABASE_URL"] = os.getenv('DATABASE_URL', '')
        os.environ["DATABASE_SCHEMA"] = "upload_pipeline"
        os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY', '')
        
        try:
            # Step 1: Check database content
            print("\n1️⃣ Checking database content...")
            await self.check_database_content()
            
            # Step 2: Test similarity search with different thresholds
            print("\n2️⃣ Testing similarity search with different thresholds...")
            await self.test_similarity_thresholds()
            
            # Step 3: Test with different user IDs
            print("\n3️⃣ Testing with different user IDs...")
            await self.test_different_user_ids()
            
            # Step 4: Test raw SQL query
            print("\n4️⃣ Testing raw SQL query...")
            await self.test_raw_sql_query()
            
            # Step 5: Analyze embedding similarities
            print("\n5️⃣ Analyzing embedding similarities...")
            await self.analyze_embedding_similarities()
            
            print("\n✅ Similarity search debugging completed!")
            
        except Exception as e:
            print(f"\n❌ Debugging failed: {str(e)}")
            return False
        
        return True
    
    async def check_database_content(self):
        """Check what's actually in the database."""
        print("🔍 Checking database content...")
        
        import asyncpg
        
        database_url = os.getenv('DATABASE_URL')
        conn = await asyncpg.connect(database_url)
        
        try:
            # Check total chunks
            total_chunks = await conn.fetchval("SELECT COUNT(*) FROM upload_pipeline.document_chunks")
            print(f"   📊 Total chunks in database: {total_chunks}")
            
            # Check chunks for our user
            user_chunks = await conn.fetchval(
                "SELECT COUNT(*) FROM upload_pipeline.document_chunks dc "
                "JOIN upload_pipeline.documents d ON dc.document_id = d.document_id "
                "WHERE d.user_id = $1",
                self.user_id
            )
            print(f"   📊 Chunks for user {self.user_id}: {user_chunks}")
            
            # Check all users
            all_users = await conn.fetch(
                "SELECT d.user_id, COUNT(*) as chunk_count "
                "FROM upload_pipeline.document_chunks dc "
                "JOIN upload_pipeline.documents d ON dc.document_id = d.document_id "
                "GROUP BY d.user_id "
                "ORDER BY chunk_count DESC"
            )
            print(f"   📊 Chunks by user:")
            for user in all_users:
                print(f"     User {user['user_id']}: {user['chunk_count']} chunks")
            
            # Check sample chunk content
            sample_chunks = await conn.fetch(
                "SELECT dc.text, dc.embedding IS NOT NULL as has_embedding, "
                "d.user_id, d.filename "
                "FROM upload_pipeline.document_chunks dc "
                "JOIN upload_pipeline.documents d ON dc.document_id = d.document_id "
                "LIMIT 5"
            )
            print(f"   📊 Sample chunks:")
            for i, chunk in enumerate(sample_chunks, 1):
                print(f"     {i}. User: {chunk['user_id']}, File: {chunk['filename']}")
                print(f"        Content: {chunk['text'][:100]}...")
                print(f"        Has embedding: {chunk['has_embedding']}")
            
        finally:
            await conn.close()
    
    async def test_similarity_thresholds(self):
        """Test similarity search with different thresholds."""
        print("🔍 Testing similarity search with different thresholds...")
        
        from agents.tooling.rag.core import RAGTool, RetrievalConfig
        
        test_query = "What is my deductible?"
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        
        for threshold in thresholds:
            try:
                config = RetrievalConfig(
                    max_chunks=10,
                    similarity_threshold=threshold
                )
                rag_tool = RAGTool(self.user_id, config)
                
                chunks = await rag_tool.retrieve_chunks_from_text(test_query)
                print(f"   Threshold {threshold}: {len(chunks)} chunks")
                
                if chunks:
                    print(f"     Best similarity: {chunks[0].similarity:.4f}")
                    print(f"     Content: {chunks[0].content[:80]}...")
                    break  # Found chunks, no need to test higher thresholds
                    
            except Exception as e:
                print(f"   Threshold {threshold}: Error - {str(e)}")
    
    async def test_different_user_ids(self):
        """Test with different user IDs to see if it's a user-specific issue."""
        print("🔍 Testing with different user IDs...")
        
        from agents.tooling.rag.core import RAGTool, RetrievalConfig
        
        # Get all user IDs from database
        import asyncpg
        database_url = os.getenv('DATABASE_URL')
        conn = await asyncpg.connect(database_url)
        
        try:
            user_ids = await conn.fetch(
                "SELECT DISTINCT d.user_id "
                "FROM upload_pipeline.document_chunks dc "
                "JOIN upload_pipeline.documents d ON dc.document_id = d.document_id "
                "LIMIT 5"
            )
            
            test_query = "What is my deductible?"
            config = RetrievalConfig(max_chunks=5, similarity_threshold=0.1)
            
            for user_row in user_ids:
                user_id = user_row['user_id']
                try:
                    rag_tool = RAGTool(user_id, config)
                    chunks = await rag_tool.retrieve_chunks_from_text(test_query)
                    print(f"   User {user_id}: {len(chunks)} chunks")
                    
                    if chunks:
                        print(f"     Best similarity: {chunks[0].similarity:.4f}")
                        print(f"     Content: {chunks[0].content[:80]}...")
                        
                except Exception as e:
                    print(f"   User {user_id}: Error - {str(e)}")
                    
        finally:
            await conn.close()
    
    async def test_raw_sql_query(self):
        """Test the raw SQL query to see what's happening."""
        print("🔍 Testing raw SQL query...")
        
        import asyncpg
        from agents.tooling.rag.core import RAGTool, RetrievalConfig
        
        # Generate embedding for test query
        config = RetrievalConfig()
        rag_tool = RAGTool(self.user_id, config)
        test_query = "What is my deductible?"
        
        try:
            embedding = await rag_tool._generate_embedding(test_query)
            print(f"   Generated embedding: {len(embedding)} dimensions")
            print(f"   Sample values: {embedding[:5]}")
            
            # Test raw SQL query
            database_url = os.getenv('DATABASE_URL')
            conn = await asyncpg.connect(database_url)
            
            try:
                # Convert embedding to PostgreSQL vector format
                vector_string = '[' + ','.join(str(x) for x in embedding) + ']'
                
                # Test the exact query from RAGTool
                sql = f"""
                    SELECT dc.chunk_id, dc.document_id, dc.chunk_ord as chunk_index, dc.text as content,
                           NULL as section_path, NULL as section_title,
                           NULL as page_start, NULL as page_end,
                           NULL as tokens,
                           1 - (dc.embedding <=> $1::vector(1536)) as similarity
                    FROM upload_pipeline.document_chunks dc
                    JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
                    WHERE d.user_id = $2
                      AND dc.embedding IS NOT NULL
                      AND 1 - (dc.embedding <=> $1::vector(1536)) > $3
                    ORDER BY dc.embedding <=> $1::vector(1536)
                    LIMIT $4
                """
                
                print(f"   Testing SQL query with user_id: {self.user_id}")
                print(f"   Similarity threshold: 0.1")
                
                rows = await conn.fetch(sql, vector_string, self.user_id, 0.1, 10)
                print(f"   Raw SQL result: {len(rows)} rows")
                
                if rows:
                    for i, row in enumerate(rows[:3]):
                        print(f"     Row {i+1}: similarity={row['similarity']:.4f}, content={row['content'][:80]}...")
                else:
                    print("   No rows returned from raw SQL query")
                    
                    # Let's check if there are any chunks for this user at all
                    check_sql = """
                        SELECT COUNT(*) as total_chunks
                        FROM upload_pipeline.document_chunks dc
                        JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
                        WHERE d.user_id = $1
                    """
                    total = await conn.fetchval(check_sql, self.user_id)
                    print(f"   Total chunks for user: {total}")
                    
                    # Check if embeddings exist
                    embedding_check = """
                        SELECT COUNT(*) as chunks_with_embeddings
                        FROM upload_pipeline.document_chunks dc
                        JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
                        WHERE d.user_id = $1 AND dc.embedding IS NOT NULL
                    """
                    with_embeddings = await conn.fetchval(embedding_check, self.user_id)
                    print(f"   Chunks with embeddings: {with_embeddings}")
                    
            finally:
                await conn.close()
                
        except Exception as e:
            print(f"   ❌ Raw SQL test failed: {str(e)}")
    
    async def analyze_embedding_similarities(self):
        """Analyze the actual similarities between query and stored embeddings."""
        print("🔍 Analyzing embedding similarities...")
        
        import asyncpg
        from agents.tooling.rag.core import RAGTool, RetrievalConfig
        
        # Generate embedding for test query
        config = RetrievalConfig()
        rag_tool = RAGTool(self.user_id, config)
        test_query = "What is my deductible?"
        
        try:
            query_embedding = await rag_tool._generate_embedding(test_query)
            
            database_url = os.getenv('DATABASE_URL')
            conn = await asyncpg.connect(database_url)
            
            try:
                # Get all similarities for this user
                vector_string = '[' + ','.join(str(x) for x in query_embedding) + ']'
                
                sql = """
                    SELECT dc.chunk_id, dc.text, 
                           1 - (dc.embedding <=> $1::vector(1536)) as similarity
                    FROM upload_pipeline.document_chunks dc
                    JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
                    WHERE d.user_id = $2
                      AND dc.embedding IS NOT NULL
                    ORDER BY dc.embedding <=> $1::vector(1536)
                    LIMIT 20
                """
                
                rows = await conn.fetch(sql, vector_string, self.user_id)
                print(f"   Top 20 similarities for user {self.user_id}:")
                
                if rows:
                    for i, row in enumerate(rows, 1):
                        print(f"     {i:2d}. similarity={row['similarity']:.4f}, content={row['text'][:60]}...")
                    
                    # Find the best similarity
                    best_similarity = rows[0]['similarity'] if rows else 0
                    print(f"\n   Best similarity: {best_similarity:.4f}")
                    
                    if best_similarity < 0.1:
                        print("   ⚠️  Very low similarities - embeddings may not be meaningful")
                    elif best_similarity < 0.3:
                        print("   ⚠️  Low similarities - may need lower threshold")
                    else:
                        print("   ✅ Good similarities found")
                else:
                    print("   ❌ No chunks found for this user")
                    
            finally:
                await conn.close()
                
        except Exception as e:
            print(f"   ❌ Similarity analysis failed: {str(e)}")

async def main():
    """Run the similarity search debugging."""
    debugger = SimilaritySearchDebugger()
    success = await debugger.run_debug()
    
    if success:
        print("\n🎉 Similarity search debugging completed!")
    else:
        print("\n❌ Similarity search debugging found issues!")

if __name__ == "__main__":
    asyncio.run(main())
