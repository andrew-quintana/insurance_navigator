#!/usr/bin/env python3
"""
Test Backend-Orchestrated Upload Pipeline

This script tests the new /upload-document-backend endpoint that:
1. Orchestrates the complete edge function pipeline
2. Ensures LlamaParse processing for PDFs
3. Provides reliable user and regulatory document uploads
"""

import asyncio
import aiohttp
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

# Test credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"
TEST_NAME = "Test User"

async def test_backend_orchestrated_upload():
    """Test the complete backend-orchestrated upload pipeline."""
    
    print("🚀 Testing Backend-Orchestrated Upload Pipeline")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Supabase URL: {SUPABASE_URL}")
    print()
    
    # Create test file content
    test_content = """
    Sample Insurance Policy Document
    
    Policy Number: TEST-12345
    Policy Holder: John Doe
    Coverage: Medical Insurance
    Effective Date: 2024-01-01
    
    This is a test document for the backend-orchestrated upload pipeline.
    It should be processed with LlamaParse if it's a PDF, or direct processing if it's text.
    
    Benefits:
    - Hospital coverage: $100,000
    - Doctor visits: $50 copay
    - Prescription drugs: 80% coverage
    - Emergency room: $200 copay
    
    This document contains important information about your insurance coverage.
    """
    
    timeout = aiohttp.ClientTimeout(total=120)  # 2 minute timeout
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        # Step 1: Register/Login to get authentication token
        print("🔐 Step 1: Authentication")
        print("-" * 25)
        
        # Try to register user (will fail if exists, that's OK)
        register_payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": TEST_NAME
        }
        
        try:
            async with session.post(f"{BACKEND_URL}/register", json=register_payload) as response:
                if response.status == 200:
                    register_data = await response.json()
                    print(f"✅ User registered successfully")
                    auth_token = register_data['access_token']
                elif response.status == 400:
                    print(f"ℹ️ User already exists, proceeding to login...")
                    auth_token = None
                else:
                    error_text = await response.text()
                    print(f"❌ Registration failed: {response.status} - {error_text}")
                    auth_token = None
        except Exception as e:
            print(f"❌ Registration error: {e}")
            auth_token = None
        
        # Login to get token
        if not auth_token:
            login_payload = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            try:
                async with session.post(f"{BACKEND_URL}/login", json=login_payload) as response:
                    if response.status == 200:
                        login_data = await response.json()
                        auth_token = login_data['access_token']
                        print(f"✅ Login successful")
                    else:
                        error_text = await response.text()
                        print(f"❌ Login failed: {response.status} - {error_text}")
                        return False
            except Exception as e:
                print(f"❌ Login error: {e}")
                return False
        
        if not auth_token:
            print("❌ Could not obtain authentication token")
            return False
        
        print(f"🎫 Auth token: {auth_token[:20]}...")
        print()
        
        # Step 2: Test backend-orchestrated upload
        print("📤 Step 2: Backend-Orchestrated Upload")
        print("-" * 35)
        
        # Prepare multipart form data
        form_data = aiohttp.FormData()
        form_data.add_field('file', 
                           test_content.encode('utf-8'),
                           filename='test_policy.txt',
                           content_type='text/plain')
        
        headers = {
            'Authorization': f'Bearer {auth_token}'
        }
        
        try:
            print(f"🔄 Uploading test document via backend orchestration...")
            
            async with session.post(f"{BACKEND_URL}/upload-document-backend", 
                                  data=form_data, 
                                  headers=headers) as response:
                
                upload_status = response.status
                upload_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                print(f"📊 Upload Status: {upload_status}")
                
                if upload_status == 200:
                    print(f"✅ Backend-orchestrated upload successful!")
                    print(f"📄 Document ID: {upload_data.get('document_id')}")
                    print(f"📁 Filename: {upload_data.get('filename')}")
                    print(f"📈 Status: {upload_data.get('status')}")
                    print(f"🔧 Processing Method: {upload_data.get('processing_method')}")
                    print(f"💬 Message: {upload_data.get('message')}")
                    
                    document_id = upload_data.get('document_id')
                    
                else:
                    print(f"❌ Upload failed: {upload_data}")
                    return False
                    
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False
        
        print()
        
        # Step 3: Test regulatory document upload
        print("🏛️ Step 3: Regulatory Document Upload")
        print("-" * 35)
        
        regulatory_content = """
        Medicare Advantage Plan Guidelines
        
        Document Type: Regulatory Guidance
        Agency: Centers for Medicare & Medicaid Services (CMS)
        Publication Date: 2024
        
        This document provides guidance on Medicare Advantage plan requirements,
        including coverage standards, network adequacy, and quality measures.
        
        Key Requirements:
        1. Network adequacy standards must be met
        2. Essential health benefits must be covered
        3. Quality ratings must be maintained
        4. Member appeals processes must be established
        
        This is a test regulatory document for the backend-orchestrated pipeline.
        """
        
        # Prepare regulatory upload form data
        reg_form_data = aiohttp.FormData()
        reg_form_data.add_field('file', 
                               regulatory_content.encode('utf-8'),
                               filename='medicare_guidelines.txt',
                               content_type='text/plain')
        reg_form_data.add_field('document_title', 'Medicare Advantage Plan Guidelines')
        reg_form_data.add_field('source_url', 'https://cms.gov/test-guidelines')
        reg_form_data.add_field('category', 'medicare_guidance')
        
        try:
            print(f"🔄 Uploading regulatory document...")
            
            async with session.post(f"{BACKEND_URL}/upload-regulatory-document", 
                                  data=reg_form_data, 
                                  headers=headers) as response:
                
                reg_status = response.status
                reg_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                print(f"📊 Regulatory Upload Status: {reg_status}")
                
                if reg_status == 200:
                    print(f"✅ Regulatory document upload successful!")
                    print(f"📄 Document ID: {reg_data.get('document_id')}")
                    print(f"📁 Filename: {reg_data.get('filename')}")
                    print(f"📈 Status: {reg_data.get('status')}")
                    print(f"🔧 Processing Method: {reg_data.get('processing_method')}")
                    print(f"💬 Message: {reg_data.get('message')}")
                    
                else:
                    print(f"❌ Regulatory upload failed: {reg_data}")
                    return False
                    
        except Exception as e:
            print(f"❌ Regulatory upload error: {e}")
            return False
        
        print()
        
        # Step 4: Verify documents in database (if we have direct DB access)
        print("🔍 Step 4: Verification")
        print("-" * 20)
        print("✅ Both uploads completed successfully!")
        print("📋 Documents should now be processing via edge functions")
        print("🦙 PDFs will use LlamaParse, text files will use direct processing")
        print("📨 Status updates will come via webhooks")
        print()
        
        return True

