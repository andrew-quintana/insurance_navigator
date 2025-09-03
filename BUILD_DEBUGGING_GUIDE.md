# Build Debugging Guide - Render Services

## Overview

This guide provides comprehensive instructions for debugging build issues with the Insurance Navigator API and Worker services on Render. The guide covers when to debug, how to analyze build failures, and how to resolve common issues.

## When to Debug Build Issues

### 🔍 **Immediate Debugging Required**

1. **Service Health Check Failures**
   - API service returns non-200 status codes
   - Worker service completely inaccessible
   - Health endpoints not responding

2. **Deployment Failures**
   - Build process fails during Docker image creation
   - Service fails to start after successful build
   - Environment variable configuration errors

3. **Performance Issues**
   - Response times > 5 seconds
   - High error rates (>5%)
   - Service timeouts or crashes

### ⚠️ **Investigation Recommended**

1. **Warning Status in Tests**
   - Services return 404/500 status codes
   - Intermittent connectivity issues
   - Performance degradation

2. **Configuration Issues**
   - Environment variables not loading
   - Database connection failures
   - External service integration problems

## Build Analysis Tools

### 1. **Automated Build Analyzer**

Run the comprehensive build analyzer:

```bash
python scripts/cloud_deployment/render_build_analyzer.py
```

**What it analyzes:**
- Service health and deployment status
- Performance metrics and response times
- Deployment logs and build history
- Build quality assessment with grades
- Specific recommendations for improvements

### 2. **Phase 1 Testing Framework**

Run the updated Phase 1 tests with build validation:

```bash
python scripts/cloud_deployment/phase1_test.py
```

**What it tests:**
- Vercel frontend deployment
- Render API service deployment
- Render worker service deployment
- **NEW:** Render build status and deployment logs
- Supabase database connectivity

## Debugging Workflow

### Step 1: Run Build Analysis

```bash
# Run comprehensive build analysis
python scripts/cloud_deployment/render_build_analyzer.py

# Run Phase 1 tests with build validation
python scripts/cloud_deployment/phase1_test.py
```

### Step 2: Analyze Results

Check the generated JSON files for detailed analysis:
- `render_build_analysis_YYYYMMDD_HHMMSS.json`
- `phase1_test_results_YYYYMMDD_HHMMSS.json`

### Step 3: Access Render Dashboard

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Navigate to Services**:
   - `insurance-navigator-api` (API service)
   - `insurance-navigator-worker` (Worker service)
3. **Check Deployment Logs**:
   - Click on the service
   - Go to "Logs" tab
   - Review build and runtime logs

### Step 4: Common Issue Resolution

## Common Build Issues & Solutions

### 🚨 **API Service Issues**

#### Issue: Health Check Failing (500 Error)
**Symptoms:**
- `/health` endpoint returns 500
- Service appears deployed but unhealthy

**Debug Steps:**
1. Check Render logs for Python errors
2. Verify environment variables are set
3. Check database connectivity
4. Review dependency installation

**Common Causes:**
- Missing environment variables
- Database connection issues
- Python dependency conflicts
- Port binding problems

**Solutions:**
```bash
# Check environment variables in Render dashboard
# Verify these are set:
- SUPABASE_URL
- SUPABASE_KEY
- SERVICE_ROLE_KEY
- DATABASE_URL
- API_BASE_URL

# Check database connectivity
# Ensure DATABASE_URL is correct and accessible
```

#### Issue: Service Not Starting
**Symptoms:**
- Build succeeds but service doesn't start
- Container exits immediately

**Debug Steps:**
1. Check Dockerfile configuration
2. Verify start command in render.yaml
3. Review port configuration
4. Check for missing dependencies

**Solutions:**
```yaml
# In render.yaml, ensure correct start command:
startCommand: "uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1"

# Verify Dockerfile exposes correct port:
EXPOSE 8000
```

### ⚙️ **Worker Service Issues**

#### Issue: Worker Service Not Deploying
**Symptoms:**
- Worker service returns 404 (expected)
- But service shows as failed in Render dashboard

**Debug Steps:**
1. Check worker Dockerfile
2. Verify worker requirements.txt
3. Review worker startup script
4. Check worker-specific environment variables

**Solutions:**
```dockerfile
# Ensure worker Dockerfile is correct:
FROM python:3.11-slim
WORKDIR /app
COPY backend/workers/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/workers/ ./
CMD ["python", "enhanced_runner.py"]
```

#### Issue: Worker Not Processing Jobs
**Symptoms:**
- Worker deploys successfully
- But no job processing occurs

