"""
Conversation service module for managing chat conversations.
"""
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status
from supabase import Client as SupabaseClient
import logging
from config.database import get_supabase_client_sync as get_base_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationService:
    """Service for managing chat conversations."""

    def __init__(self, supabase_client: SupabaseClient):
        """Initialize the conversation service."""
        self.supabase = supabase_client
        self.table = "conversations"

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID."""
        try:
            response = self.supabase.table(self.table).select("*").eq("id", conversation_id).execute()
            
            if response.error:
                logger.error(f"Error getting conversation {conversation_id}: {response.error}")
                return None
                
            if not response.data:
                return None
                
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}")
            return None

    def create_conversation(self, user_id: str, metadata: Dict[str, Any], conversation_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a new conversation."""
        try:
            data = {
                "user_id": user_id,
                "metadata": metadata
            }
            
            # Add ID if provided
            if conversation_id:
                data["id"] = conversation_id
            
            response = self.supabase.table(self.table).insert(data).execute()
            
            # Handle both old and new Supabase client response structures
            if hasattr(response, 'error') and response.error:
                logger.error(f"Error creating conversation: {response.error}")
                return None
            elif hasattr(response, 'data') and response.data:
                return response.data[0]
            else:
                logger.error(f"Unexpected response structure: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            return None

def get_conversation_service() -> ConversationService:
    """Get configured conversation service instance."""
    try:
        client = get_base_client()
        return ConversationService(client)
    except Exception as e:
        logger.error(f"Error creating conversation service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 