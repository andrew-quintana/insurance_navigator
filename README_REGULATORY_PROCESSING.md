# Regulatory Document Processing System

## Overview

The regulatory document processing system allows bulk upload and processing of healthcare regulatory documents from URLs. It downloads raw files, stores them in the `raw_documents` storage bucket, extracts text content, and creates searchable vector embeddings.

## Features

✅ **Download & Store Raw Files** - Downloads actual PDFs and documents from URLs  
✅ **Unified Vector Storage** - Uses the existing `document_vectors` table for all document types  
✅ **Duplicate Detection** - Content hashing prevents reprocessing  
✅ **Batch Processing** - Respectful server interaction with delays  
✅ **Comprehensive Healthcare Coverage** - 30+ curated regulatory documents  
✅ **Storage Integration** - Files stored in Supabase `raw_documents` bucket  
✅ **Search Ready** - Vector similarity search for regulatory content  

## Architecture

### Database Schema

The system enhances the existing `document_vectors` table:

```sql
-- Unified vector storage for user documents AND regulatory documents
document_vectors:
  - user_id (NULL for regulatory docs)
  - regulatory_document_id (FK to regulatory_documents)
  - document_record_id (FK to documents table for user docs)  
  - document_source_type ('user_document' | 'regulatory_document')
  - content_embedding (vector data)
  - encrypted_chunk_text/metadata (HIPAA compliant)
```

### Storage Structure

```
raw_documents/
├── regulatory/
│   ├── 2025/01/
│   │   ├── uuid_Medicare-and-You-2024.pdf
│   │   ├── uuid_HIPAA-Privacy-Rule.pdf
│   │   └── ...
│   └── 2025/02/
└── user_uploads/
    └── ...
```

## Quick Start

### 1. Run Database Migration

```bash
psql -f db/migrations/015_add_regulatory_vectors_support.sql
```

### 2. Process High-Priority Documents

```bash
python scripts/bulk_regulatory_processor.py data/healthcare_urls.txt
```

### 3. Process All Curated Documents

```bash
python scripts/bulk_regulatory_processor.py --healthcare-documents
```

## Document Collection

### Healthcare Document Categories (30 total)

1. **Medicare/Medicaid Core** (5 docs)
   - Official Medicare handbook
   - Medicaid eligibility guidelines  
   - Part D prescription coverage
   - Medicare Advantage plans
   - CHIP program information

2. **Patient Rights & HIPAA** (3 docs)
   - Patient Bill of Rights
   - HIPAA Privacy Rule
   - Medical records access rights

3. **CMS Guidelines** (3 docs)
   - Medicare Learning Network
   - Coverage database
   - Quality measures

4. **ACA & Insurance Protections** (3 docs)
   - Essential health benefits
   - No Surprises Act
   - Mental health parity

5. **Appeals & Assistance** (2 docs)
   - Medicare appeals process
   - Extra Help program

### High Priority Documents (18 with priority ≥8)

Documents with priority scores 8-10 cover the most essential regulatory information for patient navigation.

## Usage Examples

### Basic Processing

```bash
# Single URL
python scripts/bulk_regulatory_processor.py "https://www.medicare.gov/Pubs/pdf/10050-Medicare-and-You.pdf"

# File with URLs
echo "https://www.medicare.gov/claims-appeals/" > my_urls.txt
python scripts/bulk_regulatory_processor.py my_urls.txt

# All curated documents
python scripts/bulk_regulatory_processor.py --healthcare-documents
```

### Advanced Processing

```bash
# Process only high-priority documents
python -c "
from data.healthcare_regulatory_documents import get_high_priority_documents
docs = get_high_priority_documents()
with open('high_priority_urls.txt', 'w') as f:
    for doc in docs: f.write(doc['url'] + '\n')
"
python scripts/bulk_regulatory_processor.py high_priority_urls.txt

# Process by category
python -c "
from data.healthcare_regulatory_documents import get_documents_by_category
docs = get_documents_by_category('medicare_core')
with open('medicare_urls.txt', 'w') as f:
    for doc in docs: f.write(doc['url'] + '\n')
"
python scripts/bulk_regulatory_processor.py medicare_urls.txt
```

## Search & Query

### Vector Search

```python
import asyncio
from db.services.db_pool import get_db_pool
from db.services.encryption_aware_embedding_service import get_encryption_aware_embedding_service

async def search_regulatory_docs(query: str):
    """Search regulatory documents using vector similarity."""
    embedding_service = await get_encryption_aware_embedding_service()
    query_embedding = await embedding_service._get_embedding(query)
    
    pool = await get_db_pool()
    async with pool.get_connection() as conn:
        results = await conn.fetch("""
            SELECT 
                rd.title,
                rd.jurisdiction,
                rd.source_url,
                dv.content_embedding <=> $1::vector as similarity_score
            FROM document_vectors dv
            JOIN regulatory_documents rd ON dv.regulatory_document_id = rd.document_id
            WHERE dv.document_source_type = 'regulatory_document'
            AND dv.is_active = true
            ORDER BY similarity_score
            LIMIT 10
        """, str(query_embedding))
        
        return results

# Usage
results = asyncio.run(search_regulatory_docs("Medicare prescription drug coverage"))
for doc in results:
    print(f"{doc['title']} - Similarity: {doc['similarity_score']:.3f}")
```

### Database Queries

