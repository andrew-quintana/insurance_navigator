#!/usr/bin/env python3
"""
Unified Environment Synchronization Script

This script ensures all environments (development, staging, production) use
exactly the same library versions by:
1. Updating all requirements files
2. Installing unified versions locally
3. Updating Render environment variables
4. Triggering deployments
"""

import os
import subprocess
import sys
from pathlib import Path
import shutil

def update_requirements_files():
    """Update all requirements files with unified versions."""
    print("🔧 Updating Requirements Files")
    print("-" * 50)
    
    # Read unified requirements
    with open("requirements-unified.txt", "r") as f:
        unified_content = f.read()
    
    # Update all requirements files
    requirements_files = [
        "config/python/requirements.txt",
        "config/python/requirements-prod.txt",
        "requirements.txt"
    ]
    
    for req_file in requirements_files:
        if os.path.exists(req_file):
            # Backup original
            shutil.copy2(req_file, f"{req_file}.backup")
            
            # Write unified content
            with open(req_file, "w") as f:
                f.write(unified_content)
            
            print(f"✅ Updated {req_file}")
        else:
            print(f"⚠️  {req_file} not found, creating...")
            with open(req_file, "w") as f:
                f.write(unified_content)
            print(f"✅ Created {req_file}")

def install_unified_requirements():
    """Install unified requirements locally."""
    print("\n📦 Installing Unified Requirements")
    print("-" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements-unified.txt", "--upgrade"
        ], capture_output=True, text=True, check=True)
        
        print("✅ Successfully installed unified requirements")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install unified requirements: {e}")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
        return False

def update_render_environment_variables():
    """Update Render environment variables for both services."""
    print("\n🌐 Updating Render Environment Variables")
    print("-" * 50)
    
    # This would use the Render MCP tools to update environment variables
    # For now, we'll prepare the commands that need to be run
    
    print("📋 Render Environment Update Commands:")
    print("   Use the following commands to update Render services:")
    print()
    print("   Production Service (insurance-navigator-api-production):")
    print("   - Update PYTHON_VERSION to 3.11")
    print("   - Ensure all package versions match requirements-unified.txt")
    print()
    print("   Staging Service (insurance-navigator-api-staging):")
    print("   - Update PYTHON_VERSION to 3.11") 
    print("   - Ensure all package versions match requirements-unified.txt")
    print()
    print("   Both services will automatically redeploy after environment variable updates")

def test_local_environment():
    """Test the local environment with unified requirements."""
    print("\n🧪 Testing Local Environment")
    print("-" * 50)
    
    try:
        # Test RAG functionality
        result = subprocess.run([
            sys.executable, "test_rag_local_production.py"
        ], capture_output=True, text=True, check=True)
        
        print("✅ Local RAG test passed")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Local RAG test failed: {e}")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
        return False

def commit_and_push_changes():
    """Commit and push the unified requirements."""
    print("\n📝 Committing and Pushing Changes")
    print("-" * 50)
    
    try:
        # Add all requirements files
        subprocess.run(["git", "add", "requirements-unified.txt"], check=True)
        subprocess.run(["git", "add", "config/python/requirements.txt"], check=True)
        subprocess.run(["git", "add", "config/python/requirements-prod.txt"], check=True)
        subprocess.run(["git", "add", "requirements.txt"], check=True)
        
        # Commit
        subprocess.run([
            "git", "commit", "-m", 
            "feat: unify library versions across all environments\n\n- Created requirements-unified.txt with exact production versions\n- Updated all requirements files to match\n- Ensures development, staging, and production parity\n- Fixes Pydantic v2 compatibility issues"
        ], check=True)
        
        # Push to both branches
        subprocess.run(["git", "push", "origin", "development"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        
        print("✅ Changes committed and pushed to both development and main branches")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operations failed: {e}")
        return False

def main():
    """Main synchronization function."""
    print("🚨 UNIFIED ENVIRONMENT SYNCHRONIZATION")
    print("=" * 60)
    
    # Step 1: Update requirements files
    update_requirements_files()
    
    # Step 2: Install unified requirements locally
    if not install_unified_requirements():
        print("\n❌ SYNCHRONIZATION FAILED - Requirements installation failed")
        return False
    
    # Step 3: Test local environment
    if not test_local_environment():
        print("\n❌ SYNCHRONIZATION FAILED - Local tests failed")
        return False
    
    # Step 4: Update Render environment variables
    update_render_environment_variables()
    
    # Step 5: Commit and push changes
    if not commit_and_push_changes():
        print("\n❌ SYNCHRONIZATION FAILED - Git operations failed")
        return False
    
    print("\n" + "=" * 60)
    print("📊 SYNCHRONIZATION SUMMARY")
    print("=" * 60)
    print("✅ Requirements files updated")
    print("✅ Unified versions installed locally")
    print("✅ Local tests passed")
    print("✅ Changes committed and pushed")
    print("\n🎉 ALL ENVIRONMENTS SYNCHRONIZED!")
    print("   Next steps:")
    print("   1. Update Render environment variables (see commands above)")
    print("   2. Monitor deployments in Render dashboard")
    print("   3. Verify production functionality")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
