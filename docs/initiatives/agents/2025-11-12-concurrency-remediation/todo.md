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

## 🚨 **PHASE 1: Emergency Stabilization (Week 1)**
**Status**: 🔄 **READY TO START**  
**Goal**: Eliminate immediate resource exhaustion risks  
**Prompt**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/phase_1_prompt.md`

### **Critical Fixes (P0)**

#### **1.1 Semaphore Controls for asyncio.gather()**
- [ ] **File**: `agents/patient_navigator/strategy/workflow/performance_benchmark.py:200-202`
- [ ] **Task**: Add semaphore wrapper for `asyncio.gather(*tasks)` operations
- [ ] **Implementation**: Create `ConcurrentWorkflowRunner` with configurable limits
- [ ] **Limit**: Maximum 10 concurrent stress test operations
- [ ] **Verification**: Resource usage remains bounded during full stress test
- [ ] **Commit Reference**: `Addresses: FM-043` (Action Item 1)

#### **1.2 Database Connection Pooling for RAG**
- [ ] **File**: `agents/tooling/rag/core.py:129-214`
- [ ] **Task**: Replace per-operation connections with connection pooling
- [ ] **Implementation**: Create `DatabasePoolManager` class
- [ ] **Pool Config**: min_size=5, max_size=20 connections
- [ ] **Verification**: Connection count never exceeds 20 during concurrent operations
- [ ] **Commit Reference**: `Addresses: FM-043` (Action Item 2)

#### **1.3 Thread Management Replacement**
- [ ] **File**: `agents/patient_navigator/information_retrieval/agent.py:614-639`
- [ ] **Task**: Replace daemon threading with async task management  
- [ ] **Implementation**: Use `asyncio.timeout()` and `asyncio.create_task()`
- [ ] **Timeout**: 60 second timeout for LLM calls
- [ ] **Verification**: No daemon threads created, proper timeout handling
- [ ] **Commit Reference**: `Addresses: FM-043` (Action Item 3)

#### **1.4 Basic Concurrency Monitoring**
- [ ] **File**: `agents/shared/monitoring/concurrency_monitor.py` (new)
- [ ] **Task**: Create basic resource usage monitoring
- [ ] **Metrics**: Semaphore usage, connection pool utilization, active tasks
- [ ] **Alerts**: Log warnings at 80% resource usage
- [ ] **Verification**: Monitoring dashboards show real-time resource usage
- [ ] **Commit Reference**: `Addresses: FM-043` (Monitoring setup)

### **Phase 1 Success Criteria**
- [ ] All `asyncio.gather()` operations use semaphore controls
- [ ] Database operations use connection pooling
- [ ] No unmanaged thread creation in agent workflows  
- [ ] Resource usage stays within defined limits under stress testing
- [ ] Basic resource monitoring active

### **Phase 1 Testing Requirements**
- [ ] **Unit Tests**: Semaphore limits enforced correctly
- [ ] **Integration Tests**: Connection pooling works across RAG operations
- [ ] **Stress Tests**: System remains stable under 20 concurrent operations
- [ ] **Resource Tests**: Memory and connection usage within limits

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
- [ ] **Verification**: No deprecation warnings in logs
- [ ] **Commit Reference**: `Addresses: FM-043` (Action Item 4)

#### **2.2 Migrate to Async HTTP Clients**
- [ ] **File**: `agents/patient_navigator/information_retrieval/agent.py:98`
- [ ] **Task**: Replace synchronous HTTP calls in threads with async clients
- [ ] **Implementation**: Use `httpx.AsyncClient` for all external API calls
- [ ] **Timeout**: Consistent 60s timeout for all HTTP operations
- [ ] **Verification**: All HTTP calls use async patterns
- [ ] **Commit Reference**: `Addresses: FM-043` (HTTP client migration)

#### **2.3 Async Context Manager Implementation**
- [ ] **File**: `agents/tooling/rag/core.py` (database operations)
- [ ] **Task**: Implement proper async context managers for resource cleanup
- [ ] **Implementation**: Add `__aenter__` and `__aexit__` methods
- [ ] **Verification**: Resources properly cleaned up in all scenarios
- [ ] **Commit Reference**: `Addresses: FM-043` (Resource cleanup)

#### **2.4 Rate Limiting for External APIs**
- [ ] **File**: `agents/shared/rate_limiting/limiter.py` (new)
- [ ] **Task**: Add configurable rate limiting for external API calls
- [ ] **Limits**: OpenAI (60 req/min), Anthropic (50 req/min)
- [ ] **Implementation**: Token bucket or sliding window rate limiter
- [ ] **Verification**: API calls respect configured rate limits
- [ ] **Commit Reference**: `Addresses: FM-043` (Rate limiting)

### **Phase 2 Success Criteria**
- [ ] All deprecated async APIs replaced with current patterns
- [ ] Consistent async/await usage across all agents
- [ ] Proper resource cleanup with async context managers
- [ ] External API calls respect rate limiting
- [ ] No synchronous HTTP calls in async context

### **Phase 2 Testing Requirements**
- [ ] **Compatibility Tests**: All existing functionality works with new patterns
- [ ] **Performance Tests**: No regression in response times
- [ ] **Rate Limit Tests**: External APIs properly throttled
- [ ] **Cleanup Tests**: Resources released in error scenarios

---

## 🏗️ **PHASE 3: Framework Integration (Month 1)**
**Status**: ⏳ **PENDING PHASE 2 COMPLETION**  
**Goal**: Deploy centralized concurrency management framework  
**Prompt**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/phase_3_prompt.md`

