# CORS Management and Security Guide

## Overview

This document outlines the comprehensive CORS (Cross-Origin Resource Sharing) management system implemented for the Insurance Navigator API to prevent and quickly resolve CORS issues like the one experienced with the `k2ui23iaj` Vercel deployment.

## Problem Analysis

### Root Cause of the Original Issue

The CORS error with `https://insurance-navigator-k2ui23iaj-andrew-quintanas-projects.vercel.app` was caused by:

1. **502 Bad Gateway Error**: Server overwhelmed during large PDF processing (232 pages)
2. **Missing CORS Headers**: When a 502 error occurs, CORS headers may not be sent
3. **Browser Security Policy**: Browser blocks requests when CORS headers are missing

**Key Insight**: The CORS configuration was actually correct, but server errors prevented proper header delivery.

## Solution Architecture

### 1. Multi-Layer CORS Protection

```python
# Layer 1: Custom CORS Middleware (Primary)
class CustomCORSMiddleware(BaseHTTPMiddleware):
    - Comprehensive pattern matching
    - Error-resilient header injection
    - Security validation
    - Performance monitoring

# Layer 2: FastAPI CORS Middleware (Backup)
app.add_middleware(CORSMiddleware, ...)
    - Explicit origin lists
    - Regex patterns
    - Wildcard support
```

### 2. Pattern-Based Origin Validation

```regex
# Vercel Preview Deployments
^insurance-navigator-[a-z0-9]+-andrew-quintanas-projects\.vercel\.app$

# Security Protection (Blocked)
^insurance-navigator-[a-z0-9]+-(?!andrew-quintanas-projects).*\.vercel\.app$
```

### 3. Enhanced Upload Resilience

- **File Size Limits**: 50MB maximum to prevent memory issues
- **Processing Timeouts**: 60s text extraction, 30s chunking, 10s embeddings
- **Batch Processing**: 10 chunks per batch to prevent overwhelming
- **Resource Cleanup**: Automatic cleanup on errors
- **Progress Tracking**: Detailed logging with milestones

## Implementation Details

### CORS Middleware Features

1. **Comprehensive Pattern Matching**
   - Localhost development support
   - Production domain validation
   - Vercel preview deployment patterns
   - Security threat detection

2. **Error-Resilient Headers**
   - Always inject CORS headers, even on errors
   - Fallback mechanisms for failed validation
   - Custom error responses with proper headers

3. **Performance Monitoring**
   - Request timing headers
   - Resource usage tracking
   - Automatic alerting on slow responses

4. **Security Validation**
   - Pattern-based threat detection
   - User validation for Vercel deployments
   - Risk level assessment

### Upload Endpoint Improvements

1. **Resource Management**
   ```python
   # File size validation
   MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
   
   # Text content limits
   MAX_TEXT_LENGTH = 1_000_000  # 1MB of text
   
   # Chunk limits
   MAX_CHUNKS = 500
   ```

2. **Timeout Protection**
   ```python
   # Text extraction timeout
   await asyncio.wait_for(extraction_task, timeout=60.0)
   
   # Database operation timeout
   await asyncio.wait_for(db_insert, timeout=5.0)
   ```

3. **Batch Processing**
   ```python
   BATCH_SIZE = 10
   for batch in chunks_batches:
       process_batch(batch)
       await asyncio.sleep(0.1)  # Prevent overwhelming
   ```

## Monitoring and Prevention

### 1. Automated CORS Testing

```bash
# Run comprehensive CORS test suite
python test_cors.py

# Continuous monitoring
python scripts/monitoring/cors_monitor.py --continuous
```

**Test Coverage:**
- 20+ URL patterns including future deployments
- Security threat detection
- Performance monitoring
- Pattern validation

### 2. Monitoring System

The `CORSMonitor` class provides:

- **Real-time Testing**: Continuous CORS endpoint validation
- **Security Alerts**: Unauthorized deployment detection
- **Performance Monitoring**: Response time tracking
- **Automated Reports**: Historical analysis and trends

### 3. Alert System

**Alert Categories:**
- 🚨 `SECURITY_BREACH`: Unauthorized user deployments
- ❌ `CORS_FAILURE`: CORS configuration issues
- ⚠️ `PERFORMANCE`: Slow response times
- 📊 `PATTERN_MISMATCH`: Unknown deployment patterns

