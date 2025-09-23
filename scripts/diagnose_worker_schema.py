#!/usr/bin/env python3
"""
Worker Database Schema Diagnostic Script

This script helps diagnose the missing database schema issue affecting the enhanced base worker.
Run this script to quickly identify what's missing and provide guidance for resolution.
"""

import asyncio
import asyncpg
import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

class WorkerSchemaDiagnostic:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'issues_found': [],
            'recommendations': [],
            'schema_status': {},
            'table_status': {}
        }
    
    async def run_diagnostic(self):
        """Run complete diagnostic check."""
        print("🔍 Starting Worker Database Schema Diagnostic...")
        print(f"📅 Timestamp: {self.results['timestamp']}")
        print(f"🔗 Database URL: {self.database_url[:50]}..." if self.database_url else "❌ No DATABASE_URL found")
        print()
        
        if not self.database_url:
            self.results['issues_found'].append("DATABASE_URL environment variable not set")
            self.results['recommendations'].append("Set DATABASE_URL environment variable")
            return self.results
        
        try:
            conn = await asyncpg.connect(self.database_url)
            print("✅ Database connection successful")
            
            # Check schema existence
            await self.check_schema_exists(conn)
            
            # Check required tables
            await self.check_required_tables(conn)
            
            # Check table structures
            await self.check_table_structures(conn)
            
            # Check permissions
            await self.check_permissions(conn)
            
            await conn.close()
            print("✅ Database connection closed")
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.results['issues_found'].append(f"Database connection failed: {e}")
            self.results['recommendations'].append("Check DATABASE_URL and database availability")
        
        self.generate_report()
        return self.results
    
    async def check_schema_exists(self, conn):
        """Check if upload_pipeline schema exists."""
        print("🔍 Checking upload_pipeline schema...")
        
        try:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.schemata 
                    WHERE schema_name = 'upload_pipeline'
                )
            """)
            
            if result:
                print("✅ upload_pipeline schema exists")
                self.results['schema_status']['upload_pipeline'] = 'EXISTS'
            else:
                print("❌ upload_pipeline schema does not exist")
                self.results['schema_status']['upload_pipeline'] = 'MISSING'
                self.results['issues_found'].append("upload_pipeline schema does not exist")
                self.results['recommendations'].append("Create upload_pipeline schema: CREATE SCHEMA upload_pipeline;")
                
        except Exception as e:
            print(f"❌ Error checking schema: {e}")
            self.results['issues_found'].append(f"Error checking schema: {e}")
    
    async def check_required_tables(self, conn):
        """Check if required tables exist."""
        print("🔍 Checking required tables...")
        
        required_tables = ['upload_jobs', 'documents', 'document_chunks']
        
        for table in required_tables:
            try:
                result = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'upload_pipeline' 
                        AND table_name = $1
                    )
                """, table)
                
                if result:
                    print(f"✅ upload_pipeline.{table} exists")
                    self.results['table_status'][table] = 'EXISTS'
                else:
                    print(f"❌ upload_pipeline.{table} does not exist")
                    self.results['table_status'][table] = 'MISSING'
                    self.results['issues_found'].append(f"upload_pipeline.{table} table does not exist")
                    
            except Exception as e:
                print(f"❌ Error checking table {table}: {e}")
                self.results['issues_found'].append(f"Error checking table {table}: {e}")
    
    async def check_table_structures(self, conn):
        """Check table structures if they exist."""
        print("🔍 Checking table structures...")
        
        tables_to_check = [k for k, v in self.results['table_status'].items() if v == 'EXISTS']
        
        for table in tables_to_check:
            try:
                columns = await conn.fetch("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_schema = 'upload_pipeline' 
                    AND table_name = $1
                    ORDER BY ordinal_position
                """, table)
                
                print(f"📋 upload_pipeline.{table} structure:")
                for col in columns:
                    print(f"   - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
                
            except Exception as e:
                print(f"❌ Error checking structure for {table}: {e}")
    
    async def check_permissions(self, conn):
        """Check database permissions."""
        print("🔍 Checking database permissions...")
        
        try:
            # Check if current user can create tables
            can_create = await conn.fetchval("""
                SELECT has_schema_privilege('upload_pipeline', 'CREATE')
            """)
            
            if can_create:
                print("✅ User has CREATE permission on upload_pipeline schema")
            else:
                print("❌ User lacks CREATE permission on upload_pipeline schema")
                self.results['issues_found'].append("User lacks CREATE permission on upload_pipeline schema")
                self.results['recommendations'].append("Grant CREATE permission: GRANT CREATE ON SCHEMA upload_pipeline TO current_user;")
                
        except Exception as e:
            print(f"❌ Error checking permissions: {e}")
            self.results['issues_found'].append(f"Error checking permissions: {e}")
    
    def generate_report(self):
        """Generate diagnostic report."""
        print("\n" + "="*60)
        print("📊 DIAGNOSTIC REPORT")
        print("="*60)
        
        if not self.results['issues_found']:
            print("✅ No issues found! Database schema appears to be correct.")
        else:
            print(f"❌ Found {len(self.results['issues_found'])} issues:")
            for i, issue in enumerate(self.results['issues_found'], 1):
                print(f"   {i}. {issue}")
        
        if self.results['recommendations']:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        print(f"\n📋 Schema Status:")
        for schema, status in self.results['schema_status'].items():
            print(f"   - {schema}: {status}")
        
        print(f"\n📋 Table Status:")
        for table, status in self.results['table_status'].items():
            print(f"   - {table}: {status}")
        
        print("\n" + "="*60)
    
    def save_report(self, filename: str = None):
        """Save diagnostic report to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"worker_schema_diagnostic_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📄 Report saved to: {filename}")

async def main():
    """Main diagnostic function."""
    diagnostic = WorkerSchemaDiagnostic()
    results = await diagnostic.run_diagnostic()
    
    # Save report
    diagnostic.save_report()
    
    # Exit with error code if issues found
    if results['issues_found']:
        print("\n❌ Issues found - exiting with error code 1")
        sys.exit(1)
    else:
        print("\n✅ No issues found - exiting with success code 0")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
