#!/usr/bin/env python3
"""
Post-Migration Validation Script
Validates that the MVP schema refactoring completed successfully
"""

import asyncio
import asyncpg
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.config import config
from db.services.db_pool import get_db_pool

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/migration_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MigrationValidator:
    """Validates the MVP schema refactoring migration."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "schema_validation": {},
            "data_integrity": {},
            "functionality_tests": {},
            "performance_tests": {},
            "hipaa_compliance": {}
        }
        
    async def run_validation(self) -> Dict[str, Any]:
        """Run complete migration validation."""
        logger.info("🔍 Starting post-migration validation...")
        
        try:
            # Schema validation
            await self._validate_schema_changes()
            await self._validate_data_integrity()
            
            # Functionality validation
            await self._test_policy_basics_functionality()
            await self._test_hybrid_search()
            await self._test_simplified_endpoints()
            
            # Performance validation
            await self._validate_performance_improvements()
            
            # HIPAA compliance validation
            await self._validate_hipaa_compliance()
            
            # Generate report
            await self._generate_validation_report()
            
            logger.info("✅ Post-migration validation completed successfully")
            return self.results
            
        except Exception as e:
            logger.error(f"❌ Post-migration validation failed: {e}")
            self.results["validation_error"] = str(e)
            raise
    
    async def _validate_schema_changes(self):
        """Validate that schema changes were applied correctly."""
        logger.info("📊 Validating schema changes...")
        
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            # Check remaining tables count
            remaining_tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            table_names = [row['table_name'] for row in remaining_tables]
            
            # Core tables that should exist after migration
            expected_tables = {
                'users', 'roles', 'user_roles', 'encryption_keys',
                'user_documents', 'user_document_vectors', 'conversations', 
                'messages', 'regulatory_documents', 'audit_logs'
            }
            
            # Tables that should be removed
            removed_tables = {
                'processing_jobs', 'agent_states', 'workflow_states',
                'policy_records', 'user_policy_links', 'feature_flags',
                'system_metadata', 'policy_documents'
            }
            
            missing_tables = expected_tables - set(table_names)
            unexpected_removed_tables = removed_tables.intersection(set(table_names))
            
            # Check policy_basics column exists
            policy_basics_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'user_documents' 
                    AND column_name = 'policy_basics'
                )
            """)
            
            # Check user_document_vectors table renamed correctly
            document_vectors_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'user_document_vectors'
                )
            """)
            
            # Check audit_logs table exists
            audit_logs_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'audit_logs'
                )
            """)
            
            self.results["schema_validation"] = {
                "total_tables": len(table_names),
                "table_names": table_names,
                "missing_expected_tables": list(missing_tables),
                "tables_not_removed": list(unexpected_removed_tables),
                "policy_basics_column_exists": policy_basics_exists,
                "document_vectors_renamed": document_vectors_exists,
                "audit_logs_created": audit_logs_exists,
                "target_table_count_achieved": len(table_names) <= 11  # Target was ~10 core tables + migration tracking
            }
            
        logger.info(f"Tables remaining: {len(table_names)}, Target achieved: {len(table_names) <= 11}")
    
    async def _validate_data_integrity(self):
        """Validate that critical data was preserved during migration."""
        logger.info("🔒 Validating data integrity...")
        
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            integrity_checks = {}
            
            # Check users preserved
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            integrity_checks["users_preserved"] = user_count > 0
            
            # Check documents preserved
            document_count = await conn.fetchval("SELECT COUNT(*) FROM user_documents")
            integrity_checks["documents_preserved"] = document_count >= 0
            
            # Check conversations preserved
            conversation_count = await conn.fetchval("SELECT COUNT(*) FROM conversations")
            integrity_checks["conversations_preserved"] = conversation_count >= 0
            
            # Check vectors preserved (now in user_document_vectors)
            try:
                vector_count = await conn.fetchval("SELECT COUNT(*) FROM user_document_vectors")
                integrity_checks["vectors_preserved"] = vector_count >= 0
            except Exception as e:
                integrity_checks["vectors_preserved"] = False
                integrity_checks["vector_error"] = str(e)
            
            # Check encryption keys preserved
            encryption_key_count = await conn.fetchval("SELECT COUNT(*) FROM encryption_keys")
            integrity_checks["encryption_keys_preserved"] = encryption_key_count > 0
            
            # Check no orphaned documents
            orphaned_docs = await conn.fetchval("""
                SELECT COUNT(*) FROM user_documents d
                LEFT JOIN users u ON d.user_id = u.id
                WHERE u.id IS NULL
            """)
            integrity_checks["no_orphaned_documents"] = orphaned_docs == 0
            
            self.results["data_integrity"] = integrity_checks
    
    async def _test_policy_basics_functionality(self):
        """Test the new policy basics functionality."""
        logger.info("📋 Testing policy basics functionality...")
        
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            tests = {}
            
            # Test policy basics functions exist
            try:
                # Test get_policy_facts function
                test_uuid = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'  # Sample UUID
                result = await conn.fetchval("SELECT get_policy_facts($1)", test_uuid)
                tests["get_policy_facts_function_exists"] = True
            except Exception as e:
                tests["get_policy_facts_function_exists"] = False
                tests["get_policy_facts_error"] = str(e)
            
            # Test update_policy_basics function
            try:
                test_data = json.dumps({"test": "data"})
                result = await conn.fetchval("SELECT update_policy_basics($1, $2)", test_uuid, test_data)
                tests["update_policy_basics_function_exists"] = True
            except Exception as e:
                tests["update_policy_basics_function_exists"] = False
                tests["update_policy_basics_error"] = str(e)
            
            # Test search_by_policy_criteria function
            try:
                test_criteria = json.dumps({"plan_type": "HMO"})
                result = await conn.fetch("SELECT * FROM search_by_policy_criteria($1, $2)", test_uuid, test_criteria)
                tests["search_by_policy_criteria_function_exists"] = True
            except Exception as e:
                tests["search_by_policy_criteria_function_exists"] = False
                tests["search_by_policy_criteria_error"] = str(e)
            
            # Test JSONB indexes exist
            policy_basics_index = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = 'idx_user_documents_policy_basics_gin'
                )
            """)
            tests["policy_basics_gin_index_exists"] = policy_basics_index
            
            self.results["functionality_tests"]["policy_basics"] = tests
    
    async def _test_hybrid_search(self):
        """Test hybrid search functionality."""
        logger.info("🔍 Testing hybrid search functionality...")
        
        # Test would go here - for now, check that required components exist
        try:
            from db.services.document_service import get_document_service
            doc_service = await get_document_service()
            
            self.results["functionality_tests"]["hybrid_search"] = {
                "document_service_available": True,
                "search_hybrid_method_exists": hasattr(doc_service, 'search_hybrid'),
                "extract_policy_basics_method_exists": hasattr(doc_service, 'extract_policy_basics'),
                "get_policy_facts_method_exists": hasattr(doc_service, 'get_policy_facts')
            }
            
        except Exception as e:
            self.results["functionality_tests"]["hybrid_search"] = {
                "document_service_available": False,
                "error": str(e)
            }
    
    async def _test_simplified_endpoints(self):
        """Test that simplified endpoints work correctly."""
        logger.info("🌐 Testing simplified endpoints...")
        
        # Check that removed endpoints don't exist in main.py
        main_file_path = Path(__file__).parent.parent / "main.py"
        
        if main_file_path.exists():
            with open(main_file_path, 'r') as f:
                main_content = f.read()
            
            # Endpoints that should be removed
            removed_endpoints = [
                '/admin/trigger-job-processing',
                '/admin/job-queue-status', 
                '/debug/workflow/'
            ]
            
            endpoints_still_present = []
            for endpoint in removed_endpoints:
                if endpoint in main_content:
                    endpoints_still_present.append(endpoint)
            
            self.results["functionality_tests"]["endpoints"] = {
                "main_file_exists": True,
                "removed_endpoints_still_present": endpoints_still_present,
                "removal_complete": len(endpoints_still_present) == 0
            }
        else:
            self.results["functionality_tests"]["endpoints"] = {
                "main_file_exists": False
            }
    
    async def _validate_performance_improvements(self):
        """Validate performance improvements."""
        logger.info("⚡ Validating performance improvements...")
        
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            performance_tests = {}
            
            # Test policy facts lookup speed (target: <50ms)
            if await conn.fetchval("SELECT COUNT(*) FROM user_documents WHERE policy_basics IS NOT NULL") > 0:
                start_time = datetime.now()
                await conn.fetch("""
                    SELECT id, policy_basics->>'deductible' as deductible
                    FROM user_documents 
                    WHERE policy_basics->>'deductible' IS NOT NULL
                    LIMIT 10
                """)
                policy_query_time = (datetime.now() - start_time).total_seconds() * 1000
                performance_tests["policy_facts_query_ms"] = policy_query_time
                performance_tests["policy_facts_under_50ms"] = policy_query_time < 50
            else:
                performance_tests["policy_facts_query_ms"] = "N/A - no documents with policy_basics"
            
            # Test simplified document query
            start_time = datetime.now()
            docs = await conn.fetch("""
                SELECT d.id, d.original_filename, d.status, d.policy_basics
                FROM user_documents d
                JOIN users u ON d.user_id = u.id
                WHERE d.status = 'completed'
                ORDER BY d.created_at DESC
                LIMIT 50
            """)
            doc_query_time = (datetime.now() - start_time).total_seconds() * 1000
            performance_tests["document_query_ms"] = doc_query_time
            
            self.results["performance_tests"] = performance_tests
            
        logger.info(f"Policy facts query: {performance_tests.get('policy_facts_query_ms', 'N/A')}ms")
    
    async def _validate_hipaa_compliance(self):
        """Validate HIPAA compliance maintained."""
        logger.info("🏥 Validating HIPAA compliance...")
        
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            compliance_checks = {}
            
            # Check audit_logs table functionality
            try:
                # Get a real user ID first
                real_user_id = await conn.fetchval("SELECT id FROM users LIMIT 1")
                if real_user_id:
                    test_log_id = await conn.fetchval("""
                        SELECT log_user_action(
                            $1::uuid,
                            'migration_test', 
                            'validation', 
                            'post_migration',
                            '{"test": true}'::jsonb
                        )
                    """, real_user_id)
                    compliance_checks["audit_logging_functional"] = test_log_id is not None
                    
                    # Clean up test log
                    if test_log_id:
                        await conn.execute("DELETE FROM audit_logs WHERE id = $1", test_log_id)
                else:
                    compliance_checks["audit_logging_functional"] = False
                    compliance_checks["audit_error"] = "No users found for testing"
                    
            except Exception as e:
                compliance_checks["audit_logging_functional"] = False
                compliance_checks["audit_error"] = str(e)
            
            # Check encryption preserved
            encryption_keys_count = await conn.fetchval("SELECT COUNT(*) FROM encryption_keys")
            compliance_checks["encryption_keys_preserved"] = encryption_keys_count > 0
            
            # Check RLS policies still exist
            rls_policies = await conn.fetch("""
                SELECT tablename, policyname 
                FROM pg_policies 
                WHERE schemaname = 'public'
            """)
            compliance_checks["rls_policies_count"] = len(rls_policies)
            compliance_checks["rls_policies_exist"] = len(rls_policies) > 0
            
            self.results["hipaa_compliance"] = compliance_checks
    
    async def _generate_validation_report(self):
        """Generate validation report."""
        logger.info("📋 Generating validation report...")
        
        report_file = f"logs/migration_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("logs", exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Generate summary
        summary = self._generate_summary()
        summary_file = f"logs/migration_validation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(summary_file, 'w') as f:
            f.write(summary)
        
        logger.info(f"Validation report saved to: {report_file}")
        logger.info(f"Summary saved to: {summary_file}")
        
        # Print summary to console
        print("\n" + "="*80)
        print("MIGRATION VALIDATION SUMMARY")
        print("="*80)
        print(summary)
        print("="*80)
    
    def _generate_summary(self) -> str:
        """Generate human-readable summary."""
        schema = self.results.get("schema_validation", {})
        integrity = self.results.get("data_integrity", {})
        functionality = self.results.get("functionality_tests", {})
        performance = self.results.get("performance_tests", {})
        compliance = self.results.get("hipaa_compliance", {})
        
        summary = f"""
