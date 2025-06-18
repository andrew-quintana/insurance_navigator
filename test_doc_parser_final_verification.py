#!/usr/bin/env python3

import os
import sys
import requests
import json
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_doc_parser_with_dashboard_secret():
    """Test doc-parser after adding CUSTOM_SERVICE_ROLE_KEY to Dashboard secrets"""
    
    print("🔍 Testing doc-parser with Dashboard secret...")
    print(f"Timestamp: {datetime.now()}")
    print("-" * 60)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not anon_key:
        print("❌ Missing environment variables!")
        return False
    
    print(f"Supabase URL: {supabase_url}")
    print(f"Anon Key: {anon_key[:20]}...")
    print()
    
    # Test with a realistic document ID that should exist
    test_document_id = "1750189404"  # The vectorization test document
    
    # Prepare the request payload
    payload = {
        "document_id": test_document_id
    }
    
    headers = {
        'Authorization': f'Bearer {anon_key}',
        'Content-Type': 'application/json'
    }
    
    function_url = f"{supabase_url}/functions/v1/doc-parser"
    
    try:
        print(f"📤 Invoking doc-parser with document_id: {test_document_id}")
        print(f"URL: {function_url}")
        print()
        
        response = requests.post(
            function_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"📄 Response Data: {json.dumps(response_data, indent=2)}")
        except:
            print(f"📄 Response Text: {response.text}")
        
        print()
        
        # Check for success indicators
        if response.status_code == 200:
            print("✅ SUCCESS: Doc-parser responded with 200!")
            if 'error' not in response.text.lower():
                print("✅ No error messages detected!")
                return True
            else:
                print("⚠️  200 response but contains error messages")
        else:
            print(f"❌ FAILED: Doc-parser returned status {response.status_code}")
            if "Failed to download file" in response.text:
                print("❌ Still getting 'Failed to download file' error")
                print("   This suggests the environment variable issue persists")
            
        return False
        
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: Request timed out after 30 seconds")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def main():
    print("🔧 Final Doc-Parser Verification")
    print("=" * 60)
    print()
    
    success = test_doc_parser_with_dashboard_secret()
    
    print()
    print("=" * 60)
    if success:
        print("🎉 DOC-PARSER IS NOW WORKING!")
        print("✅ The MVP should be fully functional")
    else:
        print("❌ Doc-parser still has issues")
        print("💡 Check Supabase Dashboard logs for more details")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 

import os
import sys
import requests
import json
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_doc_parser_with_dashboard_secret():
    """Test doc-parser after adding CUSTOM_SERVICE_ROLE_KEY to Dashboard secrets"""
    
    print("🔍 Testing doc-parser with Dashboard secret...")
    print(f"Timestamp: {datetime.now()}")
    print("-" * 60)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not anon_key:
        print("❌ Missing environment variables!")
        return False
    
    print(f"Supabase URL: {supabase_url}")
    print(f"Anon Key: {anon_key[:20]}...")
    print()
    
    # Test with a realistic document ID that should exist
    test_document_id = "1750189404"  # The vectorization test document
    
    # Prepare the request payload
    payload = {
        "document_id": test_document_id
    }
    
    headers = {
        'Authorization': f'Bearer {anon_key}',
        'Content-Type': 'application/json'
    }
    
    function_url = f"{supabase_url}/functions/v1/doc-parser"
    
    try:
        print(f"📤 Invoking doc-parser with document_id: {test_document_id}")
        print(f"URL: {function_url}")
        print()
        
        response = requests.post(
            function_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"📄 Response Data: {json.dumps(response_data, indent=2)}")
        except:
            print(f"📄 Response Text: {response.text}")
        
        print()
        
        # Check for success indicators
        if response.status_code == 200:
            print("✅ SUCCESS: Doc-parser responded with 200!")
            if 'error' not in response.text.lower():
                print("✅ No error messages detected!")
                return True
            else:
                print("⚠️  200 response but contains error messages")
        else:
            print(f"❌ FAILED: Doc-parser returned status {response.status_code}")
            if "Failed to download file" in response.text:
                print("❌ Still getting 'Failed to download file' error")
                print("   This suggests the environment variable issue persists")
            
        return False
        
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: Request timed out after 30 seconds")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def main():
    print("🔧 Final Doc-Parser Verification")
    print("=" * 60)
    print()
    
    success = test_doc_parser_with_dashboard_secret()
    
    print()
    print("=" * 60)
    if success:
        print("🎉 DOC-PARSER IS NOW WORKING!")
        print("✅ The MVP should be fully functional")
    else:
        print("❌ Doc-parser still has issues")
        print("💡 Check Supabase Dashboard logs for more details")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 