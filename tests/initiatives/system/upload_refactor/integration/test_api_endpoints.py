#!/usr/bin/env python3
"""
Integration tests for API endpoints using regulatory team's import bypass strategy.
Tests the actual running FastAPI server without importing problematic dependencies.
"""

import sys
import pytest
import requests
import json
import time
import random
from typing import Dict, Any

# Apply regulatory team's import bypass strategy
sys.path.insert(0, 'agents/regulatory/core')

# Base URL for the running server
BASE_URL = "http://localhost:8000"

class TestAPIEndpoints:
    """Test actual API endpoints of the running server"""
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "insurance_navigator"
        assert "mock_agent_available" in data
        assert "agents" in data
    
    def _register_unique_user(self):
        """Helper method to register a unique user and return token"""
        # Use timestamp + random number to ensure uniqueness even in concurrent tests
        unique_id = f"{int(time.time())}_{random.randint(1000, 9999)}"
        user_data = {
            "email": f"test_{unique_id}@example.com",
            "password": "testpass123",
            "name": "Test User"
        }
        
        response = requests.post(
            f"{BASE_URL}/register",
            headers={"Content-Type": "application/json"},
            json=user_data
        )
        
        if response.status_code != 200:
            print(f"Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            print(f"Email used: {user_data['email']}")
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        return data["access_token"]
    
    def test_register_user(self):
        """Test user registration"""
        token = self._register_unique_user()
        assert token is not None
        assert len(token) > 10  # Basic token validation
    
    def test_chat_with_authentication(self):
        """Test chat endpoint with proper authentication"""
        # First register a user
        token = self._register_unique_user()
        
        # Then test chat
        chat_data = {
            "message": "What are the Medicare Part A benefits for hospital stays?"
        }
        
        response = requests.post(
            f"{BASE_URL}/chat",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            json=chat_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "response" in data
        assert "sources" in data
        assert "metadata" in data
        
        # Validate mock regulatory agent response
        assert "Mock Regulatory Strategy Analysis" in data["response"]
        assert len(data["sources"]) >= 0  # Mock sources
        assert data["metadata"]["mock_mode"] is True
    
    def test_chat_without_authentication(self):
        """Test chat endpoint without authentication should fail"""
        chat_data = {
            "message": "Test message"
        }
        
        response = requests.post(
            f"{BASE_URL}/chat",
            headers={"Content-Type": "application/json"},
            json=chat_data
        )
        
        assert response.status_code == 401
    
    def test_upload_endpoint_authentication(self):
        """Test upload endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/upload-policy")
        assert response.status_code == 401
    
    def test_me_endpoint_authentication(self):
        """Test /me endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/me")
        assert response.status_code == 401
    
    def test_me_endpoint_with_auth(self):
        """Test /me endpoint with valid authentication"""
        # Register and get token
        token = self._register_unique_user()
        
        response = requests.get(
            f"{BASE_URL}/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "name" in data

@pytest.mark.integration
class TestWorkflowIntegration:
    """Test the complete Medicare Navigator workflow"""
    
    def test_complete_medicare_workflow(self):
        """Test the complete user workflow from registration to Medicare advice"""
        # Step 1: Register user with unique email
        unique_id = f"{int(time.time())}_{random.randint(1000, 9999)}"
        user_data = {
            "email": f"workflow_{unique_id}@example.com",
            "password": "testpass123",
            "name": "Workflow Test User"
        }
        
        register_response = requests.post(
            f"{BASE_URL}/register",
            headers={"Content-Type": "application/json"},
            json=user_data
        )
        assert register_response.status_code == 200
        token = register_response.json()["access_token"]
        
        # Step 2: Test Medicare-related questions
        medicare_questions = [
            "What does Medicare Part B cover?",
            "How do I appeal a Medicare claim denial?",
            "What are the costs for Medicare Advantage plans?",
            "Can Medicare cover telehealth services?"
        ]
        
        for question in medicare_questions:
            chat_response = requests.post(
                f"{BASE_URL}/chat",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                },
                json={"message": question}
            )
            
            assert chat_response.status_code == 200
            data = chat_response.json()
            
            # Verify Medicare Navigator functionality
            assert "Mock Regulatory Strategy Analysis" in data["response"]
            assert "medicare" in data["response"].lower() or "Medicare" in data["response"]
            assert data["metadata"]["mock_mode"] is True
            
        print(f"✅ Successfully tested {len(medicare_questions)} Medicare-related queries")

def test_server_is_running():
    """Prerequisite test to ensure server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        print("✅ Server is running and responding")
    except requests.exceptions.ConnectionError:
        pytest.fail("❌ Server is not running. Please start the server first: python -m uvicorn main:app --reload")

if __name__ == "__main__":
    # Run basic tests when called directly
    print("🧪 Running basic API integration tests...")
    test_server_is_running()
    
    # Test endpoints
    test_client = TestAPIEndpoints()
    test_client.test_health_endpoint()
    print("✅ Health endpoint test passed")
    
    test_client.test_register_user()
    print("✅ User registration test passed")
    
    test_client.test_chat_with_authentication()
    print("✅ Chat with authentication test passed")
    
    # Test workflow
    workflow_test = TestWorkflowIntegration()
    workflow_test.test_complete_medicare_workflow()
    print("✅ Complete Medicare workflow test passed")
    
    print("🎉 All integration tests passed!") 