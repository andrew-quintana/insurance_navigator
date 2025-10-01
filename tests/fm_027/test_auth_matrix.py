#!/usr/bin/env python3
"""
FM-027: Auth Matrix Test Harness
Test authentication matrix across different contexts to identify worker storage access issue
"""

import asyncio
import httpx
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load staging environment
load_dotenv('.env.staging')

async def test_auth_matrix():
    """Test authentication matrix across different contexts"""
    
    print("🔧 FM-027: Auth Matrix Test Harness")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print()
    
    # Test file from worker logs
    file_path = "user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/fd5b5f12_5e4390c2.pdf"
    base_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    anon_key = os.getenv("SUPABASE_ANON_KEY")
    
    print(f"Base URL: {base_url}")
    print(f"Service Role Key Present: {bool(service_role_key and len(service_role_key) > 10)}")
    print(f"Anon Key Present: {bool(anon_key and len(anon_key) > 10)}")
    print()
    
    # Test contexts
    contexts = [
        {
            "name": "Direct Test (Service Role)",
            "headers": {
                "Authorization": f"Bearer {service_role_key}",
                "apikey": service_role_key
            }
        },
        {
            "name": "Worker Simulation (Service Role)",
            "headers": {
                "Authorization": f"Bearer {service_role_key}",
                "apikey": service_role_key
            }
        },
        {
            "name": "Anon Key Test",
            "headers": {
                "Authorization": f"Bearer {anon_key}",
                "apikey": anon_key
            }
        }
    ]
    
    # Test paths (old vs new endpoint format)
    paths = [
        {
            "name": "New Format (Fixed)",
            "url": f"{base_url}/storage/v1/object/files/{file_path}"
        },
        {
            "name": "Old Format (Broken)",
            "url": f"{base_url}/object/files/{file_path}"
        }
    ]
    
    results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for context in contexts:
            print(f"Testing Context: {context['name']}")
            print("-" * 40)
            
            for path in paths:
                try:
                    print(f"  {path['name']}: {path['url']}")
                    
                    response = await client.head(path['url'], headers=context['headers'])
                    
                    result = {
                        "context": context['name'],
                        "path": path['name'],
                        "url": path['url'],
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "success": response.status_code == 200
                    }
                    
                    if response.status_code == 200:
                        print(f"    ✅ Status: {response.status_code} - SUCCESS")
                    else:
                        print(f"    ❌ Status: {response.status_code} - FAILED")
                        try:
                            error_text = response.text
                            print(f"    Error: {error_text[:100]}...")
                        except:
                            print(f"    Error: [Could not read response text]")
                    
                    results.append(result)
                    
                except Exception as e:
                    print(f"    💥 Exception: {str(e)}")
                    results.append({
                        "context": context['name'],
                        "path": path['name'],
                        "url": path['url'],
                        "status_code": None,
                        "headers": {},
                        "success": False,
                        "error": str(e)
                    })
            
            print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    successful_tests = [r for r in results if r.get('success', False)]
    failed_tests = [r for r in results if not r.get('success', False)]
    
    print(f"Total Tests: {len(results)}")
    print(f"Successful: {len(successful_tests)}")
    print(f"Failed: {len(failed_tests)}")
    print()
    
    if successful_tests:
        print("✅ SUCCESSFUL TESTS:")
        for result in successful_tests:
            print(f"  - {result['context']} + {result['path']} = {result['status_code']}")
        print()
    
    if failed_tests:
        print("❌ FAILED TESTS:")
        for result in failed_tests:
            status = result.get('status_code', 'EXCEPTION')
            error = result.get('error', '')
            print(f"  - {result['context']} + {result['path']} = {status}")
            if error:
                print(f"    Error: {error}")
        print()
    
    # Analysis
    print("ANALYSIS")
    print("-" * 20)
    
    # Check if new format works with service role
    service_role_new = [r for r in results if 'Service Role' in r['context'] and 'New Format' in r['path']]
    if service_role_new:
        if service_role_new[0]['success']:
            print("✅ Service Role + New Format = SUCCESS (Expected)")
        else:
            print("❌ Service Role + New Format = FAILED (Unexpected - this should work)")
    
    # Check if old format fails with service role
    service_role_old = [r for r in results if 'Service Role' in r['context'] and 'Old Format' in r['path']]
    if service_role_old:
        if not service_role_old[0]['success']:
            print("✅ Service Role + Old Format = FAILED (Expected - endpoint fixed)")
        else:
            print("❌ Service Role + Old Format = SUCCESS (Unexpected - should fail)")
    
    # Check for differences between contexts
    direct_tests = [r for r in results if 'Direct Test' in r['context']]
    worker_tests = [r for r in results if 'Worker Simulation' in r['context']]
    
    if direct_tests and worker_tests:
        print(f"\nDirect vs Worker Comparison:")
        for i, (direct, worker) in enumerate(zip(direct_tests, worker_tests)):
            if direct['success'] != worker['success']:
                print(f"  ⚠️  Mismatch in test {i+1}: Direct={direct['success']}, Worker={worker['success']}")
            else:
                print(f"  ✅ Match in test {i+1}: Both={direct['success']}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"artifacts/fm_027/{timestamp}/auth_matrix_results.json"
    
    # Create artifacts directory
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "environment": os.getenv('ENVIRONMENT', 'development'),
            "base_url": base_url,
            "file_path": file_path,
            "results": results,
            "summary": {
                "total_tests": len(results),
                "successful": len(successful_tests),
                "failed": len(failed_tests)
            }
        }, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_auth_matrix())
