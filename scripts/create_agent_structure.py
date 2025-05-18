"""
Agent Structure Generator

This script creates a standardized directory structure and base files for agents in the Insurance Navigator system.

IMPORTANT NOTES:
- This script is primarily for documentation and creating new agents
- Existing agents already have their structure established
- All agents use a centralized /logs directory rather than agent-specific log directories
- This script will NOT create agent-specific log directories, as they are deprecated
  (the centralized logs structure is enforced in the BaseAgent class)
- Models are part of the core functionality and are created under core/models directory

Usage:
- Run this script to create a new agent: python create_agent_structure.py [agent_name]
- If no agent name is provided, it will attempt to create all missing agents
"""

import os
import json
import sys

def create_agent_structure(specific_agent=None):
    """
    Create directory structure and base files for agents.
    
    Args:
        specific_agent: Optional name of a specific agent to create.
                       If not provided, creates all agents.
    """
    # Ensure the main logs directory exists
    os.makedirs("logs", exist_ok=True)
    print(f"Ensured central logs directory exists")
    
    # Determine which agents to create
    agents_to_create = [specific_agent] if specific_agent else AGENT_TEMPLATES.keys()
    
    for agent_id in agents_to_create:
        if agent_id not in AGENT_TEMPLATES:
            print(f"Error: Unknown agent '{agent_id}'")
            continue
            
        template = AGENT_TEMPLATES[agent_id]
        print(f"Creating structure for {template['name']}...")
        
        # Create directories
        dirs = [
            f"agents/{agent_id}/core",
            f"agents/{agent_id}/core/models",
            f"agents/{agent_id}/docs",
            f"agents/{agent_id}/tests/unit",
            f"agents/{agent_id}/tests/integration",
            f"agents/{agent_id}/prompts/templates",
            f"agents/{agent_id}/prompts/examples",
            f"agents/{agent_id}/utils"
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
            
        # Explicitly remove logs directory if it exists
        logs_dir = f"agents/{agent_id}/logs"
        if os.path.exists(logs_dir):
            try:
                os.rmdir(logs_dir)
                print(f"  Removed agent-specific logs directory (using centralized logs)")
            except OSError:
                print(f"  Warning: Could not remove {logs_dir}, it may contain files")
        
        # Create README.md
        readme_content = f"""# {template['name']}

## Overview
{template['description']}

## Features
{chr(10).join(f"- {feature}" for feature in template['features'])}

## Architecture
The agent follows a modular architecture with the following components:
- Core processing engine
- Validation system
- Integration handlers
- Monitoring system
- Reporting module

## Usage
```python
from agents.{agent_id} import {template['name'].replace(' ', '')}Agent

# Initialize the agent
agent = {template['name'].replace(' ', '')}Agent()

# Process content
result = agent.process(content="...")
```

## Configuration
The agent can be configured through environment variables or a configuration file:
- `{agent_id.upper()}_LOG_LEVEL`: Logging verbosity
- `{agent_id.upper()}_MODE`: Operation mode
- `{agent_id.upper()}_CONFIG_PATH`: Configuration file path

## Development
See the [Development Guide](docs/development.md) for setup and contribution guidelines.

## Testing
Run the test suite:
```bash
pytest agents/{agent_id}/tests/
```

## License
Proprietary - All rights reserved
"""
        
        with open(f"agents/{agent_id}/README.md", "w") as f:
            f.write(readme_content)
        
        # Create changelog.md
        changelog_content = f"""# Changelog

All notable changes to the {template['name']} will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- Basic agent scaffolding
- Core processing engine
- Validation system
- Integration handlers
- Monitoring system
- Reporting module

### Changed
- None

### Deprecated
- None

### Removed
- None

### Fixed
- None

### Security
- None

## [0.1.0] - YYYY-MM-DD
### Added
- Initial release
- Basic functionality
- Core features
- Integration capabilities
- Monitoring and reporting
"""
        
        with open(f"agents/{agent_id}/changelog.md", "w") as f:
            f.write(changelog_content)
        
        # Create __init__.py
        init_content = f"""from .{agent_id}_agent import {template['name'].replace(' ', '')}Agent

__all__ = ['{template['name'].replace(' ', '')}Agent']
"""
        
        with open(f"agents/{agent_id}/__init__.py", "w") as f:
            f.write(init_content)
            
        print(f"Structure for {template['name']} created successfully.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        create_agent_structure(sys.argv[1])
    else:
        create_agent_structure() 