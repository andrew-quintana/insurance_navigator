#!/usr/bin/env python3
"""
Simple RAG Test

Test the RAG tool with the correct environment variables.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_rag_tool():
    """Test the RAG tool with production environment."""
    print("🔍 Testing RAG Tool with Production Environment")
    print("-" * 50)
    
    # Set production environment variables
    os.environ["DATABASE_URL"] = "postgresql://postgres.znvwzkdblknkkztqyfnu:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "sk-test-key-for-testing")
    os.environ["DATABASE_SCHEMA"] = "upload_pipeline"
    
    try:
        from agents.tooling.rag.core import RAGTool, RetrievalConfig
        
        # Create RAG tool instance
        user_id = "0905435f-50e2-428a-9a59-0c92f27f5097"
        config = RetrievalConfig(
            similarity_threshold=0.3,
            max_chunks=5,
            token_budget=2000
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
            for i, chunk in enumerate(chunks):
                print(f"     {i+1}. Similarity: {chunk.similarity:.6f}")
                print(f"        Content: {chunk.content[:80]}...")
            return True
        else:
            print("   No chunks returned")
            return False
        
    except Exception as e:
        print(f"❌ RAG tool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("🚨 SIMPLE RAG TOOL TEST")
    print("=" * 60)
    
    success = await test_rag_tool()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    if success:
        print("🎉 RAG TOOL TEST PASSED!")
        print("   The updated RAG system is working correctly.")
        print("   Ready for deployment!")
    else:
        print("❌ RAG TOOL TEST FAILED")
        print("   Issues need to be resolved before deployment.")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
