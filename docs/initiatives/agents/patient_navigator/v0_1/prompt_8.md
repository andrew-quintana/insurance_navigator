# Phase 8 Prompt Template - External API Integration

**Phase**: External API Integration  
**Duration**: 1 week  
**Focus**: External API integration and error handling  
**Start Date**: 2025-12-01  

---

## 🎯 Phase 8 Objectives

Integrate with external APIs and implement robust error handling:
- **Web Search Tool** (service-agnostic) integration for Tool Calling Chat Agent Component
- **Translation Service** integration for Translation Edge Function Component
- **LLM Integration** for all components (Anthropic Claude)
- **Microsoft Presidio** integration for Security Edge Function Component
- **Comprehensive error handling** and retry logic across all components
- **Rate limiting and quota management** for external APIs
- **Component-specific data model validation** across all integrations

---

## 📋 Integration Guidance

### 📚 Reference Documentation
- **PRD**: `/docs/initiatives/agents/patient_navigator/v0_1/PRD.md` - External API requirements
- **RFC**: `/docs/initiatives/agents/patient_navigator/v0_1/RFC.md` - API specifications
- **TODO**: `/docs/initiatives/agents/patient_navigator/v0_1/TODO.md` - Phase 8 detailed tasks

### 🔧 API Integration Reference
- **Existing API Patterns**: Study `/main.py` for API integration patterns
- **Configuration**: Reference `/config/` directory for API configuration
- **Error Handling**: See existing error handling patterns in `/core/`
- **Rate Limiting**: Reference existing rate limiting implementations

### 🎯 Key Deliverables
1. **Tavily Integration** - See TODO Phase 8 deliverables
   - Consistent tool model structures
   - Standardized output formats
2. **ElevenLabs Integration** - See TODO Phase 8 translation requirements
   - Vercel Edge Function implementation
   - `translate(message: str, direction: "inbound" | "outbound")` function
3. **Microsoft Presidio Integration** - See TODO Phase 8 security requirements
   - PHI/PII toggle functionality
   - Deterministic security processes
4. **Anthropic Integration** - See TODO Phase 8 LLM requirements
5. **Error Handling** - See TODO Phase 8 error handling requirements

### 📁 Implementation Location
- **Web Search Tool**: `/agents/patient_navigator/shared/web_search_tool.py`
- **Translation Edge Function**: `/agents/patient_navigator/vercel_edge_functions/translation/`
- **Security Edge Function**: `/agents/patient_navigator/vercel_edge_functions/security/`
- **API Clients**: `/agents/patient_navigator/core/clients/` directory
- **Error Handling**: `/agents/patient_navigator/core/error_handling/` directory

### 🔧 Integration Patterns
- **API Clients**: Reference existing API client patterns
- **Error Handling**: Study existing error handling in `/core/resilience/`
- **Rate Limiting**: Use existing rate limiting patterns
- **Retry Logic**: Reference existing retry implementations

### 📊 Success Criteria
- **API Reliability**: See TODO Phase 8 success criteria
- **Error Handling**: See TODO Phase 8 deliverables checklist
- **Performance**: See PRD Section 7 for performance metrics
- **Rate Limiting**: See TODO Phase 8 rate limiting requirements

### 🔄 Phase Completion
- **Documentation**: Create phase_8_decisions.md, phase_8_notes.md, phase_8_handoff.md
- **Next Phase**: See TODO Phase 9 for continuation requirements

---

**Phase Status**: Pending  
**Last Updated**: 2025-10-13  
**Next Review**: 2025-12-08