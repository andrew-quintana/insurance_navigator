"""Script to set up the test database in Supabase."""
import os
import sys
from pathlib import Path
from supabase import create_client

def setup_test_database():
    """Set up the test database in Supabase."""
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")  # Note: Using service key for admin operations
    
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        sys.exit(1)
    
    try:
        # Initialize Supabase client
        supabase = create_client(url, key)
        
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
                    supabase.rpc("exec_sql", {"sql": statement}).execute()
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