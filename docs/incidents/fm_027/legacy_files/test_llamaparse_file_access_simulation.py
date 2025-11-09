#!/usr/bin/env python3
"""
FM-027: LlamaParse File Access Simulation Test

This script simulates exactly what LlamaParse experiences when trying to access
a file from Supabase Storage, including:
1. Direct HTTP requests to Supabase Storage API
2. Authentication using service role key
3. File path parsing and bucket/key extraction
4. Error handling and retry logic

This will help us understand if the issue is:
- File not actually uploaded
- Authentication problems
- File path issues
- Supabase Storage API problems
- Network/timing issues
"""

import asyncio
import httpx
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

class LlamaParseFileAccessSimulator:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.supabase_storage_url = os.getenv("SUPABASE_STORAGE_URL")
        
        if not all([self.supabase_url, self.supabase_service_role_key, self.supabase_storage_url]):
            raise ValueError("Missing required Supabase environment variables")
        
        print(f"🔧 Supabase URL: {self.supabase_url}")
        print(f"🔧 Storage URL: {self.supabase_storage_url}")
        print(f"🔧 Service Role Key: {self.supabase_service_role_key[:20]}...")
    
    async def simulate_llamaparse_file_access(self, file_path: str, job_id: str) -> Dict[str, Any]:
        """
        Simulate exactly how LlamaParse would access a file from Supabase Storage
        """
        print(f"\n🎯 Simulating LlamaParse file access for: {file_path}")
        print(f"📋 Job ID: {job_id}")
        print(f"⏰ Timestamp: {datetime.now().isoformat()}")
        
        # Step 1: Parse file path to extract bucket and key
        bucket, key = self._parse_storage_path(file_path)
        print(f"📁 Parsed - Bucket: {bucket}, Key: {key}")
        
        # Step 2: Construct Supabase Storage API URL
        storage_api_url = f"{self.supabase_storage_url}/object/{bucket}/{key}"
        print(f"🌐 Storage API URL: {storage_api_url}")
        
        # Step 3: Set up authentication headers (exactly like StorageManager)
        headers = {
            "Authorization": f"Bearer {self.supabase_service_role_key}",
            "apikey": self.supabase_service_role_key,
            "Content-Type": "application/json"
        }
        
        # Step 4: Test different HTTP methods and approaches
        results = {}
        
        # Method 1: HEAD request to check if file exists
        print(f"\n1️⃣ Testing HEAD request (file existence check)...")
        head_result = await self._test_head_request(storage_api_url, headers)
        results["head_request"] = head_result
        
        # Method 2: GET request to download file
        print(f"\n2️⃣ Testing GET request (file download)...")
        get_result = await self._test_get_request(storage_api_url, headers)
        results["get_request"] = get_result
        
        # Method 3: List objects in bucket to see what's actually there
        print(f"\n3️⃣ Testing bucket listing...")
        list_result = await self._test_bucket_listing(bucket, headers)
        results["bucket_listing"] = list_result
        
        # Method 4: Test with different file path formats
        print(f"\n4️⃣ Testing alternative file path formats...")
        alt_paths = self._generate_alternative_paths(file_path)
        alt_results = {}
        for alt_path in alt_paths:
            alt_bucket, alt_key = self._parse_storage_path(alt_path)
            alt_url = f"{self.supabase_storage_url}/object/{alt_bucket}/{alt_key}"
            alt_result = await self._test_head_request(alt_url, headers)
            alt_results[alt_path] = alt_result
        results["alternative_paths"] = alt_results
        
        return results
    
    def _parse_storage_path(self, file_path: str) -> tuple[str, str]:
        """Parse storage path to extract bucket and key (same logic as StorageManager)"""
        if file_path.startswith('files/'):
            bucket = 'files'
            key = file_path[6:]  # Remove 'files/' prefix
        else:
            raise Exception(f"Invalid file path format: {file_path}")
        return bucket, key
    
    def _generate_alternative_paths(self, file_path: str) -> list[str]:
        """Generate alternative file path formats to test"""
        alternatives = [file_path]
        
        # Remove leading slash if present
        if file_path.startswith('/'):
            alternatives.append(file_path[1:])
        
        # Add leading slash if not present
        if not file_path.startswith('/'):
            alternatives.append(f"/{file_path}")
        
        # Try without 'files/' prefix
        if file_path.startswith('files/'):
            alternatives.append(file_path[6:])
        
        # Try with different separators
        if '/' in file_path:
            alternatives.append(file_path.replace('/', '\\'))
        
        return list(set(alternatives))  # Remove duplicates
    
    async def _test_head_request(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Test HEAD request to check file existence"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.head(url, headers=headers)
                
                result = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "success": response.status_code == 200,
                    "error": None
                }
                
                if response.status_code == 200:
                    print(f"   ✅ HEAD request successful - File exists")
                    print(f"   📊 Content-Length: {response.headers.get('content-length', 'unknown')}")
                    print(f"   📊 Content-Type: {response.headers.get('content-type', 'unknown')}")
                else:
                    print(f"   ❌ HEAD request failed - Status: {response.status_code}")
                    print(f"   📝 Response: {response.text}")
                
                return result
                
        except Exception as e:
            print(f"   💥 HEAD request exception: {str(e)}")
            return {
                "status_code": None,
                "headers": {},
                "success": False,
                "error": str(e)
            }
    
    async def _test_get_request(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Test GET request to download file"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=headers)
                
                result = {
                    "status_code": response.status_code,
                    "content_length": len(response.content) if response.content else 0,
                    "content_type": response.headers.get('content-type'),
                    "success": response.status_code == 200,
                    "error": None
                }
                
                if response.status_code == 200:
                    print(f"   ✅ GET request successful - Downloaded {len(response.content)} bytes")
                    print(f"   📊 Content-Type: {response.headers.get('content-type', 'unknown')}")
                else:
                    print(f"   ❌ GET request failed - Status: {response.status_code}")
                    print(f"   📝 Response: {response.text[:200]}...")
                
                return result
                
        except Exception as e:
            print(f"   💥 GET request exception: {str(e)}")
            return {
                "status_code": None,
                "content_length": 0,
                "content_type": None,
                "success": False,
                "error": str(e)
            }
    
    async def _test_bucket_listing(self, bucket: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Test listing objects in bucket to see what's actually there"""
        try:
            list_url = f"{self.supabase_storage_url}/object/list/{bucket}"
            print(f"   🔍 Listing bucket: {list_url}")
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(list_url, headers=headers, json={"limit": 100})
                
                result = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "objects": [],
                    "error": None
                }
                
                if response.status_code == 200:
                    data = response.json()
                    objects = data.get("data", [])
                    result["objects"] = objects
                    print(f"   ✅ Bucket listing successful - Found {len(objects)} objects")
                    
                    # Show first few objects
                    for i, obj in enumerate(objects[:5]):
                        print(f"   📄 Object {i+1}: {obj.get('name', 'unknown')}")
                else:
                    print(f"   ❌ Bucket listing failed - Status: {response.status_code}")
                    print(f"   📝 Response: {response.text}")
                
                return result
                
        except Exception as e:
            print(f"   💥 Bucket listing exception: {str(e)}")
            return {
                "status_code": None,
                "success": False,
                "objects": [],
                "error": str(e)
            }

async def test_with_real_job_data():
    """Test with real job data from the database"""
    print("🔍 Testing with real job data from database...")
    
    # Get the latest failed job
    job_id = "4eaa5cf2-1141-4471-8f9c-f7fc47b80386"
    document_id = "2f064818-4568-5ca2-ad05-e26484d8f1c4"
    
    print(f"📋 Testing Job ID: {job_id}")
    print(f"📄 Document ID: {document_id}")
    
    # We need to construct the file path - let's try common patterns
    possible_paths = [
        f"files/{document_id}.pdf",
        f"files/{document_id}",
        f"files/documents/{document_id}.pdf",
        f"files/uploads/{document_id}.pdf",
        f"files/{document_id}/document.pdf"
    ]
    
    simulator = LlamaParseFileAccessSimulator()
    
    for file_path in possible_paths:
        print(f"\n{'='*60}")
        print(f"🧪 Testing file path: {file_path}")
        print(f"{'='*60}")
        
        try:
            results = await simulator.simulate_llamaparse_file_access(file_path, job_id)
            
            # Save results to file for analysis
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"llamaparse_simulation_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump({
                    "job_id": job_id,
                    "document_id": document_id,
                    "file_path": file_path,
                    "timestamp": datetime.now().isoformat(),
                    "results": results
                }, f, indent=2)
            
            print(f"💾 Results saved to: {filename}")
            
        except Exception as e:
            print(f"💥 Simulation failed for {file_path}: {str(e)}")

async def test_with_manual_file_path():
    """Test with a manually specified file path"""
    print("\n🔍 Testing with manual file path...")
    
    # You can modify this to test specific file paths
    test_file_path = input("Enter file path to test (or press Enter for default): ").strip()
    if not test_file_path:
        test_file_path = "files/test-document.pdf"
    
    simulator = LlamaParseFileAccessSimulator()
    
    try:
        results = await simulator.simulate_llamaparse_file_access(test_file_path, "manual-test")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"llamaparse_manual_test_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump({
                "file_path": test_file_path,
                "timestamp": datetime.now().isoformat(),
                "results": results
            }, f, indent=2)
        
        print(f"💾 Results saved to: {filename}")
        
    except Exception as e:
        print(f"💥 Manual test failed: {str(e)}")

async def main():
    """Main test function"""
    print("🚀 FM-027: LlamaParse File Access Simulation Test")
    print("=" * 60)
    
    try:
        # Test with real job data
        await test_with_real_job_data()
        
        # Test with manual file path
        await test_with_manual_file_path()
        
    except Exception as e:
        print(f"💥 Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
