#!/usr/bin/env python3
"""
Script to check and fix stuck document processing jobs.
This will:
1. Check current document and job status
2. Identify stuck jobs
3. Manually trigger job processing
4. Set up basic cron if needed
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase URL from environment
SUPABASE_URL = os.getenv('SUPABASE_URL')
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable not set")

# Configuration
API_BASE = "https://insurance-navigator-api.onrender.com"

def check_backend_health():
    """Check if backend is healthy"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is healthy")
            return True
        else:
            print(f"❌ Backend unhealthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def trigger_job_processing():
    """Manually trigger job processing"""
    try:
        service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        if not service_role_key:
            print("❌ SUPABASE_SERVICE_ROLE_KEY not found in environment")
            return False
            
        response = requests.post(
            f"{SUPABASE_URL}/functions/v1/job-processor",
            headers={
                "Authorization": f"Bearer {service_role_key}",
                "Content-Type": "application/json"
            },
            json={
                "source": "manual_trigger",
                "timestamp": datetime.now().isoformat()
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Job processing triggered: {result}")
            return True
        else:
            print(f"❌ Job processing failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Job processing error: {e}")
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

def check_recent_uploads():
    """Try to identify recent uploads that might be stuck"""
    # This would ideally query the database, but we'll use the job processor response
    print("🔍 Checking for stuck jobs...")
    trigger_job_processing()

def setup_basic_monitoring():
    """Set up basic monitoring and alerts"""
    print("📊 Setting up monitoring...")
    
    # Create a simple monitoring script
    monitoring_script = """#!/bin/bash
# Simple monitoring script for insurance navigator
echo "$(date): Checking job processing health..."

# Trigger job processing
curl -X POST "https://jhrespvvhbnloxrieycf.supabase.co/functions/v1/job-processor" \\
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"source": "monitoring", "timestamp": "'$(date -Iseconds)'"}' \\
  --max-time 30

echo ""
echo "$(date): Job processing check complete"
"""
    
    with open("scripts/monitor-jobs.sh", "w") as f:
        f.write(monitoring_script)
    
    os.chmod("scripts/monitor-jobs.sh", 0o755)
    print("✅ Created monitoring script: scripts/monitor-jobs.sh")
    print("💡 You can run this manually or set up a cron job:")
    print("   */5 * * * * /path/to/scripts/monitor-jobs.sh")

def main():
    print("🔧 Insurance Navigator Job Processor Check & Fix")
    print("=" * 50)
    
    # Step 1: Check backend health
    if not check_backend_health():
        print("❌ Cannot proceed - backend is not healthy")
        return
    
    # Step 2: Check for environment variables
    if not os.getenv('SUPABASE_SERVICE_ROLE_KEY'):
        print("⚠️  SUPABASE_SERVICE_ROLE_KEY not found")
        print("💡 Please set it for full functionality:")
        print("   export SUPABASE_SERVICE_ROLE_KEY=your_key_here")
    
    # Step 3: Trigger job processing
    print("\n🚀 Triggering job processing...")
    trigger_job_processing()
    
    # Step 4: Wait and check again
    print("\n⏳ Waiting 10 seconds for processing...")
    time.sleep(10)
    
    print("\n🔄 Triggering again to process any new jobs...")
    trigger_job_processing()
    
    # Step 5: Setup monitoring
    print("\n📊 Setting up monitoring tools...")
    setup_basic_monitoring()
    
    # Step 6: Check specific documents if provided
    if len(os.sys.argv) > 1:
        doc_id = os.sys.argv[1]
        print(f"\n🔍 Checking document {doc_id}...")
        status = check_document_status(doc_id)
        if status:
            print(f"📄 Document status: {json.dumps(status, indent=2)}")
    
    print("\n✅ Job check and fix complete!")
    print("\n📋 Next steps:")
    print("1. Check if your documents are now processing")
    print("2. Run the monitoring script periodically")
    print("3. Set up the enhanced cron jobs in Supabase (see db/scripts/document_processing/setup-cron-with-validation.sql)")

if __name__ == "__main__":
    import sys
    main() 