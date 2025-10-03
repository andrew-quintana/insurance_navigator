#!/usr/bin/env python3
"""
Verify worker service configuration and environment variables.
"""

import os
import subprocess
import sys
import json
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {cmd}")
        print(f"   Error: {e.stderr}")
        return None

def check_environment_variables():
    """Check if required environment variables are set in the worker service."""
    print("🔍 Checking Worker Service Environment Variables")
    print("=" * 50)
    
    # Get environment variables from Render
    env_output = run_command("render env list --service insurance-navigator-worker", "Getting worker environment variables")
    
    if not env_output:
        print("❌ Could not retrieve environment variables")
        return False
    
    # Parse environment variables
    env_vars = {}
    for line in env_output.strip().split('\n'):
        if '=' in line:
            key, value = line.split('=', 1)
            env_vars[key] = value
    
    # Required environment variables for production
    required_vars = {
        'SERVICE_MODE': 'real',
        'ENVIRONMENT': 'production',
        'LLAMAPARSE_API_URL': 'https://api.cloud.llamaindex.ai',
        'OPENAI_API_URL': 'https://api.openai.com',
        'SUPABASE_URL': 'https://your-project.supabase.co'
    }
    
    # API keys that should be set (but we won't show the values)
    api_keys = [
        'LLAMAPARSE_API_KEY',
        'OPENAI_API_KEY',
        'SUPABASE_ANON_KEY',
        'SUPABASE_SERVICE_ROLE_KEY',
        'DATABASE_URL'
    ]
    
    print("\n📋 Checking Required Configuration:")
    all_good = True
    
    for var, expected_value in required_vars.items():
        if var in env_vars:
            actual_value = env_vars[var]
            if actual_value == expected_value:
                print(f"  ✅ {var}: {actual_value}")
            else:
                print(f"  ⚠️  {var}: {actual_value} (expected: {expected_value})")
                all_good = False
        else:
            print(f"  ❌ {var}: NOT SET")
            all_good = False
    
    print("\n🔑 Checking API Keys:")
    for key in api_keys:
        if key in env_vars and env_vars[key]:
            print(f"  ✅ {key}: [SET]")
        else:
            print(f"  ❌ {key}: NOT SET")
            all_good = False
    
    return all_good

def check_worker_logs():
    """Check worker logs for any errors or issues."""
    print("\n📊 Checking Worker Logs (last 20 lines):")
    print("=" * 50)
    
    logs_output = run_command("render logs --service insurance-navigator-worker --tail 20", "Getting worker logs")
    
    if logs_output:
        print(logs_output)
        
        # Check for common issues
        if "Real service 'openai' unavailable" in logs_output:
            print("\n⚠️  Warning: OpenAI service appears to be unavailable")
        if "Real service 'llamaparse' unavailable" in logs_output:
            print("\n⚠️  Warning: LlamaParse service appears to be unavailable")
        if "using mock service" in logs_output:
            print("\n⚠️  Warning: Worker is still using mock services")
        if "Service health check completed" in logs_output:
            print("\n✅ Service health checks are running")
    else:
        print("❌ Could not retrieve worker logs")

def main():
    """Verify worker service configuration."""
    print("🔍 Worker Service Configuration Verification")
    print("=" * 60)
    
    # Check if render CLI is installed
    if not run_command("which render", "Checking Render CLI installation"):
        print("❌ Error: Render CLI not found. Please install it first:")
        print("   curl -fsSL https://cli.render.com/install | sh")
        sys.exit(1)
    
    # Check if logged in to Render
    if not run_command("render auth whoami", "Checking Render authentication"):
        print("❌ Error: Not logged in to Render. Please run:")
        print("   render auth login")
        sys.exit(1)
    
    # Check environment variables
    env_ok = check_environment_variables()
    
    # Check worker logs
    check_worker_logs()
    
    print("\n" + "=" * 60)
    if env_ok:
        print("✅ Worker service configuration looks good!")
        print("\n📋 Next Steps:")
        print("  1. Test document upload with real APIs")
        print("  2. Monitor worker logs for successful processing")
        print("  3. Verify that real embeddings are being generated")
    else:
        print("❌ Worker service configuration has issues!")
        print("\n🔧 Fix Required:")
        print("  1. Set missing environment variables in Render dashboard")
        print("  2. Ensure API keys are properly configured")
        print("  3. Redeploy the worker service")

if __name__ == "__main__":
    main()
