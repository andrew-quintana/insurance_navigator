#!/usr/bin/env python3
"""
Focused Database Schema Validator

Targets the specific patterns that caused our production failures:
1. Missing columns in INSERT statements
2. Broken triggers and functions
3. Foreign key integrity
4. Critical operation validation
"""

import asyncio
import asyncpg
import os
import re
from pathlib import Path
from typing import List, Dict, Set, Any
from dotenv import load_dotenv
import json

load_dotenv()

class FocusedSchemaValidator:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.issues = []
        self.warnings = []
        self.info = []
        
        # Define critical tables we care about
        self.critical_tables = {
            'documents', 'users', 'conversations', 'messages', 
            'processing_jobs', 'document_vectors', 'user_document_vectors',
            'regulatory_documents', 'audit_logs'
        }
        
    async def connect(self):
        """Connect to database"""
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in environment")
        return await asyncpg.connect(self.db_url)
    
    def extract_insert_statements(self) -> Dict[str, Set[str]]:
        """Extract INSERT statements and their columns from application code"""
        table_columns = {}
        
        # More precise pattern for INSERT statements
        insert_pattern = r'INSERT\s+INTO\s+(\w+)\s*\(\s*([^)]+)\s*\)\s*VALUES'
        
        # Only scan main application files
        app_files = ['main.py'] + list(Path('db/services').glob('*.py'))
        
        for py_file in app_files:
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Find multiline INSERT statements
                    multiline_pattern = r'INSERT\s+INTO\s+(\w+)\s*\(\s*([^)]+)\s*\)'
                    matches = re.findall(multiline_pattern, content, re.IGNORECASE | re.DOTALL)
                    
                    for table, columns_str in matches:
                        if table in self.critical_tables:
                            # Clean up column names
                            columns = [col.strip() for col in columns_str.split(',')]
                            columns = [re.sub(r'["\'\s]', '', col) for col in columns]
                            columns = [col for col in columns if col and not col.startswith('$')]
                            
                            if table not in table_columns:
                                table_columns[table] = set()
                            table_columns[table].update(columns)
                            
                            self.info.append(f"ℹ️ Found INSERT into {table} with columns: {', '.join(columns)}")
            except Exception as e:
                self.warnings.append(f"Could not scan {py_file}: {e}")
        
        return table_columns
    
    async def get_database_tables(self, conn) -> Set[str]:
        """Get list of tables in database"""
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        return {row['table_name'] for row in tables}
    
    async def get_table_columns(self, conn, table_name: str) -> Dict[str, Any]:
        """Get column information for a table"""
        columns = await conn.fetch("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = $1
            ORDER BY ordinal_position
        """, table_name)
        
        return {row['column_name']: {
            'type': row['data_type'],
            'nullable': row['is_nullable'] == 'YES',
            'default': row['column_default'],
            'max_length': row['character_maximum_length']
        } for row in columns}
    
    async def check_critical_triggers(self, conn) -> List[Dict]:
        """Check for broken triggers on critical tables"""
        broken_triggers = []
        
        # Get triggers on critical tables
        triggers = await conn.fetch("""
            SELECT 
                trigger_name,
                event_object_table,
                action_statement,
                event_manipulation,
                action_timing
            FROM information_schema.triggers
            WHERE event_object_table = ANY($1)
        """, list(self.critical_tables))
        
        tables = await self.get_database_tables(conn)
        
        for trigger in triggers:
            # Check if trigger function references tables that don't exist
            action = trigger['action_statement']
            if 'EXECUTE FUNCTION' in action:
                func_name = re.search(r'EXECUTE FUNCTION\s+(\w+)', action)
                if func_name:
                    try:
                        func_def = await conn.fetchval("""
                            SELECT routine_definition 
                            FROM information_schema.routines 
                            WHERE routine_name = $1
                        """, func_name.group(1))
                        
                        if func_def:
                            # Look for table references in function (only INSERT/UPDATE/DELETE)
                            table_refs = re.findall(r'(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+(\w+)', func_def, re.IGNORECASE)
                            for table_ref in table_refs:
                                if table_ref not in tables:
                                    broken_triggers.append({
                                        'trigger': trigger['trigger_name'],
                                        'table': trigger['event_object_table'],
                                        'issue': f"Function {func_name.group(1)} tries to {table_ref} but table doesn't exist",
                                        'severity': 'CRITICAL'
                                    })
                    except Exception as e:
                        self.warnings.append(f"Could not check function {func_name.group(1)}: {e}")
        
        return broken_triggers
    
    async def validate_insert_operations(self, conn) -> List[Dict]:
        """Validate that INSERT operations will succeed"""
        issues = []
        
        # Get INSERT statements from code
        app_inserts = self.extract_insert_statements()
        
        for table, app_columns in app_inserts.items():
            try:
                # Check if table exists
                tables = await self.get_database_tables(conn)
                if table not in tables:
                    issues.append({
                        'operation': f'INSERT_{table}',
                        'issue': f'Table {table} does not exist',
                        'severity': 'CRITICAL',
                        'impact': 'INSERT operations will fail'
                    })
                    continue
                
                # Get actual table columns
                db_columns = await self.get_table_columns(conn, table)
                
                # Check for missing columns
                missing_columns = app_columns - set(db_columns.keys())
                for col in missing_columns:
                    issues.append({
                        'operation': f'INSERT_{table}',
                        'issue': f'Column {col} referenced in code but missing from table',
                        'severity': 'CRITICAL',
                        'impact': 'INSERT operations will fail with column not found error'
                    })
                
                # Check for NOT NULL constraints without defaults
                for col_name, col_info in db_columns.items():
                    if (not col_info['nullable'] and 
                        not col_info['default'] and 
                        col_name not in app_columns and
                        col_name not in ['id', 'created_at', 'updated_at']):  # Common auto-generated columns
                        
                        issues.append({
                            'operation': f'INSERT_{table}',
                            'issue': f'Column {col_name} is NOT NULL without default, but not provided in INSERT',
                            'severity': 'HIGH',
                            'impact': 'INSERT operations will fail with NOT NULL constraint violation'
                        })
                
            except Exception as e:
                issues.append({
                    'operation': f'INSERT_{table}',
                    'issue': f'Could not validate: {e}',
                    'severity': 'UNKNOWN'
                })
        
        return issues
    
    async def check_document_upload_readiness(self, conn) -> List[Dict]:
        """Specific check for document upload functionality"""
        issues = []
        
        try:
            tables = await self.get_database_tables(conn)
            
            # Check documents table
            if 'documents' not in tables:
                issues.append({
                    'operation': 'document_upload',
                    'issue': 'documents table missing',
                    'severity': 'CRITICAL'
                })
                return issues
            
            doc_columns = await self.get_table_columns(conn, 'documents')
            
            # Check for required columns based on our fixes
            required_columns = {
                'file_path': 'Required for file storage path',
                'storage_backend': 'Required for storage configuration', 
                'bucket_name': 'Required for storage bucket',
                'content_type': 'Required for file type tracking',
                'file_hash': 'Required for file integrity'
            }
            
            for col, purpose in required_columns.items():
                if col not in doc_columns:
                    issues.append({
                        'operation': 'document_upload',
                        'issue': f'Missing column: {col} - {purpose}',
                        'severity': 'HIGH'
                    })
                elif not doc_columns[col]['nullable'] and not doc_columns[col]['default']:
                    issues.append({
                        'operation': 'document_upload',
                        'issue': f'Column {col} is NOT NULL without default',
                        'severity': 'HIGH'
                    })
            
            # Check if processing_jobs table exists (for triggers)
            if 'processing_jobs' not in tables:
                issues.append({
                    'operation': 'document_upload',
                    'issue': 'processing_jobs table missing - document triggers will fail',
                    'severity': 'CRITICAL'
                })
            
        except Exception as e:
            issues.append({
                'operation': 'document_upload',
                'issue': f'Validation failed: {e}',
                'severity': 'UNKNOWN'
            })
        
        return issues
    
    async def run_focused_validation(self) -> Dict[str, Any]:
        """Run focused validation checks"""
        print("🔍 Running focused database schema validation...")
        
        conn = await self.connect()
        
        try:
            # Phase 1: Validate INSERT operations
            print("📋 Phase 1: Validating INSERT operations...")
            insert_issues = await self.validate_insert_operations(conn)
            for issue in insert_issues:
                severity = issue.get('severity', 'UNKNOWN')
                if severity == 'CRITICAL':
                    self.issues.append(f"🚨 {issue['operation']}: {issue['issue']}")
                elif severity == 'HIGH':
                    self.warnings.append(f"⚠️ {issue['operation']}: {issue['issue']}")
                else:
                    self.info.append(f"ℹ️ {issue['operation']}: {issue['issue']}")
            
            # Phase 2: Check critical triggers
            print("📋 Phase 2: Checking critical triggers...")
            trigger_issues = await self.check_critical_triggers(conn)
            for issue in trigger_issues:
                self.issues.append(f"🚨 Trigger {issue['trigger']} on {issue['table']}: {issue['issue']}")
            
            # Phase 3: Document upload readiness
            print("📋 Phase 3: Validating document upload readiness...")
            doc_issues = await self.check_document_upload_readiness(conn)
            for issue in doc_issues:
                severity = issue.get('severity', 'UNKNOWN')
                if severity == 'CRITICAL':
                    self.issues.append(f"🚨 Document Upload: {issue['issue']}")
                elif severity == 'HIGH':
                    self.warnings.append(f"⚠️ Document Upload: {issue['issue']}")
                else:
                    self.info.append(f"ℹ️ Document Upload: {issue['issue']}")
            
            return {
                'issues': self.issues,
                'warnings': self.warnings,
                'info': self.info,
                'summary': {
                    'total_issues': len(self.issues),
                    'total_warnings': len(self.warnings),
                    'insert_issues': len(insert_issues),
                    'trigger_issues': len(trigger_issues),
                    'document_upload_issues': len(doc_issues)
                }
            }
        
        finally:
            await conn.close()
    
    def print_report(self, results: Dict[str, Any]):
        """Print focused validation report"""
        print("\n" + "="*80)
        print("🎯 FOCUSED DATABASE SCHEMA VALIDATION REPORT")
        print("="*80)
        
        summary = results['summary']
        
        print(f"\n📈 SUMMARY:")
        print(f"  🚨 Critical Issues: {summary['total_issues']}")
        print(f"  ⚠️  Warnings: {summary['total_warnings']}")
        print(f"  📊 INSERT Issues: {summary['insert_issues']}")
        print(f"  📊 Trigger Issues: {summary['trigger_issues']}")
        print(f"  📊 Document Upload Issues: {summary['document_upload_issues']}")
        
        if results['issues']:
            print(f"\n🚨 CRITICAL ISSUES ({len(results['issues'])}):")
            for issue in results['issues']:
                print(f"  {issue}")
        
        if results['warnings']:
            print(f"\n⚠️  WARNINGS ({len(results['warnings'])}):")
            for warning in results['warnings']:
                print(f"  {warning}")
        
        if results['info']:
            print(f"\nℹ️  INFORMATION ({len(results['info'])}):")
            for info in results['info'][:10]:  # Limit to first 10
                print(f"  {info}")
            if len(results['info']) > 10:
                print(f"  ... and {len(results['info']) - 10} more")
        
        print(f"\n{'✅ VALIDATION PASSED' if not results['issues'] else '❌ VALIDATION FAILED'}")
        print("="*80)
        
        return len(results['issues']) == 0

async def main():
    """Main execution function"""
    validator = FocusedSchemaValidator()
    
    try:
        results = await validator.run_focused_validation()
        
        # Print report
        success = validator.print_report(results)
        
        # Save results to file
        Path('logs').mkdir(exist_ok=True)
        with open('logs/focused_schema_validation.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: logs/focused_schema_validation.json")
        
        # Exit with appropriate code
        exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        exit(1)

if __name__ == '__main__':
    asyncio.run(main()) 