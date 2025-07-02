# Production Deployment Checklist

## Pre-Deployment
- [ ] Review and update environment variables
- [ ] Run local test suite
- [ ] Run security scans
- [ ] Create database backup
- [ ] Notify team of deployment window

## Deployment Steps
1. **Database**
   - [ ] Run schema validation
   - [ ] Apply migrations
   - [ ] Verify table structures
   - [ ] Check RLS policies

2. **Edge Functions**
   - [ ] Deploy updated functions
   - [ ] Verify JWT configuration
   - [ ] Test CORS settings
   - [ ] Check function logs

3. **Backend**
   - [ ] Deploy FastAPI service
   - [ ] Verify API endpoints
   - [ ] Check authentication flows
   - [ ] Test rate limiting

4. **Frontend**
   - [ ] Run build process
   - [ ] Deploy to production
   - [ ] Verify assets loading
   - [ ] Check accessibility

5. **Monitoring**
   - [ ] Set up database monitoring
   - [ ] Configure Edge Function logging
   - [ ] Enable error tracking
   - [ ] Set up alert thresholds

## Post-Deployment
- [ ] Run smoke tests
- [ ] Verify monitoring dashboards
- [ ] Check error logs
- [ ] Test document processing pipeline
- [ ] Monitor system performance

## Rollback Procedure
1. **If database issues:**
   ```bash
   ./scripts/deployment/rollback-production-schema.sh
   ```

2. **If Edge Function issues:**
   ```bash
   supabase functions delete-deployment <function-name>
   supabase functions deploy <function-name> --version <previous-version>
   ```

3. **If frontend issues:**
   ```bash
   vercel rollback
   ```

## Emergency Contacts
- DevOps Lead: [Contact Info]
- Backend Lead: [Contact Info]
- Frontend Lead: [Contact Info]
- Security Team: [Contact Info] 