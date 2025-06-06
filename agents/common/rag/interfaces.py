# RAG Interfaces - Phase 6
from typing import Protocol, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class ContextSourceType(Enum):
    VECTOR_STORE = "vector_store"
    USER_DOCUMENTS = "user_documents"

@dataclass
class ContextItem:
    content: str
    source_id: str
    relevance_score: float

class ContextRetriever(Protocol):
    async def retrieve_context(self, query: str, user_id: str) -> List[ContextItem]: ...
