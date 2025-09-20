# Port Configuration Standard

**Date**: January 21, 2025  
**Version**: 1.0  
**Status**: ✅ **IMPLEMENTED**  

## Overview

This document establishes the standardized port configuration for the Insurance Navigator project across all environments and services, following industry best practices for port management.

## Port Assignment Standards

### Standard Port Assignments

| Service | Port | Protocol | Environment | Justification |
|---------|------|----------|-------------|---------------|
| **API Service** | 8000 | HTTP | All | Standard FastAPI port, consistent across environments |
| **Worker Service** | N/A | N/A | All | Background worker, no port needed |
| **Database** | 5432 | PostgreSQL | All | Standard PostgreSQL port |
| **Database Pooler** | 6543 | PostgreSQL | All | Standard Supabase pooler port |

### Environment-Specific Overrides

| Environment | API Port | DB Port | Notes |
|-------------|----------|---------|-------|
| **Development** | 8000 | 54322 | Local development with different DB port |
| **Staging** | 10000 | 5432 | Render platform requirement |
| **Production** | 8000 | 6543 | Production with pooler |

## Configuration Implementation

### 1. Application Configuration

#### main.py
```python
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
```

#### Dockerfile
```dockerfile
# Set up environment variables
ENV PORT=${PORT:-8000}

# Expose port and configure health check
EXPOSE ${PORT:-8000}
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start uvicorn with optimized settings
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --timeout-keep-alive 75 --limit-max-requests 1000"]
```

### 2. Environment Variables

#### .env.development
```bash
API_PORT=8000
DB_PORT=54322
```

#### .env.staging
```bash
API_PORT=8000
PORT=10000
DB_PORT=5432
```

#### .env.production
```bash
API_PORT=8000
PORT=8000
DB_PORT=6543
```

### 3. Render Service Configuration

#### Staging API Service
- **Port**: 10000 (Render requirement)
- **Environment Variable**: `PORT=10000`
- **Health Check**: `/health`

#### Production API Service
- **Port**: 8000 (Standard)
- **Environment Variable**: `PORT=8000`
- **Health Check**: `/health`

## Best Practices

### 1. **Use Environment Variables for Port Configuration**
- ✅ **Implemented**: All services use `PORT` environment variable
- ✅ **Benefit**: Flexible configuration across environments
- ✅ **Compliance**: Follows Twelve-Factor App methodology

### 2. **Standardize Port Assignments Across Environments**
- ✅ **Implemented**: Consistent port 8000 for API services
- ✅ **Exception**: Staging uses port 10000 due to Render platform requirements
- ✅ **Benefit**: Reduces configuration errors and simplifies deployments

### 3. **Implement Centralized Configuration Management**
- ✅ **Implemented**: Port configuration centralized in environment files
- ✅ **Benefit**: Easier management and auditing

### 4. **Avoid Hardcoding Environment Names in Code**
- ✅ **Implemented**: No hardcoded ports in application code
- ✅ **Benefit**: Cleaner code and easier maintenance

### 5. **Secure Port Bindings**
- ✅ **Implemented**: Using standard ports (8000, 10000)
- ✅ **Recommendation**: Implement firewall rules and monitoring
- ✅ **Benefit**: Enhanced security

### 6. **Document and Audit Port Configurations**
- ✅ **Implemented**: Comprehensive documentation
- ✅ **Benefit**: Easier troubleshooting and maintenance

## Validation and Testing

### Port Configuration Validation

1. **Environment Variable Check**
   ```bash
   # Verify PORT variable is set
   echo $PORT
   ```

2. **Application Startup Test**
   ```bash
   # Test application starts on correct port
   python main.py
   ```

3. **Health Check Test**
   ```bash
   # Test health check endpoint
   curl http://localhost:${PORT:-8000}/health
   ```

### Deployment Validation

1. **Staging Environment**
   - Port: 10000
   - Health Check: `/health`
   - Expected: 200 OK

2. **Production Environment**
   - Port: 8000
   - Health Check: `/health`
   - Expected: 200 OK

## Troubleshooting

### Common Issues

1. **Port Mismatch**
   - **Symptom**: Service times out during deployment
   - **Cause**: Application port doesn't match Render configuration
   - **Solution**: Set `PORT` environment variable correctly

2. **Health Check Failure**
   - **Symptom**: Service fails health checks
   - **Cause**: Health check endpoint not accessible
   - **Solution**: Verify health check endpoint and port configuration

3. **Environment Variable Not Set**
   - **Symptom**: Application uses default port instead of configured port
   - **Cause**: `PORT` environment variable not set
   - **Solution**: Set `PORT` environment variable in service configuration

### Debugging Commands

```bash
# Check environment variables
env | grep PORT

# Test port binding
netstat -tlnp | grep :8000

# Test health check
curl -v http://localhost:8000/health
```

## Monitoring and Alerting

### Key Metrics to Monitor
- Port binding success rate
- Health check response time
- Service startup time
- Port conflict detection

### Alerts to Set Up
- Port binding failures
- Health check failures
- Service startup timeouts
- Port configuration mismatches

## Maintenance

### Regular Tasks
1. **Monthly**: Review port assignments and conflicts
2. **Quarterly**: Audit port configuration compliance
3. **Annually**: Review and update port standards

### Change Management
1. **Port Changes**: Must be documented and approved
2. **Environment Updates**: Must follow standard configuration
3. **Service Additions**: Must use standard port assignments

---

**Standard Status**: ✅ **IMPLEMENTED**  
**Compliance**: ✅ **FULLY COMPLIANT**  
**Next Review**: April 21, 2025
