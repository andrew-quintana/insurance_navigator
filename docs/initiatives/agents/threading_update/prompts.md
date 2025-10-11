# Threading Update Initiative - Prompts

> **Reference Documents**: This prompts document should be used in conjunction with:
> - [`README.md`](./README.md) - Initiative overview and phase summary
> - [`prd.md`](./prd.md) - Product Requirements Document with functional/non-functional requirements
> - [`rfc.md`](./rfc.md) - RFC document (to be completed in Phase 1)
> - [`phase1-research-plan.md`](./phase1-research-plan.md) - Detailed research plan for Phase 1
> - [`phase2-implementation-plan.md`](./phase2-implementation-plan.md) - Implementation strategy for Phase 2
> - [`phase3-testing-plan.md`](./phase3-testing-plan.md) - Testing strategy for Phase 3
> - [`phase4-deployment-plan.md`](./phase4-deployment-plan.md) - Deployment strategy for Phase 4
> - [`phased-todo.md`](./phased-todo.md) - Comprehensive task tracking for all phases

## Phase 1: Research & Analysis Prompts

### Research Prompt 1: Async/Await Best Practices
```
Research Python async/await best practices for web applications, specifically:

1. Best practices for async/await patterns in Python
2. FastAPI async integration patterns
3. HTTP client connection pooling strategies
4. Concurrency control patterns (semaphores, rate limiting)
5. Async error handling best practices
6. Circuit breaker patterns for async systems

Focus on:
- Performance optimization
- Resource management
- Error handling
- Scalability patterns
- Integration with existing frameworks

Document findings with code examples and implementation recommendations.

Reference: See [phase1-research-plan.md](./phase1-research-plan.md) for detailed research areas and [rfc.md](./rfc.md) for documenting findings.
```

### Research Prompt 2: Current Implementation Analysis
```
Analyze the current threading implementation in the RAG system:

1. Examine `agents/tooling/rag/core.py` threading logic
2. Map the current flow and dependencies
3. Identify specific problem areas in `_generate_embedding()` method
4. Document current architecture and threading logic
5. Identify integration points with service manager
6. Analyze observability and monitoring integration

Focus on:
- Threading patterns and issues
- Resource contention points
- Error handling gaps
- Performance bottlenecks
- Integration complexity

Provide detailed analysis with code references and problem identification.

Reference: See [phase1-research-plan.md](./phase1-research-plan.md) for code analysis tasks and [rfc.md](./rfc.md) for documenting current state analysis.
```

### Research Prompt 3: Architecture Design
```
Design a new async architecture for the RAG system:

1. Define async service architecture
2. Specify HTTP client and connection pooling design
3. Design concurrency control mechanisms
4. Plan error handling and circuit breaker integration
5. Define monitoring and observability integration
6. Create migration strategy from threading to async

Focus on:
- Clean architecture principles
- Performance optimization
- Maintainability
- Scalability
- Backward compatibility

Provide architectural diagrams and implementation specifications.

Reference: See [phase1-research-plan.md](./phase1-research-plan.md) for architecture design tasks and [rfc.md](./rfc.md) for documenting proposed solution.
```

## Phase 2: Implementation Prompts

### Implementation Prompt 1: HTTP Client Setup
```
Implement async HTTP client with connection pooling:

1. Set up httpx or aiohttp client
2. Configure connection pooling
3. Implement timeout and retry logic
4. Add rate limiting and throttling
5. Test HTTP client performance

Requirements:
- Async/await pattern
- Connection reuse
- Configurable timeouts
- Error handling
- Performance monitoring

Provide implementation with configuration options and testing.

Reference: See [phase2-implementation-plan.md](./phase2-implementation-plan.md) for Task 1 details and [phased-todo.md](./phased-todo.md) for implementation tracking.
```

### Implementation Prompt 2: Concurrency Control
```
Implement concurrency control for async operations:

1. Implement semaphores for request limiting
2. Add circuit breaker pattern
3. Configure resource limits
4. Add monitoring and metrics
5. Test under load

Requirements:
- Configurable limits
- Graceful degradation
- Monitoring integration
- Error handling
- Performance metrics

Provide implementation with configuration and monitoring.

Reference: See [phase2-implementation-plan.md](./phase2-implementation-plan.md) for Task 2 details and [phased-todo.md](./phased-todo.md) for implementation tracking.
```