```sql
-- Count regulatory documents by type
SELECT document_source_type, COUNT(*) 
FROM document_vectors 
GROUP BY document_source_type;

-- List stored regulatory files
SELECT rd.title, rd.source_url, rd.raw_document_path
FROM regulatory_documents rd
WHERE rd.raw_document_path LIKE 'regulatory/%';

-- Search by text (fallback)
SELECT rd.title, rd.jurisdiction, rd.program
FROM regulatory_documents rd
WHERE rd.title ILIKE '%medicare%'
OR 'Medicare' = ANY(rd.program);
```

## Monitoring & Maintenance

### Processing Results

The bulk processor provides detailed output:

```
======================================================================
BULK REGULATORY PROCESSING RESULTS
======================================================================
✅ Successfully processed: 25
🔄 Duplicates skipped: 2
❌ Failed: 3
📊 Total vectors created: 1,247
⏱️  Processing time: 180.45 seconds

Successfully processed documents:
  📄 Medicare & You 2024 Official Handbook...
      Vectors: 89 | 📁 Medicare-and-You-2024.pdf | Size: 2,450,123 bytes
  📄 HIPAA Privacy Rule Summary...
      Vectors: 34 | 🌐 Text only | Size: N/A bytes
```

### Health Checks

```bash
# Check storage bucket
python -c "
import asyncio
from scripts.bulk_regulatory_processor import UnifiedRegulatoryProcessor
processor = UnifiedRegulatoryProcessor()
# Check if files are accessible
"

# Check database
psql -c "SELECT COUNT(*) FROM regulatory_documents;"
psql -c "SELECT COUNT(*) FROM document_vectors WHERE document_source_type = 'regulatory_document';"
```

### File Management

```bash
# List stored files in Supabase
# (Via Supabase dashboard or storage API)

# Check file sizes
psql -c "
SELECT 
    rd.title,
    (rd.search_metadata->>'file_size')::bigint as file_size_bytes,
    rd.raw_document_path
FROM regulatory_documents rd 
WHERE rd.raw_document_path LIKE 'regulatory/%'
ORDER BY (rd.search_metadata->>'file_size')::bigint DESC;
"
```

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure you're in project root
cd /path/to/insurance_navigator
python scripts/bulk_regulatory_processor.py
```

**Storage Upload Failures**
- Check `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` environment variables
- Verify `raw_documents` bucket exists
- Check file size limits (50MB default)

**Vector Processing Errors**
- Ensure embedding service is available
- Check content extraction for short documents
- Monitor encryption key availability

**Database Connection Issues**
- Verify `DATABASE_URL` environment variable
- Check if migration 015 was applied
- Test basic database connectivity

### Log Analysis

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python scripts/bulk_regulatory_processor.py --healthcare-documents

# Check recent processing
psql -c "
SELECT rd.title, rd.created_at, rd.extraction_method
FROM regulatory_documents rd 
ORDER BY rd.created_at DESC 
LIMIT 10;
"
```

## Configuration

### Environment Variables

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://user:pass@host:port/db

# Optional
LOG_LEVEL=INFO
ASYNCPG_DISABLE_PREPARED_STATEMENTS=1  # For transaction poolers
```

### Storage Settings

- **Bucket**: `raw_documents`
- **Path Pattern**: `regulatory/YYYY/MM/uuid_filename.ext`
- **Max File Size**: 50MB
- **Allowed Types**: PDF, DOC, DOCX, TXT, RTF

### Processing Settings

- **Batch Size**: 3 URLs per batch
- **Delay Between Batches**: 2 seconds
- **Chunk Size**: 1,200 characters
- **Chunk Overlap**: 200 characters

## Integration

### With Existing Chat System

The regulatory vectors integrate seamlessly with your chat system:

```python
# In your chat service
async def get_regulatory_context(user_query: str):
    """Get relevant regulatory information for user query."""
    embedding_service = await get_encryption_aware_embedding_service()
    query_embedding = await embedding_service._get_embedding(user_query)
    
    pool = await get_db_pool()
    async with pool.get_connection() as conn:
        # Search both user documents and regulatory documents
        user_results = await conn.fetch("""
            SELECT 'user' as source, d.original_filename as title, 
                   dv.content_embedding <=> $1::vector as score
            FROM document_vectors dv
            JOIN documents d ON dv.document_record_id = d.id
            WHERE dv.document_source_type = 'user_document'
            AND dv.user_id = $2
            ORDER BY score LIMIT 5
        """, str(query_embedding), user_id)
        
        regulatory_results = await conn.fetch("""
            SELECT 'regulatory' as source, rd.title,
                   dv.content_embedding <=> $1::vector as score
            FROM document_vectors dv
            JOIN regulatory_documents rd ON dv.regulatory_document_id = rd.document_id
            WHERE dv.document_source_type = 'regulatory_document'
            ORDER BY score LIMIT 5
        """, str(query_embedding))
        
        return list(user_results) + list(regulatory_results)
```

### With Document Service

```python
# Enhanced document search
from db.services.document_service import DocumentService

class EnhancedDocumentService(DocumentService):
    async def search_all_documents(self, user_id: str, query: str):
        """Search both user and regulatory documents."""
        user_results = await self.search_user_documents(user_id, query)
        regulatory_results = await self.search_regulatory_documents(query)
        
        return {
            'user_documents': user_results,
            'regulatory_documents': regulatory_results,
            'total_results': len(user_results) + len(regulatory_results)
        }
```

---

## Next Steps

1. **Run Migration**: Apply database schema changes
2. **Process Documents**: Start with high-priority healthcare URLs
3. **Test Search**: Verify vector search functionality
4. **Monitor Processing**: Check logs and storage usage
5. **Integrate with Chat**: Enhance user queries with regulatory context

The system is designed to scale and can easily accommodate additional document sources and categories as needed. 