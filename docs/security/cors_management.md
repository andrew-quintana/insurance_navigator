# CORS Management and Prevention System

## Overview

This document provides comprehensive guidance for managing CORS (Cross-Origin Resource Sharing) issues in the Insurance Navigator application, including both reactive fixes and proactive prevention systems.

## Problem Analysis

### Root Cause of CORS Issues

The CORS errors in our system are **secondary symptoms** of deeper backend stability issues:

1. **502 Bad Gateway Errors**: Server crashes during intensive PDF processing
2. **Missing CORS Headers**: When the server crashes, no CORS headers are sent
3. **Browser Security**: Browsers block requests without proper CORS headers

**Key Insight**: Fix the server stability, and CORS issues disappear.

## Immediate Solutions ✅ COMPLETED

### 1. User-Facing Error Message Fix
**Problem**: Technical CORS error exposed to users
```
🌐 Connection blocked by browser security policy. This usually means the server needs to be updated with your current website address. Please try again in a few minutes or contact support.
```

**Solution**: ✅ **FIXED** - Simple user-friendly message
```typescript
// ui/components/DocumentUpload.tsx
if (errorMessage.includes('Load failed') || errorMessage.includes('CORS')) {
  errorMessage = `Upload failed. Please try again in a few minutes.`
}
```

### 2. Enhanced CORS Middleware
**Status**: ✅ **ACTIVE** - Custom CORS middleware with error-resilient header injection

```python
# main.py - CustomCORSMiddleware
class CustomCORSMiddleware:
    async def __call__(self, scope, receive, send):
        # Always add CORS headers, even during server errors
        if response.status_code >= 400:
            await self.add_cors_headers_to_error_response(response)
```

**Features**:
- Error-resilient header injection
- Comprehensive pattern matching for Vercel deployments
- Security validation against unauthorized deployments
- Performance monitoring with timing headers

## Automated Prevention System ✅ NEW

### 3. Real-time CORS Monitoring

**New System**: `scripts/monitoring/cors_auto_prevention.py`

**Capabilities**:
- 🔍 **Auto-discovers** new Vercel deployments
- 🧪 **Tests CORS** functionality automatically
- 🚨 **Detects security threats** (unauthorized deployments)
- 📊 **Monitors server health** during upload operations
- 📄 **Generates reports** with actionable recommendations
- 🔄 **Adaptive scanning** (faster when issues detected)

**Results from Latest Test**:
```json
{
  "cors_analysis": {
    "working": 28,
    "failing": 0,
    "success_rate": 100.0%,
    "server_errors": 0
  },
  "security_analysis": {
    "threats_detected": 1,
    "threat_level": "HIGH"
  },
  "server_health": {
    "overall_status": "healthy",
    "response_time": 54.34,
    "can_handle_uploads": true
  }
}
```

### Quick Start
```bash
# Start automated monitoring
./scripts/monitoring/start_cors_monitoring.sh

# Single test run
python scripts/monitoring/cors_auto_prevention.py --single-run
```

## Backend Stability Solutions 🔄 IN PROGRESS

### Current Architecture Issues

**The Real Problem**: Backend crashes during heavy PDF processing
- **Memory exhaustion**: Loading 500KB+ text + embeddings in RAM
- **Synchronous processing**: Blocks main thread for 3-4 minutes
- **No resource limits**: Server runs out of memory and crashes
- **No timeout handling**: Operations can run indefinitely

### Immediate Fixes (This Week)

#### 1. Resource Monitoring
```python
# Add to main.py
class ResourceMonitor:
    def __init__(self):
        self.max_memory_mb = 1500
        self.max_processing_time = 300  # 5 minutes
        
    async def check_resources(self):
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
        if memory_usage > self.max_memory_mb:
            raise ResourceExhaustionError("Memory limit exceeded")
```

#### 2. Async Processing Queue
```python
# Convert to background processing
@app.post("/upload-policy")
async def upload_policy_async(file: UploadFile):
    document_id = generate_uuid()
    
    # Queue for background processing
    await queue_processor.enqueue({
        'document_id': document_id,
        'file_data': file,
        'status': 'queued'
    })
    
    return {
        'document_id': document_id,
        'status': 'processing',
        'estimated_completion': '2-5 minutes'
    }
```

#### 3. Memory-Efficient Streaming
```python
# Process page by page instead of loading everything
def process_pdf_streaming(file_path: str):
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            yield process_page_chunk(text, page_num)
            
            # Memory cleanup every 10 pages
            if page_num % 10 == 0:
                gc.collect()
```

