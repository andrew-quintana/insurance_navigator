"""
Script to update document vectors for a specific user.
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables from .env file
load_dotenv()

def main():
    # Supabase connection details
    supabase_url = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_key:
        print("Error: SUPABASE_SERVICE_ROLE_KEY environment variable not set")
        print("Please make sure .env file exists and contains SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)

    try:
        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Target user ID to set for all records
        target_user_id = "27b30e9d-0d06-4325-910f-20fe9d686f14"
        
        # First, check what user IDs exist in the table
        print("Checking existing user IDs in document_vectors table...")
        response = supabase.table("document_vectors").select("user_id", count="exact").execute()
        print(f"Total records in table: {response.count}")
        
        # Get unique user IDs
        user_ids = set(row['user_id'] for row in response.data)
        print("\nUnique user IDs found:")
        for user_id in user_ids:
            count = len([row for row in response.data if row['user_id'] == user_id])
            print(f"- {user_id}: {count} records")
        
        # Now perform the update for records that don't have the target user ID
        print(f"\nUpdating records to target user ID: {target_user_id}")
        response = supabase.table("document_vectors").update({"user_id": target_user_id}).neq("user_id", target_user_id).execute()
        
        print(f"Update completed. Response:", response)
        
    except Exception as e:
        print(f"Error updating document vectors: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
 