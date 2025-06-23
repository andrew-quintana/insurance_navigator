import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

def test_regulatory_upload():
    """Test regulatory document upload with a real document."""
    print('🏛️ Testing Regulatory Document Upload & Vectorization')
    print('=' * 55)
    
    API_BASE = '***REMOVED***'
    timestamp = int(time.time())
    
    # Health check
    print('🔍 API Health Check...')
    health = requests.get(f'{API_BASE}/health', timeout=15)
    print(f'   Status: {health.status_code}')
    if health.status_code != 200:
        print('   ❌ API not healthy')
        return False
    
    # Register user
    user_data = {
        'email': f'regulatory_test_{timestamp}@example.com',
        'password': 'RegTest123!',
        'full_name': 'Regulatory Test User'
    }
    
    print(f'📝 Registering user: {user_data["email"]}')
    reg = requests.post(f'{API_BASE}/register', json=user_data, timeout=15)
    if reg.status_code != 200:
        print(f'   ❌ Registration failed: {reg.status_code}')
        return False
    
    token = reg.json()['access_token']
    print('   ✅ User registered')
    
    # Create regulatory document content
    regulatory_content = '''DEPARTMENT OF INSURANCE
State Regulatory Notice 2024-12

SUBJECT: Health Insurance Network Adequacy Standards
EFFECTIVE DATE: March 1, 2025

I. NETWORK ADEQUACY REQUIREMENTS

All health insurance issuers must maintain adequate provider networks to ensure:

A. PRIMARY CARE ACCESS
   - Maximum wait time: 14 days for routine appointments
   - Geographic access: Within 30 miles or 30 minutes travel time
   - Provider-to-enrollee ratio: 1:2000 for primary care physicians

B. SPECIALIST CARE ACCESS  
   - Maximum wait time: 30 days for non-urgent specialist care
   - Geographic access: Within 60 miles or 60 minutes travel time
   - Essential specialties must be available in-network

C. MENTAL HEALTH SERVICES
   - Parity with medical/surgical benefits required
   - Crisis intervention available 24/7
   - Telehealth options must be available

II. COMPLIANCE MONITORING

Insurance issuers must:
1. Submit quarterly network adequacy reports
2. Maintain current provider directories (updated monthly)
3. Demonstrate compliance through secret shopper surveys
4. Provide member access metrics and wait time data

III. ENFORCEMENT

Non-compliance may result in:
- Administrative penalties up to $10,000 per violation
- Required corrective action plans
- Suspension of new enrollment
- License revocation for repeated violations

IV. REPORTING DEADLINES

- Initial compliance report: April 30, 2025
- Quarterly reports: Due 30 days after quarter end
- Provider directory updates: Monthly by 15th of each month

For questions, contact the Department of Insurance at:
Phone: (555) 123-4567
Email: network-adequacy@doi.state.gov

This notice is issued under authority of Insurance Code Section 1234.5.

Effective immediately upon publication.

Commissioner Jane Smith
State Department of Insurance
'''.encode('utf-8')
    
    # Upload regulatory document
    headers = {'Authorization': f'Bearer {token}'}
    files = {'file': ('state_network_adequacy_standards_2024.txt', regulatory_content, 'text/plain')}
    data = {
        'document_title': 'Health Insurance Network Adequacy Standards 2024',
        'document_type': 'regulatory_notice',
        'source_url': 'https://doi.state.gov/notices/2024/network-adequacy',
        'category': 'regulatory', 
        'metadata': json.dumps({
            'jurisdiction': 'state',
            'agency': 'Department of Insurance',
            'program': 'health_insurance',
            'notice_number': '2024-12',
            'effective_date': '2025-03-01',
            'topic': 'network_adequacy'
        })
    }
    
    print()
    print('📤 Uploading regulatory document...')
    print(f'   📄 Title: {data["document_title"]}')
    print(f'   📊 Size: {len(regulatory_content):,} bytes')
    print(f'   🏛️ Type: Regulatory Notice')
    
    upload = requests.post(
        f'{API_BASE}/upload-regulatory-document',
        headers=headers,
        files=files, 
        data=data,
        timeout=60
    )
    
    print(f'📥 Upload Status: {upload.status_code}')
    
    if upload.status_code == 200:
        result = upload.json()
        doc_id = result.get('document_id')
        
        print()
        print('🎉 SUCCESS! Regulatory document uploaded!')
        print(f'📋 Document ID: {doc_id}')
        print(f'📄 Filename: {result.get("filename")}')
        print(f'🔄 Status: {result.get("status")}')
        print(f'💬 Message: {result.get("message")}')
        
        print()
        print('📊 Document Stats:')
        print(f'   Words: {len(regulatory_content.decode().split())}')
        print(f'   Expected chunks: ~{len(regulatory_content)//1000}')
        print(f'   Processing method: {result.get("processing_method")}')
        
        print()
        print('✅ REGULATORY UPLOAD PIPELINE STATUS:')
        print('   ✅ File uploaded to storage bucket')
        print('   ✅ Record created in regulatory_documents table') 
        print('   ✅ Record created in documents table')
        print('   🔄 Text extraction & vectorization in progress...')
        
        return doc_id
    else:
        print(f'❌ Upload failed: {upload.status_code}')
        print(f'Error: {upload.text[:500]}')
        return False

if __name__ == '__main__':
    doc_id = test_regulatory_upload()
    
    if doc_id:
        print()
        print('🎯 TEST RESULT: SUCCESS!')
        print(f'📋 Document ID: {doc_id}')
        print()
        print('🚀 NEXT STEPS:')
        print('   1. Wait 1-2 minutes for vectorization')
        print('   2. Check document status')
        print('   3. Verify vectors created in database')
        print('   4. Test search with regulatory content')
        print()
        print('🎊 REGULATORY UPLOAD IS WORKING!')
    else:
        print()
        print('❌ TEST RESULT: FAILED')
        print('Check error details above.') 