async def test_health_check():
    """Test the health check endpoint."""
    print("🏥 Testing Health Check")
    print("-" * 22)
    
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(f"{BACKEND_URL}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Health check passed")
                    print(f"📊 Status: {health_data.get('status')}")
                    print(f"🔢 Version: {health_data.get('version')}")
                    print(f"🚀 Features: {health_data.get('features')}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

async def main():
    """Run all tests."""
    print("🧪 Backend-Orchestrated Upload Pipeline Tests")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Test health check first
    health_ok = await test_health_check()
    print()
    
    if not health_ok:
        print("❌ Health check failed, skipping upload tests")
        return
    
    # Test upload pipeline
    upload_ok = await test_backend_orchestrated_upload()
    
    print()
    print("📋 Test Summary")
    print("-" * 15)
    print(f"Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Upload Pipeline: {'✅ PASS' if upload_ok else '❌ FAIL'}")
    
    if health_ok and upload_ok:
        print()
        print("🎉 All tests passed! Backend-orchestrated upload pipeline is working.")
        print("🔧 Next steps:")
        print("   1. Monitor edge function logs for processing status")
        print("   2. Check document status in database")
        print("   3. Verify LlamaParse integration for PDFs")
        print("   4. Test webhook status updates")
    else:
        print()
        print("❌ Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    asyncio.run(main()) 