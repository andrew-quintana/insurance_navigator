#!/usr/bin/env python3
"""
Agent Reorganization Script

This script reorganizes all agents into a standardized directory structure:
agents/
├── agent_name/
│   ├── core/               # Core agent logic
│   │   └── logic.py       # Main agent implementation
│   ├── prompts/           # Prompt templates
│   │   └── prompt_v1.0.md # Current prompt version
│   ├── tests/             # Test suite
│   │   ├── unit/         # Unit tests
│   │   └── integration/  # Integration tests
│   ├── utils/            # Utility functions
│   ├── fmea/             # Failure mode analysis
│   │   └── analysis.json # FMEA data
│   ├── docs/             # Agent documentation
│   │   └── dfmea.md      # Design FMEA documentation
│   ├── __init__.py       # Module exports
│   ├── changelog.md      # Version history
│   └── README.md         # Documentation
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path

# Define the standard directory structure
AGENT_STRUCTURE = {
    "core": ["logic.py"],
    "prompts": {
        "templates": ["prompt_v1.0.md"],
        "examples": ["examples.json"],
        "versions": []
    },
    "tests": {
        "unit": [],
        "integration": [],
        "data": {
            "fixtures": [],
            "mocks": [],
            "examples": []
        }
    },
    "utils": [],
    "fmea": ["analysis.json"],
    "docs": ["dfmea.md"]
}

# List of agents to reorganize
AGENTS = [
    "intent_structuring",
    "document_parser",
    "quality_assurance",
    "healthcare_guide",
    "task_requirements",
    "patient_navigator",
    "guide_to_pdf",
    "regulatory",
    "service_access_strategy",
    "database_guard",
    "policy_compliance",
    "service_provider",
    "intake_validation"
]

def create_directory_structure(agent_name: str):
    """Create the standard directory structure for an agent."""
    base_path = Path("agents") / agent_name
    
    # Create main directories
    for dir_name, contents in AGENT_STRUCTURE.items():
        if isinstance(contents, list):
            (base_path / dir_name).mkdir(parents=True, exist_ok=True)
        else:
            for subdir in contents:
                if isinstance(contents[subdir], list):
                    (base_path / dir_name / subdir).mkdir(parents=True, exist_ok=True)
                else:
                    for subsubdir in contents[subdir]:
                        (base_path / dir_name / subdir / subsubdir).mkdir(parents=True, exist_ok=True)
    
    # Create empty files
    for dir_name, contents in AGENT_STRUCTURE.items():
        if isinstance(contents, list):
            for file in contents:
                (base_path / dir_name / file).touch()
        else:
            for subdir, subcontents in contents.items():
                if isinstance(subcontents, list):
                    for file in subcontents:
                        (base_path / dir_name / subdir / file).touch()
                else:
                    for subsubdir, subsubfiles in subcontents.items():
                        for file in subsubfiles:
                            (base_path / dir_name / subdir / subsubdir / file).touch()

def create_init_file(agent_name: str):
    """Create the __init__.py file for an agent."""
    content = f'''"""
{agent_name.replace('_', ' ').title()} Agent

