#!/usr/bin/env python3
"""
Local RAG Production Test

This script tests the RAG system locally with the exact same environment
as production to catch issues before deployment.
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

async def test_production_environment():
    """Test with production environment variables."""
    print("🔍 Testing RAG System with Production Environment")
    print("=" * 60)
    
    # Set production environment variables exactly as they are in Render
    os.environ["DATABASE_URL"] = "postgresql://postgres.znvwzkdblknkkztqyfnu:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "sk-test-key-for-testing")
    os.environ["DATABASE_SCHEMA"] = "upload_pipeline"
    os.environ["ENVIRONMENT"] = "production"
    os.environ["NODE_ENV"] = "production"
    
    print("✅ Environment variables set")
    
    try:
        # Test 1: Direct OpenAI API call (reproduce the exact error)
        print("\n🔍 Test 1: Direct OpenAI API Call")
        print("-" * 40)
        
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            max_retries=5,
            timeout=60.0
        )
        
        # This should reproduce the Pydantic error
        try:
            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input="test query for diagnostic imaging",
                encoding_format="float"
            )
            print("✅ Direct OpenAI API call succeeded")
            print(f"   Embedding dimensions: {len(response.data[0].embedding)}")
        except Exception as e:
            print(f"❌ Direct OpenAI API call failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            return False
        
        # Test 2: RAG Tool initialization
        print("\n🔍 Test 2: RAG Tool Initialization")
        print("-" * 40)
        
        from agents.tooling.rag.core import RAGTool, RetrievalConfig
        
        user_id = "0905435f-50e2-428a-9a59-0c92f27f5097"
        config = RetrievalConfig(
            similarity_threshold=0.3,
            max_chunks=5,
            token_budget=2000
        )
        
        rag_tool = RAGTool(user_id=user_id, config=config)
        print("✅ RAG tool initialized successfully")
        
        # Test 3: RAG Tool query (this should fail with Pydantic error)
        print("\n🔍 Test 3: RAG Tool Query")
        print("-" * 40)
        
        query_text = "diagnostic imaging services radiographic x-ray examinations coverage"
        
        try:
            chunks = await rag_tool.retrieve_chunks_from_text(query_text)
            print(f"✅ RAG tool query succeeded: {len(chunks)} chunks")
            
            if chunks:
                print("   Top chunks:")
                for i, chunk in enumerate(chunks[:3]):
                    print(f"     {i+1}. Similarity: {chunk.similarity:.6f}")
                    print(f"        Content: {chunk.content[:60]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ RAG tool query failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_pydantic_versions():
    """Test Pydantic version compatibility."""
    print("\n🔍 Testing Pydantic Version Compatibility")
    print("-" * 40)
    
    try:
        import pydantic
        print(f"✅ Pydantic version: {pydantic.VERSION}")
        
        import openai
        print(f"✅ OpenAI version: {openai.__version__}")
        
        # Test if we can create a simple Pydantic model
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            name: str
            value: float
        
        test_instance = TestModel(name="test", value=1.0)
        print("✅ Pydantic model creation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Pydantic version test failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🚨 LOCAL RAG PRODUCTION TEST")
    print("=" * 60)
    
    # Test Pydantic compatibility first
    pydantic_ok = await test_pydantic_versions()
    
    # Test production environment
    production_ok = await test_production_environment()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Pydantic Compatibility: {'✅ PASS' if pydantic_ok else '❌ FAIL'}")
    print(f"Production Environment: {'✅ PASS' if production_ok else '❌ FAIL'}")
    
    if pydantic_ok and production_ok:
        print("\n🎉 ALL TESTS PASSED!")
        print("   The RAG system should work in production.")
    else:
        print("\n❌ TESTS FAILED!")
        print("   Issues need to be fixed before deployment.")
    
    return pydantic_ok and production_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
