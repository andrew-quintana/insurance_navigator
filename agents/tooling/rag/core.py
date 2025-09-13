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
    """
    Configuration for RAG retrieval.
    Args:
        similarity_threshold: Minimum similarity for chunk inclusion (0, 1].
        max_chunks: Maximum number of chunks to return.
        token_budget: Maximum total tokens for all returned chunks.
    """
    similarity_threshold: float = 0.01
    max_chunks: int = 10
    token_budget: int = 4000

    @classmethod
    def default(cls) -> "RetrievalConfig":
        """Return default configuration."""
        return cls()

    def validate(self) -> None:
        """Validate configuration parameters."""
        assert 0.0 < self.similarity_threshold <= 1.0, "similarity_threshold must be in (0, 1]"
        assert self.max_chunks > 0, "max_chunks must be positive"
        assert self.token_budget > 0, "token_budget must be positive"

# --- ChunkWithContext ---
@dataclass
class ChunkWithContext:
    """
    Data structure for a document chunk with context and metadata.
    Args:
        id: Unique chunk identifier
        doc_id: Document identifier
        chunk_index: Index of chunk in document
        content: Text content of the chunk
        section_path: Hierarchical section path (if available)
        section_title: Section title (if available)
        page_start: Start page (if available)
        page_end: End page (if available)
        similarity: Similarity score (if available)
        tokens: Token count (if available)
    """
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
    """
    Main class for Retrieval-Augmented Generation (RAG) using vector similarity search.
    Performs user-scoped access control and token budget enforcement.
    """
    def __init__(self, user_id: str, config: Optional[RetrievalConfig] = None):
        """
        Args:
            user_id: User identifier for access control
            config: RetrievalConfig instance (optional)
        """
        self.user_id = user_id
        self.config = config or RetrievalConfig.default()
        self.logger = logging.getLogger("RAGTool")

    async def retrieve_chunks(self, query_embedding: List[float]) -> List[ChunkWithContext]:
        """
        Retrieve document chunks most similar to the query embedding, enforcing user access and token budget.
        Args:
            query_embedding: List of floats (embedding vector)
        Returns:
            List of ChunkWithContext objects
        """
        self.config.validate()
        conn = None
        try:
            conn = await self._get_db_conn()
            # Query for top-k chunks with user-scoped access
            schema = os.getenv("DATABASE_SCHEMA", "upload_pipeline")
            
            # Convert Python list to PostgreSQL vector format (no spaces)
            vector_string = '[' + ','.join(str(x) for x in query_embedding) + ']'
            
            # Use string interpolation for vector parameter (asyncpg doesn't support vector parameter binding)
            sql = f"""
                SELECT dc.chunk_id, dc.document_id, dc.chunk_ord as chunk_index, dc.text as content,
                       NULL as section_path, NULL as section_title,
                       NULL as page_start, NULL as page_end,
                       NULL as tokens,
                       1 - (dc.embedding <=> '{vector_string}'::vector) as similarity
                FROM {schema}.document_chunks dc
                JOIN {schema}.documents d ON dc.document_id = d.document_id
                WHERE d.user_id = $1
                  AND dc.embedding IS NOT NULL
                  AND 1 - (dc.embedding <=> '{vector_string}'::vector) > $2
                ORDER BY dc.embedding <=> '{vector_string}'::vector
                LIMIT $3
            """
            rows = await conn.fetch(sql, self.user_id, self.config.similarity_threshold, self.config.max_chunks)
            chunks = []
            total_tokens = 0
            for row in rows:
                tokens = row.get("tokens") or 0
                if total_tokens + tokens > self.config.token_budget:
                    break
                chunk = ChunkWithContext(
                    id=str(row["chunk_id"]),
                    doc_id=str(row["document_id"]),
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

    async def retrieve_chunks_from_text(self, query_text: str) -> List[ChunkWithContext]:
        """
        Retrieve document chunks most similar to the query text, generating embedding internally.
        This is the main method that should be used by agents - it handles embedding generation internally.
        
        Args:
            query_text: Natural language query text
        Returns:
            List of ChunkWithContext objects
        """
        try:
            # Step 1: Generate embedding for the query text (MUST happen first)
            query_embedding = await self._generate_embedding(query_text)
            
            # Step 2: Use the generated embedding to perform similarity search
            return await self.retrieve_chunks(query_embedding)
            
        except Exception as e:
            self.logger.error(f"RAGTool text retrieval error: {e}")
            return []

    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI text-embedding-3-small model.
        
        Args:
            text: Text to embed
        Returns:
            List of floats representing the embedding
        """
        try:
            import openai
            import os
            
            # Set OpenAI API key if not already set
            if not openai.api_key:
                openai.api_key = os.getenv('OPENAI_API_KEY')
            
            if not openai.api_key:
                self.logger.warning("OPENAI_API_KEY not found, falling back to mock embedding")
                return self._generate_mock_embedding(text)
            
            # Generate real OpenAI embedding
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            self.logger.warning(f"OpenAI embedding failed ({e}), falling back to mock embedding")
            return self._generate_mock_embedding(text)
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """
        Generate a mock embedding for testing purposes.
        
        Args:
            text: Text to embed
        Returns:
            List of floats representing a mock embedding
        """
        # Generate a deterministic mock embedding based on text content
        import hashlib
        import random
        
        # Use text hash as seed for deterministic mock embeddings
        text_hash = hashlib.md5(text.encode()).hexdigest()
        random.seed(int(text_hash[:8], 16))
        
        # Generate 1536-dimensional mock embedding
        mock_embedding = [random.uniform(-1, 1) for _ in range(1536)]
        
        self.logger.warning(f"Using mock embedding for text: {text[:50]}...")
        return mock_embedding

    async def _get_db_conn(self) -> Any:
        """
        Get an asyncpg database connection using environment variables.
        Returns:
            asyncpg.Connection
        """
        # Try to use DATABASE_URL first, then fall back to individual parameters
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            try:
                return await asyncpg.connect(database_url)
            except Exception as e:
                self.logger.warning(f"Failed to connect using DATABASE_URL: {e}, falling back to individual parameters")
        
        # Fallback to individual environment variables
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