This module provides the {agent_name.replace('_', ' ')} agent implementation.
"""

from agents.{agent_name}.core.logic import {agent_name.replace('_', '').title()}Agent

__all__ = ["{agent_name.replace('_', '').title()}Agent"]
'''
    
    with open(f"agents/{agent_name}/__init__.py", "w") as f:
        f.write(content)

def create_readme(agent_name: str):
    """Create the README.md file for an agent."""
    content = f'''# {agent_name.replace('_', ' ').title()} Agent

This module provides the {agent_name.replace('_', ' ')} agent implementation.

## Directory Structure

```
{agent_name}/
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
from agents.{agent_name} import {agent_name.replace('_', '').title()}Agent

# Initialize the agent
agent = {agent_name.replace('_', '').title()}Agent()

# Use the agent
result = agent.process(input_data)
```

## Testing

Run the test suite:

```bash
# Run unit tests
pytest agents/{agent_name}/tests/unit/

# Run integration tests
pytest agents/{agent_name}/tests/integration/
```

## Versioning

See `changelog.md` for version history and changes.
'''
    
    with open(f"agents/{agent_name}/README.md", "w") as f:
        f.write(content)

def create_changelog(agent_name: str):
    """Create the changelog.md file for an agent."""
    content = f'''# {agent_name.replace('_', ' ').title()} Agent Changelog

## V1.0 (2024-03-20)
- Initial implementation of {agent_name} agent
- Basic functionality implemented
- Core features added
- Initial test suite created
- FMEA analysis started

### Features
- Core agent functionality
- Basic prompt implementation
- Initial test coverage
- Basic error handling

### Technical Details
- Uses Claude 3 Sonnet for reasoning
- Implements Pydantic for output validation
- Uses LangChain for chain composition

### Known Limitations
- Initial implementation
- Limited test coverage
- Basic error handling
'''
    
    with open(f"agents/{agent_name}/changelog.md", "w") as f:
        f.write(content)

def create_fmea_analysis(agent_name: str):
    """Create the FMEA analysis file for an agent."""
    # Default template if file not found
    default_template = {
        "agent_name": agent_name,
        "last_updated": datetime.now().isoformat(),
        "metadata": {
            "created_by": "System",
            "review_date": datetime.now().isoformat(),
            "next_review_date": datetime.now().isoformat()
        }
    }
    
    # Try to load template from file, otherwise use default
    try:
        with open("scripts/fmea_template.json", "r") as f:
            template = json.load(f)
    except FileNotFoundError:
        template = default_template
    
    # Update template with agent-specific information
    template["agent_name"] = agent_name
    template["last_updated"] = datetime.now().isoformat()
    template["metadata"]["created_by"] = "System"
    template["metadata"]["review_date"] = datetime.now().isoformat()
    template["metadata"]["next_review_date"] = datetime.now().isoformat()
    
    # Save to agent's FMEA directory
    with open(f"agents/{agent_name}/fmea/analysis.json", "w") as f:
        json.dump(template, f, indent=4)

def create_dfmea_doc(agent_name: str):
    """Create the DFMEA documentation file."""
    content = f'''# Design FMEA for {agent_name.replace('_', ' ').title()} Agent

## Overview

This document outlines the Design Failure Mode and Effects Analysis (DFMEA) for the {agent_name.replace('_', ' ').title()} Agent.

## Failure Modes

### 1. Input Validation Failure
- **Description**: Agent fails to properly validate input data
- **Potential Causes**: Missing validation checks, incomplete rules, unhandled edge cases
- **Effects**: Incorrect processing, system errors, security vulnerabilities
- **Controls**: Input validation, type checking, error handling
- **Actions**: Implement comprehensive validation, add test cases, improve error handling

### 2. Prompt Injection
- **Description**: Agent is vulnerable to prompt injection attacks
- **Potential Causes**: Insufficient security, missing sanitization, weak boundaries
- **Effects**: Unauthorized access, system compromise, data leakage
- **Controls**: Security checks, input sanitization, system boundaries
- **Actions**: Implement security agent, add sanitization, strengthen boundaries

### 3. Reasoning Failure
- **Description**: Agent fails to properly reason about inputs
- **Potential Causes**: Insufficient context, complex patterns, ambiguous requirements
- **Effects**: Incorrect decisions, poor response quality, user dissatisfaction
- **Controls**: Multiple reasoning paths, self-consistency checks, validation chains
- **Actions**: Improve reasoning, add context handling, implement better validation

## Risk Assessment

| Failure Mode | Severity | Occurrence | Detection | RPN |
|--------------|----------|------------|-----------|-----|
| Input Validation | 8 | 3 | 7 | 168 |
| Prompt Injection | 9 | 2 | 6 | 108 |
| Reasoning Failure | 7 | 4 | 5 | 140 |

## Mitigation Strategies

1. **Input Validation**
   - Implement comprehensive validation checks
   - Add type checking and boundary validation
   - Improve error handling and reporting

2. **Prompt Security**
   - Implement prompt security agent
   - Add input sanitization
   - Strengthen system boundaries

3. **Reasoning Quality**
   - Implement multiple reasoning paths
   - Add self-consistency checks
   - Improve validation chains

## Monitoring and Review

- Regular review of failure modes
- Continuous monitoring of agent performance
- Periodic updates to mitigation strategies
'''
    
    with open(f"agents/{agent_name}/docs/dfmea.md", "w") as f:
        f.write(content)

def create_prompt_examples(agent_name: str):
    """Create the prompt examples file."""
    content = {
        "version": "1.0",
        "examples": [
            {
                "name": "Basic Example",
                "input": "Example input text",
                "expected_output": "Example expected output",
                "context": "Example context",
                "notes": "Example notes"
            }
        ]
    }
    
    with open(f"agents/{agent_name}/prompts/examples/examples.json", "w") as f:
        json.dump(content, f, indent=4)

def create_test_data(agent_name: str):
    """Create test data files."""
    # Create fixtures
    fixtures = {
        "version": "1.0",
        "fixtures": [
            {
                "name": "basic_fixture",
                "data": {
                    "input": "Test input",
                    "expected": "Test output"
                }
            }
        ]
    }
    
    with open(f"agents/{agent_name}/tests/data/fixtures/basic_fixtures.json", "w") as f:
        json.dump(fixtures, f, indent=4)
    
    # Create mocks
    mocks = {
        "version": "1.0",
        "mocks": [
            {
                "name": "basic_mock",
                "mock_data": {
                    "input": "Mock input",
                    "response": "Mock response"
                }
            }
        ]
    }
    
    with open(f"agents/{agent_name}/tests/data/mocks/basic_mocks.json", "w") as f:
        json.dump(mocks, f, indent=4)
    
    # Create examples
    examples = {
        "version": "1.0",
        "examples": [
            {
                "name": "basic_example",
                "input": "Example input",
                "expected": "Example output",
                "context": "Example context"
            }
        ]
    }
    
    with open(f"agents/{agent_name}/tests/data/examples/basic_examples.json", "w") as f:
        json.dump(examples, f, indent=4)

def find_agent_files(agent_name: str) -> dict:
    """Find all files related to an agent in any location."""
    files = {
        'core': [],
        'prompts': [],
        'tests': {'unit': [], 'integration': []},
        'logs': [],
        'fmea': [],
        'docs': []
    }
    
    # Search through all relevant directories
    search_dirs = [
        'prompts',
        'logs',
        'tests',
        'data/fmea',
        'docs'
    ]
    
    for base_dir in search_dirs:
        if not os.path.exists(base_dir):
            continue
            
        for root, _, filenames in os.walk(base_dir):
            for filename in filenames:
                if agent_name in filename or agent_name in root:
                    full_path = os.path.join(root, filename)
                    
                    # Categorize the file
                    if 'test' in filename or 'test_' in root:
                        if 'run_' in filename:
                            files['tests']['integration'].append(full_path)
                        else:
                            files['tests']['unit'].append(full_path)
                    elif 'prompt' in filename or 'prompt' in root:
                        files['prompts'].append(full_path)
                    elif 'log' in filename or 'log' in root:
                        files['logs'].append(full_path)
                    elif 'fmea' in filename or 'dfmea' in filename:
                        if filename.endswith('.json'):
                            files['fmea'].append(full_path)
                        else:
                            files['docs'].append(full_path)
                    elif filename.endswith('.py') and agent_name in filename:
                        files['core'].append(full_path)
    
    return files

def move_related_files(agent_name: str):
    """Move all related files to their new locations."""
    # Find all related files
    files = find_agent_files(agent_name)
    
    # Create target directories if they don't exist
    for dir_name in ['core', 'prompts', 'tests/unit', 'tests/integration', 'logs', 'fmea', 'docs']:
        os.makedirs(f"agents/{agent_name}/{dir_name}", exist_ok=True)
    
    # Move core files
    for file in files['core']:
        if os.path.exists(file):
            target = f"agents/{agent_name}/core/logic.py"
            shutil.move(file, target)
    
    # Move prompt files
    for file in files['prompts']:
        if os.path.exists(file):
            target = f"agents/{agent_name}/prompts/prompt_v1.0.md"
            shutil.move(file, target)
    
    # Move test files
    for file in files['tests']['unit']:
        if os.path.exists(file):
            target = f"agents/{agent_name}/tests/unit/{os.path.basename(file)}"
            shutil.move(file, target)
    
    for file in files['tests']['integration']:
        if os.path.exists(file):
            target = f"agents/{agent_name}/tests/integration/{os.path.basename(file)}"
            shutil.move(file, target)
    
    # Move log files
    for file in files['logs']:
        if os.path.exists(file):
            target = f"agents/{agent_name}/logs/{os.path.basename(file)}"
            shutil.move(file, target)
    
    # Move FMEA files
    for file in files['fmea']:
        if os.path.exists(file):
            target = f"agents/{agent_name}/fmea/analysis.json"
            shutil.move(file, target)
    
    # Move documentation files
    for file in files['docs']:
        if os.path.exists(file):
            target = f"agents/{agent_name}/docs/{os.path.basename(file)}"
            shutil.move(file, target)
    
    # Clean up empty directories
    for base_dir in ['prompts', 'logs', 'tests', 'data/fmea', 'docs']:
        if os.path.exists(base_dir):
            for root, dirs, files in os.walk(base_dir, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    if agent_name in dir_path and not os.listdir(dir_path):
                        os.rmdir(dir_path)

def move_temporary_scripts_and_tests():
    """Move temporary scripts and tests to a new folder under /scripts/temp."""
    temp_dir = Path("scripts/temp")
    temp_dir.mkdir(exist_ok=True)
    
    # List of temporary scripts and tests to move
    temp_files = [
        "convert_all_agents.py",
        "utils/sheet_importer.py",
        "utils/sheets_README.md",
        "utils/airtable.py",
        "data/excel/README.md",
        "tests/agents/test_sheet_importer.py",
        "tests/run_sheet_importer_tests.py",
        "tests/test_sheet_importer_simple.py"
    ]
    
    for file in temp_files:
        if os.path.exists(file):
            shutil.move(file, temp_dir / os.path.basename(file))
    
    # Move temporary tests under /tests/agents
    tests_agents_dir = Path("tests/agents")
    if tests_agents_dir.exists():
        for test_file in tests_agents_dir.glob("*.py"):
            shutil.move(test_file, temp_dir / test_file.name)
    
    print("Temporary scripts and tests moved to /scripts/temp")

def main():
    """Main function to reorganize all agents."""
    for agent_name in AGENTS:
        print(f"Reorganizing {agent_name} agent...")
        
        # Create directory structure
        create_directory_structure(agent_name)
        
        # Create standard files
        create_init_file(agent_name)
        create_readme(agent_name)
        create_changelog(agent_name)
        create_fmea_analysis(agent_name)
        create_dfmea_doc(agent_name)
        create_prompt_examples(agent_name)
        create_test_data(agent_name)
        
        # Move existing files
        move_related_files(agent_name)
        
        print(f"Completed {agent_name} agent reorganization")
    
    # Move temporary scripts and tests
    move_temporary_scripts_and_tests()

if __name__ == "__main__":
    main() 