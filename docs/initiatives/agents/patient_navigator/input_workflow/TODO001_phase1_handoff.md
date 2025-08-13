# Phase 1 to Phase 2 Handoff - Input Processing Workflow

## Phase 2 Implementation Requirements

### 1. Voice Input Implementation

**Current State**: Placeholder implementation in `handler.py`
**Phase 2 Requirements**:

#### Audio Capture Implementation
- **Library**: PyAudio integration for microphone access
- **Formats**: Support WAV, MP3, and common audio formats  
- **Quality**: Implement audio level detection and noise filtering
- **Timeout**: Robust timeout handling with user feedback
- **Permissions**: Handle microphone permission requests gracefully

**Implementation Tasks**:
```python
# In handler.py, replace placeholder with:
import pyaudio
import wave
import speech_recognition as sr

async def capture_voice_input(self, timeout: float = 30.0) -> bytes:
    # Real PyAudio implementation
    # Audio format detection
    # Noise level analysis
    # Timeout with progress feedback
```

**Dependencies Already Added**:
- PyAudio>=0.2.11
- SpeechRecognition>=3.10.0  
- scipy>=1.11.0

**Testing Requirements**:
- Test with different microphone hardware
- Test timeout scenarios
- Test audio quality validation
- Test background noise handling

### 2. Real Translation API Integration

**Current State**: Stub implementations in providers/
**Phase 2 Requirements**:

#### ElevenLabs API Integration
- **Endpoint**: Implement real HTTP calls to ElevenLabs v3 API
- **Authentication**: API key management and rotation
- **Rate Limiting**: Handle API rate limits and quotas
- **Error Handling**: Real API error response handling
- **Cost Tracking**: Actual usage and cost monitoring

**Implementation Tasks**:
```python
# In providers/elevenlabs.py, replace stubs with:
import httpx

async def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
    async with httpx.AsyncClient() as client:
        # Real API call implementation
        # Response parsing and validation
        # Error handling for API failures
        # Cost calculation from API response
```

#### Flash API Integration  
- **Endpoint**: Implement Flash v2.5 API calls
- **Cost Optimization**: Implement intelligent routing for cost savings
- **Quality Comparison**: A/B test translation quality vs ElevenLabs
- **Fallback Logic**: Real fallback chain implementation

**API Keys Required**:
- ELEVENLABS_API_KEY (production key)
- FLASH_API_KEY (production key)

### 3. Advanced Caching Implementation

**Current State**: Simple LRU cache placeholder
**Phase 2 Requirements**:

#### Redis Integration
- **Cache Backend**: Replace in-memory cache with Redis
- **TTL Management**: Configurable cache expiration
- **Cache Invalidation**: Smart invalidation strategies
- **Distributed Caching**: Support multiple app instances

**Implementation Tasks**:
```python
# New file: cache.py
import redis.asyncio as redis

class TranslationCache:
    async def get_cached_translation(self, cache_key: str) -> Optional[TranslationResult]
    async def set_cached_translation(self, cache_key: str, result: TranslationResult, ttl: int)
    async def invalidate_cache(self, pattern: str)
```

**Dependencies to Add**:
- redis>=4.5.0
- hiredis>=2.0.0 (for better performance)

### 4. Advanced Sanitization Features

**Current State**: Basic cleanup and structuring
**Phase 2 Requirements**:

#### Coreference Resolution Enhancement
- **NLP Library**: Integrate spaCy or similar for better coreference resolution
- **Context Awareness**: Use conversation history for better resolution
- **Domain Training**: Train on insurance-specific coreference patterns

#### Intent Clarification Enhancement  
- **Ambiguity Detection**: Better detection of ambiguous terms
- **User Validation**: Implement user confirmation loops for unclear intent
- **Domain Expansion**: Expanded insurance terminology dictionary

**Implementation Tasks**:
```python
# Enhanced sanitizer.py
import spacy

class AdvancedSanitizationAgent:
    def _resolve_coreferences_advanced(self, text: str, context: UserContext) -> str:
        # spaCy integration for coreference resolution
        # Machine learning-based disambiguation
        # Context-aware pronoun resolution
```

**Dependencies to Add**:
- spacy>=3.6.0
- spacy model: en_core_web_sm

### 5. Performance Optimization

**Current State**: Basic async implementation
**Phase 2 Requirements**:

#### Parallel Processing
- **Concurrent Requests**: Process multiple inputs simultaneously
- **Pipeline Parallelization**: Run sanitization while translation is finishing
- **Resource Management**: Connection pooling and resource limits

#### Latency Optimization
- **Target**: <5 seconds end-to-end (currently ~600ms with stubs)
- **Bottleneck Analysis**: Profile real API response times
- **Optimization**: Implement request batching where possible

**Implementation Tasks**:
```python
# Performance optimizations
import asyncio
from asyncio import Semaphore

class OptimizedTranslationRouter:
    def __init__(self):
        self.semaphore = Semaphore(10)  # Limit concurrent requests
        self.connection_pool = httpx.AsyncClient()
```

### 6. Monitoring and Observability

**Current State**: Basic logging
**Phase 2 Requirements**:

#### Metrics Collection
- **Performance Metrics**: Response times, error rates, cache hit rates
- **Usage Metrics**: API calls, cost tracking, user patterns
- **Quality Metrics**: Translation confidence distributions, user satisfaction

#### Health Monitoring
- **API Health Checks**: Real-time provider availability monitoring  
- **Alerting**: Automated alerts for service degradation
- **Dashboard**: Monitoring dashboard for system health

