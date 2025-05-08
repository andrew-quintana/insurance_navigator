# Agent Prompt Conversion Guide

This guide explains how to convert agent modules to use external prompt files instead of embedded prompts.

## 1. Overview

We've implemented a new approach for managing agent prompts:

- All prompts are now stored in separate files in the `prompts/agents/` directory
- Agents load these prompts at initialization using the `prompt_loader` utility
- This makes prompts easier to update, version control, and maintain

## 2. Conversion Steps

### 2.1 Extract Existing Prompts

We've already extracted all existing prompts from agent files using the `utils/extract_prompts.py` script. The prompts are now available in the `prompts/agents/` directory.

### 2.2 Update Agent Files

To update an agent file to use the prompt loader:

1. Add the import for the prompt loader:
   ```python
   from utils.prompt_loader import load_prompt
   ```

2. Replace the embedded prompt with a call to load the prompt from file:
   ```python
   # Before:
   self.system_prompt = """
   Your embedded prompt text here...
   """
   
   # After:
   try:
       self.system_prompt = load_prompt("agent_name")
   except FileNotFoundError:
       self.logger.warning("Could not find agent_name.md prompt file, using default prompt")
       self.system_prompt = """
       Default fallback prompt text (shorter version)...
       """
   ```

3. Make sure the prompt file name matches the naming convention:
   - For base system prompts: `agent_name.md`
   - For specialized prompts: `agent_name_purpose.md` (e.g., `regulatory_assessment.md`)

### 2.3 Automated Conversion

You can use the `utils/convert_to_prompt_loader.py` script to automatically convert agent files:

```bash
# Convert a specific agent
python -m utils.convert_to_prompt_loader --agent=agent_name

# Convert all agents (dry run first to see what would change)
python -m utils.convert_to_prompt_loader --dry-run

# Convert all agents
python -m utils.convert_to_prompt_loader
```

## 3. Testing

After converting an agent, make sure to test it to verify it works correctly:

1. Create a test file in the `tests/` directory
2. Test that the agent can load prompts from files
3. Test that the agent functionality still works as expected

### Example Test

See `tests/test_prompt_security_with_loader.py` for a complete example of testing an agent with the prompt loader.

## 4. Prompt Management Best Practices

1. **Avoid Direct Edits in Code**: Make changes to prompt files, not in the agent code
2. **Version Control**: Commit prompt changes with meaningful commit messages
3. **Testing**: Always test after changing a prompt
4. **Documentation**: Document the purpose and structure of each prompt
5. **Consistency**: Follow the naming conventions for prompt files

## 5. Benefits

- **Maintainability**: Easier to update and modify prompts
- **Version Control**: Better tracking of prompt changes
- **Collaboration**: Easier for non-developers to contribute prompt improvements
- **Testing**: Easier to test different prompt versions
- **Deployment**: Enables prompt updates without code changes

## 6. Conversion Progress

| Agent | Converted | Tested |
|-------|-----------|--------|
| prompt_security | ✅ | ✅ |
| database_guard | ✅ | ✅ |
| task_requirements | ✅ | ❌ |
| quality_assurance | ✅ | ❌ |
| regulatory | ✅ | ❌ |
| patient_navigator | ✅ | ❌ |
| document_parser | ✅ | ❌ |
| healthcare_guide | ✅ | ❌ |
| service_provider | ✅ | ❌ |
| service_access_strategy | ✅ | ❌ |
| guide_to_pdf | ✅ | ❌ |
| policy_compliance | ✅ | ❌ |
| intent_structuring | ✅ | ❌ | 