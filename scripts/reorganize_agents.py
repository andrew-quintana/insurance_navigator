#!/usr/bin/env python3
"""
Script to reorganize agent directory structure to flatten the core directory.
New structure: agents/{agent_name}/[models/, current_prompt.md, prompts/, current_example.json, examples/, {agent_name}.py, metrics/, tests/]
"""

import os
import shutil
import yaml
from pathlib import Path

def reorganize_agent(agent_path: Path, agent_name: str):
    """Reorganize a single agent directory"""
    print(f"Reorganizing {agent_name}...")
    
    core_path = agent_path / "core"
    if not core_path.exists():
        print(f"No core directory found for {agent_name}, skipping...")
        return
    
    # 1. Move the main agent Python file to root level
    agent_py = core_path / f"{agent_name}.py"
    if agent_py.exists():
        shutil.move(str(agent_py), str(agent_path / f"{agent_name}.py"))
        print(f"  Moved {agent_name}.py to root level")
    
    # 2. Move models directory to root level
    models_dir = core_path / "models"
    if models_dir.exists():
        if (agent_path / "models").exists():
            shutil.rmtree(str(agent_path / "models"))
        shutil.move(str(models_dir), str(agent_path / "models"))
        print(f"  Moved models/ to root level")
    
    # 3. Handle prompts - move current version to root, keep versions in prompts/
    prompts_dir = core_path / "prompts"
    if prompts_dir.exists():
        # Find the current prompt file (usually the one without version directory)
        current_prompt = None
        for file in prompts_dir.glob("*.md"):
            if file.is_file():
                current_prompt = file
                break
        
        if current_prompt:
            shutil.copy2(str(current_prompt), str(agent_path / "current_prompt.md"))
            print(f"  Copied current prompt to current_prompt.md")
        
        # Move the entire prompts directory (keeping versions, templates, etc.)
        if (agent_path / "prompts").exists():
            shutil.rmtree(str(agent_path / "prompts"))
        shutil.move(str(prompts_dir), str(agent_path / "prompts"))
        print(f"  Moved prompts/ to root level")
    
    # 4. Handle examples - move current version to root, keep versions in examples/
    examples_dir = core_path / "examples"
    if examples_dir.exists():
        # Find current example files
        for file in examples_dir.glob("*.json"):
            if file.is_file():
                shutil.copy2(str(file), str(agent_path / "current_example.json"))
                print(f"  Copied current example to current_example.json")
                break
        
        # Move the entire examples directory
        if (agent_path / "examples").exists():
            shutil.rmtree(str(agent_path / "examples"))
        shutil.move(str(examples_dir), str(agent_path / "examples"))
        print(f"  Moved examples/ to root level")
    
    # Also check for examples in prompts/examples (alternative structure)
    prompts_examples_dir = agent_path / "prompts" / "examples"
    if prompts_examples_dir.exists() and not (agent_path / "examples").exists():
        for file in prompts_examples_dir.glob("*.json"):
            if file.is_file():
                shutil.copy2(str(file), str(agent_path / "current_example.json"))
                print(f"  Copied current example from prompts/examples to current_example.json")
                break
        
        # Move prompts/examples to root examples
        shutil.move(str(prompts_examples_dir), str(agent_path / "examples"))
        print(f"  Moved prompts/examples/ to root level examples/")
    
    # 5. Remove the now-empty core directory
    if core_path.exists():
        try:
            # Remove __pycache__ and __init__.py if they exist
            pycache = core_path / "__pycache__"
            if pycache.exists():
                shutil.rmtree(str(pycache))
            
            init_file = core_path / "__init__.py"
            if init_file.exists():
                init_file.unlink()
            
            # Remove core directory if empty
            if not any(core_path.iterdir()):
                core_path.rmdir()
                print(f"  Removed empty core/ directory")
            else:
                print(f"  Warning: core/ directory not empty, contains: {list(core_path.iterdir())}")
        except Exception as e:
            print(f"  Warning: Could not remove core directory: {e}")

def update_config_file():
    """Update the config.yaml file to reflect the new structure"""
    config_path = Path("config/config.yaml")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Update paths for each agent
    for agent_name, agent_config in config.get('agents', {}).items():
        if 'core_file' in agent_config:
            # Update core file path
            old_path = agent_config['core_file']['path']
            new_path = old_path.replace('/core/', '/').replace('core/', '')
            agent_config['core_file']['path'] = new_path
        
        if 'prompt' in agent_config:
            # Update prompt path to current_prompt.md
            agent_config['prompt']['path'] = f"agents/{agent_name}/current_prompt.md"
        
        if 'examples' in agent_config:
            # Update examples path to current_example.json
            agent_config['examples']['path'] = f"agents/{agent_name}/current_example.json"
    
    # Write back the updated config
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print("Updated config.yaml with new paths")

def main():
    """Main reorganization function"""
    agents_dir = Path("agents")
    
    if not agents_dir.exists():
        print("Agents directory not found!")
        return
    
    # Get list of agent directories
    agent_dirs = [d for d in agents_dir.iterdir() if d.is_dir() and not d.name.startswith('__')]
    
    print(f"Found {len(agent_dirs)} agent directories to reorganize...")
    
    # Reorganize each agent
    for agent_dir in agent_dirs:
        if agent_dir.name in ['common', '__pycache__']:
            continue
        reorganize_agent(agent_dir, agent_dir.name)
    
    # Update config file
    update_config_file()
    
    print("\nReorganization complete!")
    print("New structure: agents/{agent_name}/[models/, current_prompt.md, prompts/, current_example.json, examples/, {agent_name}.py, metrics/, tests/]")

if __name__ == "__main__":
    main() 