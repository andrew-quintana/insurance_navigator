# Phase 3 Prompt Template - Security Edge Function

**Phase**: Security Edge Function  
**Duration**: 1 week  
**Focus**: Security Edge Function Component with Microsoft Presidio and generative CoT  
**Start Date**: 2025-10-27  

---

## 🎯 Phase 3 Objectives

Implement Security Edge Function Component with deterministic and generative approaches:
- **TypeScript Vercel Edge Function** implementation
- **Microsoft Presidio WebAssembly Integration** for deterministic PHI/PII detection
- **Chain-of-Thought Sanitization Agent** (100% generative)
- **Security Output Parsing Agent** with TypeScript interface adaptation
- **Vercel Edge Function Deployment** with proper configuration
- **Component-Specific Data Models** for security structures

---

## 📋 Development Guidance

### 📚 Reference Documentation
- **PRD**: `/docs/initiatives/agents/patient_navigator/v0_1/PRD.md` - Complete product requirements
- **RFC**: `/docs/initiatives/agents/patient_navigator/v0_1/RFC.md` - Technical architecture and design
- **TODO**: `/docs/initiatives/agents/patient_navigator/v0_1/TODO.md` - Detailed task breakdown

### 🏗️ Architecture Reference
- **Workflow Diagram**: See RFC Section 3.1 for Mermaid diagram
- **Component Specs**: RFC Section 3.2 for detailed component interfaces
- **Data Models**: RFC Section 3.3 for required data structures

### 🔧 Implementation Guidance
- **Base Agent Pattern**: Reference `/agents/base_agent.py` for agent structure
- **Existing Agents**: Study `/agents/patient_navigator/` for patterns
- **FastAPI Integration**: See `/main.py` for API patterns
- **Configuration**: Use `/config/` directory patterns

### 🎯 Key Deliverables
1. **Security Edge Function Component** - See TODO Phase 3 deliverables
   - TypeScript Vercel Edge Function implementation
   - Microsoft Presidio WebAssembly PII/PHI detection with configurable toggles
   - Chain-of-Thought sanitization agent (100% generative)
   - Security output parsing agent with TypeScript interfaces
   - Deterministic prompt injection pattern detection
2. **Component-Specific Data Models** - Security-specific data structures
   - `SecurityResult` - TypeScript interface for security validation and sanitization results
   - `RiskLevel` - TypeScript enum for security risk levels
3. **Vercel Edge Function Deployment** - Production-ready deployment
   - Environment variable configuration
   - Security event logging and monitoring
   - Health check endpoints

### 📁 Implementation Location
- **Security Edge Function Component**: `/agents/patient_navigator/vercel_edge_functions/security/`
  - `types.ts` - TypeScript interfaces for security data structures
  - `index.ts` - Main Vercel Edge Function entry point
  - `presidioIntegration.ts` - Microsoft Presidio WebAssembly integration
  - `sanitizingAgent.ts` - Chain-of-Thought sanitization agent
  - `structuredOutputParser.ts` - Security output parsing agent
  - `prompts.ts` - Security prompts
  - `tests/` - Component-specific tests
- **Integration**: TypeScript Vercel Edge Function deployment

### 🧪 Testing Reference
- **TypeScript Testing Framework**: Use **Jest** for all Security Edge Function tests
- **Test Configuration**: Use existing `jest.config.js` and `jest.setup.js` in project root
- **Test Location**: Tests in `/agents/patient_navigator/vercel_edge_functions/security/tests/`
- **Python Testing**: Use `pytest.ini` for Python backend components
- **Mock Patterns**: Reference `/backend/mocks/` for test utilities

### 📊 Success Criteria
- **Security Functionality**: Microsoft Presidio and generative CoT implementations working
- **Performance**: Security processing within acceptable latency
- **Vercel Deployment**: Edge Function deployed and accessible
- **Data Models**: Security-specific data structures implemented
- **Error Handling**: Comprehensive error handling and fallback mechanisms

### 🔄 Phase Completion
- **Documentation**: Create phase_3_decisions.md with security architectural decisions
- **Next Phase**: See TODO Phase 4 for Security Edge Function unit tests

---

**Phase Status**: Pending  
**Last Updated**: 2025-10-13  
**Next Review**: 2025-11-03