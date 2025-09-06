#!/usr/bin/env python3
"""
Test script to verify Supabase sandbox email configuration.
"""

import asyncio
import requests
import json

async def test_supabase_sandbox():
    """Test Supabase sandbox email configuration."""
    
    # Test registration with sandbox email
    test_emails = [
        "test1@example.com",
        "test2@test.com", 
        "sandbox@example.org",
        "user@testdomain.com"
    ]
    
    for email in test_emails:
        print(f"\n=== Testing registration with {email} ===")
        
        try:
            response = requests.post(
                "***REMOVED***/register",
                headers={"Content-Type": "application/json"},
                json={
                    "email": email,
                    "password": "testpassword123",
                    "full_name": "Test User"
                },
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ Registration successful!")
                break
            elif "rate limit" in response.text.lower():
                print("⏳ Rate limit - waiting 30 seconds...")
                await asyncio.sleep(30)
            else:
                print(f"❌ Registration failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_supabase_sandbox())
