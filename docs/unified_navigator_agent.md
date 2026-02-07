# Unified Navigator Agent

A single, unified agent that replaces the complex multi-agent supervisor system with guardrails and tool integration. Designed for low latency while maintaining security and functionality.

## Overview

The Unified Navigator Agent consolidates the insurance navigation functionality into a single LangGraph workflow with:

- **Smart Input Guardrails**: Two-stage validation (fast rules + LLM when needed)
- **Tool Selection**: Heuristic-based routing between web search and RAG
- **Output Sanitization**: Template-based cleaning with LLM backup
- **Low Latency Design**: Optimized for <5 second total response time

## Architecture

```
User Input → Input Guardrail → Tool Selection → [Web Search | RAG] → Response Generation → Output Guardrail → Final Response
```

### Components

1. **UnifiedNavigatorAgent**: Main agent class extending `BaseAgent`
2. **Input Sanitizer**: Two-stage safety validation
3. **Web Search Tool**: Brave API integration with caching
4. **RAG Search Tool**: Integration with existing RAG system
5. **Output Sanitizer**: Response filtering and formatting
6. **Configuration**: Environment-based config management

## Quick Start

### Basic Usage

```python
from agents.unified_navigator import UnifiedNavigatorAgent, UnifiedNavigatorInput

# Initialize agent
agent = UnifiedNavigatorAgent(use_mock=False)

# Create input
input_data = UnifiedNavigatorInput(
    user_query="What does my insurance cover?",
    user_id="user_123"
)

# Execute
result = await agent.execute(input_data)
print(result.response)
```

### API Usage

Start the API server:

```bash
python api/unified_navigator_api.py
```

Make requests:

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my insurance deductible?",
    "user_id": "user_123"
  }'
```

### Testing

Run the test script:

```bash
# Automated tests
python test_unified_navigator.py

# Interactive testing
python test_unified_navigator.py interactive
```

## Configuration

The agent uses environment variables for configuration. Key variables:

```bash
# Required
ANTHROPIC_API_KEY=your_key_here
BRAVE_API_KEY=your_key_here

# Optional
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
NAVIGATOR_TIMEOUT=30.0
GUARDRAIL_FAST_CHECK=true
WEB_SEARCH_TIMEOUT=5.0
RAG_SIMILARITY_THRESHOLD=0.25
```

See `agents/unified_navigator/config.py` for full configuration options.

## Performance Characteristics

### Target Performance
- **Total Response Time**: <5 seconds (fast path)
- **Input Sanitization**: <100ms (rule-based) or <500ms (with LLM)
- **Tool Selection**: <50ms (heuristic-based)
- **Tool Execution**: 1-5 seconds
- **Output Sanitization**: <200ms

### Fast Path Optimization
- Most queries (90%+) avoid LLM calls in input sanitization
- Tool selection uses lightweight heuristics
- Connection pooling for HTTP clients
- Response caching for web search

## Tools

### Web Search Tool
- **Provider**: Brave Search API
- **Features**: Query optimization, caching, insurance domain focus
- **Use Cases**: Current information, news, regulations
- **Configuration**: `WEB_SEARCH_*` environment variables

### RAG Search Tool
- **Provider**: Existing RAG system (`agents.tooling.rag.core`)
- **Features**: User-scoped access, vector similarity search
- **Use Cases**: Personal documents, policy information
- **Configuration**: `RAG_*` environment variables

### Tool Selection Logic
```python
# Web search indicators
if "latest" in query or "2025" in query or "news" in query:
    return ToolType.WEB_SEARCH

# RAG search indicators  
elif "my" in query or "policy" in query or "document" in query:
    return ToolType.RAG_SEARCH

# Combined search indicators
elif "compare" in query or len(query.split()) > 15:
    return ToolType.COMBINED

# Default
else:
    return ToolType.RAG_SEARCH
