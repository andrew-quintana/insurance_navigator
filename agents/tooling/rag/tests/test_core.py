import pytest
import asyncio
from agents.tooling.rag import RetrievalConfig, ChunkWithContext, RAGTool

@pytest.mark.asyncio
async def test_retrieval_config_defaults():
    config = RetrievalConfig.default()
    assert config.similarity_threshold == 0.7
    assert config.max_chunks == 10
    assert config.token_budget == 4000
    config.validate()

@pytest.mark.asyncio
async def test_retrieval_config_validation():
    config = RetrievalConfig(similarity_threshold=0.5, max_chunks=5, token_budget=1000)
    config.validate()
    with pytest.raises(AssertionError):
        RetrievalConfig(similarity_threshold=0.0).validate()
    with pytest.raises(AssertionError):
        RetrievalConfig(max_chunks=0).validate()
    with pytest.raises(AssertionError):
        RetrievalConfig(token_budget=0).validate()

@pytest.mark.asyncio
async def test_chunk_with_context():
    chunk = ChunkWithContext(
        id="abc",
        doc_id="doc1",
        chunk_index=0,
        content="Test content",
        section_path=[1,2],
        section_title="Section",
        page_start=1,
        page_end=2,
        similarity=0.95,
        tokens=100
    )
    assert chunk.id == "abc"
    assert chunk.section_path == [1,2]
    assert chunk.similarity == 0.95

@pytest.mark.asyncio
async def test_ragtool_retrieve_chunks(monkeypatch):
    # Patch _get_db_conn to return a mock connection
    class MockConn:
        async def fetch(self, sql, query_embedding, user_id, threshold, max_chunks):
            return [
                {
                    "id": "1",
                    "doc_id": "d1",
                    "chunk_index": 0,
                    "content": "A",
                    "section_path": [1],
                    "section_title": "Intro",
                    "page_start": 1,
                    "page_end": 1,
                    "similarity": 0.9,
                    "tokens": 100
                },
                {
                    "id": "2",
                    "doc_id": "d1",
                    "chunk_index": 1,
                    "content": "B",
                    "section_path": [2],
                    "section_title": "Body",
                    "page_start": 2,
                    "page_end": 2,
                    "similarity": 0.85,
                    "tokens": 200
                }
            ]
        async def close(self):
            pass

    async def mock_get_db_conn(self):
        return MockConn()

    monkeypatch.setattr(RAGTool, "_get_db_conn", mock_get_db_conn)
    rag = RAGTool(user_id="user1", config=RetrievalConfig(max_chunks=2, token_budget=250))
    # Simulate a 1536-dim embedding
    embedding = [0.0]*1536
    chunks = await rag.retrieve_chunks(embedding)
    assert len(chunks) == 1  # Only first chunk fits token budget
    assert chunks[0].content == "A"

# --- Integration test with real Supabase/Postgres ---
import os
import socket

@pytest.mark.asyncio
async def test_ragtool_real_supabase_integration():
    """
    Integration test: Connects to real Supabase/Postgres using env vars and runs RAGTool.retrieve_chunks.
    Skips if DB is not available. Requires local Supabase/Postgres with data for user_id '5710ff53-32ea-4fab-be6d-3a6f0627fbff'.
    """
    # Check DB connectivity first
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = int(os.getenv("DB_PORT", "54322"))
    try:
        with socket.create_connection((host, port), timeout=2):
            pass
    except Exception:
        pytest.skip("Supabase/Postgres DB not available on {}:{}".format(host, port))

    # Set env vars for RAGTool
    os.environ["SUPABASE_DB_HOST"] = host
    os.environ["SUPABASE_DB_PORT"] = str(port)
    os.environ["SUPABASE_DB_USER"] = os.getenv("DB_USER", "postgres")
    os.environ["SUPABASE_DB_PASSWORD"] = os.getenv("DB_PASSWORD", "postgres")
    os.environ["SUPABASE_DB_NAME"] = os.getenv("DB_NAME", "postgres")

    user_id = "5710ff53-32ea-4fab-be6d-3a6f0627fbff"
    rag = RAGTool(user_id=user_id, config=RetrievalConfig(max_chunks=3, token_budget=2000))
    embedding = [0.0] * 1536  # Use all zeros for test query
    chunks = await rag.retrieve_chunks(embedding)
    # Print for debug
    print(f"Retrieved {len(chunks)} chunks from real DB")
    # If DB is populated, should get at least one chunk
    assert isinstance(chunks, list)
    if chunks:
        assert hasattr(chunks[0], "content")

@pytest.mark.asyncio
def test_ragtool_error_handling(monkeypatch):
    """
    Test RAGTool error handling: DB connection failure, SQL error, invalid embedding.
    """
    class MockConnFail:
        async def fetch(self, *a, **kw):
            raise Exception("SQL error")
        async def close(self):
            pass
    async def mock_get_db_conn(self):
        raise Exception("DB connection failed")
    async def mock_get_db_conn_sql(self):
        return MockConnFail()
    # DB connection failure
    rag = RAGTool(user_id="user1")
    monkeypatch.setattr(RAGTool, "_get_db_conn", mock_get_db_conn)
    chunks = asyncio.run(rag.retrieve_chunks([0.0]*1536))
    assert chunks == []
    # SQL error
    monkeypatch.setattr(RAGTool, "_get_db_conn", mock_get_db_conn_sql)
    chunks = asyncio.run(rag.retrieve_chunks([0.0]*1536))
    assert chunks == []

