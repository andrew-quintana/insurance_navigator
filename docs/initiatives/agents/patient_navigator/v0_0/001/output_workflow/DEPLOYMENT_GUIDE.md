# Output Communication Agent - Production Deployment Guide

## 🚀 Overview

This guide provides step-by-step instructions for deploying the Output Communication Agent to production. The system is **production-ready** with comprehensive testing, error handling, and monitoring.

## 📋 Prerequisites

### Environment Requirements
- **Python**: 3.9+ (tested with Python 3.9.12)
- **Dependencies**: All requirements installed via pip/conda
- **Environment Variables**: Proper configuration for production

### Required Services
- **Claude Haiku API**: Anthropic API credentials
- **Environment Configuration**: Production environment variables
- **Monitoring**: Logging and health check endpoints

## 🔧 Configuration Setup

### 1. Environment Variables

Create a `.env.production` file with the following variables:

```bash
# Claude Haiku Configuration
ANTHROPIC_API_KEY=your_production_api_key_here
ANTHROPIC_MODEL=claude-3-haiku-20240307

# Output Processing Configuration
OUTPUT_PROCESSING_LLM_MODEL=claude-3-haiku
OUTPUT_PROCESSING_TIMEOUT=30.0
OUTPUT_PROCESSING_MAX_INPUT_LENGTH=10000
OUTPUT_PROCESSING_MAX_CONCURRENT=10
OUTPUT_PROCESSING_DEFAULT_TONE=warm_empathetic
OUTPUT_PROCESSING_ENABLE_TONE_ADAPTATION=true
OUTPUT_PROCESSING_MIN_EMPATHY_SCORE=0.7
OUTPUT_PROCESSING_MAX_AGENT_OUTPUTS=10
OUTPUT_PROCESSING_ENABLE_CONSOLIDATION=true
OUTPUT_PROCESSING_ENABLE_PLAIN_LANGUAGE=true
OUTPUT_PROCESSING_MIN_QUALITY=0.8
OUTPUT_PROCESSING_MAX_TIME=5.0
OUTPUT_PROCESSING_ENABLE_FALLBACK=true
OUTPUT_PROCESSING_FALLBACK_TO_ORIGINAL=true
OUTPUT_PROCESSING_MAX_RETRIES=2
```

### 2. Configuration Validation

The system automatically validates configuration on startup. Ensure all values are within acceptable ranges:

```python
from agents.patient_navigator.output_processing.config import OutputProcessingConfig

# This will raise ValueError if configuration is invalid
config = OutputProcessingConfig.from_environment()
config.validate()
```

## 🚀 Deployment Steps

### Step 1: Code Deployment

```bash
# 1. Pull the latest code
git pull origin main

# 2. Install/update dependencies
pip install -r requirements.txt

# 3. Verify the module structure
ls -la agents/patient_navigator/output_processing/
```

### Step 2: Environment Setup

```bash
# 1. Set production environment
export ENVIRONMENT=production

# 2. Load production environment variables
source .env.production

# 3. Verify Claude Haiku API key
python -c "import os; print('API Key:', 'SET' if os.getenv('ANTHROPIC_API_KEY') else 'NOT SET')"
```

### Step 3: Health Check Verification

```bash
# 1. Run health checks
python -c "
from agents.patient_navigator.output_processing.workflow import OutputWorkflow
workflow = OutputWorkflow()
health = workflow.health_check()
print('Health Status:', health)
"

# Expected output:
# Health Status: {'workflow': 'healthy', 'agent': 'healthy', 'config': 'valid', 'timestamp': ...}
```

### Step 4: Integration Testing

```bash
# 1. Run the comprehensive test suite
python -m pytest tests/agents/patient_navigator/output_processing/ -v

# Expected output: 54 tests passing
# If any tests fail, investigate before proceeding to production
```

## 🔍 Production Validation

### 1. Health Check Endpoints

The system provides built-in health monitoring:

```python
from agents.patient_navigator.output_processing.workflow import OutputWorkflow

workflow = OutputWorkflow()

# Basic health check
health = workflow.health_check()
print(f"Workflow Status: {health['workflow']}")
print(f"Agent Status: {health['agent']}")
print(f"Config Status: {health['config']}")

# Workflow information
info = workflow.get_workflow_info()
print(f"Workflow Type: {info['workflow_type']}")
print(f"Version: {info['workflow_version']}")
```

### 2. Performance Validation

```python
import asyncio
import time
from agents.patient_navigator.output_processing.workflow import OutputWorkflow
from agents.patient_navigator.output_processing.types import CommunicationRequest, AgentOutput

async def validate_performance():
    workflow = OutputWorkflow()
    
    # Test with sample data
    test_outputs = [
        AgentOutput(
            agent_id="test_agent",
            content="Your plan covers 80% of in-network costs after $500 deductible.",
            metadata={"test": True}
        )
    ]
    
    request = CommunicationRequest(agent_outputs=test_outputs)
    
    # Measure response time
    start_time = time.time()
    response = await workflow.process_request(request)
    end_time = time.time()
    
    response_time = end_time - start_time
    print(f"Response Time: {response_time:.3f}s")
    print(f"Performance OK: {response_time < 0.5}")  # Should be <500ms
    
    return response

# Run validation
response = asyncio.run(validate_performance())
```

### 3. Error Handling Validation

```python
async def validate_error_handling():
    workflow = OutputWorkflow()
    
    # Test with invalid request (no outputs)
    invalid_request = CommunicationRequest(agent_outputs=[])
    
    try:
        response = await workflow.process_request(invalid_request)
        print("✅ Error handling working: Got fallback response")
        print(f"Fallback used: {response.metadata.get('fallback_used', False)}")
    except Exception as e:
        print(f"❌ Error handling failed: {e}")

# Run validation
asyncio.run(validate_error_handling())
```

