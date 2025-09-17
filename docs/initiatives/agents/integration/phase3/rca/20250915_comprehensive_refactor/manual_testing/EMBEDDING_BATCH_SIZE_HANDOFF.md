# Embedding Generation Batch Size Issue - Agent Handoff

## 🎯 **Current Issue: FM-032 - Embedding Generation Failure**

### **Problem Summary**
The upload pipeline processes documents successfully (chunks created, parsed markdown content) but RAG functionality fails because all embedding vectors contain only zeros. The root cause is that the OpenAI embedding generation is failing due to batch size limits.

### **Evidence**
- **Batch Size Error**: Enhanced worker logs show `"Batch size 1128 exceeds maximum 256"`
- **Zero Embeddings**: All embedding vectors in database are zero-filled arrays
- **RAG Failure**: Queries like "what is my deductible" return AI-generated apologies instead of document content
- **Pipeline Success**: Document parsing and chunking work correctly

### **Root Cause Identified**
The OpenAI embedding service has a maximum batch size limit of 256, but the enhanced worker is trying to process 1128 chunks at once, causing the embedding generation to fail and fall back to zero vectors.

### **Files to Investigate**
1. **`backend/workers/enhanced_base_worker.py`** (lines 893-976) - `_process_embeddings_real` method
2. **`backend/shared/external/openai_real.py`** (lines 216-217) - Batch size validation
3. **`backend/shared/external/enhanced_service_client.py`** (lines 221-315) - Service client batch handling

### **Current Implementation Issues**
```python
# In enhanced_base_worker.py line 932
embeddings = await self.enhanced_service_client.call_openai_service(
    texts=chunk_texts,  # This is ALL chunks at once (1128 items)
    user_id=user_id,
    job_id=str(job_id),
    document_id=str(document_id),
    correlation_id=correlation_id
)
```

### **Required Fix**
Implement proper batch processing for OpenAI embeddings:
1. **Split large batches** into chunks of 256 or fewer
2. **Process batches sequentially** or with controlled concurrency
3. **Handle rate limiting** appropriately
4. **Ensure proper vector storage** (currently stored as strings, not vectors)

### **Database State**
- **Total Chunks**: 1166 chunks exist in `upload_pipeline.document_chunks`
- **Embedding Format**: Stored as strings like `"[0.0,0.0,0.0,...]"` instead of proper vector type
- **Vector Dimensions**: 1536 (correct for text-embedding-3-small)
- **Content Quality**: Chunks contain actual insurance document content

### **Expected Outcome**
After fixing batch size handling:
- Embeddings should contain actual vector values (not zeros)
- RAG tool should retrieve relevant document chunks
- Chat queries should return document-based responses
- Similarity search should work correctly

### **Testing Approach**
1. Fix batch size handling in embedding generation
2. Test with a small document (few chunks) first
3. Verify embeddings contain non-zero values
4. Test RAG functionality with document queries
5. Scale up to larger documents

### **Priority**
**CRITICAL** - This blocks the entire RAG functionality despite successful document processing.

---

**Handoff Date**: 2025-09-17  
**Previous Agent**: Claude Sonnet 4  
**Issue**: FM-032  
**Status**: Root cause identified, fix required