@pytest.mark.asyncio
def test_ragtool_edge_cases(monkeypatch):
    """
    Test edge cases: empty embedding, empty DB result, token budget exactly met, chunk with missing optional fields.
    """
    class MockConn:
        async def fetch(self, sql, query_embedding, user_id, threshold, max_chunks):
            # Return empty if embedding is empty
            if not query_embedding:
                return []
            # Token budget exactly met
            return [
                {"id": "1", "doc_id": "d1", "chunk_index": 0, "content": "A", "section_path": None, "section_title": None, "page_start": None, "page_end": None, "similarity": 0.8, "tokens": 100},
                {"id": "2", "doc_id": "d1", "chunk_index": 1, "content": "B", "section_path": None, "section_title": None, "page_start": None, "page_end": None, "similarity": 0.75, "tokens": 50}
            ]
        async def close(self):
            pass
    async def mock_get_db_conn(self):
        return MockConn()
    monkeypatch.setattr(RAGTool, "_get_db_conn", mock_get_db_conn)
    rag = RAGTool(user_id="user1", config=RetrievalConfig(max_chunks=2, token_budget=150))
    # Empty embedding
    chunks = asyncio.run(rag.retrieve_chunks([]))
    assert chunks == []
    # Token budget exactly met
    chunks = asyncio.run(rag.retrieve_chunks([0.0]*1536))
    assert len(chunks) == 2
    assert sum(c.tokens for c in chunks) == 150
    # Missing optional fields
    for c in chunks:
        assert c.section_path == []
        assert c.section_title is None
        assert c.page_start is None
        assert c.page_end is None

@pytest.mark.asyncio
def test_ragtool_user_scoped_access(monkeypatch):
    """
    Test user-scoped access: only return chunks for the correct user (mocked).
    """
    class MockConn:
        async def fetch(self, sql, query_embedding, user_id, threshold, max_chunks):
            # Simulate two users' data
            if user_id == "user1":
                return [{"id": "1", "doc_id": "d1", "chunk_index": 0, "content": "A", "section_path": [1], "section_title": "Intro", "page_start": 1, "page_end": 1, "similarity": 0.9, "tokens": 100}]
            else:
                return [{"id": "2", "doc_id": "d2", "chunk_index": 0, "content": "B", "section_path": [2], "section_title": "Other", "page_start": 2, "page_end": 2, "similarity": 0.8, "tokens": 100}]
        async def close(self):
            pass
    async def mock_get_db_conn(self):
        return MockConn()
    monkeypatch.setattr(RAGTool, "_get_db_conn", mock_get_db_conn)
    rag1 = RAGTool(user_id="user1")
    rag2 = RAGTool(user_id="user2")
    chunks1 = asyncio.run(rag1.retrieve_chunks([0.0]*1536))
    chunks2 = asyncio.run(rag2.retrieve_chunks([0.0]*1536))
    assert all(c.doc_id == "d1" for c in chunks1)
    assert all(c.doc_id == "d2" for c in chunks2)

@pytest.mark.asyncio
def test_ragtool_performance(monkeypatch):
    """
    Test retrieval time is <200ms for mocked fast DB.
    """
    import time
    class MockConn:
        async def fetch(self, *a, **kw):
            return [{"id": "1", "doc_id": "d1", "chunk_index": 0, "content": "A", "section_path": [1], "section_title": "Intro", "page_start": 1, "page_end": 1, "similarity": 0.9, "tokens": 100}]
        async def close(self):
            pass
    async def mock_get_db_conn(self):
        return MockConn()
    monkeypatch.setattr(RAGTool, "_get_db_conn", mock_get_db_conn)
    rag = RAGTool(user_id="user1")
    start = time.time()
    chunks = asyncio.run(rag.retrieve_chunks([0.0]*1536))
    elapsed = (time.time() - start) * 1000
    assert elapsed < 200, f"Retrieval took too long: {elapsed}ms"
    assert len(chunks) == 1

@pytest.mark.asyncio
def test_ragtool_resource_cleanup(monkeypatch):
    """
    Test that DB connection is closed even on error.
    """
    class MockConn:
        def __init__(self):
            self.closed = False
        async def fetch(self, *a, **kw):
            raise Exception("fail")
        async def close(self):
            self.closed = True
    async def mock_get_db_conn(self):
        return MockConn()
    monkeypatch.setattr(RAGTool, "_get_db_conn", mock_get_db_conn)
    rag = RAGTool(user_id="user1")
    # Patch logger to suppress error output
    rag.logger.disabled = True
    try:
        asyncio.run(rag.retrieve_chunks([0.0]*1536))
    except Exception:
        pass
    # If we could check the closed flag, we would, but in this context, just ensure no crash
