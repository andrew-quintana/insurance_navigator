# Supabase Storage Integration Documentation

## Overview

The Insurance Navigator system now includes comprehensive Supabase Storage integration for secure policy document management. This integration provides enterprise-grade file storage with access control, signed URLs, and seamless database integration.

## Features Implemented

### ✅ Core Storage Operations
- **File Upload**: Secure upload with content type detection and file size validation
- **File Download**: Direct download and signed URL generation
- **File Listing**: Query documents by policy, type, user, and status
- **File Metadata**: Comprehensive metadata tracking and retrieval
- **File Permissions**: Role-based access control with owner/admin/user permissions

### ✅ Security Features
- **Private Storage Bucket**: All files stored in private Supabase Storage bucket
- **Signed URLs**: Time-limited access URLs (configurable expiry)
- **Access Control**: User-based permissions (read/write/delete)
- **Secure File Paths**: UUID-based file naming to prevent path traversal
- **File Size Limits**: Configurable maximum file size (default: 10MB)

### ✅ Database Integration
- **Metadata Storage**: File metadata stored in PostgreSQL with JSONB support
- **Soft Delete**: Files can be soft-deleted (marked inactive) or hard-deleted
- **Audit Trail**: Track upload time, user, and deletion metadata
- **Indexing**: Optimized queries with policy_id indexing

### ✅ File Type Support
- **Documents**: PDF, DOC, DOCX
- **Spreadsheets**: XLS, XLSX, CSV
- **Images**: JPG, JPEG, PNG, GIF
- **Text Files**: TXT, CSV
- **Content Type Detection**: Automatic MIME type detection

## API Reference

### StorageService Class

#### `upload_policy_document(policy_id, file_data, filename, user_id, document_type, metadata)`
Upload a policy document to Supabase Storage.

**Parameters:**
- `policy_id` (str): UUID of the policy
- `file_data` (bytes): Raw file data
- `filename` (str): Original filename
- `user_id` (str): ID of user uploading the file
- `document_type` (str): Type of document (policy, claim, etc.)
- `metadata` (dict, optional): Additional metadata

**Returns:**
```python
{
    'document_id': int,
    'file_path': str,
    'original_filename': str,
    'content_type': str,
    'file_size': int,
    'uploaded_at': str,
    'metadata': dict
}
```

#### `get_signed_url(file_path, expires_in, download)`
Generate a signed URL for file access.

**Parameters:**
- `file_path` (str): Path to the document in storage
- `expires_in` (int, optional): URL expiration time in seconds
- `download` (bool): Whether URL should force download

**Returns:** Signed URL string

#### `list_policy_documents(policy_id, document_type, user_id, include_inactive)`
List documents for a policy with filtering options.

**Parameters:**
- `policy_id` (str): UUID of the policy
- `document_type` (str, optional): Filter by document type
- `user_id` (str, optional): Filter by uploader
- `include_inactive` (bool): Include soft-deleted files

**Returns:** List of document dictionaries

#### `delete_document(file_path, user_id, hard_delete)`
Delete a document (soft or hard delete).

**Parameters:**
- `file_path` (str): Path to the document
- `user_id` (str): ID of user requesting deletion
- `hard_delete` (bool): Whether to permanently delete

**Returns:** Boolean success status

#### `get_file_access_permissions(file_path, user_id)`
Check file access permissions for a user.

**Returns:**
```python
{
    "read": bool,
    "write": bool,
    "delete": bool
}
```

## Configuration

