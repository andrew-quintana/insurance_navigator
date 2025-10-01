#!/usr/bin/env python3
"""
FM-027: StorageManager blob_exists Method Test

This script tests the StorageManager's blob_exists method directly to see if
it's working correctly and identify any issues with file existence checking.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the backend directory to the path so we can import StorageManager
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from shared.storage.storage_manager import StorageManager

async def test_blob_exists_method():
    """Test the StorageManager's blob_exists method"""
    print("🔍 Testing StorageManager.blob_exists method...")
    
    # Initialize StorageManager
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_anon_key = os.getenv("ANON_KEY")  # Different name in staging
        supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        # Construct storage URL from Supabase URL
        supabase_storage_url = f"{supabase_url}/storage/v1"
        
        print(f"🔧 Supabase URL: {supabase_url}")
        print(f"🔧 Storage URL: {supabase_storage_url}")
        print(f"🔧 Anon Key: {supabase_anon_key[:20] if supabase_anon_key else 'None'}...")
        print(f"🔧 Service Role Key: {supabase_service_role_key[:20] if supabase_service_role_key else 'None'}...")
        
        storage = StorageManager({
            "storage_url": supabase_storage_url,
            "anon_key": supabase_anon_key,
            "service_role_key": supabase_service_role_key
        })
        print("✅ StorageManager initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize StorageManager: {str(e)}")
        return
    
    # Test with the failed job's document ID
    document_id = "2f064818-4568-5ca2-ad05-e26484d8f1c4"
    job_id = "4eaa5cf2-1141-4471-8f9c-f7fc47b80386"
    
    print(f"📋 Testing with Document ID: {document_id}")
    print(f"📋 Job ID: {job_id}")
    
    # Test different possible file paths
    test_paths = [
        f"files/{document_id}.pdf",
        f"files/{document_id}",
        f"files/documents/{document_id}.pdf",
        f"files/uploads/{document_id}.pdf",
        f"files/{document_id}/document.pdf",
        "files/test-document.pdf",  # Generic test file
        "files/nonexistent-file.pdf"  # Should definitely not exist
    ]
    
    print(f"\n🧪 Testing {len(test_paths)} different file paths...")
    print("=" * 60)
    
    results = {}
    
    for i, file_path in enumerate(test_paths, 1):
        print(f"\n{i}. Testing: {file_path}")
        print("-" * 40)
        
        try:
            # Test blob_exists
            start_time = datetime.now()
            exists = await storage.blob_exists(file_path)
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            
            result = {
                "file_path": file_path,
                "exists": exists,
                "duration_seconds": duration,
                "error": None,
                "timestamp": start_time.isoformat()
            }
            
            if exists:
                print(f"   ✅ File EXISTS (checked in {duration:.3f}s)")
            else:
                print(f"   ❌ File does NOT exist (checked in {duration:.3f}s)")
            
            # Also test read_blob to see what error we get
            try:
                print(f"   🔍 Testing read_blob...")
                content = await storage.read_blob(file_path)
                if content:
                    print(f"   ✅ read_blob successful - {len(content)} bytes")
                    result["read_blob_success"] = True
                    result["content_length"] = len(content)
                else:
                    print(f"   ⚠️  read_blob returned empty content")
                    result["read_blob_success"] = False
                    result["content_length"] = 0
            except Exception as read_error:
                print(f"   ❌ read_blob failed: {str(read_error)}")
                result["read_blob_success"] = False
                result["read_blob_error"] = str(read_error)
            
        except Exception as e:
            print(f"   💥 blob_exists failed: {str(e)}")
            result = {
                "file_path": file_path,
                "exists": False,
                "duration_seconds": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
        results[file_path] = result
    
    # Summary
    print(f"\n📊 SUMMARY")
    print("=" * 60)
    
    existing_files = [path for path, result in results.items() if result.get("exists", False)]
    non_existing_files = [path for path, result in results.items() if not result.get("exists", False)]
    
    print(f"✅ Files that exist: {len(existing_files)}")
    for path in existing_files:
        print(f"   - {path}")
    
    print(f"\n❌ Files that don't exist: {len(non_existing_files)}")
    for path in non_existing_files:
        print(f"   - {path}")
    
    # Check for errors
    error_files = [path for path, result in results.items() if result.get("error")]
    if error_files:
        print(f"\n💥 Files with errors: {len(error_files)}")
        for path in error_files:
            print(f"   - {path}: {results[path]['error']}")
    
    # Save detailed results
    import json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"storage_manager_test_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump({
            "document_id": document_id,
            "job_id": job_id,
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {filename}")
    
    return results

async def main():
    """Main test function"""
    print("🚀 FM-027: StorageManager blob_exists Method Test")
    print("=" * 60)
    
    # Check environment variables
    required_vars = ["SUPABASE_URL", "ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please set these environment variables and try again.")
        return
    
    try:
        results = await test_blob_exists_method()
        
        # Analyze results for potential issues
        print(f"\n🔍 ANALYSIS")
        print("=" * 60)
        
        # Check if any files exist
        any_exist = any(result.get("exists", False) for result in results.values())
        if not any_exist:
            print("⚠️  WARNING: No files were found to exist!")
            print("   This could indicate:")
            print("   - Files are not being uploaded to the expected location")
            print("   - File path format is incorrect")
            print("   - Authentication issues with Supabase Storage")
            print("   - Files are being deleted before processing")
        
        # Check for authentication errors
        auth_errors = [path for path, result in results.items() 
                      if result.get("error") and "401" in str(result.get("error"))]
        if auth_errors:
            print(f"🔐 AUTHENTICATION ISSUES detected in {len(auth_errors)} files")
            print("   Check SUPABASE_SERVICE_ROLE_KEY configuration")
        
        # Check for network errors
        network_errors = [path for path, result in results.items() 
                         if result.get("error") and any(err in str(result.get("error")).lower() 
                                                      for err in ["timeout", "connection", "network"])]
        if network_errors:
            print(f"🌐 NETWORK ISSUES detected in {len(network_errors)} files")
            print("   Check network connectivity and Supabase Storage URL")
        
    except Exception as e:
        print(f"💥 Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
