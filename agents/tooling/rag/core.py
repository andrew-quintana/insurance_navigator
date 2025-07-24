"""
MVP RAG System - Core Components

Implements the baseline Retrieval-Augmented Generation (RAG) system for insurance document analysis agents.

Components:
- RetrievalConfig: Configurable parameters for retrieval (similarity threshold, max chunks, token budget)
- ChunkWithContext: Data structure for a document chunk with metadata and source attribution
- RAGTool: Main class for vector similarity search with user-scoped access and token budget enforcement

This MVP is designed for rapid, simple, and secure retrieval, serving as a control for future retrieval strategy experiments (cascading, recursive, etc.).
"""
import os
import asyncio
from typing import List, Optional, Any
from dataclasses import dataclass, field
import asyncpg
import logging

# --- RetrievalConfig ---
@dataclass
class RetrievalConfig:
    similarity_threshold: float = 0.7
    max_chunks: int = 10
    token_budget: int = 4000

    @classmethod
    def default(cls):
        return cls()

    def validate(self):
        assert 0.0 < self.similarity_threshold <= 1.0, "similarity_threshold must be in (0, 1]"
        assert self.max_chunks > 0, "max_chunks must be positive"
        assert self.token_budget > 0, "token_budget must be positive"

# --- ChunkWithContext ---
@dataclass
class ChunkWithContext:
    id: str
    doc_id: str
    chunk_index: int
    content: str
    section_path: Optional[List[int]] = field(default_factory=list)
    section_title: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    similarity: Optional[float] = None
    tokens: Optional[int] = None  # If available

# --- RAGTool ---
class RAGTool:
    def __init__(self, user_id: str, config: Optional[RetrievalConfig] = None):
        self.user_id = user_id
        self.config = config or RetrievalConfig.default()
        self.logger = logging.getLogger("RAGTool")

    async def retrieve_chunks(self, query_embedding: List[float]) -> List[ChunkWithContext]:
        self.config.validate()
        conn = None
        try:
            conn = await self._get_db_conn()
            # Query for top-k chunks with user-scoped access
            sql = f"""
                SELECT dc.id, dc.doc_id, dc.chunk_index, dc.content, dc.section_path, dc.section_title,
                       dc.page_start, dc.page_end, dc.tokens,
                       1 - (dc.embedding <=> $1) as similarity
                FROM documents.document_chunks dc
                JOIN documents.documents d ON dc.doc_id = d.id
                WHERE d.owner = $2
                  AND dc.embedding IS NOT NULL
                  AND 1 - (dc.embedding <=> $1) > $3
                ORDER BY dc.embedding <=> $1
                LIMIT $4
            """
            rows = await conn.fetch(sql, query_embedding, self.user_id, self.config.similarity_threshold, self.config.max_chunks)
            chunks = []
            total_tokens = 0
            for row in rows:
                tokens = row.get("tokens") or 0
                if total_tokens + tokens > self.config.token_budget:
                    break
                chunk = ChunkWithContext(
                    id=str(row["id"]),
                    doc_id=str(row["doc_id"]),
                    chunk_index=row["chunk_index"],
                    content=row["content"],
                    section_path=row["section_path"] or [],
                    section_title=row["section_title"],
                    page_start=row["page_start"],
                    page_end=row["page_end"],
                    similarity=row["similarity"],
                    tokens=tokens
                )
                chunks.append(chunk)
                total_tokens += tokens
            return chunks
        except Exception as e:
            self.logger.error(f"RAGTool retrieval error: {e}")
            return []
        finally:
            if conn:
                await conn.close()

    async def _get_db_conn(self):
        # Use environment variables for DB connection
        host = os.getenv("SUPABASE_DB_HOST", "127.0.0.1")
        port = int(os.getenv("SUPABASE_DB_PORT", "5432"))
        user = os.getenv("SUPABASE_DB_USER", "postgres")
        password = os.getenv("SUPABASE_DB_PASSWORD", "postgres")
        database = os.getenv("SUPABASE_DB_NAME", "postgres")
        return await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
        )
