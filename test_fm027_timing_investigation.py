#!/usr/bin/env python3
"""
FM-027 Timing Issue Investigation Test

This test reproduces the exact timing issue where:
- Worker environment: 400 "Bucket not found" 
- Local environment: 200 OK with PDF content
"""

import asyncio
import httpx
import os
import time
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
from typing import Dict, List

# Load environment variables
load_dotenv('.env.staging')

class FM027TimingInvestigation:
    def __init__(self):
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.file_path = 'files/user/8d65c725-ff38-4726-809e-018c05dfb874/raw/9966956e_222c3864.pdf'
        self.url = f'{self.supabase_url}/storage/v1/object/{self.file_path}'
        
        # Headers that match worker configuration
        self.headers = {
            'apikey': self.service_role_key,
            'authorization': f'Bearer {self.service_role_key}',
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate',
            'connection': 'keep-alive',
            'user-agent': 'python-httpx/0.28.1'
        }
        
        print(f"FM-027 Timing Investigation")
        print(f"URL: {self.url}")
        print(f"Service role key present: {bool(self.service_role_key)}")
        print(f"Service role key length: {len(self.service_role_key) if self.service_role_key else 0}")
        print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 80)

    async def test_single_request(self, test_name: str, additional_headers: Dict = None) -> Dict:
        """Test a single request with specific configuration"""
        headers = self.headers.copy()
        if additional_headers:
            headers.update(additional_headers)
            
        print(f"\n{test_name}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                start_time = time.time()
                response = await client.get(self.url, headers=headers)
                end_time = time.time()
                
                result = {
                    'test_name': test_name,
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'headers': dict(response.headers),
                    'content_length': len(response.content),
                    'success': response.status_code == 200,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
                if response.status_code == 200:
                    print(f"✅ SUCCESS: {response.status_code} - {result['content_length']} bytes")
                    print(f"   Response time: {result['response_time']:.3f}s")
                else:
                    print(f"❌ FAILURE: {response.status_code}")
                    print(f"   Response: {response.text}")
                
                return result
                
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            return {
                'test_name': test_name,
                'status_code': 0,
                'response_time': 0,
                'headers': {},
                'content_length': 0,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    async def test_timing_scenarios(self):
        """Test various timing scenarios to identify the issue"""
        results = []
        
        # Test 1: Basic request (should work)
        result = await self.test_single_request("Test 1: Basic Request")
        results.append(result)
        
        # Test 2: Multiple rapid requests (timing issue)
        print(f"\nTest 2: Multiple Rapid Requests")
        for i in range(5):
            result = await self.test_single_request(f"Test 2.{i+1}: Rapid Request {i+1}")
            results.append(result)
            await asyncio.sleep(0.1)  # Small delay between requests
        
        return results

    async def run_investigation(self):
        """Run the complete investigation"""
        print("Starting FM-027 Timing Investigation...")
        
        # Test timing scenarios
        results = await self.test_timing_scenarios()
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fm027_timing_investigation_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'investigation_timestamp': datetime.now(timezone.utc).isoformat(),
                'file_path': self.file_path,
                'url': self.url,
                'results': results
            }, f, indent=2)
        
        print(f"\nResults saved to: {filename}")
        return results

async def main():
    investigation = FM027TimingInvestigation()
    await investigation.run_investigation()

if __name__ == "__main__":
    asyncio.run(main())
