# Insurance Navigator System

A comprehensive multi-agent system for navigating healthcare insurance options, focusing on Medicare.

## Overview

The Insurance Navigator system consists of multiple specialized agents that work together to help users understand their healthcare options, verify document requirements, and develop strategies for accessing healthcare services.

## Architecture

The system is built on a modular architecture with four main agents:

1. **Prompt Security Agent**: Validates user inputs for security issues
2. **Patient Navigator Agent**: Front-facing agent that understands user needs and questions
3. **Task Requirements Agent**: Determines required documentation for service requests
4. **Service Access Strategy Agent**: Develops strategies for accessing healthcare services

Each agent has standardized components:
- Core implementation files
- Pydantic models for type safety
- Standard error handling
- Unit tests
- Configuration through a centralized config manager

## Directory Structure

```
insurance_navigator/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── common/
│   │   └── exceptions.py
│   ├── prompt_security/
│   │   ├── core/
│   │   ├── models/
│   │   └── tests/
│   ├── patient_navigator/
│   │   ├── core/
│   │   ├── models/
│   │   └── tests/
│   ├── task_requirements/
│   │   ├── core/
│   │   ├── models/
│   │   └── tests/
│   └── service_access_strategy/
│       ├── core/
│       ├── models/
│       └── tests/
├── config/
│   └── agent_config.json
├── utils/
│   └── config_manager.py
└── examples/
    └── insurance_navigator_example.py
```

## Key Features

- **Standardized Error Handling**: Consistent hierarchy of exceptions
- **Type Safety**: Pydantic models for all agent inputs and outputs
- **Modular Components**: Clean boundaries between agents
- **Comprehensive Testing**: Unit tests for each agent
- **Configurability**: Centralized configuration
- **Resilience**: Graceful handling of component failures

## DRY (Don't Repeat Yourself) Principles

The refactored codebase follows DRY principles by:

1. **Common BaseAgent**: Implementing shared functionality in the BaseAgent class
   - Standardized prompt loading with fallbacks
   - Consistent error handling
   - Performance tracking
   - Logging configuration
   
2. **Shared Models**: Using Pydantic models consistently across the system
   - Each agent has dedicated model files
   - Models are exported through the main `__init__.py`
   - Cross-agent referencing when needed

3. **Unified Exceptions**: Implementing a hierarchy of exceptions for specific error cases
   - Base exceptions for general categories
   - Agent-specific exceptions for detailed error reporting
   - Consistent error handling patterns

## Getting Started

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run the example:

```bash
python examples/insurance_navigator_example.py
```

## Development

To extend or modify the system:

1. Follow the modular architecture
2. Add new agent functionality in a dedicated module
3. Use Pydantic for all data models
4. Add appropriate exception types
5. Write comprehensive tests
6. Update the config file

## License

MIT 