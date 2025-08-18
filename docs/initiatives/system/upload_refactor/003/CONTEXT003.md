# Accessa Ingestion Context (003 Worker Refactor) — v1.0

**Purpose**: Single source of truth for implementing the 003 Worker Refactor iteration - a local-first development approach with Docker-based testing environments, building upon the 002 BaseWorker architecture while addressing critical infrastructure validation and deployment verification gaps.

**Authoritative decisions captured from 003 iteration requirements on 2025-08-18.**

---

## 0) TL;DR (What's changing and why)

- **Local-First Development**: Complete Docker-based local environment replicating production architecture before any deployment
- **Infrastructure Validation**: Automated validation framework preventing deployment configuration failures experienced in 002
- **Extended Phase Structure**: 8 phases instead of 4, with proper validation and testing at each stage
- **Enhanced Monitoring**: Comprehensive observability and alerting throughout development and production
- **Deployment Safety**: Automated rollback procedures and verification against local baseline

---

## 1) Context & Goals from 002 Lessons

**002 Failure Analysis:**
- No functional worker processes despite "successful" deployment
- Testing disconnected from real deployment behavior  
- Infrastructure configuration gaps preventing actual processing
- Silent failures in state machine transitions and buffer operations

**Core Goals for 003:**
1. **Local validation precedes deployment** - 100% pipeline functionality validated locally first
2. **Infrastructure configuration management** - Automated validation and rollback procedures
3. **Comprehensive monitoring and observability** - No silent failures, immediate detection
4. **Deployment verification** - Objective validation that deployed system matches local baseline

---

## 2) Development Flow (Local-First Approach)

### Development Phases
```
Local Environment → Infrastructure Validation → Production Deployment
     (Phases 1-4)        (Phase 5)              (Phases 6-8)
```

### Phase Progression Requirements
1. **Phases 1-4**: Complete local validation with 100% test coverage
2. **Phase 5**: Infrastructure deployment with automated validation
3. **Phases 6-8**: Application deployment with verification against local baseline

### Validation Gates
- **Phase Completion**: Objective validation criteria must be met
- **Local Baseline**: All functionality validated in Docker environment
- **Deployment Verification**: Production behavior matches local environment
- **Rollback Capability**: Automated rollback if validation fails

---

## 3) Local Development Environment Architecture

### Docker Compose Stack
```
┌─────────────────────────────────────────────────────────────────┐
│                         Docker Compose Stack                    │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   API Server    │   BaseWorker    │        Dependencies         │
│   (FastAPI)     │   (Unified)     │                             │
│   - Webhooks    │   - State Mgmt  │   - Postgres + Vector Ext   │
│   - Job Status  │   - Buffer Ops  │   - Supabase Local          │
│   - Health      │   - External    │   - Mock LlamaParse         │
│                 │     Services    │   - Mock OpenAI             │
│                 │                 │   - Monitoring Dashboard    │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### Service Configuration
**Core Services:**
- **postgres**: pgvector/pgvector:pg15 with buffer tables and vector extension
- **supabase-storage**: Local storage simulation with proper access controls
- **api-server**: FastAPI with webhook endpoints and job status API
- **base-worker**: Unified worker with state machine and buffer operations
- **mock-llamaparse**: Deterministic parsing with webhook callbacks
- **mock-openai**: Deterministic embeddings with rate limiting simulation
- **monitoring**: Real-time dashboard and alerting system

### Local Environment Setup
```bash
# Quick setup - must complete in <30 minutes
./scripts/setup-local-env.sh

# Comprehensive testing - must complete in <5 minutes
./scripts/run-local-tests.sh

