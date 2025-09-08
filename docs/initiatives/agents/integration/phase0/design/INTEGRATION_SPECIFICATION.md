# Integration Specification: Agentic System to Chat Endpoint
## Technical Design Document

**Date**: September 7, 2025  
**Version**: 1.0  
**Status**: Draft - Ready for Review

---

## Executive Summary

This document specifies the technical integration of the existing agentic patient navigator system (input workflow + output workflow) with the `/chat` endpoint in the API service. The integration will enable multilingual, empathetic chat interactions while maintaining backward compatibility.

---

## Documentation References

### **Critical Reading for Implementation**

Before implementing the integration, review these key documents:

#### **Input Workflow (Production-Ready)**
- **`@docs/initiatives/agents/patient_navigator/input_workflow/PHASE3_STATUS.md`** - ✅ Complete implementation status (0.203s-0.278s performance)
- **`@docs/initiatives/agents/patient_navigator/input_workflow/TODO001_phase3_summary.md`** - ✅ Final completion with APIs and interfaces
- **`@docs/initiatives/agents/patient_navigator/input_workflow/PHASE3_IMPLEMENTATION.md`** - Technical implementation details
- **`@docs/initiatives/agents/patient_navigator/input_workflow/RFC001.md`** - API design and integration patterns

#### **Output Workflow (Production-Ready)**
- **`@docs/initiatives/agents/patient_navigator/output_workflow/PHASE2_FINAL_COMPLETION.md`** - ✅ Complete with Claude Haiku LLM (54 tests, 100% pass)
- **`@docs/initiatives/agents/patient_navigator/output_workflow/README.md`** - Usage examples and API interfaces
- **`@docs/initiatives/agents/patient_navigator/output_workflow/DEPLOYMENT_GUIDE.md`** - Production deployment instructions
- **`@docs/initiatives/agents/patient_navigator/output_workflow/RFC001.md`** - Technical design and workflow patterns

#### **Architecture and Requirements**
- **`@docs/initiatives/agents/patient_navigator/input_workflow/CONTEXT.md`** - Input workflow requirements and interfaces
- **`@docs/initiatives/agents/patient_navigator/output_workflow/CONTEXT.md`** - Output workflow communication principles
- **`@docs/initiatives/agents/patient_navigator/input_workflow/PRD001.md`** - Input workflow product requirements
- **`@docs/initiatives/agents/patient_navigator/output_workflow/PRD001.md`** - Output workflow product requirements

#### **Integration-Specific References**
- **`@docs/initiatives/agents/patient_navigator/input_workflow/TODO001_phase3_handoff.md`** - Production readiness and interface contracts
- **`@docs/initiatives/agents/patient_navigator/output_workflow/@TODO001_phase1_handoff.md`** - Integration handoff requirements
- **`@docs/initiatives/agents/patient_navigator/input_workflow/SECURITY_REVIEW.md`** - Security considerations for API integration
- **`@docs/initiatives/agents/patient_navigator/output_workflow/@TODO001_phase1_decisions.md`** - Architectural decisions for integration

---

## Current Architecture

### **Existing Components**

#### **Chat Endpoint (Current)**
```python
# Location: api/endpoints/chat.py
POST /chat
{
  "message": "user query",
  "conversation_id": "optional_conversation_id"
}

Response:
{
  "response": "basic chat response", 
  "conversation_id": "conversation_id"
}
```

#### **Input Workflow System**
- **Location**: `docs/initiatives/agents/patient_navigator/input_workflow/`
- **Capabilities**: Multilingual translation, input sanitization, intent clarification
- **APIs**: ElevenLabs integration, fallback handling
- **Status**: Implemented and tested

#### **Output Workflow System**  
- **Location**: `docs/initiatives/agents/patient_navigator/output_workflow/`
- **Capabilities**: Response consolidation, tone adaptation, empathetic formatting
- **Features**: Warm communication, plain language, actionable guidance
- **Status**: Implemented and tested

