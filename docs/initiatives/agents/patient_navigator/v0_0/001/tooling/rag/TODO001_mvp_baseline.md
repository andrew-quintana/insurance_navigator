# MVP RAG System - Baseline Documentation

## System Overview
The MVP RAG system provides a simple, robust baseline for retrieval-augmented generation in insurance document analysis agents. It implements:
- Vector similarity search over document chunks
- User-scoped access control (multi-tenant security)
- Token budget enforcement for efficient context retrieval
- Simple, extensible Python API

## API Reference (Summary)
- **RetrievalConfig**: Configuration dataclass for retrieval parameters (similarity_threshold, max_chunks, token_budget)
- **ChunkWithContext**: Data structure for chunk results, including content, metadata, and source attribution
- **RAGTool**: Main retrieval class; method `retrieve_chunks(query_embedding: List[float]) -> List[ChunkWithContext]`

## Agent Integration Pattern
- Use property-based lazy initialization for RAGTool in agents
- Integrate with BaseAgent pattern for stateless, testable agent logic
- Example:

```python
from agents.tooling.rag import RAGTool, RetrievalConfig
class MyAgent(BaseAgent):
    @property
    def rag_tool(self):
        if not hasattr(self, '_rag_tool'):
            self._rag_tool = RAGTool(self.user_id, RetrievalConfig.default())
        return self._rag_tool
```

## Performance Benchmarks
- Mocked DB: <200ms retrieval (validated in tests)
- Real DB: passes integration test (performance depends on environment)
- Robust error handling and resource cleanup

## Best Practices
- Always validate RetrievalConfig before use
- Handle errors gracefully (system returns empty result on DB/SQL/embedding errors)
- Enforce user-scoped access for security
- Monitor retrieval performance and resource usage

## Extension Points
- System is ready for plugin/expander strategies in future phases (see RFC001)
- Use this baseline for all future retrieval strategy experiments (cascading, recursive, hybrid, etc.)

## Status
- All tests pass, system is production-ready as MVP baseline
- Documentation and integration examples provided for agent developers 