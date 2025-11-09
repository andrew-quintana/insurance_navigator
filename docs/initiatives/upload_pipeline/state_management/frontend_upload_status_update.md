# Frontend Upload Status Update - Option 1: Direct Supabase Client Update

## Overview

This document describes Option 1 for updating the upload job status after a successful file upload. This approach uses the Supabase client directly from the frontend, leveraging Row Level Security (RLS) policies to ensure users can only update their own jobs.

## Problem Analysis

### Current Issue

Currently, the upload job status is set to `'uploaded'` when the job is initially created (before the actual file upload occurs), which is semantically incorrect. The status should reflect the actual state of the file upload:

1. **Initial Status**: When the upload job is created, the status should be `'pending_upload'` or similar, indicating the file hasn't been uploaded yet.
2. **Post-Upload Status**: After the frontend successfully uses the signed URL to upload the file to blob storage, the status should be updated to `'uploaded'`.

### Current Flow Problems

- Status is set to `'uploaded'` before the file actually exists in storage
- No confirmation mechanism after successful upload via signed URL
- Status doesn't accurately reflect the actual upload state
- No way to track if upload succeeded or failed

## Solution: Direct Supabase Client Update

### Architecture Decision

**Option 1 (Recommended)**: Use Supabase client directly from frontend
- ✅ **Simple**: No additional backend endpoint needed
- ✅ **Secure**: RLS policies enforce authorization automatically
- ✅ **Efficient**: Direct database update without API roundtrip
- ✅ **Already Available**: Frontend already uses Supabase client for auth

**Option 2 (Alternative)**: Create backend endpoint
- ⚠️ More complex (requires new endpoint)
- ⚠️ Additional API call overhead
- ✅ Better for logging/auditing
- ✅ More control over update logic

This document focuses on **Option 1** as the recommended approach.

## Implementation Details

### 1. RLS Policy Verification

The existing RLS policies already support this approach. Users can update their own jobs through the `job_update_self` policy:

```sql
-- From supabase/migrations/20250925211343_phase3_upload_pipeline_rls_final.sql
create policy job_update_self on upload_pipeline.upload_jobs
    for update using (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.upload_jobs.document_id
                  and d.user_id = auth.uid())
    )
    with check (
        exists (select 1 from upload_pipeline.documents d
                where d.document_id = upload_pipeline.upload_jobs.document_id
                  and d.user_id = auth.uid())
    );
```

**Security**: This policy ensures users can only update jobs for documents they own, enforced automatically by Supabase's RLS system.

### 2. Frontend Implementation

#### Update Upload Status After Successful Upload

After the frontend successfully uploads a file using the signed URL, update the job status:

```typescript
// After successful upload to signed URL
import { supabase } from '@/lib/supabase-client'

const updateJobStatus = async (jobId: string) => {
  try {
    const { data, error } = await supabase
      .from('upload_jobs')
      .update({ status: 'uploaded' })
      .eq('job_id', jobId)
      .select()
    
    if (error) {
      console.error('Failed to update job status:', error)
      throw error
    }
    
    console.log('Job status updated successfully:', data)
    return data
  } catch (error) {
    console.error('Error updating job status:', error)
    throw error
  }
}
```

#### Integration with Document Upload Component

Update `ui/components/DocumentUpload.tsx` to call the status update after successful upload:

```typescript
// In handleUpload function, after successful file upload
if (fileUploadResponse.ok) {
  console.log('✅ File upload successful')
  
  // Update job status to 'uploaded'
  if (result.job_id) {
    try {
      await updateJobStatus(result.job_id)
      console.log('✅ Job status updated to uploaded')
    } catch (error) {
      console.error('⚠️ Failed to update job status:', error)
      // Don't fail the upload, but log the error
    }
  }
}
```

### 3. Backend Changes

#### Change Initial Status

Update `api/upload_pipeline/endpoints/upload.py` to set initial status to `'pending_upload'` instead of `'uploaded'`:

```python
# In _create_upload_job function
await db.execute(
    query,
    job_id,
    document_id,
    "pending_upload",  # Changed from "uploaded"
    "queued"  # state remains "queued"
)
```

**Note**: You may need to add `'pending_upload'` to the valid statuses list in the models if it's not already included.

#### Status Validation