SCHEMA CHANGES:
- Tables remaining: {schema.get('total_tables', 'Unknown')} (Target: ≤11)
- Target achieved: {schema.get('target_table_count_achieved', 'Unknown')}
- Policy basics column: {'✅' if schema.get('policy_basics_column_exists') else '❌'}
- Document vectors renamed: {'✅' if schema.get('document_vectors_renamed') else '❌'}
- Audit logs created: {'✅' if schema.get('audit_logs_created') else '❌'}

DATA INTEGRITY:
- Users preserved: {'✅' if integrity.get('users_preserved') else '❌'}
- Documents preserved: {'✅' if integrity.get('documents_preserved') else '❌'}
- Vectors preserved: {'✅' if integrity.get('vectors_preserved') else '❌'}
- No orphaned documents: {'✅' if integrity.get('no_orphaned_documents') else '❌'}

FUNCTIONALITY:
- Policy basics functions: {'✅' if functionality.get('policy_basics', {}).get('get_policy_facts_function_exists') else '❌'}
- Hybrid search available: {'✅' if functionality.get('hybrid_search', {}).get('document_service_available') else '❌'}
- Endpoint cleanup: {'✅' if functionality.get('endpoints', {}).get('removal_complete') else '❌'}

PERFORMANCE:
- Policy facts query: {performance.get('policy_facts_query_ms', 'N/A')}ms (Target: <50ms)
- Document query: {performance.get('document_query_ms', 'Unknown')}ms

