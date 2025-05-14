"""
Convert Agent Files to Use Prompt Loader

This script converts agent files to use the prompt_loader utility instead of embedded prompts.
"""

import os
import re
import glob
from typing import Dict, List, Tuple
import argparse

# Directory paths
AGENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents")

def add_import_if_missing(content: str) -> str:
    """
    Add the prompt_loader import statement if it's missing.
    
    Args:
        content: File content
        
    Returns:
        Updated file content
    """
    if "from utils.prompt_loader import load_prompt" not in content:
        # Find the last import statement
        import_pattern = r"^import .*$|^from .* import .*$"
        matches = list(re.finditer(import_pattern, content, re.MULTILINE))
        
        if matches:
            # Insert after the last import
            last_import = matches[-1]
            pos = last_import.end()
            return content[:pos] + "\nfrom utils.prompt_loader import load_prompt" + content[pos:]
        else:
            # If no imports found, add at the beginning after any comments
            return "from utils.prompt_loader import load_prompt\n\n" + content
    
    return content

def replace_prompt_variable(content: str, var_name: str, prompt_file: str) -> str:
    """
    Replace a prompt variable with a call to load_prompt.
    
    Args:
        content: File content
        var_name: Variable name to replace
        prompt_file: Name of the prompt file to load
        
    Returns:
        Updated file content
    """
    # Pattern to match the variable assignment and triple-quoted string
    pattern = rf"({var_name}\s*=\s*\"\"\".+?\"\"\")"
    
    # Replacement string
    replacement = f"""# Load the {var_name} from file
        try:
            {var_name} = load_prompt("{prompt_file}")
        except FileNotFoundError:
            self.logger.warning("Could not find {prompt_file}.md prompt file, using default prompt")
            {var_name} = \"\"\"
            Default prompt for {var_name}. Replace with actual prompt if needed.
            \"\"\"
        """
    
    # Replace in content
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

def process_agent_file(file_path: str, agent_name: str, dry_run: bool = False) -> None:
    """
    Process an agent file to replace embedded prompts with prompt loader calls.
    
    Args:
        file_path: Path to the agent file
        agent_name: Name of the agent
        dry_run: Whether to only print changes without writing to file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add the import statement if needed
        updated_content = add_import_if_missing(content)
        
        # Map of variable names to prompt file names
        prompt_map = {
            "self.system_prompt": agent_name,
            "self.security_system_prompt": f"{agent_name}_security_prompt",
            "self.qa_system_prompt": f"{agent_name}_qa_prompt",
            "self.requirements_system_prompt": f"{agent_name}_requirements_prompt",
            "self.assessment_system_prompt": f"{agent_name}_assessment_prompt",
            "self.redaction_system_prompt": f"{agent_name}_redaction_prompt"
        }
        
        # Replace each prompt variable
        for var_name, prompt_file in prompt_map.items():
            if var_name in updated_content:
                updated_content = replace_prompt_variable(updated_content, var_name, prompt_file)
        
        # Check if there were changes
        if content != updated_content:
            if dry_run:
                print(f"Would update {file_path} (dry run)")
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                print(f"Updated {file_path}")
        else:
            print(f"No changes needed for {file_path}")
            
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")

def main() -> None:
    """Convert agent files to use prompt_loader."""
    parser = argparse.ArgumentParser(description="Convert agent files to use prompt_loader")
    parser.add_argument("--agent", help="Name of a specific agent to convert")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without modifying files")
    args = parser.parse_args()
    
    print("Converting agent files to use prompt_loader...")
    
    if args.agent:
        # Convert a specific agent
        agent_file = os.path.join(AGENTS_DIR, f"{args.agent}.py")
        if os.path.exists(agent_file):
            process_agent_file(agent_file, args.agent, args.dry_run)
        else:
            print(f"Agent file not found: {agent_file}")
    else:
        # Convert all agent files
        agent_files = glob.glob(os.path.join(AGENTS_DIR, "*.py"))
        for agent_file in agent_files:
            agent_name = os.path.splitext(os.path.basename(agent_file))[0]
            if agent_name != "__init__" and agent_name != "base_agent":
                process_agent_file(agent_file, agent_name, args.dry_run)
    
    print("Conversion completed!")

if __name__ == "__main__":
    main() 