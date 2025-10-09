#!/usr/bin/env python3
"""
Production Configuration Loader
Loads environment variables and updates production.config.json with actual values
"""

import os
import json
import sys
from pathlib import Path

def load_env_file(env_path):
    """Load environment variables from .env file"""
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

def substitute_env_vars(config_str, env_vars):
    """Substitute environment variables in configuration string"""
    for key, value in env_vars.items():
        config_str = config_str.replace(f"${{{key}}}", value)
        config_str = config_str.replace(f"${{{key}:-", f"${{{key}:-")
    return config_str

def main():
    # Load environment variables
    env_vars = {}
    
    # Try to load from .env.production if it exists
    env_file = Path(__file__).parent / '.env.production'
    if env_file.exists():
        env_vars.update(load_env_file(env_file))
    
    # Override with actual environment variables
    for key in os.environ:
        env_vars[key] = os.environ[key]
    
    # Required environment variables for production
    required_vars = [
        'SUPABASE_PROJECT_ID',
        'SUPABASE_ORG_ID', 
        'DATABASE_HOST',
        'DATABASE_PORT',
        'DATABASE_NAME',
        'DATABASE_USER',
        'DATABASE_PASSWORD',
        'DATABASE_MAX_CONNECTIONS',
        'DATABASE_POOL_SIZE',
        'SITE_URL',
        'ADDITIONAL_REDIRECT_URLS',
        'JWT_EXPIRY',
        'STORAGE_BUCKET_NAME',
        'STORAGE_FILE_SIZE_LIMIT',
        'STORAGE_ALLOWED_MIME_TYPES',
        'REALTIME_MAX_CONNECTIONS',
        'EDGE_FUNCTIONS_MAX_EXECUTION_TIME',
        'MONITORING_METRICS_RETENTION_DAYS',
        'MONITORING_LOG_RETENTION_DAYS',
        'BACKUP_SCHEDULE',
        'BACKUP_RETENTION_DAYS',
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    # Check for missing required variables
    missing_vars = []
    for var in required_vars:
        if var not in env_vars or not env_vars[var] or env_vars[var].strip() == '':
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Please set these variables in your environment or .env.production file")
        print("📋 See production.env.template for reference values")
        print("\n🔧 Example usage:")
        print("   export DATABASE_PASSWORD='your-password'")
        print("   export SUPABASE_PROJECT_ID='mrbigmtnadjtyepxqefa'")
        print("   # ... set all required variables")
        print("   python config_loader.py")
        sys.exit(1)
    
    # Load the template configuration
    config_path = Path(__file__).parent / 'production.config.json'
    with open(config_path, 'r') as f:
        config_str = f.read()
    
    # Substitute environment variables
    config_str = substitute_env_vars(config_str, env_vars)
    
    # Parse and validate JSON
    try:
        config = json.loads(config_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)
    
    # Write the resolved configuration
    resolved_config_path = Path(__file__).parent / 'production.config.resolved.json'
    with open(resolved_config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Production configuration resolved and saved to {resolved_config_path}")
    print(f"📋 Configuration includes:")
    print(f"   - Project ID: {config['project_id']}")
    print(f"   - Database Host: {config['database']['host']}")
    print(f"   - Site URL: {config['auth']['site_url']}")
    print(f"   - Storage Bucket: {config['storage']['buckets'][0]['name']}")

if __name__ == '__main__':
    main()
