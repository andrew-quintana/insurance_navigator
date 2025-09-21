# 🚀 FastAPI + Supabase + Render Deployment Guide

This guide will help you deploy your Insurance Navigator FastAPI backend to production using Supabase and Render.

## 📋 Prerequisites Checklist

- ✅ FastAPI application (`main.py`)
- ✅ `requirements.txt` with dependencies
- ✅ Git repository
- ✅ `Dockerfile` (created)
- ✅ Supabase client integration (already in your code)

## 🗄️ Step 1: Supabase Setup

### Option A: Using Supabase Dashboard (Recommended)

1. **Create Supabase Account**
   - Go to [supabase.com](https://supabase.com)
   - Sign up with GitHub/Google

2. **Create New Project**
   - Click "New Project"
   - Choose organization
   - Name: `insurance-navigator`
   - Database password: Generate strong password
   - Region: Choose closest to your users
   - Click "Create new project"

3. **Get Configuration Values**
   - Go to Settings → API
   - Copy these values:
     - `Project URL` → `SUPABASE_URL`
     - `anon public` key → `SUPABASE_ANON_KEY`
     - `service_role secret` key → `SUPABASE_SERVICE_ROLE_KEY`
   - Go to Settings → Database
   - Copy `Connection string` → `DATABASE_URL`

### Option B: Using Supabase CLI

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Initialize project
supabase init

# Link to existing project or create new
supabase link --project-ref your-project-ref
```

## 🚀 Step 2: Render Deployment

### Method 1: Using render.yaml (Recommended)

1. **Connect Repository**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml`

2. **Configure Environment Variables**
   - In Render dashboard, go to your service
   - Navigate to "Environment" tab
   - Add these variables:
   ```
   SUPABASE_URL=https://your-project-ref.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   DATABASE_URL=${DATABASE_URL}/month)
   - Auto-Deploy: Yes
   - Health Check Path: `/health`

## 🔐 Step 3: Environment Variables Setup

Create these environment variables in Render:

```bash
# Supabase Configuration
SUPABASE_URL=https://xyzcompany.supabase.co
SUPABASE_ANON_KEY=${SUPABASE_JWT_TOKEN}
SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_JWT_TOKEN}

# Database (from Supabase Settings → Database)
DATABASE_URL=${DATABASE_URL}//your-app-name.onrender.com
```

## 🔌 Step 4: Database Connection Test

Your app already has Supabase integration! Test with this endpoint after deployment:

```bash
# Test health endpoint
curl https://your-app-name.onrender.com/health

# Test database connection (requires auth)
curl https://your-app-name.onrender.com/me \
  -H "Authorization: Bearer your-jwt-token"
```

## 🧪 Step 5: Local Testing

Test your Docker setup locally:

```bash
# Build Docker image
docker build -t insurance-navigator .

# Run with environment file
docker run -p 8000:8000 --env-file .env insurance-navigator

# Test endpoints
curl http://localhost:8000/health
```

## 🔄 Step 6: CI/CD Auto-Deploy

Render automatically deploys when you push to your main branch. To customize:

1. **Branch Settings**
   - Go to service settings
   - Change "Branch" from main to your preferred branch

2. **Build Hooks**
   - Use deploy hooks for manual triggers
   - Webhook URL available in service settings

## ✅ Step 7: Production Checklist

### Before Going Live:
- [ ] Test all API endpoints
- [ ] Verify database connection
- [ ] Check CORS origins for your frontend
- [ ] Enable monitoring/logging
- [ ] Set up SSL (automatic with Render)
- [ ] Configure custom domain (optional)

### Security:
- [ ] JWT secret is strong and unique
- [ ] Database credentials are secure
- [ ] `SECURITY_BYPASS_ENABLED=false`
- [ ] All sensitive data in environment variables

### Performance:
- [ ] Enable connection pooling
- [ ] Monitor resource usage
- [ ] Set up health checks
- [ ] Configure proper logging

## 🛠️ Troubleshooting

### Common Issues:

**Build Failures:**
```bash
# Check build logs in Render dashboard
# Verify Dockerfile syntax
# Ensure all dependencies in requirements.txt
```

**Database Connection:**
```bash
# Verify DATABASE_URL format
# Check Supabase project status
# Confirm connection pooling settings
```

**Environment Variables:**
```bash
# Ensure no extra spaces in values
# Check for proper encoding
# Verify all required vars are set
```

## 📊 Monitoring & Logs

1. **Render Logs**
   - Go to service → Logs tab
   - Real-time log streaming
   - Filter by log level

2. **Health Monitoring**
   - Automatic health checks on `/health`
   - Uptime monitoring included
   - Alert configuration available

## 🚀 Next Steps

1. **Custom Domain**
   ```bash
   # In Render dashboard:
   # Settings → Custom Domains → Add Domain
   ```

2. **Frontend Integration**
   - Update CORS_ORIGINS with your frontend URL
   - Update API_BASE_URL in frontend config

3. **Database Migrations**
   - Run Alembic migrations after first deploy
   - Set up migration automation

## 💰 Cost Estimate

- **Render Starter**: $7/month
- **Supabase Pro**: $25/month (includes auth, database, storage)
- **Total**: ~$32/month for production-ready setup

## 🔗 Useful Links

- [Render Documentation](https://render.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

Your API will be available at: `https://your-app-name.onrender.com` 