### **Integration Gaps**
1. No connection between chat endpoint and input workflow
2. No connection between chat endpoint and output workflow
3. No orchestration of the complete user journey
4. No multilingual support in chat endpoint
5. No empathetic response formatting in chat endpoint

---

## Target Architecture

### **Enhanced Chat Endpoint Flow**

```
User Request → Chat Endpoint → Integration Orchestrator
                                      ↓
Input Workflow ← User Input (any language)
    ↓ (translated, sanitized)
Agent Processing ← Clean English Prompt
    ↓ (agent outputs)
Output Workflow ← Technical/Fragmented Response
    ↓ (formatted, empathetic)
Chat Endpoint Response → User-Friendly Response
```

### **Component Integration**

#### **1. Chat Orchestrator (New)**
```python
class ChatOrchestrator:
    def __init__(self):
        self.input_processor = InputWorkflowProcessor()
        self.agent_router = AgentRouter() 
        self.output_formatter = OutputWorkflowFormatter()
    
    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        # 1. Process input through input workflow
        processed_input = await self.input_processor.process(request.message)
        
        # 2. Route to appropriate agents
        agent_outputs = await self.agent_router.route_and_process(processed_input)
        
        # 3. Format output through output workflow
        formatted_response = await self.output_formatter.format(agent_outputs)
        
        # 4. Build final response
        return self.build_response(formatted_response, request)
```

#### **2. Input Workflow Integration**
```python
class InputWorkflowProcessor:
    def __init__(self):
        self.translator = ElevenLabsTranslator()
        self.sanitizer = IntentSanitizer()
    
    async def process(self, user_input: str, language_hint: str = None) -> ProcessedInput:
        # Language detection and translation
        if language_hint or self.needs_translation(user_input):
            translated = await self.translator.translate_to_english(user_input)
        else:
            translated = user_input
            
        # Intent sanitization and clarification
        sanitized = await self.sanitizer.sanitize(translated)
        
        return ProcessedInput(
            original=user_input,
            translated=translated,
            sanitized=sanitized,
            confidence=self.calculate_confidence()
        )
```

#### **3. Output Workflow Integration**
```python
class OutputWorkflowFormatter:
    def __init__(self):
        self.tone_adapter = ToneAdapter()
        self.consolidator = ResponseConsolidator()
        
    async def format(self, agent_outputs: List[AgentOutput]) -> FormattedResponse:
        # Consolidate multiple agent outputs
        consolidated = self.consolidator.consolidate(agent_outputs)
        
        # Apply tone adaptation
        formatted = await self.tone_adapter.apply_empathetic_tone(consolidated)
        
        # Add actionable guidance
        enhanced = self.add_actionable_guidance(formatted)
        
        return FormattedResponse(
            text=enhanced,
            tone="empathetic",
            next_steps=self.extract_next_steps(enhanced)
        )
```

---

## API Contract Enhancement

### **Enhanced Chat Endpoint**

#### **Request Format**
```python
POST /chat
{
  "message": "user query (any language)",
  "conversation_id": "optional_conversation_id",
  "user_language": "optional_language_hint", # e.g., "es", "fr"
  "context": "optional_context",
  "preferences": {
    "tone": "empathetic", # default
    "language_processing": "auto", # auto, disabled
    "output_format": "conversational" # conversational, technical
  }
}
```

#### **Response Format**
```python
{
  "response": "formatted, empathetic response",
  "conversation_id": "conversation_id",
  "metadata": {
    "input_processing": {
      "original_language": "detected_language",
      "translation_applied": true/false,
      "confidence": 0.95
    },
    "agent_processing": {
      "agents_used": ["benefits_analyzer", "eligibility_checker"],
      "processing_time_ms": 3500
    },
    "output_formatting": {
      "tone_applied": "empathetic",
      "readability_level": "8th_grade",
      "next_steps_included": true
    }
  },
  "next_steps": [
    "Contact your insurance provider at 1-800-xxx-xxxx",
    "Review your benefits summary in your member portal"
  ],
  "sources": ["policy_document_xyz", "benefits_database"]
}
```

