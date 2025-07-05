# Vector-First Migration Guide

## Overview

This guide covers the complete migration from a traditional relational database schema to a vector-first architecture for the insurance policy management system. The migration consolidates `policy_documents` and `policy_records` tables into unified vector storage optimized for RAG (Retrieval Augmented Generation) workflows.

## Migration Goals

### 🎯 Primary Objectives

1. **Consolidate Policy Data**: Merge `policy_documents` and `policy_records` into `policy_content_vectors`
2. **Enable Semantic Search**: Implement vector-based similarity search for documents
3. **Optimize RAG Workflows**: Streamline context retrieval for 7+ AI agents
4. **Improve Performance**: Target <100ms for vector searches
5. **Maintain Data Integrity**: Preserve all existing functionality

### 📊 Success Criteria

- [ ] Policy and document data consolidated into vector tables
- [ ] Semantic search working for both policy and user content  
- [ ] RAG workflows simplified to single vector queries
- [ ] Performance improved (target: <100ms for vector searches)
- [ ] All existing functionality preserved
- [ ] Data migration completed with >95% success rate

## Architecture Changes

### Before (Traditional Schema)
```
policy_records (structured metadata)
     ↓
policy_documents (file storage)
     ↓
Complex multi-table joins for context retrieval
```

### After (Vector-First Schema)
```
policy_content_vectors (unified policy data + embeddings)
user_document_vectors (chunked user documents + embeddings)
     ↓
Single vector similarity search for RAG context
```

## New Database Schema

### 1. Policy Content Vectors Table
```sql
CREATE TABLE policy_content_vectors (
    id UUID PRIMARY KEY,
    policy_id UUID NOT NULL,
    user_id UUID NOT NULL,
    content_embedding VECTOR(1536) NOT NULL,
    content_text TEXT NOT NULL,
    policy_metadata JSONB NOT NULL DEFAULT '{}',
    document_metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true
);
```

### 2. User Document Vectors Table
```sql
CREATE TABLE user_document_vectors (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    document_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL,
    content_embedding VECTOR(1536) NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);
```

## Migration Process

### Step 1: Pre-Migration Preparation

#### 1.1 Dependencies Check
```bash
# Verify required Python packages
pip install sentence-transformers>=2.2.0
pip install langchain>=0.0.200
pip install pgvector>=0.2.3

# Verify PostgreSQL version (requires 11+)
psql -c "SELECT version();"
```

#### 1.2 Database Backup
```bash
# Create full database backup
pg_dump $DATABASE_URL > backup_pre_vector_migration_$(date +%Y%m%d_%H%M%S).sql

# Verify backup integrity
pg_restore --list backup_pre_vector_migration_*.sql
```

#### 1.3 Environment Setup
```bash
# Set environment variables
export USE_OPENAI_EMBEDDINGS=false  # Use local embeddings
export VECTOR_DIMENSION=1536        # Target embedding dimension
export MIGRATION_BATCH_SIZE=100     # Process in batches
```

### Step 2: Execute Migration

#### 2.1 Dry Run (Recommended)
```bash
cd /path/to/insurance_navigator
python db/scripts/run_vector_migration.py --dry-run
```

This will:
- ✅ Run all pre-migration checks
- ✅ Validate dependencies and configuration  
- ✅ Estimate migration time and resources
- ✅ Generate detailed report without making changes

#### 2.2 Full Migration
```bash
# Execute complete migration
python db/scripts/run_vector_migration.py

# Or with specific options
python db/scripts/run_vector_migration.py --skip-migration --force
```

**Migration Flags:**
- `--dry-run`: Check everything without making changes
- `--skip-migration`: Skip schema migration (if already run)
- `--force`: Continue even if pre-checks fail

### Step 3: Post-Migration Validation

The migration script automatically validates:

1. **Vector Tables Created**: Confirms new tables exist with proper schema
2. **Data Migrated**: Verifies record counts and data integrity
3. **Vector Search Working**: Tests semantic search functionality
4. **Indexes Operational**: Confirms vector indexes are optimized
5. **RLS Policies Active**: Validates Row Level Security is working

## New Services and APIs

### 1. Embedding Service

**Location**: `db/services/embedding_service.py`

```python
from db.services.embedding_service import get_embedding_service

# Generate embeddings for policy documents
service = await get_embedding_service()
vector_id = await service.process_policy_document(
    policy_id="policy-123",
    user_id="user-456", 
    content_text="Insurance policy content...",
    policy_metadata={"coverage_type": "health"},
    document_metadata={"document_type": "policy_summary"}
)

# Search similar content
results = await service.search_policy_content(
    query="What are my dental benefits?",
    user_id="user-456",
    limit=5
)
```

