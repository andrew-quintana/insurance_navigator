"""
Agent Configuration Manager

This module provides utilities for loading, updating, and managing agent configurations.
It serves as a central point for accessing agent prompts, examples, and test cases.
"""

import os
import json
import time
import datetime
from typing import Dict, Any, Optional, List, Union

# Default configuration path
DEFAULT_CONFIG_PATH = os.path.join("config", "agent_config.json")

class AgentConfigManager:
    """Manager for agent configurations."""
    
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        """Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in configuration file: {self.config_path}")
    
    def save_config(self) -> None:
        """Save the current configuration to file."""
        # Update the last_updated timestamp
        self.config["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d")
        
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get the configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary containing the agent's configuration
            
        Raises:
            ValueError: If the agent is not found in the configuration
        """
        if agent_name not in self.config["agents"]:
            raise ValueError(f"Agent not found in configuration: {agent_name}")
        
        return self.config["agents"][agent_name]
    
    def get_all_agents(self) -> List[str]:
        """Get a list of all agent names in the configuration."""
        return list(self.config["agents"].keys())
    
    def get_active_agents(self) -> List[str]:
        """Get a list of active agent names."""
        return [
            name for name, config in self.config["agents"].items()
            if config.get("active", False)
        ]
    
    def get_prompt_path(self, agent_name: str) -> str:
        """Get the path to the prompt file for an agent."""
        agent_config = self.get_agent_config(agent_name)
        return agent_config["prompt"]["path"]
    
    def get_examples_path(self, agent_name: str) -> str:
        """Get the path to the examples file for an agent."""
        agent_config = self.get_agent_config(agent_name)
        return agent_config["examples"]["path"]
    
    def get_test_examples_path(self, agent_name: str) -> str:
        """Get the path to the test examples file for an agent."""
        agent_config = self.get_agent_config(agent_name)
        return agent_config["test_examples"]["path"]
    
    def get_model_config(self, agent_name: str) -> Dict[str, Any]:
        """Get the model configuration for an agent."""
        agent_config = self.get_agent_config(agent_name)
        return agent_config["model"]
    
    def update_agent_prompt(
        self, 
        agent_name: str, 
        version: str, 
        path: str, 
        description: str
    ) -> None:
        """Update the prompt configuration for an agent.
        
        Args:
            agent_name: Name of the agent
            version: New version of the prompt
            path: Path to the prompt file
            description: Description of the prompt
        """
        agent_config = self.get_agent_config(agent_name)
        agent_config["prompt"] = {
            "version": version,
            "path": path,
            "description": description
        }
        self.save_config()
    
    def update_agent_examples(
        self, 
        agent_name: str, 
        version: str, 
        path: str, 
        description: str
    ) -> None:
        """Update the examples configuration for an agent."""
        agent_config = self.get_agent_config(agent_name)
        agent_config["examples"] = {
            "version": version,
            "path": path,
            "description": description
        }
        self.save_config()
    
    def update_agent_test_examples(
        self, 
        agent_name: str, 
        version: str, 
        path: str, 
        description: str
    ) -> None:
        """Update the test examples configuration for an agent."""
        agent_config = self.get_agent_config(agent_name)
        agent_config["test_examples"] = {
            "version": version,
            "path": path,
            "description": description
        }
        self.save_config()
    
    def update_metrics_run(self, agent_name: str, metrics_path: str) -> None:
        """Update the latest metrics run for an agent."""
        agent_config = self.get_agent_config(agent_name)
        agent_config["metrics"]["latest_run"] = metrics_path
        self.save_config()
    
    def toggle_agent_active(self, agent_name: str, active: bool) -> None:
        """Toggle whether an agent is active."""
        agent_config = self.get_agent_config(agent_name)
        agent_config["active"] = active
        self.save_config()
    
    def add_new_agent(
        self,
        agent_name: str,
        description: str,
        prompt: Dict[str, str],
        examples: Dict[str, str],
        test_examples: Dict[str, str],
        model: Dict[str, Any],
        active: bool = True
    ) -> None:
        """Add a new agent to the configuration."""
        if agent_name in self.config["agents"]:
            raise ValueError(f"Agent already exists in configuration: {agent_name}")
        
        self.config["agents"][agent_name] = {
            "active": active,
            "description": description,
            "prompt": prompt,
            "examples": examples,
            "test_examples": test_examples,
            "model": model,
            "metrics": {
                "latest_run": None
            }
        }
        self.save_config()
    
    def remove_agent(self, agent_name: str) -> None:
        """Remove an agent from the configuration."""
        if agent_name not in self.config["agents"]:
            raise ValueError(f"Agent not found in configuration: {agent_name}")
        
        del self.config["agents"][agent_name]
        self.save_config()
    
    def print_agent_summary(self, agent_name: Optional[str] = None) -> None:
        """Print a summary of agent configurations.
        
        Args:
            agent_name: Optional name of a specific agent to summarize
        """
        if agent_name:
            # Print summary for a specific agent
            try:
                agent_config = self.get_agent_config(agent_name)
                print(f"\n=== {agent_name.upper()} ===")
                print(f"Active: {agent_config['active']}")
                print(f"Description: {agent_config['description']}")
                print(f"Prompt: v{agent_config['prompt']['version']} - {agent_config['prompt']['path']}")
                print(f"Examples: v{agent_config['examples']['version']} - {agent_config['examples']['path']}")
                print(f"Test Examples: v{agent_config['test_examples']['version']} - {agent_config['test_examples']['path']}")
                print(f"Model: {agent_config['model']['name']} (temp={agent_config['model']['temperature']})")
                print(f"Latest Metrics: {agent_config['metrics']['latest_run'] or 'None'}")
            except ValueError:
                print(f"Agent not found: {agent_name}")
        else:
            # Print summary for all agents
            print("\n=== AGENT CONFIGURATION SUMMARY ===")
            print(f"Total Agents: {len(self.config['agents'])}")
            print(f"Active Agents: {len(self.get_active_agents())}")
            print(f"Last Updated: {self.config['last_updated']}")
            print("\nACTIVE AGENTS:")
            
            for name in self.get_active_agents():
                agent_config = self.get_agent_config(name)
                print(f"  - {name}: v{agent_config['prompt']['version']} ({agent_config['model']['name']})")
            
            print("\nINACTIVE AGENTS:")
            inactive = set(self.get_all_agents()) - set(self.get_active_agents())
            for name in inactive:
                agent_config = self.get_agent_config(name)
                print(f"  - {name}: v{agent_config['prompt']['version']} ({agent_config['model']['name']})")

# Convenience function to get a singleton instance
_instance = None

def get_config_manager(config_path: str = DEFAULT_CONFIG_PATH) -> AgentConfigManager:
    """Get a singleton instance of the configuration manager."""
    global _instance
    if _instance is None:
        _instance = AgentConfigManager(config_path)
    return _instance

if __name__ == "__main__":
    # Simple CLI for testing
    manager = get_config_manager()
    
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            manager.print_agent_summary()
        elif sys.argv[1] == "show" and len(sys.argv) > 2:
            manager.print_agent_summary(sys.argv[2])
        else:
            print("Usage: python agent_config_manager.py [list|show <agent_name>]")
    else:
        manager.print_agent_summary() 