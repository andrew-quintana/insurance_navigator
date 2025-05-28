"""
Configuration Manager for the Insurance Navigator system.

This module provides a centralized configuration manager for all agents in the system.
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("config_manager")

class ConfigManager:
    """
    Configuration manager for the Insurance Navigator system.
    
    This class loads and manages configurations for all agents in the system.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the config manager.
        
        Args:
            config_path: Path to the configuration file (defaults to 'config/config.yaml')
        """
        self.config_path = config_path or os.path.join("config", "config.yaml")
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """
        Load the configuration from file.
        
        Returns:
            The loaded configuration
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                        return yaml.safe_load(f)
                    else:
                        return json.load(f)
            else:
                logger.warning(f"Configuration file not found at {self.config_path}. Using default configuration.")
                return {}
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return {}
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent configuration dictionary
        """
        if not self.config:
            return {}
            
        if "agents" in self.config and agent_name in self.config["agents"]:
            return self.config["agents"][agent_name]
        elif agent_name in self.config:
            return self.config[agent_name]
        else:
            logger.warning(f"No configuration found for agent {agent_name}")
            return {}
    
    def get_model_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get model configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Model configuration dictionary
        """
        agent_config = self.get_agent_config(agent_name)
        if "model" in agent_config:
            return agent_config["model"]
        else:
            logger.warning(f"No model configuration found for agent {agent_name}")
            return {
                "name": "claude-3-sonnet-20240229-v1h",
                "temperature": 0.0
            }
    
    def get_prompt_path(self, agent_name: str) -> Optional[str]:
        """
        Get prompt path for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Path to the prompt file
        """
        agent_config = self.get_agent_config(agent_name)
        if "prompt" in agent_config and "path" in agent_config["prompt"]:
            return agent_config["prompt"]["path"]
        else:
            logger.warning(f"No prompt path found for agent {agent_name}")
            return None
    
    def get_examples_path(self, agent_name: str) -> Optional[str]:
        """
        Get examples path for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Path to the examples file
        """
        agent_config = self.get_agent_config(agent_name)
        if "examples" in agent_config and "path" in agent_config["examples"]:
            return agent_config["examples"]["path"]
        else:
            logger.warning(f"No examples path found for agent {agent_name}")
            return None


# Singleton instance
_config_manager = None

def get_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """
    Get the singleton instance of the config manager.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        The config manager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    return _config_manager 