# Prompt Security Agent

This module provides a security agent for validating and sanitizing user inputs before they are processed by other agents in the system.

## Directory Structure

```
prompt_security_agent/
├── core/               # Core agent logic
│   └── logic.py       # Main agent implementation
├── prompts/           # Prompt templates and versions
│   └── prompt_v1.0.md # Current prompt version
├── tests/             # Test suite
│   ├── unit/         # Unit tests
│   └── integration/  # Integration tests
├── utils/            # Utility functions
├── __init__.py       # Module exports
├── changelog.md      # Version history
└── README.md         # This file
```

## Features

- Input validation and sanitization
- Threat detection and classification
- Multiple reasoning paths with self-consistency
- Comprehensive logging and error handling
- Integration with LangSmith for tracing and evaluation

## Usage

```python
from agents.prompt_security_agent import PromptSecurityAgent

# Initialize the agent
security_agent = PromptSecurityAgent()

# Process user input
is_safe, sanitized_input, metadata = security_agent.process(user_input)
```

## Testing

Run the test suite:

```bash
# Run unit tests
pytest agents/prompt_security_agent/tests/unit/

# Run integration tests
pytest agents/prompt_security_agent/tests/integration/
```

## Versioning

See `changelog.md` for version history and changes. 