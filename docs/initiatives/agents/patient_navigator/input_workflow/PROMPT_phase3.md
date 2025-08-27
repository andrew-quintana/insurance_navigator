# Phase 3 Implementation Prompt - Input Processing Workflow Integration & Fallback Systems

## Session Setup Instructions
**IMPORTANT**: Run `/clear` to start a fresh Claude Code session before beginning this phase.

## Project Context

You are implementing **Phase 3: Integration & Fallback Systems** for the Insurance Navigator Input Processing Workflow. This is a new session - use only the context provided below.

**Project**: Insurance Navigator - Input Processing Workflow MVP  
**Goal**: Add Flash v2.5 fallback provider, implement comprehensive error handling, and create end-to-end CLI workflow  
**Architecture**: Sequential pipeline with fallback chains, graceful degradation, performance optimization

## Current Status
Core pipeline implemented in Phase 2:
- Input Handler functional for voice and text capture
- Translation Router working with ElevenLabs provider integration
- Sanitization Agent processing insurance domain queries
- Integration Layer formatting output for downstream workflow
- FastAPI endpoints operational with basic functionality

## Phase 3 Focus
- Add Flash v2.5 fallback provider with cost optimization
- Implement circuit breaker pattern and comprehensive error handling
- Performance optimization with parallel processing where possible
- Complete end-to-end CLI workflow orchestration
- Target metrics: <5s latency, >85% fallback success rate, cost optimization

## Reference Documents to Read First

Before starting implementation, read these files for complete context:

1. `./RFC001.md` - Technical architecture and fallback strategy
2. `@/docs/initiatives/agents/patient_navigator/input_workflow/TODO001_phase2_notes.md` - Phase 2 implementation details and architecture decisions
3. `@/docs/initiatives/agents/patient_navigator/input_workflow/TODO001_phase2_handoff.md` - Known issues and Phase 3 requirements from Phase 2
4. `@/docs/initiatives/agents/patient_navigator/input_workflow/TODO001_phase2_test_update.md` - Performance baselines and testing results from Phase 2

## Phase 3 Tasks

### 1. Fallback Provider Implementation

#### Flash v2.5 Integration
- Implement Flash v2.5 provider following same interface as ElevenLabs provider
- Direct API integration using requests/httpx
- Cost optimization routing logic (prefer Flash for common languages)
- Performance comparison metrics vs ElevenLabs
- Rate limiting and quota management for free-tier usage

#### Translation Router Enhancement
- Add fallback chain logic: ElevenLabs → Flash v2.5 → Browser API (if available)
- Automatic failover triggers based on response time and error rates
- Provider selection logic based on text complexity analysis
- Cost tracking and optimization recommendations
- Provider health monitoring and status checking

**Files**:
- `agents/patient_navigator/input_processing/providers/flash.py`
- Update `agents/patient_navigator/input_processing/router.py`

### 2. Advanced Error Handling & Resilience

#### Circuit Breaker Pattern
- Implement circuit breaker for translation services
- Monitor API health and response times (success rate, latency)
- Automatic circuit opening on repeated failures (3+ consecutive)
- Gradual service recovery with health checks
- Circuit state persistence across sessions

#### Comprehensive Error Recovery
- 2 automatic retries with exponential backoff for translation failures
- User guidance prompts for recoverable errors
- Graceful degradation when services are unavailable
- Manual escalation workflow for complete translation failures
- Error categorization and appropriate response strategies

#### Timeout and Resource Management
- Request timeout handling (5s for translation APIs)
- Memory usage monitoring and cleanup
- Connection pooling for API requests
- Resource leak prevention and monitoring

**Files**:
- `agents/patient_navigator/input_processing/circuit_breaker.py`
- Update error handling across all existing modules

### 3. Performance Optimization

#### Parallel Processing
- Concurrent service health checks during initialization
- Parallel processing for batch input scenarios
- Async/await optimization throughout pipeline
- Connection pooling and keep-alive for API calls
- Non-blocking voice capture and processing

