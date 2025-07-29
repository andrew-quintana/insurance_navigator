# Information Retrieval Agent - Implementation Context

## Overview
This document provides comprehensive context for implementing the Information Retrieval Agent within the patient navigator domain. The agent will translate user queries into insurance terminology, utilize the existing RAG system, and provide consistent, accurate responses using self-consistency methodology.

## Current State Analysis

### ✅ Existing RAG System (`agents/tooling/rag/core.py`)
- **MVP Implementation**: Production-ready foundation with `RetrievalConfig`, `ChunkWithContext`, and `RAGTool` classes
- **Features**: 
  - User-scoped access control with database-level security
  - Token budget enforcement (configurable limits)
  - Vector similarity search via pgvector extension
  - Configurable similarity thresholds and result limits
- **Database Integration**: 
  - Supabase integration with `documents.document_chunks` table
  - Proper connection management and error handling
  - User access control at the database level
- **Performance**: Optimized for <200ms per document query with token budget management

### ✅ Prototype Design (`agents/zPrototyping/sandboxes/20250621_architecture_refactor/information_retrieval_workflow/`)
- **Design Philosophy**: ReAct framework with self-consistency validation
- **Key Components**:
  - Expert query reframing for insurance terminology
  - Multiple response generation (3-5 variants)
  - Consistency verification across responses
  - Confidence scoring based on agreement
- **Output Structure**: Structured JSON with:
  - `expert_reframe`: Professionally reframed query
  - `direct_answer`: Concise, focused response
  - `key_points`: Ranked list of relevant information
  - `confidence_score`: 0.0-1.0 based on consistency
- **Templates**: Complete system prompt, examples, and human message templates ready for adaptation

### ✅ LangGraph Reference Implementation (`supervisor_workflow/`)
- **Architecture**: Production-ready LangGraph workflow with proper state management
- **Agent Chain**: Workflow Prescription → Document Requirements → Document Availability → Router
- **Testing**: Comprehensive test suite demonstrating 85-90% success rates
- **Model Configuration**: Cost-optimized Claude Haiku setup with budget considerations
- **Patterns**: Established patterns for agent creation, state management, and error handling

### ✅ Existing Agent Patterns
- **BaseAgent**: Standard inheritance pattern used across all production agents
- **Directory Structure**: Established patterns with `models/`, `prompts/`, `tests/` organization
- **Pydantic Models**: Structured I/O with validation (see `WorkflowPrescriptionOutput`)
- **Error Handling**: Graceful degradation and fallback strategies

## Key Gaps Identified

### 🔧 Missing Integration Components
1. **Translation Layer**: 
   - No insurance document terminology translation capability
   - Need mapping from common language to insurance-specific terms
   - Should handle synonyms and context-specific interpretations

2. **Embedding Generation**: 
   - No query embedding generation for RAG search
   - Current RAG system expects embeddings as input
   - Need integration with embedding service/model

3. **Response Synthesis**: 
   - No mechanism to combine RAG results with expert reframing
   - Missing structured response generation from retrieved chunks
   - Need confidence scoring based on retrieval quality

4. **Error Handling**: 
   - Limited fallback strategies for RAG failures
   - No graceful degradation when documents unavailable
   - Missing user-friendly error messages for different failure modes

5. **Context Management**: 
   - No session memory for follow-up questions
   - Missing conversation state preservation
   - No reference to previous query context

### 🏗️ Technical Integration Challenges
1. **RAG Integration**: 
   - Prototype doesn't connect to actual RAG system
   - Need proper embedding generation pipeline
   - Require chunk relevance assessment and filtering

2. **Query Processing Pipeline**: 
   - Missing query preprocessing and normalization
   - No insurance terminology mapping implementation
   - Need query expansion for better retrieval

3. **Response Quality Assessment**: 
   - No quality scoring of retrieved chunks
   - Missing relevance filtering mechanisms
   - Need confidence calibration based on retrieval results

