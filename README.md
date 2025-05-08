# Insurance Navigator

A HIPAA-aware, agent-based system for navigating insurance information and providing personalized guidance.

## Project Structure

```
/agents/          # Agent implementations
/tests/           # Test suites
/logs/            # Logging directories
/docs/            # Documentation
/graph/           # LangGraph process chains
/data/            # Data storage
/ui/              # Frontend interface
```

## Setup

1. Clone the repository:
```bash
git clone https://github.com/andrew-quintana/insurance_navigator.git
cd insurance_navigator
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
```bash
cp .env.template .env
# Edit .env with your API keys and configuration
```

## Development

- Run tests: `pytest`
- Start development server: `uvicorn main:app --reload`

## Documentation

- Process maps and system architecture are in `/docs/`
- Agent specifications and prompts are in `/agents/`
- Testing documentation is in `/tests/`

## Security

This project is designed with HIPAA compliance in mind. All sensitive data handling follows security best practices and is configured through secure environment variables.

## License

[License information to be added] 