### **Backward Compatibility**

#### **Legacy Request Support**
```python
# Legacy format still supported
POST /chat
{
  "message": "user query",
  "conversation_id": "optional_conversation_id"
}

# Automatically converted to:
{
  "message": "user query",
  "conversation_id": "optional_conversation_id", 
  "user_language": "auto",
  "preferences": {
    "tone": "empathetic",
    "language_processing": "auto",
    "output_format": "conversational"
  }
}
```

---

## Data Flow Architecture

### **Detailed Flow Diagram**

```
1. User Input
   └─ POST /chat {"message": "¿Cuáles son mis beneficios?"}

2. Chat Orchestrator
   ├─ Input Processing
   │  ├─ Language Detection: Spanish detected
   │  ├─ Translation: "What are my benefits?"
   │  └─ Sanitization: "Please explain my insurance benefits coverage"
   │
   ├─ Agent Processing
   │  ├─ Route to BenefitsAnalyzerAgent
   │  ├─ Execute benefits lookup
   │  └─ Generate technical response
   │
   └─ Output Processing
      ├─ Consolidate agent outputs
      ├─ Apply empathetic tone
      ├─ Add plain language explanation
      └─ Include next steps

3. Final Response
   └─ "I'd be happy to help you understand your benefits! Based on your 
       current plan, you have..."
```

### **Error Handling Flow**

```
Error at Any Stage
├─ Input Processing Error
│  ├─ Translation fails → Use original text
│  ├─ Sanitization fails → Use translated text
│  └─ Complete failure → Fallback to basic chat
│
├─ Agent Processing Error  
│  ├─ Agent timeout → Partial response with disclaimer
│  ├─ Agent error → Fallback to basic information
│  └─ Complete failure → Error message with support contact
│
└─ Output Processing Error
   ├─ Formatting fails → Return agent output directly
   ├─ Tone adaptation fails → Return consolidated response
   └─ Complete failure → Basic response with error note
```

---

## Performance Requirements

### **Latency Targets**

| Component | Target Latency | Max Acceptable |
|-----------|---------------|----------------|
| Input Processing | < 3s | < 5s |
| Agent Processing | < 4s | < 6s | 
| Output Processing | < 1s | < 2s |
| **Total End-to-End** | **< 8s** | **< 10s** |

### **Optimization Strategies**

#### **Parallel Processing**
```python
async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
    # Parallel execution where possible
    async with asyncio.gather(
        self.input_processor.process(request.message),
        self.load_user_context(request.conversation_id),
        return_exceptions=True
    ) as results:
        processed_input, user_context = results
        
    # Continue with sequential processing
    agent_outputs = await self.agent_router.route_and_process(processed_input)
    formatted_response = await self.output_formatter.format(agent_outputs)
```

#### **Caching Strategy**
- **Translation Cache**: Cache common translations (24-hour TTL)
- **Agent Response Cache**: Cache agent responses for identical queries (1-hour TTL)  
- **User Context Cache**: Cache user context and preferences (session-based)

#### **Resource Management**
- **Connection Pooling**: Reuse HTTP connections to external APIs
- **Request Batching**: Batch multiple API calls where possible
- **Circuit Breakers**: Prevent cascade failures from external services

---

## Security Considerations

### **Data Protection**

#### **In Transit**
- All API calls use HTTPS/TLS encryption
- Secure communication with external translation services
- Encrypted websocket connections for real-time features

#### **At Rest**
- No persistent storage of sensitive user input
- Conversation history encrypted in database
- API keys and secrets managed through secure secret management

#### **Processing Security**
- Input sanitization prevents injection attacks
- Output filtering prevents sensitive data leakage
- Rate limiting prevents abuse and DoS attacks