4. **Performance Optimization**: 
   - No caching for repeated queries
   - Missing query optimization strategies
   - Need response time monitoring and optimization

## Target Architecture: Domain-Driven Organization

### 🎭 Proposed Structure
```
agents/
├── patient_navigator/                 # Patient navigation domain
│   ├── __init__.py                    # Domain initialization
│   ├── information_retrieval/         # NEW: Information retrieval agent
│   │   ├── __init__.py
│   │   ├── agent.py                   # Main IR agent implementation (~200-300 lines)
│   │   ├── models.py                  # I/O models (queries, responses)
│   │   └── prompts/
│   │       ├── system_prompt.md       # Expert reframing system prompt
│   │       ├── human_message.md       # User input template
│   │       └── examples.json          # Few-shot examples
│   ├── workflow_prescription/         # MOVE: Existing agent into domain
│   │   └── [existing files]           # Relocate from current location
│   └── shared/                        # Domain-specific utilities
│       ├── __init__.py
│       ├── terminology.py             # Insurance term translation
│       └── consistency.py             # Self-consistency methodology
└── tooling/                           # Cross-domain utilities (unchanged)
    └── rag/                           # Existing vector retrieval system
```

### 🔗 Key Integration Points
1. **Existing RAG System**: Direct integration with `agents/tooling/rag/core.py`
2. **Supabase Database**: Existing document storage and vector search capabilities
3. **LangGraph Patterns**: Follow supervisor_workflow implementation patterns
4. **BaseAgent Pattern**: Inherit from existing BaseAgent for consistency
5. **Insurance Knowledge Base**: Domain-specific terminology and context mapping

## Implementation Requirements

### 🎯 Core Functionality Requirements
1. **Query Translation**:
   - Accept natural language user input
   - Translate to insurance-specific terminology
   - Generate expert-level query reframing
   - Handle synonyms and context variations

2. **RAG Integration**:
   - Generate embeddings for semantic search
   - Use existing `RAGTool` for document retrieval
   - Apply similarity thresholds and token budgets
   - Filter and rank retrieved chunks

3. **Response Generation**:
   - Apply self-consistency methodology
   - Generate 3-5 response variants
   - Calculate consistency-based confidence scores
   - Synthesize final structured response

4. **Output Formatting**:
   - Provide structured JSON output
   - Include confidence scoring and source attribution
   - Maintain compatibility with existing agent ecosystem
   - Support follow-up question context

### 📊 Success Metrics
1. **Query Translation Accuracy**: >90% accurate insurance terminology mapping
2. **RAG Retrieval Relevance**: >0.7 similarity threshold for included chunks
3. **Response Consistency**: >0.8 agreement across multiple generated responses
4. **User Satisfaction**: Measured through response completeness and accuracy
5. **Performance**: <2s total response time including RAG retrieval
6. **Integration**: 100% compatibility with existing BaseAgent patterns

### 🔄 MVP Implementation Scope

#### Phase 1: Foundation Setup (Week 1)
- Create domain-driven directory structure under `patient_navigator/`
- Move existing `workflow_prescription/` into domain
- Set up basic agent structure inheriting from BaseAgent
- Adapt prototype prompts for production use

#### Phase 2: Core Implementation (Week 2)
- Implement insurance terminology translation (keyword-based mapping)
- Direct integration with existing `agents/tooling/rag/core.py`
- Basic self-consistency methodology (3 response variants)
- Structured JSON output matching prototype specification

#### Phase 3: Integration & Testing (Week 3)
- Basic unit tests for terminology translation
- Integration testing with existing RAG system
- Response quality validation and consistency checks
- Performance optimization and error handling

### 🛠️ Technical Implementation Details

