# Stage Progression Update Summary

## Overview
The stage progression for the upload pipeline has been updated to include buffer states and validation steps for better process tracking and error handling.

## Updated Stage Progression

### Previous Stages
```
upload_validated → parsing → chunking → embedding → finalizing
```

### New Stages
```
queued → job_validated → parsing → parsed → parse_validated → chunking → chunks_buffered → chunked → embedding → embeddings_buffered → embedded
```

## Stage Descriptions

### 1. **queued**
- Job created and waiting for processing
- Initial state for all new upload jobs

### 2. **job_validated**
- File uploaded, dedupe check complete
- Ready for parsing (replaces previous `upload_validated`)

### 3. **parsing**
- PDF converted to normalized markdown via LlamaIndex
- Processing in progress

### 4. **parsed**
- Parse complete, content stored
- Ready for validation

### 5. **parse_validated**
- Parse validation complete (SHA256 verification)
- Ready for chunking

### 6. **chunking**
- Markdown split into semantic chunks
- Processing in progress

### 7. **chunks_buffered**
- Chunks placed in buffer table
- Ready for database commit

### 8. **chunked**
- Chunks committed to database
- Ready for embedding

### 9. **embedding**
- Chunks converted to vectors via OpenAI
- Processing in progress

### 10. **embeddings_buffered**
- Embeddings placed in buffer table
- Ready for database commit

### 11. **embedded**
- Embeddings committed to database
- Document ready for search (terminal stage)

## Files Updated

### 1. Database Schema
- **File**: `supabase/migrations/20250814000000_init_upload_pipeline.sql`
- **Changes**: Updated stage check constraint and validation function

### 2. Utility Functions
- **File**: `utils/upload_pipeline_utils.py`
- **Changes**: Updated `validate_stage_transition()` function with new progression

### 3. API Models
- **File**: `api/upload_pipeline/models.py`
- **Changes**: Updated stage validation and job payload models

### 4. Documentation
- **Files**: All documentation files updated to reflect new progression
- **Changes**: Stage descriptions, examples, and implementation guidance

## Benefits of New Progression

### 1. **Better Process Tracking**
- Clear distinction between processing and buffered states
- Validation steps ensure data integrity at each stage
- More granular progress reporting

### 2. **Improved Error Handling**
- Buffer states prevent partial database updates
- Validation steps catch issues before proceeding
- Clear rollback points for failed operations

### 3. **Enhanced Observability**
- More detailed event logging opportunities
- Better progress calculation for frontend
- Clearer debugging and troubleshooting

### 4. **Atomic Operations**
- Buffer states enable clean commit/rollback
- Prevents partial state corruption
- Better support for concurrent processing

## Implementation Impact

### 1. **Worker Logic**
- Workers must handle new buffer states
- Validation logic for parse and chunk stages
- Buffer cleanup after successful commits

### 2. **Frontend Updates**
- Progress calculation must account for new stages
- Status display should show buffer states
- Error handling for validation failures

### 3. **Database Operations**
- Buffer table operations for chunks and embeddings
- Advisory locking for atomic updates
- Cleanup procedures for buffer data

### 4. **Event Logging**
- New event codes for buffer states
- Validation success/failure events
- Progress tracking for each stage

## Migration Considerations

### 1. **Existing Jobs**
- Any existing jobs in old stages need migration
- Consider data migration scripts if needed
- Update any hardcoded stage references

### 2. **Frontend Compatibility**
- Update progress calculation logic
- Handle new stage names in UI
- Update error handling for new states

### 3. **Worker Updates**
- Update stage transition logic
- Implement buffer state handling
- Add validation step processing

### 4. **Testing**
- Update test cases for new stages
- Validate stage transition logic
- Test buffer operations and cleanup

## Next Steps

### 1. **Phase 2 Implementation**
- Update worker logic for new stages
- Implement buffer state handling
- Add validation step processing

### 2. **Frontend Updates**
- Update progress calculation
- Handle new stage names
- Implement buffer state display

### 3. **Testing and Validation**
- Test new stage progression
- Validate buffer operations
- Ensure proper cleanup

### 4. **Documentation Updates**
- Update implementation guides
- Add buffer state examples
- Document validation procedures

## Conclusion

The updated stage progression provides better process tracking, improved error handling, and enhanced observability. The addition of buffer states and validation steps ensures data integrity and enables atomic operations throughout the pipeline.

**Key Benefits**:
- More granular process tracking
- Better error handling and recovery
- Enhanced observability and debugging
- Atomic operations with buffer states
- Clear validation checkpoints

**Implementation Priority**: High - This affects the core pipeline logic and should be implemented before Phase 2 development begins.
