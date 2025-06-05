#!/usr/bin/env python3
"""
Test script to verify .env setup and API configuration for build logs.

This script checks if the required environment variables are properly set
and can successfully connect to the Vercel and Render APIs.
"""

import os
import sys
import requests
from pathlib import Path


def load_env_file(env_path=".env"):
    """Load environment variables from .env file."""
    if not os.path.exists(env_path):
        return False
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key.strip()] = value
        return True
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False


def mask_token(token):
    """Mask token for display purposes."""
    if not token:
        return "Not set"
    if len(token) < 8:
        return "*" * len(token)
    return token[:4] + "*" * (len(token) - 8) + token[-4:]


def test_vercel_api():
    """Test Vercel API connection."""
    token = os.getenv('VERCEL_API_TOKEN')
    project_id = os.getenv('VERCEL_PROJECT_ID')
    
    print("🌐 Testing Vercel API...")
    print(f"   Token: {mask_token(token)}")
    print(f"   Project ID: {project_id or 'Not set'}")
    
    if not token or not project_id:
        print("   ❌ Missing required environment variables")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://api.vercel.com/v6/deployments?projectId={project_id}&limit=1"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            deployments = response.json().get('deployments', [])
            print(f"   ✅ Connection successful! Found {len(deployments)} deployment(s)")
            return True
        else:
            print(f"   ❌ API Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False


def test_render_api():
    """Test Render API connection."""
    token = os.getenv('RENDER_API_TOKEN')
    service_id = os.getenv('RENDER_SERVICE_ID')
    
    print("🔧 Testing Render API...")
    print(f"   Token: {mask_token(token)}")
    print(f"   Service ID: {service_id or 'Not set'}")
    
    if not token or not service_id:
        print("   ❌ Missing required environment variables")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://api.render.com/v1/services/{service_id}/deploys?limit=1"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            deploys = response.json()
            print(f"   ✅ Connection successful! Found {len(deploys)} deployment(s)")
            return True
        else:
            print(f"   ❌ API Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False


def show_setup_instructions():
    """Show setup instructions for missing configuration."""
    print("\n💡 Setup Instructions:")
    print("=" * 50)
    
    print("\n1. Create a .env file in your project root:")
    print("   touch .env")
    
    print("\n2. Add your API credentials to .env:")
    print("   # Vercel Configuration")
    print("   VERCEL_API_TOKEN=your-vercel-token-here")
    print("   VERCEL_PROJECT_ID=your-project-id-here")
    print("   ")
    print("   # Render Configuration")
    print("   RENDER_API_TOKEN=your-render-token-here")
    print("   RENDER_SERVICE_ID=your-service-id-here")
    
    print("\n3. Get your API tokens:")
    print("   Vercel Token: https://vercel.com/account/tokens")
    print("   Vercel Project ID: Project Settings → General → Project ID")
    print("   Render Token: https://dashboard.render.com/account/api-keys")
    print("   Render Service ID: From your service URL (srv-xxxxx)")
    
    print("\n4. Test again with:")
    print("   python scripts/test_env_setup.py")


def main():
    """Main test function."""
    print("🧪 Testing Build Logs Environment Setup")
    print("=" * 50)
    
    # Load .env file
    print("📄 Loading .env file...")
    if load_env_file():
        print("   ✅ .env file loaded successfully")
    else:
        print("   ⚠️  No .env file found or error loading")
    
    print()
    
    # Test APIs
    vercel_ok = test_vercel_api()
    print()
    render_ok = test_render_api()
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    
    if vercel_ok and render_ok:
        print("   🎉 All APIs configured and working!")
        print("   ✅ You can now use automatic log fetching")
        print("\n   Run: ./scripts/new_build_logs.sh")
    elif vercel_ok or render_ok:
        print("   ⚠️  Partial setup - some APIs working")
        working = []
        if vercel_ok:
            working.append("Vercel")
        if render_ok:
            working.append("Render")
        print(f"   ✅ Working: {', '.join(working)}")
        print("   ⚠️  Configure remaining APIs for full functionality")
    else:
        print("   ❌ No APIs configured")
        show_setup_instructions()
    
    return vercel_ok or render_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 