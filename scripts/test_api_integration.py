#!/usr/bin/env python3
"""
API Integration Test Script

Comprehensive script to test the FastAPI integration with database services.
Handles setup, server startup verification, and comprehensive testing.
"""

import os
import sys
import asyncio
import subprocess
import signal
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIIntegrationTester:
    """Handles comprehensive API integration testing."""

    def __init__(self):
        self.server_process = None
        self.project_root = Path(__file__).parent.parent

    async def verify_environment(self):
        """Verify that the environment is properly configured."""
        logger.info("🔍 Verifying environment configuration...")
        
        # Check for .env file
        env_file = self.project_root / ".env"
        if not env_file.exists():
            logger.error("❌ .env file not found!")
            logger.info("Please copy .env.template to .env and configure your settings")
            return False
        
        # Check required environment variables
        required_vars = [
            'SUPABASE_URL',
            'SUPABASE_SERVICE_ROLE_KEY',
            'DATABASE_URL'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            return False
        
        logger.info("✅ Environment configuration verified")
        return True

    async def test_database_connectivity(self):
        """Test database connectivity before starting API tests."""
        logger.info("🗄️ Testing database connectivity...")
        
        try:
            from db.services.db_pool import get_db_pool
            
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                result = await conn.fetchval("SELECT 1")
                assert result == 1
            
            logger.info("✅ Database connectivity verified")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connectivity failed: {e}")
            return False

    def start_api_server(self):
        """Start the FastAPI server in background."""
        logger.info("🚀 Starting FastAPI server...")
        
        try:
            # Start server process
            cmd = [
                sys.executable, 
                str(self.project_root / "main.py")
            ]
            
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.project_root
            )
            
            # Wait a moment for server to start
            time.sleep(3)
            
            # Check if process is still running
            if self.server_process.poll() is None:
                logger.info("✅ API server started successfully")
                return True
            else:
                stdout, stderr = self.server_process.communicate()
                logger.error(f"❌ API server failed to start")
                logger.error(f"STDOUT: {stdout.decode()}")
                logger.error(f"STDERR: {stderr.decode()}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to start API server: {e}")
            return False

    def stop_api_server(self):
        """Stop the FastAPI server."""
        if self.server_process:
            logger.info("🛑 Stopping API server...")
            
            try:
                # Send SIGTERM
                self.server_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    self.server_process.kill()
                    self.server_process.wait()
                
                logger.info("✅ API server stopped")
                
            except Exception as e:
                logger.error(f"Error stopping server: {e}")

    async def run_integration_tests(self):
        """Run the comprehensive integration test suite."""
        logger.info("🧪 Running API integration tests...")
        
        try:
            # Import and run the test suite
            from tests.integration.test_fastapi_endpoints import main as run_endpoint_tests
            
            # Run the tests
            success = await run_endpoint_tests()
            
            if success:
                logger.info("✅ All integration tests passed!")
                return True
            else:
                logger.error("❌ Some integration tests failed!")
                return False
                
        except Exception as e:
            logger.error(f"❌ Integration test execution failed: {e}")
            return False

    async def run_comprehensive_test(self):
        """Run the complete integration test workflow."""
        logger.info("🎯 Starting Comprehensive API Integration Test")
        logger.info("=" * 60)
        
        try:
            # Step 1: Verify environment
            if not await self.verify_environment():
                return False
            
            # Step 2: Test database connectivity
            if not await self.test_database_connectivity():
                return False
            
            # Step 3: Start API server
            if not self.start_api_server():
                return False
            
            # Wait a bit more for server to be fully ready
            time.sleep(2)
            
            # Step 4: Run integration tests
            success = await self.run_integration_tests()
            
            logger.info("=" * 60)
            
            if success:
                logger.info("🎉 Comprehensive API Integration Test PASSED!")
                logger.info("✅ FastAPI application is fully integrated with database services")
                logger.info("✅ Authentication, chat, and storage endpoints are working")
                logger.info("✅ Database persistence is functioning correctly")
                return True
            else:
                logger.error("❌ Comprehensive API Integration Test FAILED!")
                logger.error("Please check the test output above for specific failures")
                return False
            
        except Exception as e:
            logger.error(f"❌ Comprehensive test failed: {e}")
            return False
        
        finally:
            # Always stop the server
            self.stop_api_server()

    def print_test_summary(self):
        """Print a summary of what was tested."""
        print("\n" + "=" * 60)
        print("📋 INTEGRATION TEST SUMMARY")
        print("=" * 60)
        print("✅ Environment Configuration")
        print("✅ Database Connectivity (Supabase PostgreSQL)")
        print("✅ User Service Integration")
        print("✅ Conversation Service Integration") 
        print("✅ Storage Service Integration")
        print("✅ FastAPI Endpoint Testing:")
        print("   • User registration and authentication")
        print("   • JWT token validation")
        print("   • Chat endpoint with conversation persistence")
        print("   • Document upload and download")
        print("   • Permission-based access control")
        print("   • Error handling and security")
        print("=" * 60)


async def main():
    """Main test execution."""
    print("Insurance Navigator - API Integration Test")
    print("=" * 50)
    
    tester = APIIntegrationTester()
    
    try:
        success = await tester.run_comprehensive_test()
        
        if success:
            tester.print_test_summary()
            print("\n🎉 API Integration is working perfectly!")
            print("✅ Ready for frontend integration and production deployment")
        else:
            print("\n❌ API Integration has issues that need to be resolved")
            print("Please check the logs above for specific error details")
        
        return success
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        tester.stop_api_server()
        return False
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        tester.stop_api_server()
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1) 