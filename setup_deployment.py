#!/usr/bin/env python3
"""
Setup Script for Edge Functions Deployment
Helps get Supabase access token and deploy functions
"""

import os
import sys
import webbrowser
from pathlib import Path

def main():
    print("🚀 Edge Functions Deployment Setup")
    print("=" * 50)
    
    # Check if token already exists
    existing_token = os.getenv('SUPABASE_ACCESS_TOKEN')
    
    if existing_token and existing_token.startswith('sbp_'):
        print("✅ Access token already configured!")
        print(f"Token format: {existing_token[:10]}...")
        
        response = input("\nProceed with deployment? (y/n): ").lower()
        if response == 'y':
            run_deployment()
        else:
            print("Deployment cancelled.")
        return
    
    print("🔑 Access Token Setup Required")
    print("-" * 30)
    print("1. You need a Supabase access token to deploy Edge Functions")
    print("2. The token should start with 'sbp_' and be about 40 characters long")
    print("3. You can get one from: https://app.supabase.com/account/tokens")
    print()
    
    # Offer to open browser
    open_browser = input("Open Supabase account page in browser? (y/n): ").lower()
    if open_browser == 'y':
        try:
            webbrowser.open('https://app.supabase.com/account/tokens')
            print("🌐 Browser opened to Supabase account tokens page")
        except:
            print("❌ Could not open browser automatically")
            print("Please manually visit: https://app.supabase.com/account/tokens")
    
    print()
    print("📋 Steps to get your token:")
    print("1. Go to: https://app.supabase.com/account/tokens")
    print("2. Click 'Generate new token'")
    print("3. Give it a name (e.g., 'Edge Functions Deployment')")
    print("4. Copy the generated token")
    print("5. Come back here and paste it below")
    print()
    
    # Get token from user
    while True:
        token = input("Paste your Supabase access token here: ").strip()
        
        if not token:
            print("❌ No token provided")
            continue
        
        if not token.startswith('sbp_'):
            print("❌ Token should start with 'sbp_'")
            print(f"Your token starts with: {token[:5]}...")
            continue
        
        if len(token) < 20:
            print("❌ Token seems too short")
            continue
        
        print("✅ Token format looks correct!")
        break
    
    # Set environment variable
    os.environ['SUPABASE_ACCESS_TOKEN'] = token
    
    print()
    print("🔧 Token configured for this session")
    print("💡 To make it permanent, add this to your shell profile:")
    print(f"   export SUPABASE_ACCESS_TOKEN='{token}'")
    print()
    
    # Offer to run deployment
    run_deploy = input("Run deployment now? (y/n): ").lower()
    if run_deploy == 'y':
        run_deployment()
    else:
        print()
        print("✅ Setup complete!")
        print("Run deployment later with:")
        print("   python deploy_edge_functions_final.py")

def run_deployment():
    """Run the actual deployment"""
    print()
    print("🚀 Starting deployment...")
    print("=" * 50)
    
    # Import and run the deployment
    try:
        import subprocess
        result = subprocess.run([sys.executable, 'deploy_edge_functions_final.py'])
        
        if result.returncode == 0:
            print("🎉 Deployment completed successfully!")
        else:
            print("❌ Deployment failed - check the logs above")
            
    except Exception as e:
        print(f"❌ Error running deployment: {e}")
        print("Try running manually:")
        print("   python deploy_edge_functions_final.py")

if __name__ == "__main__":
    main() 