## Prevention Strategies

### 1. Proactive Monitoring

```bash
# Set up cron job for regular monitoring
0 */6 * * * cd /path/to/project && python scripts/monitoring/cors_monitor.py
```

### 2. Deployment Integration

```yaml
# GitHub Actions example
- name: Test CORS Configuration
  run: python test_cors.py
  
- name: Validate New Deployment
  run: python scripts/monitoring/cors_monitor.py
```

### 3. Pattern Management

**Update patterns when:**
- New deployment infrastructure is added
- Security requirements change
- New team members join
- Domain structure changes

### 4. Resource Limits

**Prevent 502 errors by:**
- Limiting file upload sizes
- Implementing request timeouts
- Using batch processing
- Monitoring server resources

## Security Considerations

### 1. Origin Validation

```python
# Explicit validation hierarchy
1. Localhost (development)
2. Production domains (whitelist)
3. Authorized Vercel previews (pattern match)
4. Generic Vercel (with review flag)
5. Reject all others
```

### 2. Threat Detection

**Blocked patterns:**
- Different user Vercel deployments
- Suspicious domain patterns
- Unauthorized applications

### 3. Security Headers

```http
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 86400
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, HEAD
Access-Control-Allow-Headers: *
```

## Troubleshooting Guide

### Common Issues and Solutions

1. **New Vercel Deployment Fails CORS**
   ```bash
   # Test the specific URL
   python test_cors.py
   
   # Check pattern matching
   python -c "
   import re
   pattern = re.compile(r'^insurance-navigator-[a-z0-9]+-andrew-quintanas-projects\.vercel\.app$')
   print(pattern.match('your-new-url-domain'))
   "
   ```

2. **502 Errors During Upload**
   ```bash
   # Check file size and server resources
   # Reduce upload size or implement streaming
   # Monitor server logs for resource exhaustion
   ```

3. **Pattern Mismatch**
   ```python
   # Update patterns in main.py CustomCORSMiddleware
   # Add new patterns to monitoring system
   # Test with updated configuration
   ```

### Diagnostic Commands

```bash
# Test specific URL
curl -i -X OPTIONS https://api.domain.com/upload-policy \
  -H "Origin: https://your-frontend.vercel.app" \
  -H "Access-Control-Request-Method: POST"

# Check pattern validation
python -c "
from test_cors import test_cors_pattern_validation
test_cors_pattern_validation()
"

# Run monitoring cycle
python scripts/monitoring/cors_monitor.py
```

## Best Practices

### 1. Regular Testing

- Run CORS tests before major deployments
- Test new Vercel URLs immediately after deployment
- Monitor production endpoints continuously

### 2. Pattern Maintenance

- Review patterns monthly
- Update for new infrastructure
- Document all changes

### 3. Security Hygiene

- Regularly audit allowed origins
- Monitor for unauthorized deployments
- Implement alerting for security issues

### 4. Performance Optimization

- Monitor upload processing times
- Implement resource limits
- Use batch processing for large operations

## Configuration Files

### Environment Variables

```bash
# Backend configuration
BACKEND_URL=***REMOVED***

# Monitoring settings
CORS_MONITORING_INTERVAL=300
CORS_ALERT_WEBHOOK_URL=https://hooks.slack.com/...
```

### Monitoring Config

```json
{
  "backend_url": "***REMOVED***",
  "monitoring_interval": 300,
  "alert_thresholds": {
    "failure_rate": 0.1,
    "response_time": 5.0,
    "consecutive_failures": 3
  },
  "notification": {
    "enabled": true,
    "webhook_url": "https://hooks.slack.com/...",
    "email": "alerts@yourdomain.com"
  }
}
```

## Future Enhancements

### 1. Automated Pattern Updates

- GitHub webhook integration
- Vercel API integration
- Dynamic pattern generation

### 2. Advanced Monitoring

- Integration with APM tools
- Dashboard creation
- Predictive alerting

### 3. Performance Optimization

- CDN integration
- Edge computing deployment
- Streaming upload processing

## Contact and Support

For CORS-related issues:

1. Check this documentation first
2. Run diagnostic commands
3. Review monitoring logs
4. Contact development team with:
   - Specific error messages
   - Browser console logs
   - Network request details
   - Deployment URL

---

**Last Updated**: January 2025  
**Version**: 2.0  
**Maintainer**: Development Team 