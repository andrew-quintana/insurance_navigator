# BaseWorker Testing Framework

This directory contains comprehensive tests for the enhanced BaseWorker implementation, covering unit tests, integration tests, and performance tests.

## Test Structure

```
tests/
├── conftest.py                 # Common fixtures and configuration
├── unit/                       # Unit tests
│   └── test_base_worker.py    # BaseWorker unit tests
├── integration/                # Integration tests
│   └── test_base_worker_integration.py  # BaseWorker integration tests
├── performance/                # Performance tests
│   └── test_base_worker_performance.py  # BaseWorker performance tests
├── run_tests.py               # Test runner script
└── README.md                  # This file
```

## Test Categories

### 1. Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components and methods in isolation
- **Coverage**: BaseWorker methods, ProcessingMetrics, configuration handling
- **Dependencies**: Mocked external services and database
- **Speed**: Fast execution (< 1 second)

**Key Test Areas:**
- Component initialization and cleanup
- Circuit breaker logic
- Content hashing and chunking
- Error handling and retry logic
- Metrics collection

### 2. Integration Tests (`tests/integration/`)
- **Purpose**: Test component interactions and workflows
- **Coverage**: End-to-end job processing, error recovery, concurrent processing
- **Dependencies**: Mocked components with realistic interactions
- **Speed**: Medium execution (1-5 seconds)

**Key Test Areas:**
- Complete job processing workflow
- Error recovery and retry mechanisms
- Circuit breaker integration
- Concurrent job processing
- Idempotent operations
- Health check integration

### 3. Performance Tests (`tests/performance/`)
- **Purpose**: Test system performance under load
- **Coverage**: Throughput, scalability, memory usage
- **Dependencies**: Mocked components optimized for performance testing
- **Speed**: Slow execution (5-30 seconds)

**Key Test Areas:**
- Job processing throughput
- Concurrent worker scaling
- Large document processing
- Memory usage under load
- Error handling performance

## Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Ensure you're in the backend directory
cd backend
```

### Basic Test Execution
```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/performance/

# Run with verbose output
python -m pytest -v

# Run with coverage
python -m pytest --cov=backend --cov-report=html
```

### Using the Test Runner Script
```bash
# Run all tests
python tests/run_tests.py all

# Run specific test types
python tests/run_tests.py unit
python tests/run_tests.py integration
python tests/run_tests.py performance

# Run with verbose output and coverage
python tests/run_tests.py all -v -c
```

### Test Selection
```bash
# Run only fast tests (exclude performance)
python -m pytest -m "not slow"

# Run only unit tests
python -m pytest -m unit

# Run only integration tests
python -m pytest -m integration

# Run specific test file
python -m pytest tests/unit/test_base_worker.py

# Run specific test method
python -m pytest tests/unit/test_base_worker.py::TestBaseWorker::test_initialization
```

## Test Configuration

### Environment Variables
Tests use mock configurations by default. For real integration testing, set:
```bash
export TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/testdb"
export TEST_SUPABASE_URL="http://localhost:5000"
export TEST_OPENAI_API_KEY="your-test-key"
```

### Pytest Configuration
The `conftest.py` file provides:
- Common fixtures for all tests
- Mock component setup
- Test data generation
- Automatic test marking

## Test Data

### Sample Jobs
Tests use realistic job data structures matching the production schema:
```python
{
    "job_id": "uuid",
    "document_id": "uuid", 
    "status": "parsed",
    "parsed_path": "storage://parsed/test.md",
    "chunks_version": "markdown-simple@1",
    "embed_model": "text-embedding-3-small",
    "retry_count": 0
}
```

### Sample Content
Tests use various content types:
- Simple markdown documents
- Large documents (1000+ sections)
- Empty content (error cases)
- Malformed content (validation tests)

## Mocking Strategy

### External Services
- **Database**: Mocked with realistic query responses
- **Storage**: Mocked with file content responses
- **LlamaParse**: Mocked API client
- **OpenAI**: Mocked embedding generation

### Component Interactions
- **Async Operations**: Properly mocked with AsyncMock
- **Context Managers**: Database connections properly mocked
- **Error Conditions**: Various failure scenarios tested

## Performance Benchmarks

### Expected Performance
- **Unit Tests**: < 1 second total
- **Integration Tests**: 1-5 seconds total  
- **Performance Tests**: 5-30 seconds total
- **All Tests**: < 1 minute total

### Throughput Targets
- **Job Processing**: > 5 jobs/second
- **Chunk Processing**: > 30 chunks/second
- **Concurrent Workers**: Linear scaling with worker count

## Continuous Integration

### GitHub Actions
Tests are automatically run on:
- Pull requests
- Main branch pushes
- Release tags

### Test Matrix
- Python versions: 3.8, 3.9, 3.10, 3.11
- Operating systems: Ubuntu, macOS, Windows
- Database: PostgreSQL (mocked for unit tests)

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure you're in the backend directory
2. **Async Test Failures**: Check event loop configuration
3. **Mock Assertion Failures**: Verify mock setup and expectations
4. **Performance Test Timeouts**: Adjust timeout values for slower systems

### Debug Mode
```bash
# Run with debug output
python -m pytest -s -v

# Run single test with debug
python -m pytest tests/unit/test_base_worker.py::TestBaseWorker::test_initialization -s -v
```

### Coverage Reports
```bash
# Generate HTML coverage report
python -m pytest --cov=backend --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

## Contributing

### Adding New Tests
1. Follow the existing test structure
2. Use appropriate test categories
3. Add proper mocking and fixtures
4. Include performance assertions where relevant
5. Update this README if adding new test types

### Test Naming Conventions
- Test classes: `Test<ClassName>`
- Test methods: `test_<functionality>_<scenario>`
- Fixtures: descriptive names with `test_` prefix

### Test Documentation
- Each test should have a clear docstring
- Explain what is being tested and why
- Document any complex setup or mocking
- Include expected performance characteristics

