# Agent Concurrency Remediation - Implementation TODO

**Initiative**: 2025-11-12 Concurrency Remediation  
**Related FRACAS**: FM-043  
**RFC Reference**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/rfc.md`  
**Last Updated**: 2025-11-12  

## 📋 **Phase Overview**

This TODO tracks the 4-phase implementation plan to remediate critical concurrency issues identified in **FM-043**. Each phase has specific deliverables, success criteria, and verification requirements.

**Reference Documents**:
- **FRACAS Analysis**: `@docs/incidents/fm_043/FRACAS_FM_043_UNBOUNDED_CONCURRENCY_AGENTS.md`
- **RFC Specification**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/rfc.md`

## 📈 **Current Progress Summary**

**Phase 1 Status**: ✅ **COMPLETE** (4/4 critical fixes completed)  
**All Critical Items COMPLETED**:
- ✅ **Semaphore Controls** - `performance_benchmark.py:200-210` - asyncio.Semaphore(10) implemented
- ✅ **Database Connection Pooling** - `database_manager.py` - DatabasePoolManager (min=5, max=20)  
- ✅ **Thread Management** - `information_retrieval/agent.py:614-627` - asyncio.timeout(60.0) implemented
- ✅ **Basic Concurrency Monitoring** - Full implementation with comprehensive test suite
  - Core monitoring system: `agents/shared/monitoring/concurrency_monitor.py` 
  - Test coverage: `agents/tests/concurrency_validation/test_concurrency_monitoring.py`

**Ready for Phase 2**: All Phase 1 success criteria have been met

## 🚨 **PHASE 1: Emergency Stabilization (Week 1)**
**Status**: ✅ **COMPLETE**  
**Goal**: Eliminate immediate resource exhaustion risks ✅  
**Prompt**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/phase_1_prompt.md`

### **Critical Fixes (P0)**

#### **1.1 Semaphore Controls for asyncio.gather()**
- [x] **File**: `agents/patient_navigator/strategy/workflow/performance_benchmark.py:200-210` ✅
- [x] **Task**: Add semaphore wrapper for `asyncio.gather(*tasks)` operations ✅
- [x] **Implementation**: Create `limited_workflow()` with semaphore controls ✅
- [x] **Limit**: Maximum 10 concurrent stress test operations ✅
- [x] **Verification**: Resource usage remains bounded during full stress test ✅
- [x] **Commit Reference**: `Addresses: FM-043` (Action Item 1) ✅

#### **1.2 Database Connection Pooling for RAG**
- [x] **File**: `agents/tooling/rag/database_manager.py` (new) ✅
- [x] **Task**: Replace per-operation connections with connection pooling ✅
- [x] **Implementation**: Create `DatabasePoolManager` class ✅
- [x] **Pool Config**: min_size=5, max_size=20 connections ✅
- [x] **Verification**: Connection count never exceeds 20 during concurrent operations ✅
- [x] **Commit Reference**: `Addresses: FM-043` (Action Item 2) ✅

#### **1.3 Thread Management Replacement**
- [x] **File**: `agents/patient_navigator/information_retrieval/agent.py:614-627` ✅
- [x] **Task**: Replace daemon threading with async task management ✅ 
- [x] **Implementation**: Use `asyncio.timeout(60.0)` and `run_in_executor()` ✅
- [x] **Timeout**: 60 second timeout for LLM calls ✅
- [x] **Verification**: No daemon threads created, proper timeout handling ✅
- [x] **Commit Reference**: `Addresses: FM-043` (Action Item 3) ✅

#### **1.4 Basic Concurrency Monitoring**
- [x] **File**: `agents/shared/monitoring/concurrency_monitor.py` (new) ✅
- [x] **Task**: Create basic resource usage monitoring ✅
- [x] **Metrics**: Semaphore usage, connection pool utilization, active tasks ✅
- [x] **Alerts**: Log warnings at 80% resource usage ✅
- [x] **Verification**: Monitoring dashboards show real-time resource usage ✅
- [x] **Commit Reference**: `Addresses: FM-043` (Monitoring setup) ✅

### **Phase 1 Success Criteria**
- [x] All `asyncio.gather()` operations use semaphore controls ✅
- [x] Database operations use connection pooling ✅
- [x] No unmanaged thread creation in agent workflows ✅
- [x] Resource usage stays within defined limits under stress testing ✅
- [x] Basic resource monitoring active ✅ (ConcurrencyMonitor implemented with comprehensive testing)

### **Phase 1 Testing Requirements**
- [ ] **Unit Tests**: Semaphore limits enforced correctly
- [ ] **Integration Tests**: Connection pooling works across RAG operations
- [ ] **Stress Tests**: System remains stable under 20 concurrent operations
- [ ] **Resource Tests**: Memory and connection usage within limits
- [x] **Monitoring Tests**: Concurrency monitoring system tests completed ✅ (`agents/tests/concurrency_validation/test_concurrency_monitoring.py`)

---

## 🔄 **PHASE 2: Pattern Modernization (Week 2-3)**
**Status**: ⏳ **PENDING PHASE 1 COMPLETION**  
**Goal**: Modernize async/await patterns and improve resource management  
**Prompt**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/phase_2_prompt.md`

