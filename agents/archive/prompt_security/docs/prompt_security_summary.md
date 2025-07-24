# Prompt Security Agent with Prompt Chaining

The Prompt Security Agent is designed to detect and mitigate potential security threats in user inputs. It uses a prompt chaining approach to enhance its accuracy and adaptability to different types of threats.

## Overview

The agent implements a multi-stage prompt chaining system:

1. **Main Prompt**: The initial system prompt (`prompt_security.md`) introduces the agent's role, tasks, and constraints.
2. **Self-Consistency Examples**: For each failure mode, the agent loads specific examples from `prompt_security_prompt_examples.json` to improve classification accuracy.
3. **Specialized Analysis**: When potential threats are detected, the agent uses targeted, failure-mode-specific chains to provide more accurate assessment.

## How Prompt Chaining Works

1. **Initial Assessment**: User input is first evaluated with a quick pattern-based check for obvious threats.
2. **Base Analysis**: If the quick check passes, the input is processed by the base chain using the main system prompt.
3. **Specialized Analysis**: If the base analysis detects a potential threat, specialized chains for specific failure modes are used.
4. **Confidence-Weighted Decision**: The agent selects the result with the highest confidence score.
5. **Safe Input Validation**: For inputs deemed safe, an additional check against the "Incorrectly blocks normal queries" failure mode examples is performed to prevent false positives.

## Failure Modes Covered

The agent addresses the following failure modes:

1. **Jailbreak Detection**: Identifying attempts to bypass system constraints or role definitions.
2. **Instruction Override**: Catching attempts to ignore, disable, or manipulate system instructions.
3. **Prompt Leakage**: Detecting attempts to extract system prompts or implementation details.
4. **Role Hijacking**: Preventing unauthorized role assignment or impersonation.
5. **Obfuscation**: Identifying attempts to hide malicious content through character substitution.
6. **Payload Splitting**: Detecting distributed threats across multiple tokens or messages.
7. **False Positive Prevention**: Ensuring legitimate healthcare/insurance queries aren't incorrectly blocked.

## Implementation Details

### Prompt Templates

The agent uses two main prompt templates:

1. **Base Template**: Includes the system prompt and user input.
2. **Examples Template**: Includes the system prompt, specific failure mode examples, and user input.

### Chains

- **Base Chain**: The initial evaluation chain using only the main system prompt.
- **Failure Mode Chains**: Specialized chains for each failure mode, incorporating relevant examples.

### Classification Output

Each evaluation produces a `SecurityCheck` object containing:

- `is_safe`: Boolean indicating if the input is safe to process.
- `threat_detected`: Boolean indicating if a security threat was detected.
- `threat_type`: The specific type of threat detected (if any).
- `threat_severity`: The assessed severity level ("none_detected", "borderline", or "explicit").
- `sanitized_input`: The cleaned or redacted version of the input.
- `confidence`: The model's confidence in its assessment.
- `reasoning`: A brief explanation of the assessment.

## Usage

```python
from agents.prompt_security import PromptSecurityAgent

# Initialize the agent
agent = PromptSecurityAgent()

# Process user input
is_safe, sanitized_input, result = agent.process("User input here")

# Check the results
if is_safe:
    # Process the sanitized input
    pass
else:
    # Handle the unsafe input
    threat_type = result["threat_type"]
    severity = result["threat_severity"]
    # Respond appropriately based on threat type and severity
```

## Extending the Agent

To extend the agent's capabilities:

1. **Add New Examples**: Add new examples to `prompt_security_prompt_examples.json` under the appropriate failure mode.
2. **Add New Failure Modes**: Create a new failure mode section in the examples file.
3. **Customize System Prompt**: Modify `prompt_security.md` to adjust the initial guidance given to the agent.

## Testing

The agent includes comprehensive tests that verify:

1. **Format Verification**: Ensure examples are correctly formatted for the prompt.
2. **Process Flow**: Validate the entire process chain from input to output.
3. **Integration Testing**: Test with real examples from the examples file.
4. **Quick Check Validation**: Verify obvious threats are caught without invoking the LLM. 