#!/usr/bin/env python3
"""
Convert All Agents Script

This script converts all agent files to use the prompt_loader utility.
It runs the conversion step by step with confirmation for each agent.
"""

import os
import sys
import subprocess
import argparse
from typing import List, Tuple
import glob

# Get the list of all agent files
def get_agent_files() -> List[Tuple[str, str]]:
    """
    Get a list of all agent files.
    
    Returns:
        List of tuples (agent_name, file_path)
    """
    agents_dir = os.path.join(os.path.dirname(__file__), "agents")
    agent_files = []
    
    for file_path in glob.glob(os.path.join(agents_dir, "*.py")):
        agent_name = os.path.splitext(os.path.basename(file_path))[0]
        if agent_name != "__init__" and agent_name != "base_agent":
            agent_files.append((agent_name, file_path))
    
    return agent_files

def convert_agent(agent_name: str, dry_run: bool = False) -> bool:
    """
    Convert an agent to use prompt_loader.
    
    Args:
        agent_name: Name of the agent to convert
        dry_run: Whether to run in dry-run mode
        
    Returns:
        True if conversion was successful, False otherwise
    """
    cmd = ["python", "-m", "utils.convert_to_prompt_loader", f"--agent={agent_name}"]
    if dry_run:
        cmd.append("--dry-run")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Warnings/Errors: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error converting {agent_name}: {e}")
        print(f"Output: {e.output}")
        print(f"Error: {e.stderr}")
        return False

def run_tests(agent_name: str) -> bool:
    """
    Run tests for an agent.
    
    Args:
        agent_name: Name of the agent to test
        
    Returns:
        True if tests passed, False otherwise
    """
    test_file = f"tests/test_{agent_name}_with_loader.py"
    
    # Check if the test file exists
    if not os.path.exists(test_file):
        print(f"Test file {test_file} does not exist. Skipping tests.")
        return False
    
    try:
        result = subprocess.run(["python", "-m", test_file], check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Warnings/Errors: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Tests failed for {agent_name}: {e}")
        print(f"Output: {e.output}")
        print(f"Error: {e.stderr}")
        return False

def main() -> None:
    """Convert all agents to use prompt_loader."""
    parser = argparse.ArgumentParser(description="Convert all agents to use prompt_loader")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without modifying files")
    parser.add_argument("--force", action="store_true", help="Convert all agents without confirmation")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests after conversion")
    args = parser.parse_args()
    
    print("Converting agents to use prompt_loader...\n")
    
    # Get all agent files
    agent_files = get_agent_files()
    
    # Print the list of agents to convert
    print(f"Found {len(agent_files)} agents to convert:")
    for i, (agent_name, _) in enumerate(agent_files, 1):
        print(f"{i}. {agent_name}")
    print()
    
    # Process each agent
    for i, (agent_name, file_path) in enumerate(agent_files, 1):
        print(f"\n{'=' * 80}")
        print(f"Processing agent {i}/{len(agent_files)}: {agent_name}")
        print(f"{'=' * 80}")
        
        # Ask for confirmation unless force is specified
        if not args.force:
            confirm = input(f"Convert {agent_name}? [y/N/q] ").lower()
            if confirm == "q":
                print("Exiting...")
                sys.exit(0)
            if confirm != "y":
                print(f"Skipping {agent_name}\n")
                continue
        
        # Convert the agent
        success = convert_agent(agent_name, args.dry_run)
        if not success:
            print(f"Failed to convert {agent_name}. Skipping tests.\n")
            continue
        
        # Run tests unless skip-tests is specified
        if not args.skip_tests and not args.dry_run:
            print(f"\nRunning tests for {agent_name}...")
            run_tests(agent_name)
        
        print(f"\nCompleted processing {agent_name}\n")
    
    print("\nConversion completed!")

if __name__ == "__main__":
    main() 