## 📊 Monitoring & Observability

### 1. Logging Configuration

The system provides comprehensive logging:

```python
import logging

# Configure logging level for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

# The system will log:
# - Agent initialization and configuration
# - Request processing and timing
# - Error conditions and fallback usage
# - Performance metrics
```

### 2. Key Metrics to Monitor

```python
# Response time monitoring
response_time = response.processing_time
if response_time > 0.5:  # >500ms threshold
    logging.warning(f"Slow response time: {response_time:.3f}s")

# Fallback usage monitoring
if response.metadata.get('fallback_used'):
    logging.warning("Fallback response used - investigate LLM issues")

# Error rate monitoring
if response.metadata.get('error_message'):
    logging.error(f"Error in response: {response.metadata['error_message']}")
```

### 3. Health Check Integration

```python
# Regular health checks (recommended: every 30 seconds)
import time
import threading

def health_monitor():
    while True:
        try:
            workflow = OutputWorkflow()
            health = workflow.health_check()
            
            if health['workflow'] != 'healthy':
                logging.error(f"Health check failed: {health}")
                # Send alert to monitoring system
            
            time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logging.error(f"Health monitor error: {e}")
            time.sleep(30)

# Start health monitoring in background
health_thread = threading.Thread(target=health_monitor, daemon=True)
health_thread.start()
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Claude Haiku API Errors

**Symptoms**: Responses using fallback mode, error messages about API calls

**Solutions**:
```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Verify API quota
# Check Anthropic dashboard for usage limits

# Test API connectivity
python -c "
from anthropic import Anthropic
client = Anthropic(api_key='$ANTHROPIC_API_KEY')
print('API connection test:', 'OK' if client else 'FAILED')
"
```

#### 2. Configuration Validation Errors

**Symptoms**: Startup failures, configuration validation errors

**Solutions**:
```python
# Validate configuration manually
from agents.patient_navigator.output_processing.config import OutputProcessingConfig

try:
    config = OutputProcessingConfig.from_environment()
    config.validate()
    print("✅ Configuration valid")
except Exception as e:
    print(f"❌ Configuration error: {e}")
    # Check environment variables and fix invalid values
```

#### 3. Performance Issues

**Symptoms**: Response times >500ms, high memory usage

**Solutions**:
```python
# Check configuration limits
config = OutputProcessingConfig.from_environment()
print(f"Max input length: {config.max_input_length}")
print(f"Max agent outputs: {config.max_agent_outputs}")
print(f"Request timeout: {config.request_timeout}")

# Adjust if needed
# Reduce max_input_length for better performance
# Increase request_timeout if needed
```

### Emergency Procedures

#### 1. Disable LLM Integration

If Claude Haiku is causing issues, temporarily disable:

```bash
# Remove API key to force mock mode
unset ANTHROPIC_API_KEY

# Restart the service
# System will automatically fall back to mock mode
```

#### 2. Rollback to Previous Version

```bash
# Revert to previous working version
git log --oneline -5  # Find previous version
git checkout <previous_commit_hash>

# Restart service
# Verify functionality
```

## 🔒 Security Considerations

### 1. API Key Management

- **Never commit API keys** to version control
- **Use environment variables** for sensitive configuration
- **Rotate API keys** regularly
- **Monitor API usage** for unusual patterns

### 2. Input Validation

- **All inputs validated** before processing
- **Content length limits** enforced
- **Agent output limits** enforced
- **Error messages** don't expose sensitive information

### 3. Logging Security

- **No sensitive data** logged in production
- **Log levels appropriate** for production environment
- **Log rotation** configured to prevent disk space issues

## 📈 Performance Optimization

### 1. Configuration Tuning

```python
# For high-throughput scenarios
config = OutputProcessingConfig(
    max_concurrent_requests=50,  # Increase from default 10
    max_processing_time=10.0,    # Increase from default 5.0
    request_timeout=60.0         # Increase from default 30.0
)
```

### 2. Caching Strategy

```python
# Implement response caching for identical inputs
import hashlib
import json

def cache_key(request: CommunicationRequest) -> str:
    """Generate cache key for request."""
    content = json.dumps(request.dict(), sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()

# Cache responses for identical requests
# Implement based on your caching infrastructure
```

## 🎯 Success Criteria

### Deployment Validation Checklist

- [ ] **Health Checks**: All components report healthy status
- [ ] **Performance**: Response times <500ms for typical requests
- [ ] **Error Handling**: Fallback mechanisms working correctly
- [ ] **Integration**: Seamless integration with existing workflows
- [ ] **Monitoring**: Logging and metrics collection working
- [ ] **Configuration**: All environment variables properly set
- [ ] **Testing**: All 54 tests passing in production environment

### Go-Live Criteria

- [ ] **100% test pass rate** in production environment
- [ ] **Health checks passing** for 5+ consecutive checks
- [ ] **Performance metrics** within acceptable ranges
- [ ] **Error rates** below 1% threshold
- [ ] **Monitoring systems** fully operational
- [ ] **Team trained** on monitoring and troubleshooting

## 📞 Support & Escalation

### Contact Information

- **Development Team**: For code-related issues
- **DevOps Team**: For infrastructure and deployment issues
- **Anthropic Support**: For Claude Haiku API issues

### Escalation Path

1. **Level 1**: Check logs and health status
2. **Level 2**: Restart service and verify configuration
3. **Level 3**: Rollback to previous version
4. **Level 4**: Engage development team for investigation

---

**Document Version**: 1.0  
**Last Updated**: 2025-08-13  
**Production Status**: ✅ READY FOR DEPLOYMENT  
**Next Review**: After 30 days of production operation
