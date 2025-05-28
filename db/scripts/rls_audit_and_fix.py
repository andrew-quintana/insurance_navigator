#!/usr/bin/env python3
"""
Row Level Security (RLS) Audit and Fix Script

This script identifies tables without RLS enabled, creates appropriate RLS policies,
and generates a comprehensive report of all changes made.

Usage:
    python rls_audit_and_fix.py [--dry-run] [--apply-fixes]
"""

import asyncio
import asyncpg
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rls_audit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TableInfo:
    """Information about a database table."""
    schema: str
    name: str
    has_rls: bool
    policies: List[Dict[str, Any]]
    columns: List[str]
    references_users: bool
    needs_user_access_policy: bool
    needs_admin_access_policy: bool

@dataclass
class RLSAuditResult:
    """Result of RLS audit."""
    timestamp: str
    tables_analyzed: int
    tables_without_rls: List[str]
    tables_with_incomplete_policies: List[str]
    recommended_actions: List[str]
    errors: List[str]

class RLSAuditor:
    """Main class for auditing and fixing RLS issues."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection: Optional[asyncpg.Connection] = None
        self.audit_result = RLSAuditResult(
            timestamp=datetime.now().isoformat(),
            tables_analyzed=0,
            tables_without_rls=[],
            tables_with_incomplete_policies=[],
            recommended_actions=[],
            errors=[]
        )
        
    async def connect(self):
        """Connect to the database."""
        try:
            self.connection = await asyncpg.connect(self.database_url)
            logger.info("Connected to database successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    async def disconnect(self):
        """Disconnect from the database."""
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from database")
            
    async def get_all_tables(self) -> List[TableInfo]:
        """Get information about all tables in the public schema."""
        query = """
        SELECT 
            schemaname,
            tablename,
            rowsecurity as has_rls
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY tablename;
        """
        
        tables = []
        rows = await self.connection.fetch(query)
        
        for row in rows:
            table_info = await self.get_table_details(row['schemaname'], row['tablename'], row['has_rls'])
            tables.append(table_info)
            
        self.audit_result.tables_analyzed = len(tables)
        return tables
        
    async def get_table_details(self, schema: str, table_name: str, has_rls: bool) -> TableInfo:
        """Get detailed information about a specific table."""
        
        # Get table columns
        columns_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = $1 AND table_name = $2
        ORDER BY ordinal_position;
        """
        columns = [row['column_name'] for row in await self.connection.fetch(columns_query, schema, table_name)]
        
        # Check if table references users
        references_users = 'user_id' in columns or table_name == 'users'
        
        # Get existing RLS policies
        policies = []
        if has_rls:
            policies_query = """
            SELECT 
                policyname,
                cmd,
                permissive,
                qual,
                with_check
            FROM pg_policies 
            WHERE schemaname = $1 AND tablename = $2;
            """
            policy_rows = await self.connection.fetch(policies_query, schema, table_name)
            policies = [dict(row) for row in policy_rows]
        
        # Determine what policies are needed
        needs_user_access = references_users and table_name != 'users'
        needs_admin_access = table_name in ['policy_access_logs', 'encryption_keys', 'roles', 'user_roles']
        
        return TableInfo(
            schema=schema,
            name=table_name,
            has_rls=has_rls,
            policies=policies,
            columns=columns,
            references_users=references_users,
            needs_user_access_policy=needs_user_access,
            needs_admin_access_policy=needs_admin_access
        )
        
    async def analyze_rls_issues(self, tables: List[TableInfo]) -> Dict[str, Any]:
        """Analyze RLS issues and generate recommendations."""
        issues = {
            'tables_without_rls': [],
            'tables_with_missing_policies': [],
            'recommended_fixes': []
        }
        
        for table in tables:
            # Check if RLS is enabled
            if not table.has_rls:
                issues['tables_without_rls'].append(table.name)
                self.audit_result.tables_without_rls.append(table.name)
                
            # Check for missing policies
            missing_policies = self.check_missing_policies(table)
            if missing_policies:
                issues['tables_with_missing_policies'].append({
                    'table': table.name,
                    'missing_policies': missing_policies
                })
                self.audit_result.tables_with_incomplete_policies.append(table.name)
                
        return issues
        
    def check_missing_policies(self, table: TableInfo) -> List[str]:
        """Check what policies are missing for a table."""
        missing = []
        
        if not table.has_rls:
            return ['RLS not enabled']
            
        policy_commands = {policy['cmd'] for policy in table.policies}
        
        # Check for basic access policies based on table type
        if table.name == 'users':
            if 'SELECT' not in policy_commands:
                missing.append('user_self_select_policy')
            if 'UPDATE' not in policy_commands:
                missing.append('user_self_update_policy')
                
        elif table.references_users and table.name != 'users':
            if 'SELECT' not in policy_commands:
                missing.append('user_data_select_policy')
            if 'INSERT' not in policy_commands:
                missing.append('user_data_insert_policy')
            if 'UPDATE' not in policy_commands:
                missing.append('user_data_update_policy')
                
        # Check for admin policies on sensitive tables
        if table.needs_admin_access_policy:
            admin_policy_exists = any(
                'admin' in str(policy.get('qual', '')) or 'admin' in str(policy.get('with_check', ''))
                for policy in table.policies
            )
            if not admin_policy_exists:
                missing.append('admin_access_policy')
                
        return missing
        
    async def generate_rls_fixes(self, tables: List[TableInfo]) -> List[str]:
        """Generate SQL statements to fix RLS issues."""
        sql_statements = []
        
        for table in tables:
            # Enable RLS if not enabled
            if not table.has_rls:
                sql_statements.append(f"-- Enable RLS for {table.name}")
                sql_statements.append(f"ALTER TABLE {table.schema}.{table.name} ENABLE ROW LEVEL SECURITY;")
                sql_statements.append("")
                
            # Add missing policies
            missing_policies = self.check_missing_policies(table)
            if missing_policies and table.has_rls:
                sql_statements.extend(self.generate_policies_for_table(table))
                
        return sql_statements
        
    def generate_policies_for_table(self, table: TableInfo) -> List[str]:
        """Generate RLS policies for a specific table."""
        policies = []
        table_name = f"{table.schema}.{table.name}"
        
        if table.name == 'users':
            # Users can only access their own records
            policies.extend([
                f"-- RLS policies for {table.name}",
                f"CREATE POLICY \"users_self_select\" ON {table_name}",
                f"    FOR SELECT USING (id = auth.uid());",
                f"",
                f"CREATE POLICY \"users_self_update\" ON {table_name}",
                f"    FOR UPDATE USING (id = auth.uid());",
                f""
            ])
            
        elif table.name == 'policy_records':
            policies.extend([
                f"-- RLS policies for {table.name}",
                f"CREATE POLICY \"policy_records_user_access\" ON {table_name}",
                f"    FOR SELECT USING (",
                f"        EXISTS (",
                f"            SELECT 1 FROM user_policy_links",
                f"            WHERE user_policy_links.policy_id = policy_records.policy_id",
                f"            AND user_policy_links.user_id = auth.uid()",
                f"            AND user_policy_links.relationship_verified = true",
                f"        )",
                f"    );",
                f"",
                f"CREATE POLICY \"policy_records_admin_access\" ON {table_name}",
                f"    FOR ALL USING (",
                f"        EXISTS (",
                f"            SELECT 1 FROM user_roles ur",
                f"            JOIN roles r ON r.id = ur.role_id",
                f"            WHERE ur.user_id = auth.uid()",
                f"            AND r.name = 'admin'",
                f"        )",
                f"    );",
                f""
            ])
            
        elif table.name == 'user_policy_links':
            policies.extend([
                f"-- RLS policies for {table.name}",
                f"CREATE POLICY \"user_policy_links_user_access\" ON {table_name}",
                f"    FOR SELECT USING (user_id = auth.uid());",
                f"",
                f"CREATE POLICY \"user_policy_links_admin_access\" ON {table_name}",
                f"    FOR ALL USING (",
                f"        EXISTS (",
                f"            SELECT 1 FROM user_roles ur",
                f"            JOIN roles r ON r.id = ur.role_id",
                f"            WHERE ur.user_id = auth.uid()",
                f"            AND r.name = 'admin'",
                f"        )",
                f"    );",
                f""
            ])
            
        elif table.name == 'policy_access_logs':
            policies.extend([
                f"-- RLS policies for {table.name}",
                f"CREATE POLICY \"policy_access_logs_user_access\" ON {table_name}",
                f"    FOR SELECT USING (user_id = auth.uid());",
                f"",
                f"CREATE POLICY \"policy_access_logs_admin_access\" ON {table_name}",
                f"    FOR ALL USING (",
                f"        EXISTS (",
                f"            SELECT 1 FROM user_roles ur",
                f"            JOIN roles r ON r.id = ur.role_id",
                f"            WHERE ur.user_id = auth.uid()",
                f"            AND r.name = 'admin'",
                f"        )",
                f"    );",
                f""
            ])
            
        elif table.name == 'agent_policy_context':
            policies.extend([
                f"-- RLS policies for {table.name}",
                f"CREATE POLICY \"agent_policy_context_user_access\" ON {table_name}",
                f"    FOR SELECT USING (user_id = auth.uid());",
                f"",
                f"CREATE POLICY \"agent_policy_context_admin_access\" ON {table_name}",
                f"    FOR ALL USING (",
                f"        EXISTS (",
                f"            SELECT 1 FROM user_roles ur",
                f"            JOIN roles r ON r.id = ur.role_id",
                f"            WHERE ur.user_id = auth.uid()",
                f"            AND r.name = 'admin'",
                f"        )",
                f"    );",
                f""
            ])
            
        elif table.name in ['roles', 'user_roles']:
            policies.extend([
                f"-- RLS policies for {table.name}",
                f"CREATE POLICY \"{table.name}_admin_access\" ON {table_name}",
                f"    FOR ALL USING (",
                f"        EXISTS (",
                f"            SELECT 1 FROM user_roles ur",
                f"            JOIN roles r ON r.id = ur.role_id",
                f"            WHERE ur.user_id = auth.uid()",
                f"            AND r.name = 'admin'",
                f"        )",
                f"    );",
                f""
            ])
            
        elif table.name in ['encryption_keys', 'policy_access_policies']:
            policies.extend([
                f"-- RLS policies for {table.name}",
                f"CREATE POLICY \"{table.name}_admin_only\" ON {table_name}",
                f"    FOR ALL USING (",
                f"        EXISTS (",
                f"            SELECT 1 FROM user_roles ur",
                f"            JOIN roles r ON r.id = ur.role_id",
                f"            WHERE ur.user_id = auth.uid()",
                f"            AND r.name = 'admin'",
                f"        )",
                f"    );",
                f""
            ])
            
        # Note: regulatory_documents already has proper RLS policies
        
        return policies
        
    async def apply_fixes(self, sql_statements: List[str], dry_run: bool = True) -> Dict[str, Any]:
        """Apply the RLS fixes to the database."""
        results = {
            'successful': [],
            'failed': [],
            'dry_run': dry_run
        }
        
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be applied")
            for statement in sql_statements:
                if statement.strip() and not statement.startswith('--'):
                    results['successful'].append(statement.strip())
            return results
            
        # Apply fixes
        for statement in sql_statements:
            if statement.strip() and not statement.startswith('--'):
                try:
                    await self.connection.execute(statement)
                    results['successful'].append(statement.strip())
                    logger.info(f"Successfully executed: {statement.strip()}")
                except Exception as e:
                    error_msg = f"Failed to execute '{statement.strip()}': {e}"
                    results['failed'].append(error_msg)
                    self.audit_result.errors.append(error_msg)
                    logger.error(error_msg)
                    
        return results
        
    async def test_rls_policies(self) -> Dict[str, Any]:
        """Test that RLS policies are working correctly."""
        test_results = {
            'passed': [],
            'failed': [],
            'skipped': []
        }
        
        # Test basic RLS functionality
        try:
            # Check if RLS is enabled on key tables
            key_tables = ['users', 'policy_records', 'user_policy_links', 'policy_access_logs']
            
            for table in key_tables:
                rls_check = await self.connection.fetchval(
                    "SELECT rowsecurity FROM pg_tables WHERE tablename = $1 AND schemaname = 'public'",
                    table
                )
                
                if rls_check:
                    test_results['passed'].append(f"RLS enabled on {table}")
                else:
                    test_results['failed'].append(f"RLS not enabled on {table}")
                    
        except Exception as e:
            test_results['failed'].append(f"Error testing RLS: {e}")
            
        return test_results
        
    def generate_report(self, tables: List[TableInfo], fixes_applied: Dict[str, Any], 
                       test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive report of the RLS audit and fixes."""
        report = {
            'audit_summary': asdict(self.audit_result),
            'tables_details': [asdict(table) for table in tables],
            'fixes_applied': fixes_applied,
            'test_results': test_results,
            'recommendations': []
        }
        
        # Add recommendations
        if self.audit_result.tables_without_rls:
            report['recommendations'].append(
                "Enable RLS on all tables that contain user-specific or sensitive data"
            )
            
        if self.audit_result.tables_with_incomplete_policies:
            report['recommendations'].append(
                "Create comprehensive RLS policies for all tables with user data"
            )
            
        report['recommendations'].extend([
            "Regularly audit RLS policies to ensure they meet security requirements",
            "Test RLS policies with different user roles to verify access controls",
            "Monitor access logs for any suspicious activity",
            "Consider implementing additional policies for specific business requirements"
        ])
        
        return report
        
    async def run_audit(self, dry_run: bool = True, apply_fixes: bool = False) -> Dict[str, Any]:
        """Run the complete RLS audit and fix process."""
        try:
            await self.connect()
            
            # Step 1: Analyze current state
            logger.info("Step 1: Analyzing current RLS state...")
            tables = await self.get_all_tables()
            issues = await self.analyze_rls_issues(tables)
            
            # Step 2: Generate fixes
            logger.info("Step 2: Generating RLS fixes...")
            sql_fixes = await self.generate_rls_fixes(tables)
            
            # Step 3: Apply fixes (if requested)
            fixes_applied = {'successful': [], 'failed': [], 'dry_run': True}
            if apply_fixes:
                logger.info("Step 3: Applying RLS fixes...")
                fixes_applied = await self.apply_fixes(sql_fixes, dry_run=dry_run)
            else:
                logger.info("Step 3: Skipping fix application (use --apply-fixes to enable)")
                
            # Step 4: Test policies
            logger.info("Step 4: Testing RLS policies...")
            test_results = await self.test_rls_policies()
            
            # Step 5: Generate report
            logger.info("Step 5: Generating report...")
            report = self.generate_report(tables, fixes_applied, test_results)
            
            return report
            
        finally:
            await self.disconnect()

async def main():
    """Main function to run the RLS audit."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Audit and fix RLS issues in the database')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without applying')
    parser.add_argument('--apply-fixes', action='store_true', help='Apply the fixes to the database')
    parser.add_argument('--database-url', help='Database URL (defaults to DATABASE_URL env var)')
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("Database URL not provided. Use --database-url or set DATABASE_URL environment variable")
        return
        
    # Run audit
    auditor = RLSAuditor(database_url)
    report = await auditor.run_audit(dry_run=args.dry_run, apply_fixes=args.apply_fixes)
    
    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'rls_audit_report_{timestamp}.json'
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
        
    logger.info(f"Report saved to {report_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("RLS AUDIT SUMMARY")
    print("="*60)
    print(f"Tables analyzed: {report['audit_summary']['tables_analyzed']}")
    print(f"Tables without RLS: {len(report['audit_summary']['tables_without_rls'])}")
    print(f"Tables with incomplete policies: {len(report['audit_summary']['tables_with_incomplete_policies'])}")
    print(f"Fixes applied: {len(report['fixes_applied']['successful'])}")
    print(f"Errors encountered: {len(report['audit_summary']['errors'])}")
    
    if report['audit_summary']['tables_without_rls']:
        print(f"\nTables without RLS: {', '.join(report['audit_summary']['tables_without_rls'])}")
        
    if report['audit_summary']['tables_with_incomplete_policies']:
        print(f"Tables with incomplete policies: {', '.join(report['audit_summary']['tables_with_incomplete_policies'])}")

if __name__ == "__main__":
    asyncio.run(main()) 