### Environment Variables
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_STORAGE_BUCKET=documents
SIGNED_URL_EXPIRY_SECONDS=3600
```

### Database Schema
The integration automatically creates the `policy_documents` table:

```sql
CREATE TABLE policy_documents (
    id SERIAL PRIMARY KEY,
    policy_id TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    original_filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    document_type TEXT NOT NULL,
    uploaded_by TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_policy_documents_policy_id ON policy_documents(policy_id);
```

## Usage Examples

### Basic File Upload
```python
from db.services.storage_service import get_storage_service

storage_service = await get_storage_service()

# Upload a policy document
result = await storage_service.upload_policy_document(
    policy_id="123e4567-e89b-12d3-a456-426614174000",
    file_data=file_bytes,
    filename="policy.pdf",
    user_id="user123",
    document_type="policy",
    metadata={"department": "claims"}
)

print(f"Uploaded: {result['file_path']}")
```

### Generate Signed URL
```python
# Get a download URL that expires in 1 hour
signed_url = await storage_service.get_signed_url(
    file_path=result['file_path'],
    expires_in=3600,
    download=True
)

print(f"Download URL: {signed_url}")
```

### List Policy Documents
```python
# List all active documents for a policy
documents = await storage_service.list_policy_documents(
    policy_id="123e4567-e89b-12d3-a456-426614174000"
)

for doc in documents:
    print(f"{doc['original_filename']} - {doc['file_size']} bytes")
```

### Check Permissions
```python
# Check what a user can do with a file
permissions = await storage_service.get_file_access_permissions(
    file_path="policy/123/abc.pdf",
    user_id="user123"
)

if permissions['read']:
    print("User can read this file")
```

## Testing

### Comprehensive Test Suite
The storage integration includes a comprehensive test suite that validates:

- ✅ File upload functionality
- ✅ Signed URL generation
- ✅ Document listing and filtering
- ✅ Metadata retrieval
- ✅ File permissions (owner/non-owner)
- ✅ File download
- ✅ Multiple file type support
- ✅ Soft delete functionality
- ✅ Cleanup and error handling

### Running Tests
```bash
python db/scripts/test_storage_integration.py
```

### Test Results
```
🎉 Storage integration is working correctly!
✅ Supabase Storage is properly configured
✅ File upload/download working
✅ Signed URLs working
✅ Permissions working
✅ Database integration working
```

## Security Considerations

### Access Control
- Files are stored in a private Supabase Storage bucket
- Access is controlled through signed URLs with expiration
- Role-based permissions (owner, admin, user)
- Database-level access control for metadata

### File Security
- Secure file naming with UUIDs prevents path traversal
- Content type validation prevents malicious uploads
- File size limits prevent storage abuse
- Audit trail tracks all file operations

### Data Privacy
- Soft delete preserves audit trail while hiding files
- Hard delete permanently removes files and metadata
- User permissions prevent unauthorized access
- Metadata stored securely in PostgreSQL

## Integration Points

### Agent Integration
The storage service integrates with:
- **Chat Communicator**: File upload/download in conversations
- **Patient Navigator**: Policy document management
- **Service Access Strategy**: Document verification workflows

### Database Integration
- Seamless integration with existing user management
- Foreign key relationships with policies and users
- JSONB metadata for flexible document properties
- Optimized queries with proper indexing

### Frontend Integration
Ready for integration with:
- File upload components
- Document viewers
- Permission-based UI controls
- Progress indicators for uploads/downloads

## Performance Characteristics

### Upload Performance
- Direct upload to Supabase Storage (no server proxy)
- Concurrent uploads supported
- Progress tracking available
- Automatic retry on failure

### Download Performance
- Signed URLs provide direct access to Supabase CDN
- No server bandwidth usage for downloads
- Configurable expiration times
- Browser caching supported

### Database Performance
- Indexed queries for fast document listing
- JSONB metadata for flexible querying
- Connection pooling for concurrent operations
- Optimized for high-volume document management

## Monitoring and Logging

### Comprehensive Logging
- All operations logged with structured logging
- Error tracking with detailed context
- Performance metrics for upload/download times
- User activity audit trail

### Error Handling
- Graceful degradation on storage failures
- Detailed error messages for debugging
- Automatic cleanup on partial failures
- Retry logic for transient errors

## Future Enhancements

### Planned Features
- [ ] Document versioning
- [ ] Bulk upload operations
- [ ] Document search and indexing
- [ ] Thumbnail generation for images
- [ ] Document conversion (PDF generation)
- [ ] Advanced metadata querying

### Scalability Improvements
- [ ] CDN integration for global distribution
- [ ] Compression for large files
- [ ] Background processing for uploads
- [ ] Webhook integration for external systems

## Conclusion

The Supabase Storage integration provides a robust, secure, and scalable foundation for document management in the Insurance Navigator system. With comprehensive testing, security features, and seamless database integration, it's ready for production use and future enhancements. 