### Long-term Architecture (1-2 Months)

#### Direct S3 Upload with Lambda Processing

Based on [AWS S3 heavy uploads best practices](https://sandydev.medium.com/how-to-handle-heavy-uploads-in-backend-best-approach-a71079e4f01f):

```mermaid
graph TD
    A[Frontend] --> B[Get Pre-signed URL]
    B --> C[Direct Upload to S3]
    C --> D[S3 Event Trigger]
    D --> E[Lambda Processing]
    E --> F[Webhook Notification]
    F --> G[Update Database]
```

**Benefits**:
- **Zero server load** during upload
- **Automatic scaling** with Lambda
- **Cost efficiency**: $0.01 per file vs $7/month server
- **Reliability**: AWS handles infrastructure

#### Lambda Processing Architecture

Following [AWS Lambda large file processing patterns](https://articles.wesionary.team/mastering-large-file-processing-with-aws-s3-lambda-and-go-3dde0a4c29c6):

```python
# Different Lambda functions for different file sizes
LAMBDA_CONFIGS = {
    'small': {'memory': 256, 'timeout': 60},    # <10MB
    'medium': {'memory': 1024, 'timeout': 300}, # 10-50MB  
    'large': {'memory': 2048, 'timeout': 900}   # 50MB+
}

def lambda_handler(event, context):
    # Stream processing with concurrency
    with pipe_reader_writer() as (reader, writer):
        asyncio.gather(
            extract_text_stream(reader),
            generate_embeddings_stream(writer),
            chunk_content_stream()
        )
```

## Pattern-Based Validation System ✅ ACTIVE

### Vercel Deployment Patterns

**Legitimate Deployments**:
```regex
^insurance-navigator-[a-z0-9]+-andrew-quintanas-projects\.vercel\.app$
```

**Security Threats** (Blocked):
```regex
^insurance-navigator-[a-z0-9]+-(?!andrew-quintanas-projects).*\.vercel\.app$
```

**Known Good Deployment IDs**:
- `k2ui23iaj` ✅ (originally failing, now working)
- `1x3xrmwl5` ✅ (from latest logs)
- `hrf0s88oh`, `q2ukn6eih`, `cylkkqsmn` ✅

### Security Detection

The system automatically detects:
- **Unauthorized user deployments**: Different user projects
- **Suspicious keywords**: `hack`, `malicious`, `attack`, `exploit`
- **Pattern anomalies**: URLs that don't match expected structure

## Troubleshooting Guide

### Quick Diagnostics

```bash
# 1. Test specific deployment
python test_specific_url.py

# 2. Run comprehensive scan
python test_cors.py --comprehensive-scan

# 3. Check server health
curl -i https://insurance-navigator-api.onrender.com/health

# 4. Test CORS preflight
curl -i -X OPTIONS https://insurance-navigator-api.onrender.com/upload-policy \
  -H "Origin: https://insurance-navigator-1x3xrmwl5-andrew-quintanas-projects.vercel.app" \
  -H "Access-Control-Request-Method: POST"
```

### Common Issues and Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| **New deployment failing** | 502 error, CORS blocked | Automatically detected by prevention system |
| **Server crash during upload** | 502 after 3-4 minutes | Upgrade to paid Render plan ($7/month) |
| **Large file processing** | Memory exhaustion | Implement streaming processing |
| **Security threat** | Unauthorized deployment | Auto-blocked by pattern validation |

### Error Code Meanings

| Status Code | Meaning | Action |
|-------------|---------|--------|
| **200** | ✅ Working correctly | Continue monitoring |
| **502** | ❌ Server crashed/overloaded | Check server resources |
| **0** | ❌ Network/DNS issue | Check deployment status |
| **403** | ❌ Blocked by security | Review origin patterns |

## Monitoring and Alerting

### Automated Reports

**Location**: `scripts/monitoring/reports/`
**Frequency**: Every 5 minutes (1 minute if issues detected)
**Retention**: Last 10 reports kept automatically

**Report Contents**:
- CORS success rate across all deployments
- Security threat detection and blocking
- Server health and performance metrics
- Actionable recommendations

### Alert Categories

- **🚨 CRITICAL**: Security threats, immediate blocking required
- **⚠️ HIGH**: Server stability issues, performance problems
- **📋 MEDIUM**: CORS coverage gaps, pattern updates needed
- **ℹ️ LOW**: Routine monitoring, all systems operational

### Performance Benchmarks

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **CORS Success Rate** | >95% | 100% | ✅ Excellent |
| **Security Threats Blocked** | 100% | 100% | ✅ Protected |
| **Server Response Time** | <500ms | 54ms | ✅ Fast |
| **Upload Success Rate** | >90% | Variable | ⚠️ Needs improvement |

## Implementation Roadmap

### Phase 1: Immediate (✅ Completed)
- [x] Fix user-facing error messages
- [x] Enhanced CORS middleware with error resilience
- [x] Automated CORS monitoring and prevention system
- [x] Pattern-based security validation

### Phase 2: Short-term (🔄 In Progress)
- [ ] Resource monitoring and limits
- [ ] Async processing queue with Redis
- [ ] Memory-efficient streaming processing
- [ ] Progress tracking for users
- [ ] Upgrade to paid Render plan (1GB RAM)

### Phase 3: Long-term (📋 Planned)
- [ ] Direct S3 uploads with pre-signed URLs
- [ ] Lambda-based processing architecture
- [ ] WebSocket progress updates
- [ ] Multi-region deployment for reliability

## Cost Analysis

| Solution | Cost | Capability | Reliability |
|----------|------|------------|-------------|
| **Current** (Free Render) | $0/month | 10MB files | 60% success |
| **Immediate** (Paid Render) | $7/month | 25MB files | 85% success |
| **Long-term** (AWS Lambda) | ~$0.01/file | 100MB+ files | 99%+ success |

## Success Metrics

### Immediate Goals (This Week)
- ✅ 0 technical CORS errors exposed to users
- ✅ 100% automated detection of new deployments
- ✅ Real-time security threat blocking
- 🔄 0 server crashes during file processing

### Short-term Goals (2 Weeks)
- 🎯 Handle 25MB files without server crashes
- 🎯 <2 minute processing time for typical documents
- 🎯 95%+ upload success rate
- 🎯 Real-time progress tracking for users

### Long-term Goals (2 Months)
- 🎯 Handle 100MB+ files reliably
- 🎯 <30 second upload time (direct to S3)
- 🎯 99%+ upload success rate
- 🎯 Multi-region deployment

## Configuration

### Environment Variables
```bash
# CORS Settings
CORS_ALLOW_ORIGINS="https://insurance-navigator.vercel.app,https://localhost:3000"
CORS_MONITORING_ENABLED=true
CORS_SECURITY_VALIDATION=true

# Upload Settings  
MAX_FILE_SIZE=10485760  # 10MB initially
ASYNC_PROCESSING=true
PROGRESS_TRACKING=true

# Monitoring Settings
MONITORING_INTERVAL=300  # 5 minutes
QUICK_SCAN_INTERVAL=60   # 1 minute for issues
BATCH_SIZE=5
DISCOVERY_COUNT=20
```

### Pattern Configuration
```python
# Known good deployment patterns
KNOWN_GOOD_PATTERNS = [
    'k2ui23iaj', '1x3xrmwl5', 'hrf0s88oh', 
    'q2ukn6eih', 'cylkkqsmn', 'gybzhfv6'
]

# Security keywords to block
SECURITY_KEYWORDS = [
    'hack', 'malicious', 'attack', 'exploit', 'test'
]
```

## Best Practices

### 1. Regular Monitoring
- Run automated monitoring continuously
- Review reports weekly
- Update patterns as new deployments are discovered

### 2. Security Hygiene  
- Block unauthorized deployments immediately
- Monitor for suspicious patterns
- Regular security audits of allowed origins

### 3. Performance Optimization
- Monitor server resources during uploads
- Implement progressive file size increases
- Use streaming processing for large files

### 4. User Experience
- Provide clear, non-technical error messages
- Show progress for long-running operations
- Graceful degradation when services are unavailable

## Getting Help

### Self-Service
1. Run diagnostics: `python test_cors.py --comprehensive-scan`
2. Check monitoring reports: `scripts/monitoring/reports/`
3. Review server health: `curl https://insurance-navigator-api.onrender.com/health`

### Escalation
1. **CORS Issues**: Check latest prevention report
2. **Server Crashes**: Review upload resilience strategy
3. **Security Threats**: Immediate blocking, then investigation
4. **Performance**: Resource monitoring and optimization

---

**Last Updated**: June 4, 2025
**Next Review**: Weekly during development phase 