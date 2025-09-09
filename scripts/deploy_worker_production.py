#!/usr/bin/env python3
"""
Deploy worker service with production configuration to Render.
"""

import os
import subprocess
import sys
import time
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

def main():
    """Deploy worker service with production configuration."""
    print("🚀 Deploying Worker Service with Production Configuration")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("config/render/render.yaml").exists():
        print("❌ Error: Must be run from project root directory")
        sys.exit(1)
    
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
    
    print("\n📋 Production Configuration Changes:")
    print("  ✅ Updated worker config to use production API URLs")
    print("  ✅ Set SERVICE_MODE to 'real' for production")
    print("  ✅ Added LLAMAPARSE_API_URL and OPENAI_API_URL")
    print("  ✅ Updated service router to use REAL mode in production")
    
    # Deploy the worker service
    print("\n🚀 Deploying worker service...")
    
    # First, let's check the current services
    print("\n📊 Current Render services:")
    run_command("render services list", "Listing current services")
    
    # Deploy using the render.yaml configuration
    deploy_cmd = "render deploy --service insurance-navigator-worker"
    result = run_command(deploy_cmd, "Deploying worker service")
    
    if result:
        print("\n✅ Worker service deployment initiated!")
        print("\n📋 Next Steps:")
        print("  1. Monitor deployment in Render dashboard")
        print("  2. Check worker logs for successful startup")
        print("  3. Verify API keys are properly set in environment")
        print("  4. Test document upload with real APIs")
        
        print("\n🔍 To monitor the deployment:")
        print("  render logs --service insurance-navigator-worker --follow")
        
        print("\n🔧 To check environment variables:")
        print("  render env list --service insurance-navigator-worker")
        
    else:
        print("\n❌ Deployment failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
