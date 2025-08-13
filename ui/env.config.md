# Environment Variables Configuration

This document outlines the environment variables required for the Next.js frontend application.

## Required Environment Variables

Create a `.env.local` file in the `ui` directory with the following variables:

```bash
# Environment Configuration
NODE_ENV=development

# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=v1

# Application URLs
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_WEB_URL=http://localhost:3000

# Authentication
NEXT_PUBLIC_AUTH_ENABLED=true
NEXT_PUBLIC_SESSION_TIMEOUT=3600000

# Feature Flags
NEXT_PUBLIC_CHAT_ENABLED=true
NEXT_PUBLIC_ANALYTICS_ENABLED=false
NEXT_PUBLIC_MAINTENANCE_MODE=false

# Third-party Services
NEXT_PUBLIC_SENTRY_DSN=
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=
NEXT_PUBLIC_HOTJAR_ID=

# Debug and Development
NEXT_PUBLIC_DEBUG_MODE=false
NEXT_PUBLIC_MOCK_API=false

# Security
NEXT_PUBLIC_CSRF_TOKEN=
NEXT_PUBLIC_ALLOWED_ORIGINS=http://localhost:3000

# Theme and UI
NEXT_PUBLIC_DEFAULT_THEME=light
NEXT_PUBLIC_BRAND_NAME="Medicare Navigator by Insurance Navigator"

# Rate Limiting
NEXT_PUBLIC_RATE_LIMIT_ENABLED=true
NEXT_PUBLIC_MAX_REQUESTS_PER_MINUTE=60

# Cache Configuration
NEXT_PUBLIC_CACHE_TTL=300000
NEXT_PUBLIC_STATIC_CACHE_TTL=86400000
```

## Production Environment Variables (Vercel)

For Vercel deployment, set these environment variables in your Vercel dashboard:

### Required for Production:
- `NEXT_PUBLIC_API_BASE_URL`: Your production API URL
- `NEXT_PUBLIC_APP_URL`: Your production frontend URL
- `NEXT_PUBLIC_WEB_URL`: Your production website URL

### Optional but Recommended:
- `NEXT_PUBLIC_SENTRY_DSN`: For error tracking
- `NEXT_PUBLIC_GOOGLE_ANALYTICS_ID`: For analytics
- `NEXT_PUBLIC_HOTJAR_ID`: For user experience tracking

## Environment Variable Usage

### Public vs Private Variables

- Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser
- Variables without this prefix are server-side only
- Be careful not to expose sensitive data in public variables

### Accessing Environment Variables

```typescript
// In components or client-side code
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

// In API routes or server-side code
const secretKey = process.env.SECRET_KEY;
```

## Development vs Production

- Development: Use `.env.local` file
- Production: Set variables in Vercel dashboard under "Environment Variables"
- Staging: Can use separate environment variable sets in Vercel 