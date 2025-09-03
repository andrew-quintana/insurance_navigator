# Phase 1 Cloud Deployment Architecture

## 🏗️ **System Architecture Overview**

### **Deployment Topology**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Worker        │
│   (Vercel)      │◄──►│   (Render)      │◄──►│   (Render)      │
│                 │    │                 │    │                 │
│ Next.js App     │    │ FastAPI Server  │    │ Background      │
│ Port: 3000      │    │ Port: 8000      │    │ Worker Process  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Supabase Database                           │
│                 (PostgreSQL + Extensions)                      │
│                                                               │
│ • Authentication & Authorization                              │
│ • Document Storage & Processing                               │
│ • Vector Embeddings & Search                                  │
│ • Real-time Subscriptions                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🌐 **Service Details**

### **Frontend Service (Vercel)**
- **Platform**: Vercel
- **URL**: https://insurance-navigator.vercel.app
- **Technology**: Next.js 14, React, TypeScript
- **Configuration**:
  - Production build optimization
  - Legacy peer dependencies support
  - Environment variable management
  - CORS configuration

### **Backend API Service (Render)**
- **Platform**: Render (Web Service)
- **URL**: ***REMOVED***
- **Technology**: FastAPI, Python 3.11, Uvicorn
- **Configuration**:
  - Docker-based deployment
  - Multi-stage build optimization
  - Health check endpoints
  - Auto-scaling configuration
- **Services**:
  - Database connection pooling
  - User authentication service
  - Conversation management
  - Document storage service
  - External API integrations (OpenAI, LlamaParse)

### **Worker Service (Render)**
- **Platform**: Render (Background Worker)
- **Type**: Background processing service
- **Technology**: Python 3.11, Enhanced BaseWorker
- **Configuration**:
  - Docker-based deployment
  - Optimized for background processing
  - Environment variable isolation
  - Health monitoring
- **Capabilities**:
  - Document processing workflows
  - Queue management
  - Error handling and retries
  - Cost tracking and monitoring

### **Database Service (Supabase)**
- **Platform**: Supabase (PostgreSQL)
- **URL**: ***REMOVED***
- **Technology**: PostgreSQL with extensions
- **Features**:
  - Vector similarity search (pgvector)
  - Real-time subscriptions
  - Row-level security
  - Authentication & authorization
  - Edge functions support

---

## 🔧 **Configuration Management**

### **Environment Variables**

#### **Frontend (Vercel)**
```bash
NEXT_PUBLIC_SUPABASE_URL=***REMOVED***
NEXT_PUBLIC_SUPABASE_ANON_KEY=***REMOVED***...
NEXT_PUBLIC_API_BASE_URL=***REMOVED***
```

#### **Backend API (Render)**
```bash
SUPABASE_URL=***REMOVED***
SUPABASE_ANON_KEY=***REMOVED***...
SUPABASE_SERVICE_ROLE_KEY=***REMOVED***...
DATABASE_URL=postgresql://postgres:beqhar-qincyg-Syxxi8@db.znvwzkdblknkkztqyfnu.supabase.co:5432/postgres
DOCUMENT_ENCRYPTION_KEY=iSUAmk2NHMNW5bsn8F0UnPSCk9L+IxZhu/v/UyDwFcc=
OPENAI_API_KEY=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
ANTHROPIC_API_KEY=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
LLAMAPARSE_API_KEY=llx-X9bRG4r7mq5Basype0fCvfvlj1372pDdQXi7KaxVqkRlkoSb
```

#### **Worker Service (Render)**
```bash
SUPABASE_URL=***REMOVED***
SUPABASE_ANON_KEY=***REMOVED***...
SUPABASE_SERVICE_ROLE_KEY=***REMOVED***...
DATABASE_URL=postgresql://postgres:beqhar-qincyg-Syxxi8@db.znvwzkdblknkkztqyfnu.supabase.co:5432/postgres
OPENAI_API_KEY=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
ANTHROPIC_API_KEY=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
LLAMAPARSE_API_KEY=llx-X9bRG4r7mq5Basype0fCvfvlj1372pDdQXi7KaxVqkRlkoSb
```

---

## 🐳 **Docker Configuration**

### **API Service Dockerfile**
```dockerfile
# Multi-stage build for faster deployment
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies with caching
COPY config/python/requirements-prod.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Final stage - smaller image
FROM python:3.11-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory and copy app code
WORKDIR /app
COPY . .

# Copy pre-built dependencies
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Expose port and set environment variables
EXPOSE 8000
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Optimized health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=2 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use uvicorn directly
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### **Worker Service Dockerfile**
```dockerfile
# Multi-stage build for faster deployment
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies with caching
COPY backend/workers/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Final stage - smaller image
FROM python:3.11-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy pre-built dependencies
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy shared modules first
COPY backend/shared/ ./shared/

