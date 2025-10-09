#!/usr/bin/env python3
"""
Local Chat Testing Script for FM-038 Investigation

This script helps recreate the chat pipeline failure locally
and test our comprehensive logging changes.
"""

import os
import sys
import asyncio
import json
import time
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment for development
os.environ['ENVIRONMENT'] = 'development'

def setup_environment():
    """Set up environment variables for local testing."""
    print("🔧 Setting up environment for local testing...")
    
    # Set minimal environment variables for testing
    env_vars = {
        'ENVIRONMENT': 'development',
        'LOG_LEVEL': 'DEBUG',
        'DEBUG': 'true',
        'SERVICE_HOST': '0.0.0.0',
        'SERVICE_PORT': '8000',
        'CORS_ORIGINS': 'http://localhost:3000,http://localhost:3001',
        
        # Mock database (we'll use in-memory for testing)
        'DATABASE_URL': 'sqlite:///test.db',
        
        # Mock API keys (we'll use mock mode)
        'OPENAI_API_KEY': 'mock-key',
        'ANTHROPIC_API_KEY': 'mock-key',
        'LLAMAPARSE_API_KEY': 'mock-key',
        'RESEND_API_KEY': 'mock-key',
        
        # Mock Supabase
        'SUPABASE_URL': 'http://localhost:54321',
        'SUPABASE_ANON_KEY': 'mock-anon-key',
        'SUPABASE_SERVICE_ROLE_KEY': 'mock-service-key',
        'JWT_SECRET': 'mock-jwt-secret',
        'DOCUMENT_ENCRYPTION_KEY': 'mock-encryption-key',
        
        # RAG Configuration
        'RAG_SIMILARITY_THRESHOLD': '0.3',
        'RAG_MAX_CHUNKS': '10',
        'RAG_TOKEN_BUDGET': '4000',
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"  ✓ {key}={value}")
    
    print("✅ Environment setup complete!")

async def test_chat_endpoint():
    """Test the chat endpoint with our comprehensive logging."""
    print("\n🚀 Starting local chat test...")
    
    try:
        # Import the FastAPI app
        from main import app
        print("✅ FastAPI app imported successfully")
        
        # Override the authentication dependency for testing
        from unittest.mock import patch
        from main import get_current_user
        
        # Mock user data
        mock_user = {
            "id": "test-user-123",
            "email": "test@example.com",
            "sub": "test-user-123"
        }
        
        # Patch the authentication function
        with patch('main.get_current_user', return_value=mock_user):
            print("✅ Authentication mocked successfully")
            
            # Create a test client
            from fastapi.testclient import TestClient
            client = TestClient(app)
            print("✅ Test client created")
            
            # Test data similar to the production logs
            test_message = {
                "message": "What is my deductible amount?",
                "conversation_id": "test_conv_123",
                "user_language": "en",
                "context": {}
            }
            
            print(f"\n📝 Sending test message: {test_message['message']}")
            print("🔍 Watching for our comprehensive logging...")
            print("=" * 60)
            
            # Send the request and capture the response
            start_time = time.time()
            response = client.post("/chat", json=test_message)
            end_time = time.time()
            
            print("=" * 60)
            print(f"⏱️  Request completed in {end_time - start_time:.2f} seconds")
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"✅ Response received successfully!")
                print(f"📄 Response content: {response_data.get('text', 'No text')[:100]}...")
            else:
                print(f"❌ Request failed with status {response.status_code}")
                print(f"📄 Error response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        print(f"📄 Traceback: {traceback.format_exc()}")

def check_logging_presence():
    """Check if our comprehensive logging is present in the code."""
    print("\n🔍 Checking for comprehensive logging presence...")
    
    logging_checks = [
        ("main.py", "=== CHAT ENDPOINT CALLED ==="),
        ("main.py", "Starting chat message processing with 60-second timeout"),
        ("agents/patient_navigator/information_retrieval/agent.py", "=== RAG OPERATIONS COMPLETED ==="),
        ("agents/patient_navigator/chat_interface.py", "=== WORKFLOW OUTPUTS PROCESSING COMPLETED ==="),
        ("agents/patient_navigator/output_processing/two_stage_synthesizer.py", "=== TWO-STAGE SYNTHESIZER CALLED ==="),
        ("agents/patient_navigator/output_processing/agent.py", "=== COMMUNICATION AGENT ENHANCE_RESPONSE CALLED ==="),
        ("agents/patient_navigator/chat_interface.py", "=== CREATING CHAT RESPONSE ==="),
        ("main.py", "=== CHAT INTERFACE RETURNED RESPONSE ==="),
        ("main.py", "=== CREATING FINAL JSON RESPONSE ==="),
    ]
    
    all_present = True
    for file_path, log_text in logging_checks:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                if log_text in content:
                    print(f"  ✅ {file_path}: Found '{log_text}'")
                else:
                    print(f"  ❌ {file_path}: Missing '{log_text}'")
                    all_present = False
        except FileNotFoundError:
            print(f"  ❌ {file_path}: File not found")
            all_present = False
    
    if all_present:
        print("✅ All comprehensive logging statements are present!")
    else:
        print("❌ Some logging statements are missing!")
    
    return all_present

async def main():
    """Main test function."""
    print("🔬 FM-038 Local Chat Testing")
    print("=" * 50)
    
    # Check if logging is present
    logging_present = check_logging_presence()
    
    if not logging_present:
        print("\n❌ Comprehensive logging not found. Please ensure our changes are committed.")
        return
    
    # Set up environment
    setup_environment()
    
    # Test the chat endpoint
    await test_chat_endpoint()
    
    print("\n🎯 Test completed!")
    print("Check the logs above to see which of our comprehensive logging statements appear.")

if __name__ == "__main__":
    asyncio.run(main())
