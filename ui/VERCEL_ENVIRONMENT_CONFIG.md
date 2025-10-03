# Vercel Environment Configuration Guide

This guide explains how to properly configure different environments (development, staging, production) for Vercel deployments using best practices.

## 🎯 **Best Practice: Environment Variables in Project Settings**

**Recommended Approach**: Use a single `vercel.json` file with environment variable substitution and manage environment-specific values through Vercel Project Settings.

## 📁 **File Structure**

```
ui/
├── vercel.json                    # Main configuration (production)
├── vercel.workflow-testing.json   # Workflow testing configuration
└── VERCEL_ENVIRONMENT_CONFIG.md   # This guide
```

## 🔧 **Configuration Strategy**

### **1. Single `vercel.json` + `next.config.ts` for Dynamic Rewrites**

The `vercel.json` handles static configuration, while `next.config.ts` handles dynamic rewrites:

**`vercel.json`** (static configuration):
```json
{
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        {
          "key": "Access-Control-Allow-Origin",
          "value": "*"
        }
      ]
    }
  ]
}
```

**`next.config.ts`** (dynamic rewrites):
```typescript
async rewrites() {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  
  return [
    {
      source: '/api/:path*',
      destination: `${apiBaseUrl}/api/:path*`,
    },
    {
      source: '/auth/:path*',
      destination: `${apiBaseUrl}/auth/:path*`,
    },
  ];
}
```

### **2. Environment Variables in Vercel Dashboard**

Set these variables in **Project Settings > Environment Variables**:

#### **Production Environment**
```
NEXT_PUBLIC_API_BASE_URL=https://your-production-api.onrender.com
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_production_anon_key_here
NEXT_PUBLIC_APP_ENV=production
NODE_ENV=production
```

#### **Staging Environment**
```
NEXT_PUBLIC_API_BASE_URL=https://your-staging-api.onrender.com
NEXT_PUBLIC_SUPABASE_URL=https://your-staging-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_staging_anon_key_here
NEXT_PUBLIC_APP_ENV=staging
NODE_ENV=staging
```

#### **Development Environment**
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_development_anon_key_here
NEXT_PUBLIC_APP_ENV=development
NODE_ENV=development
```

## 🚀 **Deployment Strategies**

### **Option 1: Branch-Based Deployments (Recommended)**

1. **Production**: Deploy from `main` branch
2. **Staging**: Deploy from `staging` branch  
3. **Preview**: Deploy from feature branches

Set environment variables for each branch in Vercel Project Settings.

### **Option 2: Multiple Projects (Advanced)**

For completely different configurations, create separate Vercel projects:

```bash
# Production project
vercel --prod --project insurance-navigator-prod

# Staging project  
vercel --prod --project insurance-navigator-staging
```

### **Option 3: Multiple Config Files (Not Recommended)**

While possible, this is **not recommended** by Vercel:

```bash
# Deploy with specific config
vercel --local-config vercel.staging.json
```

**Why not recommended:**
- Harder to maintain
- Risk of configuration drift
- Not the Vercel best practice

## 🔒 **Security Best Practices**

### **Environment Variable Management**

1. **Never commit sensitive data** to `vercel.json`
2. **Use Vercel Project Settings** for all environment variables
3. **Separate public vs private variables**:
   - `NEXT_PUBLIC_*` = Client-side (browser accessible)
   - `*` = Server-side only

### **Variable Naming Convention**

```
# Environment identification
NEXT_PUBLIC_APP_ENV=production|staging|development
NODE_ENV=production|staging|development

# API Configuration
NEXT_PUBLIC_API_BASE_URL=https://api.example.com
NEXT_PUBLIC_API_VERSION=v1

# Authentication
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Feature Flags
NEXT_PUBLIC_DEBUG_MODE=false
NEXT_PUBLIC_ANALYTICS_ENABLED=true
```

## 🛠️ **Implementation Steps**

### **1. Update Vercel Project Settings**

1. Go to your Vercel project dashboard
2. Navigate to **Settings > Environment Variables**
3. Add variables for each environment (Development, Preview, Production)
4. Set appropriate values for each environment

### **2. Update `vercel.json`**

Remove hardcoded values and use environment variable substitution:

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "$NEXT_PUBLIC_API_BASE_URL/api/$1"
    },
    {
      "source": "/auth/(.*)", 
      "destination": "$NEXT_PUBLIC_API_BASE_URL/auth/$1"
    }
  ]
}
```

### **3. Test Environment Variables**

Add debugging to your application:

```typescript
// In your app code
console.log('Environment:', process.env.NEXT_PUBLIC_APP_ENV);
console.log('API Base URL:', process.env.NEXT_PUBLIC_API_BASE_URL);
```

## 📋 **Environment-Specific Configurations**

### **Production**
- **API**: `https://your-production-api.onrender.com`
- **Supabase**: Production project
- **Debug**: Disabled
- **Analytics**: Enabled

### **Staging**  
- **API**: `https://your-staging-api.onrender.com`
- **Supabase**: Staging project
- **Debug**: Enabled
- **Analytics**: Disabled

### **Development**
- **API**: `http://localhost:8000`
- **Supabase**: Local instance
- **Debug**: Enabled
- **Analytics**: Disabled

## ✅ **Benefits of This Approach**

1. **Security**: Sensitive data not in codebase
2. **Maintainability**: Single configuration file
3. **Flexibility**: Easy to change environment values
4. **Consistency**: Same configuration structure across environments
5. **Vercel Best Practice**: Follows official recommendations

## 🚨 **Common Pitfalls to Avoid**

1. **Don't hardcode URLs** in `vercel.json`
2. **Don't use multiple config files** unless absolutely necessary
3. **Don't commit environment variables** to version control
4. **Don't mix public and private variables** incorrectly
5. **Don't forget to set variables** for all environments

## 📚 **References**

- [Vercel Environment Variables Documentation](https://vercel.com/docs/project-configuration/project-settings)
- [Vercel Configuration Best Practices](https://vercel.com/docs/project-configuration)
- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)
