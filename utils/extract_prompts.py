"""
Extract Prompts Script

This script extracts system prompts from agent files and saves them as separate prompt files.
"""

import os
import re
import glob
from typing import Dict, List, Tuple

# Directory paths
AGENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents")
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")
AGENT_PROMPTS_DIR = os.path.join(PROMPTS_DIR, "agents")

# Ensure directories exist
os.makedirs(AGENT_PROMPTS_DIR, exist_ok=True)

def extract_prompt_variable(file_content: str, var_name: str) -> Tuple[bool, str]:
    """
    Extract a prompt variable from file content.
    
    Args:
        file_content: The content of the file
        var_name: The name of the variable to extract
        
    Returns:
        Tuple of (found, prompt_text)
    """
    # Regular expression to match the variable assignment and triple-quoted string
    pattern = rf"{var_name}\s*=\s*\"\"\"(.*?)\"\"\""
    match = re.search(pattern, file_content, re.DOTALL)
    
    if match:
        # Extract the content within the triple quotes
        prompt_text = match.group(1).strip()
        return True, prompt_text
    
    return False, ""

def process_agent_file(file_path: str) -> Dict[str, str]:
    """
    Process an agent file to extract prompts.
    
    Args:
        file_path: Path to the agent file
        
    Returns:
        Dictionary of prompt names to prompt texts
    """
    prompts = {}
    agent_name = os.path.splitext(os.path.basename(file_path))[0]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Try to extract different types of prompt variables
            var_names = [
                "system_prompt",
                "self.system_prompt",
                "security_system_prompt", 
                "self.security_system_prompt",
                "qa_system_prompt",
                "self.qa_system_prompt",
                "requirements_system_prompt",
                "self.requirements_system_prompt",
                "assessment_system_prompt",
                "self.assessment_system_prompt",
                "redaction_system_prompt",
                "self.redaction_system_prompt"
            ]
            
            for var_name in var_names:
                found, prompt_text = extract_prompt_variable(content, var_name)
                if found and prompt_text:
                    # Generate a meaningful prompt name
                    base_name = var_name.replace("self.", "").replace("_system", "")
                    
                    if base_name == "system_prompt":
                        prompt_name = f"{agent_name}.md"
                    else:
                        prompt_name = f"{agent_name}_{base_name}.md"
                    
                    prompts[prompt_name] = prompt_text
        
        return prompts
    
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return {}

def save_prompt(prompt_name: str, prompt_text: str) -> None:
    """
    Save a prompt to a file.
    
    Args:
        prompt_name: Name of the prompt file
        prompt_text: Content of the prompt
    """
    file_path = os.path.join(AGENT_PROMPTS_DIR, prompt_name)
    
    # Add a title to the prompt file
    title = prompt_name.replace(".md", "").replace("_", " ").title()
    formatted_prompt = f"# {title} Prompt\n\n{prompt_text}"
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_prompt)
        print(f"Saved prompt to {file_path}")
    except Exception as e:
        print(f"Error saving prompt to {file_path}: {str(e)}")

def main() -> None:
    """Extract all prompts from agent files."""
    print("Extracting prompts from agent files...")
    
    # Get all agent files
    agent_files = glob.glob(os.path.join(AGENTS_DIR, "*.py"))
    
    # Keep track of extracted prompts
    all_prompts = {}
    
    # Process each agent file
    for agent_file in agent_files:
        agent_name = os.path.splitext(os.path.basename(agent_file))[0]
        print(f"Processing {agent_name}...")
        
        prompts = process_agent_file(agent_file)
        all_prompts.update(prompts)
    
    # Save all extracted prompts
    for prompt_name, prompt_text in all_prompts.items():
        save_prompt(prompt_name, prompt_text)
    
    print(f"Extracted {len(all_prompts)} prompts to {AGENT_PROMPTS_DIR}")

if __name__ == "__main__":
    main() 