### **Framework Development (P1)**

#### **3.1 Centralized Concurrency Manager**
- [ ] **File**: `agents/shared/concurrency/manager.py` (new)
- [ ] **Task**: Implement centralized ConcurrencyManager class
- [ ] **Features**: Named semaphores, connection pools, rate limiters
- [ ] **Configuration**: YAML-based configuration for all limits
- [ ] **Verification**: All components use centralized manager
- [ ] **Commit Reference**: `Addresses: FM-043` (Framework core)

#### **3.2 System-wide Policy Enforcement**
- [ ] **File**: `agents/shared/config/concurrency_config.py` (new)
- [ ] **Task**: Define and enforce system-wide concurrency policies
- [ ] **Policies**: Default limits for all operation types
- [ ] **Enforcement**: Automatic policy application to all new components
- [ ] **Verification**: Consistent limits across all agents
- [ ] **Commit Reference**: `Addresses: FM-043` (Policy framework)

#### **3.3 Comprehensive Monitoring and Alerting**
- [ ] **File**: `agents/shared/monitoring/advanced_monitor.py` (new)
- [ ] **Task**: Real-time concurrency monitoring with alerting
- [ ] **Metrics**: Resource utilization, performance trends, error rates
- [ ] **Alerts**: Automated alerts for resource exhaustion
- [ ] **Dashboards**: Grafana dashboards for concurrency metrics
- [ ] **Verification**: 24/7 monitoring with proactive alerting
- [ ] **Commit Reference**: `Addresses: FM-043` (Advanced monitoring)

#### **3.4 Performance Regression Testing Suite**
- [ ] **File**: `tests/performance/concurrency_regression.py` (new)
- [ ] **Task**: Automated performance regression testing
- [ ] **Coverage**: All concurrency patterns and resource limits
- [ ] **CI Integration**: Automated testing on every commit
- [ ] **Baselines**: Established performance baselines for comparison
- [ ] **Verification**: No performance regression detected
- [ ] **Commit Reference**: `Addresses: FM-043` (Regression testing)

### **Phase 3 Success Criteria**
- [ ] Centralized concurrency management framework operational
- [ ] System-wide concurrency policies enforced
- [ ] Comprehensive monitoring and alerting in place
- [ ] Performance benchmarks show consistent resource usage
- [ ] All legacy patterns migrated to framework

### **Phase 3 Testing Requirements**
- [ ] **Framework Tests**: Centralized manager handles all use cases
- [ ] **Policy Tests**: System-wide limits properly enforced
- [ ] **Monitoring Tests**: All metrics collected and alerts functional
- [ ] **Regression Tests**: Performance within established baselines

---

## 🔄 **PHASE 4: Long-term Maintenance (Ongoing)**
**Status**: ⏳ **PENDING PHASE 3 COMPLETION**  
**Goal**: Maintain and evolve concurrency best practices  
**Prompt**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/phase_4_prompt.md`

### **Maintenance Operations (P2)**

#### **4.1 Regular Concurrency Audits**
- [ ] **Schedule**: Quarterly concurrency pattern audits
- [ ] **Scope**: All agent workflows and shared components
- [ ] **Process**: Automated scanning + manual review
- [ ] **Documentation**: Audit reports with recommendations
- [ ] **Verification**: Zero critical concurrency issues found
- [ ] **Commit Reference**: `Addresses: FM-043` (Audit process)

#### **4.2 Performance Optimization**
- [ ] **Process**: Continuous performance optimization based on metrics
- [ ] **Triggers**: Performance degradation alerts
- [ ] **Analysis**: Root cause analysis of performance issues  
- [ ] **Implementation**: Optimize based on real-world usage patterns
- [ ] **Verification**: Performance improvements over baseline
- [ ] **Commit Reference**: `Addresses: FM-043` (Performance optimization)

#### **4.3 Team Training and Documentation**
- [ ] **Training**: Team training on async best practices
- [ ] **Documentation**: Comprehensive concurrency guidelines
- [ ] **Code Review**: Updated review checklist for concurrency patterns
- [ ] **Knowledge Base**: Internal wiki with troubleshooting guides
- [ ] **Verification**: Team proficiency assessment passed
- [ ] **Commit Reference**: `Addresses: FM-043` (Knowledge transfer)

#### **4.4 Continuous Improvement Process**
- [ ] **Feedback Loop**: Regular review of concurrency framework effectiveness
- [ ] **Updates**: Framework updates based on new async patterns
- [ ] **Research**: Monitor industry best practices and new libraries
- [ ] **Evolution**: Continuous evolution of concurrency practices
- [ ] **Verification**: Framework stays current with best practices
- [ ] **Commit Reference**: `Addresses: FM-043` (Continuous improvement)

### **Phase 4 Success Criteria**
- [ ] Quarterly concurrency audits completed
- [ ] Team trained on best practices  
- [ ] Performance continuously optimized
- [ ] Zero concurrency-related incidents for 90+ days
- [ ] Framework evolution process established

### **Phase 4 Testing Requirements**
- [ ] **Audit Tests**: Automated scanning tools function correctly
- [ ] **Training Tests**: Team knowledge assessments passed
- [ ] **Process Tests**: Continuous improvement process validated
- [ ] **Incident Tests**: Zero concurrency-related production issues

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