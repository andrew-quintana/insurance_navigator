#!/usr/bin/env python3
"""
Quick Validation Script for MVP Async Fix

Validates basic functionality before running full concurrent tests.
This script tests:
1. Single request functionality
2. Basic async operation
3. Environment setup
4. Database connectivity

Run this before the full concurrent test suite.
"""

import os
import asyncio
import sys
import time
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load development environment
load_dotenv('.env.development')

async def validate_basic_functionality():
    """Validate basic RAG functionality"""
    print("🔍 MVP Async Fix - Basic Validation")
    print("=" * 50)
    
    # Check environment variables
    print("📋 Checking environment setup...")
    
    required_vars = [
        'OPENAI_API_KEY',
        'DATABASE_URL',
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"  ✅ {var}: Set")
    
    if missing_vars:
        print(f"  ❌ Missing environment variables: {missing_vars}")
        return False
    
    print("  ✅ All required environment variables are set")
    
    # Test RAG tool creation
    print("\n🔧 Testing RAG tool creation...")
    try:
        from agents.tooling.rag.core import RAGTool, RetrievalConfig
        
        rag_config = RetrievalConfig(
            similarity_threshold=0.3,
            max_chunks=5,
            token_budget=2000
        )
        
        test_user_id = 'f0cfcc46-5fdb-48c4-af13-51c6cf53e408'
        rag_tool = RAGTool(user_id=test_user_id, config=rag_config)
        
        print("  ✅ RAG tool created successfully")
        
    except Exception as e:
        print(f"  ❌ Failed to create RAG tool: {e}")
        return False
    
    # Test single request
    print("\n🧪 Testing single request...")
    try:
        test_query = "What does my insurance cover?"
        print(f"  📝 Query: {test_query}")
        
        start_time = time.time()
        chunks = await rag_tool.retrieve_chunks_from_text(test_query)
        end_time = time.time()
        
        duration = end_time - start_time
        
        print(f"  ⏱️  Duration: {duration:.2f}s")
        print(f"  📊 Chunks returned: {len(chunks)}")
        
        if duration > 10.0:
            print(f"  ⚠️  Warning: Request took {duration:.2f}s (exceeds 10s threshold)")
            return False
        
        if len(chunks) == 0:
            print("  ⚠️  Warning: No chunks returned (may be normal if no documents uploaded)")
        else:
            print(f"  ✅ First chunk preview: {chunks[0].content[:100]}...")
        
        print("  ✅ Single request test passed")
        
    except Exception as e:
        print(f"  ❌ Single request test failed: {e}")
        return False
    
    # Test async operation
    print("\n🔄 Testing async operation...")
    try:
        async def async_test():
            return await rag_tool.retrieve_chunks_from_text("Test async operation")
        
        # Run multiple async operations
        tasks = [async_test() for _ in range(3)]
        results = await asyncio.gather(*tasks)
        
        print(f"  ✅ Async operations completed: {len(results)} tasks")
        
    except Exception as e:
        print(f"  ❌ Async operation test failed: {e}")
        return False
    
    print("\n🎉 Basic validation PASSED!")
    print("   Ready to run full concurrent test suite.")
    return True

async def main():
    """Main validation execution"""
    try:
        success = await validate_basic_functionality()
        
        if success:
            print("\n🚀 Proceeding to run full concurrent test suite...")
            print("   Execute: python tests/test_concurrent_rag_mvp.py")
            sys.exit(0)
        else:
            print("\n❌ Basic validation FAILED!")
            print("   Fix issues before running concurrent tests.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
