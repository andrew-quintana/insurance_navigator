# Vercel Deployment Guide

This guide walks you through deploying the Medicare Navigator frontend to Vercel.

## Prerequisites

- [Vercel CLI](https://vercel.com/docs/cli) installed globally
- Vercel account with GitHub integration
- Node.js 18+ installed locally

## Quick Start

### 1. Install Vercel CLI

```bash
npm i -g vercel
```

### 2. Login to Vercel

```bash
vercel login
```

### 3. Deploy from UI Directory

```bash
cd ui
vercel
```

Follow the prompts and deploy!

## Detailed Deployment Steps

### Step 1: Environment Variables Setup

1. Create a `.env.local` file in the `ui` directory (see `env.config.md` for variables)
2. Set up production environment variables in Vercel dashboard:

**Required Variables:**
```
NEXT_PUBLIC_API_BASE_URL=https://your-api-domain.com
NEXT_PUBLIC_APP_URL=https://your-frontend-domain.vercel.app
NEXT_PUBLIC_WEB_URL=https://your-frontend-domain.vercel.app
```

**Optional Variables:**
```
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
NEXT_PUBLIC_HOTJAR_ID=1234567
NEXT_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/xxx
NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION=xxx
```

### Step 2: Vercel Project Configuration

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your GitHub repository
4. Select the `ui` directory as the root directory
5. Vercel will automatically detect Next.js

### Step 3: Build Settings

Vercel should automatically configure these, but verify:

- **Framework Preset:** Next.js
- **Root Directory:** `ui`
- **Build Command:** `npm run build`
- **Output Directory:** `.next`
- **Install Command:** `npm ci`
- **Node.js Version:** 18.x

### Step 4: Domain Setup

1. In Vercel dashboard, go to your project
2. Navigate to "Settings" → "Domains"
3. Add your custom domain if needed
4. Update `NEXT_PUBLIC_APP_URL` to match your domain

### Step 5: Environment Variables

1. Go to "Settings" → "Environment Variables"
2. Add all required variables for Production, Preview, and Development
3. Make sure `NEXT_PUBLIC_API_BASE_URL` points to your production API

## Build Optimization

### Bundle Analysis

Run locally to analyze bundle size:

```bash
npm run build:analyze
```

### Performance Monitoring

1. Enable Vercel Analytics in your dashboard
2. Set up Core Web Vitals monitoring
3. Configure error tracking with Sentry (optional)

## Deployment Strategies

### Automatic Deployments

- **Production:** Deploy from `main` branch automatically
- **Preview:** Deploy from feature branches for testing
- **Development:** Use `vercel dev` for local development with Vercel functions

### Manual Deployments

```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod

# Deploy specific branch
vercel --prod --confirm
```

## Custom Domains

### Setup

1. Add domain in Vercel dashboard
2. Configure DNS records:
   - **A Record:** Point to Vercel's IP
   - **CNAME:** Point to `cname.vercel-dns.com`

### SSL

Vercel automatically provisions SSL certificates for all domains.

## Environment Configuration

### Development
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### Production
```bash
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
NEXT_PUBLIC_APP_URL=https://yourdomain.com
```

## Monitoring and Analytics

### Vercel Analytics

1. Enable in dashboard → Analytics
2. View performance metrics
3. Monitor Core Web Vitals

### Error Tracking

Configure Sentry in `next.config.ts`:

```typescript
// Add to next.config.ts
const { withSentryConfig } = require('@sentry/nextjs');

module.exports = withSentryConfig(nextConfig, {
  silent: true,
  org: 'your-org',
  project: 'your-project',
});
```

## Security

### Headers

Security headers are configured in `next.config.ts` and `vercel.json`:

- Content Security Policy
- X-Frame-Options
- X-Content-Type-Options
- Strict-Transport-Security

### Environment Variables

- Use `NEXT_PUBLIC_` prefix only for client-side variables
- Keep sensitive data in server-only variables
- Never commit `.env.local` files

## Troubleshooting

### Common Issues

#### Build Failures

1. **TypeScript Errors:**
   ```bash
   npm run type-check
   ```

2. **Lint Errors:**
   ```bash
   npm run lint:check
   ```

3. **Missing Dependencies:**
   ```bash
   npm ci
   ```

#### Runtime Errors

1. **API Connection Issues:**
   - Verify `NEXT_PUBLIC_API_BASE_URL`
   - Check CORS settings on API
   - Ensure API is deployed and accessible

2. **Environment Variables:**
   - Confirm all required variables are set
   - Verify public variables have `NEXT_PUBLIC_` prefix

#### Performance Issues

1. **Large Bundle Size:**
   ```bash
   npm run build:analyze
   ```

2. **Slow Loading:**
   - Enable Vercel Analytics
   - Check Core Web Vitals
   - Optimize images and fonts

### Debugging

1. **Build Logs:**
   - Check Vercel deployment logs
   - Review function logs for errors

2. **Local Development:**
   ```bash
   vercel dev
   ```

3. **Production Debugging:**
   ```bash
   vercel logs [deployment-url]
   ```

## Rollback

### Quick Rollback

1. Go to Vercel dashboard
2. Find previous successful deployment
3. Click "Promote to Production"

### Git Rollback

```bash
git revert <commit-hash>
git push origin main
```

## Performance Optimization

### Caching

- Static assets: Cached automatically by Vercel
- API responses: Configure in `next.config.ts`
- Images: Optimized by Next.js Image component

### CDN

Vercel automatically distributes your app globally via CDN.

### Monitoring

Set up monitoring for:
- Response times
- Error rates
- User engagement
- Core Web Vitals

## Support

### Vercel Support

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Community](https://github.com/vercel/vercel/discussions)
- [Next.js Documentation](https://nextjs.org/docs)

### Project Support

Check the project's GitHub issues or contact the development team. 