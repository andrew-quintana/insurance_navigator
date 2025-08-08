import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from scripts.workers.memory_processor import process_once
from agents.tooling.mcp.memory.summarizer_agent import MemorySummarizerAgent


@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_once_happy_path(monkeypatch):
    # Mock MemoryService
    service = MagicMock()
    service.get_pending_queue = AsyncMock(return_value=[{
        "id": "q1",
        "chat_id": "chat-1",
        "new_context_snippet": "User confirmed plan is HMO.",
        "retry_count": 0,
    }])
    service.get_memory = AsyncMock(return_value={
        "chat_id": "chat-1",
        "user_confirmed": {},
        "llm_inferred": {},
        "general_summary": "",
    })
    service.upsert_memory = AsyncMock(return_value={})
    service.update_queue_status = AsyncMock(return_value=True)

    # Mock agent
    agent = MemorySummarizerAgent(mock=True)

    processed = await process_once(service, agent, token_limit=8000)
    assert processed == 1
    service.upsert_memory.assert_awaited()
    service.update_queue_status.assert_awaited()

