Implement MVP Output Communication Agent following TODO001.md Week 1 tasks.

**Study existing patterns:**
- `agents/base_agent.py` - BaseAgent class for inheritance
- `agents/patient_navigator/information_retrieval/agent.py` - reference implementation
- `agents/patient_navigator/input_processing/config.py` - configuration patterns

**Create directory structure:**
```
agents/patient_navigator/output_processing/
├── __init__.py
├── types.py  
├── agent.py
├── config.py
├── prompts/
│   ├── __init__.py
│   └── system_prompt.md
└── tests/
    ├── __init__.py
    └── test_agent.py
```

**Key files to implement:**

1. **types.py** - Pydantic models:
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class AgentOutput(BaseModel):
    agent_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CommunicationRequest(BaseModel):
    agent_outputs: List[AgentOutput]
    user_context: Optional[Dict[str, Any]] = None

class CommunicationResponse(BaseModel):
    enhanced_content: str
    original_sources: List[str]
    processing_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

2. **agent.py** - CommunicationAgent inheriting from BaseAgent:
```python
from agents.base_agent import BaseAgent
from .types import CommunicationRequest, CommunicationResponse

class CommunicationAgent(BaseAgent):
    def __init__(self, llm_client=None, **kwargs):
        super().__init__(
            name="output_communication",
            prompt="prompts/system_prompt.md",
            output_schema=CommunicationResponse,
            llm=llm_client,  # Claude Haiku
            **kwargs
        )
    
    async def enhance_response(self, request: CommunicationRequest) -> CommunicationResponse:
        # Process agent outputs with warm, empathetic communication
```

3. **prompts/system_prompt.md** - Communication prompt:
```
You are a warm, empathetic insurance navigator assistant. Transform technical agent outputs into supportive responses.

Input: {{input}}

Guidelines:
- Use friendly, supportive language acknowledging insurance can be stressful
- Show appropriate empathy for sensitive topics (claim denials, limitations)
- Be encouraging and reassuring while remaining accurate
- Convert insurance jargon to plain language with brief explanations
- Structure information clearly with headers/bullets when helpful
- Maintain factual accuracy from original outputs
- Integrate multiple agent outputs into cohesive response
- Include clear next steps when helpful

Special handling:
- Claim denials/limitations: Extra empathy, clear explanations, alternative options
- Benefits explanations: Focus on clarity and practical examples  
- Form assistance: Encouraging tone with step-by-step guidance
- Eligibility results: Clear, supportive messaging about coverage status

Return structured JSON response with enhanced_content, original_sources, processing_time, and metadata.
```

4. **config.py** - Following input_processing patterns:
```python
from dataclasses import dataclass
from typing import Optional, Dict, Any
import os

@dataclass 
class OutputProcessingConfig:
    llm_model: str = "claude-3-haiku"
    request_timeout: float = 30.0
    max_input_length: int = 10000
    
    @classmethod
    def from_environment(cls):
        return cls(
            llm_model=os.getenv("OUTPUT_PROCESSING_LLM_MODEL", "claude-3-haiku"),
            request_timeout=float(os.getenv("OUTPUT_PROCESSING_TIMEOUT", "30.0"))
        )
```

5. **tests/test_agent.py** - Basic unit tests with mock data

**Requirements:**
- Inherit from BaseAgent using same patterns as information_retrieval agent
- Use Claude Haiku LLM (consistent with other agents)
- Follow existing config/prompt/testing patterns
- Include error handling with fallback to original content
- Test with sample insurance-related agent outputs

**Save documentation:**
- `@TODO001_phase1_notes.md` (implementation details, decisions made)
- `@TODO001_phase1_decisions.md` (why BaseAgent pattern, Claude Haiku choice)  
- `@TODO001_phase1_test_update.md` (testing approach, sample results)
- `@TODO001_phase1_handoff.md` (status, next steps for Phase 2)