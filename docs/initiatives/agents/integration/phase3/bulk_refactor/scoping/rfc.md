# RFC: Agent Integration Infrastructure Refactor

## Meta
- **Status**: Draft
- **Author**: System Architecture Team
- **Created**: 2025-09-15
- **Updated**: 2025-09-15

## Abstract
This RFC proposes a comprehensive refactor of the agent integration infrastructure to address five critical areas: import management, API reliability, data integrity, RAG performance tuning, and observability enhancement. The changes will establish a robust foundation for multi-user production deployments.

## Motivation
Current agent integration infrastructure has several critical issues:

1. **Import Failures**: Persistent psycopg2 and agents directory module import errors causing runtime instability
2. **Silent API Failures**: Llamaparse calls defaulting to mock implementations in production, masking real issues
3. **Data Integrity Issues**: Lack of proper document row duplication for multi-user scenarios where different users upload the same document
4. **Suboptimal RAG Performance**: Default similarity thresholds may be filtering out relevant results (note: performance speed is non-critical)
5. **Poor Observability**: Limited visibility into RAG performance characteristics

## Detailed Design

### 1. Import Management Restructuring
**Problem**: Circular imports and missing dependencies causing runtime failures.

**Solution**: 
- Implement proper dependency injection pattern
- Consolidate database connection management
- Create explicit module initialization order
- Add import validation in CI/CD pipeline

**Implementation**:
```python
# New structure
from core.database import DatabaseManager
from agents.base import AgentBase
from integrations.llamaparse import LlamaParseClient

class AgentIntegrationManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.llamaparse = LlamaParseClient()
```

### 2. Production API Reliability
**Problem**: Mock fallbacks hiding production API failures.

**Solution**:
- Remove mock fallbacks in production environment
- Implement proper error handling with UUID traceability
- Add retry logic with exponential backoff
- Surface meaningful error messages to users

**Implementation**:
```python
class LlamaParseClient:
    def parse_document(self, document_id: str) -> ParseResult:
        try:
            result = self._make_api_call(document_id)
            return result
        except APIError as e:
            error_uuid = generate_uuid()
            logger.error(f"LlamaParse API failure {error_uuid}: {e}")
            raise UserFacingError(f"Document processing failed. Reference: {error_uuid}")
```

### 3. Multi-User Data Integrity
**Problem**: Current system prevents multiple users from uploading the same document, lacking proper document row duplication.

**Solution**:
- Implement document row duplication for multi-user scenarios
- When duplicate content is detected, create new document row for the new user
- Copy all processing data from existing document while updating user_id
- Preserve existing document chunks and processing results
- Maintain RAG functionality through proper table relationships

**Implementation**:
```sql
-- Detect existing document by content hash
SELECT id, * FROM documents WHERE content_hash = %s LIMIT 1;

-- Create new document row for new user with same processing data
INSERT INTO documents (user_id, filename, content_hash, processed_content, metadata, created_at)
SELECT %s, filename, content_hash, processed_content, metadata, NOW()
FROM documents WHERE id = %s;

-- RAG queries will work normally as they reference documents table first
SELECT dc.* FROM document_chunks dc 
JOIN documents d ON dc.document_id = d.id 
WHERE d.user_id = %s;
```

### 4. RAG Performance Optimization
**Problem**: Default similarity threshold potentially too restrictive.

**Solution**:
- Update default threshold from current value to 0.3
- Make threshold configurable per user/context
- Implement A/B testing framework for threshold optimization

### 5. Enhanced Observability
**Problem**: No visibility into RAG similarity score distributions.

**Solution**:
- Add INFO-level logging with similarity histograms
- Include operation UUIDs for traceability
- Create developer-friendly output format

**Implementation**:
```python
def log_similarity_histogram(similarities: List[float], operation_uuid: str):
    bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    hist = np.histogram(similarities, bins=bins)
    logger.info(f"RAG Similarity Distribution [{operation_uuid}]: " +
                " ".join([f"{bins[i]:.1f}-{bins[i+1]:.1f}:{count}" 
                         for i, count in enumerate(hist[0])]))
```

## Implementation Plan

### Phase 1: Import Management (Week 1)
- Audit current import dependencies
- Implement dependency injection pattern
- Add CI/CD import validation
- Test in staging environment

### Phase 2: API Reliability (Week 2)
- Remove production mock fallbacks
- Implement error handling with UUIDs
- Add retry mechanisms
- Update error messaging

### Phase 3: Data Integrity (Week 2)
- Update duplicate detection logic
- Create database indexes
- Migrate existing data if needed
- Add user isolation tests

### Phase 4: RAG Optimization (Week 3)
- Update similarity threshold configuration
- Implement histogram logging
- Add performance monitoring
- Validate retrieval quality

### Phase 5: Testing & Deployment (Week 4)
- Comprehensive integration testing
- Performance benchmarking
- Production deployment
- Monitor and iterate

## Alternatives Considered

1. **Gradual Migration**: Rejected due to complexity of managing mixed states
2. **Mock Fallback with Alerts**: Rejected as it doesn't solve the underlying reliability issue
3. **Global Similarity Threshold**: Rejected in favor of configurable per-context thresholds

## Backwards Compatibility
- API contracts remain unchanged
- Database schema changes are additive
- Configuration changes are opt-in initially
- Deprecated mock behavior will be removed after migration period

## Security Considerations
- User isolation must be maintained in all database operations
- Error messages must not leak sensitive information
- UUID generation must be cryptographically secure
- Logging must not include PII

## Monitoring & Metrics
- Import failure rates
- API success/failure rates with breakdown by error type
- RAG performance metrics (latency, relevance scores)
- Similarity histogram analysis
- Error UUID tracking for support correlation

## Success Criteria
- Zero import-related runtime errors
- 99.9% API reliability (excluding upstream failures)
- Improved RAG retrieval quality metrics
- Developer productivity improvement through better observability
- Reduced support tickets related to document processing failures