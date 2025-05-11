# Service Provider Agent

This module provides the service provider agent implementation.

## Directory Structure

```
service_provider/
├── core/               # Core agent logic
│   └── logic.py       # Main agent implementation
├── prompts/           # Prompt templates
│   └── prompt_v1.0.md # Current prompt version
├── tests/             # Test suite
│   ├── unit/         # Unit tests
│   └── integration/  # Integration tests
├── utils/            # Utility functions
├── fmea/             # Failure mode analysis
│   └── analysis.json # FMEA data
├── docs/             # Agent documentation
│   └── dfmea.md      # Design FMEA documentation
├── __init__.py       # Module exports
├── changelog.md      # Version history
└── README.md         # This file
```

## Features

- Core agent functionality
- Prompt-based reasoning
- Comprehensive testing
- Failure mode analysis
- Utility functions

## Usage

```python
from agents.service_provider import ServiceproviderAgent

# Initialize the agent
agent = ServiceproviderAgent()

# Use the agent
result = agent.process(input_data)
```

## Testing

Run the test suite:

```bash
# Run unit tests
pytest agents/service_provider/tests/unit/

# Run integration tests
pytest agents/service_provider/tests/integration/
```

## Versioning

See `changelog.md` for version history and changes.
