#!/usr/bin/env python3
"""
Debug RAG system issues systematically.
This script will identify and help resolve the problems preventing RAG from working.
"""

import asyncio
import sys
import os
import json
import asyncpg
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

class RAGSystemDebugger:
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
        
    async def run_debug(self):
        """Run comprehensive RAG system debugging."""
        print("🔍 RAG System Debugging")
        print("=" * 60)
        
        try:
            # Step 1: Check environment variables
            print("\n1️⃣ Checking environment variables...")
            await self.check_environment_variables()
            
            # Step 2: Test database connection
            print("\n2️⃣ Testing database connection...")
            await self.test_database_connection()
            
            # Step 3: Check database schema and tables
            print("\n3️⃣ Checking database schema and tables...")
            await self.check_database_schema()
            
            # Step 4: Test OpenAI API connection
            print("\n4️⃣ Testing OpenAI API connection...")
            await self.test_openai_connection()
            
            # Step 5: Test RAG system components
            print("\n5️⃣ Testing RAG system components...")
            await self.test_rag_components()
            
            # Step 6: Apply fixes
            print("\n6️⃣ Applying fixes...")
            await self.apply_fixes()
            
            # Step 7: Test RAG system after fixes
            print("\n7️⃣ Testing RAG system after fixes...")
            await self.test_rag_after_fixes()
            
            print("\n✅ Debugging completed!")
            
        except Exception as e:
            print(f"\n❌ Debugging failed: {str(e)}")
            return False
        
        return True
    
    async def check_environment_variables(self):
        """Check all required environment variables."""
        print("🔍 Checking environment variables...")
        
        # Load from .env.production
        try:
            from dotenv import load_dotenv
            load_dotenv('.env.production')
            print("✅ Loaded .env.production")
        except Exception as e:
            print(f"⚠️  Could not load .env.production: {e}")
        
        required_vars = {
            'DATABASE_URL': 'PostgreSQL connection string',
            'OPENAI_API_KEY': 'OpenAI API key',
            'SUPABASE_URL': 'Supabase project URL',
            'SUPABASE_ANON_KEY': 'Supabase anonymous key',
            'SUPABASE_SERVICE_ROLE_KEY': 'Supabase service role key'
        }
        
        missing_vars = []
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                if 'KEY' in var or 'URL' in var:
                    masked_value = value[:10] + "..." if len(value) > 10 else "***"
                    print(f"   ✅ {var}: {masked_value}")
                else:
                    print(f"   ✅ {var}: {value}")
            else:
                print(f"   ❌ {var}: NOT SET")
                missing_vars.append(var)
        
        if missing_vars:
            self.issues_found.append(f"Missing environment variables: {missing_vars}")
            print(f"❌ Missing {len(missing_vars)} environment variables")
        else:
            print("✅ All required environment variables are set")
    
    async def test_database_connection(self):
        """Test database connection with different approaches."""
        print("🔍 Testing database connection...")
        
        # Test 1: Direct connection with DATABASE_URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not set")
            self.issues_found.append("DATABASE_URL not set")
            return False
        
        print(f"   Testing connection to: {database_url[:50]}...")
        
        try:
            # Test connection
            conn = await asyncpg.connect(database_url)
            print("   ✅ Database connection successful")
            
            # Test basic query
            result = await conn.fetchval("SELECT 1")
            print(f"   ✅ Basic query successful: {result}")
            
            await conn.close()
            return True
            
        except Exception as e:
            print(f"   ❌ Database connection failed: {str(e)}")
            self.issues_found.append(f"Database connection failed: {str(e)}")
            
            # Try alternative connection methods
            print("   🔄 Trying alternative connection methods...")
            
            # Test 2: Parse URL and connect with individual parameters
            try:
                import urllib.parse
                parsed = urllib.parse.urlparse(database_url)
                
                conn = await asyncpg.connect(
                    host=parsed.hostname,
                    port=parsed.port,
                    user=parsed.username,
                    password=parsed.password,
                    database=parsed.path[1:],  # Remove leading slash
                    ssl='require'
                )
                print("   ✅ Alternative connection successful")
                await conn.close()
                return True
                
            except Exception as e2:
                print(f"   ❌ Alternative connection also failed: {str(e2)}")
                self.issues_found.append(f"Alternative connection failed: {str(e2)}")
                return False
    
    async def check_database_schema(self):
        """Check database schema and required tables."""
        print("🔍 Checking database schema...")
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ Cannot check schema - DATABASE_URL not set")
            return False
        
        try:
            conn = await asyncpg.connect(database_url)
            
            # Check if upload_pipeline schema exists
            schema_query = """
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = 'upload_pipeline'
            """
            schema_exists = await conn.fetchval(schema_query)
            
            if schema_exists:
                print("   ✅ upload_pipeline schema exists")
                
                # Check required tables
                tables_query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'upload_pipeline'
                    ORDER BY table_name
                """
                tables = await conn.fetch(tables_query)
                table_names = [row['table_name'] for row in tables]
                
                print(f"   📋 Tables in upload_pipeline schema: {table_names}")
                
                required_tables = ['documents', 'document_chunks', 'upload_jobs']
                missing_tables = [t for t in required_tables if t not in table_names]
                
                if missing_tables:
                    print(f"   ❌ Missing tables: {missing_tables}")
                    self.issues_found.append(f"Missing tables: {missing_tables}")
                else:
                    print("   ✅ All required tables exist")
                
                # Check document_chunks table structure
                if 'document_chunks' in table_names:
                    chunks_query = """
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_schema = 'upload_pipeline' 
                        AND table_name = 'document_chunks'
                        ORDER BY ordinal_position
                    """
                    columns = await conn.fetch(chunks_query)
                    print(f"   📋 document_chunks columns: {[(c['column_name'], c['data_type']) for c in columns]}")
                    
                    # Check if embedding column exists and has data
                    embedding_query = """
                        SELECT COUNT(*) as total_chunks,
                               COUNT(embedding) as chunks_with_embeddings
                        FROM upload_pipeline.document_chunks
                    """
                    embedding_stats = await conn.fetchrow(embedding_query)
                    print(f"   📊 Chunk statistics: {dict(embedding_stats)}")
                
            else:
                print("   ❌ upload_pipeline schema does not exist")
                self.issues_found.append("upload_pipeline schema does not exist")
            
            await conn.close()
            return True
            
        except Exception as e:
            print(f"   ❌ Schema check failed: {str(e)}")
            self.issues_found.append(f"Schema check failed: {str(e)}")
            return False
    
    async def test_openai_connection(self):
        """Test OpenAI API connection."""
        print("🔍 Testing OpenAI API connection...")
        
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            print("   ❌ OPENAI_API_KEY not set")
            self.issues_found.append("OPENAI_API_KEY not set")
            return False
        
        try:
            import openai
            client = openai.AsyncOpenAI(
                api_key=openai_key,
                max_retries=3,
                timeout=30.0
            )
            
            # Test with a simple embedding
            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input="test",
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            print(f"   ✅ OpenAI API connection successful")
            print(f"   📊 Embedding dimension: {len(embedding)}")
            print(f"   📊 Sample values: {embedding[:5]}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ OpenAI API connection failed: {str(e)}")
            self.issues_found.append(f"OpenAI API connection failed: {str(e)}")
            return False
    
    async def test_rag_components(self):
        """Test RAG system components individually."""
        print("🔍 Testing RAG system components...")
        
        # Set environment variables
        os.environ["DATABASE_URL"] = os.getenv('DATABASE_URL', '')
        os.environ["DATABASE_SCHEMA"] = "upload_pipeline"
        os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY', '')
        
        try:
            from agents.tooling.rag.core import RAGTool, RetrievalConfig
            
            # Test RAGTool initialization
            print("   Testing RAGTool initialization...")
            config = RetrievalConfig(max_chunks=5, similarity_threshold=0.4)
            user_id = "936551b6-b7a4-4d3d-9fe0-a491794fd66b"  # Test user ID
            
            rag_tool = RAGTool(user_id, config)
            print("   ✅ RAGTool initialized successfully")
            
            # Test embedding generation
            print("   Testing embedding generation...")
            try:
                embedding = await rag_tool._generate_embedding("test query")
                print(f"   ✅ Embedding generated: {len(embedding)} dimensions")
                print(f"   📊 Sample values: {embedding[:5]}")
            except Exception as e:
                print(f"   ❌ Embedding generation failed: {str(e)}")
                self.issues_found.append(f"Embedding generation failed: {str(e)}")
            
            # Test database connection from RAGTool
            print("   Testing RAGTool database connection...")
            try:
                conn = await rag_tool._get_db_conn()
                print("   ✅ RAGTool database connection successful")
                await conn.close()
            except Exception as e:
                print(f"   ❌ RAGTool database connection failed: {str(e)}")
                self.issues_found.append(f"RAGTool database connection failed: {str(e)}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ RAG component test failed: {str(e)}")
            self.issues_found.append(f"RAG component test failed: {str(e)}")
            return False
    
    async def apply_fixes(self):
        """Apply fixes for identified issues."""
        print("🔧 Applying fixes...")
        
        if not self.issues_found:
            print("   ✅ No issues found to fix")
            return
        
        print(f"   📋 Issues to fix: {len(self.issues_found)}")
        for i, issue in enumerate(self.issues_found, 1):
            print(f"   {i}. {issue}")
        
        # Fix 1: Ensure environment variables are properly loaded
        print("\n   🔧 Fix 1: Loading environment variables...")
        try:
            from dotenv import load_dotenv
            load_dotenv('.env.production')
            print("   ✅ Environment variables loaded from .env.production")
            self.fixes_applied.append("Loaded environment variables from .env.production")
        except Exception as e:
            print(f"   ⚠️  Could not load .env.production: {e}")
        
        # Fix 2: Set explicit environment variables
        print("\n   🔧 Fix 2: Setting explicit environment variables...")
        env_vars = {
            'DATABASE_URL': os.getenv('DATABASE_URL'),
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'DATABASE_SCHEMA': 'upload_pipeline'
        }
        
        for key, value in env_vars.items():
            if value:
                os.environ[key] = value
                print(f"   ✅ Set {key}")
            else:
                print(f"   ❌ {key} not available")
        
        self.fixes_applied.append("Set explicit environment variables")
    
    async def test_rag_after_fixes(self):
        """Test RAG system after applying fixes."""
        print("🔍 Testing RAG system after fixes...")
        
        try:
            from agents.tooling.rag.core import RAGTool, RetrievalConfig
            
            # Initialize RAG system
            config = RetrievalConfig(max_chunks=5, similarity_threshold=0.3)
            user_id = "936551b6-b7a4-4d3d-9fe0-a491794fd66b"
            rag_tool = RAGTool(user_id, config)
            
            # Test query
            test_query = "What is my deductible?"
            print(f"   Testing query: {test_query}")
            
            # Test retrieve_chunks_from_text
            chunks = await rag_tool.retrieve_chunks_from_text(test_query)
            print(f"   ✅ Retrieved {len(chunks)} chunks")
            
            if chunks:
                print("   📊 Chunk details:")
                for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                    print(f"     Chunk {i+1}: {chunk.content[:100]}... (similarity: {chunk.similarity:.3f})")
                
                # Check if content looks real
                real_content_indicators = ['deductible', 'coverage', 'policy', 'insurance', 'premium']
                has_real_content = any(
                    any(indicator in chunk.content.lower() for indicator in real_content_indicators)
                    for chunk in chunks
                )
                
                if has_real_content:
                    print("   ✅ Found real insurance content!")
                else:
                    print("   ⚠️  Content may still be mock")
            else:
                print("   ⚠️  No chunks retrieved")
            
            return len(chunks) > 0
            
        except Exception as e:
            print(f"   ❌ RAG test after fixes failed: {str(e)}")
            return False

async def main():
    """Run the RAG system debugging."""
    debugger = RAGSystemDebugger()
    success = await debugger.run_debug()
    
    print("\n" + "=" * 60)
    print("📋 DEBUG SUMMARY")
    print("=" * 60)
    
    if debugger.issues_found:
        print(f"❌ Issues found: {len(debugger.issues_found)}")
        for i, issue in enumerate(debugger.issues_found, 1):
            print(f"   {i}. {issue}")
    else:
        print("✅ No issues found")
    
    if debugger.fixes_applied:
        print(f"\n🔧 Fixes applied: {len(debugger.fixes_applied)}")
        for i, fix in enumerate(debugger.fixes_applied, 1):
            print(f"   {i}. {fix}")
    
    if success:
        print("\n🎉 RAG system debugging completed successfully!")
    else:
        print("\n❌ RAG system debugging found issues that need attention")

if __name__ == "__main__":
    asyncio.run(main())