#### Performance Monitoring
- End-to-end latency tracking for each pipeline component
- Success/failure rate monitoring with detailed metrics
- API usage and cost tracking with optimization suggestions
- Memory usage profiling and optimization
- Real-time performance dashboard for CLI debug mode

#### Caching Enhancements
- Multi-level caching strategy (session + short-term persistence)
- Cache warming for common insurance terminology
- Cache eviction policies based on usage patterns
- Cache hit/miss ratio optimization
- Provider-specific cache keys for optimal performance

**Files**:
- `agents/patient_navigator/input_processing/performance_monitor.py`
- Update caching logic in existing modules

### 4. End-to-End CLI Workflow Integration

#### Complete CLI Orchestration
- Integrate all pipeline components into single CLI command
- Interactive mode for testing different input types and languages
- Batch processing mode for multiple inputs
- Progress indicators and real-time status updates
- User-friendly error messages and guidance

#### CLI Testing and Validation Utilities
- Built-in test scenarios for 5 different languages
- Performance benchmarking commands with detailed reporting
- Debug mode with pipeline step-by-step logging
- Validation utilities for output quality assessment
- Load testing capabilities for concurrent processing

#### FastAPI Integration Enhancement
- Complete error handling in existing endpoints
- Add performance metrics to API responses
- Implement request queuing for high load scenarios
- Add health check endpoints for system monitoring
- WebSocket support for real-time progress updates

**Files**:
- Update `agents/patient_navigator/input_processing/cli_interface.py`
- Enhance FastAPI endpoints in `main.py`

### 5. Quality Assurance & Validation

#### Edge Case Handling
- Mixed-language input parsing and processing
- Silent audio detection and user prompting
- Extremely long input chunking and processing
- Malformed or corrupted input validation
- Network connectivity issues and offline mode

#### Quality Metrics and Validation
- Translation accuracy scoring for insurance domain
- Sanitization effectiveness measurement
- User intent preservation validation
- Confidence scoring improvement
- Output consistency across multiple runs

**Files**:
- `agents/patient_navigator/input_processing/quality_validator.py`
- Update existing modules with quality metrics

## Expected Outputs

Save these files at the end of Phase 3:
- `@TODO001_phase3_notes.md` - Integration details, performance optimizations, fallback implementation
- `@TODO001_phase3_decisions.md` - Fallback strategy decisions, error handling approach, optimization choices
- `@TODO001_phase3_handoff.md` - Remaining issues, Phase 4 documentation needs, production readiness gaps
- `@TODO001_phase3_test_update.md` - Comprehensive test results, performance benchmarks, edge case handling validation

## Validation Checklist

### Setup Tasks
- [ ] Review Phase 2 outputs and validate core component functionality
- [ ] Install additional dependencies for circuit breaker (e.g., pybreaker) and performance monitoring
- [ ] Configure Flash v2.5 API credentials and test connectivity
- [ ] Verify existing ElevenLabs integration is stable and performant

### Implementation Tasks
- [ ] Implement Flash v2.5 translation provider with cost optimization logic
- [ ] Add fallback chain logic to Translation Router (ElevenLabs → Flash → Browser API)
- [ ] Create circuit breaker pattern for translation service reliability
- [ ] Implement retry logic with exponential backoff for failed requests
- [ ] Add performance monitoring with latency and success rate tracking
- [ ] Enhance caching with multi-level strategy and optimization
- [ ] Build complete CLI workflow orchestrating all pipeline components
- [ ] Add comprehensive error handling and user guidance systems

### Integration Tasks
- [ ] Test fallback chain activation under simulated API failures
- [ ] Validate circuit breaker behavior with deliberate service outages
- [ ] Verify parallel processing improves performance without resource issues
- [ ] Test connection pooling and resource management under load
- [ ] Ensure FastAPI endpoints handle all error scenarios gracefully
- [ ] Validate WebSocket integration for real-time updates (if implemented)