### **API Modernization (P1)**

#### **2.1 Replace Deprecated get_event_loop()**
- [ ] **File**: `agents/patient_navigator/input_processing/handler.py:84`
- [ ] **Task**: Replace `asyncio.get_event_loop()` with `get_running_loop()`
- [ ] **Implementation**: Update all deprecated async API usage
- [ ] **Unit Tests**: `tests/unit/test_async_api_migration.py`
  - Test deprecated API removal
  - Test `get_running_loop()` functionality
  - Test error handling for no running loop
- [ ] **Verification**: No deprecation warnings in logs
- [ ] **Commit Reference**: `Addresses: FM-043` (Action Item 4)

#### **2.2 Migrate to Async HTTP Clients**
- [ ] **File**: `agents/patient_navigator/information_retrieval/agent.py:98`
- [ ] **Task**: Replace synchronous HTTP calls in threads with async clients
- [ ] **Implementation**: Use `httpx.AsyncClient` for all external API calls
- [ ] **Unit Tests**: `tests/unit/test_async_http_client.py`
  - Test `httpx.AsyncClient` integration
  - Test timeout handling (60s)
  - Test connection pooling behavior
  - Test error handling and retries
  - Performance comparison vs sync calls
- [ ] **Timeout**: Consistent 60s timeout for all HTTP operations
- [ ] **Verification**: All HTTP calls use async patterns
- [ ] **Commit Reference**: `Addresses: FM-043` (HTTP client migration)

#### **2.3 Async Context Manager Implementation**
- [ ] **File**: `agents/tooling/rag/core.py` (database operations)
- [ ] **Task**: Implement proper async context managers for resource cleanup
- [ ] **Implementation**: Add `__aenter__` and `__aexit__` methods
- [ ] **Unit Tests**: `tests/unit/test_async_context_managers.py`
  - Test `__aenter__` and `__aexit__` methods
  - Test resource cleanup on success
  - Test resource cleanup on exceptions
  - Test nested context managers
  - Performance impact measurement
- [ ] **Verification**: Resources properly cleaned up in all scenarios
- [ ] **Commit Reference**: `Addresses: FM-043` (Resource cleanup)

#### **2.4 Rate Limiting for External APIs**
- [ ] **File**: `agents/shared/rate_limiting/limiter.py` (new)
- [ ] **Task**: Add configurable rate limiting for external API calls
- [ ] **Limits**: OpenAI (60 req/min), Anthropic (50 req/min)
- [ ] **Implementation**: Token bucket or sliding window rate limiter
- [ ] **Unit Tests**: `tests/unit/test_rate_limiter.py`
  - Test token bucket algorithm accuracy
  - Test sliding window algorithm accuracy
  - Test rate limit enforcement under load
  - Test concurrent access to rate limiter
  - Performance benchmarks for different algorithms
  - Test configuration changes during runtime
