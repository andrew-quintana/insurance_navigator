#!/usr/bin/env python3
"""
Setup script for Phase 2.5 test environment.

This script creates the necessary test buckets and configurations
for real service integration testing.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.shared.storage.supabase_real import RealSupabaseStorage, SupabaseStorageConfig

async def setup_test_environment():
    """Set up the test environment with required buckets and configurations."""
    print("Setting up Phase 2.5 test environment...")
    
    # Load configuration
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase configuration")
        print("Please set SUPABASE_URL and SUPABASE_KEY environment variables")
        return False
    
    try:
        # Initialize storage client
        storage_config = SupabaseStorageConfig(
            url=supabase_url,
            anon_key=supabase_key,
            service_role_key=supabase_key,
            storage_bucket="test-documents"
        )
        
        storage = RealSupabaseStorage(storage_config)
        
        # List existing buckets
        print("📋 Checking existing buckets...")
        buckets = await storage.list_buckets()
        bucket_names = [b.get("name", "unknown") for b in buckets]
        print(f"Found buckets: {bucket_names}")
        
        # Create test-documents bucket if it doesn't exist
        if "test-documents" not in bucket_names:
            print("🔧 Creating test-documents bucket...")
            bucket_result = await storage.create_bucket(
                name="test-documents",
                public=False,
                file_size_limit=25 * 1024 * 1024,  # 25MB
                allowed_mime_types=["application/pdf", "text/plain", "application/octet-stream"]
            )
            print(f"Bucket created: {bucket_result}")
        else:
            print("✅ test-documents bucket already exists")
        
        # Test bucket operations
        print("🧪 Testing bucket operations...")
        buckets = await storage.list_buckets()
        bucket_names = [b.get("name", "unknown") for b in buckets]
        
        if "test-documents" in bucket_names:
            print("✅ Test environment setup completed successfully")
            return True
        else:
            print("❌ Failed to create test-documents bucket")
            return False
            
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False
    finally:
        if 'storage' in locals():
            await storage.close()

async def main():
    """Main setup function."""
    success = await setup_test_environment()
    
    if success:
        print("\n🎉 Test environment is ready for Phase 2.5 testing!")
        sys.exit(0)
    else:
        print("\n💥 Test environment setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
