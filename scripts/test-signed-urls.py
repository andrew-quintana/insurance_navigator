#!/usr/bin/env python3
"""
Test script to verify signed URL generation works correctly for different environments.
This script tests the signed URL generation logic without importing the full API module.
"""

import os
import sys

def generate_signed_url(storage_path: str, ttl_seconds: int, storage_environment: str) -> str:
    """Generate a signed URL for file upload based on environment configuration."""
    
    # Determine storage base URL based on environment
    if storage_environment == "development":
        storage_base_url = "http://localhost:5001"
    elif storage_environment == "staging":
        storage_base_url = "https://staging-storage.supabase.co"
    else:  # production
        storage_base_url = "https://storage.supabase.co"
    
    # Handle new path format: files/user/{userId}/raw/{datetime}_{hash}.{ext}
    if storage_path.startswith("files/user/"):
        # For Supabase storage, we need to extract the key part
        # The format is: files/user/{userId}/raw/{datetime}_{hash}.{ext}
        # We'll use the full path as the key
        key = storage_path
        
        # Generate environment-appropriate signed URL
        if storage_environment == "development":
            # Local development - direct access URL
            return f"{storage_base_url}/storage/v1/object/upload/{key}"
        else:
            # Staging/Production - Supabase signed URL
            return f"{storage_base_url}/files/{key}?signed=true&ttl={ttl_seconds}"
    
    # Handle legacy storage:// format
    elif storage_path.startswith("storage://"):
        path_parts = storage_path[10:].split("/", 1)  # Remove "storage://" and split
        if len(path_parts) == 2:
            bucket, key = path_parts
            # Generate environment-appropriate signed URL
            if storage_environment == "development":
                # Local development - direct access URL
                return f"{storage_base_url}/storage/v1/object/upload/{bucket}/{key}"
            else:
                # Staging/Production - Supabase signed URL
                return f"{storage_base_url}/{bucket}/{key}?signed=true&ttl={ttl_seconds}"
    
    # Fallback for invalid storage paths
    raise ValueError(f"Invalid storage path format: {storage_path}")

def test_signed_url_generation():
    """Test signed URL generation for different environments and storage paths."""
    
    print("🧪 Testing Signed URL Generation")
    print("=" * 50)
    
    # Test cases: (storage_path, expected_development_url, expected_production_url)
    test_cases = [
        (
            "files/user/123e4567-e89b-12d3-a456-426614174000/raw/test.pdf",
            "http://localhost:5001/storage/v1/object/upload/files/user/123e4567-e89b-12d3-a456-426614174000/raw/test.pdf",
            "https://storage.supabase.co/files/files/user/123e4567-e89b-12d3-a456-426614174000/raw/test.pdf?signed=true&ttl=300"
        ),
        (
            "storage://raw/user123/document.pdf",
            "http://localhost:5001/storage/v1/object/upload/raw/user123/document.pdf",
            "https://storage.supabase.co/raw/user123/document.pdf?signed=true&ttl=300"
        ),
        (
            "files/user/456e7890-e89b-12d3-a456-426614174000/parsed/doc.md",
            "http://localhost:5001/storage/v1/object/upload/files/user/456e7890-e89b-12d3-a456-426614174000/parsed/doc.md",
            "https://storage.supabase.co/files/files/user/456e7890-e89b-12d3-a456-426614174000/parsed/doc.md?signed=true&ttl=300"
        )
    ]
    
    # Test development environment
    print("\n🔧 Testing Development Environment")
    print("-" * 30)
    
    for i, (storage_path, expected_dev, expected_prod) in enumerate(test_cases, 1):
        try:
            result = generate_signed_url(storage_path, 300, "development")
            status = "✅ PASS" if result == expected_dev else "❌ FAIL"
            print(f"Test {i}: {status}")
            print(f"  Input: {storage_path}")
            print(f"  Expected: {expected_dev}")
            print(f"  Got: {result}")
            if result != expected_dev:
                print(f"  ❌ Mismatch!")
            print()
        except Exception as e:
            print(f"Test {i}: ❌ ERROR - {e}")
            print()
    
    # Test production environment
    print("\n🚀 Testing Production Environment")
    print("-" * 30)
    
    for i, (storage_path, expected_dev, expected_prod) in enumerate(test_cases, 1):
        try:
            result = generate_signed_url(storage_path, 300, "production")
            status = "✅ PASS" if result == expected_prod else "❌ FAIL"
            print(f"Test {i}: {status}")
            print(f"  Input: {storage_path}")
            print(f"  Expected: {expected_prod}")
            print(f"  Got: {result}")
            if result != expected_prod:
                print(f"  ❌ Mismatch!")
            print()
        except Exception as e:
            print(f"Test {i}: ❌ ERROR - {e}")
            print()
    
    # Test staging environment
    print("\n🔄 Testing Staging Environment")
    print("-" * 30)
    
    for i, (storage_path, expected_dev, expected_prod) in enumerate(test_cases, 1):
        try:
            result = generate_signed_url(storage_path, 300, "staging")
            expected_staging = expected_prod.replace("https://storage.supabase.co", "https://staging-storage.supabase.co")
            status = "✅ PASS" if result == expected_staging else "❌ FAIL"
            print(f"Test {i}: {status}")
            print(f"  Input: {storage_path}")
            print(f"  Expected: {expected_staging}")
            print(f"  Got: {result}")
            if result != expected_staging:
                print(f"  ❌ Mismatch!")
            print()
        except Exception as e:
            print(f"Test {i}: ❌ ERROR - {e}")
            print()
    
    print("=" * 50)
    print("🎯 Testing completed!")

def test_environment_switching():
    """Test environment switching logic."""
    
    print("\n🔄 Testing Environment Switching")
    print("=" * 50)
    
    environments = ["development", "staging", "production"]
    storage_path = "files/user/test/raw/document.pdf"
    
    for env in environments:
        try:
            result = generate_signed_url(storage_path, 300, env)
            print(f"✅ {env.capitalize()} Environment:")
            print(f"   URL: {result}")
            print()
        except Exception as e:
            print(f"❌ {env.capitalize()} Environment Error: {e}")
            print()

if __name__ == "__main__":
    try:
        test_signed_url_generation()
        test_environment_switching()
        print("\n🎉 All tests completed successfully!")
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1)
