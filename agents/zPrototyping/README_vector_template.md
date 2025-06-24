# 🚀 Agent Vector Integration Template

## Overview

The `agent_vector_integration_template.ipynb` is a complete, working Jupyter notebook template for prototyping vector-integrated agents. It provides a foundation for building agents that can retrieve and process document content from Supabase with proper encryption handling.

## ✅ What's Fixed

This template addresses all the issues from previous versions:

- **✅ Correct Imports**: Uses proper import paths (`db.services.encryption_service.EncryptionServiceFactory`, `db.services.db_pool.get_db_pool`, etc.)
- **✅ Working Services**: All service initialization uses correct constructors and methods
- **✅ Proper Error Handling**: Debug logging for expected decryption failures in development
- **✅ Real Database Integration**: Connects to Supabase by default for production data testing
- **✅ Complete Agent Class**: Full `VectorAgent` implementation with all necessary methods
- **✅ Testing Framework**: Built-in testing with multiple domains and queries

## 🎯 Quick Start

1. **Open the notebook**: `agent_vector_integration_template.ipynb`
2. **Run cells sequentially**: Each cell builds on the previous one
3. **Customize configuration**: Modify the `AGENT_CONFIG` in cell 2
4. **Test your agent**: Run the test cells to see it in action
5. **Iterate and improve**: Adjust parameters and re-run

## 🔧 Key Configuration Options

```python
AGENT_CONFIG = AgentConfig(
    name="MyPrototypeAgent",        # Your agent's name
    domain="healthcare",            # healthcare | finance | legal | general  
    max_context_chunks=15,          # Number of chunks to retrieve
    confidence_threshold=0.6,       # When to use fallback responses
    enable_encryption=True,         # Enable content decryption
    fallback_enabled=True,          # Enable fallback responses
    debug_mode=True,                # Enable detailed logging
    use_supabase=True              # Use Supabase vs local database
)
```

## 🏥 Domain Templates

The template includes pre-built prompt templates for:

- **Healthcare**: Insurance navigation and medical benefits
- **Finance**: Financial guidance and account analysis  
- **Legal**: Document analysis and legal research
- **General**: Generic document analysis

## 🧪 Testing

The notebook includes domain-specific test queries:

- **Healthcare**: "What does my insurance cover for specialist visits?"
- **Finance**: "What are my investment account balances?"
- **Legal**: "What are the key terms of my contract?"
- **General**: "What are the main topics covered in my documents?"

## 🤖 Adding LLM Integration

Replace the TODO section in `generate_response()` with your preferred AI model:

```python
# OpenAI Example
import openai
response = await openai.ChatCompletion.acreate(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}]
)
return response.choices[0].message.content

# Anthropic Example  
import anthropic
response = await anthropic.messages.create(
    model="claude-3-sonnet-20240229", 
    messages=[{"role": "user", "content": prompt}]
)
return response.content[0].text
```

## 📊 Expected Results

When you run the tests, you should see:

- **Vector Retrieval**: ~15-20 chunks retrieved from Supabase
- **Decryption Handling**: Debug messages for expected dev environment failures
- **Fallback Responses**: Professional responses when content unavailable  
- **Performance Metrics**: Confidence scores and context chunk counts

## 🔍 Troubleshooting

- **Import Errors**: Make sure you're in the correct directory (`agents/zPrototyping`)
- **Service Failures**: Check database connectivity and service configurations
- **No Results**: Verify the test user ID exists in your database
- **Decryption Issues**: Expected in development - uses mock encryption service

## 🚀 Deployment Path

Once your prototype works:

1. **Copy Configuration**: Move your settings to `agent_vector_template.py`
2. **Add LLM Integration**: Implement your AI model calls
3. **Production Setup**: Configure real encryption and database settings
4. **Monitoring**: Add logging and performance tracking
5. **Deploy**: Integrate into your application

## 💡 Tips for Success

- **Start Simple**: Begin with basic queries in your domain
- **Iterate Configuration**: Adjust thresholds and test with different settings
- **Test Edge Cases**: Try queries with no matches or complex requests
- **Monitor Performance**: Watch context chunk retrieval and confidence scores
- **Use Real Data**: Test with actual user IDs and production documents

---

**Happy prototyping! 🎉** 