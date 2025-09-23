#!/usr/bin/env python3
"""
Test script to simulate Render environment configuration locally
"""
import os
import subprocess
import time
import requests
import signal
import sys

def test_port_configuration():
    """Test the application with Render-like environment variables"""
    
    print("🧪 Testing Render Environment Configuration Locally")
    print("=" * 60)
    
    # Set Render-like environment variables
    env = os.environ.copy()
    env.update({
        'PORT': '10000',
        'API_HOST': '0.0.0.0', 
        'API_PORT': '8000',
        'ENVIRONMENT': 'staging'
    })
    
    print("📋 Environment Variables:")
    for key in ['PORT', 'API_HOST', 'API_PORT', 'ENVIRONMENT']:
        print(f"  {key}: {env.get(key, 'NOT SET')}")
    
    print("\n🚀 Starting application with Render config...")
    
    # Start the application
    process = subprocess.Popen(
        [sys.executable, 'main.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Wait for startup
        print("⏳ Waiting for application to start...")
        time.sleep(10)
        
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        try:
            response = requests.get('http://localhost:10000/health', timeout=5)
            if response.status_code == 200:
                print("✅ Health check passed!")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Health check failed: {e}")
        
        # Test port 8000 (should not be accessible)
        print("🔍 Testing port 8000 (should fail)...")
        try:
            response = requests.get('http://localhost:8000/health', timeout=2)
            print(f"⚠️  Port 8000 is accessible (unexpected): {response.status_code}")
        except requests.exceptions.RequestException:
            print("✅ Port 8000 not accessible (expected)")
        
        # Check process output
        print("\n📝 Application Output:")
        try:
            stdout, stderr = process.communicate(timeout=1)
            if stdout:
                print("STDOUT:", stdout[-500:])  # Last 500 chars
            if stderr:
                print("STDERR:", stderr[-500:])  # Last 500 chars
        except subprocess.TimeoutExpired:
            print("Application still running (timeout on output read)")
        
    finally:
        # Clean up
        print("\n🛑 Stopping application...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        print("✅ Application stopped")

if __name__ == "__main__":
    test_port_configuration()
