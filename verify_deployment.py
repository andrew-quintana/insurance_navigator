#!/usr/bin/env python3
"""
Edge Functions Deployment Verification Script
Tests all deployed functions to ensure they're working
"""

import requests
import json
from datetime import datetime

def main():
    project_ref = 'jhrespvvhbnloxrieycf'
    functions = [
        'doc-processor', 
        'vector-processor', 
        'upload-handler', 
        'progress-tracker', 
        'link-assigner', 
        'job-processor', 
        'processing-webhook', 
        'doc-parser'
    ]

    print('🧪 Testing all deployed Edge Functions...')
    print('=' * 50)

    results = []
    for func in functions:
        url = f'https://{project_ref}.supabase.co/functions/v1/{func}'
        try:
            response = requests.get(url, timeout=10)
            # Any response means the function is deployed (200, 400, 401, 405 are all valid)
            status = '✅ Deployed' if response.status_code in [200, 400, 401, 405] else f'❌ Status {response.status_code}'
            results.append({'function': func, 'status': status, 'code': response.status_code})
            print(f'{status:<12} {func}')
        except Exception as e:
            results.append({'function': func, 'status': '❌ Error', 'error': str(e)})
            print(f'❌ Error      {func}: {e}')

    print()
    deployed_count = len([r for r in results if '✅' in r['status']])
    print(f'📊 Summary: {deployed_count}/{len(functions)} functions deployed successfully')

    # Save results
    with open('edge_functions_verification.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_functions': len(functions),
            'deployed_successfully': deployed_count,
            'deployment_method': 'Supabase CLI --use-api (Docker-free)',
            'results': results
        }, f, indent=2)

    print('📋 Results saved to edge_functions_verification.json')
    
    if deployed_count == len(functions):
        print('🎉 All Edge Functions deployed successfully!')
        return True
    else:
        print('⚠️ Some functions may need attention')
        return False

if __name__ == "__main__":
    main() 