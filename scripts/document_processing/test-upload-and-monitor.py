#!/usr/bin/env python3
"""
Test script to upload a document and monitor job processing in real-time.
This helps identify exactly where the processing pipeline is failing.
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
API_BASE = "https://insurance-navigator-api.onrender.com"
SUPABASE_URL = "https://jhrespvvhbnloxrieycf.supabase.co"

# Test credentials (from your logs)
TEST_EMAIL = "deploymenttest@example.com"
TEST_PASSWORD = "testpass123"

def login():
    """Login and get access token"""
    try:
        response = requests.post(
            f"{API_BASE}/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ Login successful, token received")
            return token
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def create_test_file():
    """Create a simple test PDF content"""
    # Create a simple text file that we'll pretend is a PDF
    test_content = f"""
Medicare Plan Document - Test Upload
Generated at: {datetime.now()}

This is a test document for the Insurance Navigator system.
It contains sample Medicare plan information.

Plan Details:
- Plan Name: Test HMO Plan
- Plan ID: TEST-001
- Coverage Area: Test County
- Monthly Premium: $50.00

Benefits:
- Doctor Visits: $20 copay
- Emergency Room: $100 copay  
- Prescription Drugs: Tier 1 $10, Tier 2 $25

This document is being used to test the upload and processing pipeline.
"""
    return test_content.encode('utf-8')

def upload_document(token):
    """Upload a test document"""
    try:
        files = {
            'file': ('test_medicare_plan.pdf', create_test_file(), 'application/pdf')
        }
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        print("🚀 Uploading test document...")
        response = requests.post(
            f"{API_BASE}/upload-document-backend",
            files=files,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Upload successful!")
            print(f"📄 Document ID: {data.get('document_id')}")
            print(f"📊 Response: {json.dumps(data, indent=2)}")
            return data.get('document_id')
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

def monitor_document_processing(doc_id, max_wait_minutes=5):
    """Monitor document processing status"""
    print(f"\n📊 Monitoring document {doc_id} processing...")
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    check_interval = 10  # Check every 10 seconds
    
    while time.time() - start_time < max_wait_seconds:
        try:
            # Check document status
            response = requests.get(f"{API_BASE}/debug/document/{doc_id}/status", timeout=10)
            
            if response.status_code == 200:
                status = response.json()
                print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Document Status:")
                print(f"   📄 Status: {status.get('document', {}).get('status', 'unknown')}")
                print(f"   📊 Progress: {status.get('document', {}).get('progress_percentage', 0)}%")
                print(f"   🔧 Jobs: {status.get('job_summary', {})}")
                
                # Check if processing is complete
                doc_status = status.get('document', {}).get('status')
                if doc_status in ['completed', 'ready']:
                    print(f"✅ Document processing completed!")
                    return True
                elif doc_status == 'failed':
                    print(f"❌ Document processing failed!")
                    return False
                    
            else:
                print(f"⚠️ Status check failed: {response.status_code}")
            
            # Trigger job processing
            trigger_job_processing()
            
            # Wait before next check
            time.sleep(check_interval)
            
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            time.sleep(check_interval)
    
    print(f"⏰ Monitoring timeout after {max_wait_minutes} minutes")
    return False

def trigger_job_processing():
    """Manually trigger job processing"""
    try:
        service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        if not service_role_key:
            return False
            
        response = requests.post(
            f"{SUPABASE_URL}/functions/v1/job-processor",
            headers={
                "Authorization": f"Bearer {service_role_key}",
                "Content-Type": "application/json"
            },
            json={
                "source": "monitoring",
                "timestamp": datetime.now().isoformat()
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            processed = result.get('processed', 0)
            if processed > 0:
                print(f"🔄 Processed {processed} jobs")
            return True
        else:
            return False
            
    except Exception as e:
        return False

def main():
    print("🧪 Insurance Navigator Upload & Processing Test")
    print("=" * 50)
    
    # Step 1: Check environment
    if not os.getenv('SUPABASE_SERVICE_ROLE_KEY'):
        print("⚠️  SUPABASE_SERVICE_ROLE_KEY not found")
        print("💡 Some monitoring features will be limited")
    
    # Step 2: Login
    print("\n🔐 Logging in...")
    token = login()
    if not token:
        print("❌ Cannot proceed without login")
        return
    
    # Step 3: Upload document
    print("\n📤 Testing document upload...")
    doc_id = upload_document(token)
    if not doc_id:
        print("❌ Upload failed, cannot test processing")
        return
    
    # Step 4: Monitor processing
    print(f"\n📊 Starting processing monitor for document: {doc_id}")
    success = monitor_document_processing(doc_id)
    
    # Step 5: Final status
    if success:
        print("\n✅ Test completed successfully!")
        print("🎉 Document upload and processing pipeline is working!")
    else:
        print("\n❌ Test failed or timed out")
        print("🔧 There may be issues with the job processing pipeline")
        
    print(f"\n📄 Test document ID: {doc_id}")
    print("💡 You can check this document in your frontend or debug endpoints")

if __name__ == "__main__":
    main() 