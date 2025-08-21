#!/usr/bin/env python3
"""
Simple script to test environment variable access.
"""

import os
import sys

def test_environment_access():
    """Test access to environment variables."""
    print("Testing environment variable access...")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Test key environment variables
    env_vars = [
        'LLAMAPARSE_API_KEY',
        'OPENAI_API_KEY', 
        'LLAMAPARSE_BASE_URL',
        'LLAMAPARSE_WEBHOOK_SECRET'
    ]
    
    print("\nEnvironment variable status:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:20]}...")
        else:
            print(f"❌ {var}: NOT FOUND")
    
    # Test if we can access the .env file directly
    print("\nTrying to read .env.development directly...")
    try:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.development')
        if os.path.exists(env_file):
            print(f"✅ .env.development file exists at: {env_file}")
            
            # Read and parse the file
            with open(env_file, 'r') as f:
                content = f.read()
            
            # Look for our variables
            for var in env_vars:
                for line in content.split('\n'):
                    if line.startswith(f'{var}='):
                        value = line.split('=', 1)[1].strip()
                        print(f"✅ Found {var} in file: {value[:20]}...")
                        break
                else:
                    print(f"❌ {var} not found in .env.development file")
        else:
            print(f"❌ .env.development file not found at: {env_file}")
    except Exception as e:
        print(f"❌ Error reading .env.development: {e}")

if __name__ == "__main__":
    test_environment_access()
