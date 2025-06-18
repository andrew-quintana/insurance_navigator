#!/usr/bin/env python3
"""
Debug 500 Errors in Edge Functions
Since API keys are configured, investigate the actual runtime errors
"""

import requests
import json
from datetime import datetime

def test_function_with_payload(function_name: str, payload: dict):
    """Test a function with a given payload and return detailed error info"""
    
    url = f'https://jhrespvvhbnloxrieycf.supabase.co/functions/v1/{function_name}'
    
    print(f"\n🧪 Testing {function_name}")
    print("-" * 40)
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.text:
            try:
                json_response = response.json()
                print(f"JSON Response: {json.dumps(json_response, indent=2)}")
            except:
                print(f"Raw Response: {response.text}")
        else:
            print("Empty response body")
            
        return {
            'function': function_name,
            'status': response.status_code,
            'response': response.text,
            'success': response.status_code < 400
        }
        
    except Exception as e:
        print(f"Request Error: {e}")
        return {
            'function': function_name,
            'status': 'error',
            'error': str(e),
            'success': False
        }

def main():
    print("🔍 Debugging 500 Errors in Edge Functions")
    print("=" * 50)
    print(f"Timestamp: {datetime.now()}")
    print(f"All API keys are configured, investigating runtime errors...")
    
    results = []
    
    # Test vector-processor with minimal payload
    results.append(test_function_with_payload('vector-processor', {
        'test': 'minimal'
    }))
    
    # Test doc-parser with minimal payload  
    results.append(test_function_with_payload('doc-parser', {
        'test': 'minimal'
    }))
    
    # Test vector-processor with realistic payload
    results.append(test_function_with_payload('vector-processor', {
        'documentId': 'test-id',
        'extractedText': 'This is test text for processing',
        'documentType': 'user'
    }))
    
    # Test doc-parser with realistic payload
    results.append(test_function_with_payload('doc-parser', {
        'documentId': 'test-document-id'
    }))
    
    # Summary
    print(f"\n📊 Summary")
    print("=" * 20)
    
    for result in results:
        status = "✅ Working" if result['success'] else f"❌ Error ({result['status']})"
        print(f"{result['function']:<20} {status}")
    
    # Save detailed results
    with open('edge_function_debug_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': 'API keys are configured, investigating runtime errors',
            'results': results
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to edge_function_debug_results.json")

if __name__ == "__main__":
    main() 