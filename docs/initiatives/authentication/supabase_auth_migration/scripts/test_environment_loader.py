#!/usr/bin/env python3
"""
Test script for environment loader
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from config.environment_loader import load_environment, get_environment_info

def test_environment_loader():
    """Test the environment loader functionality"""
    print("=== Environment Loader Test ===")
    
    try:
        # Get environment info
        env_info = get_environment_info()
        print(f"Environment: {env_info['environment']}")
        print(f"Platform: {env_info['platform']}")
        print(f"Cloud Deployment: {env_info['is_cloud_deployment']}")
        print(f"Required Variables: {env_info['required_vars']}")
        
        # Load environment variables
        env_vars = load_environment()
        print(f"Loaded Variables: {list(env_vars.keys())}")
        
        # Test specific variables
        print("\n=== Key Environment Variables ===")
        key_vars = ['ENVIRONMENT', 'SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY', 'DATABASE_URL']
        for var in key_vars:
            value = os.getenv(var, 'NOT_SET')
            if var == 'SUPABASE_SERVICE_ROLE_KEY':
                print(f"{var}: {value[:20]}..." if value != 'NOT_SET' else f"{var}: {value}")
            else:
                print(f"{var}: {value}")
        
        print("\n✅ Environment loader test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Environment loader test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_environment_loader()
    sys.exit(0 if success else 1)