# Environment health validation
./scripts/validate-local-environment.sh
```

---

## 4) State Machine (Enhanced from 002)

### Status Values (Identical to 002)
```
uploaded → parse_queued → parsed → parse_validated → chunking → chunks_stored → embedding_queued → embedding_in_progress → embeddings_stored → complete
```

**Error Terminals:** `failed_parse`, `failed_chunking`, `failed_embedding`

### Enhanced Monitoring and Logging
- **Correlation IDs**: Every processing stage tracked with unique correlation ID
- **State Transition Logging**: Comprehensive logging for every status change
- **Progress Tracking**: Real-time progress updates with buffer count validation
- **Error Classification**: Transient, permanent, and retryable error classification

### Local Validation Requirements
- All state transitions must be validated in local environment
- Buffer operations tested with real database constraints
- External service integration tested with both mock and real APIs
- Complete pipeline tested with realistic document workloads

---

## 5) Data Model (Enhanced Buffer Strategy)

### upload_jobs (Enhanced Monitoring)
```sql
CREATE TABLE upload_jobs (
    job_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    document_id UUID NOT NULL,
    status TEXT NOT NULL CHECK (status IN (
        'uploaded', 'parse_queued', 'parsed', 'parse_validated', 
        'chunking', 'chunks_stored', 'embedding_queued', 
        'embedding_in_progress', 'embeddings_stored', 'complete',
        'failed_parse', 'failed_chunking', 'failed_embedding'
    )),
    raw_path TEXT NOT NULL,
    parsed_path TEXT,
    parsed_sha256 TEXT,
    chunks_version TEXT NOT NULL DEFAULT 'markdown-simple@1',
    embed_model TEXT DEFAULT 'text-embedding-3-small',
    embed_version TEXT DEFAULT '1',
    progress JSONB DEFAULT '{}',
    retry_count INT DEFAULT 0,
    last_error JSONB,
    webhook_secret TEXT,
    -- Enhanced monitoring fields
    correlation_id UUID DEFAULT gen_random_uuid(),
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Enhanced indexing for monitoring
CREATE INDEX idx_upload_jobs_correlation ON upload_jobs (correlation_id);
CREATE INDEX idx_upload_jobs_processing_time ON upload_jobs (processing_started_at, processing_completed_at);
```

### Buffer Tables (Identical to 002 with Enhanced Monitoring)
- `document_chunk_buffer`: Staging for chunks with deterministic chunk_id
- `document_vector_buffer`: Staging for embeddings with batch tracking
- Enhanced with monitoring fields for local development and debugging

---

## 6) Mock Service Strategy

### Mock LlamaParse Service
**Behavior:**
- Realistic processing delays (2-5 seconds configurable)
- Deterministic content generation based on document_id
- Webhook callback with proper HMAC signing
- Error injection capability for failure testing

**Implementation:**
```python
# Configurable mock responses
MOCK_PROCESSING_DELAY = os.getenv("MOCK_LLAMAPARSE_DELAY", "2")
MOCK_FAILURE_RATE = float(os.getenv("MOCK_LLAMAPARSE_FAILURE_RATE", "0.0"))

# Deterministic content generation
def generate_mock_content(document_id: str) -> str:
    return f"""# Mock Document {document_id}
    
This is deterministic mock content for testing.
Content is based on document_id for reproducible testing.

## Section 1
Test content that will generate consistent chunks.

## Section 2
Additional content for multi-chunk testing scenarios.
"""
```

### Mock OpenAI Service
**Behavior:**
- Deterministic embedding generation using document content hash
- Rate limiting simulation with configurable delays
- Batch processing support up to 256 vectors
- Cost tracking simulation for development

**Implementation:**
```python
# Deterministic embedding generation
def generate_mock_embedding(text: str) -> List[float]:
    text_hash = hashlib.md5(text.encode()).hexdigest()
    np.random.seed(int(text_hash[:8], 16))
    return np.random.normal(0, 1, 1536).tolist()
```

---

## 7) Infrastructure Validation Framework

### Deployment Validation Components
**Configuration Validation:**
- Render service configuration validation against local environment
- Environment variable and secrets validation
- Database schema and performance validation
- Storage configuration and access control validation

**Health Check Framework:**
```python
class DeploymentValidator:
    async def validate_complete_deployment(self) -> Dict[str, bool]:
        results = {}
        results["database"] = await self._validate_database()
        results["api_server"] = await self._validate_api_server()
        results["worker_process"] = await self._validate_worker_process()
        results["external_services"] = await self._validate_external_services()
        results["storage"] = await self._validate_storage()
        return results
```

### Automated Rollback System
**Rollback Triggers:**
- Infrastructure validation failure
- Application deployment verification failure
- Production health check failure
- Performance degradation beyond threshold

**Rollback Procedures:**
- Automated infrastructure state restoration
- Database rollback to known good state
- Service version rollback with health validation
- Monitoring and alerting during rollback operations

---

## 8) Enhanced BaseWorker Implementation

### Core Architecture (Enhanced from 002)
```python
class BaseWorker:
    """Enhanced BaseWorker with comprehensive monitoring"""
    
    def __init__(self, config):
        self.db = DatabaseManager(config.database_url)
        self.storage = StorageManager(config.storage_config)
        self.llamaparse = LlamaParseClient(config.llamaparse_config)
        self.openai = OpenAIClient(config.openai_config)
        self.logger = StructuredLogger("base_worker")
        self.metrics = ProcessingMetrics()  # Enhanced metrics collection
        
    async def process_jobs_continuously(self):
        """Main worker loop with enhanced health monitoring"""
        while True:
            try:
                job = await self._get_next_job()
                if job:
                    await self._process_single_job_with_monitoring(job)
                else:
                    await asyncio.sleep(5)
            except Exception as e:
                self.logger.error("Worker loop error", error=str(e))
                await asyncio.sleep(10)
```

### Enhanced Error Handling
**Error Classification:**
- **TransientError**: Network timeouts, rate limits (retry with backoff)
- **PermanentError**: Invalid content, authentication failures (no retry)
- **RecoverableError**: External service outages (retry with circuit breaker)

**Monitoring Integration:**
- Real-time error rate monitoring
- Error pattern detection and alerting
- Correlation ID tracking for debugging
- Performance impact measurement

---

## 9) Comprehensive Testing Strategy

### Local Testing Framework
**Unit Testing:**
```bash
# State machine transition testing
pytest backend/tests/unit/test_state_machine.py -v

# Buffer operation testing  
pytest backend/tests/unit/test_buffer_operations.py -v

# External service integration testing
pytest backend/tests/unit/test_external_services.py -v
```

**Integration Testing:**
```bash
# End-to-end pipeline testing
python backend/tests/e2e/test_complete_pipeline.py

# Mock service integration testing
python backend/tests/integration/test_mock_services.py

# Real external API testing (with test credentials)
python backend/tests/integration/test_real_apis.py
```

**Performance Testing:**
```bash
# Large document processing
python backend/tests/performance/test_large_documents.py

# Concurrent processing
python backend/tests/performance/test_concurrent_workers.py

# Database performance under load
python backend/tests/performance/test_database_load.py
```

### Testing Requirements
- **100% State Machine Coverage**: Every transition tested in local environment
- **Realistic Workloads**: Testing with actual document sizes and complexities
- **Failure Scenarios**: External service outages, database failures, network issues
- **Performance Baselines**: Establishes benchmarks for production comparison

---

## 10) Monitoring and Observability

### Local Development Monitoring
**Real-time Dashboard:**
- Processing pipeline status and health
- Buffer table growth and cleanup monitoring
- External service health and performance
- Error rates and failure patterns

**Structured Logging:**
```python
# Enhanced logging with correlation IDs
self.logger.info(
    "Processing stage completed",
    job_id=str(job_id),
    correlation_id=str(correlation_id),
    stage="chunking",
    duration_seconds=duration,
    chunks_generated=chunk_count
)
```

### Production Monitoring
**Health Checks:**
- Service health validation every 30 seconds
- Processing pipeline health validation
- Database performance monitoring
- External service dependency monitoring

**Alerting Systems:**
- Processing failure detection and escalation
- Performance degradation monitoring
- Infrastructure health monitoring
- Security incident detection

---

## 11) Deployment Safety and Verification

### Deployment Phases
**Phase 5: Infrastructure Deployment**
- Automated infrastructure deployment with validation
- Configuration validation against local baseline
- Health check validation for all services
- Rollback capability if validation fails

**Phase 6: Application Deployment** 
- Application deployment with verification
- Functionality validation against local baseline
- Performance benchmark validation
- Production readiness verification

**Phase 7-8: Production Integration**
- Gradual production rollout with monitoring
- SLA compliance validation
- Operational excellence establishment
- Long-term reliability and maintenance

### Verification Procedures
```bash
# Infrastructure validation
python infrastructure/validation/deployment_validator.py config/production.yaml

# Application functionality verification
python scripts/validate-production-deployment.py

# Production smoke testing
python scripts/production-smoke-tests.py
```

---

## 12) Success Criteria and KPIs

### Local Development KPIs
- **Environment Setup Time**: <30 minutes for complete pipeline setup
- **Test Execution Time**: <5 minutes for complete end-to-end test
- **Local Pipeline Reliability**: >99% success rate in local environment
- **Issue Detection**: 100% of critical failures detected locally

### Production KPIs
- **Deployment Verification**: 100% validation against local baseline
- **Processing Pipeline Reliability**: >98% success rate
- **Recovery Time**: <5 minutes for automatic failure recovery
- **Processing Predictability**: <10% variance in processing times
- **Operational Complexity Reduction**: 50% compared to 002

### Development Velocity KPIs
- **Development Iteration Speed**: 50% faster through local testing
- **Issue Resolution Time**: 75% reduction through local debugging
- **Deployment Confidence**: 100% confidence through local validation
- **Knowledge Transfer**: Complete documentation and training materials

---

## 13) Security and Compliance (Enhanced)

### Local Development Security
- **Secret Management**: Local secrets isolated from production
- **Access Control**: Development environment access controls
- **Data Protection**: Test data protection and privacy
- **Audit Logging**: Comprehensive logging for development activities

### Production Security
- **Infrastructure Security**: Automated security configuration validation
- **Access Control**: Role-based access control with monitoring
- **Data Encryption**: Encryption in transit and at rest
- **Compliance Monitoring**: Continuous compliance validation and reporting

---

## 14) Future Migration Considerations

### Cloud Platform Readiness
**Enhanced from 002:**
- **Container Orchestration**: Docker compose translates to Kubernetes manifests
- **Infrastructure as Code**: All configuration version controlled and validated
- **Service Mesh**: Local networking patterns support service mesh migration
- **Observability**: Monitoring and logging compatible with cloud platforms

### Technology Evolution
**Prepared for Future Enhancements:**
- **Multi-model Support**: Buffer architecture supports multiple embedding models
- **Advanced Processing**: State machine extensible for additional processing stages
- **Queue Services**: Database polling replaceable with managed queue services
- **Serverless**: BaseWorker stages convertible to cloud functions

---

## 15) Operational Excellence

### Incident Response
**Comprehensive Procedures:**
- **Detection**: Automated monitoring and alerting for all failure scenarios
- **Escalation**: Clear escalation paths and communication procedures
- **Resolution**: Documented troubleshooting and recovery procedures
- **Post-incident**: Root cause analysis and improvement procedures

### Capacity Planning
**Proactive Management:**
- **Resource Monitoring**: Continuous monitoring and capacity planning
- **Scaling Procedures**: Automated and manual scaling procedures
- **Performance Optimization**: Regular performance review and optimization
- **Cost Management**: Cost monitoring and optimization procedures

### Knowledge Management
**Comprehensive Documentation:**
- **Operational Runbooks**: Complete procedures for all operational tasks
- **Troubleshooting Guides**: Comprehensive debugging and resolution guides
- **Training Materials**: Complete training materials for all team members
- **Best Practices**: Documented best practices and lessons learned

---

*End of Context 003*