- [ ] **Verification**: API calls respect configured rate limits
- [ ] **Commit Reference**: `Addresses: FM-043` (Rate limiting)

### **Phase 2 Success Criteria**
- [ ] All deprecated async APIs replaced with current patterns
- [ ] Consistent async/await usage across all agents
- [ ] Proper resource cleanup with async context managers
- [ ] External API calls respect rate limiting
- [ ] No synchronous HTTP calls in async context

### **Phase 2 Testing Requirements**
- [ ] **Unit Tests**: All new components have comprehensive unit test coverage (>90%)
  - `test_async_api_migration.py` - Async API modernization
  - `test_async_http_client.py` - HTTP client migration
  - `test_async_context_managers.py` - Resource cleanup patterns
  - `test_rate_limiter.py` - Rate limiting algorithms
- [ ] **Compatibility Tests**: All existing functionality works with new patterns
- [ ] **Performance Tests**: No regression in response times, measure improvements
- [ ] **Rate Limit Tests**: External APIs properly throttled under concurrent load
- [ ] **Cleanup Tests**: Resources released in error scenarios with async context managers

---

## 🏗️ **PHASE 3: Framework Integration & Integration Testing (Month 1)**
**Status**: ⏳ **PENDING PHASE 2 COMPLETION**  
**Goal**: Deploy centralized concurrency management framework and validate via comprehensive integration testing  
**Prompt**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/phase_3_prompt.md`

### **Framework Development (P1)**

#### **3.1 Centralized Concurrency Manager**
- [ ] **File**: `agents/shared/concurrency/manager.py` (new)
- [ ] **Task**: Implement centralized ConcurrencyManager class
- [ ] **Features**: Named semaphores, connection pools, rate limiters
- [ ] **Configuration**: YAML-based configuration for all limits
- [ ] **Integration Tests**: `tests/integration/test_concurrency_manager_integration.py`
  - Test manager coordination across multiple agent workflows
  - Test framework integration with existing Phase 1 & 2 components
  - Test YAML configuration loading and hot-reloading
  - Cross-component resource sharing validation
- [ ] **Verification**: All components use centralized manager
- [ ] **Commit Reference**: `Addresses: FM-043` (Framework core)

#### **3.2 System-wide Policy Enforcement**
- [ ] **File**: `agents/shared/config/concurrency_config.py` (new)
- [ ] **Task**: Define and enforce system-wide concurrency policies
- [ ] **Policies**: Default limits for all operation types
- [ ] **Enforcement**: Automatic policy application to all new components
- [ ] **Integration Tests**: `tests/integration/test_policy_enforcement_integration.py`
  - Test policy enforcement across all agent types
  - Test policy override mechanisms in different scenarios
  - Test policy validation during agent startup
  - End-to-end policy compliance verification
- [ ] **Verification**: Consistent limits across all agents
- [ ] **Commit Reference**: `Addresses: FM-043` (Policy framework)

#### **3.3 Comprehensive Monitoring and Alerting**
- [ ] **File**: `agents/shared/monitoring/advanced_monitor.py` (new)
- [ ] **Task**: Real-time concurrency monitoring with alerting
- [ ] **Metrics**: Resource utilization, performance trends, error rates
- [ ] **Alerts**: Automated alerts for resource exhaustion
- [ ] **Dashboards**: Grafana dashboards for concurrency metrics
- [ ] **Integration Tests**: `tests/integration/test_monitoring_integration.py`
  - Test monitoring integration with all agents and workflows
  - Test alert system integration with external services
  - Test dashboard data accuracy across system components
  - Test monitoring under various load conditions
- [ ] **Verification**: 24/7 monitoring with proactive alerting
- [ ] **Commit Reference**: `Addresses: FM-043` (Advanced monitoring)

#### **3.4 End-to-End Integration Validation**
- [ ] **File**: `tests/integration/test_e2e_concurrency_validation.py` (new)
- [ ] **Task**: Comprehensive end-to-end integration testing
- [ ] **Coverage**: Full agent workflows with all concurrency patterns
- [ ] **Integration Tests**: `tests/integration/test_e2e_concurrency_validation.py`
  - Test complete user journeys through all agent types
  - Test cross-agent communication under concurrent load
  - Test framework behavior during system startup/shutdown
  - Test graceful degradation scenarios
  - Test framework rollback and recovery procedures
- [ ] **CI Integration**: Automated testing on every commit
- [ ] **Baselines**: Established integration test baselines for comparison
- [ ] **Verification**: All integration scenarios pass consistently
- [ ] **Commit Reference**: `Addresses: FM-043` (Integration validation)

### **Phase 3 Success Criteria**
- [ ] Centralized concurrency management framework operational
- [ ] System-wide concurrency policies enforced
- [ ] Comprehensive monitoring and alerting in place
- [ ] Performance benchmarks show consistent resource usage
- [ ] All legacy patterns migrated to framework

### **Phase 3 Testing Requirements**
- [ ] **Integration Tests**: Comprehensive integration test suite (>95% coverage)
  - `test_concurrency_manager_integration.py` - Framework integration
  - `test_policy_enforcement_integration.py` - Policy system integration
  - `test_monitoring_integration.py` - Monitoring system integration  
  - `test_e2e_concurrency_validation.py` - End-to-end validation
- [ ] **Cross-Component Tests**: All components work together seamlessly
- [ ] **System Integration Tests**: Full system behavior under realistic conditions
- [ ] **Framework Migration Tests**: Smooth transition from Phase 2 to Phase 3 patterns

---

## 🔄 **PHASE 4: Production Validation & Stress Testing (Ongoing)**
**Status**: ⏳ **PENDING PHASE 3 COMPLETION**  
**Goal**: Validate system resilience through comprehensive stress testing and establish long-term maintenance practices  
**Prompt**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/phase_4_prompt.md`