### 2. Enhanced Storage Service

**Location**: `db/services/storage_service.py`

```python
from db.services.storage_service import get_storage_service

# Upload with automatic vector generation
storage = await get_storage_service()
result = await storage.upload_policy_document_with_vectors(
    policy_id="policy-123",
    file_data=pdf_bytes,
    filename="policy.pdf", 
    user_id="user-456",
    policy_metadata={"coverage_type": "health"}
)

# Search documents by content
matches = await storage.search_documents_by_content(
    query="prescription drug coverage",
    user_id="user-456",
    limit=10
)
```

### 3. Unified RAG Interface

**Location**: `agents/common/vector_rag.py`

```python
from agents.common.vector_rag import get_vector_rag

# Simple agent integration
rag = await get_vector_rag()

# Get context for agent prompts
context = await rag.get_rag_prompt_context(
    query="What dental procedures are covered?",
    user_id="user-456",
    max_context_length=4000
)

# Use in agent prompt
prompt = f"""
Based on the following context, answer the user's question:

{context}

User Question: What dental procedures are covered?
"""
```

## Agent Integration

### Updating Existing Agents

Replace complex database queries with simple vector searches:

**Before:**
```python
# Old complex approach
policy_data = await get_policy_records(user_id)
document_data = await get_policy_documents(policy_id)
context = combine_and_filter_data(policy_data, document_data, query)
```

**After:**
```python
# New streamlined approach  
vector_rag = await get_vector_rag()
context = await vector_rag.get_rag_prompt_context(query, user_id)
```

### Example Agent Update

```python
# agents/patient_navigator/core/navigator_agent.py

from agents.common.vector_rag import get_vector_rag

class PatientNavigatorAgent:
    async def answer_question(self, user_id: str, question: str) -> str:
        # Get relevant context using vectors
        rag = await get_vector_rag()
        context = await rag.get_combined_context(
            query=question,
            user_id=user_id,
            policy_limit=3,
            document_limit=5
        )
        
        # Build prompt with context
        prompt = self._build_prompt(question, context)
        
        # Generate response
        response = await self.llm.generate(prompt)
        return response
```

## Performance Optimization

### Vector Index Tuning

```sql
-- Adjust IVFFlat parameters for better performance
DROP INDEX IF EXISTS idx_policy_content_vectors_embedding;
CREATE INDEX idx_policy_content_vectors_embedding 
    ON policy_content_vectors 
    USING ivfflat (content_embedding vector_cosine_ops)
    WITH (lists = 1000);  -- Adjust based on data volume

-- Monitor index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch 
FROM pg_stat_user_indexes 
WHERE indexname LIKE '%embedding%';
```

### Query Performance

```sql
-- Monitor vector search performance
EXPLAIN (ANALYZE, BUFFERS) 
SELECT content_text, content_embedding <=> $1 as distance 
FROM policy_content_vectors 
WHERE user_id = $2 
ORDER BY content_embedding <=> $1 
LIMIT 5;
```

### Embedding Model Optimization

```python
# Switch to faster/smaller models for production
# In embedding_service.py

# Option 1: Smaller, faster model
self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions

# Option 2: Better quality, larger model  
self.embedding_model = SentenceTransformer('all-mpnet-base-v2')  # 768 dimensions

# Option 3: OpenAI embeddings (requires API key)
from langchain_openai import OpenAIEmbeddings
self.embedding_model = OpenAIEmbeddings()  # 1536 dimensions
```

## Troubleshooting

### Common Issues

#### 1. pgvector Extension Not Available
```sql
-- Check if extension is installed
SELECT * FROM pg_available_extensions WHERE name = 'vector';

-- Install extension (requires superuser)
CREATE EXTENSION IF NOT EXISTS vector;
```

#### 2. Embedding Model Download Issues
```bash
# Pre-download models to avoid runtime delays
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print('Model downloaded successfully')
"
```

#### 3. Memory Issues with Large Documents
```python
# Adjust chunking parameters in embedding_service.py
self.text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      # Reduce chunk size
    chunk_overlap=100,   # Reduce overlap
    length_function=len,
    separators=["\n\n", "\n", " ", ""]
)
```

