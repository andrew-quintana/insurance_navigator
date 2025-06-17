#!/usr/bin/env python3
"""
Database Schema Validation Script

Proactively detects schema-code synchronization issues before they cause production failures.
Analyzes the patterns that caused our recent upload failures.
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

class DatabaseSchemaValidator:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.issues = []
        self.warnings = []
        self.info = []
        
    async def connect(self):
        """Connect to database"""
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in environment")
        return await asyncpg.connect(self.db_url)
    
    def scan_application_table_references(self) -> Set[str]:
        """Scan application code for database table references"""
        table_refs = set()
        
        # SQL patterns to match table references
        sql_patterns = [
            r'INSERT\s+INTO\s+(\w+)',
            r'UPDATE\s+(\w+)\s+SET',
            r'DELETE\s+FROM\s+(\w+)',
            r'FROM\s+(\w+)(?:\s|$|,|\))',
            r'JOIN\s+(\w+)(?:\s|$|,|\))',
            r'REFERENCES\s+(\w+)',
        ]
        
        # Scan Python files
        for py_file in Path('.').rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for pattern in sql_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        # Filter out common SQL keywords
                        filtered = [m for m in matches if m.lower() not in 
                                  ['select', 'where', 'order', 'group', 'having', 'limit', 'offset']]
                        table_refs.update(filtered)
            except Exception as e:
                self.warnings.append(f"Could not scan {py_file}: {e}")
        
        # Scan SQL migration files
        for sql_file in Path('db/migrations').glob('*.sql'):
            try:
                with open(sql_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for pattern in sql_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        table_refs.update(matches)
            except Exception as e:
                self.warnings.append(f"Could not scan {sql_file}: {e}")
        
        return table_refs
    
    def scan_column_references(self) -> Dict[str, Set[str]]:
        """Scan for specific column references in INSERT statements"""
        table_columns = {}
        
        # Pattern to match INSERT statements with column lists
        insert_pattern = r'INSERT\s+INTO\s+(\w+)\s*\(\s*([^)]+)\s*\)'
        
        for py_file in Path('.').rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    matches = re.findall(insert_pattern, content, re.IGNORECASE | re.DOTALL)
                    
                    for table, columns_str in matches:
                        # Parse column names
                        columns = [col.strip() for col in columns_str.split(',')]
                        columns = [col.strip('"`\'') for col in columns]  # Remove quotes
                        
                        if table not in table_columns:
                            table_columns[table] = set()
                        table_columns[table].update(columns)
            except Exception as e:
                self.warnings.append(f"Could not scan {py_file} for columns: {e}")
        
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
    
    async def check_broken_triggers(self, conn) -> List[Dict]:
        """Check for database triggers that reference non-existent objects"""
        broken_triggers = []
        
        # Get all triggers
        triggers = await conn.fetch("""
            SELECT 
                trigger_name,
                event_object_table,
                action_statement,
                event_manipulation,
                action_timing
            FROM information_schema.triggers
        """)
        
        # Get all tables
        tables = await self.get_database_tables(conn)
        
        for trigger in triggers:
            # Check if trigger table exists
            if trigger['event_object_table'] not in tables:
                broken_triggers.append({
                    'trigger': trigger['trigger_name'],
                    'issue': f"Trigger on non-existent table: {trigger['event_object_table']}",
                    'details': trigger
                })
            
            # Check if trigger function references tables that don't exist
            action = trigger['action_statement']
            if 'EXECUTE FUNCTION' in action:
                func_name = re.search(r'EXECUTE FUNCTION\s+(\w+)', action)
                if func_name:
                    # Check function definition
                    try:
                        func_def = await conn.fetchval("""
                            SELECT routine_definition 
                            FROM information_schema.routines 
                            WHERE routine_name = $1
                        """, func_name.group(1))
                        
                        if func_def:
                            # Look for table references in function
                            for table_ref in re.findall(r'(?:INSERT INTO|UPDATE|DELETE FROM|FROM)\s+(\w+)', func_def, re.IGNORECASE):
                                if table_ref not in tables:
                                    broken_triggers.append({
                                        'trigger': trigger['trigger_name'],
                                        'issue': f"Function {func_name.group(1)} references non-existent table: {table_ref}",
                                        'details': trigger
                                    })
                    except Exception as e:
                        self.warnings.append(f"Could not check function {func_name.group(1)}: {e}")
        
        return broken_triggers
    
    async def check_foreign_key_integrity(self, conn) -> List[Dict]:
        """Check for broken foreign key constraints"""
        broken_fks = []
        
        fk_info = await conn.fetch("""
            SELECT 
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu 
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
        """)
        
        tables = await self.get_database_tables(conn)
        
        for fk in fk_info:
            if fk['foreign_table_name'] not in tables:
                broken_fks.append({
                    'constraint': fk['constraint_name'],
                    'table': fk['table_name'],
                    'column': fk['column_name'],
                    'issue': f"References non-existent table: {fk['foreign_table_name']}",
                    'details': fk
                })
        
        return broken_fks
    
    async def validate_critical_operations(self, conn) -> List[Dict]:
        """Test critical operations that have failed before"""
        operation_issues = []
        
        # Test document insertion (our recent failure)
        try:
            # Check if documents table has required columns
            if 'documents' in await self.get_database_tables(conn):
                doc_columns = await self.get_table_columns(conn, 'documents')
                
                required_columns = ['file_path', 'storage_backend', 'bucket_name']
                for col in required_columns:
                    if col not in doc_columns:
                        operation_issues.append({
                            'operation': 'document_upload',
                            'issue': f"Missing required column: {col}",
                            'table': 'documents'
                        })
                    elif not doc_columns[col]['nullable'] and not doc_columns[col]['default']:
                        operation_issues.append({
                            'operation': 'document_upload',
                            'issue': f"Column {col} is NOT NULL without default value",
                            'table': 'documents'
                        })
                
                # Check if processing_jobs table exists (trigger dependency)
                if 'processing_jobs' not in await self.get_database_tables(conn):
                    operation_issues.append({
                        'operation': 'document_upload',
                        'issue': 'processing_jobs table missing - triggers will fail',
                        'table': 'documents'
                    })
        except Exception as e:
            operation_issues.append({
                'operation': 'document_upload',
                'issue': f"Could not validate: {e}",
                'table': 'documents'
            })
        
        return operation_issues
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation checks"""
        print("🔍 Starting comprehensive database schema validation...")
        
        conn = await self.connect()
        
        try:
            # Phase 1: Basic schema validation
            print("📋 Phase 1: Scanning application code for table references...")
            app_tables = self.scan_application_table_references()
            app_columns = self.scan_column_references()
            
            print(f"📊 Found {len(app_tables)} table references in application code")
            
            # Phase 2: Database schema analysis
            print("📋 Phase 2: Analyzing database schema...")
            db_tables = await self.get_database_tables(conn)
            
            print(f"📊 Found {len(db_tables)} tables in database")
            
            # Phase 3: Schema-code synchronization check
            print("📋 Phase 3: Checking schema-code synchronization...")
            missing_tables = app_tables - db_tables
            orphaned_tables = db_tables - app_tables
            
            if missing_tables:
                for table in missing_tables:
                    self.issues.append(f"🚨 Table '{table}' referenced in code but missing from database")
            
            if orphaned_tables:
                for table in orphaned_tables:
                    self.info.append(f"ℹ️ Table '{table}' exists in database but not referenced in code")
            
            # Phase 4: Column validation
            print("📋 Phase 4: Validating column requirements...")
            for table, columns in app_columns.items():
                if table in db_tables:
                    db_columns = await self.get_table_columns(conn, table)
                    missing_columns = columns - set(db_columns.keys())
                    
                    for col in missing_columns:
                        self.issues.append(f"🚨 Column '{col}' referenced in code but missing from table '{table}'")
                    
                    # Check for NOT NULL columns without defaults
                    for col_name, col_info in db_columns.items():
                        if not col_info['nullable'] and not col_info['default'] and col_name in columns:
                            self.warnings.append(f"⚠️ Column '{table}.{col_name}' is NOT NULL without default - potential INSERT failures")
            
            # Phase 5: Trigger validation
            print("📋 Phase 5: Checking database triggers...")
            broken_triggers = await self.check_broken_triggers(conn)
            for trigger in broken_triggers:
                self.issues.append(f"🚨 Broken trigger: {trigger['trigger']} - {trigger['issue']}")
            
            # Phase 6: Foreign key validation
            print("📋 Phase 6: Validating foreign key constraints...")
            broken_fks = await self.check_foreign_key_integrity(conn)
            for fk in broken_fks:
                self.issues.append(f"🚨 Broken foreign key: {fk['constraint']} - {fk['issue']}")
            
            # Phase 7: Critical operation validation
            print("📋 Phase 7: Testing critical operations...")
            operation_issues = await self.validate_critical_operations(conn)
            for op in operation_issues:
                self.issues.append(f"🚨 Critical operation issue: {op['operation']} - {op['issue']}")
            
            return {
                'issues': self.issues,
                'warnings': self.warnings,
                'info': self.info,
                'summary': {
                    'total_issues': len(self.issues),
                    'total_warnings': len(self.warnings),
                    'app_tables': len(app_tables),
                    'db_tables': len(db_tables),
                    'missing_tables': len(missing_tables),
                    'broken_triggers': len(broken_triggers),
                    'broken_foreign_keys': len(broken_fks),
                    'operation_issues': len(operation_issues)
                }
            }
        
        finally:
            await conn.close()
    
    def print_report(self, results: Dict[str, Any]):
        """Print validation report"""
        print("\n" + "="*80)
        print("📊 DATABASE SCHEMA VALIDATION REPORT")
        print("="*80)
        
        summary = results['summary']
        
        print(f"\n📈 SUMMARY:")
        print(f"  🚨 Critical Issues: {summary['total_issues']}")
        print(f"  ⚠️  Warnings: {summary['total_warnings']}")
        print(f"  📊 Application Tables: {summary['app_tables']}")
        print(f"  📊 Database Tables: {summary['db_tables']}")
        
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
            for info in results['info']:
                print(f"  {info}")
        
        print(f"\n{'✅ VALIDATION PASSED' if not results['issues'] else '❌ VALIDATION FAILED'}")
        print("="*80)
        
        return len(results['issues']) == 0

async def main():
    """Main execution function"""
    validator = DatabaseSchemaValidator()
    
    try:
        results = await validator.run_comprehensive_validation()
        
        # Print report
        success = validator.print_report(results)
        
        # Save results to file
        with open('logs/schema_validation_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: logs/schema_validation_results.json")
        
        # Exit with appropriate code
        exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        exit(1)

if __name__ == '__main__':
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    asyncio.run(main()) 