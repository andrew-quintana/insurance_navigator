# Phase 3 Implementation Prompt: Framework Integration

**Initiative**: Agent Concurrency Remediation  
**Phase**: 3 - Framework Integration  
**Timeline**: Month 1  
**Priority**: P1 - High  

## 🎯 **Objective**
Deploy centralized concurrency management framework with comprehensive monitoring and system-wide policy enforcement, validated through comprehensive integration testing.

## 📋 **Context & References**

**Read these documents first for complete context:**
- **FRACAS Analysis**: `@docs/incidents/fm_043/FRACAS_FM_043_UNBOUNDED_CONCURRENCY_AGENTS.md`
- **RFC Specification**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/rfc.md`  
- **Implementation TODO**: `@docs/initiatives/agents/2025-11-12-concurrency-remediation/todo.md`

**Prerequisites**: Phases 1 and 2 must be completed and validated before starting Phase 3.

## 🏗️ **Framework Development Tasks**

### **Task 1: Centralized Concurrency Manager**
**File**: `agents/shared/concurrency/manager.py` (new)

**Required Implementation**: Central orchestrator for all concurrency controls.

**Core Features**:
```python
class ConcurrencyManager:
    """Centralized concurrency control and resource management"""
    
    def __init__(self, config: ConcurrencyConfig):
        self.semaphores: Dict[str, asyncio.Semaphore] = {}
        self.connection_pools: Dict[str, asyncpg.Pool] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.metrics = ConcurrencyMetrics()
    
    async def acquire_semaphore(self, name: str, limit: int = 10):
        """Get or create named semaphore with specified limit"""
        
    async def get_connection_pool(self, service: str):
        """Get or create connection pool for service"""
        
    async def rate_limit(self, service: str, operation: str):
        """Apply rate limiting for service operation"""
```

**Integration Test Requirements**: `tests/integration/test_concurrency_manager_integration.py`
- Test manager coordination across multiple agent workflows simultaneously
- Test framework integration with existing Phase 1 & 2 components
- Test YAML configuration loading and hot-reloading without restarts
- Cross-component resource sharing validation and conflict resolution
- Test graceful degradation when components reach limits

### **Task 2: Configuration Management System**
**File**: `agents/shared/config/concurrency_config.py` (new)

**Required Implementation**: Centralized configuration for all concurrency limits.

**Configuration Structure**:
```python
@dataclass
class ConcurrencyConfig:
    # Semaphore limits
    default_semaphore_limit: int = 10
    stress_test_semaphore_limit: int = 5
    api_call_semaphore_limit: int = 20
    
    # Database connection pools
    rag_pool_min_size: int = 5
    rag_pool_max_size: int = 20
    
    # Rate limiting
    openai_requests_per_minute: int = 60
    anthropic_requests_per_minute: int = 50
    
    # Timeouts and monitoring
    default_operation_timeout: float = 30.0
    enable_metrics: bool = True
    alert_threshold_percentage: float = 0.8
