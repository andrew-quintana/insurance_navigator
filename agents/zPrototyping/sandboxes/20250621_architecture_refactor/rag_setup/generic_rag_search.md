# Generic RAG Search Implementation

## Overview
This document outlines a flexible RAG search implementation that can handle both user-specific documents and regulatory/program documents in a single query. The system is designed to be domain-agnostic and reusable across different use cases.

## Core Functionality

### Search Parameters
```python
class RAGSearchParams:
    query: str                    # The search query text
    user_id: Optional[str]        # User ID to search their specific documents
    document_types: List[str]     # Types of documents to search (e.g., ["user", "regulatory", "expert"])
    programs: List[str]           # Program contexts to search within (e.g., ["Medicare", "Medicaid", "SNAP"])
    max_chunks: int = 10          # Maximum number of chunks to return per document type
    chunk_overlap: bool = True    # Whether to allow overlapping chunks
```

### Search Flow
1. **User Document Search**
   - If user_id is provided, search through all documents owned by that user
   - Filter by specified document_types
   - Return most relevant chunks

2. **Program/Regulatory Search**
   - For each program in programs list:
     - Search through regulatory/program documents
     - Filter by document_types
     - Return most relevant chunks

3. **Result Merging**
   - Combine results from both searches
   - Deduplicate overlapping content
   - Sort by relevance score
   - Return formatted chunks with metadata

## Example Usage

```python
# Example search for insurance strategy validation
search_params = RAGSearchParams(
    query="HSA coverage for preventive care",
    user_id="user123",                              # Get user's specific documents
    document_types=["user", "regulatory", "policy"], # Search both user and regulatory docs
    programs=["Medicare", "HSA"]                     # Look in Medicare and HSA contexts
)

results = await rag_search(search_params)

# Results will contain:
# - Chunks from user123's documents about HSA/preventive care
# - Chunks from Medicare regulatory documents about HSA/preventive care
# - Chunks from HSA program documents about preventive care
```

## Implementation Details

### Vector Store Schema
```python
class DocumentMetadata:
    doc_id: str
    owner_id: Optional[str]      # User ID if user-owned
    doc_type: str               
    programs: List[str]          # Associated programs
    source_url: Optional[str]    # Original document source
    timestamp: datetime          # Last updated
```

### Chunk Format
```python
class ChunkData:
    text: str                    # The actual chunk content
    metadata: DocumentMetadata   # Source document metadata
    relevance_score: float       # Search relevance score
    chunk_id: str               # Unique chunk identifier
    prev_chunk_id: Optional[str] # Previous chunk in document
    next_chunk_id: Optional[str] # Next chunk in document
```

## Search Pipeline

1. **Query Processing**
   ```python
   async def process_query(params: RAGSearchParams) -> List[ChunkData]:
       user_chunks = []
       regulatory_chunks = []
       
       # Get user-specific documents if user_id provided
       if params.user_id:
           user_chunks = await search_user_documents(
               query=params.query,
               user_id=params.user_id,
               doc_types=params.document_types
           )
       
       # Get regulatory/program documents
       for program in params.programs:
           program_chunks = await search_program_documents(
               query=params.query,
               program=program,
               doc_types=params.document_types
           )
           regulatory_chunks.extend(program_chunks)
           
       # Merge and deduplicate results
       return merge_chunk_results(user_chunks, regulatory_chunks)
   ```

2. **Result Processing**
   - Deduplicate similar chunks
   - Ensure context continuity
   - Add source attribution
   - Format for LLM consumption

## Usage Considerations

1. **Performance Optimization**
   - Implement caching for frequently accessed chunks
   - Use batch processing for multiple program searches
   - Consider parallel processing for user and regulatory searches

2. **Security**
   - Ensure user can only access their own documents
   - Implement role-based access for regulatory documents
   - Log all search operations for audit

3. **Maintenance**
   - Regular reindexing of documents
   - Update vector embeddings when documents change
   - Monitor search performance and relevance

## Integration Points

1. **Document Processing**
   - Document ingestion pipeline
   - Chunking strategy
   - Embedding generation

2. **Search Infrastructure**
   - Vector store selection
   - Indexing strategy
   - Query optimization

3. **Result Handling**
   - Context window management
   - Result ranking
   - Response formatting 