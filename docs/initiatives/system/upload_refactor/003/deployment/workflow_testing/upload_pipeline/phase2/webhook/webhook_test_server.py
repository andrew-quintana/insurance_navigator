#!/usr/bin/env python3
"""
Webhook Test Server
Local webhook server to receive LlamaParse callbacks and update database
"""

import asyncio
import json
import time
import uuid
import hashlib
import httpx
import asyncpg
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

load_dotenv('.env.production')

# Test configuration
RUN_ID = f"webhook_test_{int(time.time())}"
TEST_USER_ID = "766e8693-7fd5-465e-9ee4-4a9b3a696480"

# API Configuration
API_CONFIG = {
    "SUPABASE_URL": os.getenv("SUPABASE_URL"),
    "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY"),
    "DATABASE_URL": os.getenv("DATABASE_URL"),
    "LLAMAPARSE_API_KEY": os.getenv("LLAMAPARSE_API_KEY"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "LLAMAPARSE_BASE_URL": "https://api.cloud.llamaindex.ai",
    "OPENAI_API_URL": "https://api.openai.com/v1"
}

# FastAPI app for webhook
app = FastAPI(title="LlamaParse Webhook Server", version="1.0.0")

class WebhookTestServer:
    def __init__(self):
        self.db_connection = None
        self.test_results = {
            "run_id": RUN_ID,
            "start_time": datetime.now().isoformat(),
            "webhook_calls": [],
            "database_updates": [],
            "summary": {}
        }
        
    async def connect_to_database(self):
        """Connect to production Supabase database"""
        try:
            self.db_connection = await asyncpg.connect(API_CONFIG["DATABASE_URL"])
            print("✅ Connected to production Supabase database")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    async def generate_signed_url(self, job_id: str, filename: str) -> str:
        """Generate signed URL for LlamaParse to upload parsed document"""
        try:
            # Generate storage path for parsed document
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            parsed_filename = f"parsed_{timestamp}_{filename}"
            storage_path = f"files/{TEST_USER_ID}/parsed/{parsed_filename}"
            
            # Create signed URL using Supabase Storage API
            headers = {
                "Authorization": f"Bearer {API_CONFIG['SUPABASE_SERVICE_ROLE_KEY']}",
                "Content-Type": "application/json"
            }
            
            # Request signed URL for upload
            signed_url_data = {
                "path": storage_path,
                "expiresIn": 3600  # 1 hour
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_CONFIG['SUPABASE_URL']}/storage/v1/object/sign/{storage_path}",
                    headers=headers,
                    json=signed_url_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    signed_url = result.get('signedURL')
                    print(f"✅ Generated signed URL: {signed_url}")
                    return signed_url
                else:
                    print(f"❌ Failed to generate signed URL: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error generating signed URL: {e}")
            return None
    
    async def update_job_status(self, job_id: str, status: str, progress: str = "1.0") -> bool:
        """Update job status in database"""
        try:
            query = """
                UPDATE upload_pipeline.upload_jobs 
                SET status = $1, progress = $2, updated_at = $3
                WHERE job_id = $4
            """
            
            await self.db_connection.execute(
                query,
                status,
                progress,
                datetime.now(),
                job_id
            )
            
            print(f"✅ Updated job {job_id} status to {status}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update job status: {e}")
            return False
    
    async def create_webhook_job(self, filename: str) -> Dict[str, Any]:
        """Create a test job for webhook processing"""
        try:
            # Create document record
            document_id = str(uuid.uuid4())
            job_id = str(uuid.uuid4())
            
            # Generate unique file hash
            unique_content = f"{filename}_{RUN_ID}".encode()
            file_hash = hashlib.sha256(unique_content).hexdigest()
            
            # Insert document
            doc_query = """
                INSERT INTO upload_pipeline.documents 
                (document_id, filename, file_sha256, bytes_len, mime, processing_status, raw_path, user_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """
            
            await self.db_connection.execute(
                doc_query,
                document_id,
                filename,
                file_hash,
                1000,  # Mock file size
                'application/pdf',
                'uploaded',
                f"files/{TEST_USER_ID}/raw/{filename}",
                TEST_USER_ID,
                datetime.now(),
                datetime.now()
            )
            
            # Insert job
            job_query = """
                INSERT INTO upload_pipeline.upload_jobs 
                (job_id, document_id, state, status, progress, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """
            
            await self.db_connection.execute(
                job_query,
                job_id,
                document_id,
                'queued',
                'parse_queued',
                '0.0',
                datetime.now(),
                datetime.now()
            )
            
            print(f"✅ Created webhook test job: {job_id}")
            return {
                "success": True,
                "job_id": job_id,
                "document_id": document_id,
                "filename": filename
            }
            
        except Exception as e:
            print(f"❌ Failed to create webhook job: {e}")
            return {"success": False, "error": str(e)}

# Global server instance
webhook_server = WebhookTestServer()

