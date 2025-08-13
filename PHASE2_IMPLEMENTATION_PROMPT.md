# Phase 2: Testing & Refinement Implementation

## Implementation Context

You are implementing **Phase 2 (Week 2)** of the Output Communication Agent MVP from `/docs/initiatives/agents/patient_navigator/output_workflow/TODO001.md`. Phase 1 (core implementation) should be complete with the basic communication agent structure.

## Phase 2 Objectives

Focus on **testing, refinement, and production readiness** of the MVP Output Communication Agent workflow.

## Expected File Structure

```
agents/patient_navigator/output_processing/
├── __init__.py
├── types.py                    # Data models (from Phase 1)
├── config.py                   # Configuration (from Phase 1)
├── agent.py                    # CommunicationAgent class (from Phase 1)
├── workflow.py                 # OutputWorkflow class (from Phase 1)
└── prompts/
    └── system_prompt.md        # Communication prompt (from Phase 1)

tests/agents/patient_navigator/output_processing/
├── __init__.py
├── test_communication_agent.py  # NEW - Agent unit tests
├── test_workflow.py             # NEW - Workflow tests
├── test_integration.py          # NEW - End-to-end tests
└── test_data/                   # NEW - Sample workflow outputs
    ├── sample_information_retrieval.json
    ├── sample_strategy_creator.json
    ├── sample_regulatory_agent.json
    └── sample_supervisor_workflow.json
```

## Existing Workflow Output Models

The communication agent must handle outputs from all existing patient navigator workflows:

**InformationRetrievalOutput** (from `agents/patient_navigator/information_retrieval/models.py`):
- `expert_reframe: str` - Expert-level query reframing
- `direct_answer: str` - Concise response to user query
- `key_points: List[str]` - Ranked information points
- `confidence_score: float` - Self-consistency confidence (0.0-1.0)
- `source_chunks: List[SourceChunk]` - Source attribution

**StrategyCreatorOutput** (from `agents/patient_navigator/strategy/creator/models.py`):
- `title: str` - Strategy title
- `category: str` - Strategy category
- `approach: str` - Strategic approach description
- `rationale: str` - Reasoning behind strategy
- `actionable_steps: List[str]` - Concrete steps to take
- `llm_scores: StrategyScores` - Speed/cost/effort scores

**RegulatoryAgentOutput** (from `agents/patient_navigator/strategy/regulatory/models.py`):
- `compliance_status: str` - 'approved', 'flagged', 'rejected'
- `validation_reasons: List[ValidationReason]` - Compliance details
- `confidence_score: float` - Validation confidence
- `source_references: List[SourceReference]` - Regulatory sources

**SupervisorWorkflowOutput** (from `agents/patient_navigator/supervisor/models.py`):
- `routing_decision: Literal["PROCEED", "COLLECT"]` - Next action
- `prescribed_workflows: List[WorkflowType]` - Recommended workflows
- `next_steps: List[str]` - User action items
- `document_availability: DocumentAvailabilityResult` - Document status

## Phase 2 Implementation Tasks

### Task 1: Create Comprehensive Test Suite

Create test files with real workflow output models:

**tests/agents/patient_navigator/output_processing/test_communication_agent.py:**
- Test communication agent with InformationRetrievalOutput, StrategyCreatorOutput, RegulatoryAgentOutput, SupervisorWorkflowOutput
- Validate tone improvement (warmth, empathy) for each workflow type
- Test insurance terminology conversion for different output content
- Verify error handling and fallbacks with malformed workflow outputs

**tests/agents/patient_navigator/output_processing/test_workflow.py:**
- Test end-to-end workflow processing with actual workflow output models
- Validate CommunicationRequest/CommunicationResponse interface compliance
- Test error scenarios and recovery with real model validation
- Performance testing with realistic workflow output sizes

**tests/agents/patient_navigator/output_processing/test_integration.py:**
- Integration with existing agent patterns from `agents/patient_navigator/`
- Test multiple workflow output consolidation (e.g., Information Retrieval + Strategy Creator)
- Validate existing workflow compatibility with actual model schemas

### Task 2: Create Test Data

Create `test_data/` directory with realistic sample workflow outputs using actual models:

