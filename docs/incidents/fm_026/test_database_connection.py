#!/usr/bin/env python3
"""
FRACAS FM-026 Database Connection Test Script

This script tests database connections to identify the root cause of the
SCRAM authentication failure in the staging API service.

Error: 'NoneType' object has no attribute 'group'
Location: asyncpg.protocol.scram.SCRAMAuthentication.verify_server_final_message
"""

import asyncio
import asyncpg
import os
import sys
from typing import Optional, Dict, Any

class DatabaseConnectionTester:
    def __init__(self):
        self.results = []
    
    async def test_connection(self, name: str, connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """Test a database connection with given parameters."""
        result = {
            'name': name,
            'success': False,
            'error': None,
            'connection_params': connection_params
        }
        
        try:
            print(f"\n🔍 Testing connection: {name}")
            print(f"   Host: {connection_params.get('host', 'N/A')}")
            print(f"   Port: {connection_params.get('port', 'N/A')}")
            print(f"   Database: {connection_params.get('database', 'N/A')}")
            print(f"   User: {connection_params.get('user', 'N/A')}")
            
            # Test connection
            conn = await asyncpg.connect(**connection_params)
            
            # Test basic query
            version = await conn.fetchval("SELECT version()")
            print(f"   ✅ Connection successful!")
            print(f"   📊 PostgreSQL version: {version[:50]}...")
            
            # Test upload_pipeline schema
            try:
                schema_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'upload_pipeline')"
                )
                print(f"   📋 upload_pipeline schema exists: {schema_exists}")
            except Exception as e:
                print(f"   ⚠️  Could not check schema: {e}")
            
            await conn.close()
            result['success'] = True
            
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            result['error'] = str(e)
        
        return result
    
    async def run_tests(self):
        """Run all database connection tests."""
        print("🚀 FRACAS FM-026 Database Connection Test")
        print("=" * 50)
        
        # Test 1: Current failing configuration (your-project)
        current_config = {
            'host': 'aws-0-us-west-1.pooler.supabase.com',
            'port': 6543,
            'database': 'postgres',
            'user': 'postgres.your-project',
            'password': 'ERaZFjC8QqJzK9mN',
            'ssl': 'require'
        }
        
        result1 = await self.test_connection("Current Config (your-project)", current_config)
        self.results.append(result1)
        
        # Test 2: FM-020 working configuration (dfgzeastcxnoqshgyotp)
        fm020_config = {
            'host': 'aws-0-us-west-1.pooler.supabase.com',
            'port': 6543,
            'database': 'postgres',
            'user': 'postgres.dfgzeastcxnoqshgyotp',
            'password': 'ERaZFjC8QqJzK9mN',  # Using same password for now
            'ssl': 'require'
        }
        
        result2 = await self.test_connection("FM-020 Config (dfgzeastcxnoqshgyotp)", fm020_config)
        self.results.append(result2)
        
        # Test 3: Direct database connection (your-project)
        direct_config = {
            'host': 'db.your-project.supabase.co',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': 'ERaZFjC8QqJzK9mN',
            'ssl': 'require'
        }
        
        result3 = await self.test_connection("Direct DB (your-project)", direct_config)
        self.results.append(result3)
        
        # Test 4: Direct database connection (dfgzeastcxnoqshgyotp)
        direct_config_dfgz = {
            'host': 'db.dfgzeastcxnoqshgyotp.supabase.co',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': 'ERaZFjC8QqJzK9mN',
            'ssl': 'require'
        }
        
        result4 = await self.test_connection("Direct DB (dfgzeastcxnoqshgyotp)", direct_config_dfgz)
        self.results.append(result4)
        
        # Test 5: Connection string format (your-project)
        connection_string = "postgresql://postgres.your-project:ERaZFjC8QqJzK9mN@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
        
        try:
            print(f"\n🔍 Testing connection string: your-project")
            conn = await asyncpg.connect(connection_string, ssl='require')
            version = await conn.fetchval("SELECT version()")
            print(f"   ✅ Connection string successful!")
            print(f"   📊 PostgreSQL version: {version[:50]}...")
            await conn.close()
            self.results.append({
                'name': 'Connection String (your-project)',
                'success': True,
                'error': None,
                'connection_params': {'connection_string': connection_string}
            })
        except Exception as e:
            print(f"   ❌ Connection string failed: {e}")
            self.results.append({
                'name': 'Connection String (your-project)',
                'success': False,
                'error': str(e),
                'connection_params': {'connection_string': connection_string}
            })
        
        # Test 6: Connection string format (dfgzeastcxnoqshgyotp)
        connection_string_dfgz = "postgresql://postgres.dfgzeastcxnoqshgyotp:ERaZFjC8QqJzK9mN@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
        
        try:
            print(f"\n🔍 Testing connection string: dfgzeastcxnoqshgyotp")
            conn = await asyncpg.connect(connection_string_dfgz, ssl='require')
            version = await conn.fetchval("SELECT version()")
            print(f"   ✅ Connection string successful!")
            print(f"   📊 PostgreSQL version: {version[:50]}...")
            await conn.close()
            self.results.append({
                'name': 'Connection String (dfgzeastcxnoqshgyotp)',
                'success': True,
                'error': None,
                'connection_params': {'connection_string': connection_string_dfgz}
            })
        except Exception as e:
            print(f"   ❌ Connection string failed: {e}")
            self.results.append({
                'name': 'Connection String (dfgzeastcxnoqshgyotp)',
                'success': False,
                'error': str(e),
                'connection_params': {'connection_string': connection_string_dfgz}
            })
    
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]
        
        print(f"✅ Successful connections: {len(successful)}")
        print(f"❌ Failed connections: {len(failed)}")
        
        if successful:
            print("\n✅ WORKING CONFIGURATIONS:")
            for result in successful:
                print(f"   - {result['name']}")
        
        if failed:
            print("\n❌ FAILED CONFIGURATIONS:")
            for result in failed:
                print(f"   - {result['name']}: {result['error']}")
        
        print("\n🔍 RECOMMENDATIONS:")
        if any(r['name'].startswith('FM-020') and r['success'] for r in self.results):
            print("   - Use FM-020 configuration (dfgzeastcxnoqshgyotp project)")
        elif any(r['name'].startswith('Direct DB (dfgzeastcxnoqshgyotp)') and r['success'] for r in self.results):
            print("   - Use direct database connection to dfgzeastcxnoqshgyotp")
        else:
            print("   - Investigate Supabase project configurations")
            print("   - Check authentication credentials")
            print("   - Verify network connectivity")

async def main():
    """Main test function."""
    tester = DatabaseConnectionTester()
    
    try:
        await tester.run_tests()
        tester.print_summary()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
