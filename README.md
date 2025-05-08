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
├── agents/           # AI agents for policy analysis
├── tests/           # Test suites
│   ├── config/      # Configuration tests
│   ├── agents/      # Agent tests
│   └── data/        # Test data
└── docs/            # Documentation
```

## License

MIT License 