# FM-030 Production Environment Reference

## **Production Service Configuration**

### **API Service (Production)**
- **Service ID**: `srv-d0v2nqvdiees73cejf0g`
- **Service Name**: `api-service-production`
- **Type**: Web Service
- **Status**: ✅ **HEALTHY**
- **URL**: `https://insurance-navigator-api.onrender.com`
- **Port**: 8000
- **Health Check**: `/health`
- **Environment**: Production
- **Branch**: `main`

### **Worker Service (Production)**
- **Service ID**: `srv-d2h5mr8dl3ps73fvvlog`
- **Service Name**: `upload-worker-production`
- **Type**: Background Worker
- **Status**: ❌ **FAILED**
- **Environment**: Production
- **Branch**: `main`

## **Production Environment Variables**

### **Required Environment Variables**

#### **Core Configuration**
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

#### **Supabase Configuration**
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpudnd6a2RibGtua2t6dHF5Zm51Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0NTYsImV4cCI6MjA2NzI1NjQ1Nn0.k0QHYOgm4EilyyTml57kCGDpbikpEtJCzq-qzGYQZqY
SUPABASE_SERVICE_ROLE_KEY=<PRODUCTION_SERVICE_ROLE_KEY>
```

#### **Database Configuration**
```bash
DATABASE_URL=postgresql://postgres.your-project:<PASSWORD>@aws-0-us-west-1.pooler.supabase.com:6543/postgres
DATABASE_SCHEMA=upload_pipeline
ASYNCPG_DISABLE_PREPARED_STATEMENTS=1
```

#### **External API Keys**
```bash
OPENAI_API_KEY=<PRODUCTION_OPENAI_KEY>
LLAMAPARSE_API_KEY=<PRODUCTION_LLAMAPARSE_KEY>
ANTHROPIC_API_KEY=<PRODUCTION_ANTHROPIC_KEY>
DOCUMENT_ENCRYPTION_KEY=<PRODUCTION_ENCRYPTION_KEY>
```

#### **Worker-Specific Configuration**
```bash
USE_MOCK_STORAGE=false
SERVICE_MODE=real
WORKER_POLL_INTERVAL=5
WORKER_MAX_RETRIES=3
WORKER_MAX_JOBS=10
LLAMAPARSE_BASE_URL=https://api.cloud.llamaindex.ai
OPENAI_API_URL=https://api.openai.com
OPENAI_MODEL=text-embedding-3-small
```

## **Production Database Configuration**

### **Database Details**
- **Host**: `aws-0-us-west-1.pooler.supabase.com`
- **Port**: `6543`
- **Database**: `postgres`
- **User**: `postgres.your-project`
- **SSL Mode**: `require`
- **Connection Pool**: 5-20 connections

### **Database URL Format**
```
postgresql://postgres.your-project:<PASSWORD>@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

## **Production Supabase Configuration**

### **Supabase Project Details**
- **Project URL**: `https://your-project.supabase.co`
- **Project ID**: `your-project`
- **Region**: `us-west-1`
- **Database Host**: `db.your-project.supabase.co`
- **Pooler Host**: `aws-0-us-west-1.pooler.supabase.com`

### **Supabase Keys**
- **Anon Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpudnd6a2RibGtua2t6dHF5Zm51Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0NTYsImV4cCI6MjA2NzI1NjQ1Nn0.k0QHYOgm4EilyyTml57kCGDpbikpEtJCzq-qzGYQZqY`
- **Service Role Key**: `<PRODUCTION_SERVICE_ROLE_KEY>`

## **Production API Keys**

### **OpenAI Configuration**
- **API URL**: `https://api.openai.com`
- **Model**: `text-embedding-3-small`
- **API Key**: `<PRODUCTION_OPENAI_KEY>`

### **LlamaParse Configuration**
- **API URL**: `https://api.cloud.llamaindex.ai`
- **API Key**: `<PRODUCTION_LLAMAPARSE_KEY>`

### **Anthropic Configuration**
- **API Key**: `<PRODUCTION_ANTHROPIC_KEY>`

## **Production Worker Configuration**

### **Worker Settings**
- **Poll Interval**: 5 seconds
- **Max Retries**: 3
- **Max Jobs**: 10
- **Service Mode**: Real (not mock)
- **Mock Storage**: Disabled

### **Worker Dependencies**
- Database connection pool
- Supabase storage service
- OpenAI API service
- LlamaParse API service
- Document encryption service

## **Production Monitoring**

### **Health Checks**
- **API Service**: `/health` endpoint
- **Worker Service**: Internal health monitoring
- **Database**: Connection pool health
- **External APIs**: Service availability

### **Logging Configuration**
- **Log Level**: INFO
- **Format**: JSON
- **Retention**: 7 days
- **Monitoring**: Enabled

## **Production Security**

### **Encryption**
- **Document Encryption**: Enabled
- **Database SSL**: Required
- **API Keys**: Secured in environment variables
- **Service Role Key**: Restricted access

### **Access Control**
- **Database**: Service role key required
- **Storage**: Service role key required
- **External APIs**: API keys required
- **Worker**: Internal service communication

## **Production Deployment**

### **Deployment Process**
1. Environment variables validation
2. Database connectivity test
3. Service initialization
4. Health check validation
5. Job processing test

### **Rollback Plan**
1. Revert environment variables
2. Restart worker service
3. Monitor service health
4. Validate functionality

## **Troubleshooting Guide**

### **Common Issues**
1. **Database Connection**: Check DATABASE_URL format
2. **Environment Variables**: Verify all required variables are set
3. **API Keys**: Validate key format and permissions
4. **Service Initialization**: Check service dependencies

### **Debug Commands**
```bash
# Check environment variables
echo $DATABASE_URL
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY

# Test database connection
psql $DATABASE_URL -c "SELECT 1;"

# Check worker logs
# (Use Render Dashboard or MCP tools)
```

### **Error Patterns**
- `[Errno 101] Network is unreachable` → Database URL issue
- `Required configuration field 'database_url' is empty` → Missing DATABASE_URL
- `CONFIGURATION_ERROR_FATAL` → Environment variable issue
- `Failed to start enhanced worker runner` → Initialization issue

## **Production Environment Checklist**

### **Pre-Deployment**
- [ ] All environment variables are set
- [ ] Database URL is correct
- [ ] API keys are valid
- [ ] Supabase configuration is correct
- [ ] Worker configuration is complete

### **Post-Deployment**
- [ ] Worker starts successfully
- [ ] Database connection is established
- [ ] Health checks are passing
- [ ] Job processing is working
- [ ] Error handling is functional

### **Monitoring**
- [ ] Worker logs are clean
- [ ] Database operations are successful
- [ ] External API calls are working
- [ ] Job processing is stable
- [ ] Performance is acceptable