# Copy application code
COPY backend/workers/ ./

# Remove any conflicting config files that might be imported from the main API
RUN rm -rf ./config/ 2>/dev/null || true

# Set Python path to include the current directory
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Optimized health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=2 \
    CMD python -c "from enhanced_base_worker import EnhancedBaseWorker; print('Enhanced worker import successful')" || exit 1

# Run the enhanced worker
CMD ["python", "enhanced_runner.py"]
```

---

## 📊 **Service Configuration**

### **Render Service Configuration (render.yaml)**
```yaml
services:
  - type: web
    name: insurance-navigator-api
    env: docker
    plan: starter
    dockerfilePath: ./Dockerfile
    region: oregon
    branch: main
    port: 8000
    healthCheckPath: /health
    numReplicas: 1
    autoscaling:
      enabled: true
      minInstances: 1
      maxInstances: 3
      targetCPUPercent: 70

  - type: worker
    name: insurance-navigator-worker
    env: docker
    plan: starter
    dockerfilePath: ./backend/workers/Dockerfile
    region: oregon
    branch: main
    numReplicas: 1
    autoscaling:
      enabled: true
      minInstances: 1
      maxInstances: 2
      targetCPUPercent: 80
```

### **Vercel Configuration (vercel.json)**
```json
{
  "buildCommand": "npm run build",
  "installCommand": "npm install --legacy-peer-deps",
  "framework": "nextjs",
  "regions": ["iad1"],
  "functions": {
    "ui/pages/api/**/*.js": {
      "maxDuration": 30
    }
  }
}
```

---

## 🔍 **Monitoring & Health Checks**

### **Health Check Endpoints**
- **API Service**: `GET /health`
- **Worker Service**: Import validation check
- **Database**: Connection pool health
- **External Services**: OpenAI, LlamaParse, Anthropic API connectivity

### **Monitoring Tools**
- **Render Dashboard**: Service status and metrics
- **Vercel Analytics**: Frontend performance monitoring
- **Supabase Dashboard**: Database performance and usage
- **Custom Health Checks**: Automated service validation

### **Logging Configuration**
- **Structured Logging**: JSON-formatted logs for all services
- **Error Tracking**: Comprehensive error logging and monitoring
- **Performance Metrics**: Request timing and resource usage
- **Audit Trails**: User actions and system events

---

## 🚀 **Deployment Process**

### **Automated Deployment**
1. **Code Push**: Git push to main branch
2. **Build Trigger**: Automatic build initiation
3. **Docker Build**: Multi-stage optimized builds
4. **Service Deployment**: Rolling deployment with health checks
5. **Health Validation**: Automated service health verification
6. **Traffic Routing**: Gradual traffic migration to new deployment

### **Manual Deployment**
```bash
# API Service
curl -X POST "https://api.render.com/v1/services/srv-d0v2nqvdiees73cejf0g/deploys" \
  -H "Authorization: Bearer $RENDER_CLI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"clearCache": "clear"}'

# Worker Service
curl -X POST "https://api.render.com/v1/services/srv-d2h5mr8dl3ps73fvvlog/deploys" \
  -H "Authorization: Bearer $RENDER_CLI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"clearCache": "clear"}'
```

---

## 🔐 **Security Configuration**

### **Network Security**
- **HTTPS**: All services use HTTPS with SSL certificates
- **CORS**: Properly configured cross-origin resource sharing
- **Firewall**: Network-level security controls

### **Authentication & Authorization**
- **Supabase Auth**: JWT-based authentication
- **API Keys**: Secure storage and rotation
- **Environment Variables**: Encrypted storage in deployment platforms

### **Data Security**
- **Encryption**: Document encryption with Fernet
- **Database Security**: Row-level security policies
- **API Security**: Rate limiting and request validation

---

## 📈 **Performance Optimization**

### **Build Optimization**
- **Multi-stage Docker builds**: Reduced image size and build time
- **Dependency caching**: Optimized package installation
- **Parallel builds**: Concurrent service deployment

### **Runtime Optimization**
- **Connection pooling**: Database connection optimization
- **Caching**: Response caching and static asset optimization
- **Auto-scaling**: Dynamic resource allocation based on demand

### **Monitoring & Alerting**
- **Performance metrics**: Real-time service performance monitoring
- **Error tracking**: Automated error detection and alerting
- **Resource monitoring**: CPU, memory, and network usage tracking

---

**Architecture Status**: ✅ **PRODUCTION READY**  
**Last Updated**: September 3, 2025  
**Next Review**: Phase 2 completion
