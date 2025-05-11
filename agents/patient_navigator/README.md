# Patient Navigator Agent

This module provides the patient navigator agent implementation.

## Directory Structure

```
patient_navigator/
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
from agents.patient_navigator import PatientnavigatorAgent

# Initialize the agent
agent = PatientnavigatorAgent()

# Use the agent
result = agent.process(input_data)
```

## Testing

Run the test suite:

```bash
# Run unit tests
pytest agents/patient_navigator/tests/unit/

# Run integration tests
pytest agents/patient_navigator/tests/integration/
```

## Versioning

See `changelog.md` for version history and changes.
