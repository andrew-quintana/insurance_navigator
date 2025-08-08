import asyncio
import pytest

from db.services.memory_service import MemoryService


pytestmark = pytest.mark.asyncio


@pytest.mark.unit
async def test_get_memory_returns_defaults_when_missing(monkeypatch):
    service = MemoryService(supabase_client=object())

    class MockResponse:
        data = []
        error = None

    async def _exec():
        return MockResponse()

    # Monkeypatch the supabase client chain: table(...).select(...).eq(...).execute()
    class MockQuery:
        async def execute(self):
            return MockResponse()

    class MockEq:
        def eq(self, *_args, **_kwargs):
            return MockQuery()

    class MockSelect:
        def select(self, *_args, **_kwargs):
            return MockEq()

    class MockTable:
        def table(self, *_args, **_kwargs):
            return MockSelect()

    service.db = MockTable()

    result = await service.get_memory("chat-xyz")
    assert result["chat_id"] == "chat-xyz"
    assert result["user_confirmed"] == {}
    assert result["llm_inferred"] == {}
    assert result["general_summary"] == ""


@pytest.mark.unit
async def test_upsert_memory_validates_types(monkeypatch):
    service = MemoryService(supabase_client=object())

    with pytest.raises(Exception):
        await service.upsert_memory("chat-1", user_confirmed="not-a-dict")

    with pytest.raises(Exception):
        await service.upsert_memory("chat-1", llm_inferred="not-a-dict")

    with pytest.raises(Exception):
        await service.upsert_memory("chat-1", general_summary={})

    with pytest.raises(Exception):
        await service.upsert_memory("chat-1", token_count=-1)


@pytest.mark.unit
async def test_enqueue_and_query_pending(monkeypatch):
    service = MemoryService(supabase_client=object())

    # Minimal mocks for insert and select
    class MockInsertResponse:
        error = None
        data = [{"id": "queue-1", "chat_id": "chat-1", "status": "pending_summarization"}]

    class MockSelectResponse:
        error = None
        data = [{"id": "queue-1", "chat_id": "chat-1", "status": "pending_summarization"}]

    class MockSelectQuery:
        def eq(self, *_args, **_kwargs):
            return self

        def order(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

        async def execute(self):
            return MockSelectResponse()

    class MockInsertQuery:
        async def execute(self):
            return MockInsertResponse()

    class MockTable:
        def __init__(self, name: str):
            self.name = name

        def insert(self, *_args, **_kwargs):
            return MockInsertQuery()

        def select(self, *_args, **_kwargs):
            return MockSelectQuery()

    class MockClient:
        def table(self, name: str):
            return MockTable(name)

    service.db = MockClient()

    enqueued = await service.enqueue_context("chat-1", "new info")
    assert enqueued["status"] == "pending_summarization"

    pending = await service.get_pending_queue(limit=10)
    assert len(pending) == 1
    assert pending[0]["chat_id"] == "chat-1"

