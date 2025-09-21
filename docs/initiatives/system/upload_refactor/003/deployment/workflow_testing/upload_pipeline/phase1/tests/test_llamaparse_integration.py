#!/usr/bin/env python3
"""
Test LlamaParse integration to verify API connectivity.
"""

import asyncio
import os
import sys
sys.path.append('/Users/aq_home/1Projects/accessa/insurance_navigator/backend')

from shared.external import LlamaParseClient

async def test_llamaparse():
    """Test LlamaParse API connectivity."""
    print("Testing LlamaParse integration...")
    
    # Initialize client
    client = LlamaParseClient({
        "api_key": os.getenv("LLAMAPARSE_API_KEY", "${LLAMAPARSE_API_KEY}"),
        "api_url": "https://api.llamaindex.ai",
        "timeout": 120,
        "max_retries": 3
    })
    
    try:
        # Test submitting a parse job
        result = await client.submit_parse_job(
            job_id="test-job-123",
            source_url="https://example.com/test.pdf",
            webhook_url="http://localhost:8000/webhook/llamaparse/test-job-123",
            webhook_secret="test-secret"
        )
        
        print(f"LlamaParse submission result: {result}")
        
        if result.get("success"):
            print("✅ LlamaParse integration working!")
        else:
            print(f"❌ LlamaParse integration failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ LlamaParse integration error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_llamaparse())
