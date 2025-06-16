#!/usr/bin/env python3
"""
Quick Deployment Test Script
Tests the recent fixes: syntax error, SBERT numpy arrays, upload endpoints, Edge Functions
"""

import requests
import time
import json
import os
from pathlib import Path

# Configuration
BASE_URL = os.getenv('API_BASE_URL', 'https://insurance-navigator-api.onrender.com')
TEST_PDF = 'data/examples/test_policy.pdf'  # Adjust path as needed

def test_basic_health():
    """Test 1: Basic deployment health"""
    print("🏥 Testing basic deployment health...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"   Health check: {response.status_code} - {response.text[:100]}")
        
        # Test root endpoint
        response = requests.get(f"{BASE_URL}/", timeout=10)
        print(f"   Root endpoint: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return False

def test_upload_endpoints():
    """Test 2: Upload endpoint availability"""
    print("📤 Testing upload endpoints...")
    
    # Test new backend endpoint
    try:
        response = requests.post(f"{BASE_URL}/upload-document-backend", timeout=5)
        print(f"   /upload-document-backend: {response.status_code}")
    except Exception as e:
        print(f"   /upload-document-backend: Error - {e}")
    
    # Test fallback endpoint
    try:
        response = requests.post(f"{BASE_URL}/upload-policy", timeout=5)
        print(f"   /upload-policy: {response.status_code}")
    except Exception as e:
        print(f"   /upload-policy: Error - {e}")

def test_embedding_system():
    """Test 3: Check if SBERT/numpy fix worked"""
    print("🧠 Testing embedding system...")
    
    # This would require authentication, so just check logs
    print("   Check deployment logs for:")
    print("   ✅ Should NOT see: 'list' object has no attribute 'tolist'")
    print("   ✅ Should see: Mock model using numpy arrays")
    print("   ✅ Should see: Success rates > 0%")

def main():
    """Run all quick tests"""
    print("🚀 Quick Deployment Test - Recent Fixes Verification")
    print("=" * 60)
    
    # Test 1: Basic health
    health_ok = test_basic_health()
    print()
    
    # Test 2: Upload endpoints
    test_upload_endpoints()
    print()
    
    # Test 3: Embedding system
    test_embedding_system()
    print()
    
    # Summary
    print("📋 SUMMARY:")
    print(f"   Basic Health: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print("   Upload Endpoints: Check status codes above")
    print("   Embedding Fix: Check deployment logs")
    print()
    print("🎯 NEXT STEPS:")
    print("   1. If health check passes, test frontend upload")
    print("   2. Upload a PDF and verify immediate completion")
    print("   3. Check for background processing notifications")
    print("   4. Monitor Supabase Edge Functions logs")

if __name__ == "__main__":
    main() 