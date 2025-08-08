"""
Memory service module for managing short-term chat memory.

Provides CRUD operations for `chat_metadata` and queue operations for
`chat_context_queue`, following existing Supabase client patterns.
"""

from typing import Optional, Dict, Any, List, Tuple
import logging
from fastapi import HTTPException, status
from supabase import Client as SupabaseClient
from config.database import get_supabase_client as get_base_client


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryService:
    """Service for managing chat memory and context queue."""

    def __init__(self, supabase_client: SupabaseClient) -> None:
        self.db = supabase_client
        self.metadata_table = "chat_metadata"
        self.queue_table = "chat_context_queue"

    # ------------------------------
    # Memory (chat_metadata) methods
    # ------------------------------
    async def get_memory(self, chat_id: str) -> Dict[str, Any]:
        """Retrieve memory for a chat. Returns defaults if missing."""
        try:
            response = await self.db.table(self.metadata_table).select("*").eq("chat_id", chat_id).execute()
            if getattr(response, "error", None):
                logger.error(f"Error retrieving memory for chat {chat_id}: {response.error}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

            if not response.data:
                return {
                    "chat_id": chat_id,
                    "user_confirmed": {},
                    "llm_inferred": {},
                    "general_summary": "",
                    "token_count": 0,
                    "last_updated": None,
                    "created_at": None,
                }

            return response.data[0]
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Unexpected error retrieving memory for chat {chat_id}: {exc}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    async def upsert_memory(
        self,
        chat_id: str,
        user_confirmed: Optional[Dict[str, Any]] = None,
        llm_inferred: Optional[Dict[str, Any]] = None,
        general_summary: Optional[str] = None,
        token_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Insert or update chat memory with validation."""
        payload: Dict[str, Any] = {"chat_id": chat_id}
        if user_confirmed is not None:
            if not isinstance(user_confirmed, dict):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="user_confirmed must be object")
            payload["user_confirmed"] = user_confirmed
        if llm_inferred is not None:
            if not isinstance(llm_inferred, dict):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="llm_inferred must be object")
            payload["llm_inferred"] = llm_inferred
        if general_summary is not None:
            if not isinstance(general_summary, str):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="general_summary must be string")
            payload["general_summary"] = general_summary
        if token_count is not None:
            if not isinstance(token_count, int) or token_count < 0:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="token_count must be non-negative integer")
            payload["token_count"] = token_count

        try:
            # Use upsert if available in supabase-py v2, else emulate with insert+on conflict
            response = await self.db.table(self.metadata_table).upsert(payload, on_conflict="chat_id").execute()
            if getattr(response, "error", None):
                logger.error(f"Error upserting memory for chat {chat_id}: {response.error}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
            return response.data[0] if response.data else payload
        except AttributeError:
            # Fallback: insert; if conflict, update
            try:
                insert_resp = await self.db.table(self.metadata_table).insert(payload).execute()
                if getattr(insert_resp, "error", None):
                    # Try update if conflict error
                    update_resp = await self.db.table(self.metadata_table).update(payload).eq("chat_id", chat_id).execute()
                    if getattr(update_resp, "error", None):
                        logger.error(f"Error updating memory for chat {chat_id}: {update_resp.error}")
                        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
                    return update_resp.data[0] if update_resp.data else payload
                return insert_resp.data[0] if insert_resp.data else payload
            except Exception as exc:
                logger.error(f"Unexpected error upserting memory for chat {chat_id}: {exc}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Unexpected error upserting memory for chat {chat_id}: {exc}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    # ------------------------------
    # Queue (chat_context_queue) methods
    # ------------------------------
    async def enqueue_context(self, chat_id: str, snippet: str, status_value: str = "pending_summarization") -> Dict[str, Any]:
        if not snippet or not isinstance(snippet, str):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="context_snippet must be non-empty string")

        payload = {
            "chat_id": chat_id,
            "new_context_snippet": snippet,
            "status": status_value,
        }
        try:
            response = await self.db.table(self.queue_table).insert(payload).execute()
            if getattr(response, "error", None):
                logger.error(f"Error enqueuing context for chat {chat_id}: {response.error}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Unexpected error enqueuing context for chat {chat_id}: {exc}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    async def update_queue_status(self, queue_id: str, status_value: str, error_message: Optional[str] = None, retry_increment: int = 0) -> bool:
        update_fields: Dict[str, Any] = {"status": status_value}
        if error_message is not None:
            update_fields["error_message"] = error_message
        if retry_increment:
            update_fields["retry_count"] = retry_increment  # caller responsible for computing next value if needed
        try:
            response = await self.db.table(self.queue_table).update(update_fields).eq("id", queue_id).execute()
            if getattr(response, "error", None):
                logger.error(f"Error updating queue {queue_id} status: {response.error}")
                return False
            return True
        except Exception as exc:
            logger.error(f"Unexpected error updating queue {queue_id} status: {exc}")
            return False

    async def get_pending_queue(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            response = await self.db.table(self.queue_table).select("*").eq("status", "pending_summarization").order("created_at", desc=False).limit(limit).execute()
            if getattr(response, "error", None):
                logger.error(f"Error querying pending queue: {response.error}")
                return []
            return response.data or []
        except Exception as exc:
            logger.error(f"Unexpected error querying pending queue: {exc}")
            return []


async def get_memory_service() -> MemoryService:
    """Factory for MemoryService matching existing service patterns."""
    try:
        client = await get_base_client()
        return MemoryService(client)
    except Exception as exc:
        logger.error(f"Error creating memory service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

