# Agent Vector Integration Template

A comprehensive, reusable template for building agents with vector integration capabilities.

## 🚀 Quick Start

```bash
cd agents/zPrototyping
python agent_vector_template.py
```

## 📋 Features

- ✅ **Supabase Integration**: Direct vector retrieval from production database
- ✅ **Encryption Support**: Secure content decryption with proper error handling
- ✅ **Domain Templates**: Pre-built prompts for healthcare, finance, legal, and general use
- ✅ **Professional Logging**: Debug-friendly with appropriate log levels
- ✅ **Performance Monitoring**: Context chunk tracking and confidence scoring
- ✅ **Fallback Strategies**: Graceful handling when content unavailable
- ✅ **Configurable**: Easy customization for different agent types

## 🛠️ Customization Guide

### 1. Agent Configuration

```python
config = AgentConfig(
    name="YourAgentName",           # Custom agent name
    domain="healthcare",            # "healthcare", "finance", "legal", "general"
    max_context_chunks=20,          # Number of vector chunks to retrieve
    confidence_threshold=0.5,       # Minimum confidence for high-quality response
    enable_encryption=True,         # Enable content decryption
    fallback_enabled=True,          # Enable fallback responses
    debug_mode=True                 # Enable detailed logging
)
```

### 2. Domain-Specific Prompts

Modify the `get_agent_prompt_template()` function to add your domain:

```python
"your_domain": """
You are a [description] assistant.

Context from user documents:
{context}

User Query: {query}

Instructions:
1. [Your specific instruction 1]
2. [Your specific instruction 2]
...

Response:"""
```

### 3. Response Generation

Customize the `generate_response()` method in `VectorAgent` class:

```python
async def generate_response(self, query: str, context: List[str], confidence: float) -> str:
    # Add your LLM integration here
    # Example: OpenAI, Anthropic, local models, etc.
    pass
```

### 4. Test Queries

Update the test queries for your specific use case:

```python
test_queries = [
    "Your domain-specific question 1?",
    "Your domain-specific question 2?",
    "Your domain-specific question 3?"
]
```

## 🏗️ Architecture

```
VectorAgent
├── retrieve_context()     # Vector retrieval + decryption
├── generate_response()    # LLM integration point
├── process_query()        # Main orchestration
└── _get_fallback_response() # Domain-specific fallbacks
```

## 📊 Response Structure

```python
{
    'response': str,           # Generated response text
    'confidence': float,       # Confidence score (0.0-1.0)
    'citations': List[str],    # Document chunk references
    'context_chunks': int,     # Number of chunks used
    'has_documents': bool,     # Whether documents were found
    'agent_name': str,         # Agent identifier
    'domain': str             # Domain type
}
```

## 🔒 Security Features

- **Encryption**: Content automatically decrypted using proper key management
- **Error Handling**: Graceful failures with debug logging (not warnings)
- **Validation**: Database connection and service validation
- **Fallbacks**: Safe responses when decryption fails

## 🎯 Use Cases

### Healthcare Agent
```python
config = AgentConfig(name="HealthNavigator", domain="healthcare")
# Handles insurance, medical benefits, provider networks
```

### Finance Agent
```python
config = AgentConfig(name="FinanceAdvisor", domain="finance")
# Handles investment documents, financial planning, budgets
```

### Legal Agent
```python
config = AgentConfig(name="LegalAnalyzer", domain="legal")
# Handles contracts, legal documents, compliance
```

### Custom Agent
```python
config = AgentConfig(name="CustomAgent", domain="general")
# Add your own domain logic
```

## 🧪 Testing

The template includes comprehensive testing:

1. **Vector Retrieval**: Tests database connectivity and vector fetching
2. **Decryption**: Tests content decryption with error handling
3. **Response Generation**: Tests end-to-end query processing
4. **Confidence Scoring**: Tests confidence calculation logic

## 📈 Performance

- **Vector Retrieval**: ~1-2 seconds for 20 chunks
- **Database Integration**: All Supabase tables accessible
- **Memory Efficient**: Streaming content processing
- **Scalable**: Configurable chunk limits and thresholds

## 🔧 Integration Examples

### With OpenAI
```python
async def generate_response(self, query: str, context: List[str], confidence: float) -> str:
    client = openai.AsyncOpenAI()
    prompt = self.prompt_template.format(context="\\n".join(context), query=query)
    
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content
```

### With Anthropic
```python
async def generate_response(self, query: str, context: List[str], confidence: float) -> str:
    client = anthropic.AsyncAnthropic()
    prompt = self.prompt_template.format(context="\\n".join(context), query=query)
    
    response = await client.messages.create(
        model="claude-3-sonnet-20240229",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text
```

## 🚨 Troubleshooting

### Decryption Failures
- **Expected Behavior**: Dev environment can't decrypt production data
- **Solution**: Use debug mode to see detailed logs, not warnings

### No Vector Results
- **Check**: User ID exists in database
- **Check**: Documents are properly vectorized
- **Check**: Database connection is working

### Low Confidence Scores
- **Increase**: `max_context_chunks` for more context
- **Decrease**: `confidence_threshold` for less strict filtering
- **Enable**: `fallback_enabled` for graceful degradation

## 📝 Next Steps

1. **Customize Configuration**: Set your agent name, domain, and parameters
2. **Add LLM Integration**: Implement your preferred language model
3. **Test Thoroughly**: Run with your specific queries and user data
4. **Deploy**: Integrate into your application workflow
5. **Monitor**: Track performance and confidence scores

## 🤝 Contributing

This template is designed to be extended. Common extensions:
- Additional domain templates
- Advanced retrieval strategies
- Custom confidence calculations
- Integration with specific LLM providers
- Enhanced error handling patterns 