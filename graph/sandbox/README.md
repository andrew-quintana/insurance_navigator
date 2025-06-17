# Agent/Workflow Prototyping Sandbox

A comprehensive development environment for rapid agent and workflow prototyping in the Insurance Navigator system.

## Structure

```
graph/sandbox/
├── src/
│   ├── prototyping_studio.py  # Core implementation classes
│   ├── examples.py            # Comprehensive examples
│   └── __init__.py           # Package initialization
├── notebooks/
│   └── agent_workflow_prototyping.ipynb  # Interactive prototyping notebook
└── README.md                 # This file
```

## Features

### 🔍 **Auto-Discovery**
- Automatically discovers all existing agents in the `/agents` directory
- Imports all model classes for easy access via `Models.` namespace
- No manual configuration required

### 🧪 **Agent Prototyping**
- **Lightweight agents** without BaseAgent inheritance overhead
- **Hot-swappable configurations** (prompts, model params, memory)
- **Real Anthropic integration** - Full Claude model support
- **Session-only changes** - no file modifications
- Built-in conversation history and memory management

### 🔗 **Workflow Design**
- **Sequential workflows** with simple agent chaining
- **Conditional branching** with custom logic functions
- **Workflow visualization** and debugging
- **Local state management** mimicking existing systems

### 🤖 **Existing Agent Testing**
- **Mock/Real toggle** for safe testing
- Respects existing agent mock implementations
- Easy switching between development and production modes
- Compatible with all existing agent types

### 📊 **Testing Framework**
- **Comprehensive test suites** for validation
- **Agent comparison** across multiple inputs
- **Performance tracking** and results storage
- **Structured test case definition**

## Quick Start

1. **Open the notebook**: `graph/sandbox/notebooks/agent_workflow_prototyping.ipynb`
2. **Run the initialization cells** to set up the environment
3. **Explore the examples** to see all capabilities
4. **Create your own** agents and workflows in the sandbox cells

## Example Usage

### Create a Prototype Agent
```python
# Quick agent creation with real Anthropic models
agent = lab.quick_agent(
    name="my_agent",
    prompt="You are a helpful assistant. Respond to: {input}",
    model_name="claude-3-haiku-20240307",
    temperature=0.7,
    max_tokens=500
)

# Test it with real Claude API
result = agent.process("Hello world!", use_model=True)
```

### Hot-Swap Configuration
```python
# Update prompt template
config_panel.edit_agent_prompt("my_agent", "New prompt: {input}")

# Update model parameters
config_panel.edit_model_params("my_agent", temperature=0.3, max_tokens=1000)

# Add memory
config_panel.edit_memory("my_agent", {"context": "healthcare"})
```

### Create a Workflow
```python
# Create workflow with conditional branching
workflow = lab.quick_workflow("my_workflow")
workflow.add_agent(agent1)
workflow.add_agent(agent2)
workflow.add_conditional_branch(condition_func, true_agent, false_agent)

# Execute it
result = workflow.execute("Test input")
```

### Test Existing Agents
```python
# Load in mock mode
existing_tester.load_agent("PatientNavigatorAgent", use_mock=True)

# Test it
result = existing_tester.test_agent("PatientNavigatorAgent", "Find me a cardiologist")

# Toggle to real mode
existing_tester.toggle_mode("PatientNavigatorAgent")
```

## Key Benefits

✅ **Rapid Iteration** - Hot-swap configurations without restarting  
✅ **Real Anthropic Models** - Full Claude integration with all models  
✅ **Safe Testing** - Session-only changes, no file modifications  
✅ **Easy Discovery** - Auto-imports all agents and models  
✅ **Workflow Prototyping** - Design complex agent chains quickly  
✅ **Production Integration** - Test existing agents safely  
✅ **Comprehensive Testing** - Built-in validation framework  

## Integration with Existing System

The sandbox is designed to work seamlessly with your existing agent architecture:

- **Respects existing mock implementations** in each agent
- **Uses existing model classes** for consistency
- **Mimics existing memory/state systems** locally
- **Compatible with all agent types** in the system
- **No modifications** to production code required

## Development Workflow

1. **Prototype** new agent ideas quickly
2. **Test variations** of prompts and configurations
3. **Design workflows** with conditional logic
4. **Validate** with comprehensive test suites
5. **Graduate** successful prototypes to full implementation

This sandbox provides a complete development environment for agent and workflow experimentation while maintaining full compatibility with your production system. 