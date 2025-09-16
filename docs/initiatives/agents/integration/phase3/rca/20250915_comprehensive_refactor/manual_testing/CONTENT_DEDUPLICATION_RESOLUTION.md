# Content Deduplication Guide - Upload Pipeline

## 🎯 **Overview**

The Insurance Navigator implements **content deduplication** to optimize storage and processing when multiple users upload identical content. Instead of re-processing the same document content, the system copies the already-processed data (chunks, embeddings, processing status) to the new user's document record.

## 🔧 **How It Works**

### **Content Deduplication Logic**
1. **Content Hash Check**: When a user uploads a document, the system checks if the same content hash (`file_sha256`) already exists for **other users**
2. **Data Copying**: If found, the system copies:
   - Processing status from the source document
   - All chunks and embeddings from the source document
   - Creates a new document record with the current user's ID
3. **No Re-processing**: The content is not re-processed, saving computational resources

### **User Isolation**
- Each user gets their own document record with their own `user_id`
- Users can only access their own documents
- Content deduplication happens transparently in the background

## 📊 **Technical Implementation**

### **Database Schema**
```sql
-- Documents table with user isolation
CREATE TABLE upload_pipeline.documents (
    document_id uuid PRIMARY KEY,
    user_id uuid NOT NULL,
    filename varchar(255) NOT NULL,
    file_sha256 varchar(64) NOT NULL,
    processing_status varchar(50) DEFAULT 'pending',
    -- ... other fields
);

-- Chunks table with document references
CREATE TABLE upload_pipeline.document_chunks (
    chunk_id uuid PRIMARY KEY,
    document_id uuid NOT NULL REFERENCES upload_pipeline.documents(document_id),
    chunk_ord integer NOT NULL,
    text text NOT NULL,
    embedding vector(1536),
    -- ... other fields
);
```

### **Deduplication Function**
```python
async def create_document_with_content_deduplication(conn, document_id, user_id, filename, 
                                                   mime, bytes_len, file_sha256, raw_path):
    """Create a document record with content deduplication."""
    
    # Check if same content exists for other users
    existing_docs = await conn.fetch("""
        SELECT document_id, user_id, processing_status, created_at
        FROM upload_pipeline.documents 
        WHERE file_sha256 = $1 AND user_id != $2
        ORDER BY created_at ASC
        LIMIT 1
    """, file_sha256, user_id)
    
    if existing_docs:
        # Copy processed data from existing document
        source_doc = existing_docs[0]
        
        # Create new document with same processing status
        await conn.execute("""
            INSERT INTO upload_pipeline.documents (
                document_id, user_id, filename, mime, bytes_len, 
                file_sha256, raw_path, processing_status, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
        """, document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path, source_doc['processing_status'])
        
        # Copy all chunks from source document
        await conn.execute("""
            INSERT INTO upload_pipeline.document_chunks (
                chunk_id, document_id, chunk_ord, text, embedding, created_at
            )
            SELECT 
                gen_random_uuid() as chunk_id,
                $1 as document_id,
                chunk_ord,
                text,
                embedding,
                NOW() as created_at
            FROM upload_pipeline.document_chunks 
            WHERE document_id = $2
        """, document_id, source_doc['document_id'])
        
        logger.info(f"✅ Content deduplication complete: Copied chunks from {source_doc['document_id']} to {document_id}")
    else:
        # No existing content - create new document normally
        await conn.execute("""
            INSERT INTO upload_pipeline.documents (
                document_id, user_id, filename, mime, bytes_len, 
                file_sha256, raw_path, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
        """, document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path)
```

## 🧪 **Testing Content Deduplication**

### **How Content Deduplication Works**

The system handles three scenarios:

1. **Same User + Same Content**: Updates existing document metadata, **NO deduplication**
2. **Different User + Same Content**: Creates new document for new user, **copies processed data** from existing user's document
3. **Different User + Different Content**: Creates new document, **normal processing**

**Key Points:**
- Each user gets their own `document_id` and `user_id` in their document record
- Content deduplication only happens between **different users**
- Processed data (chunks, embeddings, status) is **copied**, not shared
- Users can only access their own documents

### **Test Scenario 1: Same User, Same Content**
```bash
# Upload same content with same user (should update existing)
curl -X POST http://localhost:8000/api/v2/upload \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "filename": "test.pdf",
    "bytes_len": 1000,
    "mime": "application/pdf",
    "sha256": "same_hash_12345678901234567890123456789012",
    "ocr": false
  }'

# Upload same content again with same user
curl -X POST http://localhost:8000/api/v2/upload \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "filename": "test.pdf",
    "bytes_len": 1000,
    "mime": "application/pdf",
    "sha256": "same_hash_12345678901234567890123456789012",
    "ocr": false
  }'
```
**Expected**: Same `document_id`, updates existing document metadata, **NO content deduplication** (same user)

