# Phase 2 Implementation Prompt - Input Processing Workflow Core Implementation

## Session Setup Instructions
**IMPORTANT**: Run `/clear` to start a fresh Claude Code session before beginning this phase.

## Project Context

You are implementing **Phase 2: Core Implementation** for the Insurance Navigator Input Processing Workflow. This is a new session - use only the context provided below.

**Project**: Insurance Navigator - Input Processing Workflow MVP  
**Goal**: Implement core pipeline components - Input Handler, Translation Router, and Sanitization Agent  
**Architecture**: Sequential pipeline - Input Handler → Translation Router → Sanitization Agent → Integration Layer

## Current Status
Foundation completed in Phase 1:
- Project structure created under `agents/patient_navigator/input_processing/`
- Core protocols/classes defined in `types.py`
- FastAPI endpoints added to `main.py`
- Environment configuration integrated with existing system

## Phase 2 Focus
- Implement core pipeline components with error handling
- ElevenLabs primary integration (no fallback chains yet - Phase 3)
- CLI interface only, hardcoded Spanish language
- Session-level caching with basic performance optimization

## Reference Documents to Read First

Before starting implementation, read these files for complete context:

1. `/Users/aq_home/1Projects/accessa/insurance_navigator/docs/initiatives/agents/patient_navigator/input_workflow/RFC001.md` - Technical architecture and component specifications
2. `@TODO001_phase1_notes.md` - Phase 1 implementation details
3. `@TODO001_phase1_handoff.md` - Phase 1 handoff notes and dependencies

## Phase 2 Tasks

### 1. Input Handler Implementation

#### Voice Input Capture
- Implement voice input using PyAudio for microphone access
- Use SpeechRecognition library with Google Speech API for speech-to-text
- Handle 30-second timeout using asyncio
- Basic audio quality validation using numpy/scipy audio analysis
- Error handling for microphone access issues

#### Text Input Capture  
- Standard input() interface with UTF-8 support
- Handle multi-line input and special characters
- Basic text length and encoding validation
- Integration with existing CLI argument parsing

**File**: `agents/patient_navigator/input_processing/handler.py`

### 2. Translation Router Implementation

#### Provider Abstraction
- Create abstract base class/protocol for translation providers
- Route selection logic based on language configuration
- Cost estimation and usage tracking methods
- Basic error handling for API failures

#### ElevenLabs Integration
- Direct REST API integration using requests/httpx
- Authentication handling with API keys from environment
- Request/response parsing and validation
- Cost estimation for usage tracking
- Rate limiting to stay within free-tier bounds

#### Translation Caching
- Session-level in-memory cache using functools.lru_cache (1000 entries)
- Cache key generation: source text + language + provider
- Cache hit/miss metrics collection
- Cache invalidation strategies

**Files**: 
- `agents/patient_navigator/input_processing/router.py`
- `agents/patient_navigator/input_processing/providers/elevenlabs.py`

### 3. Sanitization Agent Implementation

#### Text Cleanup Pipeline
- Remove extra whitespace and normalize punctuation
- Handle encoding issues and special characters
- Basic grammar and spelling correction for insurance domain
- Preserve original meaning while improving clarity

#### Coreference Resolution
- Simple pronoun replacement with explicit references
- Context-aware entity resolution
- Handle common insurance-related references ("my policy", "the claim")

#### Intent Clarification  
- Insurance domain keyword expansion
- Ambiguity detection and clarification
- Structured prompt formatting for downstream agents

**File**: `agents/patient_navigator/input_processing/sanitizer.py`

### 4. Integration Layer Implementation

#### Downstream Formatting
- Format sanitized output for existing patient navigator workflow
- Add required metadata for workflow compatibility
- Confidence scoring and quality metrics
- Processing step tracking and validation

#### Workflow Compatibility
- Validate output structure matches downstream expectations
- Add workflow metadata required by existing agents
- Error handling for integration failures

**File**: `agents/patient_navigator/input_processing/integration.py`

### 5. CLI Interface Enhancement

#### End-to-End Pipeline
- Integrate all components into cohesive workflow
- Command-line interface for voice vs text input selection
- Progress indicators and status messages
- Error handling and user guidance

#### Testing and Validation
- Built-in test scenarios for different input types
- Performance benchmarking utilities
- Debug mode with detailed pipeline logging

**File**: `agents/patient_navigator/input_processing/cli_interface.py`

