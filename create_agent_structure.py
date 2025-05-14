import os
import json

AGENT_TEMPLATES = {
    "database": {
        "name": "Database Agent",
        "description": "Manages database operations and ensures data integrity",
        "features": [
            "Database connection management",
            "Query optimization",
            "Data validation",
            "Transaction management",
            "Backup and recovery"
        ]
    },
    "document_manager": {
        "name": "Document Manager Agent",
        "description": "Manages document lifecycle and processing",
        "features": [
            "Document processing",
            "Version control",
            "Metadata management",
            "Storage optimization",
            "Access control"
        ]
    },
    "guide_to_pdf": {
        "name": "Guide to PDF Agent",
        "description": "Converts healthcare guides to PDF format",
        "features": [
            "PDF generation",
            "Format preservation",
            "Image handling",
            "Table formatting",
            "Document styling"
        ]
    },
    "healthcare_guide_developer": {
        "name": "Healthcare Guide Developer Agent",
        "description": "Develops and maintains healthcare guides",
        "features": [
            "Guide creation",
            "Content validation",
            "Version management",
            "Template handling",
            "Quality assurance"
        ]
    },
    "patient_navigator": {
        "name": "Patient Navigator Agent",
        "description": "Guides patients through healthcare processes",
        "features": [
            "Process guidance",
            "Resource location",
            "Appointment scheduling",
            "Document collection",
            "Progress tracking"
        ]
    },
    "prompt_security": {
        "name": "Prompt Security Agent",
        "description": "Ensures prompt security and compliance",
        "features": [
            "Prompt validation",
            "Security checking",
            "Compliance verification",
            "Audit logging",
            "Risk assessment"
        ]
    },
    "task_requirements": {
        "name": "Task Requirements Agent",
        "description": "Manages and validates task requirements",
        "features": [
            "Requirement analysis",
            "Validation rules",
            "Dependency tracking",
            "Compliance checking",
            "Documentation"
        ]
    },
    "service_access_strategy": {
        "name": "Service Access Strategy Agent",
        "description": "Manages service access strategies",
        "features": [
            "Access control",
            "Strategy implementation",
            "Policy enforcement",
            "Usage monitoring",
            "Optimization"
        ]
    },
    "regulatory": {
        "name": "Regulatory Agent",
        "description": "Ensures regulatory compliance",
        "features": [
            "Compliance checking",
            "Regulation tracking",
            "Policy enforcement",
            "Documentation",
            "Audit support"
        ]
    },
    "service_provider": {
        "name": "Service Provider Agent",
        "description": "Manages service provider interactions",
        "features": [
            "Provider management",
            "Service coordination",
            "Quality monitoring",
            "Communication handling",
            "Performance tracking"
        ]
    },
    "quality_assurance": {
        "name": "Quality Assurance Agent",
        "description": "Ensures system quality and reliability",
        "features": [
            "Quality monitoring",
            "Testing automation",
            "Performance tracking",
            "Issue detection",
            "Compliance verification"
        ]
    }
}

def create_agent_structure():
    for agent_id, template in AGENT_TEMPLATES.items():
        # Create directories
        dirs = [
            f"agents/{agent_id}/core",
            f"agents/{agent_id}/docs",
            f"agents/{agent_id}/tests/unit",
            f"agents/{agent_id}/tests/integration",
            f"agents/{agent_id}/prompts/templates",
            f"agents/{agent_id}/prompts/examples",
            f"agents/{agent_id}/logs",
            f"agents/{agent_id}/utils"
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
        
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

if __name__ == "__main__":
    create_agent_structure() 