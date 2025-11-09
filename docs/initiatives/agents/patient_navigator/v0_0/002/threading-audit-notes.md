# Threading & Concurrency Audit Notes — Initiative 002

**Date**: 2025-10-11  
**Initiative**: Threading Update & Concurrency Modernization  
**Related**: FM-038 (RAG Threading Fix), Async Conversion Initiative

---

## Quick Reference

**Main Report Location**: `/reports/threading-concurrency-report.md`

---

## Key Findings Summary

### ✅ Strengths
1. **Modern Async Foundation**: All components use `asyncio` as primary concurrency mechanism
2. **Recent Critical Fixes**: FM-038 resolved async client lifecycle conflicts in RAG system
3. **Comprehensive Testing**: Extensive concurrent testing framework in place
4. **Good Error Handling**: Most async operations have timeout protection

### ⚠️ Critical Issues

1. **Unbounded Concurrency** (ALL components)
   - No in-flight request limits
   - Risk: Memory exhaustion under load spikes
   - **Fix**: Add `asyncio.Semaphore(2 * vCPUs)` to each component

2. **Manual Threading Anti-Pattern** (Information Retrieval Agent)
   - File: `agents/patient_navigator/information_retrieval/agent.py:614-662`
   - Pattern: `threading.Thread` + `queue.Queue` for timeout protection
   - Risk: Resource leaks, race conditions
   - **Fix**: Replace with `asyncio.wait_for(loop.run_in_executor(None, ...))`

3. **No Connection Pooling** (RAG Tool)
   - File: `agents/tooling/rag/core.py:529`
   - Current: `asyncpg.connect()` per request
   - Risk: Slow connection establishment, connection exhaustion
   - **Fix**: Use `asyncpg.create_pool(min_size=2, max_size=8)`

4. **Inconsistent Timeout Values**
   - Translation: No timeout
   - Security: 100ms (simulated, will be 300ms real)
   - Orchestrator: 60s
   - RAG: 60s
   - Web Search: 5s
   - **Fix**: Standardize to target budgets (see report §4)

5. **Single-Worker ThreadPoolExecutor** (Communication Agent)
   - File: `agents/patient_navigator/output_processing/agent.py:330`
   - Pattern: `ThreadPoolExecutor(max_workers=1)` per LLM call
   - Risk: Inefficient resource utilization
   - **Fix**: Use shared pool or remove entirely (pure async)

---

## Architecture Mapping

| Target Component | Implementation | Status |
|-----------------|----------------|--------|
| **Translation Gateway** | `IntelligentTranslationRouter` | ✅ Exists, needs timeout bounds |
| **Security Agent** | `SanitizationAgent` | ⚠️ Simulated LLM, needs real implementation |
| **Tool-Calling Orchestrator** | `PatientNavigatorChatInterface` + `WorkflowPrescriptionAgent` | ✅ Exists, needs structured concurrency |
| **Retrieval Tool** | `RAGTool` | ✅ Recently fixed (FM-038), needs connection pooling |
| **Web Search (Tavily)** | `StrategyMCPTool` | ✅ Exists, needs circuit breaker |

---

## Refactor Priority Matrix

| Priority | Item | Estimated Effort | Risk Reduction |
|----------|------|------------------|----------------|
| **P0** | Add connection pooling to RAGTool | 4 hours | HIGH → LOW |
| **P0** | Remove manual threading from InformationRetrievalAgent | 3 hours | HIGH → LOW |
| **P0** | Add bounded concurrency to Orchestrator | 2 hours | HIGH → MEDIUM |
| **P1** | Add timeouts to Translation Gateway | 2 hours | HIGH → LOW |
| **P1** | Implement circuit breaker for Web Search | 3 hours | MEDIUM → LOW |
| **P1** | Replace ThreadPoolExecutor in Communication Agent | 2 hours | MEDIUM → LOW |
| **P2** | Add structured concurrency (TaskGroup) | 4 hours | MEDIUM → LOW |
| **P2** | Add Prometheus metrics | 8 hours | LOW → TRACKED |

**Total Estimated Effort**: ~28 hours (3.5 days)

---

## Target Design Budgets (Per-Component)

### Translation Gateway
```
IN_FLIGHT: 4 × vCPUs
CPU_POOL: min(4, vCPUs)
QUEUE_BOUND: 2 × in-flight
TIMEOUT: 800ms (in/out)
```

### Security Agent
```
HEURISTIC_POOL: min(4, vCPUs)
ML_POOL: min(8, vCPUs)
HEURISTIC_TIMEOUT: 20ms
ML_TIMEOUT: 300ms
TOTAL_BUDGET: 600ms
```

### Orchestrator
```
IN_FLIGHT: 2 × vCPUs
ORCHESTRATOR_POOL: min(8, vCPUs // 2)
MAX_PARALLEL_TOOLS: 3
MAX_WAVES: 2
WAVE_BUDGET: 800ms
TOTAL_BUDGET: 3000ms
```

### Retrieval Tool
```
DB_POOL_SIZE: 6-8
HTTP_CONN_POOL: 10 keepalive, 20 max
CACHE_BUDGET: 10ms
EMBEDDING_BUDGET: 150ms
KNN_BUDGET: 120ms
RERANK_BUDGET: 80ms
TOTAL_BUDGET: 200ms (P95 target)
```

