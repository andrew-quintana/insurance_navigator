#!/usr/bin/env python3
"""
Integration tests for FastAPI endpoints with database services.
Tests the complete API flow including authentication, chat, and storage.
"""

import os
import sys
import asyncio
import pytest
import httpx
import tempfile
from pathlib import Path
from datetime import datetime
import uuid

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = f"test_api_{uuid.uuid4().hex[:8]}@example.com"
TEST_USER_PASSWORD = "TestPassword123!"
TEST_USER_NAME = "API Test User"

class FastAPIEndpointTests:
    """Comprehensive API endpoint integration tests."""

    def __init__(self):
        self.client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0)
        self.access_token = None
        self.conversation_id = None
        self.uploaded_file_path = None

    async def setup(self):
        """Set up test environment and check API availability."""
        try:
            # Check if API is running
            response = await self.client.get("/health")
            if response.status_code != 200:
                raise Exception(f"API health check failed: {response.status_code}")
            
            health_data = response.json()
            logger.info(f"API health status: {health_data}")
            
            # Verify database services are healthy
            services = health_data.get("services", {})
            if services.get("database") != "healthy":
                logger.warning(f"Database status: {services.get('database')}")
            
            logger.info("✅ API is running and accessible")
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            raise

    async def test_root_endpoint(self):
        """Test root endpoint information."""
        logger.info("🧪 Testing root endpoint...")
        
        response = await self.client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "Insurance Navigator API"
        assert data["version"] == "2.0.0"
        assert "endpoints" in data
        
        logger.info("✅ Root endpoint working correctly")

    async def test_health_endpoint(self):
        """Test comprehensive health check."""
        logger.info("🧪 Testing health endpoint...")
        
        response = await self.client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "timestamp" in data
        
        # Log service statuses
        for service, status in data["services"].items():
            logger.info(f"   {service}: {status}")
        
        logger.info("✅ Health endpoint working correctly")

    async def test_user_registration(self):
        """Test user registration with database persistence."""
        logger.info("🧪 Testing user registration...")
        
        registration_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "full_name": TEST_USER_NAME
        }
        
        response = await self.client.post("/register", json=registration_data)
        
        if response.status_code == 400:
            # User might already exist, try to continue with login
            logger.warning(f"Registration failed (likely user exists): {response.json()}")
            return await self.test_user_login()
        
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        self.access_token = data["access_token"]
        logger.info("✅ User registration successful")

    async def test_user_login(self):
        """Test user login with database authentication."""
        logger.info("🧪 Testing user login...")
        
        login_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        response = await self.client.post("/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        self.access_token = data["access_token"]
        logger.info("✅ User login successful")

    async def test_get_current_user(self):
        """Test authenticated user endpoint."""
        logger.info("🧪 Testing current user endpoint...")
        
        if not self.access_token:
            await self.test_user_registration()
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = await self.client.get("/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == TEST_USER_EMAIL
        assert data["full_name"] == TEST_USER_NAME
        assert "id" in data
        assert "roles" in data
        
        logger.info(f"✅ Current user: {data['email']} (ID: {data['id']})")

    async def test_chat_endpoint(self):
        """Test chat endpoint with conversation persistence."""
        logger.info("🧪 Testing chat endpoint...")
        
        if not self.access_token:
            await self.test_user_registration()
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        chat_data = {
            "message": "Hello, I need help with Medicare eligibility. What are the basic requirements?",
            "context": {"test": True}
        }
        
        response = await self.client.post("/chat", json=chat_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "text" in data
        assert "conversation_id" in data
        assert data["workflow_type"] == "medicare_navigator"
        
        self.conversation_id = data["conversation_id"]
        
        logger.info(f"✅ Chat response received (conversation: {self.conversation_id})")
        logger.info(f"   Response: {data['text'][:100]}...")

    async def test_conversation_continuation(self):
        """Test continuing an existing conversation."""
        logger.info("🧪 Testing conversation continuation...")
        
        if not self.conversation_id:
            await self.test_chat_endpoint()
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        chat_data = {
            "message": "What about Medicaid? How is it different from Medicare?",
            "conversation_id": self.conversation_id,
            "context": {"followup": True}
        }
        
        response = await self.client.post("/chat", json=chat_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["conversation_id"] == self.conversation_id
        assert "text" in data
        
        logger.info("✅ Conversation continuation successful")

    async def test_get_conversations(self):
        """Test retrieving user's conversation history."""
        logger.info("🧪 Testing conversation history retrieval...")
        
        if not self.access_token:
            await self.test_user_registration()
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = await self.client.get("/conversations", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if data:
            conversation = data[0]
            assert "id" in conversation
            assert "created_at" in conversation
            assert "message_count" in conversation
            
            logger.info(f"✅ Found {len(data)} conversations")
        else:
            logger.info("✅ No conversations found (expected for new user)")

    async def test_get_conversation_messages(self):
        """Test retrieving messages from a specific conversation."""
        logger.info("🧪 Testing conversation messages retrieval...")
        
        if not self.conversation_id:
            await self.test_chat_endpoint()
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = await self.client.get(
            f"/conversations/{self.conversation_id}/messages",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "messages" in data
        messages = data["messages"]
        
        if messages:
            # Should have at least user message and assistant response
            assert len(messages) >= 2
            
            # Check message structure
            user_message = next((m for m in messages if m["role"] == "user"), None)
            assert user_message is not None
            assert "content" in user_message
            assert "created_at" in user_message
            
            logger.info(f"✅ Retrieved {len(messages)} messages from conversation")
        else:
            logger.warning("⚠️ No messages found in conversation")

    async def test_document_upload(self):
        """Test document upload functionality."""
        logger.info("🧪 Testing document upload...")
        
        if not self.access_token:
            await self.test_user_registration()
        
        # Create a test file
        test_content = b"This is a test policy document for API testing."
        test_filename = "test_policy.txt"
        
        # Use temporary file
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as temp_file:
            temp_file.write(test_content)
            temp_file.flush()
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            with open(temp_file.name, 'rb') as f:
                files = {"file": (test_filename, f, "text/plain")}
                data = {
                    "policy_id": str(uuid.uuid4()),
                    "document_type": "policy"
                }
                
                response = await self.client.post(
                    "/upload-document",
                    files=files,
                    data=data,
                    headers=headers
                )
        
        # Clean up temp file
        os.unlink(temp_file.name)
        
        assert response.status_code == 200
        
        upload_data = response.json()
        assert "document_id" in upload_data
        assert "file_path" in upload_data
        assert upload_data["original_filename"] == test_filename
        assert upload_data["file_size"] == len(test_content)
        
        self.uploaded_file_path = upload_data["file_path"]
        
        logger.info(f"✅ Document uploaded successfully: {upload_data['file_path']}")

    async def test_document_listing(self):
        """Test document listing functionality."""
        logger.info("🧪 Testing document listing...")
        
        if not self.access_token:
            await self.test_user_registration()
        
        # Test requires policy_id parameter
        policy_id = str(uuid.uuid4())
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = await self.client.get(
            f"/documents?policy_id={policy_id}",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        logger.info(f"✅ Document listing successful ({len(data)} documents)")

    async def test_document_download_permissions(self):
        """Test document download with permission checking."""
        logger.info("🧪 Testing document download permissions...")
        
        if not self.uploaded_file_path:
            await self.test_document_upload()
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = await self.client.get(
            f"/documents/{self.uploaded_file_path}/download",
            headers=headers,
            follow_redirects=False
        )
        
        # Should redirect to signed URL
        if response.status_code == 307:
            # Follow the redirect to check if signed URL works
            redirect_url = response.headers.get("location")
            assert redirect_url is not None
            assert "supabase" in redirect_url
            logger.info(f"✅ Document download redirect successful")
        elif response.status_code == 200:
            logger.info("✅ Document download direct access successful")
        else:
            logger.warning(f"⚠️ Document download returned status: {response.status_code}")

    async def test_authentication_failure(self):
        """Test authentication failure scenarios."""
        logger.info("🧪 Testing authentication failures...")
        
        # Test without token
        response = await self.client.get("/me")
        assert response.status_code == 401
        
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = await self.client.get("/me", headers=headers)
        assert response.status_code == 401
        
        # Test protected endpoint without auth
        response = await self.client.post("/chat", json={"message": "test"})
        assert response.status_code == 401
        
        logger.info("✅ Authentication failure scenarios working correctly")

    async def cleanup(self):
        """Clean up test data and close connections."""
        logger.info("🧹 Cleaning up test data...")
        
        try:
            # Note: In a real cleanup, we might want to delete the test user
            # and associated data, but for now we'll just close the client
            await self.client.aclose()
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def run_all_tests(self):
        """Run all API endpoint tests."""
        logger.info("🚀 Starting FastAPI Endpoint Integration Tests")
        logger.info("=" * 60)
        
        test_methods = [
            self.test_root_endpoint,
            self.test_health_endpoint,
            self.test_user_registration,
            self.test_get_current_user,
            self.test_chat_endpoint,
            self.test_conversation_continuation,
            self.test_get_conversations,
            self.test_get_conversation_messages,
            self.test_document_upload,
            self.test_document_listing,
            self.test_document_download_permissions,
            self.test_authentication_failure
        ]
        
        passed_tests = 0
        failed_tests = 0
        
        for test_method in test_methods:
            try:
                await test_method()
                passed_tests += 1
            except Exception as e:
                logger.error(f"❌ {test_method.__name__} failed: {str(e)}")
                failed_tests += 1
        
        logger.info("=" * 60)
        logger.info(f"📊 Test Results: {passed_tests} passed, {failed_tests} failed")
        
        if failed_tests == 0:
            logger.info("🎉 All FastAPI endpoint tests PASSED!")
            return True
        else:
            logger.error(f"❌ {failed_tests} tests FAILED!")
            return False


async def main():
    """Main test execution."""
    print("FastAPI Endpoint Integration Tests")
    print("=" * 50)
    
    # Check if API server is running
    test_client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=5.0)
    
    try:
        response = await test_client.get("/health")
        if response.status_code != 200:
            print("❌ API server is not responding correctly")
            print("Please ensure the FastAPI server is running with: python main.py")
            return False
    except httpx.ConnectError:
        print("❌ Cannot connect to API server")
        print("Please start the FastAPI server with: python main.py")
        return False
    finally:
        await test_client.aclose()
    
    # Run the comprehensive test suite
    test_suite = FastAPIEndpointTests()
    
    try:
        await test_suite.setup()
        success = await test_suite.run_all_tests()
        return success
    
    except Exception as e:
        logger.error(f"❌ Test suite failed: {str(e)}")
        return False
    
    finally:
        await test_suite.cleanup()


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1) 