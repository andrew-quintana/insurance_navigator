"""Helper utilities for database testing."""

import os
from typing import Optional
from supabase import create_client, Client

def get_test_client(auth_type: str = "anon") -> Client:
    """Get a Supabase client for testing.
    Uses the main .env configuration.
    
    Args:
        auth_type: The type of authentication to use. Either "anon" or "service_role".
    
    Returns:
        Client: A configured Supabase client for testing
    
    Raises:
        ValueError: If required environment variables are not set
    """
    url = os.getenv("SUPABASE_URL")
    
    if auth_type == "service_role":
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable must be set")
    else:
        key = os.getenv("SUPABASE_ANON_KEY")
        if not key:
            raise ValueError("SUPABASE_ANON_KEY environment variable must be set")
    
    if not url:
        raise ValueError("SUPABASE_URL environment variable must be set")
    
    return create_client(url, key)

def cleanup_test_data(supabase: Client, document_id: Optional[str] = None, user_id: Optional[str] = None):
    """Clean up test data from the database.
    
    Args:
        supabase: The Supabase client
        document_id: Optional document ID to clean up
        user_id: Optional user ID to clean up all associated data
    """
    if document_id:
        # Clean up vectors first due to foreign key constraint
        supabase.table("document_vectors").delete().eq("document_record_id", document_id).execute()
        # Clean up the document
        supabase.table("documents").delete().eq("id", document_id).execute()
    
    if user_id:
        # Get all documents for user
        docs = supabase.table("documents").select("id").eq("user_id", user_id).execute()
        if docs.data:
            for doc in docs.data:
                cleanup_test_data(supabase, doc["id"])
        
        # Clean up any orphaned vectors
        supabase.table("document_vectors").delete().eq("user_id", user_id).execute()