### Performance Validation Tasks
- [ ] End-to-end performance test to ensure <5 second latency target consistently
- [ ] Load test with 10 concurrent CLI sessions to verify scalability
- [ ] Cost validation ensuring <$0.05 per interaction across all providers
- [ ] Memory usage validation under extended operation (no leaks)
- [ ] Network resilience testing under poor connectivity conditions
- [ ] Fallback success rate validation (>85% when primary fails)

### Quality Validation Tasks
- [ ] Test end-to-end pipeline with 5 different language inputs
- [ ] Edge case testing: silent audio, mixed languages, long input, malformed data
- [ ] Translation accuracy validation for insurance domain terminology
- [ ] Sanitization effectiveness measurement with before/after comparison
- [ ] User intent preservation validation across multiple test scenarios
- [ ] **COLLABORATIVE VOICE TESTING**: Conduct real-time voice testing session with developer (see section below)
- [ ] Generate `@TODO001_phase3_test_update.md` with comprehensive results

### Documentation Tasks
- [ ] Save `@TODO001_phase3_notes.md` with integration and optimization details
- [ ] Save `@TODO001_phase3_decisions.md` with architectural choices and rationale
- [ ] Save `@TODO001_phase3_handoff.md` with Phase 4 preparation requirements
- [ ] Save `@TODO001_phase3_test_update.md` with performance benchmarks and test results

## Success Criteria

Phase 3 is complete when:
1. **Fallback System**: Flash v2.5 provider implemented and fallback chain operational
2. **Error Handling**: Circuit breaker pattern working with automatic recovery
3. **Performance**: <5 second latency achieved consistently under normal load
4. **Resilience**: >85% fallback success rate when primary translation fails
5. **Cost Optimization**: Cost per interaction <$0.05 with intelligent provider routing
6. **Quality**: Translation accuracy >95% for Spanish insurance terminology
7. **CLI Integration**: Complete end-to-end workflow functional with all components
8. **Production Readiness**: System handles edge cases gracefully with user guidance

## Performance Targets for Phase 3

- **End-to-end latency**: <5 seconds per interaction (95th percentile)
- **Translation accuracy**: >95% for supported languages in insurance domain
- **Fallback success rate**: >85% when primary translation service fails
- **Cost per interaction**: <$0.05 with optimal provider routing
- **System availability**: Architecture supports 99.5% uptime under normal load
- **Concurrent users**: Support 10+ concurrent CLI sessions without degradation

## Known Phase 2 Dependencies

Ensure these Phase 2 outputs exist and are functional:
- Core pipeline components (Handler, Router, Sanitizer, Integration) working
- ElevenLabs integration operational with reasonable performance
- Basic caching implemented and showing benefit
- FastAPI endpoints responding correctly with authentication
- Session-level error handling providing user feedback

## Technical Debt and Optimization Notes

Address these items from Phase 2 (reference `@TODO001_phase2_handoff.md`):
- Any performance bottlenecks identified in Phase 2 testing
- API rate limiting issues or quota management gaps
- Memory usage patterns that need optimization
- Error scenarios that weren't fully handled in Phase 2

## Collaborative Voice Testing Protocol

**IMPORTANT**: Phase 3 includes mandatory real-time collaborative testing between Claude Code and the developer to validate voice processing functionality.

### Pre-Testing Setup
1. **Environment Verification**: Ensure microphone access works in CLI environment
2. **API Status Check**: Verify ElevenLabs and Flash v2.5 APIs are operational
3. **Baseline Recording**: Test basic audio capture and playback
4. **Permission Setup**: Confirm system microphone permissions are granted

### Collaborative Testing Session Structure

