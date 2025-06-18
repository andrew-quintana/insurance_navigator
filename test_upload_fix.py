#!/usr/bin/env python3
"""
Fixed Upload Test for Insurance Navigator
========================================
Correctly formats requests to match upload-handler expectations.
"""

import asyncio
import asyncpg
import aiohttp
import json
import tempfile
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

async def test_corrected_upload():
    """Test upload with correctly formatted JSON data"""
    print("🔧 Testing Corrected Upload Flow")
    print("=" * 50)
    
    # Environment setup
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    database_url = os.getenv('DATABASE_URL')
    
    if not all([supabase_url, service_role_key, database_url]):
        print("❌ Missing required environment variables")
        return
    
    test_user_id = str(uuid.uuid4())  # Generate proper UUID
    print(f"🆔 Test User ID: {test_user_id}")
    
    # Connect to database
    conn = await asyncpg.connect(database_url, statement_cache_size=0, server_settings={'jit': 'off'})
    
    try:
        # Step 1: Create test file content
        test_content = f"""
        Test Document for Fixed Upload
        ==============================
        
        Generated: {datetime.now().isoformat()}
        Test User: {test_user_id}
        
        This document tests the corrected upload flow with proper JSON formatting.
        
        Insurance Policy Information:
        - Policy Number: FIXED-TEST-{uuid.uuid4().hex[:8]}
        - Policy Type: Health Insurance
        - Coverage: Comprehensive Medical
        - Effective Date: 2024-01-01
        - Deductible: $1,000
        - Max Out-of-Pocket: $5,000
        
        Coverage Details:
        - Doctor Visits: $25 copay
        - Specialists: $50 copay  
        - Emergency Room: $200 copay
        - Prescription Drugs: Tier 1: $10, Tier 2: $25, Tier 3: $50
        
        This document should be successfully processed through the complete pipeline.
        """.strip()
        
        filename = f"fixed_upload_test_{uuid.uuid4().hex[:8]}.txt"
        file_size = len(test_content.encode('utf-8'))
        
        print(f"📄 Test file: {filename}")
        print(f"📏 File size: {file_size} bytes")
        
        # Step 2: Format upload request as JSON (not form data)
        upload_request = {
            "filename": filename,
            "contentType": "text/plain",
            "fileSize": file_size
        }
        
        print(f"📤 Upload request: {json.dumps(upload_request, indent=2)}")
        
        # Step 3: Send upload request
        upload_url = f"{supabase_url}/functions/v1/upload-handler"
        headers = {
            'Authorization': f'Bearer {service_role_key}',
            'X-User-ID': test_user_id,
            'Content-Type': 'application/json',  # Critical: JSON content type
            'apikey': service_role_key
        }
        
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            print("📞 Sending upload request...")
            
            async with session.post(upload_url, json=upload_request, headers=headers) as response:
                status = response.status
                response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                print(f"📋 Upload Response:")
                print(f"   Status: {status}")
                print(f"   Data: {json.dumps(response_data, indent=2) if isinstance(response_data, dict) else response_data}")
                
                if status == 200 and isinstance(response_data, dict) and 'documentId' in response_data:
                    document_id = response_data['documentId']
                    print(f"✅ Upload successful! Document ID: {document_id}")
                    
                    # Step 4: Upload actual file content to storage
                    storage_path = response_data.get('uploadPath') or f"documents/{test_user_id}/{filename}"
                    
                    print(f"📂 Uploading file content to: {storage_path}")
                    
                    # Upload to Supabase Storage
                    storage_url = f"{supabase_url}/storage/v1/object/documents/{storage_path}"
                    storage_headers = {
                        'Authorization': f'Bearer {service_role_key}',
                        'Content-Type': 'text/plain',
                        'apikey': service_role_key
                    }
                    
                    async with session.post(storage_url, data=test_content.encode(), headers=storage_headers) as storage_response:
                        storage_status = storage_response.status
                        print(f"📦 Storage upload status: {storage_status}")
                        
                        if storage_status in [200, 201]:
                            print("✅ File content uploaded to storage")
                            
                            # Step 5: Update document record to trigger processing
                            await conn.execute("""
                                UPDATE documents 
                                SET status = 'pending', storage_path = $1, updated_at = NOW()
                                WHERE id = $2
                            """, storage_path, document_id)
                            
                            print("✅ Document record updated")
                            
                            # Step 6: Monitor processing
                            await monitor_document_processing(conn, document_id)
                            
                        else:
                            storage_error = await storage_response.text()
                            print(f"❌ Storage upload failed: {storage_error}")
                    
                else:
                    print(f"❌ Upload failed: {response_data}")
                    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await conn.close()

