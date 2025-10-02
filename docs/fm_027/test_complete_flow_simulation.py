#!/usr/bin/env python3
"""
FM-027: Complete Flow Simulation Test

This script simulates the complete flow from document upload to worker processing
to identify where the file path mismatch occurs.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from shared.storage.storage_manager import StorageManager

async def simulate_complete_flow():
    """Simulate the complete flow from upload to processing"""
    
    print("🚀 FM-027: Complete Flow Simulation Test")
    print("=" * 60)
    
    # Simulate the API upload process
    print("\n1️⃣ SIMULATING API UPLOAD PROCESS")
    print("-" * 40)
    
    # These would be the values from a real upload
    user_id = "74a635ac-4bfe-4b6e-87d2-c0f54a366fbe"
    document_id = "2f064818-4568-5ca2-ad05-e26484d8f1c4"
    filename = "test_document.pdf"
    
    print(f"User ID: {user_id}")
    print(f"Document ID: {document_id}")
    print(f"Filename: {filename}")
    
    # Simulate generate_storage_path (from API)
    from api.upload_pipeline.utils.upload_pipeline_utils import generate_storage_path
    raw_path = generate_storage_path(user_id, document_id, filename)
    print(f"Generated raw_path: {raw_path}")
    
    # Simulate job creation
    print(f"\n2️⃣ SIMULATING JOB CREATION")
    print("-" * 40)
    
    # This is what would be stored in the job
    job_data = {
        "job_id": "test-job-123",
        "document_id": document_id,
        "user_id": user_id,
        "storage_path": raw_path,
        "mime_type": "application/pdf"
    }
    
    print(f"Job data: {job_data}")
    
    # Simulate worker processing
    print(f"\n3️⃣ SIMULATING WORKER PROCESSING")
    print("-" * 40)
    
    # Initialize StorageManager
    storage = StorageManager({
        "storage_url": "https://dfgzeastcxnoqshgyotp.supabase.co/storage/v1",
        "anon_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0ODMsImV4cCI6MjA2NzI1NjQ4M30.wV0kgqo20D1EghH47bO-4MoXpksiyQ_bvANaZlzScyM",
        "service_role_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTY4MDQ4MywiZXhwIjoyMDY3MjU2NDgzfQ.yYQWEJkDtvFXg-F2Xe4mh9Xj_0QCp6gnXkDI6lEhDT8"
    })
    
    # Get storage_path from job (this is what the worker does)
    storage_path = job_data.get("storage_path")
    print(f"Worker gets storage_path: {storage_path}")
    
    # Test file existence check (this is what our fix does)
    print(f"\n4️⃣ TESTING FILE EXISTENCE CHECK")
    print("-" * 40)
    
    print(f"Checking if file exists: {storage_path}")
    file_exists = await storage.blob_exists(storage_path)
    print(f"File exists: {file_exists}")
    
    if file_exists:
        print("✅ File exists - worker should be able to process it")
        
        # Test reading the file
        print(f"\n5️⃣ TESTING FILE READ")
        print("-" * 40)
        
        try:
            content = await storage.read_blob(storage_path)
            print(f"File read successful - {len(content)} bytes")
            print("✅ Worker should be able to read the file")
        except Exception as e:
            print(f"❌ File read failed: {str(e)}")
    else:
        print("❌ File does not exist - this is the problem!")
        
        # Let's check what files actually exist
        print(f"\n6️⃣ CHECKING WHAT FILES ACTUALLY EXIST")
        print("-" * 40)
        
        # Test with the actual file we found
        actual_file_path = "files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/b8cfa47a_5e4390c2.pdf"
        print(f"Testing with actual file: {actual_file_path}")
        
        actual_exists = await storage.blob_exists(actual_file_path)
        print(f"Actual file exists: {actual_exists}")
        
        if actual_exists:
            print("✅ The actual file exists, but the generated path doesn't match!")
            print(f"Generated path: {raw_path}")
            print(f"Actual path: {actual_file_path}")
            print("\n🔍 ANALYSIS:")
            print("The issue is that the generate_storage_path function creates a different path")
            print("than what's actually stored in the database. This suggests:")
            print("1. The file was uploaded with a different path than generated")
            print("2. The path generation logic has changed since the file was uploaded")
            print("3. There's a mismatch between upload and processing logic")

async def main():
    """Main function"""
    try:
        await simulate_complete_flow()
    except Exception as e:
        print(f"💥 Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