#### 4. Slow Vector Searches
```sql
-- Check if indexes are being used
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM policy_content_vectors 
WHERE content_embedding <=> '[...]' < 0.5;

-- Rebuild indexes if needed
REINDEX INDEX idx_policy_content_vectors_embedding;
```

### Migration Rollback

If issues occur during migration:

```bash
# 1. Restore from backup
psql $DATABASE_URL < backup_pre_vector_migration_YYYYMMDD_HHMMSS.sql

# 2. Drop vector tables (if needed)
psql $DATABASE_URL -c "
DROP TABLE IF EXISTS policy_content_vectors CASCADE;
DROP TABLE IF EXISTS user_document_vectors CASCADE;
"

# 3. Verify original functionality
python -m pytest tests/db/
```

## Monitoring and Maintenance

### Key Metrics to Monitor

1. **Vector Search Performance**
   ```sql
   -- Average query time for vector searches
   SELECT avg(total_time) as avg_ms
   FROM pg_stat_statements 
   WHERE query LIKE '%content_embedding <=>%';
   ```

2. **Storage Usage**
   ```sql
   -- Vector table sizes
   SELECT 
       schemaname,
       tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
   FROM pg_tables 
   WHERE tablename LIKE '%vectors';
   ```

3. **Embedding Generation Rate**
   ```python
   # Monitor in application logs
   embedding_stats = await embedding_service.get_embedding_stats()
   logger.info(f"Vector storage stats: {embedding_stats}")
   ```

### Regular Maintenance Tasks

```bash
# Weekly: Analyze vector tables for query optimization
psql $DATABASE_URL -c "ANALYZE policy_content_vectors, user_document_vectors;"

# Monthly: Vacuum and reindex vector tables  
psql $DATABASE_URL -c "VACUUM ANALYZE policy_content_vectors;"
psql $DATABASE_URL -c "REINDEX INDEX idx_policy_content_vectors_embedding;"

# Quarterly: Review and optimize embedding dimensions
python db/scripts/analyze_vector_performance.py
```

## Security Considerations

### Row Level Security (RLS)

The migration maintains all existing RLS policies:

```sql
-- Policy content access control
CREATE POLICY "policy_content_vectors_user_access" ON policy_content_vectors
    FOR ALL USING (
        user_id = auth.uid() OR 
        EXISTS (
            SELECT 1 FROM user_policy_links upl 
            WHERE upl.policy_id = policy_content_vectors.policy_id 
            AND upl.user_id = auth.uid() 
            AND upl.relationship_verified = true
        ) OR 
        EXISTS (
            SELECT 1 FROM user_roles ur JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = auth.uid() AND r.name = 'admin'
        )
    );
```

### Data Privacy

- **Vector Embeddings**: While embeddings obscure original text, they can still leak information
- **Metadata Storage**: Sensitive data remains in structured JSONB fields with encryption
- **Access Logging**: All vector searches are logged via existing audit mechanisms

## FAQ

### Q: Will this migration affect existing functionality?
**A**: No. The migration is designed to be backwards compatible. Existing APIs and agent functionality will continue to work while gaining new vector search capabilities.

### Q: How long does the migration take?
**A**: Migration time depends on data volume:
- Small (< 1000 policies): 5-10 minutes
- Medium (1000-10,000 policies): 30-60 minutes  
- Large (> 10,000 policies): 1-3 hours

### Q: Can I run the migration in production?
**A**: Yes, but recommended approach:
1. Run dry-run first to validate
2. Schedule during low-traffic period
3. Have rollback plan ready
4. Monitor closely post-migration

### Q: What if some documents fail to process?
**A**: The migration continues processing other documents and generates a detailed report of failures. Failed documents can be reprocessed individually after addressing issues.

### Q: How do I switch embedding models?
**A**: Update the model in `embedding_service.py` and run a re-embedding job:
```bash
python db/scripts/reprocess_embeddings.py --model all-mpnet-base-v2
```

### Q: Can I customize vector dimensions?
**A**: Yes, but requires schema changes. The current implementation uses dimension padding/truncation to support different models while maintaining database compatibility.

## Support

For migration support:
1. Check migration logs: `logs/vector_migration.log`
2. Review migration report: `db/scripts/migration_final_report_*.json`
3. Run diagnostics: `python db/scripts/run_vector_migration.py --dry-run`
4. Contact development team with specific error details

---

**Last Updated**: 2024-12-28  
**Migration Version**: 008_vector_consolidation  
**Compatibility**: PostgreSQL 11+, Python 3.8+ 