#### Session 1: Basic Voice Capture (15 minutes)
**Developer Tasks**:
1. Run the CLI interface in voice mode
2. Speak the following test phrases clearly into microphone:
   - "I need help with my insurance policy"
   - "¿Cuánto cuesta mi plan de salud?" (Spanish)
   - "My claim was denied and I don't understand why"
   - "I want to change my deductible amount"

**Claude Code Tasks**:
1. Monitor real-time processing logs and performance metrics
2. Validate speech recognition accuracy and timing
3. Check translation quality and confidence scores
4. Identify any audio quality or processing issues
5. Document actual vs expected results

#### Session 2: Edge Case Voice Testing (20 minutes)
**Developer Tasks**:
1. Test challenging scenarios:
   - Speaking very quietly (whisper test)
   - Background noise (play music/TV while speaking)
   - Fast speech with insurance jargon
   - Mixed English-Spanish in same sentence
   - Long, complex insurance question (30+ seconds)
   - Intentional silence periods (test timeout handling)

**Claude Code Tasks**:
1. Monitor fallback system activation
2. Validate error handling and user feedback
3. Test circuit breaker behavior under poor audio conditions
4. Check performance degradation patterns
5. Verify graceful handling of edge cases

#### Session 3: Performance and Reliability Testing (25 minutes)
**Developer Tasks**:
1. Rapid-fire testing: 10 voice inputs in quick succession
2. Stress test: Hold microphone button and speak continuously for 45 seconds
3. Network simulation: Test with intentionally poor internet connection
4. Multi-language testing: Switch between languages mid-conversation
5. Real-world scenario: Complex insurance claim explanation

**Claude Code Tasks**:
1. Monitor resource usage and memory patterns
2. Validate concurrent processing capabilities
3. Test API rate limiting and fallback activation
4. Measure end-to-end latency under various conditions
5. Document performance bottlenecks and optimization opportunities

### Real-Time Collaboration Requirements

**During Testing**:
- **Developer**: Provide immediate verbal feedback on system responses
- **Claude Code**: Ask developer to repeat tests if results are unclear
- **Both**: Discuss unexpected behaviors or performance issues in real-time
- **Documentation**: Record actual voice samples (if possible) and system responses

**Communication Protocol**:
- Developer announces each test: "Starting whisper test now"
- Claude Code confirms: "Ready to monitor whisper test"
- After each test: Brief discussion of results before moving to next test
- Immediate issue escalation: "Stop - I'm seeing an error in the logs"

### Post-Testing Analysis

**Immediate Debrief (10 minutes)**:
1. Review any critical issues discovered during testing
2. Identify which scenarios worked perfectly vs. need improvement
3. Prioritize any urgent fixes needed before Phase 4
4. Document unexpected behaviors or system limitations

**Detailed Documentation Requirements**:
- Record exact voice input phrases used and system responses
- Document latency measurements for each test scenario
- Note any API failures or fallback activations
- Capture performance metrics during stress testing
- Identify specific improvements needed for production readiness

### Success Criteria for Collaborative Testing

Voice processing system passes collaborative testing when:
- [ ] Basic voice capture works reliably with clear speech
- [ ] Spanish-to-English translation accuracy >90% for insurance terms
- [ ] System handles whisper/quiet speech with appropriate user guidance
- [ ] Background noise doesn't cause complete system failure
- [ ] Timeout handling works properly with user-friendly messages
- [ ] Edge cases trigger appropriate fallbacks rather than crashes
- [ ] Performance remains acceptable (<7 seconds) under stress conditions
- [ ] Developer can successfully use the system for realistic insurance queries

### Testing Output Documentation

**Required in `@TODO001_phase3_test_update.md`**:
- Detailed log of all test scenarios attempted
- Voice input samples and corresponding system outputs
- Performance metrics captured during testing
- List of issues discovered with severity ratings
- Recommendations for production deployment
- Developer feedback and user experience assessment

## Next Phase Preview

Phase 4 will focus on comprehensive documentation, final validation against all PRD acceptance criteria, security and privacy review, and production deployment preparation with technical debt summary.