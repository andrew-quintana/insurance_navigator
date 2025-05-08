# Prompts Directory

This directory contains all the prompts used by the agent system. Storing prompts in separate files makes them easier to manage, update, and version control.

## Structure

- `/prompts/agents/` - Contains agent-specific prompts
- `/prompts/chains/` - Contains prompts used in specific processing chains
- `/prompts/templates/` - Contains reusable prompt templates

## Naming Convention

Prompt files follow this naming convention:
- Agent prompts: `[agent_name].md` or `[agent_name]_[purpose].md`
- Chain prompts: `[chain_name]_[step].md`
- Template prompts: `template_[purpose].md`

## File Format

Prompts are stored as markdown (`.md`) files. This format is preferred because:
1. It allows for better readability with markdown formatting
2. It works well with version control
3. It can be easily edited in any text editor or IDE

## Usage

To use prompts in your code, use the `prompt_loader` utility:

```python
from utils.prompt_loader import load_prompt

# Load an agent prompt
prompt_text = load_prompt("database_guard_security")

# Load a prompt from a different directory
prompt_text = load_prompt("custom_prompt", "/path/to/prompts")
```

## Updating Prompts

When updating prompts:
1. Make changes to the appropriate prompt file
2. If your application is currently running, you may need to clear the prompt cache:
   ```python
   from utils.prompt_loader import clear_cache
   clear_cache()
   ```
3. Test the updated prompt to ensure it produces the expected results

## Available Prompts

### Agent Prompts

- `database_guard_security.md` - Database Guard Agent's security validation prompt
- `prompt_security.md` - Prompt Security Agent's system prompt
- `quality_assurance.md` - Quality Assurance Agent's system prompt
- `regulatory_assessment.md` - Regulatory Agent's assessment prompt
- `regulatory_redaction.md` - Regulatory Agent's redaction prompt
- `task_requirements.md` - Task Requirements Agent's system prompt 