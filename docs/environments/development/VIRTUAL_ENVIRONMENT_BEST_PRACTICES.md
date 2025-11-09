# Virtual Environment Best Practices

This document outlines the best practices for managing Python virtual environments in this project and across all development work.

## Overview

We use virtual environments to isolate project dependencies and avoid conflicts between different projects. This ensures that each project has its own clean Python environment with only the packages it needs.

## Why Virtual Environments?

- **Dependency Isolation**: Each project has its own set of packages
- **Version Control**: Different projects can use different versions of the same package
- **Clean Environment**: No global package pollution
- **Reproducible Builds**: Easy to recreate the exact environment
- **Team Collaboration**: Everyone works with the same environment

## Project Structure

Each project should have its virtual environment in a `.venv` directory:

```
project-root/
├── .venv/                 # Virtual environment (gitignored)
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies (optional)
├── activate_venv.sh       # Auto-generated activation script
└── ...
```

## Quick Start

### 1. Using the Management Script

We provide a convenient script for managing virtual environments:

```bash
# Navigate to your project
cd /path/to/your/project

# Create a new virtual environment
./scripts/manage-venv.sh create

# Activate the environment
./scripts/manage-venv.sh activate

# Install dependencies
./scripts/manage-venv.sh install

# Check status
./scripts/manage-venv.sh status
```

### 2. Manual Setup

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Deactivate when done
deactivate
```

## Best Practices

### 1. Always Use Virtual Environments

- **Never install packages globally** (except for essential tools like `pip`, `setuptools`)
- Create a virtual environment for every project
- Activate the environment before working on the project

### 2. Environment Naming Convention

- Use `.venv` as the directory name (this is gitignored by default)
- Keep the virtual environment in the project root
- Don't commit the virtual environment to version control

### 3. Dependency Management

#### Requirements Files

Create separate requirements files for different purposes:

- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Development dependencies (testing, linting, etc.)
- `requirements-test.txt` - Testing-specific dependencies (optional)

#### Example requirements.txt
```
fastapi==0.104.1
uvicorn==0.24.0
supabase==2.15.1
python-dotenv==1.0.1
```

#### Example requirements-dev.txt
```
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
flake8==6.1.0
mypy==1.7.1
```

### 4. Environment Activation

Always activate the virtual environment before working:

```bash
# Check if environment is active
echo $VIRTUAL_ENV

# If not active, activate it
source .venv/bin/activate

# Verify Python location
which python
# Should show: /path/to/project/.venv/bin/python
```

### 5. Package Installation

When installing new packages:

```bash
# Activate environment first
source .venv/bin/activate

# Install package
pip install package-name

# Update requirements file
pip freeze > requirements.txt

# Or add to specific requirements file
echo "package-name==1.0.0" >> requirements-dev.txt
```

### 6. Environment Cleanup

To clean up an environment:

```bash
# Using the management script
./scripts/manage-venv.sh clean

# Or manually
rm -rf .venv
```

## Project-Specific Setup

### Current Project (Insurance Navigator)

This project already has a virtual environment set up at `.venv/` with all necessary dependencies.

#### Activating the Environment

```bash
# Navigate to project root
cd /Users/aq_home/1Projects/accessa/insurance_navigator

# Activate environment
source .venv/bin/activate

# Or use the generated script
./activate_venv.sh
```

#### Available Dependencies

The project includes:
- **Backend**: FastAPI, Supabase, SQLAlchemy, Pydantic
- **AI/ML**: LangChain, OpenAI, Anthropic, LlamaIndex
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Development**: black, flake8, mypy, ruff
- **Documentation**: mkdocs, mkdocs-material

#### Environment Files

- `requirements.txt` - Core dependencies
- `requirements-api.txt` - API-specific dependencies
- `requirements-testing.txt` - Testing dependencies
- `requirements-worker.txt` - Worker process dependencies

## Troubleshooting

### Common Issues

#### 1. "Command not found" after activation

```bash
# Check if environment is active
echo $VIRTUAL_ENV

# If empty, activate the environment
source .venv/bin/activate
```

#### 2. Wrong Python version

```bash
# Check Python version
python --version

# If wrong, recreate the environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. Package conflicts

```bash
# Check installed packages
pip list

# Reinstall from requirements
pip install --force-reinstall -r requirements.txt
```

#### 4. Environment not found

```bash
# List all virtual environments
./scripts/manage-venv.sh list

# Create new environment
./scripts/manage-venv.sh create
```

### Environment Status Check

Use the management script to check your environment status:

```bash
./scripts/manage-venv.sh status
```

This will show:
- Whether a virtual environment is active
- Current Python and pip locations
- Available virtual environment for current project

## IDE Integration

### VS Code

1. Open the project in VS Code
2. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
3. Type "Python: Select Interpreter"
4. Choose the interpreter from `.venv/bin/python`

### PyCharm

1. Go to File → Settings → Project → Python Interpreter
2. Click the gear icon → Add
3. Choose "Existing Environment"
4. Select `.venv/bin/python`

## Team Collaboration

### Sharing Environments

1. **Never commit** the `.venv` directory
2. Always include `requirements.txt` files
3. Document any system-level dependencies
4. Use the same Python version across the team

### Onboarding New Team Members

1. Clone the repository
2. Create virtual environment: `./scripts/manage-venv.sh create`
3. Install dependencies: `./scripts/manage-venv.sh install`
4. Activate environment: `source .venv/bin/activate`

## Migration from Global Packages

If you were previously using global packages:

1. **Backup your global packages** (already done: `~/global_packages_backup.txt`)
2. **Clean global environment** (already completed)
3. **Set up virtual environments** for each project
4. **Install only necessary packages** in each environment

## Additional Resources

- [Python Virtual Environments Guide](https://docs.python.org/3/tutorial/venv.html)
- [pip User Guide](https://pip.pypa.io/en/stable/user_guide/)
- [Virtual Environment Management Script](./scripts/manage-venv.sh)

## Summary

- ✅ Use virtual environments for all projects
- ✅ Keep `.venv` in project root (gitignored)
- ✅ Separate requirements files for different purposes
- ✅ Always activate environment before working
- ✅ Never install packages globally
- ✅ Use the management script for convenience

Following these practices ensures clean, isolated, and reproducible Python environments across all your projects.
