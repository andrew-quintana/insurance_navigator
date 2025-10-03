# Vercel Build Context Guide

## Overview

This guide explains the critical importance of Vercel build context and how to configure it correctly for our insurance navigator project.

## Key Concept: Vercel Root Directory

**CRITICAL INSIGHT**: When Vercel builds your project, it establishes a "root directory" that determines:
- Where `.vercelignore` is applied
- How file paths are resolved
- What files are accessible during build
- Where TypeScript path mapping resolves

## Our Project Structure

```
insurance_navigator/
├── vercel.json (❌ WRONG - causes context mismatch)
├── .vercelignore (❌ WRONG - excludes UI files)
├── ui/ (✅ CORRECT - this should be Vercel root)
│   ├── vercel.json (✅ CORRECT)
│   ├── .vercelignore (✅ CORRECT)
│   ├── components/
│   ├── lib/
│   ├── app/
│   └── package.json
└── backend/ (excluded from frontend deployment)
```

## The Problem We Solved

### Before (Broken Configuration)
```json
// Root vercel.json
{
  "buildCommand": "cd ui && npm run build",
  "installCommand": "cd ui && npm install --legacy-peer-deps"
}
```

**Issues**:
- Vercel builds from root directory
- `.vercelignore` excludes `ui/components/`, `ui/lib/`, etc.
- Commands run in `ui/` but files aren't accessible
- TypeScript `@/*` paths can't resolve

### After (Correct Configuration)
```json
// ui/vercel.json
{
  "buildCommand": "npm run build",
  "installCommand": "npm install --legacy-peer-deps"
}
```

**Benefits**:
- Vercel builds from `ui/` directory
- All UI files are accessible
- TypeScript `@/*` paths resolve correctly
- No context mismatch

## Configuration Files

### ui/vercel.json
```json
{
  "version": 2,
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm install --legacy-peer-deps",
  "framework": "nextjs",
  "regions": ["iad1"],
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://insurance-navigator-staging-api.onrender.com/api/$1"
    }
  ],
  "env": {
    "NEXT_PUBLIC_APP_ENV": "staging"
  },
  "build": {
    "env": {
      "NEXT_PUBLIC_SUPABASE_URL": "https://dfgzeastcxnoqshgyotp.supabase.co",
      "NEXT_PUBLIC_SUPABASE_ANON_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "NEXT_PUBLIC_API_BASE_URL": "https://insurance-navigator-staging-api.onrender.com",
      "NEXT_PUBLIC_API_URL": "https://insurance-navigator-staging-api.onrender.com",
      "NODE_ENV": "staging"
    }
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        },
        {
          "key": "Referrer-Policy",
          "value": "strict-origin-when-cross-origin"
        },
        {
          "key": "Permissions-Policy",
          "value": "camera=(), microphone=(), geolocation=()"
        }
      ]
    }
  ],
  "trailingSlash": false,
  "cleanUrls": true
}
```

### ui/.vercelignore
```
# UI-specific .vercelignore
# Since we're building from ui/ directory, we only need to exclude UI-specific files

# Exclude test and development files
coverage/
playwright-report/
__tests__/
e2e/
docs/

# Exclude build artifacts
.next/
tsconfig.tsbuildinfo

# Exclude development configs (keep production ones)
*.local.*
.env.local
```

## TypeScript Path Mapping

```json
// ui/tsconfig.json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"]  // Resolves relative to ui/ directory
    }
  }
}
```

**Important**: The `@/*` path mapping resolves relative to the `ui/` directory, which is why Vercel must build from `ui/` context.

## Common Pitfalls

### 1. Root vercel.json with cd commands
```json
// ❌ WRONG
{
  "buildCommand": "cd ui && npm run build"
}
```
**Problem**: Build context mismatch

### 2. Root .vercelignore excluding UI files
```
# ❌ WRONG
ui/components/
ui/lib/
```
**Problem**: Files needed by build are excluded

### 3. Missing ui/.vercelignore
**Problem**: No control over what gets excluded from UI build

## Best Practices

1. **Single Build Context**: Vercel should build from the same directory as your application
2. **Minimal Exclusions**: Only exclude what's absolutely necessary
3. **Consistent Paths**: Ensure TypeScript paths match build context
4. **Test Locally**: Always test `npm run build` in the same directory Vercel will use
5. **Document Context**: Clearly document which directory is the Vercel root

## Troubleshooting

### Module Resolution Errors
```
Module not found: Can't resolve '@/components/ui/button'
```
**Solution**: Ensure Vercel builds from `ui/` directory where `@/*` paths resolve

### Missing Dependencies
```
Error: Cannot find module 'tailwindcss'
```
**Solution**: Ensure `ui/node_modules/` is accessible (not excluded by `.vercelignore`)

### Build Context Mismatch
**Symptoms**: Works locally but fails on Vercel
**Solution**: Verify Vercel builds from the same directory as local testing

## Migration Checklist

When moving Vercel configuration to `ui/` directory:

- [ ] Move `vercel.json` from root to `ui/`
- [ ] Remove `cd ui` from build commands
- [ ] Update `outputDirectory` to `.next` (not `ui/.next`)
- [ ] Create `ui/.vercelignore` with minimal exclusions
- [ ] Remove root `vercel.json` to avoid conflicts
- [ ] Test local build: `cd ui && npm run build`
- [ ] Deploy and verify

## References

- [Vercel Build Configuration](https://vercel.com/docs/build-step)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [TypeScript Path Mapping](https://www.typescriptlang.org/docs/handbook/module-resolution.html#path-mapping)

---

**Key Takeaway**: Vercel's root directory determines build context. For our project, the UI subdirectory must be the Vercel root to ensure proper module resolution and file access.
