#!/usr/bin/env python3
"""
Deploy Unified API to Render
============================

This script helps deploy the unified API implementation to Render and verifies the deployment.
"""

import subprocess
import sys
import time
import requests
from datetime import datetime

def run_command(command, description):
    """Run a shell command and return the result."""
    print(f"\n🔧 {description}")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ Success: {description}")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Failed: {description}")
            print(f"Error: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout: {description}")
        return False
    except Exception as e:
        print(f"💥 Exception: {e}")
        return False

def check_git_status():
    """Check if there are uncommitted changes."""
    print("\n📋 Checking Git status...")
    
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print("📝 Uncommitted changes found:")
        print(result.stdout)
        return False
    else:
        print("✅ Working directory is clean")
        return True

def commit_changes():
    """Commit the unified API changes."""
    print("\n📝 Committing unified API changes...")
    
    commands = [
        ("git add main.py", "Adding main.py"),
        ("git add unified_regulatory_uploader.py", "Adding uploader script"),
        ("git add test_unified_api.py", "Adding test script"),
        ("git add UNIFIED_API_IMPLEMENTATION.md", "Adding documentation"),
        ('git commit -m "feat: Add unified API for regulatory document processing with vector generation"', "Committing changes")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            # If add commands fail, it might be because files don't exist or are already staged
            if "add" in command:
                continue
            return False
    return True

def push_to_remote():
    """Push changes to the remote repository."""
    return run_command("git push origin main", "Pushing to origin/main")

def wait_for_deployment(max_wait=300):
    """Wait for Render deployment to complete."""
    print(f"\n⏳ Waiting for Render deployment (max {max_wait}s)...")
    print("💡 You can monitor deployment at: https://dashboard.render.com")
    
    backend_url = "https://insurance-navigator-api.onrender.com"
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            # Check if the unified endpoint is available
            response = requests.get(f"{backend_url}/openapi.json", timeout=10)
            if response.status_code == 200:
                openapi_spec = response.json()
                if "/api/documents/upload-regulatory" in openapi_spec.get("paths", {}):
                    elapsed = time.time() - start_time
                    print(f"✅ Deployment complete! (took {elapsed:.1f}s)")
                    return True
            
            print("⏳ Still deploying... (checking every 30s)")
            time.sleep(30)
            
        except Exception as e:
            print(f"⚠️ Deployment check failed: {e}")
            time.sleep(30)
    
    print("⏰ Deployment timeout reached")
    return False

def verify_deployment():
    """Verify the deployment by running tests."""
    print("\n🧪 Running deployment verification tests...")
    return run_command("python test_render_unified_api.py", "Testing unified API endpoints")

def main():
    """Main deployment function."""
    print("=" * 60)
    print("🚀 UNIFIED API DEPLOYMENT TO RENDER")
    print("=" * 60)
    print(f"Started at: {datetime.now()}")
    
    # Step 1: Check git status
    if not check_git_status():
        response = input("\n⚠️ You have uncommitted changes. Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("🛑 Deployment cancelled")
            sys.exit(1)
    
    # Step 2: Commit changes
    if not commit_changes():
        print("❌ Failed to commit changes")
        sys.exit(1)
    
    # Step 3: Push to remote
    if not push_to_remote():
        print("❌ Failed to push to remote")
        print("💡 Check your git configuration and permissions")
        sys.exit(1)
    
    # Step 4: Wait for deployment
    if not wait_for_deployment():
        print("⚠️ Deployment verification timeout")
        print("💡 Check Render dashboard for deployment status")
        print("💡 You can manually test later with: python test_render_unified_api.py")
    else:
        # Step 5: Verify deployment
        verify_deployment()
    
    print("\n" + "=" * 60)
    print("🏁 DEPLOYMENT SUMMARY")
    print("=" * 60)
    
    print("✅ Code pushed to repository")
    print("⏳ Render deployment triggered")
    print("💡 Next steps:")
    print("   1. Monitor deployment at: https://dashboard.render.com")
    print("   2. Test endpoints with: python test_render_unified_api.py")
    print("   3. Upload regulatory docs with: python unified_regulatory_uploader.py")
    
    print(f"\nCompleted at: {datetime.now()}")

if __name__ == "__main__":
    main() 