#### Agent Architecture
```python
class InformationRetrievalAgent(BaseAgent):
    """
    Information retrieval agent for insurance document navigation.
    
    Inherits from BaseAgent following established patterns.
    Integrates with existing RAG system and terminology utilities.
    """
    
    def __init__(self, use_mock: bool = False, **kwargs):
        super().__init__(use_mock=use_mock, **kwargs)
        self.terminology_translator = InsuranceTerminologyTranslator()
        self.consistency_checker = SelfConsistencyChecker()
        self.rag_tool = None  # Initialized with user context
    
    def retrieve_information(self, user_query: str, user_id: str) -> InformationRetrievalOutput:
        """Main entry point for information retrieval."""
        # 1. Translate query to insurance terminology
        # 2. Generate embeddings and retrieve chunks
        # 3. Apply self-consistency methodology
        # 4. Return structured response
```

#### Domain Utilities
```python
class InsuranceTerminologyTranslator:
    """Translates common language to insurance-specific terminology."""
    
    def translate_query(self, query: str) -> str:
        """Convert user query to expert insurance terminology."""
        # Simple keyword mapping for MVP
        # Future: ML-based translation
    
class SelfConsistencyChecker:
    """Implements self-consistency methodology for response validation."""
    
    def generate_variants(self, chunks: List[ChunkWithContext]) -> List[str]:
        """Generate multiple response variants from retrieved chunks."""
    
    def calculate_consistency(self, responses: List[str]) -> float:
        """Calculate consistency score across response variants."""
```

## Context for Documentation Generation

### PRD Context
- **Business Need**: Insurance document navigation is complex; users need expert-level information retrieval
- **User Stories**: "As a patient, I want to ask questions in plain language and get accurate insurance information"
- **Success Criteria**: High accuracy, fast response times, user-friendly explanations
- **Integration Requirements**: Must work with existing patient navigator ecosystem
- **Scalability**: Support for multiple insurance types and document formats

### RFC Context  
- **Architecture Decisions**: Domain-driven organization, RAG integration patterns, self-consistency implementation
- **Technical Constraints**: Must use existing RAG system, follow BaseAgent patterns, integrate with Supabase
- **Performance Requirements**: <2s response time, >0.7 retrieval relevance, >0.8 consistency scores
- **Security Considerations**: User-scoped access, secure database integration, input validation
- **Extensibility**: Support for future agents, terminology expansion, RAG enhancements

### TODO Context
- **Implementation Phases**: Foundation → Core Implementation → Integration & Testing
- **Dependencies**: Existing RAG system, BaseAgent patterns, Supabase infrastructure
- **Testing Strategy**: Unit tests for utilities, integration tests for RAG, performance validation
- **Deployment Requirements**: Domain restructuring, agent registration, monitoring setup
- **Success Milestones**: MVP delivery, integration validation, production readiness

## Existing Code References

### RAG System Integration
- **File**: `agents/tooling/rag/core.py`
- **Key Classes**: `RAGTool`, `RetrievalConfig`, `ChunkWithContext`
- **Usage Pattern**: 
  ```python
  rag_tool = RAGTool(user_id="user123", config=RetrievalConfig.default())
  chunks = await rag_tool.retrieve_chunks(query_embedding)
  ```

### Agent Pattern Reference
- **File**: `agents/workflow_prescription/workflow_prescription_agent.py`
- **Key Pattern**: BaseAgent inheritance, Pydantic models, structured output
- **Integration**: Process method, error handling, mock capabilities

### LangGraph Integration
- **Reference**: `agents/zPrototyping/sandboxes/20250621_architecture_refactor/supervisor_workflow/`
- **Patterns**: State management, agent chaining, structured workflows
- **Testing**: Comprehensive test suite with realistic scenarios

### Prototype Templates
- **Location**: `agents/zPrototyping/sandboxes/20250621_architecture_refactor/information_retrieval_workflow/`
- **Files**: `system_prompt.md`, `human_message_template.md`, `examples.md`
- **Usage**: Adapt for production prompts with minor modifications

This comprehensive context provides all necessary information for implementing the Information Retrieval Agent while maintaining consistency with existing systems and following established architectural patterns.