```

**Integration Test Requirements**: `tests/integration/test_policy_enforcement_integration.py`
- Test policy enforcement across all agent types under realistic workloads
- Test policy override mechanisms in different operational scenarios
- Test policy validation during agent startup and configuration changes
- End-to-end policy compliance verification across system boundaries
- Test policy conflict resolution when multiple policies apply

### **Task 3: Advanced Monitoring and Alerting**
**File**: `agents/shared/monitoring/advanced_monitor.py` (new)

**Required Features**:
- Real-time resource utilization metrics
- Automated alerting for resource exhaustion
- Performance trend analysis
- Grafana dashboard integration

**Metrics to Track**:
- Semaphore utilization by name and service
- Connection pool usage and wait times
- Rate limiter queue lengths and rejections
- Overall system resource health

**Integration Test Requirements**: `tests/integration/test_monitoring_integration.py`
- Test monitoring integration with all agents and workflows under load
- Test alert system integration with external services and notifications
- Test dashboard data accuracy across all system components
- Test monitoring behavior and reliability under various load conditions
- Test alert escalation and recovery notification systems

### **Task 4: End-to-End Integration Validation**
**File**: `tests/integration/test_e2e_concurrency_validation.py` (new)

**Required Implementation**: Comprehensive end-to-end integration testing covering complete user journeys.

**Integration Test Requirements**: `tests/integration/test_e2e_concurrency_validation.py`
- Test complete user journeys through all agent types with realistic workloads
- Test cross-agent communication and resource sharing under concurrent load
- Test framework behavior during system startup/shutdown sequences
- Test graceful degradation scenarios and recovery procedures
- Test framework rollback and recovery procedures for deployment failures
- Validate end-to-end performance meets established baselines

## ✅ **Success Criteria**
- [ ] All agent components use centralized concurrency framework
- [ ] System-wide concurrency policies are enforced consistently
- [ ] Real-time monitoring and alerting operational
- [ ] Performance benchmarks show consistent resource usage
- [ ] Zero legacy concurrency patterns remain

## 🔧 **Implementation Guidelines**

### **Framework Design Principles**
1. **Centralization**: All concurrency controls managed centrally
2. **Configuration**: All limits configurable via YAML/environment variables
3. **Observability**: Comprehensive metrics and logging
4. **Resilience**: Graceful degradation when limits reached
5. **Performance**: Minimal overhead from framework operations

### **Migration Strategy**
1. **Incremental Rollout**: Migrate components one at a time
2. **Feature Flags**: Use feature flags for gradual enablement
3. **Rollback Plan**: Maintain ability to rollback to Phase 2 state
4. **Compatibility**: Maintain backward compatibility during transition

## 🧪 **Testing Requirements**

### **Integration Tests** (Primary Focus - Required for all components)
Comprehensive integration test suite with >95% coverage:
- `tests/integration/test_concurrency_manager_integration.py` - Framework integration
- `tests/integration/test_policy_enforcement_integration.py` - Policy system integration  
- `tests/integration/test_monitoring_integration.py` - Monitoring system integration
- `tests/integration/test_e2e_concurrency_validation.py` - End-to-end validation

### **Cross-Component Integration Testing**
- Test all components work together seamlessly under realistic conditions
- Validate resource sharing and conflict resolution across agent boundaries
- Test framework coordination during high-concurrency scenarios
- Verify monitoring captures metrics across all integrated components

### **System Integration Testing**
- Full system behavior testing under realistic traffic patterns
- Integration with external services (databases, APIs, monitoring)
- Cross-environment testing (dev, staging, production configurations)
- Framework migration testing ensuring smooth transition from Phase 2 patterns

### **Framework Migration Testing**
- Test incremental migration of each component to framework
- Validate rollback procedures work correctly
- Test compatibility between framework and legacy patterns during transition
- Performance validation throughout migration process

## 📊 **Monitoring and Alerting Setup**

### **Key Metrics**
- **Semaphore Usage**: Current/max usage by semaphore name
- **Connection Pools**: Active/total connections, wait times
- **Rate Limiters**: Requests/second, queue lengths, rejections
- **System Health**: CPU, memory, network utilization

### **Alert Conditions**
- Semaphore usage > 80% for > 5 minutes
- Connection pool exhaustion detected
- Rate limiter rejection rate > 10%
- System resource usage > 90%

### **Dashboard Requirements**
- Real-time concurrency metrics visualization
- Historical performance trends
- Resource utilization heatmaps
- Alert status and history

## 🔍 **Integration Checklist**

### **Component Migration**
- [ ] Migrate performance benchmarking to use framework
- [ ] Migrate RAG operations to use centralized pools
- [ ] Migrate LLM calls to use centralized rate limiting
- [ ] Migrate all remaining async operations to framework

### **Configuration Management**
- [ ] Create YAML configuration files for all environments
- [ ] Set up environment variable overrides
- [ ] Document configuration options
- [ ] Test configuration validation and error handling

### **Monitoring Integration**
- [ ] Set up Prometheus metrics collection
- [ ] Create Grafana dashboards
- [ ] Configure alert rules and notifications
- [ ] Test monitoring under load conditions

### **Testing and Validation**
- [ ] Run comprehensive regression testing suite
- [ ] Validate performance meets established baselines
- [ ] Test failover and error recovery scenarios
- [ ] Confirm all legacy patterns have been migrated

## 🚀 **Deployment Strategy**

### **Development Environment**
1. Deploy framework components
2. Migrate test workloads to framework
3. Validate monitoring and alerting
4. Run full regression test suite

### **Staging Environment**
1. Deploy with production-like configuration
2. Run load tests with production traffic patterns
3. Validate monitoring captures all scenarios
4. Test failover and recovery procedures

### **Production Rollout**
1. **Canary Deployment**: Limited traffic to validate framework
2. **Gradual Rollout**: Increase traffic percentage incrementally  
3. **Full Deployment**: Complete migration to framework
4. **Post-deployment Monitoring**: 24/7 monitoring for first week

## 📈 **Success Validation**

### **Technical Validation**
- Framework handles all concurrency use cases
- Resource usage stays within configured limits
- Performance meets or exceeds Phase 2 baselines
- Monitoring captures all relevant metrics

### **Operational Validation**
- Team can effectively use framework
- Configuration changes work as expected
- Alerting provides actionable notifications
- Documentation supports troubleshooting

## 🚀 **Ready to Start**
Phases 1 and 2 must be completed with performance baselines established. This phase represents the major architectural upgrade to centralized concurrency management.

**Next Phase**: Phase 4 begins after framework is fully deployed and operational for 2 weeks without issues.