#!/usr/bin/env python3
"""
Supabase Database Integration Setup Script

This script sets up the complete Supabase database integration:
1. Tests database connectivity
2. Runs all migrations in order
3. Validates agent integration
4. Tests conversation service
5. Provides setup verification

Best Practice: Run this script after configuring your .env file with Supabase credentials
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SupabaseIntegrationSetup:
    """Handles complete Supabase integration setup and validation."""
    
    def __init__(self):
        self.setup_results = {
            "environment_check": False,
            "database_connection": False,
            "migrations_executed": False,
            "user_service_tested": False,
            "conversation_service_tested": False,
            "orchestrator_integration": False,
            "overall_success": False
        }
    
    async def run_complete_setup(self) -> Dict[str, Any]:
        """Run the complete Supabase integration setup."""
        print("🚀 Starting Supabase Database Integration Setup")
        print("=" * 50)
        
        try:
            # Step 1: Environment validation
            print("\n1️⃣ Validating Environment Configuration...")
            await self._validate_environment()
            
            # Step 2: Database connection test
            print("\n2️⃣ Testing Database Connection...")
            await self._test_database_connection()
            
            # Step 3: Run migrations
            print("\n3️⃣ Executing Database Migrations...")
            await self._run_migrations()
            
            # Step 4: Test user service
            print("\n4️⃣ Testing User Service Integration...")
            await self._test_user_service()
            
            # Step 5: Test conversation service
            print("\n5️⃣ Testing Conversation Service...")
            await self._test_conversation_service()
            
            # Step 6: Test orchestrator integration
            print("\n6️⃣ Testing Agent Orchestrator Integration...")
            await self._test_orchestrator_integration()
            
            # Final validation
            print("\n7️⃣ Final Integration Validation...")
            self._validate_overall_setup()
            
            # Print results
            self._print_setup_summary()
            
            return self.setup_results
            
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            print(f"\n❌ Setup failed with error: {str(e)}")
            self.setup_results["overall_success"] = False
            return self.setup_results
    
    async def _validate_environment(self) -> None:
        """Validate environment configuration."""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            required_vars = [
                "DATABASE_URL",
                "SUPABASE_URL", 
                "SUPABASE_ANON_KEY",
                "SUPABASE_SERVICE_ROLE_KEY",
                "JWT_SECRET_KEY"
            ]
            
            missing_vars = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                raise ValueError(f"Missing required environment variables: {missing_vars}")
            
            print("✅ Environment configuration validated")
            self.setup_results["environment_check"] = True
            
        except Exception as e:
            print(f"❌ Environment validation failed: {e}")
            raise
    
    async def _test_database_connection(self) -> None:
        """Test database connectivity."""
        try:
            from db.services.db_pool import get_db_pool
            
            pool = await get_db_pool()
            connection_test = await pool.test_connection()
            
            if not connection_test:
                raise Exception("Database connection test failed")
            
            print("✅ Database connection successful")
            self.setup_results["database_connection"] = True
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
    
    async def _run_migrations(self) -> None:
        """Execute database migrations."""
        try:
            from db.scripts.run_migrations import run_migrations, get_migration_status
            
            # Check current migration status
            status = await get_migration_status()
            print(f"📋 Migration status: {status['status']}")
            
            if status.get('pending_migrations'):
                print(f"🔄 Running {len(status['pending_migrations'])} pending migrations...")
                results = await run_migrations()
                
                print(f"✅ Executed: {len(results['executed'])} migrations")
                print(f"⏭️  Skipped: {len(results['skipped'])} migrations")
                
                if results['failed']:
                    print(f"❌ Failed: {len(results['failed'])} migrations")
                    for failure in results['failed']:
                        print(f"   - {failure['name']}: {failure['error']}")
                    raise Exception("Some migrations failed")
                
            else:
                print("✅ All migrations already executed")
            
            self.setup_results["migrations_executed"] = True
            
        except Exception as e:
            print(f"❌ Migration execution failed: {e}")
            raise
    
    async def _test_user_service(self) -> None:
        """Test user service functionality."""
        try:
            from db.services.user_service import get_user_service
            
            user_service = await get_user_service()
            
            # Test user creation (with cleanup)
            test_email = "test_setup@example.com"
            
            # Clean up any existing test user
            existing_user = await user_service.get_user_by_email(test_email)
            if existing_user:
                print("🧹 Cleaning up existing test user...")
            
            # Create test user
            test_user = await user_service.create_user(
                email=test_email,
                password="test_password_123!",
                full_name="Test Setup User",
                metadata={"test": True}
            )
            
            # Test authentication
            auth_user = await user_service.authenticate_user(test_email, "test_password_123!")
            if not auth_user:
                raise Exception("User authentication failed")
            
            # Test token creation
            token = user_service.create_access_token(auth_user)
            if not token:
                raise Exception("Token creation failed")
            
            # Validate token
            payload = user_service.verify_token(token)
            if payload.get("sub") != test_email:
                raise Exception("Token validation failed")
            
            print("✅ User service integration successful")
            self.setup_results["user_service_tested"] = True
            
        except Exception as e:
            print(f"❌ User service test failed: {e}")
            raise
    
    async def _test_conversation_service(self) -> None:
        """Test conversation service functionality."""
        try:
            from db.services.conversation_service import get_conversation_service
            import uuid
            
            conversation_service = await get_conversation_service()
            
            # Test conversation creation
            test_user_id = str(uuid.uuid4())
            test_conversation_id = f"test_setup_{uuid.uuid4().hex[:8]}"
            
            conversation_id = await conversation_service.create_conversation(
                user_id=test_user_id,
                conversation_id=test_conversation_id,
                metadata={"test": "setup_validation"}
            )
            
            # Test message addition
            await conversation_service.add_message(
                conversation_id=conversation_id,
                role="user",
                content="Test setup message",
                agent_name="setup_test"
            )
            
            # Test conversation history
            history = await conversation_service.get_conversation_history(
                conversation_id=conversation_id,
                limit=10
            )
            
            if not history or len(history) == 0:
                raise Exception("Conversation history retrieval failed")
            
            # Test agent state persistence
            await conversation_service.save_agent_state(
                conversation_id=conversation_id,
                agent_name="test_agent",
                state_data={"test": "state_data"},
                workflow_step="test_step"
            )
            
            state = await conversation_service.get_agent_state(
                conversation_id=conversation_id,
                agent_name="test_agent"
            )
            
            if not state or state.get("state_data", {}).get("test") != "state_data":
                raise Exception("Agent state persistence failed")
            
            # Cleanup test conversation
            await conversation_service.delete_conversation(
                conversation_id=conversation_id,
                user_id=test_user_id
            )
            
            print("✅ Conversation service integration successful")
            self.setup_results["conversation_service_tested"] = True
            
        except Exception as e:
            print(f"❌ Conversation service test failed: {e}")
            raise
    
    async def _test_orchestrator_integration(self) -> None:
        """Test agent orchestrator integration with database."""
        try:
            from graph.agent_orchestrator import get_orchestrator
            import uuid
            
            orchestrator = get_orchestrator()
            
            # Test simple workflow
            test_user_id = str(uuid.uuid4())
            test_message = "Test setup message for orchestrator"
            
            result = await orchestrator.process_message(
                message=test_message,
                user_id=test_user_id
            )
            
            if not result or "text" not in result:
                raise Exception("Orchestrator workflow failed")
            
            # Verify conversation was created in database
            conversation_id = result.get("conversation_id")
            if not conversation_id:
                raise Exception("No conversation ID returned from orchestrator")
            
            from db.services.conversation_service import get_conversation_service
            conversation_service = await get_conversation_service()
            
            history = await conversation_service.get_conversation_history(
                conversation_id=conversation_id,
                limit=5
            )
            
            if not history:
                raise Exception("Orchestrator did not persist conversation")
            
            print("✅ Agent orchestrator integration successful")
            self.setup_results["orchestrator_integration"] = True
            
        except Exception as e:
            print(f"❌ Orchestrator integration test failed: {e}")
            raise
    
    def _validate_overall_setup(self) -> None:
        """Validate overall setup completion."""
        required_components = [
            "environment_check",
            "database_connection", 
            "migrations_executed",
            "user_service_tested",
            "conversation_service_tested",
            "orchestrator_integration"
        ]
        
        success_count = sum(1 for component in required_components 
                          if self.setup_results.get(component, False))
        
        if success_count == len(required_components):
            self.setup_results["overall_success"] = True
            print("✅ All integration components validated successfully")
        else:
            failed_components = [comp for comp in required_components 
                               if not self.setup_results.get(comp, False)]
            print(f"❌ Integration validation failed. Missing: {failed_components}")
    
    def _print_setup_summary(self) -> None:
        """Print comprehensive setup summary."""
        print("\n" + "=" * 50)
        print("📋 SUPABASE INTEGRATION SETUP SUMMARY")
        print("=" * 50)
        
        components = [
            ("Environment Configuration", "environment_check"),
            ("Database Connection", "database_connection"),
            ("Migration Execution", "migrations_executed"),
            ("User Service", "user_service_tested"),
            ("Conversation Service", "conversation_service_tested"),
            ("Orchestrator Integration", "orchestrator_integration")
        ]
        
        for name, key in components:
            status = "✅ PASS" if self.setup_results.get(key, False) else "❌ FAIL"
            print(f"{name:<25}: {status}")
        
        print("-" * 50)
        overall_status = "🎉 SUCCESS" if self.setup_results["overall_success"] else "💥 FAILED"
        print(f"{'Overall Setup':<25}: {overall_status}")
        
        if self.setup_results["overall_success"]:
            print("\n🎉 Supabase integration setup completed successfully!")
            print("✅ Your Insurance Navigator system is ready for production use.")
            print("\n📝 Next Steps:")
            print("   1. Update your frontend to use the new async API endpoints")
            print("   2. Configure production environment variables")
            print("   3. Test end-to-end workflows with real user scenarios")
            print("   4. Monitor conversation persistence and agent state management")
        else:
            print("\n💥 Setup failed. Please address the failed components above.")
            print("📖 Check the logs for detailed error information.")
            print("🔧 Ensure your .env file has all required Supabase credentials.")


async def main():
    """Main setup function."""
    setup = SupabaseIntegrationSetup()
    results = await setup.run_complete_setup()
    
    # Exit with appropriate code
    exit_code = 0 if results["overall_success"] else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main()) 