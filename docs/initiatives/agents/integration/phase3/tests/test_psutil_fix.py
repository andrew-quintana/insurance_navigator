#!/usr/bin/env python3
"""
Test psutil fix after redeployment
"""

import asyncio
import sys
import os
import aiohttp
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

class PsutilFixTest:
    def __init__(self):
        self.api_base_url = "https://insurance-navigator-api.onrender.com"
        self.access_token = None
        
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv('.env.production')
            print("✅ Loaded .env.production")
        except Exception as e:
            print(f"⚠️  Could not load .env.production: {e}")
    
    async def run_test(self):
        """Test psutil fix after redeployment."""
        print("🔍 Testing psutil fix after redeployment")
        print("=" * 50)
        
        try:
            # Step 1: Get authentication token
            print("\n1️⃣ Getting authentication token...")
            await self.get_auth_token()
            
            if not self.access_token:
                print("❌ Failed to get authentication token")
                return False
            
            # Step 2: Test chat endpoint
            print("\n2️⃣ Testing chat endpoint...")
            success = await self.test_chat_endpoint()
            
            if success:
                print("\n✅ psutil fix test PASSED!")
                print("   Chat endpoint is working without psutil errors")
                return True
            else:
                print("\n❌ psutil fix test FAILED!")
                print("   Chat endpoint still has issues")
                return False
                
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            return False
    
    async def get_auth_token(self):
        """Get authentication token for testing."""
        try:
            async with aiohttp.ClientSession() as session:
                # Generate unique test user
                timestamp = int(time.time())
                test_email = f"psutil_test_{timestamp}@example.com"
                test_password = "testpass123"
                
                # Register user
                signup_data = {
                    "email": test_email,
                    "password": test_password,
                    "consent_version": "1.0",
                    "consent_timestamp": "2025-01-07T00:00:00Z"
                }
                
                async with session.post(f"{self.api_base_url}/auth/signup", json=signup_data) as response:
                    if response.status in [200, 201]:
                        signup_result = await response.json()
                        self.access_token = signup_result.get('access_token')
                        print(f"   ✅ User registered and token obtained")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"   ❌ User registration failed: {response.status} - {error_text}")
                        return False
                
        except Exception as e:
            print(f"   ❌ Authentication failed: {str(e)}")
            return False
    
    async def test_chat_endpoint(self):
        """Test chat endpoint for psutil errors."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Test chat
                chat_data = {
                    "message": "What is my deductible?",
                    "conversation_id": "",
                    "user_language": "en",
                    "context": {}
                }
                
                async with session.post(f"{self.api_base_url}/chat", json=chat_data, headers=headers) as response:
                    if response.status == 200:
                        chat_result = await response.json()
                        print(f"   ✅ Chat endpoint responded successfully")
                        print(f"   📊 Response: {chat_result.get('text', 'No response')[:100]}...")
                        
                        # Check for psutil error
                        metadata = chat_result.get('metadata', {})
                        if 'error' in metadata:
                            error_msg = metadata['error']
                            if 'psutil' in error_msg.lower():
                                print(f"   ❌ psutil error still present: {error_msg}")
                                return False
                            else:
                                print(f"   ⚠️  Other error (not psutil): {error_msg}")
                                return True
                        else:
                            print(f"   ✅ No errors in response metadata")
                            return True
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Chat endpoint failed: {response.status} - {error_text}")
                        return False
                
        except Exception as e:
            print(f"   ❌ Chat endpoint test failed: {str(e)}")
            return False

async def main():
    """Run psutil fix test."""
    print("🚀 Starting psutil fix test...")
    print("   This test will verify that the psutil dependency fix is working")
    print("   after the production services have been redeployed.\n")
    
    tester = PsutilFixTest()
    success = await tester.run_test()
    
    if success:
        print("\n🎉 psutil fix test completed successfully!")
        print("   The psutil dependency issue has been resolved!")
    else:
        print("\n⚠️  psutil fix test found issues")
        print("   The psutil dependency may still need to be resolved")

if __name__ == "__main__":
    asyncio.run(main())