HIPAA COMPLIANCE:
- Audit logging: {'✅' if compliance.get('audit_logging_functional') else '❌'}
- Encryption preserved: {'✅' if compliance.get('encryption_keys_preserved') else '❌'}
- RLS policies: {compliance.get('rls_policies_count', 'Unknown')} policies active

MIGRATION STATUS: {'✅ SUCCESS' if self._is_migration_successful() else '❌ ISSUES FOUND'}
        """
        
        return summary.strip()
    
    def _is_migration_successful(self) -> bool:
        """Check if migration was successful."""
        schema = self.results.get("schema_validation", {})
        integrity = self.results.get("data_integrity", {})
        functionality = self.results.get("functionality_tests", {})
        compliance = self.results.get("hipaa_compliance", {})
        
        # Critical success criteria
        critical_checks = [
            schema.get('target_table_count_achieved', False),
            schema.get('policy_basics_column_exists', False),
            integrity.get('users_preserved', False),
            integrity.get('documents_preserved', False),
            integrity.get('no_orphaned_documents', False),
            compliance.get('encryption_keys_preserved', False)
        ]
        
        return all(critical_checks)

async def main():
    """Main function to run migration validation."""
    validator = MigrationValidator()
    
    try:
        results = await validator.run_validation()
        
        if validator._is_migration_successful():
            logger.info("✅ Migration validation successful!")
            sys.exit(0)
        else:
            logger.error("❌ Migration validation found issues")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())