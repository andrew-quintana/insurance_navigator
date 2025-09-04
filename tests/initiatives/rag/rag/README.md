# RAG Pipeline Test Suite

This directory contains comprehensive tests for the RAG (Retrieval-Augmented Generation) pipeline, including document vectorization, vector search, and LangGraph agent integration.

## Quick Start

### Test the current configured document:
```bash
python run_rag_tests.py --quick
```

### Test with your specific document ID:
```bash
python run_rag_tests.py d64bfbbe-ff7f-4b51-b220-a0fa20756d9d --quick
```

### Run all tests:
```bash
python run_rag_tests.py --all
```

## Files Overview

### Configuration
- `tests/config/rag_test_config.py` - Flexible test configuration with easily changeable document IDs

### Test Modules
- `test_rag_runner.py` - Basic RAG pipeline tests (document existence, vectorization, search)
- `test_langgraph_integration.py` - LangGraph workflow and agent integration tests

### Main Runner
- `run_rag_tests.py` - Main test runner with CLI interface

## Usage Examples

### 1. Quick Validation
Test that the RAG pipeline is working with the current document:
```bash
python run_rag_tests.py --quick
```

### 2. Test Specific Document
Change the document ID for testing:
```bash
python run_rag_tests.py abc12345-def6-7890-ghij-klmnopqrstuv
```

### 3. Run Basic Tests Only
```bash
python run_rag_tests.py
```

### 4. Run Integration Tests Only
```bash
python run_rag_tests.py --integration
```

### 5. Run Complete Test Suite
```bash
python run_rag_tests.py --all
```

## Configuration Management

### Changing the Default Document ID

Edit `tests/config/rag_test_config.py`:

```python
# Update this line with your new document ID
CURRENT_TEST_CONFIG = RAGTestConfig(
    primary_document=DocumentTestConfig(
        document_id="YOUR-NEW-DOCUMENT-ID-HERE",
        description="Updated test document"
    ),
    test_queries=[
        "What is the deductible amount?",
        "What are the copay requirements?", 
        # Add your test queries here
    ]
)
```

### Environment Variable Support

You can also set the document ID via environment variable:
```bash
export RAG_TEST_DOCUMENT_ID="d64bfbbe-ff7f-4b51-b220-a0fa20756d9d"
python run_rag_tests.py --quick
```

## Test Categories

### Basic RAG Tests
- **Document Exists**: Verifies the document is accessible in the database
- **Document Vectorized**: Confirms the document has been processed and vectorized
- **Vector Search**: Tests semantic search functionality

### Integration Tests
- **Workflow Creation**: Tests LangGraph workflow setup
- **Agent Discovery**: Verifies agent loading and discovery
- **RAG Agent Workflow**: Tests complete RAG workflow with agent integration

## Expected Output

### Successful Quick Test
```
RAG Pipeline Quick Tests
Document ID: d64bfbbe-ff7f-4b51-b220-a0fa20756d9d
User ID: 12345678-abcd-ef01-2345-6789abcdef01

✓ Document d64bfbbe-ff7f-4b51-b220-a0fa20756d9d exists with status: processed
✓ Document d64bfbbe-ff7f-4b51-b220-a0fa20756d9d has 15 vector chunks
✓ Vector search returned 5 results in 0.234s

✓ Quick validation PASSED - RAG pipeline is ready
```

## Troubleshooting

### Common Issues

1. **Document Not Found**
   - Verify the document ID exists in your database
   - Check user permissions for document access

2. **No Vector Chunks**
   - Ensure the document has been processed through the vectorization pipeline
   - Check if vectorization jobs completed successfully

3. **Search Returns No Results**
   - Verify embeddings were generated correctly
   - Check similarity thresholds in configuration

4. **Agent Discovery Fails**
   - Ensure LangGraph utilities are properly installed
   - Check agent module paths and imports

### Debug Mode
Run with verbose logging:
```bash
python run_rag_tests.py --verbose --all
```

## Extending Tests

### Adding New Test Queries
Edit the configuration:
```python
test_queries=[
    "What is the deductible amount?",
    "Your new test query here",
]
```

### Adding New Test Documents
```python
additional_documents=[
    DocumentTestConfig(
        document_id="another-doc-id",
        description="Additional test document"
    )
]
```

### Custom Test Scenarios
Create custom configurations programmatically:
```python
from tests.config.rag_test_config import create_custom_config

custom_config = create_custom_config(
    document_id="your-doc-id",
    test_queries=["Custom query 1", "Custom query 2"],
    vector_search_limit=20
)
```
