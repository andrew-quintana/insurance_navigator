#!/usr/bin/env python3
"""
Test webhook storage functionality directly.
"""

import asyncio
import httpx
import json

async def test_webhook_storage():
    """Test the webhook storage functionality."""
    
    # Test job ID from our recent test
    job_id = "7f67ddfb-2e9d-4af4-81bc-1799965b6992"
    
    # Mock webhook payload with parsed content
    webhook_payload = {
        "status": "completed",
        "parsed_content": "# Test Document\n\nThis is a test document that was parsed from PDF.\n\n## Section 1\n\nSome content here.\n\n## Section 2\n\nMore content here.",
        "result": {
            "markdown": "# Test Document\n\nThis is a test document that was parsed from PDF.\n\n## Section 1\n\nSome content here.\n\n## Section 2\n\nMore content here."
        }
    }
    
    print(f"🧪 Testing webhook storage for job: {job_id}")
    print(f"📄 Parsed content length: {len(webhook_payload['parsed_content'])} characters")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"http://localhost:8000/api/upload-pipeline/webhook/llamaparse/{job_id}",
                json=webhook_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📄 Response Body: {response.text}")
            
            if response.status_code == 200:
                print("✅ Webhook processed successfully!")
            else:
                print(f"❌ Webhook failed with status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_webhook_storage())