### 6. FastAPI Integration Updates

Based on the existing endpoints in `main.py`, enhance the implementation:
- Complete the `InputProcessingCLI` class functionality
- Implement proper error handling and response formatting
- Add detailed logging and metrics collection
- Ensure proper integration with existing authentication system

## Expected Outputs

Save these files at the end of Phase 2:
- `@TODO001_phase2_notes.md` - Core implementation details, API integration notes
- `@TODO001_phase2_decisions.md` - Provider abstraction choices, caching strategy decisions
- `@TODO001_phase2_handoff.md` - Known issues, Phase 3 requirements
- `@TODO001_phase2_test_update.md` - Testing results, performance baselines, assumptions validated

## Validation Checklist

### Setup Tasks
- [ ] Review Phase 1 outputs (`@TODO001_phase1_notes.md`, `@TODO001_phase1_handoff.md`)
- [ ] Install additional Python dependencies (PyAudio, SpeechRecognition, requests/httpx)
- [ ] Verify ElevenLabs API credentials and test basic connectivity
- [ ] Validate existing FastAPI endpoints are accessible

### Implementation Tasks
- [ ] Implement `InputHandler` class with voice and text capture methods
- [ ] Create `TranslationRouter` with provider abstraction pattern
- [ ] Implement `ElevenLabs` provider with direct REST API integration
- [ ] Add session-level translation caching with LRU eviction
- [ ] Implement `SanitizationAgent` with cleanup and coreference resolution
- [ ] Create `WorkflowHandoff` formatting and validation methods
- [ ] Complete `InputProcessingCLI` class to support existing FastAPI endpoints

### Integration Tasks
- [ ] Ensure all components integrate properly in the pipeline
- [ ] Test voice input capture in CLI environment (10-second sample)
- [ ] Test text input processing with UTF-8 international characters
- [ ] Validate ElevenLabs API integration with Spanish test input
- [ ] Test translation caching (cache hit/miss behavior)
- [ ] Verify sanitization improves prompt clarity for insurance queries
- [ ] Check integration layer output matches downstream agent expectations

### Validation Tasks
- [ ] Test end-to-end pipeline with sample Spanish text input
- [ ] Validate voice capture and speech-to-text conversion
- [ ] Confirm ElevenLabs translation accuracy and response times
- [ ] Test caching effectiveness and performance impact
- [ ] Verify sanitization maintains original intent while improving clarity
- [ ] Test FastAPI endpoints with proper authentication
- [ ] Generate `@TODO001_phase2_test_update.md` with comprehensive test results

### Documentation Tasks
- [ ] Save `@TODO001_phase2_notes.md` with implementation details
- [ ] Save `@TODO001_phase2_decisions.md` with architectural choices and rationale
- [ ] Save `@TODO001_phase2_handoff.md` with Phase 3 preparation notes
- [ ] Save `@TODO001_phase2_test_update.md` with testing results and performance metrics

## Success Criteria

Phase 2 is complete when:
1. All core components (Handler, Router, Sanitizer, Integration) are implemented and functional
2. ElevenLabs API integration works reliably with Spanish translation
3. End-to-end pipeline processes text input successfully through all stages
4. Voice input capture and speech-to-text conversion works in CLI environment
5. Translation caching is operational and shows measurable performance improvement
6. Sanitization demonstrates improved prompt clarity for insurance domain queries
7. FastAPI endpoints in `main.py` work with implemented components
8. All four Phase 2 documentation files are saved for Phase 3 handoff

## Performance Expectations

For Phase 2 completion:
- **Text Processing**: <3 seconds end-to-end for typical insurance queries
- **Voice Processing**: <5 seconds including speech recognition
- **Translation Accuracy**: >90% for Spanish-to-English insurance terminology
- **Cache Hit Rate**: >70% for repeated common phrases during testing
- **API Success Rate**: >95% for ElevenLabs API calls under normal conditions

## Known Phase 1 Dependencies

Ensure these Phase 1 outputs exist and review them:
- Foundation project structure in `agents/patient_navigator/input_processing/`
- Core types and protocols defined in `types.py`
- Environment configuration working with existing config system
- FastAPI endpoint stubs in `main.py` (already added - see system reminder)

## Next Phase Preview

Phase 3 will add Flash v2.5 fallback provider, implement comprehensive error handling with circuit breaker patterns, and create complete end-to-end CLI workflow with performance optimization.