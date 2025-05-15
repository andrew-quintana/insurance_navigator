# Agent Configuration Management System

This system provides a centralized way to manage all agent configurations, including prompts, examples, test cases, and performance metrics.

## Overview

The agent configuration management system consists of:

1. **Central Configuration File** (`config/agent_config.json`): Stores all agent configurations in one place
2. **Configuration Manager** (`utils/agent_config_manager.py`): API for loading and updating configurations
3. **Command-Line Tool** (`utils/manage_agents.py`): CLI for managing configurations
4. **Performance Metrics Framework** (`utils/performance_metrics.py`): Standardized metrics collection

## Configuration File Structure

The configuration file (`agent_config.json`) has the following structure:

```json
{
  "version": "1.0.0",
  "last_updated": "2023-05-15",
  "agents": {
    "agent_name": {
      "active": true,
      "description": "Agent description",
      "prompt": {
        "version": "1.0",
        "path": "path/to/prompt.md",
        "description": "Prompt description"
      },
      "examples": {
        "version": "0.1",
        "path": "path/to/examples.json",
        "description": "Examples description"
      },
      "test_examples": {
        "version": "0.1",
        "path": "path/to/test_examples.json",
        "description": "Test examples description"
      },
      "model": {
        "name": "model-name",
        "temperature": 0.0
      },
      "metrics": {
        "latest_run": "path/to/metrics.json"
      }
    }
  },
  "performance_metrics": {
    "enabled": true,
    "save_directory": "metrics",
    "track_memory": true,
    "track_tokens": true
  }
}
```

## Using the Configuration Manager

### In Code

```python
from utils.agent_config_manager import get_config_manager

# Get the configuration manager
config_manager = get_config_manager()

# Get all agent names
all_agents = config_manager.get_all_agents()

# Get active agent names
active_agents = config_manager.get_active_agents()

# Get configuration for a specific agent
agent_config = config_manager.get_agent_config("prompt_security")

# Get paths to prompts and examples
prompt_path = config_manager.get_prompt_path("prompt_security")
examples_path = config_manager.get_examples_path("prompt_security")
test_examples_path = config_manager.get_test_examples_path("prompt_security")

# Get model configuration
model_config = config_manager.get_model_config("prompt_security")

# Update configurations
config_manager.update_agent_prompt(
    "prompt_security",
    version="1.1",
    path="path/to/new/prompt.md",
    description="New prompt description"
)

# Update metrics
config_manager.update_metrics_run(
    "prompt_security",
    "path/to/metrics.json"
)

# Add a new agent
config_manager.add_new_agent(
    "new_agent",
    description="New agent description",
    prompt={
        "version": "1.0",
        "path": "path/to/prompt.md",
        "description": "Prompt description"
    },
    examples={
        "version": "0.1",
        "path": "path/to/examples.json",
        "description": "Examples description"
    },
    test_examples={
        "version": "0.1",
        "path": "path/to/test_examples.json",
        "description": "Test examples description"
    },
    model={
        "name": "model-name",
        "temperature": 0.0
    }
)
```

## Command-Line Management

The system includes a command-line tool for managing agent configurations:

### Listing Agents

```bash
# List all agents
python utils/manage_agents.py list
```

Output:
```
=== AGENT CONFIGURATION SUMMARY ===
Total Agents: 3
Active Agents: 3
Last Updated: 2023-05-15

ACTIVE AGENTS:
  - prompt_security: v1.0 (claude-3-sonnet-20240229)
  - patient_navigator: v1.0 (claude-3-sonnet-20240229)
  - task_requirements: v0.1 (claude-3-sonnet-20240229)

INACTIVE AGENTS:
```

### Showing Agent Details

```bash
# Show details for an agent
python utils/manage_agents.py show prompt_security
```

Output:
```
=== PROMPT_SECURITY ===
Active: True
Description: Agent responsible for ensuring prompt security and content safety
Prompt: v1.0 - agents/prompt_security/prompts/prompt_v1.0.md
Examples: v0.1 - agents/prompt_security/prompts/examples/prompt_examples_prompt_security.json
Test Examples: v0.1 - agents/prompt_security/tests/examples/test_examples_prompt_security.json
Model: claude-3-sonnet-20240229 (temp=0.0)
Latest Metrics: agents/prompt_security/metrics/performance_metrics_20250515_103235.json
```

### Updating Agent Configurations

```bash
# Update a prompt
python utils/manage_agents.py update-prompt prompt_security \
  --version "1.1" \
  --path "path/to/new/prompt.md" \
  --description "New prompt description"

# Update examples
python utils/manage_agents.py update-examples prompt_security \
  --version "0.2" \
  --path "path/to/new/examples.json" \
  --description "New examples description"

# Update test examples
python utils/manage_agents.py update-test-examples prompt_security \
  --version "0.2" \
  --path "path/to/new/test_examples.json" \
  --description "New test examples description"
```

### Adding and Removing Agents

```bash
# Add a new agent
python utils/manage_agents.py add new_agent \
  --description "New agent description" \
  --prompt-version "1.0" \
  --prompt-path "path/to/prompt.md" \
  --prompt-description "Prompt description" \
  --examples-version "0.1" \
  --examples-path "path/to/examples.json" \
  --examples-description "Examples description" \
  --test-examples-version "0.1" \
  --test-examples-path "path/to/test_examples.json" \
  --test-examples-description "Test examples description" \
  --model-name "model-name" \
  --temperature 0.0

# Remove an agent
python utils/manage_agents.py remove new_agent
```

### Running Performance Tests

```bash
# Run a performance test
python utils/manage_agents.py test prompt_security --mock
```

## Integrating with Agents

To integrate an agent with the configuration system:

1. Update the agent's initialization to use the configuration manager:

```python
from utils.agent_config_manager import get_config_manager

class YourAgent:
    def __init__(self, name="your_agent"):
        # Get configuration
        config_manager = get_config_manager()
        agent_config = config_manager.get_agent_config(name)
        
        # Get prompt version from config
        prompt_version = agent_config["prompt"]["version"]
        prompt_path = agent_config["prompt"]["path"]
        
        # Get model config
        model_config = agent_config["model"]
        
        # Initialize with configuration
        # ...
```

2. Create a performance test script:

```python
from utils.performance_metrics import PerformanceEvaluator, TestCase
from utils.agent_config_manager import get_config_manager

def main():
    # Get configuration
    config_manager = get_config_manager()
    agent_config = config_manager.get_agent_config("your_agent")
    
    # Load test cases from the configured path
    test_examples_path = agent_config["test_examples"]["path"]
    test_cases = load_test_cases(test_examples_path)
    
    # Run tests and save metrics
    # ...
    
    # Update the configuration with the latest metrics run
    config_manager.update_metrics_run("your_agent", metrics_file)
```

## Best Practices

1. **Always use the configuration manager** to access agent configurations
2. **Keep the configuration file up to date** with the latest prompt and example versions
3. **Run performance tests** after making changes to prompts or examples
4. **Compare metrics** between different versions to track improvements
5. **Use the command-line tool** for managing configurations instead of editing the JSON file directly

## Troubleshooting

If you encounter issues with the configuration system:

1. **Check the configuration file** for syntax errors
2. **Verify file paths** in the configuration file
3. **Ensure all referenced files exist** on disk
4. **Check permissions** on the configuration file and referenced files 