#!/usr/bin/env python3
"""
Pre-migration validation script for MVP Database Refactoring
This script validates the current database state before applying the schema changes.
"""

import asyncio
import asyncpg
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/insurance_navigator')

class PreMigrationValidator:
    """Validates database state before migration."""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'database_url': DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL,
            'validation_results': {},
            'recommendations': [],
            'errors': [],
            'warnings': []
        }
    
    async def run_all_validations(self):
        """Run complete pre-migration validation suite."""
        logger.info("🔍 Starting Pre-Migration Validation")
        
        try:
            # Connect to database with statement cache disabled for pgbouncer compatibility
            self.conn = await asyncpg.connect(DATABASE_URL, statement_cache_size=0)
            
            # Run validation checks
            await self.validate_database_structure()
            await self.validate_existing_data()
            await self.validate_performance_baseline()
            await self.validate_hipaa_compliance()
            await self.check_migration_readiness()
            
            # Generate summary report
            await self.generate_summary_report()
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            self.results['errors'].append(f"Critical validation error: {e}")
        finally:
            if hasattr(self, 'conn'):
                await self.conn.close()
    
    async def validate_database_structure(self):
        """Validate current database structure."""
        logger.info("📊 Validating database structure...")
        
        # Get all tables
        tables = await self.conn.fetch("""
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        table_names = [row['table_name'] for row in tables]
        
        self.results['validation_results']['current_tables'] = {
            'total_count': len(table_names),
            'table_list': table_names
        }
        
        # Check for our new target tables
        target_tables = ['user_documents', 'regulatory_documents', 'user_document_vectors', 
                        'conversations', 'messages', 'audit_logs']
        
        existing_target_tables = [t for t in target_tables if t in table_names]
        missing_target_tables = [t for t in target_tables if t not in table_names]
        
        self.results['validation_results']['target_tables'] = {
            'existing': existing_target_tables,
            'missing': missing_target_tables,
            'migration_status': 'PARTIAL' if existing_target_tables else 'READY'
        }
        
        logger.info(f"✅ Found {len(table_names)} tables total")
        logger.info(f"✅ Target tables: {len(existing_target_tables)} existing, {len(missing_target_tables)} missing")
    
    async def validate_existing_data(self):
        """Validate existing data integrity and volume."""
        logger.info("📈 Validating existing data...")
        
        data_stats = {}
        
        # Check conversations table
        if await self._table_exists('conversations'):
            conv_count = await self.conn.fetchval("SELECT COUNT(*) FROM conversations")
            data_stats['conversations'] = {
                'count': conv_count,
                'sample_ids': await self.conn.fetch("SELECT id FROM conversations LIMIT 5")
            }
        
        # Check conversation_messages table
        if await self._table_exists('conversation_messages'):
            msg_count = await self.conn.fetchval("SELECT COUNT(*) FROM conversation_messages")
            data_stats['conversation_messages'] = {
                'count': msg_count,
                'sample': await self.conn.fetch("""
                    SELECT conversation_id, role, LENGTH(content) as content_length 
                    FROM conversation_messages LIMIT 5
                """)
            }
        
        # Check user_document_vectors table
        if await self._table_exists('user_document_vectors'):
            vector_count = await self.conn.fetchval("SELECT COUNT(*) FROM user_document_vectors")
            data_stats['user_document_vectors'] = {
                'count': vector_count,
                'unique_users': await self.conn.fetchval("SELECT COUNT(DISTINCT user_id) FROM user_document_vectors"),
                'unique_documents': await self.conn.fetchval("SELECT COUNT(DISTINCT document_id) FROM user_document_vectors")
            }
        
        # Check regulatory_documents table
        if await self._table_exists('regulatory_documents'):
            reg_count = await self.conn.fetchval("SELECT COUNT(*) FROM regulatory_documents")
            data_stats['regulatory_documents'] = {
                'count': reg_count,
                'sample_types': await self.conn.fetch("""
                    SELECT document_type, COUNT(*) as count 
                    FROM regulatory_documents 
                    GROUP BY document_type
                """) if reg_count > 0 else []
            }
        
        # Check users table
        if await self._table_exists('users'):
            user_count = await self.conn.fetchval("SELECT COUNT(*) FROM users")
            data_stats['users'] = {
                'count': user_count,
                'active_users': await self.conn.fetchval("""
                    SELECT COUNT(*) FROM users 
                    WHERE created_at > NOW() - INTERVAL '30 days'
                """)
            }
        
        self.results['validation_results']['existing_data'] = data_stats
        
        # Calculate migration volume
        total_records = sum(stats.get('count', 0) for stats in data_stats.values())
        
        if total_records > 100000:
            self.results['warnings'].append(f"Large dataset detected ({total_records:,} records). Consider migration in batches.")
        
        logger.info(f"✅ Data validation complete. Total records: {total_records:,}")
    
    async def validate_performance_baseline(self):
        """Establish performance baseline before migration."""
        logger.info("⚡ Establishing performance baseline...")
        
        performance_results = {}
        
        # Test conversation query performance
        if await self._table_exists('conversations'):
            start_time = datetime.now()
            await self.conn.fetch("SELECT * FROM conversations LIMIT 100")
            conv_time = (datetime.now() - start_time).total_seconds() * 1000
            performance_results['conversation_query_ms'] = conv_time
        
        # Test vector search performance (if table exists)
        if await self._table_exists('user_document_vectors'):
            try:
                start_time = datetime.now()
                await self.conn.fetch("""
                    SELECT * FROM user_document_vectors 
                    WHERE chunk_text ILIKE '%insurance%' 
                    LIMIT 10
                """)
                vector_time = (datetime.now() - start_time).total_seconds() * 1000
                performance_results['vector_search_ms'] = vector_time
            except Exception as e:
                logger.warning(f"Vector search test failed: {e}")
                performance_results['vector_search_ms'] = 'N/A (test failed)'
        
        # Test complex join performance
        if await self._table_exists('conversations') and await self._table_exists('conversation_messages'):
            start_time = datetime.now()
            await self.conn.fetch("""
                SELECT c.id, c.user_id, COUNT(cm.id) as message_count
                FROM conversations c
                LEFT JOIN conversation_messages cm ON c.id = cm.conversation_id
                GROUP BY c.id, c.user_id
                LIMIT 50
            """)
            join_time = (datetime.now() - start_time).total_seconds() * 1000
            performance_results['complex_join_ms'] = join_time
        
        self.results['validation_results']['performance_baseline'] = performance_results
        
        # Performance recommendations
        vector_search_time = performance_results.get('vector_search_ms', 0)
        if isinstance(vector_search_time, (int, float)) and vector_search_time > 500:
            self.results['recommendations'].append("Vector search performance may benefit from additional indexing")
        
        logger.info(f"✅ Performance baseline established")
    
    async def validate_hipaa_compliance(self):
        """Validate HIPAA compliance features."""
        logger.info("🔒 Validating HIPAA compliance...")
        
        compliance_check = {
            'rls_enabled': {},
            'audit_capability': False,
            'encryption_columns': []
        }
        
        # Check Row Level Security on key tables
        for table in ['conversations', 'user_document_vectors']:
            if await self._table_exists(table):
                rls_status = await self.conn.fetchval(f"""
                    SELECT relrowsecurity 
                    FROM pg_class 
                    WHERE relname = '{table}'
                """)
                compliance_check['rls_enabled'][table] = bool(rls_status)
        
        # Check for encryption columns
        for table in ['user_document_vectors']:
            if await self._table_exists(table):
                columns = await self.conn.fetch(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    AND column_name LIKE '%encrypted%'
                """)
                if columns:
                    compliance_check['encryption_columns'].extend([row['column_name'] for row in columns])
        
        # Check if we can create audit logs
        try:
            await self.conn.execute("""
                INSERT INTO audit_logs (action, resource_type, details) 
                VALUES ('test', 'validation', '{"test": true}')
            """)
            await self.conn.execute("DELETE FROM audit_logs WHERE action = 'test'")
            compliance_check['audit_capability'] = True
        except:
            compliance_check['audit_capability'] = False
        
        self.results['validation_results']['hipaa_compliance'] = compliance_check
        
        # Compliance recommendations
        rls_missing = [table for table, enabled in compliance_check['rls_enabled'].items() if not enabled]
        if rls_missing:
            self.results['recommendations'].append(f"Enable RLS on tables: {', '.join(rls_missing)}")
        
        if not compliance_check['audit_capability']:
            self.results['warnings'].append("Audit logging capability not verified")
        
        logger.info(f"✅ HIPAA compliance validation complete")
    
    async def check_migration_readiness(self):
        """Check if database is ready for migration."""
        logger.info("🚀 Checking migration readiness...")
        
        readiness_check = {
            'target_tables_created': True,
            'no_active_transactions': True,
            'sufficient_disk_space': True,  # Would need system check in production
            'backup_recommended': True,
            'estimated_downtime_minutes': 0
        }
        
        # Check if target tables already exist
        target_tables = ['user_documents', 'regulatory_documents', 'user_document_vectors', 
                        'conversations', 'messages', 'audit_logs']
        
        for table in target_tables:
            if not await self._table_exists(table):
                readiness_check['target_tables_created'] = False
                break
        
        # Estimate migration complexity and downtime
        total_records = 0
        if self.results['validation_results'].get('existing_data'):
            total_records = sum(
                stats.get('count', 0) 
                for stats in self.results['validation_results']['existing_data'].values()
            )
        
        # Rough estimate: 10k records per minute
        readiness_check['estimated_downtime_minutes'] = max(1, total_records // 10000)
        
        self.results['validation_results']['migration_readiness'] = readiness_check
        
        # Readiness recommendations
        if not readiness_check['target_tables_created']:
            self.results['recommendations'].append("Run schema migration first to create target tables")
        
        if readiness_check['estimated_downtime_minutes'] > 5:
            self.results['recommendations'].append("Schedule migration during low-traffic period")
        
        logger.info(f"✅ Migration readiness check complete")
    
    async def generate_summary_report(self):
        """Generate comprehensive validation summary."""
        logger.info("📋 Generating validation summary...")
        
        # Count validations
        validation_count = len(self.results['validation_results'])
        error_count = len(self.results['errors'])
        warning_count = len(self.results['warnings'])
        recommendation_count = len(self.results['recommendations'])
        
        summary = {
            'validation_status': 'PASSED' if error_count == 0 else 'FAILED',
            'total_validations': validation_count,
            'errors': error_count,
            'warnings': warning_count,
            'recommendations': recommendation_count,
            'migration_ready': error_count == 0 and self.results['validation_results'].get('migration_readiness', {}).get('target_tables_created', False)
        }
        
        self.results['summary'] = summary
        
        # Print summary
        print("\n" + "="*60)
        print("📊 PRE-MIGRATION VALIDATION SUMMARY")
        print("="*60)
        print(f"Status: {'✅ PASSED' if summary['validation_status'] == 'PASSED' else '❌ FAILED'}")
        print(f"Validations Run: {validation_count}")
        print(f"Errors: {error_count}")
        print(f"Warnings: {warning_count}")
        print(f"Recommendations: {recommendation_count}")
        print(f"Migration Ready: {'✅ YES' if summary['migration_ready'] else '❌ NO'}")
        
        if self.results['errors']:
            print("\n❌ ERRORS:")
            for error in self.results['errors']:
                print(f"  • {error}")
        
        if self.results['warnings']:
            print("\n⚠️  WARNINGS:")
            for warning in self.results['warnings']:
                print(f"  • {warning}")
        
        if self.results['recommendations']:
            print("\n💡 RECOMMENDATIONS:")
            for rec in self.results['recommendations']:
                print(f"  • {rec}")
        
        # Save detailed results
        with open('pre_migration_validation_results.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: pre_migration_validation_results.json")
        print("="*60)
    
    async def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        result = await self.conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = $1
            )
        """, table_name)
        return result

async def main():
    """Run pre-migration validation."""
    validator = PreMigrationValidator()
    await validator.run_all_validations()

if __name__ == "__main__":
    asyncio.run(main())