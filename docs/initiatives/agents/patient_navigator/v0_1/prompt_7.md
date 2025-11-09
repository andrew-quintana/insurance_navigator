# Phase 7 Prompt Template - Tooling Integration

**Phase**: Tooling Integration  
**Duration**: 1 week  
**Focus**: RAG system integration and internal tooling  
**Start Date**: 2025-11-24  

---

## 🎯 Phase 7 Objectives

Integrate with existing internal systems and optimize performance:
- **RAG Tool Integration** using existing `agents/tooling/rag/core.py` system
- **Database query optimization** for all components
- **Internal tooling connections** across components
- **Performance optimization** for component-based architecture
- **Caching layer implementation** for shared tools
- **Component-specific data model integration** across all components

---

## 📋 Integration Guidance

### 📚 Reference Documentation
- **PRD**: `/docs/initiatives/agents/patient_navigator/v0_1/PRD.md` - Integration requirements
- **RFC**: `/docs/initiatives/agents/patient_navigator/v0_1/RFC.md` - Technical specifications
- **TODO**: `/docs/initiatives/agents/patient_navigator/v0_1/TODO.md` - Phase 7 detailed tasks

### 🔧 Integration Reference
- **Existing Chat Endpoint**: Study `/main.py` chat endpoint implementation
- **Translation Edge Function**: Reference `/agents/patient_navigator/vercel_edge_functions/translation/`
- **Security Edge Function**: Reference `/agents/patient_navigator/vercel_edge_functions/security/`
- **Tool Calling Chat Agent**: Reference `/agents/patient_navigator/tool_calling_chat_agent/`
- **Core Components**: Reference `/agents/patient_navigator/core/`
- **Performance Monitoring**: See `/backend/monitoring/` for monitoring patterns
- **Configuration**: Use `/config/` directory patterns

### 🎯 Key Deliverables
1. **New Chat Endpoint** - See TODO Phase 7 deliverables
   - `/chat/v2` endpoint alongside existing `/chat` endpoint
   - Vercel Edge Function integration
   - Microsoft Presidio security integration
2. **Performance Comparison** - See TODO Phase 7 performance requirements
   - Local environment testing
   - Staging environment testing
   - Performance metrics comparison
3. **Integration Testing** - See TODO Phase 7 testing requirements
   - End-to-end workflow testing
   - Tool model consistency validation
   - PHI/PII toggle functionality testing
4. **Production Preparation** - See TODO Phase 7 production requirements
   - Deployment procedures
   - Monitoring setup
   - Documentation updates

### 📁 Implementation Location
- **New Endpoint**: Add to `/main.py` alongside existing `/chat` endpoint
- **Performance Tests**: `/tests/agents/patient_navigator/integration/` directory
- **Backend Components**: All component directories under `/agents/patient_navigator/`
- **Vercel Edge Functions**: All component directories under `/agents/patient_navigator/vercel_edge_functions/`
- **Monitoring**: Extend existing monitoring in `/backend/monitoring/`
- **Configuration**: Extend existing configuration patterns

### 🔧 Integration Patterns
- **Endpoint Implementation**: Reference existing `/chat` endpoint patterns
- **Component Integration**: HTTP calls between Translation Edge Function, Security Edge Function, and Tool Calling Chat Agent
- **Performance Testing**: Study existing performance test implementations
- **Monitoring**: Use existing monitoring patterns
- **Error Handling**: Follow existing error handling patterns

### 📊 Success Criteria
- **Integration**: See TODO Phase 7 success criteria
- **Performance**: See TODO Phase 7 deliverables checklist
- **Testing**: See PRD Section 7 for performance metrics
- **Production Readiness**: See TODO Phase 7 production requirements

### 🔄 Phase Completion
- **Documentation**: Create phase_7_decisions.md, phase_7_notes.md, phase_7_handoff.md
- **Project Completion**: See TODO project completion requirements

---

**Phase Status**: Pending  
**Last Updated**: 2025-10-13  
**Next Review**: 2025-12-01
