# Phase 5 Prompt Template - Tool-Enabled Chat Agent

**Phase**: Tool-Enabled Chat Agent  
**Duration**: 1 week  
**Focus**: All-in-one tool-enabled chat agent with Tree of Thoughts framework  
**Start Date**: 2025-11-10  

---

## 🎯 Phase 5 Objectives

Implement all-in-one tool-enabled chat agent with advanced reasoning:
- **Tree of Thoughts Framework** per [Tree of Thoughts Guide](https://www.promptingguide.ai/techniques/tot)
- **Multi-Expert Reasoning Approach** with step-by-step thought evaluation
- **Tool Integration** with Web Search and RAG tools
- **Medical Guardrails** with strict insurance assistance focus
- **Generative Tool Selection** with LLM-based decision making

---

## 📋 Development Guidance

### 📚 Reference Documentation
- **PRD**: `/docs/initiatives/agents/patient_navigator/v0_1/PRD.md` - Complete product requirements
- **RFC**: `/docs/initiatives/agents/patient_navigator/v0_1/RFC.md` - Technical architecture and design
- **TODO**: `/docs/initiatives/agents/patient_navigator/v0_1/TODO.md` - Detailed task breakdown
- **Tree of Thoughts Guide**: [https://www.promptingguide.ai/techniques/tot](https://www.promptingguide.ai/techniques/tot)

### 🏗️ Architecture Reference
- **Tree of Thoughts Framework**: Multi-expert reasoning with backtracking and exploration
- **Tool Integration**: Web Search (service-agnostic) and RAG system integration
- **Medical Guardrails**: Strict prevention of medical advice, insurance assistance only
- **Component Specs**: RFC Section 3.2 for detailed component interfaces

### 🔧 Implementation Guidance
- **Base Agent Pattern**: Reference `/agents/base_agent.py` for agent structure
- **Existing Agents**: Study `/agents/patient_navigator/` for patterns
- **RAG Integration**: Use existing `agents/tooling/rag/core.py` system
- **Web Search Integration**: Use existing `agents/tooling/web_search_tool.py` system
- **Base Tool Integration**: Use existing `agents/tooling/base_tool.py` for tool patterns
- **Configuration**: Use `/config/` directory patterns

### 🎯 Key Deliverables
1. **Tool-Enabled Chat Agent Component** - See TODO Phase 5 deliverables
   - Tree of Thoughts framework implementation
   - Multi-expert reasoning approach
   - Step-by-step thought evaluation
   - Backtracking and exploration mechanisms
2. **Tool Integration** - Comprehensive tool calling framework
   - Web Search Tool integration using existing `agents/tooling/web_search_tool.py`
   - RAG Tool integration using existing `agents/tooling/rag/core.py`
   - Base Tool integration using existing `agents/tooling/base_tool.py`
   - Tool execution framework with consistent variable names
   - Result aggregation logic with common data structures
3. **Medical Guardrails** - Strict insurance assistance focus
   - Generative guardrail implementation
   - Integration with Tree of Thoughts framework
   - Prevention of medical advice and diagnoses

### 📁 Implementation Location
- **Tool-Enabled Chat Agent Component**: `/agents/patient_navigator/tool_calling_chat_agent/`
  - `data_models.py` - Chat agent data structures
  - `chat_agent.py` - Tree of Thoughts architecture
  - `tool_selection.py` - Generative LLM-based selection
  - `response_generation.py` - Medical guardrails
  - `prompts.py` - Tree of Thoughts prompts
  - `tests/` - Component-specific tests
- **Integration**: Reference `/main.py` for FastAPI integration

### 🌳 Tree of Thoughts Implementation
Based on the [Tree of Thoughts Guide](https://www.promptingguide.ai/techniques/tot), implement:
- **Multi-Expert Approach**: "Imagine three different experts are answering this question"
- **Step-by-Step Evaluation**: Each expert writes down 1 step of their thinking
- **Collaborative Reasoning**: Experts share and build on each other's thoughts
- **Self-Correction**: "If any expert realises they're wrong at any point then they leave"
- **Tool Integration**: Tool selection and execution within ToT framework

### 🧪 Testing Reference
- **Test Patterns**: Study `/tests/` directory structure
- **Mock Patterns**: Reference `/backend/mocks/` for test utilities
- **Test Configuration**: Use `/pytest.ini` and existing test setup

### 📊 Success Criteria
- **Tree of Thoughts Functionality**: Multi-expert reasoning working correctly
- **Tool Integration**: Web Search and RAG tools properly integrated
- **Medical Guardrails**: Strict prevention of medical advice
- **Performance**: Response generation within acceptable latency
- **Error Handling**: Comprehensive error handling and fallback mechanisms

### 🔄 Phase Completion
- **Documentation**: Create phase_5_decisions.md with Tree of Thoughts framework decisions
- **Next Phase**: See TODO Phase 6 for Tool-Enabled Chat Agent unit tests

---

**Phase Status**: Pending  
**Last Updated**: 2025-10-13  
**Next Review**: 2025-11-17