**Debug Steps:**
1. Check worker logs for startup errors
2. Verify database connectivity
3. Check job queue configuration
4. Review worker environment variables

**Solutions:**
```bash
# Ensure these environment variables are set for worker:
- DATABASE_URL
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- LLAMAPARSE_API_KEY
- OPENAI_API_KEY
```

### 🗄️ **Database Issues**

#### Issue: Database Connection Failures
**Symptoms:**
- Services can't connect to Supabase
- Database queries failing

**Debug Steps:**
1. Verify DATABASE_URL format
2. Check Supabase project status
3. Verify connection limits
4. Review RLS policies

**Solutions:**
```bash
# DATABASE_URL format should be:
postgresql://postgres:[password]@[host]:5432/postgres

# Check Supabase dashboard for:
- Project status (not paused)
- Connection limits
- Database extensions (pgvector)
```

## Performance Optimization

### Build Performance

1. **Docker Layer Optimization**
   - Use multi-stage builds
   - Cache dependencies
   - Minimize image size

2. **Dependency Management**
   - Use requirements.txt with pinned versions
   - Remove unused dependencies
   - Use Python virtual environments

### Runtime Performance

1. **Response Time Optimization**
   - Target: < 2 seconds for API calls
   - Use connection pooling
   - Implement caching where appropriate

2. **Resource Management**
   - Monitor CPU and memory usage
   - Configure auto-scaling appropriately
   - Optimize database queries

## Monitoring and Alerting

### Build Monitoring

1. **Automated Testing**
   - Run build analysis after each deployment
   - Set up CI/CD pipeline integration
   - Monitor build success rates

2. **Performance Monitoring**
   - Track response times
   - Monitor error rates
   - Set up alerts for failures

### Log Analysis

1. **Render Logs**
   - Access via Render dashboard
   - Filter by service and time
   - Look for error patterns

2. **Application Logs**
   - Check Python application logs
   - Monitor database query logs
   - Review external service integration logs

## Troubleshooting Checklist

### ✅ **Pre-Deployment Checks**

- [ ] All environment variables configured
- [ ] Dockerfile syntax correct
- [ ] Requirements.txt up to date
- [ ] Database accessible
- [ ] External services configured

### ✅ **Post-Deployment Checks**

- [ ] Service health checks passing
- [ ] API endpoints responding
- [ ] Database connectivity working
- [ ] Worker processes running
- [ ] Performance metrics acceptable

### ✅ **Ongoing Monitoring**

- [ ] Regular build analysis runs
- [ ] Performance monitoring active
- [ ] Error rate tracking
- [ ] Resource usage monitoring
- [ ] Log analysis for issues

## Emergency Procedures

### 🚨 **Service Down**

1. **Immediate Actions**
   - Check Render dashboard for service status
   - Review recent deployment logs
   - Verify environment variables
   - Check external service status

2. **Rollback Options**
   - Revert to previous deployment
   - Disable auto-deployments
   - Scale down problematic services

3. **Communication**
   - Update team on status
   - Document issue and resolution
   - Post-mortem analysis

### 🔧 **Build Failures**

1. **Investigation**
   - Run build analyzer
   - Check deployment logs
   - Verify configuration
   - Test locally if possible

2. **Resolution**
   - Fix configuration issues
   - Update dependencies
   - Adjust resource limits
   - Redeploy service

## Best Practices

### Development Workflow

1. **Local Testing**
   - Test changes locally first
   - Use same environment variables
   - Verify Docker builds locally

2. **Staging Deployment**
   - Deploy to staging first
   - Run full test suite
   - Validate performance

3. **Production Deployment**
   - Deploy during low-traffic periods
   - Monitor closely after deployment
   - Have rollback plan ready

### Configuration Management

1. **Environment Variables**
   - Use consistent naming
   - Document all variables
   - Validate before deployment

2. **Service Configuration**
   - Use version-controlled config files
   - Test configuration changes
   - Document configuration decisions

## Tools and Resources

### Built-in Tools
- `scripts/cloud_deployment/render_build_analyzer.py` - Comprehensive build analysis
- `scripts/cloud_deployment/phase1_test.py` - Phase 1 testing with build validation
- `config/render/render.yaml` - Render service configuration

### External Resources
- [Render Documentation](https://render.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Docker Documentation](https://docs.docker.com/)

### Monitoring Dashboards
- [Render Dashboard](https://dashboard.render.com)
- [Supabase Dashboard](https://supabase.com/dashboard)
- [Vercel Dashboard](https://vercel.com/dashboard)

---

**Remember**: Always run the build analyzer after making changes to identify issues early and ensure optimal performance!
