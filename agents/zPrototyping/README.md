# zPrototyping Directory

This directory contains prototyping tools, utilities, and sandbox environments for architecture exploration and agent development.

## Directory Structure

```
agents/zPrototyping/
├── langgraph_demo.ipynb          # LangGraph workflow patterns and utilities demo
├── sandboxes/                    # Architecture & agent prototype notebooks
│   ├── agent_orchestrator_prototype.ipynb    # Agent orchestration prototypes
│   └── supervisor_architecture_prototype.ipynb  # Supervisor pattern prototypes
├── langgraph_utils.py            # LangGraph utility functions and helpers
├── example_prompt.md             # Sample prompt template
├── example_examples.json         # Sample example data
└── logs/                         # Prototyping logs and debug output
```

## Core Demo Notebook

**`langgraph_demo.ipynb`** - Comprehensive LangGraph patterns demonstration
- Proper StateGraph construction with TypedDict schemas
- Parallel node execution for performance optimization
- Conditional routing and edge management
- Official LangGraph workflow patterns
- Token usage tracking and callback handling
- Removed conditional availability checks for cleaner code

This notebook serves as the primary reference for LangGraph implementation patterns and should be your starting point for understanding the framework.

## Sandboxes Directory (`./sandboxes/`)

The `sandboxes/` subdirectory contains Jupyter notebooks for:

- **Architecture Prototyping**: Testing new system architectures and patterns
- **Agent Updates**: Experimenting with agent behavior modifications
- **Workflow Development**: Building and testing LangGraph workflows
- **Integration Testing**: Validating component interactions

### Current Sandbox Notebooks:

1. **`agent_orchestrator_prototype.ipynb`** - Agent orchestration experiments
   - Multi-agent coordination patterns
   - State management across agents
   - Workflow routing and decision logic

2. **`supervisor_architecture_prototype.ipynb`** - Supervisor pattern exploration
   - Hierarchical agent structures
   - Supervisor-agent communication
   - Resource allocation and task distribution

## Usage Guidelines

### Getting Started

1. **Start with `langgraph_demo.ipynb`** to understand LangGraph patterns and core concepts
2. **Explore sandbox prototypes** to understand current architecture approaches
3. **Create new sandbox notebooks** for your experiments
4. **Reference utility functions** from `langgraph_utils.py`

### Adding New Prototypes

When creating new architecture or agent prototypes:

1. **Create notebooks in `./sandboxes/`** for interactive exploration
2. **Use descriptive naming**: `{component}_{purpose}_prototype.ipynb`
3. **Include clear documentation** within notebooks
4. **Reference utility functions** from `langgraph_utils.py`

### Utility Functions

The `langgraph_utils.py` module provides:

- Prompt composition and template merging
- Structured validation with Pydantic schemas
- Dynamic agent discovery and loading
- LangGraph workflow construction helpers
- Agent prototyping convenience functions

### Best Practices

- **Clean imports**: Remove conditional availability checks
- **Proper state schemas**: Use TypedDict for LangGraph states
- **Clear documentation**: Add markdown cells explaining purpose
- **Error handling**: Include try/catch blocks for debugging
- **Logging**: Use the logs/ directory for debug output

## Integration with Main Codebase

Prototypes in this directory serve as:

- **Testing grounds** for new features before main implementation
- **Documentation** of architectural decisions and patterns
- **Reference implementations** for complex workflows
- **Debugging environments** for troubleshooting issues

## Dependencies

Ensure the following packages are installed for full functionality:

```bash
pip install langgraph langchain-core langchain-community
pip install pydantic typing-extensions
pip install jupyter notebook
```

## Getting Started

1. **Start with `langgraph_demo.ipynb`** to understand LangGraph patterns
2. **Explore existing prototypes** to understand current architecture
3. **Create new sandbox notebooks** for your experiments
4. **Reference utility functions** to avoid duplicate code
5. **Document your findings** for future reference

# Unified Agent Creation with create_agent()

