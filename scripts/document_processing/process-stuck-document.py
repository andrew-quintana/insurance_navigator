#!/usr/bin/env python3
"""
Script to find and manually process stuck documents, specifically scan_classic_hmo.pdf
"""

import requests
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase URL from environment
SUPABASE_URL = os.getenv('SUPABASE_URL')
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable not set")

# Configuration
API_BASE = "https://insurance-navigator-api.onrender.com"

# Test credentials
TEST_EMAIL = "deploymenttest@example.com"
TEST_PASSWORD = "testpass123"

def login():
    """Login and get access token"""
    try:
        response = requests.post(
            f"{API_BASE}/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"❌ Login failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def find_stuck_documents(token):
    """Find documents that might be stuck in processing"""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        
        # Try to get user's documents (this endpoint might exist)
        response = requests.get(f"{API_BASE}/documents", headers=headers, timeout=10)
        
        if response.status_code == 200:
            docs = response.json()
            print(f"📄 Found {len(docs)} documents:")
            
            stuck_docs = []
            for doc in docs:
                if isinstance(doc, dict):
                    filename = doc.get('original_filename', 'Unknown')
                    status = doc.get('status', 'Unknown')
                    progress = doc.get('progress_percentage', 0)
                    doc_id = doc.get('id', 'Unknown')
                    
                    print(f"  📄 {filename} - Status: {status}, Progress: {progress}%, ID: {doc_id}")
                    
                    # Look for scan_classic_hmo.pdf or stuck documents
                    if ('scan_classic_hmo' in filename.lower() or 
                        status in ['processing', 'uploaded'] or 
                        (progress > 0 and progress < 100)):
                        stuck_docs.append(doc)
            
            return stuck_docs
        else:
            print(f"❌ Could not fetch documents: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error fetching documents: {e}")
        return []

def manually_trigger_job_processing():
    """Manually trigger the Supabase job processor"""
    try:
        service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        if not service_role_key:
            print("⚠️  SUPABASE_SERVICE_ROLE_KEY not found - trying without it")
            return False
            
        response = requests.post(
            f"{SUPABASE_URL}/functions/v1/job-processor",
            headers={
                "Authorization": f"Bearer {service_role_key}",
                "Content-Type": "application/json"
            },
            json={
                "source": "manual_recovery",
                "timestamp": datetime.now().isoformat()
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Job processor triggered: {result}")
            return True
        else:
            print(f"❌ Job processor failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Job processor error: {e}")
        return False

def check_document_status(doc_id):
    """Check specific document status"""
    try:
        response = requests.get(f"{API_BASE}/debug/document/{doc_id}/status", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Document status check failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Document status error: {e}")
        return None

def create_manual_job_for_document(doc_id, token):
    """Try to manually create a processing job for a document"""
    try:
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        # Try to trigger processing for this specific document
        response = requests.post(
            f"{API_BASE}/documents/{doc_id}/reprocess",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ Reprocessing triggered for document {doc_id}")
            return True
        else:
            print(f"⚠️  Reprocess endpoint not available: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Reprocess error: {e}")
        return False

def main():
    print("🔧 Processing Stuck Document: scan_classic_hmo.pdf")
    print("=" * 55)
    
    # Step 1: Login
    print("🔐 Logging in...")
    token = login()
    if not token:
        print("❌ Cannot proceed without login")
        return
    
    # Step 2: Find stuck documents
    print("\n📄 Looking for stuck documents...")
    stuck_docs = find_stuck_documents(token)
    
    if not stuck_docs:
        print("📄 No obviously stuck documents found")
        print("💡 This might mean the cron jobs already processed everything!")
    else:
        print(f"\n🔍 Found {len(stuck_docs)} potentially stuck documents:")
        for i, doc in enumerate(stuck_docs, 1):
            filename = doc.get('original_filename', 'Unknown')
            doc_id = doc.get('id', 'Unknown')
            status = doc.get('status', 'Unknown')
            print(f"  {i}. {filename} (ID: {doc_id}, Status: {status})")
    
    # Step 3: Manually trigger job processing
    print("\n🚀 Manually triggering job processor...")
    manually_trigger_job_processing()
    
    # Step 4: Wait and check again
    if stuck_docs:
        print("\n⏳ Waiting 15 seconds for processing...")
        time.sleep(15)
        
        print("\n📊 Checking document status after processing...")
        for doc in stuck_docs[:3]:  # Check first 3 documents
            doc_id = doc.get('id')
            if doc_id and doc_id != 'Unknown':
                print(f"\n🔍 Checking {doc.get('original_filename', 'Unknown')}...")
                status = check_document_status(doc_id)
                if status:
                    print(f"📄 Current status: {json.dumps(status, indent=2)}")
    
    # Step 5: Manual recovery attempt
    if stuck_docs:
        print(f"\n🔧 Attempting manual recovery for stuck documents...")
        for doc in stuck_docs[:2]:  # Try first 2 documents
            doc_id = doc.get('id')
            filename = doc.get('original_filename', 'Unknown')
            if doc_id and doc_id != 'Unknown':
                print(f"🔄 Trying to reprocess {filename}...")
                create_manual_job_for_document(doc_id, token)
    
    print("\n✅ Stuck document processing complete!")
    print("\n📋 Next steps:")
    print("1. Check your frontend to see if documents are now available")
    print("2. Try uploading a new document to test the pipeline")
    print("3. The cron jobs will continue processing automatically")

if __name__ == "__main__":
    main() 