# Quality Assurance Agent

This module provides the quality assurance agent implementation.

## Directory Structure

```
quality_assurance/
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
from agents.quality_assurance import QualityassuranceAgent

# Initialize the agent
agent = QualityassuranceAgent()

# Use the agent
result = agent.process(input_data)
```

## Testing

Run the test suite:

```bash
# Run unit tests
pytest agents/quality_assurance/tests/unit/

# Run integration tests
pytest agents/quality_assurance/tests/integration/
```

## Versioning

See `changelog.md` for version history and changes.
