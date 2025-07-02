"""Script to set up the test database in Supabase."""
import os
import sys
from pathlib import Path
from supabase import create_client
from tests.config.test_config import get_supabase_test_config
from tests.db.helpers import get_test_client

def setup_test_database():
    """Set up the test database in Supabase."""
    try:
        # Get test configuration
        config = get_supabase_test_config()
        
        # Initialize Supabase client with service role key
        client = get_test_client(auth_type="service_role")
        
        # Read and execute SQL setup script
        sql_path = Path(__file__).parent / "setup_test_db.sql"
        with open(sql_path, "r") as f:
            sql = f.read()
        
        # Split SQL into individual statements
        statements = sql.split(";")
        
        # Execute each statement
        for statement in statements:
            if statement.strip():
                try:
                    client.rpc("exec_sql", {"sql": statement}).execute()
                    print(f"Successfully executed: {statement[:50]}...")
                except Exception as e:
                    print(f"Error executing statement: {statement[:50]}...")
                    print(f"Error: {str(e)}")
                    raise
        
        print("Test database setup completed successfully")
        
    except Exception as e:
        print(f"Error setting up test database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    setup_test_database() 