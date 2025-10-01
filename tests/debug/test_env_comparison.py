#!/usr/bin/env python3
"""
Test script to compare environment variables between local and Render.
"""

import os
from dotenv import load_dotenv

def test_env_comparison():
    """Compare environment variables between local and Render"""
    load_dotenv('.env.staging')
    
    print("🔬 Environment Variables Comparison")
    print("=" * 60)
    
    # Check the environment variables that are used in StorageManager
    env_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY", 
        "SUPABASE_SERVICE_ROLE_KEY"
    ]
    
    print("Local Environment Variables:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"  {var}: {value[:50]}..." if len(value) > 50 else f"  {var}: {value}")
            print(f"    Length: {len(value)}")
        else:
            print(f"  {var}: NOT SET")
        print()
    
    # Check if there are any differences in the values
    print("Environment Variable Analysis:")
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if supabase_url:
        print(f"  SUPABASE_URL: {supabase_url}")
        if "dfgzeastcxnoqshgyotp" in supabase_url:
            print("    ✅ Contains expected project reference")
        else:
            print("    ❌ Unexpected project reference")
    
    if service_role_key:
        print(f"  SUPABASE_SERVICE_ROLE_KEY length: {len(service_role_key)}")
        if len(service_role_key) == 219:
            print("    ✅ Expected length (219)")
        else:
            print(f"    ❌ Unexpected length (expected 219, got {len(service_role_key)})")
    
    print()
    print("🔬 Environment Variables Comparison Complete")

if __name__ == "__main__":
    test_env_comparison()