Ensure `'pending_upload'` is in the allowed statuses. Update `api/upload_pipeline/models.py` if needed:

```python
valid_statuses = {
    'pending_upload',  # Add this
    'uploaded', 
    'parse_queued', 
    'parsed', 
    # ... other statuses
}
```

### 4. Status Flow

The complete status flow becomes:

1. **Job Creation** (`/api/upload-pipeline/upload`)
   - Status: `'pending_upload'`
   - State: `'queued'`
   - Returns: `job_id`, `document_id`, `signed_url`

2. **Frontend Upload** (Direct to blob storage via signed URL)
   - Uploads file to storage
   - On success: Updates status to `'uploaded'`

3. **Worker Processing** (Picks up job)
   - Worker selects jobs with `status = 'uploaded'` and `state = 'queued'`
   - Proceeds with parsing, chunking, embedding, etc.

## Security Considerations

### RLS Policy Enforcement

The RLS policy `job_update_self` ensures:
- Users can only update jobs for documents they own
- The `auth.uid()` function extracts the user ID from the JWT token
- No user can update another user's jobs
- Service role can still update any job (for backend workers)

### JWT Token Requirement

The frontend must have a valid Supabase session with an authenticated user:
- User must be logged in
- JWT token must be valid
- Token is automatically included in Supabase client requests

### Error Handling

If the status update fails:
- The upload itself was successful (file is in storage)
- Log the error but don't fail the upload flow
- Worker can still process the job (it checks for `status = 'uploaded'`)
- Consider retry logic for status updates

## Benefits

### 1. Accurate Status Tracking
- Status now reflects actual upload state
- Can differentiate between "pending" and "uploaded" jobs
- Better visibility into upload pipeline state

### 2. Simplified Architecture
- No additional backend endpoint needed
- Direct database update using existing Supabase client
- Leverages existing RLS policies

### 3. Reduced Latency
- No API roundtrip for status update
- Direct database operation
- Faster user feedback

### 4. Better User Experience
- Real-time status updates
- Accurate progress tracking
- Clear indication of upload completion

## Implementation Steps

### Phase 1: Backend Changes

1. Add `'pending_upload'` to valid statuses in `api/upload_pipeline/models.py`
2. Update `_create_upload_job` to use `'pending_upload'` instead of `'uploaded'`
3. Verify worker logic handles `'pending_upload'` correctly (should only process `'uploaded'`)

### Phase 2: Frontend Changes

1. Create `updateJobStatus` helper function
2. Update `DocumentUpload.tsx` to call status update after successful upload
3. Add error handling and logging
4. Test with both successful and failed upload scenarios

### Phase 3: Testing

1. **Unit Tests**: Test status update function
2. **Integration Tests**: Test complete upload flow
3. **Security Tests**: Verify RLS prevents unauthorized updates
4. **Error Handling**: Test failure scenarios

### Phase 4: Deployment

1. Deploy backend changes first (initial status change)
2. Deploy frontend changes
3. Monitor for any issues
4. Verify status updates are working correctly

## Code Examples

### Complete Frontend Implementation

```typescript
// ui/lib/upload-helpers.ts
import { supabase } from './supabase-client'

export interface UploadJobStatus {
  job_id: string
  status: string
  state: string
  updated_at: string
}

/**
 * Update upload job status after successful file upload
 * Uses Supabase client directly with RLS policy enforcement
 */
export async function updateJobStatusAfterUpload(
  jobId: string,
  newStatus: string = 'uploaded'
): Promise<UploadJobStatus | null> {
  try {
    const { data, error } = await supabase
      .from('upload_jobs')
      .update({ 
        status: newStatus,
        updated_at: new Date().toISOString()
      })
      .eq('job_id', jobId)
      .select()
      .single()
    
    if (error) {
      console.error('Failed to update job status:', {
        jobId,
        error: error.message,
        code: error.code,
        details: error.details
      })
      throw error
    }
    
    console.log('Job status updated successfully:', {
      jobId,
      status: data.status,
      state: data.state
    })
    
    return data as UploadJobStatus
  } catch (error) {
    console.error('Error updating job status:', error)
    // Return null instead of throwing to avoid breaking upload flow
    return null
  }
}
```

### Integration in DocumentUpload Component