@app.post("/webhook/llamaparse")
async def llamaparse_webhook(request: Request):
    """Handle LlamaParse webhook callbacks"""
    try:
        # Ensure database connection
        if not webhook_server.db_connection:
            await webhook_server.connect_to_database()
        
        # Get webhook payload
        payload = await request.json()
        
        print(f"📥 Received LlamaParse webhook: {payload}")
        
        # Store webhook call
        webhook_call = {
            "timestamp": datetime.now().isoformat(),
            "payload": payload,
            "headers": dict(request.headers)
        }
        webhook_server.test_results["webhook_calls"].append(webhook_call)
        
        # Extract job information
        job_id = payload.get("job_id") or payload.get("id")
        status = payload.get("status", "unknown")
        
        if not job_id:
            raise HTTPException(status_code=400, detail="Missing job_id in webhook payload")
        
        # Update job status based on webhook
        if status in ["completed", "success", "done"]:
            # Update to parsed status
            success = await webhook_server.update_job_status(job_id, "parsed", "1.0")
            
            if success:
                webhook_server.test_results["database_updates"].append({
                    "timestamp": datetime.now().isoformat(),
                    "job_id": job_id,
                    "status": "parsed",
                    "success": True
                })
                
                return JSONResponse(
                    status_code=200,
                    content={"status": "success", "message": "Job status updated to parsed"}
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={"status": "error", "message": "Failed to update job status"}
                )
        else:
            # Handle other statuses
            success = await webhook_server.update_job_status(job_id, status, "0.5")
            
            return JSONResponse(
                status_code=200,
                content={"status": "success", "message": f"Job status updated to {status}"}
            )
            
    except Exception as e:
        print(f"❌ Webhook processing error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/webhook/status")
async def webhook_status():
    """Get webhook server status"""
    return {
        "status": "running",
        "run_id": RUN_ID,
        "webhook_calls": len(webhook_server.test_results["webhook_calls"]),
        "database_updates": len(webhook_server.test_results["database_updates"])
    }

@app.get("/webhook/test")
async def create_test_job():
    """Create a test job for webhook testing"""
    if not webhook_server.db_connection:
        await webhook_server.connect_to_database()
    
    filename = f"webhook_test_{RUN_ID}.pdf"
    result = await webhook_server.create_webhook_job(filename)
    
    return result

async def test_webhook_integration():
    """Test complete webhook integration"""
    print("🚀 Starting Webhook Integration Test")
    print(f"📋 Run ID: {RUN_ID}")
    print(f"🌐 Webhook URL: http://localhost:8001/webhook/llamaparse")
    
    # Connect to database
    if not await webhook_server.connect_to_database():
        return False
    
    # Create test job
    print("\n📄 Creating test job...")
    job_result = await webhook_server.create_webhook_job(f"webhook_test_{RUN_ID}.pdf")
    
    if not job_result["success"]:
        print(f"❌ Failed to create test job: {job_result.get('error')}")
        return False
    
    job_id = job_result["job_id"]
    print(f"✅ Test job created: {job_id}")
    
    # Simulate webhook call
    print("\n📥 Simulating webhook call...")
    webhook_payload = {
        "job_id": job_id,
        "status": "completed",
        "result_url": "https://example.com/parsed_document.md",
        "timestamp": datetime.now().isoformat()
    }
    
    # Send webhook to our server
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/webhook/llamaparse",
            json=webhook_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Webhook processed successfully: {response.json()}")
        else:
            print(f"❌ Webhook processing failed: {response.status_code} - {response.text}")
            return False
    
    # Verify database update
    print("\n🔍 Verifying database update...")
    query = """
        SELECT job_id, status, progress, updated_at
        FROM upload_pipeline.upload_jobs 
        WHERE job_id = $1
    """
    
    result = await webhook_server.db_connection.fetchrow(query, job_id)
    
    if result and result['status'] == 'parsed':
        print(f"✅ Database updated successfully: {dict(result)}")
        return True
    else:
        print(f"❌ Database update failed: {result}")
        return False

async def cleanup_test_data():
    """Clean up test data"""
    print(f"🧹 Cleaning up test data with RUN_ID: {RUN_ID}...")
    
    try:
        if webhook_server.db_connection:
            # Delete in reverse dependency order
            await webhook_server.db_connection.execute(
                "DELETE FROM upload_pipeline.document_chunks WHERE text LIKE $1",
                f"%{RUN_ID}%"
            )
            await webhook_server.db_connection.execute(
                "DELETE FROM upload_pipeline.upload_jobs WHERE job_id::text LIKE $1",
                f"%{RUN_ID}%"
            )
            await webhook_server.db_connection.execute(
                "DELETE FROM upload_pipeline.documents WHERE filename LIKE $1",
                f"%{RUN_ID}%"
            )
            
            print(f"✅ Test data cleanup complete")
            return True
            
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run webhook integration test
        async def run_test():
            success = await test_webhook_integration()
            await cleanup_test_data()
            if webhook_server.db_connection:
                await webhook_server.db_connection.close()
            return success
        
        result = asyncio.run(run_test())
        print(f"\n📊 Webhook Integration Test: {'✅ SUCCESS' if result else '❌ FAILED'}")
    else:
        # Start webhook server
        print("🚀 Starting LlamaParse Webhook Server")
        print(f"📋 Run ID: {RUN_ID}")
        print(f"🌐 Webhook URL: http://localhost:8001/webhook/llamaparse")
        print(f"📊 Status URL: http://localhost:8001/webhook/status")
        print(f"🧪 Test URL: http://localhost:8001/webhook/test")
        
        uvicorn.run(app, host="0.0.0.0", port=8001)
