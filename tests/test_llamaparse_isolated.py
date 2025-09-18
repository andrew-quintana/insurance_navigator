#!/usr/bin/env python3
"""
Isolated LlamaParse testing to understand the correct API interface.
This will test the actual LlamaParse API with our PDF file and get the exact workflow working.
"""

import asyncio
import httpx
import json
import os
import time
from dotenv import load_dotenv

async def test_llamaparse_complete_workflow():
    """Test the complete LlamaParse workflow from upload to result retrieval"""
    load_dotenv('.env.development')
    
    api_key = os.getenv('LLAMACLOUD_API_KEY')
    base_url = 'https://api.cloud.llamaindex.ai'
    
    print("🚀 Starting LlamaParse Isolated Test")
    print("=" * 50)
    print(f"API Key: {api_key[:20]}...")
    print(f"Base URL: {base_url}")
    
    # Test file path
    pdf_path = 'examples/simulated_insurance_document.pdf'
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print(f"📄 Testing with file: {pdf_path}")
    print(f"📏 File size: {os.path.getsize(pdf_path)} bytes")
    
    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Upload document for parsing
            print("\n📤 STEP 1: Uploading document to LlamaParse")
            print("-" * 30)
            
            with open(pdf_path, 'rb') as f:
                files = {'file': ('simulated_insurance_document.pdf', f, 'application/pdf')}
                data = {
                    'parsing_instruction': 'Parse this insurance document and extract all text content accurately',
                    'result_type': 'text'
                }
                
                headers = {'Authorization': f'Bearer {api_key}'}
                
                upload_response = await client.post(
                    f'{base_url}/api/parsing/upload',
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=30
                )
                
                print(f"Upload Status: {upload_response.status_code}")
                print(f"Upload Response: {upload_response.text}")
                
                if upload_response.status_code != 200:
                    print(f"❌ Upload failed: {upload_response.status_code} - {upload_response.text}")
                    return
                
                upload_result = upload_response.json()
                job_id = upload_result.get('id')
                status = upload_result.get('status')
                
                print(f"✅ Upload successful!")
                print(f"   Job ID: {job_id}")
                print(f"   Status: {status}")
            
            # Step 2: Poll for completion
            print(f"\n⏳ STEP 2: Polling for job completion")
            print("-" * 30)
            
            max_wait = 300  # 5 minutes
            poll_interval = 2  # 2 seconds
            start_time = time.time()
            
            while (time.time() - start_time) < max_wait:
                status_response = await client.get(
                    f'{base_url}/api/parsing/job/{job_id}',
                    headers={'Authorization': f'Bearer {api_key}'},
                    timeout=30
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    current_status = status_data.get('status', '').upper()
                    
                    print(f"   Status check: {current_status}")
                    
                    if current_status == 'SUCCESS':
                        print("✅ Job completed successfully!")
                        break
                    elif current_status in ['FAILED', 'ERROR']:
                        print(f"❌ Job failed with status: {current_status}")
                        return
                    else:
                        print(f"   Still processing... waiting {poll_interval} seconds")
                        await asyncio.sleep(poll_interval)
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    return
            else:
                print(f"❌ Job timed out after {max_wait} seconds")
                return
            
            # Step 3: Get the parsed result
            print(f"\n📄 STEP 3: Retrieving parsed content")
            print("-" * 30)
            
            result_response = await client.get(
                f'{base_url}/api/parsing/job/{job_id}/result/text',
                headers={'Authorization': f'Bearer {api_key}'},
                timeout=30
            )
            
            if result_response.status_code == 200:
                result_data = result_response.text
                
                print(f"✅ Result retrieved successfully!")
                print(f"   Content length: {len(result_data)} characters")
                
                # Parse the JSON response to extract the text
                try:
                    parsed_json = json.loads(result_data)
                    parsed_text = parsed_json.get('text', '')
                    
                    if parsed_text:
                        print(f"   Parsed text length: {len(parsed_text)} characters")
                        print(f"\n📋 PARSED CONTENT:")
                        print("=" * 50)
                        print(parsed_text)
                        print("=" * 50)
                        
                        # Save to file for comparison
                        output_file = 'llamaparse_test_output.md'
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(parsed_text)
                        print(f"\n💾 Parsed content saved to: {output_file}")
                        
                        # Compare with expected content
                        print(f"\n🔍 CONTENT VERIFICATION:")
                        print("-" * 30)
                        
                        expected_keywords = [
                            'Introduction',
                            'Accessa Health Insurance',
                            'Eligibility',
                            'Coverage Details',
                            'In-Network Services',
                            'Out-of-Network Services', 
                            'Prescription Drugs',
                            'Claims and Reimbursement',
                            'Contact Information',
                            '1-800-555-1234',
                            'support@accessa.org'
                        ]
                        
                        found_keywords = []
                        for keyword in expected_keywords:
                            if keyword in parsed_text:
                                found_keywords.append(keyword)
                                print(f"   ✅ Found: {keyword}")
                            else:
                                print(f"   ❌ Missing: {keyword}")
                        
                        coverage_ratio = len(found_keywords) / len(expected_keywords)
                        print(f"\n📊 Content Coverage: {coverage_ratio:.1%} ({len(found_keywords)}/{len(expected_keywords)})")
                        
                        if coverage_ratio >= 0.8:
                            print("🎉 PARSING SUCCESS! Content matches expected structure.")
                            return parsed_text
                        else:
                            print("⚠️  Parsing incomplete - some content may be missing.")
                            return parsed_text
                    else:
                        print("❌ No text content found in response")
                        return None
                        
                except json.JSONDecodeError:
                    print("❌ Failed to parse JSON response")
                    print(f"Raw response: {result_data[:500]}...")
                    return None
            else:
                print(f"❌ Failed to get result: {result_response.status_code} - {result_response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()
            return None

async def test_storage_integration():
    """Test integration with Supabase storage - download file and parse it"""
    load_dotenv('.env.development')
    
    print(f"\n🔄 STEP 4: Testing Storage Integration")
    print("-" * 30)
    
    # Test downloading from storage (like our real implementation)
    storage_path = 'files/user/115d11d4-da35-4487-93e2-255111c3603b/raw/a10c575c_70939511.pdf'
    service_role_key = '***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU'
    
    try:
        async with httpx.AsyncClient() as client:
            # Download file from storage
            bucket = 'files'
            key = storage_path[6:]  # Remove 'files/' prefix
            storage_url = f"http://127.0.0.1:54321/storage/v1/object/{bucket}/{key}"
            
            print(f"   Downloading from: {storage_url}")
            
            response = await client.get(
                storage_url,
                headers={'Authorization': f'Bearer {service_role_key}'}
            )
            
            if response.status_code == 200:
                file_content = response.content
                print(f"✅ Downloaded file: {len(file_content)} bytes")
                
                # Now parse this downloaded content with LlamaParse
                api_key = os.getenv('LLAMACLOUD_API_KEY')
                base_url = 'https://api.cloud.llamaindex.ai'
                
                filename = storage_path.split('/')[-1]
                files = {'file': (filename, file_content, 'application/pdf')}
                data = {
                    'parsing_instruction': 'Parse this insurance document and extract all text content accurately',
                    'result_type': 'text'
                }
                
                headers = {'Authorization': f'Bearer {api_key}'}
                
                print(f"   Uploading downloaded file to LlamaParse...")
                
                upload_response = await client.post(
                    f'{base_url}/api/parsing/upload',
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=30
                )
                
                if upload_response.status_code == 200:
                    upload_result = upload_response.json()
                    job_id = upload_result.get('id')
                    print(f"✅ Storage integration test successful! Job ID: {job_id}")
                    return True
                else:
                    print(f"❌ Upload failed: {upload_response.status_code}")
                    return False
            else:
                print(f"❌ Download failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Storage integration error: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 LlamaParse Isolated Testing")
    print("=" * 50)
    
    # Test 1: Complete workflow with local file
    parsed_content = await test_llamaparse_complete_workflow()
    
    if parsed_content:
        print(f"\n✅ LOCAL FILE TEST PASSED")
        
        # Test 2: Storage integration
        storage_success = await test_storage_integration()
        
        if storage_success:
            print(f"\n✅ STORAGE INTEGRATION TEST PASSED")
            print(f"\n🎉 ALL TESTS SUCCESSFUL!")
            print(f"\nNext steps:")
            print(f"1. Update RealLlamaParseService with this working implementation")
            print(f"2. Ensure proper error handling and timeouts")
            print(f"3. Test with enhanced worker integration")
        else:
            print(f"\n❌ STORAGE INTEGRATION TEST FAILED")
    else:
        print(f"\n❌ LOCAL FILE TEST FAILED")

if __name__ == "__main__":
    asyncio.run(main())