```typescript
// In ui/components/DocumentUpload.tsx
import { updateJobStatusAfterUpload } from '@/lib/upload-helpers'

// Inside handleUpload function, after successful file upload
if (fileUploadResponse.ok) {
  console.log('✅ File upload successful')
  
  // Update job status to 'uploaded'
  if (result.job_id) {
    const updateResult = await updateJobStatusAfterUpload(result.job_id)
    
    if (updateResult) {
      console.log('✅ Job status updated to uploaded')
    } else {
      console.warn('⚠️ Failed to update job status, but upload was successful')
      // Upload succeeded, so don't fail the operation
      // Worker will still process the job (checks for uploaded status)
    }
  }
  
  // Continue with success handling...
  setUploadProgress(100)
  setUploadSuccess(true)
  // ...
}
```

## Testing

### Manual Testing

1. **Successful Upload Flow**:
   - Upload a document
   - Verify job is created with `status = 'pending_upload'`
   - Verify file uploads successfully
   - Verify status updates to `'uploaded'`
   - Verify worker picks up the job

2. **Upload Failure**:
   - Attempt to upload invalid file
   - Verify job remains in `'pending_upload'` status
   - Verify no status update occurs

3. **Authorization Test**:
   - Try to update another user's job status
   - Verify RLS policy prevents the update
   - Verify appropriate error is returned

### Automated Testing

```typescript
// tests/frontend/upload-status-update.test.ts
import { updateJobStatusAfterUpload } from '@/lib/upload-helpers'

describe('updateJobStatusAfterUpload', () => {
  it('should update job status to uploaded', async () => {
    const jobId = 'test-job-id'
    const result = await updateJobStatusAfterUpload(jobId)
    
    expect(result).not.toBeNull()
    expect(result?.status).toBe('uploaded')
    expect(result?.job_id).toBe(jobId)
  })
  
  it('should fail when updating another user\'s job', async () => {
    // Test RLS enforcement
    const otherUserJobId = 'other-user-job-id'
    const result = await updateJobStatusAfterUpload(otherUserJobId)
    
    expect(result).toBeNull()
  })
})
```

## Troubleshooting

### Common Issues

#### Issue: Status Update Fails with 401/403

**Cause**: Invalid or expired JWT token
**Solution**: 
- Ensure user is logged in
- Refresh Supabase session
- Check token expiration

#### Issue: Status Update Fails with RLS Error

**Cause**: User trying to update job they don't own
**Solution**:
- Verify job belongs to current user
- Check RLS policies are correct
- Verify document ownership

#### Issue: Status Not Updating

**Cause**: Job ID mismatch or job doesn't exist
**Solution**:
- Verify correct job_id is being used
- Check job exists in database
- Verify job belongs to current user

## Future Enhancements

### 1. Status Update Retry Logic

Add automatic retry for failed status updates:

```typescript
async function updateJobStatusWithRetry(jobId: string, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await updateJobStatusAfterUpload(jobId)
    } catch (error) {
      if (i === maxRetries - 1) throw error
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)))
    }
  }
}
```

### 2. Real-time Status Sync

Use Supabase Realtime to sync status updates across clients:

```typescript
const channel = supabase
  .channel(`job:${jobId}`)
  .on('postgres_changes', {
    event: 'UPDATE',
    schema: 'upload_pipeline',
    table: 'upload_jobs',
    filter: `job_id=eq.${jobId}`
  }, (payload) => {
    console.log('Job status updated:', payload.new)
  })
  .subscribe()
```

### 3. Status History Tracking

Track status change history for debugging:

```typescript
await supabase
  .from('upload_pipeline.events')
  .insert({
    job_id: jobId,
    event_type: 'status_update',
    details: {
      from: 'pending_upload',
      to: 'uploaded',
      timestamp: new Date().toISOString()
    }
  })
```

## Conclusion

Option 1 (Direct Supabase Client Update) provides a simple, secure, and efficient solution for updating upload job status after successful file uploads. The implementation leverages existing RLS policies and the Supabase client that's already in use, requiring minimal changes to the codebase while providing accurate status tracking throughout the upload pipeline.

**Key Benefits**:
- ✅ Accurate status tracking
- ✅ Simple implementation
- ✅ Secure (RLS enforced)
- ✅ Efficient (direct database update)
- ✅ No additional infrastructure needed

**Status**: Ready for Implementation