This module provides a comprehensive `create_agent()` function that combines all LangGraph utility features with toggleable options, supporting multiple agent patterns and development workflows.

## 🎯 Quick Start

```python
from langgraph_utils import create_agent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# Define your schema
class MySchema(BaseModel):
    response: str = Field(description="Main response")
    confidence: float = Field(description="Confidence score", ge=0.0, le=1.0)

# Create agent (recommended pattern)
agent = create_agent(
    name="MyAgent",
    prompt_path="my_prompt.md",
    examples_path="my_examples.json",
    output_schema=MySchema,
    llm=ChatOpenAI(model="gpt-4")
)

# Use agent
result = agent("user query")  # Returns MySchema object
print(result.response)
print(result.confidence)
```

## 🎛️ Toggleable Features

### Message Patterns
- `use_system_message=True/False` - Whether to use SystemMessage
- `use_human_message=True/False` - Whether to use HumanMessage for input
- `custom_system_message="text"` - Override prompt files with custom message

### Structured Output
- `use_structured_output=True/False` - Enable/disable schema enforcement
- `output_schema=MySchema` - Pydantic schema for validation
- `pedantic_validation=True/False` - Strict vs lenient validation

### Agent Patterns
- `use_langchain_pattern=True/False` - LangChain vs legacy pattern
- `use_mock_mode=True/False` - Force mock mode for testing

### Prompt Composition
- `merge_examples=True/False` - Whether to merge examples into prompt
- `convert_examples_to_markdown=True/False` - JSON to markdown conversion

### Validation & Debug
- `enable_validation_wrapper=True/False` - Return validation details
- `return_raw_output=True/False` - Include raw LLM output

## 🏆 Recommended Patterns

### Production Agent
```python
# Best practice for production
agent = create_agent(
    name="ProductionAgent",
    prompt_path="prompts/healthcare.md",
    examples_path="examples/healthcare.json",
    output_schema=HealthcareResponse,
    llm=ChatOpenAI(model="gpt-4", temperature=0.1),
    # Defaults are optimal for production
)
```

### Development/Testing
```python
# Mock mode for testing
test_agent = create_agent(
    name="TestAgent",
    custom_system_message="You are a test assistant.",
    output_schema=TestSchema,
    use_mock_mode=True,
    return_raw_output=True  # Debug info
)
```

### Legacy Migration
```python
# Support existing validation patterns
legacy_agent = create_agent(
    name="LegacyAgent",
    prompt_path="legacy_prompt.md",
    output_schema=LegacySchema,
    use_langchain_pattern=False,  # Use legacy pattern
    enable_validation_wrapper=True,  # Return validation details
    llm=llm
)
```

### Plain Text Agent
```python
# No structured output
plain_agent = create_agent(
    name="PlainAgent",
    prompt_path="plain_prompt.md",
    use_structured_output=False,  # Plain text response
    llm=llm
)
```

## 📋 Message Pattern Examples

### SystemMessage + HumanMessage (Default)
```python
agent = create_agent(
    name="StandardAgent",
    custom_system_message="You are a helpful assistant.",
    output_schema=Schema,
    use_system_message=True,    # System prompt
    use_human_message=True,     # User input in HumanMessage
    llm=llm
)
# Creates: [SystemMessage, HumanMessage] → LLM
```

### Combined Message
```python
agent = create_agent(
    name="CombinedAgent",
    custom_system_message="You are a helpful assistant.",
    output_schema=Schema,
    use_system_message=True,
    use_human_message=False,    # Input appended to system message
    llm=llm
)
# Creates: [SystemMessage + user input] → LLM
```

### Single Prompt
```python
agent = create_agent(
    name="SingleAgent",
    custom_system_message="You are a helpful assistant.",
    output_schema=Schema,
    use_system_message=False,   # Everything in one message
    use_human_message=True,
    llm=llm
)
# Creates: [HumanMessage with prompt + input] → LLM
```

## 🔧 Advanced Options

