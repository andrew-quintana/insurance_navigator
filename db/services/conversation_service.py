"""
Simplified Conversation Service for MVP Refactoring
Basic conversation storage and retrieval without complex agent state tracking.
Removes workflow states and agent orchestration complexity.
"""

import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import asyncpg

from .db_pool import get_db_pool
from ..config import config

logger = logging.getLogger(__name__)

class ConversationService:
    """Service for managing conversation history and agent state persistence."""
    
    def __init__(self):
        pass
    
    async def create_conversation(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new conversation."""
        try:
            if not conversation_id:
                conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
            
            pool = await get_db_pool()
            
            async with pool.get_connection() as conn:
                # Create conversations table if it doesn't exist
                await self._ensure_conversations_table(conn)
                
                await conn.execute(
                    """
                    INSERT INTO conversations (id, user_id, metadata, created_at, updated_at)
                    VALUES ($1, $2, $3, NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING
                    """,
                    conversation_id, uuid.UUID(user_id), json.dumps(metadata or {})
                )
                
                logger.info(f"Created conversation {conversation_id} for user {user_id}")
                return conversation_id
                
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        agent_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a message to the conversation."""
        try:
            message_id = str(uuid.uuid4())
            pool = await get_db_pool()
            
            async with pool.get_connection() as conn:
                # Create messages table if it doesn't exist
                await self._ensure_messages_table(conn)
                
                await conn.execute(
                    """
                    INSERT INTO conversation_messages 
                    (id, conversation_id, role, content, agent_name, metadata, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, NOW())
                    """,
                    message_id, conversation_id, role, content, 
                    agent_name, json.dumps(metadata or {})
                )
                
                # Update conversation last activity
                await conn.execute(
                    "UPDATE conversations SET updated_at = NOW() WHERE id = $1",
                    conversation_id
                )
                
                logger.debug(f"Added message to conversation {conversation_id}")
                return message_id
                
        except Exception as e:
            logger.error(f"Error adding message to conversation {conversation_id}: {str(e)}")
            raise
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50,
        include_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        """Get conversation message history."""
        try:
            pool = await get_db_pool()
            
            async with pool.get_connection() as conn:
                query = """
                    SELECT id, role, content, agent_name, created_at
                    {} 
                    FROM conversation_messages 
                    WHERE conversation_id = $1 
                    ORDER BY created_at ASC 
                    LIMIT $2
                """.format(", metadata" if include_metadata else "")
                
                rows = await conn.fetch(query, conversation_id, limit)
                
                messages = []
                for row in rows:
                    message = {
                        "id": row["id"],
                        "role": row["role"],
                        "content": row["content"],
                        "agent_name": row["agent_name"],
                        "created_at": row["created_at"]
                    }
                    
                    if include_metadata and row.get("metadata"):
                        message["metadata"] = json.loads(row["metadata"])
                    
                    messages.append(message)
                
                return messages
                
        except Exception as e:
            logger.error(f"Error getting conversation history {conversation_id}: {str(e)}")
            return []
    
    # REMOVED: save_agent_state - complex agent state tracking removed in MVP refactor
    
    # REMOVED: get_agent_state - complex agent state tracking removed in MVP refactor
    
    # REMOVED: Workflow state functions - complex orchestration removed in MVP refactor
    
    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get user's conversation list."""
        try:
            pool = await get_db_pool()
            
            async with pool.get_connection() as conn:
                rows = await conn.fetch(
                    """
                    SELECT c.id, c.metadata, c.created_at, c.updated_at,
                           COUNT(cm.id) as message_count
                    FROM conversations c
                    LEFT JOIN conversation_messages cm ON c.id = cm.conversation_id
                    WHERE c.user_id = $1
                    GROUP BY c.id, c.metadata, c.created_at, c.updated_at
                    ORDER BY c.updated_at DESC
                    LIMIT $2
                    """,
                    uuid.UUID(user_id), limit
                )
                
                conversations = []
                for row in rows:
                    conversation = {
                        "id": row["id"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "message_count": row["message_count"]
                    }
                    
                    if row["metadata"]:
                        conversation["metadata"] = json.loads(row["metadata"])
                    
                    conversations.append(conversation)
                
                return conversations
                
        except Exception as e:
            logger.error(f"Error getting user conversations for {user_id}: {str(e)}")
            return []
    
    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation and all related data."""
        try:
            pool = await get_db_pool()
            
            async with pool.get_connection() as conn:
                # Start transaction
                async with conn.transaction():
                    # Verify ownership
                    owner = await conn.fetchval(
                        "SELECT user_id FROM conversations WHERE id = $1",
                        conversation_id
                    )
                    
                    if not owner or str(owner) != user_id:
                        return False
                    
                    # Delete related data (simplified - no agent/workflow states)
                    await conn.execute(
                        "DELETE FROM conversation_messages WHERE conversation_id = $1",
                        conversation_id
                    )
                    
                    # Delete conversation
                    result = await conn.execute(
                        "DELETE FROM conversations WHERE id = $1",
                        conversation_id
                    )
                    
                    logger.info(f"Deleted conversation {conversation_id}")
                    return "DELETE" in result
                
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
            return False
    
    async def _ensure_conversations_table(self, conn: asyncpg.Connection) -> None:
        """Ensure conversations table exists."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id UUID NOT NULL,
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Create index if not exists
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)
        """)
    
    async def _ensure_messages_table(self, conn: asyncpg.Connection) -> None:
        """Ensure conversation_messages table exists."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                agent_name TEXT,
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Create indexes if not exist
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation_id 
            ON conversation_messages(conversation_id)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation_messages_created_at 
            ON conversation_messages(created_at)
        """)
    
    # REMOVED: Complex table creation functions for agent and workflow states

# Global conversation service instance
conversation_service = ConversationService()

async def get_conversation_service() -> ConversationService:
    """Get the global conversation service instance."""
    return conversation_service 