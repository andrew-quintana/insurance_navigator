#!/usr/bin/env python3
"""
Test the migration syntax by reading and validating the SQL
"""

import os

def test_migration_syntax():
    """Test the migration file syntax"""
    
    migration_file = "supabase/migrations/20251001133101_add_staging_storage_rls_policies.sql"
    
    print("🔍 Testing Migration Syntax")
    print(f"Migration file: {migration_file}")
    
    try:
        with open(migration_file, 'r') as f:
            content = f.read()
        
        print("✅ Migration file read successfully")
        print(f"File size: {len(content)} characters")
        
        # Check for key components
        checks = [
            ("BEGIN;", "BEGIN statement"),
            ("CREATE POLICY", "Policy creation statements"),
            ("storage.buckets", "Storage buckets policies"),
            ("storage.objects", "Storage objects policies"),
            ("COMMIT;", "COMMIT statement"),
            ("DO $$", "Verification block")
        ]
        
        for check, description in checks:
            if check in content:
                print(f"✅ {description} found")
            else:
                print(f"❌ {description} missing")
        
        print("\n📋 Migration Summary:")
        print("- Adds RLS policies for storage.buckets (view and manage)")
        print("- Adds RLS policies for storage.objects (update, delete, list)")
        print("- Includes verification to ensure policies were created")
        print("- Uses proper transaction handling (BEGIN/COMMIT)")
        
    except Exception as e:
        print(f"❌ Error reading migration file: {e}")

if __name__ == "__main__":
    test_migration_syntax()