### Custom LLM Configuration
```python
agent = create_agent(
    name="CustomAgent",
    prompt_path="prompt.md",
    output_schema=Schema,
    llm=llm,
    temperature=0.3,        # Override LLM temperature
    max_tokens=1000,        # Override max tokens
    **langchain_kwargs      # Additional with_structured_output() args
)
```

### Validation Modes
```python
# Lenient validation (allows extra fields)
lenient_agent = create_agent(
    name="LenientAgent",
    custom_system_message="Assistant",
    output_schema=Schema,
    pedantic_validation=False,  # Default
    llm=llm
)

# Strict validation (exact schema match)
strict_agent = create_agent(
    name="StrictAgent", 
    custom_system_message="Assistant",
    output_schema=Schema,
    pedantic_validation=True,   # Strict mode
    llm=llm
)
```

### Debug Mode
```python
debug_agent = create_agent(
    name="DebugAgent",
    prompt_path="prompt.md",
    output_schema=Schema,
    return_raw_output=True,     # Include raw LLM response
    enable_validation_wrapper=True,  # Validation details
    llm=llm
)

result = debug_agent("test")
print(result["structured_output"])  # Pydantic object
print(result["raw_output"])         # Raw LLM text
print(result["validation_passed"])  # True/False
```

## 📁 File Structure

### Prompt Files (.md/.txt)
```markdown
# My Agent Prompt

You are a helpful assistant.

## Examples
{{examples}}

## Instructions
1. Analyze the request
2. Provide helpful response

## User Input
{{input}}
```

### Examples Files (.json)
```json
[
  {
    "input": "Example user query",
    "output": "Example response",
    "confidence": 0.9,
    "metadata": {"type": "example"}
  }
]
```

## 🔄 Migration Guide

### From quick_agent_prototype()
```python
# Old
agent = quick_agent_prototype(
    name="Agent",
    prompt_path="prompt.md",
    output_schema=Schema,
    llm=llm
)

# New
agent = create_agent(
    name="Agent",
    prompt_path="prompt.md",
    output_schema=Schema,
    llm=llm
)
```

### From create_langchain_structured_agent()
```python
# Old
agent = create_langchain_structured_agent(
    name="Agent",
    prompt_path="prompt.md",
    examples_path="examples.json",
    output_schema=Schema,
    llm=llm
)

# New (same interface)
agent = create_agent(
    name="Agent",
    prompt_path="prompt.md", 
    examples_path="examples.json",
    output_schema=Schema,
    llm=llm
)
```

## ⚠️ Error Handling

```python
from langgraph_utils import create_agent, PromptMergeError

try:
    agent = create_agent(
        name="Agent",
        # Missing required parameters
    )
except ValueError as e:
    print(f"Configuration error: {e}")

try:
    agent = create_agent(
        name="Agent",
        prompt_path="nonexistent.md",
        output_schema=Schema,
        llm=llm
    )
except PromptMergeError as e:
    print(f"Prompt loading error: {e}")
```

## 🧪 Testing

```python
# Mock mode for unit tests
def test_agent():
    agent = create_agent(
        name="TestAgent",
        custom_system_message="Test assistant",
        output_schema=TestSchema,
        use_mock_mode=True
    )
    
    result = agent("test input")
    assert isinstance(result, TestSchema)
    assert result.confidence == 0.8  # Mock default
```

## 🎯 Key Benefits

- **Unified Interface**: One function for all agent patterns
- **Backward Compatible**: Supports existing code
- **Future-Proof**: Uses LangChain best practices by default
- **Flexible**: All features toggleable
- **Production Ready**: Proper error handling
- **Development Friendly**: Mock mode and debug options
- **Type Safe**: Full Pydantic integration
- **Well Documented**: Comprehensive examples and patterns

## 📚 See Also

- `create_agent_demo.ipynb` - Interactive demonstration
- `langgraph_demo.ipynb` - Original utility demonstrations
- `workflow_agent_comparison.ipynb` - Agent pattern comparisons 