# Regulatory Agent Troubleshooting Guide

## 🚨 Common Issues & Solutions

### **Issue 1: Import Errors with Dependencies**

**Symptoms:**
```
ImportError: cannot import name 'Secret' from 'pydantic'
ModuleNotFoundError: No module named 'langchain'
```

**Root Cause:** Complex dependency conflicts between LangChain/LlamaIndex and your environment.

**Solution:** Use the import bypass pattern:
```python
import sys
import os
core_path = os.path.join(os.path.dirname(__file__), 'agents/regulatory/core')
sys.path.insert(0, core_path)

# Now import directly from core
from mock_tools import create_mock_agent
from regulatory_isolated import create_isolated_regulatory_agent
```

### **Issue 2: Agent Initialization Failures**

**Symptoms:**
```
TypeError: __init__() missing required positional argument
AttributeError: module has no attribute 'create_regulatory_agent'
```

**Root Cause:** Using outdated agent creation patterns.

**Solution:** Use the correct agent factory functions:
```python
# For testing/development
mock_agent = create_mock_agent()

# For production
isolated_agent = create_isolated_regulatory_agent()
```

### **Issue 3: Database Connection Errors**

**Symptoms:**
```
asyncpg.exceptions.ConnectionDoesNotExistError
psycopg2.OperationalError: could not connect to server
```

**Root Cause:** Missing database configuration or PostgreSQL not running.

**Solutions:**

**Option A: Mock Agent (No Database Required)**
```python
# Use mock agent - works without any database
agent = create_mock_agent()
result = agent.analyze_strategy("Your strategy")
```

**Option B: Configure Database**
```bash
# Set environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_NAME=insurance_navigator

# Start PostgreSQL
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux
```

### **Issue 4: Internet Search Rate Limiting**

**Symptoms:**
```
duckduckgo_search.exceptions.RatelimitException
aiohttp.ClientResponseError: 429, Too Many Requests
```

**Root Cause:** DuckDuckGo API rate limits.

**Solutions:**

**Option A: Use Mock Agent for Development**
```python
# Switch to mock agent during heavy testing
agent = create_mock_agent()
```

**Option B: Add Rate Limiting Delays**
```python
import asyncio

async def search_with_delays():
    agent = create_isolated_regulatory_agent()
    
    # Add delays between searches
    await asyncio.sleep(2)
    result = await agent.analyze_strategy("Strategy 1")
    
    await asyncio.sleep(2)
    result = await agent.analyze_strategy("Strategy 2")
```

### **Issue 5: Supabase Storage Errors**

**Symptoms:**
```
supabase.exceptions.AuthError
HTTPError: 401 Unauthorized
```

**Root Cause:** Missing or invalid Supabase credentials.

**Solutions:**

**Option A: Skip Supabase (Agent Still Works)**
```python
# Agent works without Supabase - just won't store documents
# Set empty environment variables
export SUPABASE_URL=""
export SUPABASE_ANON_KEY=""
```

**Option B: Configure Supabase**
```bash
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_ANON_KEY=your_anon_key
```

### **Issue 6: Claude AI Integration Errors**

**Symptoms:**
```
anthropic.exceptions.AuthenticationError
anthropic.exceptions.RateLimitError
```

**Root Cause:** Missing or invalid Anthropic API key.

**Solution:**
```bash
# Optional - agent works without Claude AI
export ANTHROPIC_API_KEY=your_claude_key

# Or leave empty for basic functionality
export ANTHROPIC_API_KEY=""
```

## 🔧 **Debugging Tools**

