#!/usr/bin/env python3
"""
Complete Vector Migration Execution Script

This script handles the full migration process from traditional relational schema
to vector-first architecture for the insurance policy management system.

Usage:
    python db/scripts/run_vector_migration.py [--dry-run] [--skip-migration] [--force]
    
Options:
    --dry-run: Run migration checks without making changes
    --skip-migration: Skip schema migration (if already run)
    --force: Force migration even if checks fail
"""

import asyncio
import argparse
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from db.services.db_pool import get_db_pool

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / 'logs' / 'vector_migration.log')
    ]
)
logger = logging.getLogger(__name__)

class VectorMigrationExecutor:
    """Executes the complete vector migration process."""
    
    def __init__(self, dry_run: bool = False, skip_migration: bool = False, force: bool = False):
        self.dry_run = dry_run
        self.skip_migration = skip_migration
        self.force = force
        self.migration_log = []
        
    async def run_complete_migration(self) -> Dict[str, Any]:
        """Execute the complete migration process."""
        
        logger.info("=" * 80)
        logger.info("STARTING VECTOR MIGRATION PROCESS")
        logger.info("=" * 80)
        
        if self.dry_run:
            logger.info("🔍 Running in DRY RUN mode - no changes will be made")
        
        try:
            # Step 1: Pre-migration checks
            logger.info("Step 1: Running pre-migration checks...")
            checks_passed = await self._run_pre_migration_checks()
            
            if not checks_passed and not self.force:
                logger.error("❌ Pre-migration checks failed. Use --force to override.")
                return {"success": False, "error": "Pre-migration checks failed"}
            
            # Step 2: Backup existing data
            logger.info("Step 2: Creating data backup...")
            backup_info = await self._create_backup()
            
            # Step 3: Run schema migration
            if not self.skip_migration:
                logger.info("Step 3: Running schema migration...")
                schema_result = await self._run_schema_migration()
                if not schema_result and not self.force:
                    logger.error("❌ Schema migration failed.")
                    return {"success": False, "error": "Schema migration failed"}
            else:
                logger.info("Step 3: Skipping schema migration (--skip-migration flag)")
            
            # Step 4: Test vector services
            logger.info("Step 4: Testing vector services...")
            services_working = await self._test_vector_services()
            if not services_working and not self.force:
                logger.error("❌ Vector services test failed.")
                return {"success": False, "error": "Vector services not working"}
            
            # Step 5: Data migration
            if not self.dry_run:
                logger.info("Step 5: Running data migration...")
                from migrate_to_vectors import VectorMigrationManager
                
                migration_manager = VectorMigrationManager()
                await migration_manager.initialize()
                await migration_manager.migrate_policy_data()
                migration_report = await migration_manager.create_migration_report()
            else:
                logger.info("Step 5: Skipping data migration (dry run)")
                migration_report = {"note": "Skipped due to dry run"}
            
            # Step 6: Validation
            logger.info("Step 6: Running post-migration validation...")
            validation_results = await self._run_post_migration_validation()
            
            # Step 7: Final report
            final_report = await self._create_final_report(
                backup_info, migration_report, validation_results
            )
            
            logger.info("=" * 80)
            logger.info("✅ VECTOR MIGRATION COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)
            
            return {"success": True, "report": final_report}
            
        except Exception as e:
            logger.error(f"❌ Migration failed with error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _run_pre_migration_checks(self) -> bool:
        """Run comprehensive pre-migration checks."""
        checks_passed = True
        
        try:
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                
                # Check 1: Database connection
                logger.info("  ✓ Database connection test...")
                await conn.fetchval("SELECT 1")
                
                # Check 2: Required extensions
                logger.info("  ✓ Checking PostgreSQL extensions...")
                extensions = await conn.fetch("SELECT extname FROM pg_extension")
                extension_names = [ext['extname'] for ext in extensions]
                
                if 'vector' not in extension_names:
                    logger.warning("  ⚠️  pgvector extension not found - will be installed during migration")
                
                # Check 3: Current schema state
                logger.info("  ✓ Checking current schema...")
                tables = await conn.fetch("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                table_names = [table['table_name'] for table in tables]
                
                legacy_tables = ['policy_records', 'policy_documents']
                vector_tables = ['policy_content_vectors', 'user_document_vectors']
                
                legacy_exists = any(table in table_names for table in legacy_tables)
                vector_exists = any(table in table_names for table in vector_tables)
                
                if vector_exists and not self.force:
                    logger.warning("  ⚠️  Vector tables already exist - migration may have been run before")
                
                if not legacy_exists:
                    logger.warning("  ⚠️  Legacy tables not found - nothing to migrate")
                
                # Check 4: Data volume estimation
                logger.info("  ✓ Estimating data volume...")
                if 'policy_records' in table_names:
                    policy_count = await conn.fetchval("SELECT COUNT(*) FROM policy_records")
                    logger.info(f"     Found {policy_count} policy records to migrate")
                
                if 'policy_documents' in table_names:
                    doc_count = await conn.fetchval("SELECT COUNT(*) FROM policy_documents")
                    logger.info(f"     Found {doc_count} policy documents to migrate")
                
                # Check 5: Disk space
                logger.info("  ✓ Checking disk space...")
                db_size = await conn.fetchval("SELECT pg_size_pretty(pg_database_size(current_database()))")
                logger.info(f"     Current database size: {db_size}")
                
                # Check 6: Python dependencies
                logger.info("  ✓ Checking Python dependencies...")
                try:
                    import sentence_transformers
                    import langchain
                    import pgvector
                    logger.info("     All required packages available")
                except ImportError as e:
                    logger.error(f"     Missing required package: {e}")
                    checks_passed = False
                
                self.migration_log.append({
                    "step": "pre_migration_checks",
                    "status": "completed" if checks_passed else "failed",
                    "details": {
                        "legacy_tables_exist": legacy_exists,
                        "vector_tables_exist": vector_exists,
                        "policy_count": policy_count if 'policy_records' in table_names else 0,
                        "document_count": doc_count if 'policy_documents' in table_names else 0
                    }
                })
                
                return checks_passed
                
        except Exception as e:
            logger.error(f"  ❌ Pre-migration checks failed: {str(e)}")
            return False
    
    async def _create_backup(self) -> Dict[str, Any]:
        """Create backup of existing data."""
        try:
            if self.dry_run:
                logger.info("  📋 Dry run: Would create data backup")
                return {"note": "Backup skipped in dry run"}
            
            # Create backup directory
            backup_dir = project_root / 'db' / 'backups'
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"pre_vector_migration_{timestamp}.sql"
            
            # Use pg_dump to create backup
            import subprocess
            import os
            
            # Get database connection info from environment or config
            db_url = os.getenv('DATABASE_URL', '')
            if db_url:
                cmd = f"pg_dump {db_url} > {backup_file}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"  ✅ Backup created: {backup_file}")
                    return {"backup_file": str(backup_file), "success": True}
                else:
                    logger.warning(f"  ⚠️  Backup failed: {result.stderr}")
                    return {"success": False, "error": result.stderr}
            else:
                logger.warning("  ⚠️  No DATABASE_URL found - skipping automatic backup")
                return {"success": False, "error": "No DATABASE_URL configured"}
                
        except Exception as e:
            logger.warning(f"  ⚠️  Backup creation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _run_schema_migration(self) -> bool:
        """Run the schema migration."""
        try:
            if self.dry_run:
                logger.info("  📋 Dry run: Would run schema migration")
                return True
            
            migration_file = project_root / 'db' / 'migrations' / '008_vector_consolidation.sql'
            
            if not migration_file.exists():
                logger.error(f"  ❌ Migration file not found: {migration_file}")
                return False
            
            # Read and execute migration
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                await conn.execute(migration_sql)
                logger.info("  ✅ Schema migration completed successfully")
                return True
                
        except Exception as e:
            logger.error(f"  ❌ Schema migration failed: {str(e)}")
            return False
    
    async def _test_vector_services(self) -> bool:
        """Test that vector services are working correctly."""
        try:
            logger.info("  🧪 Testing embedding service...")
            from db.services.encryption_aware_embedding_service import get_encryption_aware_embedding_service
            
            embedding_service = await get_encryption_aware_embedding_service()
            
            # Test embedding generation
            test_text = "This is a test document for insurance policy verification."
            embedding = await embedding_service._generate_embedding(test_text)
            
            if len(embedding) > 0:
                logger.info(f"     ✅ Embedding service working (dimension: {len(embedding)})")
            else:
                logger.error("     ❌ Embedding service returned empty embedding")
                return False
            
            # Test database connectivity for vector operations
            if not self.dry_run:
                pool = await get_db_pool()
                async with pool.get_connection() as conn:
                    # Test vector table exists
                    vector_table_exists = await conn.fetchval("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'policy_content_vectors'
                        )
                    """)
                    
                    if vector_table_exists:
                        logger.info("     ✅ Vector tables accessible")
                    else:
                        logger.error("     ❌ Vector tables not found")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Vector services test failed: {str(e)}")
            return False
    
    async def _run_post_migration_validation(self) -> Dict[str, Any]:
        """Run validation checks after migration."""
        validation_results = {
            "vector_tables_created": False,
            "data_migrated": False,
            "vector_search_working": False,
            "row_counts": {},
            "sample_queries": []
        }
        
        try:
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                
                # Check vector tables exist
                logger.info("  🔍 Validating vector tables...")
                vector_tables = ['policy_content_vectors', 'user_document_vectors']
                
                for table in vector_tables:
                    exists = await conn.fetchval(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = '{table}'
                        )
                    """)
                    if exists:
                        count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                        validation_results["row_counts"][table] = count
                        logger.info(f"     ✅ {table}: {count} records")
                    else:
                        logger.error(f"     ❌ {table}: not found")
                        return validation_results
                
                validation_results["vector_tables_created"] = True
                
                # Check if data was migrated
                total_vectors = sum(validation_results["row_counts"].values())
                if total_vectors > 0:
                    validation_results["data_migrated"] = True
                    logger.info(f"  ✅ Data migration successful: {total_vectors} total vectors")
                else:
                    logger.warning("  ⚠️  No data found in vector tables")
                
                # Test vector search functionality
                if not self.dry_run and total_vectors > 0:
                    logger.info("  🔍 Testing vector search...")
                    try:
                        from agents.common.vector_rag import get_vector_rag
                        vector_rag = await get_vector_rag()
                        
                        # Get a sample user_id for testing
                        sample_user = await conn.fetchval(
                            "SELECT user_id FROM policy_content_vectors LIMIT 1"
                        )
                        
                        if sample_user:
                            # Test search
                            results = await vector_rag.search_policy_context(
                                query="insurance coverage benefits",
                                user_id=str(sample_user),
                                limit=3
                            )
                            
                            if results:
                                validation_results["vector_search_working"] = True
                                validation_results["sample_queries"].append({
                                    "query": "insurance coverage benefits",
                                    "results_count": len(results),
                                    "max_relevance": max([r.get('relevance_score', 0) for r in results])
                                })
                                logger.info(f"     ✅ Vector search working: {len(results)} results")
                            else:
                                logger.warning("     ⚠️  Vector search returned no results")
                        else:
                            logger.warning("     ⚠️  No sample user found for testing")
                            
                    except Exception as e:
                        logger.warning(f"     ⚠️  Vector search test failed: {str(e)}")
                
                return validation_results
                
        except Exception as e:
            logger.error(f"  ❌ Post-migration validation failed: {str(e)}")
            validation_results["error"] = str(e)
            return validation_results
    
    async def _create_final_report(
        self, 
        backup_info: Dict[str, Any], 
        migration_report: Dict[str, Any], 
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive final migration report."""
        
        final_report = {
            "migration_timestamp": datetime.now().isoformat(),
            "migration_mode": "dry_run" if self.dry_run else "full_migration",
            "backup_info": backup_info,
            "migration_report": migration_report,
            "validation_results": validation_results,
            "migration_log": self.migration_log,
            "next_steps": []
        }
        
        # Add next steps based on results
        if self.dry_run:
            final_report["next_steps"].extend([
                "Run migration without --dry-run flag to execute changes",
                "Ensure all dependencies are installed",
                "Review backup procedures"
            ])
        elif validation_results.get("vector_search_working"):
            final_report["next_steps"].extend([
                "Update agent configurations to use new VectorRAG interface",
                "Test agent functionality with new vector system",
                "Monitor performance and adjust vector indexes if needed",
                "Schedule deprecation of old tables after validation period"
            ])
        else:
            final_report["next_steps"].extend([
                "Investigate vector search issues",
                "Verify embedding service configuration",
                "Check vector table indexes and permissions"
            ])
        
        # Save report to file
        report_file = project_root / 'db' / 'scripts' / f'migration_final_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        logger.info(f"📄 Final report saved to: {report_file}")
        
        return final_report

async def main():
    """Main migration execution function."""
    parser = argparse.ArgumentParser(description='Execute vector migration for insurance policy system')
    parser.add_argument('--dry-run', action='store_true', help='Run checks without making changes')
    parser.add_argument('--skip-migration', action='store_true', help='Skip schema migration step')
    parser.add_argument('--force', action='store_true', help='Force migration even if checks fail')
    
    args = parser.parse_args()
    
    executor = VectorMigrationExecutor(
        dry_run=args.dry_run,
        skip_migration=args.skip_migration,
        force=args.force
    )
    
    result = await executor.run_complete_migration()
    
    if result["success"]:
        sys.exit(0)
    else:
        logger.error(f"Migration failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 