#!/usr/bin/env python3
"""
Configuration Override for Testing Production Endpoints

This script temporarily overrides the configuration to test production endpoints
without requiring a Docker restart.
"""

import os
import sys
import tempfile
import json
from pathlib import Path

def override_environment_variables():
    """Override environment variables for testing."""
    
    # Set the required environment variables
    os.environ['UPLOAD_PIPELINE_SUPABASE_URL'] = 'http://localhost:54321'
    os.environ['UPLOAD_PIPELINE_SUPABASE_SERVICE_ROLE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJmcKHUkt3pV/LC87Dkk='
    os.environ['UPLOAD_PIPELINE_LLAMAPARSE_API_URL'] = 'http://localhost:8001'
    os.environ['UPLOAD_PIPELINE_OPENAI_API_URL'] = 'http://localhost:8002'
    os.environ['UPLOAD_PIPELINE_ENVIRONMENT'] = 'development'
    
    print("✅ Environment variables overridden for testing")
    print(f"   SUPABASE_URL: {os.environ.get('UPLOAD_PIPELINE_SUPABASE_URL')}")
    print(f"   LLAMAPARSE_API_URL: {os.environ.get('UPLOAD_PIPELINE_LLAMAPARSE_API_URL')}")
    print(f"   OPENAI_API_URL: {os.environ.get('UPLOAD_PIPELINE_OPENAI_API_URL')}")

def test_config_override():
    """Test that the configuration override is working."""
    
    print("\n🧪 Testing Configuration Override")
    print("-" * 40)
    
    try:
        # Import the config module after setting environment variables
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'api' / 'upload_pipeline'))
        from config import get_config
        
        config = get_config()
        
        print(f"✅ Config loaded successfully")
        print(f"   Supabase URL: {config.supabase_url}")
        print(f"   Service Role Key: {config.supabase_service_role_key[:20]}...")
        print(f"   LlamaParse URL: {config.llamaparse_api_url}")
        print(f"   OpenAI URL: {config.openai_api_url}")
        print(f"   Environment: {config.environment}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config override failed: {e}")
        return False

if __name__ == "__main__":
    override_environment_variables()
    test_config_override()