### **Production Stress Testing & Validation (P1)**

#### **4.1 Comprehensive Load Testing Suite**
- [ ] **File**: `tests/stress/test_concurrency_load_testing.py` (new)
- [ ] **Task**: Implement comprehensive load testing for all concurrency patterns
- [ ] **Load Tests**: Multi-level stress testing suite
  - **Light Load**: 100 concurrent operations for 10 minutes
  - **Medium Load**: 500 concurrent operations for 30 minutes  
  - **Heavy Load**: 1000+ concurrent operations for 60 minutes
  - **Spike Testing**: Sudden traffic spikes (10x normal load)
  - **Endurance Testing**: Extended periods under normal load (24+ hours)
- [ ] **Metrics Validation**: Resource usage stays within defined limits under all loads
- [ ] **Verification**: System remains stable and responsive under maximum expected load
- [ ] **Commit Reference**: `Addresses: FM-043` (Load testing framework)

#### **4.2 Chaos Engineering & Failure Testing**  
- [ ] **File**: `tests/stress/test_chaos_engineering.py` (new)
- [ ] **Task**: Implement chaos engineering tests for concurrency resilience
- [ ] **Chaos Tests**: System resilience under failure conditions
  - **Database Connection Failures**: Simulate connection pool exhaustion
  - **Network Partitions**: Test rate limiter behavior during network issues
  - **Memory Pressure**: Test system behavior under memory constraints
  - **CPU Throttling**: Validate semaphore behavior under CPU limits
  - **Service Failures**: Test graceful degradation when components fail
- [ ] **Recovery Validation**: System automatically recovers from all failure scenarios
- [ ] **Verification**: Zero data loss and minimal service impact during failures
- [ ] **Commit Reference**: `Addresses: FM-043` (Chaos engineering)