### **Test Scenario 2: Different Users, Same Content**
```bash
# User 1 uploads content
curl -X POST http://localhost:8000/api/v2/upload \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "filename": "test.pdf",
    "bytes_len": 1000,
    "mime": "application/pdf",
    "sha256": "dedup_test_hash_12345678901234567890123456789012",
    "ocr": false
  }'

# User 2 uploads same content (different user_id)
curl -X POST http://localhost:8000/api/v2/upload \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test.pdf",
    "bytes_len": 1000,
    "mime": "application/pdf",
    "sha256": "dedup_test_hash_12345678901234567890123456789012",
    "ocr": false
  }'
```
**Expected**: 
- Different `document_id` for User 2
- User 2 gets their own `user_id` in the document record
- User 2's document gets **copied** processed data (chunks, embeddings, status) from User 1's document
- **Content deduplication triggered** - no re-processing needed



### **Test Scenario 3: Different Users, Different Content**
```bash
# User 1 uploads content A
curl -X POST http://localhost:8000/api/v2/upload \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "filename": "test1.pdf",
    "bytes_len": 1000,
    "mime": "application/pdf",
    "sha256": "content_a_hash_12345678901234567890123456789012",
    "ocr": false
  }'

# User 2 uploads content B (different hash)
curl -X POST http://localhost:8000/api/v2/upload \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test2.pdf",
    "bytes_len": 1000,
    "mime": "application/pdf",
    "sha256": "content_b_hash_12345678901234567890123456789012",
    "ocr": false
  }'
```
**Expected**: Different `document_id`, creates new document (no deduplication)

## 📈 **Benefits**

### **Performance Benefits**
- **Faster Uploads**: No re-processing of identical content
- **Reduced CPU Usage**: Avoids duplicate embedding generation
- **Lower Storage Costs**: Shared content processing results
- **Better User Experience**: Instant availability of processed content

### **Resource Optimization**
- **Database Efficiency**: Reuses existing processed data
- **API Response Time**: Faster upload responses
- **Worker Service Load**: Reduces processing queue
- **Memory Usage**: Lower memory footprint

## 🔍 **Monitoring and Debugging**

### **Debug Logging**
The system includes debug logging to track deduplication activity:

```bash
# Monitor deduplication activity
tail -f logs/api_server.log | grep -E "(deduplication|Content deduplication|Copying processed data)"
```

### **Database Queries**
```sql
-- Check documents with same content hash
SELECT document_id, user_id, filename, file_sha256, processing_status, created_at
FROM upload_pipeline.documents 
WHERE file_sha256 = 'your_test_hash_here'
ORDER BY created_at DESC;

-- Check chunks for a document
SELECT chunk_id, document_id, chunk_ord, text, created_at
FROM upload_pipeline.document_chunks 
WHERE document_id = 'your_document_id_here'
ORDER BY chunk_ord;
```

### **Health Checks**
```bash
# Check API server health
curl http://localhost:8000/health

# Check worker service health
curl http://localhost:8001/health

# Test upload endpoint
curl -X POST http://localhost:8000/api/v2/upload \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"filename": "test.pdf", "bytes_len": 1000, "mime": "application/pdf", "sha256": "test_hash", "ocr": false}'
```

## 🚨 **Known Limitations**

### **Current Limitations**
1. **Content Hash Dependency**: Deduplication only works with identical content hashes
2. **User Isolation**: Users cannot access each other's documents
3. **Chunk Copying**: Only copies chunks, not other processing metadata
4. **Real-time Processing**: Deduplication happens during upload, not after processing

### **Future Enhancements**
1. **Fuzzy Matching**: Support for similar but not identical content
2. **Metadata Preservation**: Copy additional processing metadata
3. **Batch Deduplication**: Process multiple documents for deduplication
4. **Analytics**: Track deduplication statistics and savings

## 📝 **Testing Checklist**

### **Before Testing**
- [ ] API server running and healthy
- [ ] Worker service running and healthy
- [ ] Database connectivity confirmed
- [ ] Test users available

### **During Testing**
- [ ] Test same user, same content (should update)
- [ ] Test different users, same content (should deduplicate)
- [ ] Test different users, different content (should create new)
- [ ] Monitor logs for deduplication messages
- [ ] Verify database persistence
- [ ] Check chunk copying accuracy

### **After Testing**
- [ ] Document any issues found
- [ ] Record deduplication statistics
- [ ] Update test procedures if needed
- [ ] Note any performance improvements

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Required for content deduplication
DATABASE_URL=postgresql://user:pass@host:port/db
ENVIRONMENT=development
```

### **Database Requirements**
- PostgreSQL with UUID extension
- Vector extension for embeddings
- Proper indexes on `file_sha256` and `user_id` columns

---

**Status**: ✅ **IMPLEMENTED AND TESTED**  
**Last Updated**: 2025-09-16  
**Version**: 1.0  
**Maintainer**: Development Team
