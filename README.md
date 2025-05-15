# Medicare Navigator

A comprehensive insurance policy analysis and navigation system that helps users understand and manage their Medicare coverage options.

## Features

- Document parsing with LlamaParse integration
- Vector storage for efficient document retrieval
- Policy analysis and comparison
- User-friendly interface for Medicare navigation

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Set up environment variables:
```bash
cp .env.template .env
# Edit .env with your API keys
```

## Development

- Python 3.9+
- Uses pytest for testing
- Follows PEP 8 style guide

## Testing

Run tests with:
```bash
python -m pytest
```

## Project Structure

```
medicare_navigator/
├── config/           # Configuration and setup
├── agents/           # Agent modules
│   ├── base_agent.py             # Base agent class
│   ├── prompt_security/          # Prompt security agent
│   │   ├── core/                 # Core implementation
│   │   ├── prompts/              # Prompts and examples
│   │   ├── tests/                # Test cases
│   │   └── logs/                 # Agent-specific logs
│   ├── patient_navigator/        # Patient navigator agent
│   │   ├── core/                 # Core implementation
│   │   ├── prompts/              # Prompts and examples
│   │   ├── tests/                # Test cases
│   │   └── logs/                 # Agent-specific logs
│   └── task_requirements/        # Task requirements agent
│       ├── core/                 # Core implementation
│       ├── prompts/              # Prompts and examples
│       ├── tests/                # Test cases
│       └── logs/                 # Agent-specific logs
├── data/             # Data storage
│   ├── documents/    # Raw documents
│   ├── vectors/      # Vector storage
│   ├── fmea/         # FMEA analysis
│   └── design/       # System design
├── tests/            # Test suite
├── utils/            # Utility functions
└── web/              # Web interface
```

## Agent System

The Medicare Navigator uses a multi-agent architecture where specialized agents work together to process information and provide guidance:

1. **Base Agent**: Foundation for all agents with common functionality
2. **Prompt Security Agent**: Ensures user inputs are safe and free from prompt injections
3. **Policy Compliance Agent**: Evaluates insurance policy compliance
4. **Document Parser Agent**: Extracts structured information from documents
5. **Healthcare Guide Agent**: Develops personalized healthcare guides
6. **Service Provider Agent**: Identifies matching healthcare service providers
7. **Service Access Strategy Agent**: Creates access strategies for healthcare services
8. **Guide to PDF Agent**: Converts healthcare guides to formatted PDF documents
9. **Patient Navigator Agent**: Front-facing chatbot interface for users

## API Integration

The system integrates with:
- LangChain for agent orchestration
- Anthropic's Claude for natural language processing
- Various healthcare and insurance databases

## Prompt Management

Prompts for all agents are stored in separate files in the `prompts/` directory. This approach offers several benefits:

- **Maintainability**: Easier to update and modify prompts
- **Version Control**: Better tracking of prompt changes
- **Collaboration**: Non-developers can contribute prompt improvements
- **Testing**: Easier to test different prompt versions
- **Deployment**: Enables prompt updates without code changes

Agents load prompts automatically using the `prompt_loader` utility:

```python
from utils.prompt_loader import load_prompt

# Load a prompt file
prompt_text = load_prompt("agent_name")
```

For more information on working with prompts, see the [Prompt Conversion Guide](prompts/CONVERSION_GUIDE.md).

## Agent Configuration Management

The system includes a centralized configuration management system for all agents, which provides:

- **Central Configuration**: All agent configurations stored in `config/agent_config.json`
- **Version Tracking**: Track which prompt, example, and test versions are active
- **Performance Metrics**: Record and compare metrics across different configurations
- **Easy Switching**: Quickly switch between different agent configurations

### Agent Configuration Components

Each agent configuration includes the following components:

- **core_file**: Main implementation file for the agent
- **prompt**: Agent prompt file
- **examples**: Example inputs and outputs for the agent
- **test_examples**: Test cases for evaluating agent performance

### Configuration File Structure

The configuration file (`agent_config.json`) has the following structure:

```json
{
  "version": "1.0.0",
  "last_updated": "2023-05-15",
  "agents": {
    "agent_name": {
      "active": true,
      "description": "Agent description",
      "core_file": {
        "path": "path/to/core_file.py",
        "version": "0.1"
      },
      "prompt": {
        "version": "0.1",
        "path": "path/to/prompt_v0_1.md"
      },
      "examples": {
        "version": "0.1",
        "path": "path/to/examples.json"
      },
      "test_examples": {
        "version": "0.1",
        "path": "path/to/test_examples.json"
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

### Using the Configuration Manager

```python
from utils.agent_config_manager import get_config_manager

# Get the configuration manager
config_manager = get_config_manager()

# Get configuration for a specific agent
agent_config = config_manager.get_agent_config("prompt_security")

# Get core file path and version
core_file_path = agent_config["core_file"]["path"]
core_file_version = agent_config["core_file"]["version"]

# Get paths to prompts and examples
prompt_path = agent_config["prompt"]["path"]
examples_path = agent_config["examples"]["path"]
```

### Command-Line Management

The system includes a command-line tool for managing agent configurations:

```bash
# List all agents
python utils/manage_agents.py list

# Show details for an agent
python utils/manage_agents.py show prompt_security

# Update a prompt
python utils/manage_agents.py update-prompt prompt_security \
  --version "0.2" \
  --path "path/to/new/prompt_v0_2.md"

# Run a performance test
python utils/manage_agents.py test prompt_security --mock
```

### Performance Testing

The system includes a standardized performance testing framework:

```bash
# Run performance tests for an agent
python agents/prompt_security/tests/test_performance.py

# View metrics in the generated JSON file
cat agents/prompt_security/metrics/performance_metrics_*.json
```

For more information on the configuration system, see the [Agent Configuration Guide](utils/README_performance_metrics.md).

## License

MIT

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines. 

## Updated Repository Structure

The agent architecture has been refactored to follow a consistent structure with:
- Core implementation in `core/` directories
- Agent-specific logging in `logs/` directories
- Standardized interfaces across agents 