#!/usr/bin/env python3
"""
Database Connection Test

This script tests database connectivity to identify webhook timeout issues.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_database_connection():
    """Test database connection and identify issues."""
    print("🔍 TESTING DATABASE CONNECTION")
    print("=" * 50)
    
    try:
        # Test upload pipeline database
        print("1. Testing Upload Pipeline Database...")
        from api.upload_pipeline.database import get_database
        
        db = get_database()
        print(f"   Database manager created: {db is not None}")
        
        # Check if database is initialized
        print(f"   Database pool exists: {db.pool is not None}")
        
        if not db.pool:
            print("   Initializing database connection pool...")
            await db.initialize()
            print(f"   Database pool initialized: {db.pool is not None}")
        
        # Test connection
        print("   Testing database connection...")
        async with db.get_connection() as conn:
            print("   ✅ Database connection successful")
            
            # Test a simple query
            result = await conn.fetchval("SELECT 1")
            print(f"   ✅ Simple query successful: {result}")
            
            # Test the webhook query
            print("   Testing webhook query...")
            job = await conn.fetchrow("""
                SELECT uj.webhook_secret, uj.document_id, uj.status, d.user_id
                FROM upload_pipeline.upload_jobs uj
                JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
                WHERE uj.job_id = $1
            """, "test-job-123")
            
            if job:
                print(f"   ✅ Webhook query successful: {job}")
            else:
                print("   ⚠️  Webhook query returned no results (expected for test job)")
        
        print("✅ Upload Pipeline Database Test Passed")
        
    except Exception as e:
        print(f"❌ Upload Pipeline Database Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        # Test main database
        print("\n2. Testing Main Database...")
        from core.database import get_database as get_main_database
        
        main_db = get_main_database()
        print(f"   Main database manager created: {main_db is not None}")
        
        # Check if database is initialized
        print(f"   Main database pool exists: {main_db.pool is not None}")
        
        if not main_db.pool:
            print("   Initializing main database connection pool...")
            await main_db.initialize()
            print(f"   Main database pool initialized: {main_db.pool is not None}")
        
        # Test connection
        print("   Testing main database connection...")
        async with main_db.get_connection() as conn:
            print("   ✅ Main database connection successful")
            
            # Test a simple query
            result = await conn.fetchval("SELECT 1")
            print(f"   ✅ Simple query successful: {result}")
        
        print("✅ Main Database Test Passed")
        
    except Exception as e:
        print(f"❌ Main Database Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🎉 All Database Tests Passed!")
    return True

async def test_webhook_database_flow():
    """Test the exact database flow used in webhook handler."""
    print("\n🔍 TESTING WEBHOOK DATABASE FLOW")
    print("=" * 50)
    
    try:
        from api.upload_pipeline.database import get_database
        
        print("1. Getting database manager...")
        db = get_database()
        print(f"   Database manager: {db is not None}")
        
        print("2. Checking database pool...")
        if not db.pool:
            print("   Initializing database connection pool...")
            await db.initialize()
            print(f"   Database pool initialized: {db.pool is not None}")
        
        print("3. Testing webhook database flow...")
        async with db.get_connection() as conn:
            print("   ✅ Database connection established")
            
            # Test the exact webhook query
            job_id = "test-webhook-flow-123"
            print(f"   Testing webhook query for job_id: {job_id}")
            
            job = await conn.fetchrow("""
                SELECT uj.webhook_secret, uj.document_id, uj.status, d.user_id
                FROM upload_pipeline.upload_jobs uj
                JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
                WHERE uj.job_id = $1
            """, job_id)
            
            if job:
                print(f"   ✅ Webhook query successful: {job}")
            else:
                print("   ⚠️  Webhook query returned no results (expected for test job)")
                print("   This is normal - the job doesn't exist in the database")
        
        print("✅ Webhook Database Flow Test Passed")
        return True
        
    except Exception as e:
        print(f"❌ Webhook Database Flow Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("🚀 Starting Database Connection Tests")
    print("=" * 60)
    
    # Test basic database connections
    db_ok = await test_database_connection()
    
    if db_ok:
        # Test webhook-specific database flow
        webhook_ok = await test_webhook_database_flow()
        
        if webhook_ok:
            print("\n🎉 All database tests passed!")
            print("The webhook timeout issue is likely not related to database connectivity.")
            print("Check for other issues like:")
            print("- Infinite loops in webhook handler")
            print("- External API calls that are hanging")
            print("- File I/O operations that are blocking")
        else:
            print("\n❌ Webhook database flow failed!")
            print("This explains the webhook timeout issue.")
    else:
        print("\n❌ Basic database connection failed!")
        print("This explains the webhook timeout issue.")

if __name__ == "__main__":
    asyncio.run(main())
