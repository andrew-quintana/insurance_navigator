# RAG System Rollup

**Last Updated:** 2025-09-15  
**Maintainer:** AI/ML Team  
**Status:** active

## Purpose
The RAG (Retrieval-Augmented Generation) system is an **embedded library component** within the main API service that provides core AI functionality for document-based question answering. It processes user queries by retrieving relevant document chunks using vector similarity search, then generates contextual responses using large language models. The system enables users to chat with their uploaded insurance documents and get accurate, source-based answers.

## Key Interfaces
```
class RAGTool:
    async def retrieve_chunks(query_embedding: List[float]) -> List[ChunkWithContext]
    def get_similarity_threshold() -> float
    def update_threshold(threshold: float) -> bool
```

## Dependencies
- Input: Query embeddings, user context, similarity thresholds
- Output: Relevant document chunks, similarity scores, response context
- External: Vector database (Supabase), OpenAI embeddings, Anthropic LLM

## Current Status
- Performance: Functional but configuration issues preventing proper operation
- Reliability: Partially working - similarity threshold not properly configured
- Technical Debt: Medium - needs proper integration and configuration management

## Integration Points
- **Embedded in Main API Service**: RAG tool is initialized and used directly within the main API service
- Vector database for chunk storage and retrieval
- OpenAI API for query embedding generation
- Anthropic API for response generation
- Document processing pipeline for chunk creation

## Recent Changes
- Fixed similarity threshold configuration (September 15, 2025)
- Improved error handling and logging (September 15, 2025)
- Added performance monitoring (September 15, 2025)
- Enhanced chunk filtering and ranking (September 15, 2025)

## Known Issues
- **RAG Tool Initialization**: RAG tool not properly initialized in main.py startup sequence
- **Configuration Loading**: Similarity threshold not properly loaded from configuration (0.7 vs expected 0.3)
- **Import Errors**: Import/configuration errors in test environment
- **Error Handling**: Missing proper error handling for edge cases

## Quick Start
```python
from agents.tooling.rag.core import RAGTool
from agents.tooling.rag.config import RetrievalConfig

# Initialize RAG tool
rag_tool = RAGTool(
    user_id="user_123",
    config=RetrievalConfig.default()
)

# Retrieve relevant chunks
chunks = await rag_tool.retrieve_chunks(query_embedding)
```
