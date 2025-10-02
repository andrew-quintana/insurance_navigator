# Render Deployment Configurations

This directory contains Render.com deployment configurations for different environments.

## Environment Naming Convention

### ✅ **Proper Naming Convention**
- **Staging**: `insurance-navigator-staging-api.onrender.com`
- **Production**: `insurance-navigator-api.onrender.com`

### ❌ **Legacy Naming (Deprecated)**
- **Workflow Testing**: `insurance-navigator-api-workflow-testing.onrender.com` (temporary testing environment)

## Configuration Files

### `render.staging.yaml`
- **Purpose**: Proper staging environment deployment
- **URL**: `***REMOVED***`
- **Branch**: `staging`
- **Environment**: `staging`

### `render.yaml`
- **Purpose**: Production environment deployment
- **URL**: `***REMOVED***`
- **Branch**: `main`
- **Environment**: `production`

### `render.workflow-testing.yaml`
- **Purpose**: Legacy workflow testing environment (deprecated)
- **URL**: `https://insurance-navigator-api-workflow-testing.onrender.com`
- **Status**: Should be decommissioned and replaced with proper staging

## Migration Plan

1. **Deploy proper staging environment** using `render.staging.yaml`
2. **Update all configurations** to use `insurance-navigator-staging-api.onrender.com`
3. **Decommission workflow-testing environment** once staging is stable
4. **Update documentation** to reflect proper naming convention

## Webhook URL Configuration

The webhook URLs are configured in the worker environment variables:

```yaml
# Staging
- key: WEBHOOK_BASE_URL
  value: ***REMOVED***

# Production  
- key: WEBHOOK_BASE_URL
  value: ***REMOVED***
```

## Environment Variables

Each environment uses appropriate environment variables:

- **Staging**: Uses staging-specific Supabase project and configuration
- **Production**: Uses production Supabase project and configuration
- **Workflow Testing**: Uses production Supabase (legacy testing setup)

## Deployment Commands

```bash
# Deploy staging
render deploy --config config/render/render.staging.yaml

# Deploy production
render deploy --config config/render/render.yaml
```