**Information Retrieval Output samples:**
- `sample_information_retrieval.json` - InformationRetrievalOutput with expert_reframe, direct_answer, key_points, source_chunks, confidence_score

**Strategy Creator Output samples:**
- `sample_strategy_creator.json` - StrategyCreatorOutput with title, category, approach, rationale, actionable_steps, llm_scores

**Regulatory Agent Output samples:**
- `sample_regulatory_agent.json` - RegulatoryAgentOutput with compliance_status, validation_reasons, confidence_score, source_references

**Supervisor Workflow Output samples:**
- `sample_supervisor_workflow.json` - SupervisorWorkflowOutput with routing_decision, prescribed_workflows, next_steps, document_availability

### Task 3: Manual Testing & Prompt Refinement

Test the communication agent prompt with real workflow outputs and refine based on:
- **Warmth evaluation**: Does the response feel supportive for each workflow type?
- **Clarity assessment**: Are technical terms from each workflow explained clearly?
- **Empathy validation**: Appropriate sensitivity for regulatory rejections, document collection requests?
- **Actionability check**: Clear next steps derived from workflow-specific outputs?

### Task 4: Performance & Integration Validation

- Test with existing workflow patterns in `agents/patient_navigator/`
- Validate error handling with actual Pydantic model validation errors
- Check response times with realistic workflow output sizes
- Ensure CommunicationResponse format meets downstream expectations
- Test workflow type identification and routing logic

### Task 5: Documentation

Add usage documentation:
- **Configuration guide**: How to set up and configure for different workflow types
- **Integration examples**: How to use with existing InformationRetrievalAgent, StrategyCreator, etc.
- **Prompt versioning**: How to refine prompts for different workflow output types
- **Deployment notes**: Production readiness checklist for multi-workflow support

## Reference Patterns

**Follow existing test patterns from:**
- `agents/patient_navigator/input_processing/` test structure
- Configuration patterns in `agents/patient_navigator/input_processing/config.py:58-81`
- BaseAgent testing patterns from `agents/base_agent.py`

**Use BaseAgent inheritance pattern:**
```python
class CommunicationAgent(BaseAgent):
    def __init__(self, llm_client=None, **kwargs):
        super().__init__(
            name="output_communication",
            prompt="prompts/system_prompt.md",
            output_schema=CommunicationResponse,
            llm=llm_client,  # Claude Haiku
            **kwargs
        )
```

**Import actual workflow models:**
```python
from agents.patient_navigator.information_retrieval.models import InformationRetrievalOutput
from agents.patient_navigator.strategy.creator.models import StrategyCreatorOutput
from agents.patient_navigator.strategy.regulatory.models import RegulatoryAgentOutput
from agents.patient_navigator.supervisor.models import SupervisorWorkflowOutput
```

## Testing Focus Areas

1. **Workflow-Specific Response Quality**: Appropriate tone for information vs strategy vs regulatory outputs
2. **Model Compatibility**: Proper handling of all existing workflow output schemas
3. **Content Consolidation**: Meaningful combination of multiple workflow outputs
4. **Integration**: Smooth workflow with existing agent patterns using real models
5. **Error Resilience**: Graceful handling of Pydantic validation errors from workflow outputs

## Success Criteria

- [ ] Comprehensive test suite with >80% coverage using real workflow models
- [ ] Documented response quality improvements for each workflow type
- [ ] Successful integration with existing workflows using actual output schemas
- [ ] Production-ready error handling for workflow model validation
- [ ] Clear deployment and usage documentation for multi-workflow support

## Implementation Notes

- Run tests with: `pytest tests/agents/patient_navigator/output_processing/`
- Follow existing project pytest conventions
- Use existing `agents/base_agent.py` patterns
- Import and test with actual workflow output models, not mock data
- Maintain compatibility with current agent workflow interfaces
- Focus on MVP simplicity while ensuring production quality with real model schemas

## Next Steps After Phase 2

Phase 2 completion enables:
- Production deployment of MVP communication agent with full workflow compatibility
- User feedback collection on response quality across different workflow types
- Iterative prompt refinement based on real workflow output usage
- Future enhancement planning (workflow-specific personalization, A/B testing)