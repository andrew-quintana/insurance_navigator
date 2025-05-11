# Policy Compliance Agent

This module provides the policy compliance agent implementation.

## Directory Structure

```
policy_compliance/
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
from agents.policy_compliance import PolicycomplianceAgent

# Initialize the agent
agent = PolicycomplianceAgent()

# Use the agent
result = agent.process(input_data)
```

## Testing

Run the test suite:

```bash
# Run unit tests
pytest agents/policy_compliance/tests/unit/

# Run integration tests
pytest agents/policy_compliance/tests/integration/
```

## Versioning

See `changelog.md` for version history and changes.
