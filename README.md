# Medicare Navigator

A HIPAA-aware, agent-based system for navigating Medicare information and providing personalized guidance.

## Project Structure

```
/agents/          # Agent implementations
/tests/           # Test suites (unit, integration, system, security)
/config/          # Configuration and tool definitions
/utils/           # Utility functions and helpers
/graph/           # LangGraph process chains
/data/            # Data storage
/ui/              # Frontend interface
/docs/            # Documentation
/logs/            # Logging directories
```

## Features

- Multi-agent system using LangGraph and LangChain
- Regulatory compliance monitoring
- Secure data handling
- Comprehensive test suite with security checks
- Modular and extensible architecture

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/medicare_navigator.git
cd medicare_navigator
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with the following variables:
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
```

## Development

### Running Tests
The project uses a tiered testing approach:
```bash
# Run all tests
./tests/run_tests.py

# Run specific test levels
./tests/run_tests.py unit
./tests/run_tests.py integration
./tests/run_tests.py system
./tests/run_tests.py security
```

### Development Server
```bash
uvicorn main:app --reload
```

## Security

This project implements comprehensive security measures:
- Regular security scanning
- Encryption pattern detection
- Credential management
- HIPAA compliance checks
- Secure data handling

## Documentation

- Process maps and system architecture: `/docs/`
- Agent specifications: `/agents/`
- Testing documentation: `/tests/`
- Configuration: `/config/`

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Run tests: `./tests/run_tests.py`
3. Commit changes: `git commit -m "feat: your feature description"`
4. Push to branch: `git push origin feature/your-feature`
5. Create a Pull Request

## License

[License information to be added] 