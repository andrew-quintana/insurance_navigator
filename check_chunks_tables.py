#!/usr/bin/env python3
"""
Check for chunks in all possible tables.
"""

import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.production')

async def check_chunks_tables():
    """Check for chunks in all possible tables."""
    try:
        # Connect to database
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return
            
        conn = await asyncpg.connect(database_url)
        
        print("🔍 Checking for chunks in all tables")
        print("=" * 50)
        
        # Check all schemas
        schemas_query = """
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY schema_name
        """
        
        schemas = await conn.fetch(schemas_query)
        print(f"📊 Available schemas:")
        for schema in schemas:
            print(f"  - {schema['schema_name']}")
        
        # Check all tables with 'chunk' in name
        chunk_tables_query = """
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE '%chunk%'
        ORDER BY table_schema, table_name
        """
        
        chunk_tables = await conn.fetch(chunk_tables_query)
        print(f"\n📊 Tables with 'chunk' in name:")
        for table in chunk_tables:
            print(f"  - {table['table_schema']}.{table['table_name']}")
        
        # Check all tables with 'embedding' in name
        embedding_tables_query = """
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE '%embedding%'
        ORDER BY table_schema, table_name
        """
        
        embedding_tables = await conn.fetch(embedding_tables_query)
        print(f"\n📊 Tables with 'embedding' in name:")
        for table in embedding_tables:
            print(f"  - {table['table_schema']}.{table['table_name']}")
        
        # Check all tables in upload_pipeline schema
        upload_tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'upload_pipeline'
        ORDER BY table_name
        """
        
        upload_tables = await conn.fetch(upload_tables_query)
        print(f"\n📊 Tables in upload_pipeline schema:")
        for table in upload_tables:
            print(f"  - {table['table_name']}")
        
        # Check if there are any tables with vector columns
        vector_tables_query = """
        SELECT table_schema, table_name, column_name, data_type
        FROM information_schema.columns 
        WHERE data_type LIKE '%vector%' OR column_name LIKE '%embedding%'
        ORDER BY table_schema, table_name, column_name
        """
        
        vector_tables = await conn.fetch(vector_tables_query)
        print(f"\n📊 Tables with vector/embedding columns:")
        for table in vector_tables:
            print(f"  - {table['table_schema']}.{table['table_name']}.{table['column_name']} ({table['data_type']})")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error checking chunks tables: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_chunks_tables())
