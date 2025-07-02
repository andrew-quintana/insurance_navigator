"""
Supabase client service for database operations.
"""

from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from postgrest import APIResponse

class SupabaseClient:
    """Client for interacting with Supabase."""
    
    def __init__(self, url: str, key: str):
        """
        Initialize Supabase client.
        
        Args:
            url: Supabase project URL
            key: Supabase project API key
        """
        self.client = create_client(url, key)
        
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID to look up
            
        Returns:
            User data if found, None otherwise
        """
        response = self.client.table("users").select("*").eq("id", user_id).execute()
        return response.data[0] if response.data else None
        
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            user_data: User data to insert
            
        Returns:
            Created user data
        """
        response = self.client.table("users").insert(user_data).execute()
        return response.data[0]
        
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user data.
        
        Args:
            user_id: ID of user to update
            user_data: New user data
            
        Returns:
            Updated user data
        """
        response = self.client.table("users").update(user_data).eq("id", user_id).execute()
        return response.data[0]
        
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: ID of user to delete
            
        Returns:
            True if successful, False otherwise
        """
        response = self.client.table("users").delete().eq("id", user_id).execute()
        return bool(response.data)
        
    def get_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all documents for a user.
        
        Args:
            user_id: User ID to get documents for
            
        Returns:
            List of document data
        """
        response = self.client.table("documents").select("*").eq("user_id", user_id).execute()
        return response.data
        
    def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new document.
        
        Args:
            document_data: Document data to insert
            
        Returns:
            Created document data
        """
        response = self.client.table("documents").insert(document_data).execute()
        return response.data[0]
        
    def update_document(self, doc_id: str, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update document data.
        
        Args:
            doc_id: ID of document to update
            document_data: New document data
            
        Returns:
            Updated document data
        """
        response = self.client.table("documents").update(document_data).eq("id", doc_id).execute()
        return response.data[0]
        
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document.
        
        Args:
            doc_id: ID of document to delete
            
        Returns:
            True if successful, False otherwise
        """
        response = self.client.table("documents").delete().eq("id", doc_id).execute()
        return bool(response.data) 