**Implementation Tasks**:
```python
# New file: monitoring.py
from prometheus_client import Counter, Histogram, Gauge

translation_requests = Counter('translation_requests_total', 'Total translation requests')
translation_duration = Histogram('translation_duration_seconds', 'Translation request duration')
api_health = Gauge('api_health_status', 'API health status', ['provider'])
```

**Dependencies to Add**:
- prometheus-client>=0.17.0
- structlog>=23.1.0

## Dependencies to Add for Phase 2

### Required Dependencies
```txt
# Real API integration
httpx>=0.24.0  # Already added
redis>=4.5.0
hiredis>=2.0.0

# Advanced NLP
spacy>=3.6.0
# Run: python -m spacy download en_core_web_sm

# Monitoring and observability  
prometheus-client>=0.17.0
structlog>=23.1.0

# Audio processing (already added)
PyAudio>=0.2.11
SpeechRecognition>=3.10.0
scipy>=1.11.0
```

### Development Dependencies
```txt
# Testing
pytest-benchmark>=4.0.0  # Performance testing
pytest-asyncio>=0.23.0   # Already in project
faker>=19.0.0           # Test data generation

# Profiling
py-spy>=0.3.14          # Production profiling
memory-profiler>=0.61.0  # Memory usage analysis
```

## Configuration Updates Required

### Environment Variables to Add
```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
REDIS_SSL_ENABLED=false

# Performance Configuration
INPUT_PROCESSING_MAX_CONCURRENT_REQUESTS=10
INPUT_PROCESSING_CONNECTION_TIMEOUT=30
INPUT_PROCESSING_REQUEST_POOL_SIZE=20

# Monitoring Configuration
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=8001
STRUCTLOG_ENABLED=true

# Advanced Features
SPACY_MODEL=en_core_web_sm
ADVANCED_SANITIZATION_ENABLED=true
USER_VALIDATION_ENABLED=false  # For Phase 3
```

### Configuration Schema Updates
```python
# In config.py, add to InputProcessingConfig:
redis_url: Optional[str] = None
redis_password: Optional[str] = None
max_concurrent_requests: int = 10
connection_timeout: float = 30.0
prometheus_enabled: bool = False
advanced_sanitization_enabled: bool = False
```

## Testing Requirements for Phase 2

### Integration Testing
- **Real API Testing**: Test with actual ElevenLabs and Flash APIs
- **Load Testing**: Verify performance under concurrent load
- **Cost Testing**: Validate cost estimation accuracy
- **Cache Testing**: Verify Redis integration and performance

### Performance Testing
- **Latency Testing**: Measure end-to-end response times
- **Throughput Testing**: Maximum requests per second
- **Memory Testing**: Memory usage under load
- **API Limit Testing**: Behavior when hitting rate limits

### Error Scenario Testing
- **API Failures**: Test fallback behavior
- **Network Issues**: Test timeout and retry logic
- **Cache Failures**: Test degraded performance without cache
- **Resource Exhaustion**: Test behavior under resource constraints

## Known Issues to Address in Phase 2

### 1. Audio Quality Validation
**Issue**: Current quality scoring is placeholder
**Solution**: Implement proper audio analysis with scipy
**Priority**: High (required for voice input)

### 2. Translation Quality Assessment
**Issue**: Confidence scores are hardcoded
**Solution**: Implement real confidence scoring from API responses
**Priority**: High (affects user trust)

### 3. Cost Optimization
**Issue**: No actual cost tracking or optimization
**Solution**: Implement real-time cost monitoring and smart routing
**Priority**: Medium (cost management)

### 4. Error Recovery
**Issue**: Limited error recovery strategies
**Solution**: Implement exponential backoff, circuit breakers
**Priority**: Medium (reliability)

### 5. User Feedback Loop
**Issue**: No mechanism for users to correct translation errors
**Solution**: Design validation UI for ambiguous translations
**Priority**: Low (Phase 3 feature)

## Success Criteria for Phase 2

### Performance Criteria
- ✅ End-to-end latency <5 seconds (95th percentile)
- ✅ Support 10+ concurrent users
- ✅ Translation accuracy >95% for supported languages
- ✅ System availability >99.5%

### Functional Criteria  
- ✅ Real voice input processing functional
- ✅ Real translation APIs integrated with fallback
- ✅ Redis caching operational
- ✅ Advanced sanitization improves output quality
- ✅ Monitoring and alerting functional

### Quality Criteria
- ✅ Comprehensive error handling for all failure modes
- ✅ Production-ready logging and monitoring
- ✅ Cost per interaction <$0.05
- ✅ User validation >90% for sanitized output

## Phase 2 Timeline Estimate

**Week 1: API Integration**
- Real translation API implementation
- Error handling and fallback logic
- Basic performance optimization

**Week 2: Voice and Advanced Features**  
- Voice input implementation
- Advanced sanitization with NLP
- Redis caching integration

**Week 3: Monitoring and Production Readiness**
- Monitoring and metrics implementation
- Performance testing and optimization  
- Production deployment preparation

## Handoff Checklist

- ✅ Phase 1 architecture documented and validated
- ✅ All stub implementations clearly marked
- ✅ Dependencies identified and added to requirements.txt
- ✅ Configuration schema designed for Phase 2 features
- ✅ Error handling patterns established
- ✅ Testing framework ready for expansion
- ✅ Integration points with existing system validated
- ✅ Performance benchmarks established (baseline)

## Contact and Knowledge Transfer

**Code Architecture Questions**: Reference RFC001.md and this handoff document
**Implementation Details**: See @TODO001_phase1_notes.md for detailed implementation decisions
**Testing Approach**: CLI interface provides comprehensive testing framework
**Integration Questions**: FastAPI endpoints demonstrate integration pattern

Phase 2 implementation can begin immediately using this foundation. All architectural decisions have been validated and the system is ready for production feature implementation.