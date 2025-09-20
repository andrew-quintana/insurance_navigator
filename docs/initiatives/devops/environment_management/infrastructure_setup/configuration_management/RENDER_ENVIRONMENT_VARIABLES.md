# Render Environment Variables Configuration

**Date**: January 21, 2025  
**Service**: Staging API Service  
**Status**: 🔧 **CONFIGURING**  

## Critical Understanding

**⚠️ IMPORTANT**: The `.env.staging` file is **ONLY for local development**. Render services use environment variables set in the Render dashboard, not local `.env` files.

## Required Environment Variables for Staging API Service

### **Core Application Variables**
```bash
# Port Configuration (CRITICAL)
PORT=10000                    # Render platform requirement
API_HOST=0.0.0.0             # External access for Render
API_PORT=8000                # Application port (internal)

# Environment
ENVIRONMENT=staging
NODE_ENV=staging
```

### **Database Configuration**
```bash
# Supabase Staging Instance
SUPABASE_URL=***REMOVED***
ANON_KEY=***REMOVED***.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0ODMsImV4cCI6MjA2NzI1NjQ4M30.wV0kgqo20D1EghH47bO-4MoXpksiyQ_bvANaZlzScyM
SERVICE_ROLE_KEY=***REMOVED***.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0ODMsImV4cCI6MjA2NzI1NjQ4M30.wV0kgqo20D1EghH47bO-4MoXpksiyQ_bvANaZlzScyM

# Database Connection (Use Pooler URL for Render)
DATABASE_URL=postgresql://postgres.dfgzeastcxnoqshgyotp:tukwof-pyVxo5-qejnoj@aws-0-us-west-1.pooler.supabase.com:6543/postgres
SUPABASE_DATABASE_URL=postgresql://postgres.dfgzeastcxnoqshgyotp:tukwof-pyVxo5-qejnoj@aws-0-us-west-1.pooler.supabase.com:6543/postgres
SUPABASE_POOLER_URL=postgresql://postgres.dfgzeastcxnoqshgyotp:tukwof-pyVxo5-qejnoj@aws-0-us-west-1.pooler.supabase.com:6543/postgres

# Database Details
DB_HOST=aws-0-us-west-1.pooler.supabase.com
DB_PORT=6543
DB_USER=postgres.dfgzeastcxnoqshgyotp
DB_PASSWORD=tukwof-pyVxo5-qejnoj
DB_NAME=postgres
```

### **Application Configuration**
```bash
# Logging
LOG_LEVEL=INFO
API_DEBUG=false

# Health Check
HEALTH_CHECK_PATH=/health

# External URLs
NEXT_PUBLIC_API_BASE_URL=***REMOVED***
NEXT_PUBLIC_APP_URL=https://insurance-navigator.vercel.app
NEXT_PUBLIC_WEB_URL=https://insurance-navigator.vercel.app
NEXT_PUBLIC_SUPABASE_URL=***REMOVED***
NEXT_PUBLIC_SUPABASE_ANON_KEY=***REMOVED***.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0ODMsImV4cCI6MjA2NzI1NjQ4M30.wV0kgqo20D1EghH47bO-4MoXpksiyQ_bvANaZlzScyM
```

### **API Keys and External Services**
```bash
# OpenAI
OPENAI_API_KEY=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

# Anthropic
ANTHROPIC_API_KEY=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

# LlamaIndex
LLAMACLOUD_API_KEY=llx-CRtlURo7FT74ZMydik58KjPHC5aTpOSuGjWqOkTXjrPQucUS
LLAMAPARSE_API_KEY=llx-CRtlURo7FT74ZMydik58KjPHC5aTpOSuGjWqOkTXjrPQucUS
LLAMAPARSE_BASE_URL=https://api.cloud.llamaindex.ai

# LangChain
LANGCHAIN_API_KEY=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
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_TRACING_V2=true

# Encryption
DOCUMENT_ENCRYPTION_KEY=iSUAmk2NHMNW5bsn8F0UnPSCk9L+IxZhu/v/UyDwFcc=
```

## Current Status Check

### **What We've Set in Render**
✅ `API_HOST=0.0.0.0`  
✅ `PORT=10000`  
✅ `API_PORT=8000`  

### **What Still Needs to be Set**
❓ **Database URL** - Need to verify if using pooler URL  
❓ **All other environment variables** - Need to verify complete set  

## Critical Issues to Address

### **1. Database Connection**
- **Current**: May be using direct database URL
- **Required**: Must use Supabase pooler URL for Render
- **Reason**: Render platform network restrictions

### **2. Port Configuration**
- **Current**: `PORT=10000` ✅
- **Current**: `API_HOST=0.0.0.0` ✅
- **Status**: Correctly configured

### **3. Health Check**
- **Current**: May not be configured
- **Required**: `HEALTH_CHECK_PATH=/health`
- **Reason**: Render needs health check endpoint

## Next Steps

1. **Verify Current Environment Variables**: Check what's actually set in Render dashboard
2. **Update Database URL**: Ensure using pooler URL instead of direct connection
3. **Set Health Check Path**: Configure health check endpoint
4. **Complete Environment Variables**: Set all required variables
5. **Test Deployment**: Verify service starts correctly

## How to Update Render Environment Variables

1. Go to Render Dashboard
2. Navigate to `api-service-staging`
3. Go to "Environment" tab
4. Add/Update the required variables
5. Save changes (triggers new deployment)

## Expected Outcome

After setting all required environment variables:
```
INFO:     Uvicorn running on http://0.0.0.0:10000 (Press CTRL+C to quit)
INFO:     Application startup complete.
INFO:     10.219.16.25:38316 - "GET /health HTTP/1.1" 200 OK
```

---

**Configuration Status**: 🔧 **IN PROGRESS**  
**Critical Variables**: Port and Host ✅, Database ❓, Health Check ❓  
**Next Action**: Verify and complete Render environment variable configuration
