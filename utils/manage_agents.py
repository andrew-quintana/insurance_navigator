#!/usr/bin/env python
"""
Agent Management CLI

This script provides a command-line interface for managing agent configurations.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from utils.agent_config_manager import get_config_manager, AgentConfigManager

def list_agents(args):
    """List all agents in the configuration."""
    manager = get_config_manager()
    manager.print_agent_summary()

def show_agent(args):
    """Show details for a specific agent."""
    manager = get_config_manager()
    manager.print_agent_summary(args.agent_name)

def toggle_agent(args):
    """Toggle whether an agent is active."""
    manager = get_config_manager()
    manager.toggle_agent_active(args.agent_name, args.active)
    print(f"Agent '{args.agent_name}' is now {'active' if args.active else 'inactive'}")

def update_prompt(args):
    """Update the prompt for an agent."""
    manager = get_config_manager()
    manager.update_agent_prompt(
        args.agent_name,
        args.version,
        args.path,
        args.description
    )
    print(f"Updated prompt for agent '{args.agent_name}' to version {args.version}")

def update_examples(args):
    """Update the examples for an agent."""
    manager = get_config_manager()
    manager.update_agent_examples(
        args.agent_name,
        args.version,
        args.path,
        args.description
    )
    print(f"Updated examples for agent '{args.agent_name}' to version {args.version}")

def update_test_examples(args):
    """Update the test examples for an agent."""
    manager = get_config_manager()
    manager.update_agent_test_examples(
        args.agent_name,
        args.version,
        args.path,
        args.description
    )
    print(f"Updated test examples for agent '{args.agent_name}' to version {args.version}")

def add_agent(args):
    """Add a new agent to the configuration."""
    manager = get_config_manager()
    
    prompt = {
        "version": args.prompt_version,
        "path": args.prompt_path,
        "description": args.prompt_description
    }
    
    examples = {
        "version": args.examples_version,
        "path": args.examples_path,
        "description": args.examples_description
    }
    
    test_examples = {
        "version": args.test_examples_version,
        "path": args.test_examples_path,
        "description": args.test_examples_description
    }
    
    model = {
        "name": args.model_name,
        "temperature": args.temperature
    }
    
    manager.add_new_agent(
        args.agent_name,
        args.description,
        prompt,
        examples,
        test_examples,
        model,
        args.active
    )
    
    print(f"Added new agent '{args.agent_name}'")

def remove_agent(args):
    """Remove an agent from the configuration."""
    manager = get_config_manager()
    
    # Confirm removal
    if not args.force:
        confirm = input(f"Are you sure you want to remove agent '{args.agent_name}'? (y/n): ")
        if confirm.lower() != 'y':
            print("Operation cancelled")
            return
    
    manager.remove_agent(args.agent_name)
    print(f"Removed agent '{args.agent_name}'")

def run_performance_test(args):
    """Run a performance test for an agent."""
    manager = get_config_manager()
    
    # Check if agent exists and is active
    try:
        agent_config = manager.get_agent_config(args.agent_name)
        if not agent_config.get("active", False):
            print(f"Warning: Agent '{args.agent_name}' is not active")
            confirm = input("Continue anyway? (y/n): ")
            if confirm.lower() != 'y':
                print("Operation cancelled")
                return
    except ValueError:
        print(f"Agent '{args.agent_name}' not found in configuration")
        return
    
    # Import the test performance script dynamically
    test_script_path = os.path.join("agents", args.agent_name, "tests", "test_performance.py")
    if not os.path.exists(test_script_path):
        print(f"Test script not found: {test_script_path}")
        return
    
    # Run the test script
    print(f"Running performance test for agent '{args.agent_name}'...")
    print(f"This will use the test examples from: {agent_config['test_examples']['path']}")
    
    # Use mock mode if specified
    mock_arg = "--mock" if args.mock else ""
    os.system(f"python {test_script_path} {mock_arg}")

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Manage agent configurations")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List agents command
    list_parser = subparsers.add_parser("list", help="List all agents")
    list_parser.set_defaults(func=list_agents)
    
    # Show agent command
    show_parser = subparsers.add_parser("show", help="Show details for a specific agent")
    show_parser.add_argument("agent_name", help="Name of the agent")
    show_parser.set_defaults(func=show_agent)
    
    # Toggle agent command
    toggle_parser = subparsers.add_parser("toggle", help="Toggle whether an agent is active")
    toggle_parser.add_argument("agent_name", help="Name of the agent")
    toggle_parser.add_argument("--active", action="store_true", help="Set agent to active")
    toggle_parser.add_argument("--inactive", dest="active", action="store_false", help="Set agent to inactive")
    toggle_parser.set_defaults(func=toggle_agent, active=True)
    
    # Update prompt command
    update_prompt_parser = subparsers.add_parser("update-prompt", help="Update the prompt for an agent")
    update_prompt_parser.add_argument("agent_name", help="Name of the agent")
    update_prompt_parser.add_argument("--version", required=True, help="New version of the prompt")
    update_prompt_parser.add_argument("--path", required=True, help="Path to the prompt file")
    update_prompt_parser.add_argument("--description", required=True, help="Description of the prompt")
    update_prompt_parser.set_defaults(func=update_prompt)
    
    # Update examples command
    update_examples_parser = subparsers.add_parser("update-examples", help="Update the examples for an agent")
    update_examples_parser.add_argument("agent_name", help="Name of the agent")
    update_examples_parser.add_argument("--version", required=True, help="New version of the examples")
    update_examples_parser.add_argument("--path", required=True, help="Path to the examples file")
    update_examples_parser.add_argument("--description", required=True, help="Description of the examples")
    update_examples_parser.set_defaults(func=update_examples)
    
    # Update test examples command
    update_test_examples_parser = subparsers.add_parser("update-test-examples", help="Update the test examples for an agent")
    update_test_examples_parser.add_argument("agent_name", help="Name of the agent")
    update_test_examples_parser.add_argument("--version", required=True, help="New version of the test examples")
    update_test_examples_parser.add_argument("--path", required=True, help="Path to the test examples file")
    update_test_examples_parser.add_argument("--description", required=True, help="Description of the test examples")
    update_test_examples_parser.set_defaults(func=update_test_examples)
    
    # Add agent command
    add_parser = subparsers.add_parser("add", help="Add a new agent to the configuration")
    add_parser.add_argument("agent_name", help="Name of the agent")
    add_parser.add_argument("--description", required=True, help="Description of the agent")
    add_parser.add_argument("--prompt-version", required=True, help="Version of the prompt")
    add_parser.add_argument("--prompt-path", required=True, help="Path to the prompt file")
    add_parser.add_argument("--prompt-description", required=True, help="Description of the prompt")
    add_parser.add_argument("--examples-version", required=True, help="Version of the examples")
    add_parser.add_argument("--examples-path", required=True, help="Path to the examples file")
    add_parser.add_argument("--examples-description", required=True, help="Description of the examples")
    add_parser.add_argument("--test-examples-version", required=True, help="Version of the test examples")
    add_parser.add_argument("--test-examples-path", required=True, help="Path to the test examples file")
    add_parser.add_argument("--test-examples-description", required=True, help="Description of the test examples")
    add_parser.add_argument("--model-name", required=True, help="Name of the model")
    add_parser.add_argument("--temperature", type=float, default=0.0, help="Temperature for the model")
    add_parser.add_argument("--active", action="store_true", default=True, help="Whether the agent is active")
    add_parser.set_defaults(func=add_agent)
    
    # Remove agent command
    remove_parser = subparsers.add_parser("remove", help="Remove an agent from the configuration")
    remove_parser.add_argument("agent_name", help="Name of the agent")
    remove_parser.add_argument("--force", action="store_true", help="Skip confirmation")
    remove_parser.set_defaults(func=remove_agent)
    
    # Test agent command
    test_parser = subparsers.add_parser("test", help="Run a performance test for an agent")
    test_parser.add_argument("agent_name", help="Name of the agent")
    test_parser.add_argument("--mock", action="store_true", help="Use mock mode for testing")
    test_parser.set_defaults(func=run_performance_test)
    
    # Parse arguments and execute the appropriate function
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 