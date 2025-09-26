#!/usr/bin/env python3
"""
Apply Phase 3 migrations directly to the database
This script applies the upload_pipeline schema and RLS policies
"""

import os
import sys
import psycopg2
from pathlib import Path

def apply_migration_file(conn, migration_file):
    """Apply a single migration file to the database"""
    print(f"Applying migration: {migration_file.name}")
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print(f"✅ Successfully applied {migration_file.name}")
        return True
    except Exception as e:
        print(f"❌ Error applying {migration_file.name}: {e}")
        conn.rollback()
        return False

def main():
    """Apply Phase 3 migrations"""
    print("🚀 Applying Phase 3 migrations...")
    
    # Database connection
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            port=54322,
            database="postgres",
            user="postgres",
            password="postgres"
        )
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return 1
    
    # Get migration files in order
    migrations_dir = Path("supabase/migrations")
    migration_files = sorted([f for f in migrations_dir.glob("*.sql")])
    
    print(f"Found {len(migration_files)} migration files")
    
    # Apply migrations
    success_count = 0
    for migration_file in migration_files:
        if apply_migration_file(conn, migration_file):
            success_count += 1
    
    print(f"\n📊 Migration Summary:")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {len(migration_files) - success_count}")
    
    conn.close()
    
    if success_count == len(migration_files):
        print("🎉 All migrations applied successfully!")
        return 0
    else:
        print("💥 Some migrations failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