### **Privacy Compliance**

#### **Data Minimization**
- Only process data necessary for functionality
- Automatic cleanup of processing artifacts
- User control over data retention preferences

#### **Consent and Control**
- Clear disclosure of language processing
- Opt-out mechanisms for enhanced features
- User access to conversation data and deletion

---

## Monitoring and Observability

### **Key Metrics**

#### **Performance Metrics**
- End-to-end response time (p50, p95, p99)
- Component-level latency breakdown
- Error rates by component and error type
- Throughput (requests per second)

#### **Quality Metrics**
- Translation accuracy (user feedback)
- Agent response relevance (user satisfaction)
- Output formatting effectiveness (readability scores)
- User engagement (conversation length, follow-up questions)

#### **System Health Metrics**
- Service availability (uptime percentage)
- External API dependency health
- Resource utilization (CPU, memory, network)
- Error recovery success rates

### **Alerting Strategy**

#### **Critical Alerts (PagerDuty)**
- Service down or unhealthy
- Error rate > 5% for 5+ minutes  
- Response time > 15 seconds for 10+ requests
- External API failures > 50% for 3+ minutes

#### **Warning Alerts (Slack)**
- Error rate > 2% for 10+ minutes
- Response time > 10 seconds for 20+ requests
- Cache miss rate > 80% for 30+ minutes
- User satisfaction score < 3.0 for 1+ hour

---

## Testing Strategy

### **Unit Testing**
- Individual component testing (input, agent, output processors)
- Mock external API responses
- Error condition testing
- Performance benchmark testing

### **Integration Testing**
- End-to-end workflow testing
- External API integration testing
- Error handling and recovery testing
- Backward compatibility testing

### **Performance Testing**
- Load testing (100+ concurrent users)
- Stress testing (beyond normal capacity)
- Latency testing (component and end-to-end)
- Resource utilization testing

### **User Acceptance Testing**
- Multilingual input testing
- Response quality assessment
- User experience validation
- Accessibility compliance testing

---

## Deployment Strategy

### **Rollout Plan**

#### **Phase 1: Staging Deployment**
- Deploy to staging environment
- Internal testing with test data
- Performance validation
- Security review

#### **Phase 2: Canary Deployment**
- 5% traffic to new integrated endpoint
- Monitor performance and error rates
- Gradual increase to 25%, 50%, 100%
- Rollback plan ready at each stage

#### **Phase 3: Full Production**
- Complete migration to integrated endpoint
- Legacy endpoint deprecated (6-month timeline)
- Full monitoring and alerting active
- User feedback collection enabled

### **Rollback Strategy**
- Feature flags for quick disabling
- Legacy endpoint maintained during transition
- Database migration rollback procedures
- Automated health checks and rollback triggers

---

## Success Criteria

### **Technical Success**
- [ ] All integration points functional
- [ ] Performance targets met
- [ ] Error rates within acceptable limits
- [ ] Backward compatibility maintained
- [ ] Security requirements satisfied

### **User Experience Success**
- [ ] Multilingual support working accurately
- [ ] Response quality improved (user feedback)
- [ ] Response time acceptable (< 8s average)
- [ ] Error handling graceful and informative
- [ ] Accessibility standards met

### **Operational Success**
- [ ] Monitoring and alerting fully operational
- [ ] Documentation complete and accurate
- [ ] Team trained on new system
- [ ] Support procedures updated
- [ ] Deployment and rollback procedures tested

---

## Next Steps

1. **Review and Approval**: Technical review and stakeholder approval
2. **Implementation Planning**: Detailed implementation task breakdown
3. **Development**: Phased development approach
4. **Testing**: Comprehensive testing at each phase
5. **Deployment**: Staged deployment with monitoring

---

**Document Status**: Draft - Ready for Technical Review  
**Next Review Date**: Within 1 week of distribution  
**Approval Required**: Technical Lead, Product Owner, Security Team