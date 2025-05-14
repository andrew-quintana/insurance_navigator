# Guide to PDF Agent

## Overview
Converts healthcare guides to PDF format

## Features
- PDF generation
- Format preservation
- Image handling
- Table formatting
- Document styling

## Architecture
The agent follows a modular architecture with the following components:
- Core processing engine
- Validation system
- Integration handlers
- Monitoring system
- Reporting module

## Usage
```python
from agents.guide_to_pdf import GuidetoPDFAgentAgent

# Initialize the agent
agent = GuidetoPDFAgentAgent()

# Process content
result = agent.process(content="...")
```

## Configuration
The agent can be configured through environment variables or a configuration file:
- `GUIDE_TO_PDF_LOG_LEVEL`: Logging verbosity
- `GUIDE_TO_PDF_MODE`: Operation mode
- `GUIDE_TO_PDF_CONFIG_PATH`: Configuration file path

## Development
See the [Development Guide](docs/development.md) for setup and contribution guidelines.

## Testing
Run the test suite:
```bash
pytest agents/guide_to_pdf/tests/
```

## License
Proprietary - All rights reserved
