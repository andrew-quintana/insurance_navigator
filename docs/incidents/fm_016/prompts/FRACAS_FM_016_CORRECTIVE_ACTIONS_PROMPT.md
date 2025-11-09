# FRACAS FM-016 Corrective Actions Prompt

## Issue Summary
Staging API deployment failed to pick up changes from staging branch, causing 500 authentication errors when frontend calls the new standardized endpoint `/api/upload-pipeline/upload`.

## Root Cause
- Staging branch is behind development branch
- Missing critical commits for standardized endpoints
- Staging API running old code with mixed endpoints

## Corrective Actions Required

### Phase 1: Branch Synchronization
**Objective**: Update staging branch with latest standardized endpoint changes

**Actions**:
1. **Check current branch status**:
   ```bash
   git checkout staging
   git status
   git log --oneline -5
   ```

2. **Merge development branch changes**:
   ```bash
   git merge development
   # Resolve any merge conflicts if they occur
   ```

3. **Verify critical commits are present**:
   ```bash
   git log --oneline | grep -E "(standardize|upload-pipeline)"
   # Should show commits 967a163 and 2aca87d
   ```

4. **Push updated staging branch**:
   ```bash
   git push origin staging
   ```

### Phase 2: Staging Deployment Update
**Objective**: Force redeploy staging API with latest changes

**Actions**:
1. **Verify deployment configuration**:
   - Check `config/render/render.free-tier.yaml` points to `staging` branch
   - Confirm environment variables are properly configured

2. **Trigger staging deployment**:
   - Use Render.com dashboard to force redeploy
   - Or use Render CLI if available
   - Monitor deployment logs for errors

3. **Verify deployment success**:
   - Check staging API health endpoint
   - Verify new endpoints are available

### Phase 3: Endpoint Verification
**Objective**: Ensure all standardized endpoints are working correctly

**Actions**:
1. **Test standardized upload endpoint**:
   ```bash
   curl -X GET https://insurance-navigator-staging-api.onrender.com/api/upload-pipeline/upload
   # Should return 401 (unauthorized) not 404 (not found)
   ```

2. **Verify legacy endpoints are removed**:
   ```bash
   curl -X POST https://insurance-navigator-staging-api.onrender.com/api/v1/upload
   # Should return 404 (not found)
   ```

3. **Check authentication service**:
   ```bash
   curl -X POST https://insurance-navigator-staging-api.onrender.com/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test"}'
   # Should return proper response, not 500 error
   ```

### Phase 4: Frontend Integration Testing
**Objective**: Verify frontend can successfully communicate with staging API

**Actions**:
1. **Test frontend upload functionality**:
   - Access staging frontend
   - Attempt to upload a test document
   - Verify no 500 errors occur

2. **Check browser network tab**:
   - Confirm requests go to `/api/upload-pipeline/upload`
   - Verify authentication headers are present
   - Check for proper response codes

3. **Test authentication flow**:
   - Login to staging frontend
   - Verify JWT token is received
   - Confirm token is used in upload requests

### Phase 5: End-to-End Validation
**Objective**: Complete upload workflow testing

**Actions**:
1. **Full upload workflow test**:
   - Login to staging frontend
   - Upload a test PDF document
   - Verify document processing starts
   - Check job status endpoint

2. **Error handling verification**:
   - Test with invalid file types
   - Test with oversized files
   - Verify proper error messages

3. **Performance validation**:
   - Check response times
   - Verify no timeout errors
   - Monitor for any 500 errors

## Verification Checklist

### Pre-Deployment
- [ ] Staging branch updated with latest changes
- [ ] All critical commits present (967a163, 2aca87d)
- [ ] No merge conflicts
- [ ] Branch pushed to remote

### Deployment
- [ ] Staging API redeployed successfully
- [ ] Health endpoint responding
- [ ] New endpoints available
- [ ] Legacy endpoints removed

### Testing
- [ ] Standardized endpoints responding correctly
- [ ] Authentication service working (200 responses)
- [ ] Frontend upload functionality working
- [ ] No 500 errors in staging environment
- [ ] End-to-end upload workflow complete

### Post-Deployment
- [ ] Staging environment fully functional
- [ ] Upload testing can proceed
- [ ] All error conditions resolved
- [ ] Documentation updated

## Rollback Plan
If issues occur during deployment:

1. **Immediate rollback**:
   - Revert staging branch to previous working commit
   - Force redeploy staging API
   - Verify basic functionality restored

2. **Investigation**:
   - Review deployment logs
   - Identify specific failure points
   - Address issues before retry

3. **Retry deployment**:
   - Fix identified issues
   - Re-attempt deployment process
   - Monitor closely for errors

## Success Criteria
- Staging API updated with latest standardized endpoints
- Frontend can successfully upload documents
- No 500 authentication errors
- All legacy endpoints removed
- Upload functionality working end-to-end
- Staging environment ready for testing

## Monitoring
- Watch deployment logs during update
- Monitor API response times
- Check for any error spikes
- Verify frontend functionality
- Test upload workflow completion

## Files to Monitor
- `config/render/render.free-tier.yaml` - Deployment configuration
- `ui/components/DocumentUpload.tsx` - Frontend upload component
- `api/upload_pipeline/endpoints/upload.py` - Backend upload endpoint
- `main.py` - Main API application
- Staging API logs and metrics

## Expected Timeline
- **Phase 1**: 5-10 minutes (branch sync)
- **Phase 2**: 10-15 minutes (deployment)
- **Phase 3**: 5-10 minutes (endpoint verification)
- **Phase 4**: 10-15 minutes (frontend testing)
- **Phase 5**: 15-20 minutes (end-to-end validation)

**Total Estimated Time**: 45-70 minutes

## Notes
- Ensure staging environment variables are properly configured
- Monitor for any database migration issues
- Verify external service integrations (Supabase, etc.)
- Check for any environment-specific configuration issues