```

## Guardrails

### Input Sanitization

Two-stage process optimized for low latency:

**Stage 1: Fast Rules** (<50ms)
- Insurance domain keyword matching
- Obvious unsafe pattern detection
- Safe pattern recognition

**Stage 2: LLM Validation** (200-500ms, only when needed)
- Nuanced safety assessment
- Query sanitization if needed
- Only for ~5-10% of queries

### Output Sanitization

Template-based cleaning with LLM backup:

**Templates** (<100ms)
- Off-topic response replacement
- Unhelpful response improvement
- Standard insurance redirects

**LLM Backup** (200-500ms, edge cases only)
- Complex content analysis
- Professional tone adjustment
- Domain-specific improvements

## Error Handling

The agent implements comprehensive error handling:

- **Graceful Degradation**: Falls back to mock mode if real mode fails
- **Tool Fallbacks**: RAG search if web search fails
- **Timeout Handling**: Reasonable timeouts with proper cleanup
- **Safety Defaults**: Conservative assumptions on errors

## Migration from Multi-Agent System

### Before (Multi-Agent)
```python
supervisor = SupervisorWorkflow()
info_agent = InformationRetrievalAgent()
strategy_agent = StrategyAgent()

result = await supervisor.execute(input)
if result.routing == "INFORMATION":
    response = await info_agent.execute(input)
elif result.routing == "STRATEGY":  
    response = await strategy_agent.execute(input)
```

### After (Unified Agent)
```python
agent = UnifiedNavigatorAgent()
result = await agent.execute(input)
# All routing, tool selection, and sanitization handled internally
```

### Benefits
- **Simplified API**: Single endpoint vs. multiple agents
- **Better Performance**: Reduced orchestration overhead
- **Easier Maintenance**: Single workflow to debug and optimize
- **Consistent Security**: Unified guardrail system

## Development

### Running Tests
```bash
# Unit tests
pytest agents/unified_navigator/tests/

# Integration tests (requires API keys)
pytest agents/unified_navigator/tests/ -m integration

# Manual testing
python test_unified_navigator.py
```

### Adding New Tools
1. Create tool class in `agents/unified_navigator/tools/`
2. Implement LangGraph node function
3. Add tool type to `models.py`
4. Update tool selection logic in `navigator_agent.py`
5. Add routing logic in workflow

### Extending Guardrails
1. Add patterns to `input_sanitizer.py` or `output_sanitizer.py`
2. Update configuration options in `config.py`
3. Add tests for new patterns
4. Document new safety features

## Monitoring and Observability

### Health Check
```bash
curl http://localhost:8001/health
```

### Metrics
```bash
curl http://localhost:8001/metrics
```

### Logging
- **Level**: INFO by default, DEBUG for detailed tracing
- **Format**: JSON structured logging in production
- **Components**: Each major component logs separately
- **Performance**: Processing times logged for optimization

## Troubleshooting

### Common Issues

**Agent fails to initialize**
- Check `ANTHROPIC_API_KEY` and `BRAVE_API_KEY`
- Verify network connectivity
- Check logs for specific error messages

**Slow response times**
- Check tool timeouts in configuration
- Monitor individual node timing in logs
- Verify external API response times

**Sanitization too aggressive**
- Adjust safety patterns in guardrail configuration
- Review LLM sanitization prompts
- Check confidence thresholds

**Tool selection not working**
- Review tool selection keywords and weights
- Check query preprocessing
- Verify heuristic logic matches use cases

### Debug Mode
```python
# Enable detailed logging
import logging
logging.getLogger("unified_navigator").setLevel(logging.DEBUG)

# Use mock mode for testing
agent = UnifiedNavigatorAgent(use_mock=True)
```

## API Reference

See `api/unified_navigator_api.py` for complete FastAPI implementation with:

- `/chat`: Main chat endpoint
- `/chat/stream`: Streaming responses
- `/health`: Health check
- `/config`: Configuration info
- `/metrics`: Basic metrics

## Contributing

1. Follow existing code patterns and architecture
2. Add tests for new functionality
3. Update documentation for changes
4. Ensure performance targets are maintained
5. Test both mock and real modes