# Environment Management Guide

**Document:** Environment Management Procedures  
**Version:** 1.0  
**Last Updated:** 2025-01-18  
**Status:** Production Ready

## Overview

This guide provides comprehensive procedures for managing environment configurations across development and production environments for the Insurance Navigator application. It covers environment setup, validation, synchronization, and security best practices.

## Table of Contents

1. [Environment Architecture](#environment-architecture)
2. [Environment Setup](#environment-setup)
3. [Configuration Management](#configuration-management)
4. [Environment Validation](#environment-validation)
5. [Environment Synchronization](#environment-synchronization)
6. [Security Guidelines](#security-guidelines)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Environment Architecture

### Environment Types

The Insurance Navigator supports two primary environments:

- **Development**: Local development with relaxed security and enhanced debugging
- **Production**: Live environment with strict security and performance optimization

### Configuration Structure

```
config/environments/
├── types.ts              # TypeScript interfaces and types
├── index.ts              # Environment detection and loading logic
├── development.ts        # Development environment configuration
├── production.ts         # Production environment configuration
├── render.env           # Render platform environment variables
├── vercel.env           # Vercel platform environment variables
└── supabase.env         # Supabase platform environment variables
```

### Environment Variables

#### Required Variables (All Environments)

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | `https://project.supabase.co` |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:port/db` |

#### Frontend Variables (Vercel)

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_APP_URL` | Frontend application URL | `https://app.vercel.app` |
| `NEXT_PUBLIC_API_BASE_URL` | Backend API URL | `https://api.onrender.com` |

#### Backend Variables (Render)

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-proj-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |
| `LLAMAPARSE_API_KEY` | LlamaCloud API key | `llx-...` |
| `RESEND_API_KEY` | Resend email API key | `re_...` |
| `JWT_SECRET_KEY` | JWT signing secret | `secure-random-string` |
| `ENCRYPTION_KEY` | Data encryption key | `secure-random-string` |

## Environment Setup

### Prerequisites

- Node.js 18+ installed
- Access to Supabase, Render, and Vercel platforms
- Required API keys and credentials

### Development Environment Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd insurance-navigator
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Create Environment File**
   ```bash
   cp config/env.development.example .env.development
   ```

4. **Configure Environment Variables**
   Edit `.env.development` with your development values:
   ```bash
   # Database
   DATABASE_URL=postgresql://postgres:password@localhost:5432/insurance_navigator_dev
   
   # Supabase
   SUPABASE_URL=https://your-dev-project.supabase.co
   SUPABASE_ANON_KEY=your_dev_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_dev_service_role_key
   
   # API Keys
   OPENAI_API_KEY=sk-dev-...
   ANTHROPIC_API_KEY=sk-ant-dev-...
   LLAMAPARSE_API_KEY=llx-dev-...
   RESEND_API_KEY=re_dev-...
   ```

5. **Validate Configuration**
   ```bash
   npm run validate:environment -- --environment development
   ```

### Production Environment Setup

1. **Create Production Environment File**
   ```bash
   cp config/env.production.example .env.production
   ```

2. **Configure Production Variables**
   Edit `.env.production` with production values:
   ```bash
   # Database
   DATABASE_URL=postgresql://postgres:password@prod-db.example.com:5432/insurance_navigator_prod
   
   # Supabase
   SUPABASE_URL=https://your-prod-project.supabase.co
   SUPABASE_ANON_KEY=your_prod_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_prod_service_role_key
   
   # API Keys (Production)
   OPENAI_API_KEY=sk-prod-...
   ANTHROPIC_API_KEY=sk-ant-prod-...
   LLAMAPARSE_API_KEY=llx-prod-...
   RESEND_API_KEY=re_prod-...
   
   # Security
   JWT_SECRET_KEY=your-secure-jwt-secret
   ENCRYPTION_KEY=your-secure-encryption-key
   ```

3. **Validate Production Configuration**
   ```bash
   npm run validate:environment -- --environment production --strict
   ```

## Configuration Management

### Environment Detection

The application automatically detects the environment using the following priority:

1. `ENV_LEVEL` environment variable
2. `NODE_ENV` environment variable
3. Default to `development`

### Configuration Loading

```typescript
import { getEnvironmentConfig } from './config/environments';

const config = getEnvironmentConfig();
console.log(`Running in ${config.environment} mode`);
```

### Environment-Specific Settings

#### Development Configuration

- **Security**: Relaxed security settings for easier development
- **Debugging**: Enhanced logging and debug information
- **CORS**: Permissive CORS settings for local development
- **Rate Limiting**: Disabled for development convenience

#### Production Configuration

- **Security**: Strict security settings and validation
- **Performance**: Optimized for production workloads
- **CORS**: Restricted to specific trusted domains
- **Rate Limiting**: Enabled to prevent abuse

## Environment Validation

### Validation Script

The environment validation script checks configuration integrity:

```bash
# Basic validation
npm run validate:environment

# Environment-specific validation
npm run validate:environment -- --environment production

# Strict validation (fails on warnings)
npm run validate:environment -- --strict

# Verbose output
npm run validate:environment -- --verbose
```

### Validation Checks

The validation script performs the following checks:

1. **Required Variables**: Ensures all required environment variables are set
2. **Format Validation**: Validates API key formats and URL structures
3. **Security Validation**: Checks for weak or development secrets in production
4. **Configuration Integrity**: Validates configuration file structure
5. **Database Connectivity**: Tests database connection configuration
6. **External API Validation**: Validates external API key formats

### Validation Results

```bash
🔍 Validating production environment configuration...

📋 Validation Results:

✅ Environment configuration is valid!

⚠️  Warnings:
  • Optional environment variable not set: ANALYTICS_ID

📊 Summary: 0 errors, 1 warnings
```

## Environment Synchronization

### Synchronization Script

The synchronization script helps maintain consistency across platforms:

```bash
# Sync all platforms
npm run sync:environments

# Sync specific platform
npm run sync:environments -- --target render

# Sync from specific environment
npm run sync:environments -- --source production --target vercel

# Dry run (show what would be done)
npm run sync:environments -- --dry-run
```

### Platform-Specific Configuration

#### Render (Backend API)

Variables synced to Render:
- Database configuration
- API keys and secrets
- Service configuration
- Security settings

#### Vercel (Frontend)

Variables synced to Vercel:
- Frontend URLs
- API endpoints
- Public configuration
- Analytics settings

#### Supabase (Database)

Variables synced to Supabase:
- Database connection strings
- Authentication keys
- Project configuration

## Security Guidelines

### Security Audit

Perform regular security audits:

```bash
# Basic security audit
npm run security:audit

# Production security audit
npm run security:audit -- --environment production --strict

# Generate security report
npm run security:audit -- --output security-report.json
```

### Security Best Practices

#### Secret Management

1. **Never commit secrets to version control**
2. **Use strong, randomly generated secrets**
3. **Rotate secrets regularly**
4. **Use different secrets for each environment**
5. **Store secrets in secure environment variable systems**

#### Environment Isolation

1. **Maintain strict separation between environments**
2. **Use different API keys for development and production**
3. **Implement proper access controls**
4. **Monitor environment access and changes**

#### Configuration Security

1. **Validate all configuration at startup**
2. **Use secure defaults for production**
3. **Implement proper error handling**
4. **Log security events appropriately**

### Security Checklist

- [ ] All secrets are stored in environment variables
- [ ] No hardcoded secrets in code or configuration files
- [ ] Different secrets used for each environment
- [ ] Strong, randomly generated secrets (32+ characters)
- [ ] Security bypass disabled in production
- [ ] CORS properly configured for production
- [ ] Debug mode disabled in production
- [ ] File permissions properly set for sensitive files
- [ ] Regular security audits performed
- [ ] Security monitoring and alerting configured

## Troubleshooting

### Common Issues

#### Environment Detection Issues

**Problem**: Application not detecting correct environment

**Solution**:
```bash
# Check current environment
echo $NODE_ENV
echo $ENV_LEVEL

# Set environment explicitly
export NODE_ENV=production
export ENV_LEVEL=production
```

#### Missing Environment Variables

**Problem**: Required environment variables not set

**Solution**:
```bash
# Validate environment
npm run validate:environment

# Check specific variable
echo $DATABASE_URL
```

#### Configuration Validation Failures

**Problem**: Configuration validation failing

**Solution**:
```bash
# Run validation with verbose output
npm run validate:environment -- --verbose

# Check for specific errors
npm run validate:environment -- --environment production --strict
```

#### Synchronization Issues

**Problem**: Environment synchronization failing

**Solution**:
```bash
# Check synchronization with dry run
npm run sync:environments -- --dry-run --verbose

# Verify source environment file exists
ls -la .env.development .env.production
```

### Debug Mode

Enable debug mode for detailed troubleshooting:

```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run validation with debug output
npm run validate:environment -- --verbose
```

### Log Analysis

Check application logs for environment-related issues:

```bash
# Check application logs
tail -f logs/application.log | grep -i environment

# Check validation logs
npm run validate:environment -- --verbose 2>&1 | tee validation.log
```

## Best Practices

### Development Workflow

1. **Always validate environment before starting development**
2. **Use development-specific API keys and services**
3. **Test configuration changes locally before committing**
4. **Document any new environment variables**

### Production Deployment

1. **Validate production configuration before deployment**
2. **Use production-specific secrets and services**
3. **Perform security audit before deployment**
4. **Monitor environment health after deployment**

### Maintenance

1. **Regular security audits (monthly)**
2. **Rotate secrets quarterly**
3. **Update documentation when adding new variables**
4. **Monitor for configuration drift**

### Team Collaboration

1. **Share environment setup procedures with team**
2. **Use consistent naming conventions**
3. **Document environment-specific requirements**
4. **Maintain up-to-date environment examples**

## Support

### Getting Help

- **Documentation**: Check this guide and related documentation
- **Validation**: Use validation scripts to diagnose issues
- **Logs**: Check application and validation logs
- **Team**: Contact development team for complex issues

### Reporting Issues

When reporting environment issues, include:

1. **Environment type** (development/production)
2. **Validation output** (if applicable)
3. **Error messages** (full text)
4. **Configuration** (sanitized)
5. **Steps to reproduce**

### Updates

This guide is updated when:
- New environment variables are added
- Security requirements change
- Platform configurations change
- New validation rules are implemented

---

**Last Updated**: 2025-01-18  
**Next Review**: 2025-02-18  
**Maintainer**: Development Team
