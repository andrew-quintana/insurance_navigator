# Pre-Deployment Checklist

Use this checklist before deploying to Vercel to ensure everything is properly configured.

## ✅ Code Quality

- [ ] All TypeScript errors resolved
  ```bash
  cd ui && npm run type-check
  ```

- [ ] ESLint checks pass
  ```bash
  cd ui && npm run lint:check
  ```

- [ ] Build completes successfully
  ```bash
  cd ui && npm run build
  ```

- [ ] No console errors in browser (dev mode)
- [ ] All components render correctly
- [ ] Error boundaries are working

## ✅ Environment Variables

- [ ] `.env.local` file created (for local development)
- [ ] All required environment variables documented in `env.config.md`
- [ ] Environment variables follow `NEXT_PUBLIC_` prefix convention for client-side variables
- [ ] No sensitive data in public environment variables
- [ ] API base URL configured correctly for production

### Required Environment Variables:
- [ ] `NEXT_PUBLIC_API_BASE_URL`
- [ ] `NEXT_PUBLIC_APP_URL`
- [ ] `NEXT_PUBLIC_WEB_URL`

### Optional but Recommended:
- [ ] `NEXT_PUBLIC_GOOGLE_ANALYTICS_ID`
- [ ] `NEXT_PUBLIC_HOTJAR_ID`
- [ ] `NEXT_PUBLIC_SENTRY_DSN`
- [ ] `NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION`

## ✅ Configuration Files

- [ ] `vercel.json` properly configured
- [ ] `next.config.ts` optimized for production
- [ ] `package.json` scripts updated
- [ ] Security headers configured
- [ ] Image optimization settings configured
- [ ] Proper redirects and rewrites set up

## ✅ Performance

- [ ] Bundle size analysis completed
  ```bash
  cd ui && npm run build:analyze
  ```

- [ ] Images optimized and using Next.js Image component
- [ ] Fonts optimized (using Google Fonts)
- [ ] Unnecessary dependencies removed
- [ ] Code splitting implemented where needed
- [ ] Lazy loading implemented for heavy components

## ✅ Security

- [ ] Security headers configured in `next.config.ts`
- [ ] Content Security Policy implemented
- [ ] No hardcoded secrets in code
- [ ] HTTPS enforced
- [ ] Proper CORS configuration
- [ ] Input validation implemented
- [ ] XSS protection enabled

## ✅ SEO & Meta Tags

- [ ] Proper meta tags in root layout
- [ ] Open Graph tags configured
- [ ] Twitter Card meta tags added
- [ ] Favicon and app icons added
- [ ] Sitemap.xml generated (if needed)
- [ ] Robots.txt configured
- [ ] Structured data markup (if applicable)

## ✅ Error Handling

- [ ] Error boundaries implemented
- [ ] 404 page customized
- [ ] 500 page customized
- [ ] Loading states implemented
- [ ] API error handling implemented
- [ ] Retry logic for failed requests
- [ ] Proper error logging configured

## ✅ API Integration

- [ ] API client properly configured
- [ ] Environment-specific API URLs
- [ ] Authentication handling implemented
- [ ] Request timeout configured
- [ ] Retry logic implemented
- [ ] Error handling for API failures
- [ ] Loading states for API calls

## ✅ UI/UX

- [ ] All pages responsive on mobile devices
- [ ] Dark/light theme working correctly
- [ ] Loading states implemented
- [ ] Accessibility features implemented
- [ ] Form validation working
- [ ] Navigation functioning correctly
- [ ] No broken links

## ✅ Testing

- [ ] Manual testing on different browsers
- [ ] Mobile responsiveness tested
- [ ] Form submissions tested
- [ ] Navigation flows tested
- [ ] Error scenarios tested
- [ ] API integration tested
- [ ] Theme switching tested

## ✅ Analytics & Monitoring

- [ ] Google Analytics configured (if required)
- [ ] Error tracking configured (Sentry, etc.)
- [ ] Performance monitoring set up
- [ ] User behavior tracking configured (Hotjar, etc.)

## ✅ Documentation

- [ ] Environment variables documented
- [ ] Deployment guide created
- [ ] README updated with deployment instructions
- [ ] API integration documented
- [ ] Component documentation updated

## ✅ Dependencies

- [ ] All dependencies up to date
- [ ] No known security vulnerabilities
  ```bash
  cd ui && npm audit
  ```

- [ ] Unused dependencies removed
- [ ] Package-lock.json committed

## ✅ Vercel Specific

- [ ] Project root directory set to `ui`
- [ ] Build command configured: `npm run build`
- [ ] Output directory set to `.next`
- [ ] Node.js version specified (18.x)
- [ ] Function timeout configured (if needed)
- [ ] Custom domain configured (if applicable)

## ✅ Pre-Deployment Testing

- [ ] Local build and serve test
  ```bash
  cd ui && npm run build && npm run start
  ```

- [ ] Test with production environment variables
- [ ] Test API connections with production endpoints
- [ ] Performance test with production build
- [ ] Cross-browser testing completed

## ✅ Backup & Recovery

- [ ] Current working version tagged in git
- [ ] Database backup completed (if applicable)
- [ ] Rollback plan documented
- [ ] Recovery procedures documented

## ✅ Post-Deployment

After successful deployment, verify:

- [ ] All pages load correctly
- [ ] API connections working
- [ ] Analytics tracking active
- [ ] Error monitoring functional
- [ ] Performance metrics within acceptable ranges
- [ ] SSL certificate active
- [ ] Custom domain working (if applicable)

## Deployment Commands

Once all items are checked:

```bash
# Navigate to UI directory
cd ui

# Install Vercel CLI (if not already installed)
npm i -g vercel

# Login to Vercel
vercel login

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

## Emergency Rollback

If something goes wrong:

1. Go to Vercel Dashboard
2. Find the last working deployment
3. Click "Promote to Production"

Or use Git:

```bash
git revert <commit-hash>
git push origin main
```

## Support

If you encounter issues:

1. Check Vercel deployment logs
2. Review this checklist
3. Check the troubleshooting section in `DEPLOYMENT.md`
4. Contact the development team 