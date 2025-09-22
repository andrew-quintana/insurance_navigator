#!/usr/bin/env python3
"""
Exact Pydantic Error Reproduction Test

This script attempts to reproduce the exact Pydantic error seen in production:
"Fields must not use names with leading underscores; e.g., use 'pydantic_extra__' instead of '__pydantic_extra__'."
"""

import asyncio
import os
import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging to match production
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_pydantic_error_reproduction():
    """Test various scenarios that might trigger the Pydantic error."""
    print("🔍 Testing Pydantic Error Reproduction")
    print("=" * 60)
    
    # Set production environment variables
    os.environ["DATABASE_URL"] = "postgresql://postgres.znvwzkdblknkkztqyfnu:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    os.environ["OPENAI_API_KEY"] = "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"
    os.environ["DATABASE_SCHEMA"] = "upload_pipeline"
    os.environ["ENVIRONMENT"] = "production"
    os.environ["NODE_ENV"] = "production"
    
    print("✅ Environment variables set")
    
    # Test 1: Direct OpenAI client with different configurations
    print("\n🔍 Test 1: OpenAI Client Configurations")
    print("-" * 40)
    
    try:
        from openai import AsyncOpenAI
        
        # Test different client configurations that might trigger the error
        configs = [
            {"api_key": os.environ["OPENAI_API_KEY"], "max_retries": 5, "timeout": 60.0},
            {"api_key": os.environ["OPENAI_API_KEY"], "max_retries": 3, "timeout": 30.0},
            {"api_key": os.environ["OPENAI_API_KEY"]},  # Minimal config
        ]
        
        for i, config in enumerate(configs):
            try:
                print(f"   Testing config {i+1}: {config}")
                client = AsyncOpenAI(**config)
                
                response = await client.embeddings.create(
                    model="text-embedding-3-small",
                    input="test query for diagnostic imaging",
                    encoding_format="float"
                )
                print(f"   ✅ Config {i+1} succeeded: {len(response.data[0].embedding)} dimensions")
                
            except Exception as e:
                print(f"   ❌ Config {i+1} failed: {e}")
                if "pydantic" in str(e).lower() or "underscore" in str(e).lower():
                    print(f"   🎯 FOUND PYDANTIC ERROR: {e}")
                    return True
        
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        return False
    
    # Test 2: RAG Tool with different configurations
    print("\n🔍 Test 2: RAG Tool Configurations")
    print("-" * 40)
    
    try:
        from agents.tooling.rag.core import RAGTool, RetrievalConfig
        
        # Test different RAG configurations
        configs = [
            RetrievalConfig(similarity_threshold=0.3, max_chunks=5, token_budget=2000),
            RetrievalConfig(similarity_threshold=0.1, max_chunks=10, token_budget=4000),
            RetrievalConfig(similarity_threshold=0.5, max_chunks=3, token_budget=1000),
        ]
        
        user_id = "0905435f-50e2-428a-9a59-0c92f27f5097"
        
        for i, config in enumerate(configs):
            try:
                print(f"   Testing RAG config {i+1}: threshold={config.similarity_threshold}, max_chunks={config.max_chunks}")
                rag_tool = RAGTool(user_id=user_id, config=config)
                
                chunks = await rag_tool.retrieve_chunks_from_text("diagnostic imaging services radiographic x-ray examinations coverage")
                print(f"   ✅ RAG config {i+1} succeeded: {len(chunks)} chunks")
                
            except Exception as e:
                print(f"   ❌ RAG config {i+1} failed: {e}")
                if "pydantic" in str(e).lower() or "underscore" in str(e).lower():
                    print(f"   🎯 FOUND PYDANTIC ERROR: {e}")
                    return True
        
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        return False
    
    # Test 3: Multiple concurrent requests (like in production)
    print("\n🔍 Test 3: Concurrent Requests")
    print("-" * 40)
    
    try:
        from agents.tooling.rag.core import RAGTool, RetrievalConfig
        
        user_id = "0905435f-50e2-428a-9a59-0c92f27f5097"
        config = RetrievalConfig(similarity_threshold=0.3, max_chunks=5, token_budget=2000)
        
        # Create multiple concurrent requests
        async def make_request(i):
            try:
                rag_tool = RAGTool(user_id=user_id, config=config)
                chunks = await rag_tool.retrieve_chunks_from_text(f"test query {i} for diagnostic imaging")
                return f"Request {i}: {len(chunks)} chunks"
            except Exception as e:
                return f"Request {i}: ERROR - {e}"
        
        # Run 5 concurrent requests
        tasks = [make_request(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            print(f"   {result}")
            if isinstance(result, Exception) and ("pydantic" in str(result).lower() or "underscore" in str(result).lower()):
                print(f"   🎯 FOUND PYDANTIC ERROR: {result}")
                return True
        
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        return False
    
    # Test 4: Different import patterns
    print("\n🔍 Test 4: Different Import Patterns")
    print("-" * 40)
    
    try:
        # Test importing OpenAI in different ways
        import openai
        from openai import AsyncOpenAI
        
        # Test creating client with different patterns
        patterns = [
            lambda: openai.AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"]),
            lambda: AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"]),
            lambda: openai.AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"], max_retries=5, timeout=60.0),
        ]
        
        for i, pattern in enumerate(patterns):
            try:
                print(f"   Testing import pattern {i+1}")
                client = pattern()
                
                response = await client.embeddings.create(
                    model="text-embedding-3-small",
                    input="test query for diagnostic imaging",
                    encoding_format="float"
                )
                print(f"   ✅ Import pattern {i+1} succeeded: {len(response.data[0].embedding)} dimensions")
                
            except Exception as e:
                print(f"   ❌ Import pattern {i+1} failed: {e}")
                if "pydantic" in str(e).lower() or "underscore" in str(e).lower():
                    print(f"   🎯 FOUND PYDANTIC ERROR: {e}")
                    return True
        
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        return False
    
    print("\n✅ No Pydantic errors reproduced locally")
    return False

async def main():
    """Main test function."""
    print("🚨 EXACT PYDANTIC ERROR REPRODUCTION TEST")
    print("=" * 60)
    
    error_found = await test_pydantic_error_reproduction()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    if error_found:
        print("🎯 PYDANTIC ERROR REPRODUCED!")
        print("   The exact production error was found locally.")
        print("   This will help identify the root cause.")
    else:
        print("❌ PYDANTIC ERROR NOT REPRODUCED")
        print("   The error might be environment-specific or context-dependent.")
        print("   Further investigation needed.")
    
    return error_found

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
