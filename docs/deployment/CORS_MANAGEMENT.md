# CORS Management Strategy

## **📋 Overview**

This document describes the centralized CORS (Cross-Origin Resource Sharing) management strategy for the Insurance Navigator API, inspired by [Supabase's CORS documentation](https://supabase.com/docs/guides/functions/cors).

## **🎯 Architecture: Centralized Configuration**

Instead of scattered CORS configuration throughout the codebase, we use a centralized approach similar to Supabase's `cors.ts` pattern:

```python
# utils/cors_config.py - Centralized CORS configuration
from utils.cors_config import cors_config, get_cors_headers, add_cors_headers

# Easy to import and use anywhere
headers = get_cors_headers(origin)
add_cors_headers(response, origin)
```

## **🔧 Configuration Structure**

### **Environment Variables**

```bash
# .env configuration
CORS_ALLOWED_ORIGINS="https://insurance-navigator.vercel.app,***REMOVED***,http://localhost:3000,http://localhost:3001"
CORS_VERCEL_PREVIEW_PATTERN="insurance-navigator-[a-z0-9]+-andrew-quintanas-projects\.vercel\.app"
```

### **Automatic Origin Detection**

The system automatically handles:

1. **Explicit Origins**: From `CORS_ALLOWED_ORIGINS` environment variable
2. **Localhost Patterns**: `localhost:3000`, `127.0.0.1:3000`, etc.
3. **Vercel Preview URLs**: Using regex pattern matching
4. **Wildcard Vercel**: Broad fallback for any `*.vercel.app` domain

## **🏗️ Implementation Patterns**

### **Pattern 1: Supabase-Style Manual Headers**
```python
from utils.cors_config import get_cors_headers, add_cors_headers

@app.get("/api/data")
async def get_data(request: Request):
    origin = request.headers.get("origin")
    
    # Your logic here
    data = {"message": "Hello"}
    
    # Add CORS headers like Supabase edge functions
    response = Response(content=json.dumps(data), media_type="application/json")
    add_cors_headers(response, origin)
    return response

@app.options("/api/data")
async def preflight_data(request: Request):
    return create_preflight_response(request.headers.get("origin"))
```

### **Pattern 2: FastAPI Middleware Integration**
```python
from utils.cors_config import cors_config

# Apply centralized config to FastAPI's built-in middleware
cors_middleware_config = cors_config.get_fastapi_cors_middleware_config()
app.add_middleware(CORSMiddleware, **cors_middleware_config)
```

### **Pattern 3: Custom Middleware (Current Implementation)**
```python
from utils.cors_config import create_preflight_response, add_cors_headers

class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        if request.method == "OPTIONS":
            return create_preflight_response(origin)
        
        response = await call_next(request)
        add_cors_headers(response, origin)
        return response
```

## **🔄 Migration from Hardcoded URLs**

### **Before: Scattered Configuration**
```python
# Multiple locations with hardcoded URLs
allow_origins=[
    "https://insurance-navigator.vercel.app",
    "https://insurance-navigator-e3j4jn4xj-andrew-quintanas-projects.vercel.app",
    "http://localhost:3000",
    # ... more hardcoded URLs
]
```

### **After: Centralized Management**
```python
# Single source of truth
from utils.cors_config import cors_config

# Automatically handles environment variables and patterns
cors_config.is_origin_allowed(origin)  # True/False
cors_config.get_cors_headers(origin)   # Complete headers dict
```

## **📚 Configuration Options**

### **CORSConfig Class Properties**

| Property | Description | Default |
|----------|-------------|---------|
| `allowed_origins` | List of explicit allowed origins | From env + localhost |
| `allowed_headers` | HTTP headers allowed in requests | `["authorization", "content-type", ...]` |
| `allowed_methods` | HTTP methods allowed | `["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"]` |
| `expose_headers` | Headers exposed to client | `["*"]` |
| `max_age` | Preflight cache duration | `86400` (24 hours) |
| `allow_credentials` | Whether to allow credentials | `True` |

### **Environment Variable Reference**

| Variable | Purpose | Example |
|----------|---------|---------|
| `CORS_ALLOWED_ORIGINS` | Comma-separated explicit origins | `"https://app.com,http://localhost:3000"` |
| `CORS_VERCEL_PREVIEW_PATTERN` | Regex pattern for Vercel previews | `"myapp-[a-z0-9]+-user-projects\.vercel\.app"` |

## **🔍 Origin Validation Logic**

The system validates origins in this order:

1. **Exact Match**: Check if origin is in `allowed_origins` list
2. **Localhost Pattern**: Match `localhost` or `127.0.0.1` with any port
3. **Vercel Preview Pattern**: Match specific project preview URL pattern
4. **Vercel Wildcard**: Match any `*.vercel.app` domain (fallback)

## **🚀 Deployment Considerations**

### **Development Environment**
```bash
# .env.local
CORS_ALLOWED_ORIGINS="http://localhost:3000,http://localhost:3001"
```

### **Production Environment**
```bash
# Production .env
CORS_ALLOWED_ORIGINS="https://insurance-navigator.vercel.app,***REMOVED***"
CORS_VERCEL_PREVIEW_PATTERN="insurance-navigator-[a-z0-9]+-andrew-quintanas-projects\.vercel\.app"
```

### **Staging Environment**
```bash
# Staging .env
CORS_ALLOWED_ORIGINS="https://staging-app.vercel.app,https://staging-api.render.com"
```

## **⚠️ Security Considerations**

### **Origin Validation**
- Never use `"*"` for `Access-Control-Allow-Origin` with credentials
- Always validate origins against known patterns
- Log failed origin validation attempts

### **Credential Handling**
- `allow_credentials=True` requires specific origin (not wildcard)
- Credentials include cookies, authorization headers, TLS certificates

### **Headers Exposure**
- Be careful with `expose_headers=["*"]` in production
- Consider limiting to specific headers: `["X-Total-Count", "X-Processing-Time"]`

## **🧪 Testing CORS Configuration**

### **Manual Testing**
```bash
# Test preflight request
curl -X OPTIONS ***REMOVED***/chat \
  -H "Origin: https://insurance-navigator.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: authorization,content-type" \
  -v

# Test actual request
curl -X POST ***REMOVED***/chat \
  -H "Origin: https://insurance-navigator.vercel.app" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}' \
  -v
```

### **Automated Testing**
```python
# scripts/testing/test_cors.py
from utils.cors_config import cors_config

def test_origin_validation():
    assert cors_config.is_origin_allowed("https://insurance-navigator.vercel.app")
    assert cors_config.is_origin_allowed("http://localhost:3000")
    assert not cors_config.is_origin_allowed("https://malicious-site.com")
```

## **📖 Usage Examples**

See `utils/cors_examples.py` for comprehensive usage examples including:

1. Manual CORS header management (Supabase style)
2. FastAPI middleware integration
3. Custom middleware implementation
4. Edge function pattern
5. Environment-based configuration

## **🔗 Related Documentation**

- [Supabase CORS Documentation](https://supabase.com/docs/guides/functions/cors)
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [MDN CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)

## **📝 Changelog**

- **v2.0.0**: Implemented centralized CORS configuration
- **v1.0.0**: Original hardcoded CORS implementation 