#### **4.3 Performance Benchmarking & Regression Detection**
- [ ] **File**: `tests/stress/test_performance_benchmarks.py` (new)
- [ ] **Task**: Establish and monitor performance benchmarks
- [ ] **Benchmark Tests**: Continuous performance monitoring
  - **Response Time Benchmarks**: P95/P99 latency under various loads
  - **Throughput Benchmarks**: Requests per second capabilities  
  - **Resource Usage Benchmarks**: Memory, CPU, connection usage patterns
  - **Scalability Benchmarks**: Performance vs. concurrent user scaling
- [ ] **Regression Detection**: Automated alerts for performance degradation >5%
- [ ] **Verification**: Performance baselines maintained or improved over time
- [ ] **Commit Reference**: `Addresses: FM-043` (Performance benchmarking)

#### **4.4 Production Monitoring & Alerting Validation**
- [ ] **File**: `tests/stress/test_production_monitoring.py` (new)
- [ ] **Task**: Validate production monitoring under stress conditions
- [ ] **Monitoring Stress Tests**: Alert system validation under load
  - **Alert Accuracy**: Verify alerts trigger at correct thresholds under load
  - **Alert Response Time**: Validate alert delivery times during high load
  - **Dashboard Performance**: Test monitoring dashboard responsiveness
  - **Metric Collection**: Verify metric accuracy under extreme conditions
- [ ] **Production Readiness**: Full production deployment validation
- [ ] **Verification**: Monitoring system remains reliable under all conditions
- [ ] **Commit Reference**: `Addresses: FM-043` (Production monitoring validation)

### **Phase 4 Success Criteria**
- [ ] System passes all load tests up to 10x expected production traffic
- [ ] Chaos engineering tests demonstrate automatic recovery from all failure scenarios
- [ ] Performance benchmarks established and maintained (no >5% regression)
- [ ] Zero concurrency-related incidents for 90+ days under production load
- [ ] Production monitoring validated under extreme stress conditions

### **Phase 4 Testing Requirements**
- [ ] **Load Tests**: Comprehensive stress testing suite validates system resilience
  - `test_concurrency_load_testing.py` - Multi-level load testing
  - `test_chaos_engineering.py` - Failure scenario validation
  - `test_performance_benchmarks.py` - Performance regression detection
  - `test_production_monitoring.py` - Monitoring system validation
- [ ] **Stress Tests**: System remains stable under extreme conditions (10x normal load)
- [ ] **Endurance Tests**: 24+ hour continuous operation validation
- [ ] **Recovery Tests**: Automatic recovery from all failure scenarios

---

## 📊 **Overall Success Metrics**

### **Technical Metrics**
- [ ] **Zero Critical Issues**: All 8 issues from FM-043 resolved
- [ ] **Resource Efficiency**: 30%+ improvement in resource utilization
- [ ] **Performance**: No regression in response times
- [ ] **Stability**: Zero concurrency-related incidents for 30+ days

### **Process Metrics**  
- [ ] **Code Quality**: All concurrency code reviewed and tested
- [ ] **Documentation**: Complete documentation for all patterns
- [ ] **Team Readiness**: 100% team trained on new practices
- [ ] **Monitoring**: 24/7 monitoring with proactive alerting

### **Business Metrics**
- [ ] **Downtime**: Zero concurrency-related downtime
- [ ] **Cost**: Reduced infrastructure costs due to efficiency
- [ ] **Scalability**: System handles 5x traffic increase
- [ ] **Developer Velocity**: Faster development with clearer patterns

---

## 🔍 **Reference Links**

- **FRACAS Document**: `@docs/incidents/fm_043/FRACAS_FM_043_UNBOUNDED_CONCURRENCY_AGENTS.md`
- **RFC Specification**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/rfc.md`
- **Phase 1 Prompt**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/phase_1_prompt.md`
- **Phase 2 Prompt**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/phase_2_prompt.md`
- **Phase 3 Prompt**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/phase_3_prompt.md`
- **Phase 4 Prompt**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/phase_4_prompt.md`

---

**Last Updated**: 2025-11-12  
**Next Review**: 2025-11-15  
**Phase 1 Target Start**: 2025-11-12