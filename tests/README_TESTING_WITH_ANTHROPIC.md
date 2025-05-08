# Testing Agents with Anthropic Integration

This guide explains how to test agents that use Anthropic's Claude models within the Medicare Navigator project.

## Testing Approaches

There are two main approaches to testing agents that use LLMs:

1. **Mock-based testing**: Fast, free, but less realistic
2. **Real API testing**: Realistic, but costs API credits and is slower

## Setup for Testing

### 1. Environment Setup

Create a `.env.test` file in the project root with the following content:

```env
# Test environment configuration
ANTHROPIC_API_KEY=your_test_api_key

# Optional: Use lower-tier model for testing to reduce costs
ANTHROPIC_MODEL=claude-3-haiku-20240307

# Testing flags
USE_MOCK_LLM=true  # Set to false to use real Anthropic API
TEST_MODE=true
```

### 2. Mock-Based Testing (Default)

The default approach is to use mocks, which don't require an API key:

```python
from unittest.mock import MagicMock

# Initialize agent with a mock LLM
mock_llm = MagicMock()
mock_llm.invoke.return_value = your_expected_response
agent = YourAgent(llm=mock_llm)

# Test the agent
result = agent.process(input_data)
```

See `test_agent_with_anthropic.py` for a more complete example of mock-based testing.

### 3. Real API Testing

For integration testing with the real Anthropic API:

1. Set `USE_MOCK_LLM=false` in your `.env.test` file
2. Ensure you have a valid Anthropic API key

Run the test with real API:

```bash
# Run specific test with real API
python -m tests.test_agent_with_anthropic --real-api

# Or set environment variable directly
USE_MOCK_LLM=false python -m tests.test_agent_with_anthropic
```

## Example Tests

See `test_agent_with_anthropic.py` for complete examples of:
- Basic mock testing
- Mock testing with specific responses
- Real API testing with safeguards

## Best Practices

1. **Default to mocks**: Use mocks for most tests to avoid API costs
2. **Test edge cases**: Test failure modes, timeouts, and error handling
3. **Validate output structure**: Ensure the output has the expected structure
4. **Use smaller models**: When using real API, use smaller/cheaper models
5. **Limit API tests**: Run real API tests only when necessary (e.g., CI pipeline)
6. **Use deterministic settings**: Set temperature=0 for reproducible results

## Debugging Tips

If your tests are failing, check:

1. API key validity and permissions
2. Network connectivity
3. Rate limits or quotas
4. Model availability
5. Response parsing logic

## Cost Management

To manage costs when testing with real API:
- Use smaller models (haiku instead of sonnet/opus)
- Reduce test frequency
- Use shorter prompts
- Cache responses where appropriate
- Set up API usage alerts 