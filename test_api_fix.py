#!/usr/bin/env python3
"""
Quick API test script to verify Anthropic API is working
Run this after updating your API key
"""

import os
import anthropic

def test_api_key():
    """Test if the API key is working properly"""
    print("🧪 Testing Anthropic API Key...")
    print(f"Key prefix: {os.getenv('ANTHROPIC_API_KEY', 'NOT_SET')[:25]}...")
    
    try:
        # Create client
        client = anthropic.Anthropic()
        print("✅ Client created successfully")
        
        # Test simple request
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=20,
            messages=[{
                "role": "user", 
                "content": "Say 'API test successful' if you can read this."
            }]
        )
        
        print("✅ API call successful!")
        print(f"Response: {response.content[0].text}")
        print(f"Usage: {response.usage.input_tokens} input, {response.usage.output_tokens} output tokens")
        
        return True
        
    except anthropic.AuthenticationError as e:
        print(f"❌ Authentication Error: {e}")
        print("💡 Solution: Check your API key at https://console.anthropic.com/settings/keys")
        return False
        
    except anthropic.BadRequestError as e:
        if "credit balance" in str(e):
            print(f"❌ Credit Balance Error: {e}")
            print("💡 Solutions:")
            print("   1. Check billing at https://console.anthropic.com/settings/billing")
            print("   2. Verify you're in the right organization")
            print("   3. Generate a new API key")
            print("   4. Contact Anthropic support if dashboard shows credits available")
        else:
            print(f"❌ Bad Request Error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = test_api_key()
    if success:
        print("\n🎉 API is working! You can now run your supervisor team tests.")
    else:
        print("\n🚨 API still not working. Try the solutions above.") 