### Web Search (Tavily)
```
MAX_CONCURRENT: 12-16
SEARCH_BUDGET: 800ms
PARSE_BUDGET: 120ms
CIRCUIT_BREAKER:
  - failure_threshold: 5
  - recovery_timeout: 30s
  - half_open_calls: 3
```

---

## Code Change Checklist

### Phase 1: Foundation (Week 1)
- [ ] Add `asyncpg.create_pool()` to `RAGTool.__init__()` (rag/core.py:96)
- [ ] Update `main.py:startup_event()` to initialize pool
- [ ] Replace manual threading in `InformationRetrievalAgent._call_llm()` (information_retrieval/agent.py:596)
- [ ] Add `asyncio.Semaphore` to `PatientNavigatorChatInterface.__init__()` (chat_interface.py:83)
- [ ] Update `process_message()` to use semaphore with backpressure (chat_interface.py:99)

### Phase 2: Structured Concurrency (Week 2)
- [ ] Add `asyncio.TaskGroup` to `_execute_workflows()` (chat_interface.py:185)
- [ ] Update error handling to use exception groups (`except*`)
- [ ] Add automatic cancellation on first failure

### Phase 3: Timeouts & Circuit Breakers (Week 3)
- [ ] Add timeout constants to `IntelligentTranslationRouter` (router.py:65)
- [ ] Wrap `_execute_translation()` with `asyncio.wait_for()` (router.py:637)
- [ ] Create `CircuitBreaker` class in `utils/circuit_breaker.py`
- [ ] Add circuit breaker to `StrategyMCPTool.__init__()` (mcp/strategy/core.py:22)
- [ ] Update `_perform_web_searches()` to use circuit breaker (mcp/strategy/core.py:161)

### Phase 4: Observability (Week 4)
- [ ] Create `utils/metrics.py` with Prometheus metrics
- [ ] Add metrics endpoints to `main.py`
- [ ] Add trace ID middleware to FastAPI app
- [ ] Update all components to emit metrics
- [ ] Create Grafana dashboard JSON

---

## Testing Strategy

### Unit Tests (New)
- [ ] `tests/concurrency/test_connection_pooling.py`
- [ ] `tests/concurrency/test_bounded_concurrency.py`
- [ ] `tests/concurrency/test_structured_concurrency.py`
- [ ] `tests/concurrency/test_circuit_breaker.py`

### Integration Tests (Update Existing)
- [ ] Update `test_concurrent_rag_mvp.py` to verify connection pooling
- [ ] Update `scripts/comprehensive_stress_test.py` to test backpressure
- [ ] Add chaos tests for circuit breaker behavior

### Load Tests (New)
- [ ] `scripts/load_test_baseline.py` (1× QPS, 5 req/s)
- [ ] `scripts/load_test_2x.py` (2× QPS, 10 req/s)
- [ ] `scripts/load_test_4x_stress.py` (4× QPS, 20 req/s)
- [ ] `scripts/load_test_soak.py` (2 hour run)

---

## Deployment Plan

### Stage 1: Development (Weeks 1-2)
1. Implement P0 changes in feature branch
2. Run unit tests + existing integration tests
3. Run load tests locally
4. Document performance improvements

### Stage 2: Staging (Week 3)
1. Deploy to staging environment
2. Run chaos tests (latency injection, connection exhaustion)
3. Verify degradation paths work correctly
4. Monitor metrics for 48 hours

### Stage 3: Production (Week 4)
1. Deploy during low-traffic window
2. Enable feature flag for bounded concurrency (gradual rollout)
3. Monitor error rates, latency P95/99
4. Roll back if error rate > 5% increase

---

## Success Criteria

### Performance Targets
- **P95 latency**: < 2s for retrieval-only, < 3s for retrieval+web
- **P99 latency**: < 3s for retrieval-only, < 5s for retrieval+web
- **Throughput**: 10 req/s sustained without errors
- **Memory**: No growth over 2-hour soak test

### Reliability Targets
- **Error rate**: < 1% under normal load
- **Backpressure**: 429 responses when in-flight > limit (not crashes)
- **Degradation**: Web search failures don't cascade to retrieval
- **Recovery**: Circuit breaker recovers within 30s after failures stop

---

## Related Documentation

- **Main Report**: `/reports/threading-concurrency-report.md`
- **FM-038 Fix**: `tests/fm_038/FM_038_THREADING_FIX_COMPLETE.md`
- **Async Testing**: `MVP_ASYNC_TESTING_README.md`
- **Current Status**: `docs/initiatives/agents/patient_navigator/001/current_status_update.md`

---

## Questions for Discussion

1. **Python Version**: Do we need to maintain Python 3.10 compatibility or can we use 3.11+ for `TaskGroup`?
2. **Metrics Backend**: Prometheus or alternative (OpenTelemetry)?
3. **Load Testing**: Do we have a staging environment that matches production resources?
4. **Rollback Strategy**: Feature flags or blue-green deployment?
5. **SLA Targets**: Are the proposed P95/99 targets acceptable for product requirements?

---

## Next Steps

1. **Review**: Share report with team, gather feedback (1 day)
2. **Prioritization**: Finalize P0/P1/P2 ordering (1 day)
3. **Sprint Planning**: Break down into tickets, estimate effort (1 day)
4. **Implementation**: Begin Phase 1 work (Week 1)

---

**Last Updated**: 2025-10-11  
**Next Review**: After Phase 1 completion