### Implementation Prompt 3: RAG System Refactor
```
Refactor RAG system to use async/await:

1. Update `_generate_embedding()` method to async
2. Remove threading and queue logic
3. Implement async/await pattern
4. Update error handling
5. Test functionality

Requirements:
- Complete async conversion
- Maintain existing interfaces
- Improve error handling
- Add performance monitoring
- Ensure backward compatibility

Provide refactored code with tests and documentation.

Reference: See [phase2-implementation-plan.md](./phase2-implementation-plan.md) for Task 3 details and [phased-todo.md](./phased-todo.md) for implementation tracking.
```

## Phase 3: Testing Prompts

### Testing Prompt 1: Unit Testing
```
Create comprehensive unit tests for async RAG system:

1. Test async embedding generation
2. Test connection pooling behavior
3. Test concurrency limits
4. Test error handling
5. Test timeout and retry logic

Requirements:
- Async test patterns
- Mock external dependencies
- Test error scenarios
- Performance assertions
- Coverage requirements

Provide test suite with examples and assertions.

Reference: See [phase3-testing-plan.md](./phase3-testing-plan.md) for unit testing strategy and [phased-todo.md](./phased-todo.md) for testing tracking.
```

### Testing Prompt 2: Load Testing
```
Create load testing suite for concurrent request handling:

1. Test single request performance
2. Test 2-3 concurrent requests
3. Test 5-10 concurrent requests (hanging scenario)
4. Test 10+ concurrent requests (stress test)
5. Test resource usage under load

Requirements:
- Async load testing
- Performance metrics
- Resource monitoring
- Error rate tracking
- Success rate validation

Provide load testing script with metrics and reporting.

Reference: See [phase3-testing-plan.md](./phase3-testing-plan.md) for load testing scenarios and [phased-todo.md](./phased-todo.md) for testing tracking.
```

### Testing Prompt 3: Integration Testing
```
Create integration tests for async RAG system:

1. Test RAG system integration
2. Test service manager compatibility
3. Test health checks
4. Test observability integration
5. Test error propagation

Requirements:
- End-to-end testing
- Service integration
- Monitoring validation
- Error handling verification
- Performance validation

Provide integration test suite with scenarios and assertions.

Reference: See [phase3-testing-plan.md](./phase3-testing-plan.md) for integration testing strategy and [phased-todo.md](./phased-todo.md) for testing tracking.
```

## Phase 4: Deployment Prompts

### Deployment Prompt 1: Production Deployment
```
Deploy async RAG system to production:

1. Prepare deployment package
2. Execute production deployment
3. Monitor deployment health
4. Verify service startup
5. Test basic functionality

Requirements:
- Zero-downtime deployment
- Health monitoring
- Rollback capability
- Performance validation
- Error monitoring

Provide deployment script with monitoring and validation.

Reference: See [phase4-deployment-plan.md](./phase4-deployment-plan.md) for deployment steps and [phased-todo.md](./phased-todo.md) for deployment tracking.
```

### Deployment Prompt 2: Production Validation
```
Validate async RAG system in production:

1. Test concurrent requests
2. Monitor performance metrics
3. Validate fix effectiveness
4. Check for regression issues
5. Monitor for 24 hours

Requirements:
- Production testing
- Performance monitoring
- Error rate validation
- Stability verification
- Long-term monitoring

Provide validation script with monitoring and reporting.

Reference: See [phase4-deployment-plan.md](./phase4-deployment-plan.md) for validation steps and [phased-todo.md](./phased-todo.md) for deployment tracking.
```

## General Prompts

### Documentation Prompt
```
Create comprehensive documentation for the async RAG system:

1. Architecture documentation
2. Implementation guide
3. Configuration options
4. Troubleshooting guide
5. Performance tuning guide

Requirements:
- Clear explanations
- Code examples
- Configuration details
- Troubleshooting steps
- Performance guidelines

Provide documentation with examples and best practices.

Reference: See [prd.md](./prd.md) for documentation requirements and [phased-todo.md](./phased-todo.md) for documentation tracking.
```

### Monitoring Prompt
```
Set up comprehensive monitoring for async RAG system:

1. Performance metrics
2. Error rate monitoring
3. Resource usage tracking
4. Alerting configuration
5. Dashboard setup

Requirements:
- Real-time monitoring
- Alerting thresholds
- Performance dashboards
- Error tracking
- Resource monitoring

Provide monitoring setup with dashboards and alerts.

Reference: See [prd.md](./prd.md) for monitoring requirements and [phased-todo.md](./phased-todo.md) for monitoring tracking.
```
