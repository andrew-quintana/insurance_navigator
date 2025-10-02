# Production Database Migration Deployment Checklist

## 🎯 **Deployment Overview**

**Initiative**: Production Database Migration Cleanup  
**Target**: Remove unused tables and fix auth triggers  
**Risk Level**: LOW (comprehensive staging testing completed)  
**Estimated Duration**: 30-60 minutes  

## ✅ **Pre-Deployment Checklist**

### **1. Environment Preparation**
- [ ] **Production Database Backup**
  - [ ] Create full PostgreSQL backup
  - [ ] Verify backup integrity
  - [ ] Store backup in secure location
  - [ ] Document backup location and timestamp

- [ ] **Environment Variables Verification**
  - [ ] Confirm `DATABASE_URL` is correct
  - [ ] Verify `SUPABASE_URL` and keys
  - [ ] Check `NEXT_PUBLIC_API_BASE_URL`
  - [ ] Validate all required environment variables

- [ ] **Application Status Check**
  - [ ] Verify production application is healthy
  - [ ] Check current user count in `auth.users`
  - [ ] Confirm no active upload jobs
  - [ ] Review recent error logs

### **2. Migration Preparation**
- [ ] **Migration Scripts Ready**
  - [ ] `scripts/apply_staging_migrations_safe.py` tested
  - [ ] `scripts/fix_auth_trigger.py` available
  - [ ] `scripts/test_staging_environment.py` ready for verification
  - [ ] All scripts have proper permissions

- [ ] **Rollback Plan Prepared**
  - [ ] Database restore procedure documented
  - [ ] Supabase CLI rollback commands ready
  - [ ] Migration repair commands prepared
  - [ ] Emergency contact list updated

### **3. Team Coordination**
- [ ] **Stakeholder Notification**
  - [ ] Notify development team
  - [ ] Inform operations team
  - [ ] Alert monitoring team
  - [ ] Update status page if applicable

- [ ] **Maintenance Window**
  - [ ] Schedule during low-traffic period
  - [ ] Confirm team availability
  - [ ] Set up monitoring alerts
  - [ ] Prepare communication channels

## 🚀 **Deployment Execution**

### **Phase 1: Pre-Deployment Verification**
- [ ] **Final Health Check**
  ```bash
  # Check production API health
  curl -s https://insurance-navigator-api.onrender.com/health | jq .
  
  # Verify database connectivity
  python scripts/check_staging_schema.py  # (with production env)
  ```

- [ ] **User Count Verification**
  ```sql
  -- Check current user count
  SELECT COUNT(*) FROM auth.users;
  
  -- Verify no data in public.users
  SELECT COUNT(*) FROM public.users;  -- Should return error or 0
  ```

### **Phase 2: Migration Execution**
- [ ] **Apply Safe Migration**
  ```bash
  # Option 1: Safe migration script
  python scripts/apply_staging_migrations_safe.py
  
  # Option 2: Supabase CLI
  supabase db push
  ```

- [ ] **Monitor Migration Progress**
  - [ ] Watch for error messages
  - [ ] Monitor database connections
  - [ ] Check application logs
  - [ ] Verify migration completion

### **Phase 3: Post-Deployment Verification**
- [ ] **Database Schema Verification**
  ```sql
  -- Verify public.users is removed
  SELECT * FROM public.users;  -- Should return error
  
  -- Verify auth.users is intact
  SELECT COUNT(*) FROM auth.users;
  
  -- Check storage buckets
  SELECT id, name FROM storage.buckets;
  ```

- [ ] **Application Functionality Test**
  ```bash
  # Test API health
  curl -s https://insurance-navigator-api.onrender.com/health | jq .
  
  # Test authentication (if possible)
  # Test document upload endpoint
  # Verify storage access
  ```

## 🔍 **Verification Checklist**

### **Critical Functionality**
- [ ] **Authentication System**
  - [ ] User registration working
  - [ ] User login working
  - [ ] JWT token generation working
  - [ ] Protected endpoints accessible

- [ ] **Document Processing**
  - [ ] Upload pipeline operational
  - [ ] Document storage working
  - [ ] Processing jobs can be created
  - [ ] Storage buckets accessible

- [ ] **Database Operations**
  - [ ] All schemas accessible
  - [ ] RLS policies active
  - [ ] No orphaned data
  - [ ] Performance acceptable

### **Monitoring and Alerts**
- [ ] **Error Monitoring**
  - [ ] No new error patterns
  - [ ] Authentication errors resolved
  - [ ] Database connection errors absent
  - [ ] Application logs clean

- [ ] **Performance Monitoring**
  - [ ] Response times normal
  - [ ] Database query performance stable
  - [ ] Memory usage acceptable
  - [ ] CPU usage normal

## 🛡️ **Rollback Procedures**

### **If Issues Detected**
- [ ] **Immediate Actions**
  - [ ] Stop migration if in progress
  - [ ] Assess impact severity
  - [ ] Notify team of issues
  - [ ] Begin rollback procedures

- [ ] **Rollback Execution**
  ```bash
  # Restore database from backup
  # Or use Supabase CLI rollback
  supabase migration repair --status reverted <migration_id>
  ```

- [ ] **Post-Rollback Verification**
  - [ ] Verify application functionality
  - [ ] Check user authentication
  - [ ] Confirm data integrity
  - [ ] Document issues encountered

## 📊 **Success Criteria**

### **Deployment Success**
- [ ] All migrations applied successfully
- [ ] No application errors
- [ ] User authentication working
- [ ] Document processing operational
- [ ] Performance metrics normal

### **Post-Deployment Success**
- [ ] 24-hour monitoring period completed
- [ ] No critical issues reported
- [ ] User feedback positive
- [ ] System performance improved
- [ ] Documentation updated

## 📝 **Documentation Updates**

### **Post-Deployment Tasks**
- [ ] **Update Documentation**
  - [ ] Mark initiative as completed
  - [ ] Update database schema docs
  - [ ] Record deployment notes
  - [ ] Update runbooks

- [ ] **Knowledge Transfer**
  - [ ] Share lessons learned
  - [ ] Update team procedures
  - [ ] Document any issues
  - [ ] Plan future improvements

## 🎯 **Timeline**

### **Estimated Schedule**
- **Pre-deployment**: 30 minutes
- **Migration execution**: 15-30 minutes
- **Verification**: 15 minutes
- **Monitoring period**: 24 hours

### **Critical Path**
1. Database backup (10 min)
2. Migration execution (15 min)
3. Verification testing (15 min)
4. Team notification (5 min)

---

**Checklist Owner**: Database Team  
**Review Required**: Technical Lead  
**Approval Required**: DevOps Manager  
**Last Updated**: October 2, 2025