### **1. Environment Checker**
```python
def check_environment():
    import os
    
    print("🔍 Environment Check:")
    print(f"DB_HOST: {'✅' if os.getenv('DB_HOST') else '❌'}")
    print(f"SUPABASE_URL: {'✅' if os.getenv('SUPABASE_URL') else '❌'}")
    print(f"ANTHROPIC_API_KEY: {'✅' if os.getenv('ANTHROPIC_API_KEY') else '❌'}")
    
    # Test basic imports
    try:
        import sys
        sys.path.insert(0, 'agents/regulatory/core')
        from mock_tools import create_mock_agent
        print("✅ Mock agent import successful")
    except ImportError as e:
        print(f"❌ Mock agent import failed: {e}")
    
    try:
        from regulatory_isolated import create_isolated_regulatory_agent
        print("✅ Isolated agent import successful")
    except ImportError as e:
        print(f"❌ Isolated agent import failed: {e}")
```

### **2. Agent Testing Script**
```python
async def test_agents():
    import sys
    sys.path.insert(0, 'agents/regulatory/core')
    
    # Test mock agent
    print("🧪 Testing Mock Agent...")
    try:
        from mock_tools import create_mock_agent
        mock_agent = create_mock_agent()
        result = mock_agent.analyze_strategy("Test Medicare strategy")
        print(f"✅ Mock agent works: {len(result)} chars")
    except Exception as e:
        print(f"❌ Mock agent failed: {e}")
    
    # Test isolated agent
    print("🧪 Testing Isolated Agent...")
    try:
        from regulatory_isolated import create_isolated_regulatory_agent
        isolated_agent = create_isolated_regulatory_agent()
        result = await isolated_agent.analyze_strategy("Test Medicare strategy")
        print(f"✅ Isolated agent works: {len(result)} chars")
    except Exception as e:
        print(f"❌ Isolated agent failed: {e}")
```

## 🎯 **Best Practices**

### **1. Development Workflow**
```python
# Start with mock agent for fast iteration
mock_agent = create_mock_agent()

# Test your logic with instant responses
for strategy in test_strategies:
    result = mock_agent.analyze_strategy(strategy)
    # Validate result format, content structure, etc.

# Switch to isolated agent for final testing
isolated_agent = create_isolated_regulatory_agent()
```

### **2. Production Deployment**
```python
def create_regulatory_agent(use_mock=False):
    """Factory function with fallback logic."""
    if use_mock or not production_environment():
        return create_mock_agent()
    
    try:
        return create_isolated_regulatory_agent()
    except Exception as e:
        logger.warning(f"Isolated agent failed, falling back to mock: {e}")
        return create_mock_agent()
```

### **3. Error Handling Pattern**
```python
async def robust_analysis(strategy: str):
    """Robust analysis with automatic fallback."""
    try:
        # Try isolated agent first
        agent = create_isolated_regulatory_agent()
        return await agent.analyze_strategy(strategy)
    
    except Exception as e:
        logger.warning(f"Isolated agent failed: {e}, using mock")
        # Fallback to mock agent
        mock_agent = create_mock_agent()
        return mock_agent.analyze_strategy(strategy)
```

## 🆘 **Emergency Procedures**

### **Complete Failure Recovery**
If everything breaks, use this minimal working setup:

```python
# Emergency standalone script
import sys
import os

# 1. Add core to path
core_path = os.path.join(os.path.dirname(__file__), 'agents/regulatory/core')
sys.path.insert(0, core_path)

# 2. Use mock agent only
from mock_tools import create_mock_agent

# 3. Basic functionality
agent = create_mock_agent()
result = agent.analyze_strategy("Your strategy here")
print(result)
```

This should work in ANY environment with zero dependencies.

## 📞 **Getting Help**

1. **Check Environment**: Run the environment checker script
2. **Test Mock Agent**: Verify basic functionality with mock agent
3. **Incremental Testing**: Add isolated agent features one by one
4. **Review Logs**: Check application logs for specific error details
5. **Fallback Mode**: Use mock agent in production if needed

## 📚 **Additional Resources**

- **Integration Examples**: See `agents/regulatory/integration_example.py`
- **Demo Script**: Run `agents/regulatory/demo_regulatory_agent.py`
- **Unit Tests**: Check `agents/regulatory/tests/` for working examples
- **README**: Full setup guide in `agents/regulatory/README.md` 