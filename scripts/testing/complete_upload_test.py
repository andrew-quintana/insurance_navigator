#!/usr/bin/env python3
"""
Complete Upload Test Script for Phase 2
Handles both getting signed URL and uploading file content
"""

import requests
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
JWT_TOKEN = "${SUPABASE_JWT_TOKEN}"

# Timeout configuration with safety factors
TIMEOUTS = {
    "api_request": 30,      # 30s for API calls (expected: 5-10s)
    "file_upload": 120,     # 120s for file uploads (expected: 30-60s)
    "connect": 10,          # 10s for connection (expected: 1-3s)
    "read": 60              # 60s for response reading (expected: 10-20s)
}

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def get_upload_metadata(file_path: Path) -> Dict[str, Any]:
    """Get file metadata for upload"""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_size = file_path.stat().st_size
    file_hash = calculate_file_hash(file_path)
    
    return {
        "filename": file_path.name,
        "bytes_len": file_size,
        "mime": "application/pdf",
        "sha256": file_hash,
        "ocr": False
    }

def step1_get_signed_url(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Step 1: Get signed URL from upload endpoint"""
    print(f"🔗 Step 1: Getting signed URL for {metadata['filename']}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JWT_TOKEN}"
    }
    
    start_time = time.time()
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/upload-pipeline/upload",
            headers=headers,
            json=metadata,
            timeout=(TIMEOUTS["connect"], TIMEOUTS["read"])
        )
        end_time = time.time()
        
        print(f"   HTTP Status: {response.status_code}")
        print(f"   Response Time: {end_time - start_time:.3f}s")
        
        if response.status_code != 200:
            print(f"   ❌ Error: {response.text}")
            return None
        
        try:
            result = response.json()
            print(f"   ✅ Success! Got signed URL")
            print(f"   Job ID: {result.get('job_id')}")
            print(f"   Document ID: {result.get('document_id')}")
            print(f"   Signed URL: {result.get('signed_url')[:100]}...")
            print(f"   Expires: {result.get('upload_expires_at')}")
            return result
        except json.JSONDecodeError as e:
            print(f"   ❌ Failed to parse JSON response: {e}")
            print(f"   Raw response: {response.text}")
            return None
            
    except requests.exceptions.Timeout as e:
        print(f"   ❌ Timeout after {TIMEOUTS['read']}s: {e}")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection error: {e}")
        return None
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return None

def step2_upload_file_content(signed_url: str, file_path: Path, mime_type: str) -> bool:
    """Step 2: Upload actual file content to signed URL"""
    print(f"📤 Step 2: Uploading file content to signed URL")
    
    headers = {
        "Content-Type": mime_type
    }
    
    start_time = time.time()
    try:
        with open(file_path, 'rb') as f:
            response = requests.put(
                signed_url,
                headers=headers,
                data=f,
                timeout=(TIMEOUTS["connect"], TIMEOUTS["file_upload"])
            )
        end_time = time.time()
        
        print(f"   HTTP Status: {response.status_code}")
        print(f"   Upload Time: {end_time - start_time:.3f}s")
        
        if response.status_code in [200, 201]:
            print(f"   ✅ File content uploaded successfully!")
            return True
        else:
            print(f"   ❌ Upload failed: {response.text}")
            return False
            
    except requests.exceptions.Timeout as e:
        print(f"   ❌ Upload timeout after {TIMEOUTS['file_upload']}s: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Upload connection error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Upload error: {e}")
        return False

def test_complete_upload(file_path: str) -> bool:
    """Test complete upload process for a single file"""
    print(f"\n{'='*60}")
    print(f"🚀 Testing Complete Upload: {file_path}")
    print(f"{'='*60}")
    
    try:
        # Step 1: Get signed URL
        metadata = get_upload_metadata(file_path)
        print(f"📋 File Metadata:")
        for key, value in metadata.items():
            print(f"   {key}: {value}")
        
        signed_url_response = step1_get_signed_url(metadata)
        if not signed_url_response:
            print("❌ Failed to get signed URL")
            return False
        
        # Step 2: Upload file content
        signed_url = signed_url_response.get('signed_url')
        if not signed_url:
            print("❌ No signed URL in response")
            return False
        
        success = step2_upload_file_content(
            signed_url, 
            Path(file_path), 
            metadata['mime']
        )
        
        if success:
            print(f"✅ Complete upload successful for {file_path}")
            return True
        else:
            print(f"❌ Complete upload failed for {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Upload test error: {e}")
        return False

def main():
    """Main test execution"""
    print("🎯 Phase 2: Complete Upload Testing")
    print("Testing both signed URL generation AND file content upload")
    print(f"⏱️  Timeouts: API={TIMEOUTS['api_request']}s, Upload={TIMEOUTS['file_upload']}s")
    
    # Test files
    test_files = [
        "./examples/simulated_insurance_document.pdf",
        "./examples/scan_classic_hmo_parsed.pdf"
    ]
    
    results = []
    for file_path in test_files:
        try:
            success = test_complete_upload(file_path)
            results.append((file_path, success))
        except Exception as e:
            print(f"❌ Test failed for {file_path}: {e}")
            results.append((file_path, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Upload Test Results Summary")
    print(f"{'='*60}")
    
    for file_path, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {file_path}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All upload tests completed successfully!")
        return 0
    else:
        print("⚠️  Some upload tests failed")
        return 1

if __name__ == "__main__":
    exit(main())
