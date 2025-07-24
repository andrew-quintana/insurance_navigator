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
