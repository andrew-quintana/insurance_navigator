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
│   ├── prompt_security.py        # Prompt security agent
│   ├── policy_compliance.py      # Policy compliance agent
│   ├── document_parser.py        # Document parser agent
│   ├── healthcare_guide.py       # Healthcare guide agent
│   ├── service_provider.py       # Service provider agent
│   ├── service_access_strategy.py # Service access strategy agent
│   ├── guide_to_pdf.py           # Guide to PDF agent
│   └── patient_navigator.py      # Patient navigator agent
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

## License

MIT

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines. 

## Updated Repository Structure

The agent architecture has been refactored to follow a consistent structure with:
- Core implementation in `core/` directories
- Agent-specific logging in `logs/` directories
- Standardized interfaces across agents 