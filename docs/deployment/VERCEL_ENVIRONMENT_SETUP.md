# Vercel Environment Variables Setup Guide

This guide explains how to configure environment variables in Vercel to enable flexible deployment between staging and production environments.

## 🎯 Overview

The `vercel.json` configuration now uses environment variables instead of hardcoded values, allowing you to:

- **Production (main branch)**: Deploy to production with production API
- **Preview (staging branch)**: Deploy to preview with staging API
- **Flexible configuration**: Change environments without code changes

## 🔧 Required Environment Variables

You need to set these environment variables in your Vercel project:

### Core Environment Variables

| Variable | Production Value | Staging Value | Description |
|----------|------------------|---------------|-------------|
| `NEXT_PUBLIC_APP_ENV` | `production` | `staging` | Application environment |
| `NEXT_PUBLIC_API_BASE_URL` | `https://insurance-navigator-api.onrender.com` | `https://insurance-navigator-staging-api.onrender.com` | Backend API URL |
| `NEXT_PUBLIC_API_URL` | `https://insurance-navigator-api.onrender.com` | `https://insurance-navigator-staging-api.onrender.com` | Alternative API URL |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://your-staging-project.supabase.co` | `https://your-staging-project.supabase.co` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` | Supabase anonymous key |
| `NODE_ENV` | `production` | `staging` | Node.js environment |

## 📋 How to Set Environment Variables in Vercel

### Method 1: Vercel Dashboard (Recommended)

1. **Go to your Vercel project dashboard**
2. **Navigate to Settings → Environment Variables**
3. **Add each variable** with the appropriate values:

#### For Production Environment:
```
NEXT_PUBLIC_APP_ENV = production
NEXT_PUBLIC_API_BASE_URL = https://insurance-navigator-api.onrender.com
NEXT_PUBLIC_API_URL = https://insurance-navigator-api.onrender.com
NEXT_PUBLIC_SUPABASE_URL = https://your-staging-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0ODMsImV4cCI6MjA2NzI1NjQ4M30.wV0kgqo20D1EghH47bO-4MoXpksiyQ_bvANaZlzScyM
NODE_ENV = production
```

#### For Preview Environment:
```
NEXT_PUBLIC_APP_ENV = staging
NEXT_PUBLIC_API_BASE_URL = https://insurance-navigator-staging-api.onrender.com
NEXT_PUBLIC_API_URL = https://insurance-navigator-staging-api.onrender.com
NEXT_PUBLIC_SUPABASE_URL = https://your-staging-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0ODMsImV4cCI6MjA2NzI1NjQ4M30.wV0kgqo20D1EghH47bO-4MoXpksiyQ_bvANaZlzScyM
NODE_ENV = staging
```

4. **Set Environment Scope**:
   - For Production variables: Select "Production" only
   - For Preview variables: Select "Preview" only
   - For Development variables: Select "Development" only

### Method 2: Vercel CLI

```bash
# Install Vercel CLI if not already installed
npm i -g vercel

# Login to Vercel
vercel login

# Set environment variables
vercel env add NEXT_PUBLIC_APP_ENV
vercel env add NEXT_PUBLIC_API_BASE_URL
vercel env add NEXT_PUBLIC_API_URL
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY
vercel env add NODE_ENV

# Pull environment variables to local development
vercel env pull .env.local
```

## 🚀 Deployment Behavior

### Production Deployment (main branch)
- Uses `NEXT_PUBLIC_APP_ENV=production`
- Points to production API: `https://insurance-navigator-api.onrender.com`
- Sets `NODE_ENV=production`

### Preview Deployment (staging branch)
- Uses `NEXT_PUBLIC_APP_ENV=staging`
- Points to staging API: `https://insurance-navigator-staging-api.onrender.com`
- Sets `NODE_ENV=staging`

### Development Deployment (any other branch)
- Uses development environment variables
- Can point to localhost or development API

## 🔍 Verification

After setting up environment variables:

1. **Check Vercel Dashboard**: Go to your project → Settings → Environment Variables
2. **Verify Deployment**: Check the build logs to ensure variables are loaded
3. **Test Authentication**: Try signing in to verify the correct API is being used
4. **Check Network Tab**: Verify API calls are going to the correct endpoint

## 🛠️ Troubleshooting

### Common Issues

1. **Environment variables not loading**:
   - Ensure variables are set for the correct environment (Production/Preview/Development)
   - Check that variable names match exactly (case-sensitive)
   - Redeploy after adding new variables

2. **Wrong API endpoint**:
   - Verify `NEXT_PUBLIC_API_BASE_URL` is set correctly
   - Check that the environment scope matches your deployment branch

3. **Authentication issues**:
   - Ensure Supabase URL and keys are correct
   - Verify the API backend is running and accessible

### Debug Commands

```bash
# Check current environment variables in Vercel
vercel env ls

# Pull environment variables for local testing
vercel env pull .env.local

# Check deployment logs
vercel logs [deployment-url]
```

## 📝 Notes

- Environment variables prefixed with `NEXT_PUBLIC_` are available in the browser
- Variables without this prefix are only available during build time
- Changes to environment variables require a new deployment to take effect
- Always test in preview environment before promoting to production

## 🔗 Related Documentation

- [Vercel Environment Variables Documentation](https://vercel.com/docs/concepts/projects/environment-variables)
- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)
- [Project Environment Configuration Guide](../config/ENVIRONMENT_CONFIGURATION_GUIDE.md)