async def monitor_document_processing(conn, document_id):
    """Monitor document processing progress"""
    print(f"\n👀 Monitoring document {document_id} processing...")
    
    max_checks = 12  # 2 minutes max wait
    check_interval = 10  # 10 seconds between checks
    
    for check in range(max_checks):
        # Check document status
        doc_info = await conn.fetchrow("""
            SELECT id, status, progress_percentage, extracted_text, error_message, updated_at
            FROM documents 
            WHERE id = $1
        """, document_id)
        
        if doc_info:
            status = doc_info['status']
            progress = doc_info['progress_percentage']
            
            print(f"📊 Check {check + 1}/{max_checks}: Status = {status}, Progress = {progress}%")
            
            if status == 'completed':
                print("🎉 Processing completed successfully!")
                
                if doc_info['extracted_text']:
                    text_length = len(doc_info['extracted_text'])
                    print(f"📝 Extracted text length: {text_length} characters")
                    
                    # Show first 200 characters
                    preview = doc_info['extracted_text'][:200]
                    print(f"📖 Text preview: {preview}...")
                
                break
                
            elif status == 'failed':
                print(f"💥 Processing failed!")
                if doc_info['error_message']:
                    print(f"❌ Error: {doc_info['error_message']}")
                break
                
            elif status in ['parsing', 'processing']:
                print(f"⚙️ Processing in progress...")
                
        else:
            print(f"❌ Document not found")
            break
            
        # Wait before next check
        if check < max_checks - 1:
            await asyncio.sleep(check_interval)
    
    else:
        print(f"⏰ Monitoring timeout - processing may still be ongoing")

async def test_agent_integration():
    """Test agent integration with processed document"""
    print(f"\n🤖 Testing Agent Integration")
    print("-" * 30)
    
    try:
        # Test importing and using agents
        import sys
        from pathlib import Path
        project_root = Path.cwd()
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # Import agents
        from agents.patient_navigator.patient_navigator import PatientNavigatorAgent
        from agents.chat_communicator.chat_communicator import ChatCommunicatorAgent
        
        print("✅ Agent imports successful")
        
        # Create test agents (check their actual init signatures)
        try:
            navigator = PatientNavigatorAgent()
            print("✅ PatientNavigatorAgent created")
        except Exception as e:
            print(f"⚠️ PatientNavigatorAgent creation failed: {e}")
            navigator = None
        
        try:
            chat_agent = ChatCommunicatorAgent()
            print("✅ ChatCommunicatorAgent created")
        except Exception as e:
            print(f"⚠️ ChatCommunicatorAgent creation failed: {e}")
            chat_agent = None
        
        # Test basic agent functionality
        if navigator:
            test_query = "I need help understanding my health insurance deductible"
            test_user = str(uuid.uuid4())
            test_session = str(uuid.uuid4())
            
            try:
                result = navigator.process(test_query, test_user, test_session)
                print(f"✅ Navigator processing successful: {type(result)}")
                print(f"📝 Result preview: {str(result)[:100]}...")
            except Exception as e:
                print(f"⚠️ Navigator processing failed: {e}")
        
        print("🎉 Agent integration testing completed")
        
    except Exception as e:
        print(f"❌ Agent integration test failed: {e}")

async def main():
    """Run the complete fixed upload test"""
    print("🚀 Starting Fixed Upload End-to-End Test")
    print("=" * 60)
    
    # Test 1: Fixed upload flow
    await test_corrected_upload()
    
    # Test 2: Agent integration
    await test_agent_integration()
    
    print("\n✅ Fixed upload test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 