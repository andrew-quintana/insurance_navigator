#!/usr/bin/env python3
"""
Start API Server with Production Environment
Start the local API server with production Supabase configuration
"""

import os
import subprocess
import sys
from dotenv import load_dotenv

# Load production environment variables
load_dotenv('.env.production')

# Set production environment variables
production_env = {
    'DATABASE_URL': os.getenv('DATABASE_URL'),
    'SUPABASE_URL': os.getenv('SUPABASE_URL'),
    'SUPABASE_ANON_KEY': os.getenv('SUPABASE_ANON_KEY'),
    'SUPABASE_SERVICE_ROLE_KEY': os.getenv('SUPABASE_SERVICE_ROLE_KEY'),
    'LLAMAPARSE_API_KEY': os.getenv('LLAMAPARSE_API_KEY'),
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
    'LLAMAPARSE_API_URL': 'https://api.cloud.llamaindex.ai',
    'OPENAI_API_URL': 'https://api.openai.com/v1',
    'UPLOAD_PIPELINE_ENVIRONMENT': 'production',
    'UPLOAD_PIPELINE_STORAGE_ENVIRONMENT': 'production',
    'SERVICE_MODE': 'API_ONLY',
    'PYTHONPATH': '/Users/aq_home/1Projects/accessa/insurance_navigator'
}

print("🚀 Starting API Server with Production Environment")
print(f"🌐 Database: {production_env['DATABASE_URL'][:50]}...")
print(f"🔑 LlamaParse: {production_env['LLAMAPARSE_API_KEY'][:20]}...")
print(f"🔑 OpenAI: {production_env['OPENAI_API_KEY'][:20]}...")

# Change to backend directory
os.chdir('/Users/aq_home/1Projects/accessa/insurance_navigator/backend')

# Start the API server
try:
    # Update environment
    os.environ.update(production_env)
    
    # Start the server
    subprocess.run([
        sys.executable, '-m', 'uvicorn', 
        'main:app', 
        '--host', '0.0.0.0', 
        '--port', '8000',
        '--reload'
    ], env=production_env)
    
except KeyboardInterrupt:
    print("\n🛑 API Server stopped")
except Exception as e:
    print(f"❌ Failed to start API server: {e}")
