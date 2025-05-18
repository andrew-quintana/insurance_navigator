"""
Configuration Manager

This module provides a standardized configuration management system.
It loads configuration from YAML files and supports environment variable overrides.
"""

import os
import yaml
import json
import datetime
from typing import Dict, Any, Optional, List, Union
from utils.error_handling import ConfigurationError

# Constants
DEFAULT_CONFIG_PATH = os.path.join("config", "config.yaml")
ENV_PREFIX = "INSURANCE_NAV"


class ConfigManager:
    """Secure configuration management with version control."""
    
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH, env_prefix: str = ENV_PREFIX):
        """Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file
            env_prefix: Prefix for environment variables
        """
        self.config_path = config_path
        self.env_prefix = env_prefix
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and environment."""
        try:
            config = self._load_file_config()
            config = self._override_from_env(config)
            return self._validate_config(config)
        except (FileNotFoundError, yaml.YAMLError) as e:
            if isinstance(e, FileNotFoundError):
                raise ConfigurationError(f"Configuration file not found: {self.config_path}")
            else:
                raise ConfigurationError(f"Invalid YAML in configuration file: {self.config_path}")
    
    def _load_file_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        with open(self.config_path, 'r') as f:
            # Check file extension and load accordingly
            if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                return yaml.safe_load(f)
            elif self.config_path.endswith('.json'):
                return json.load(f)
            else:
                raise ConfigurationError(f"Unsupported configuration file format: {self.config_path}")
    
    def _override_from_env(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Override configuration from environment variables.
        
        Environment variables should be in the format:
        ENV_PREFIX_SECTION_KEY=value
        
        For example:
        INSURANCE_NAV_AGENT_PROMPT_SECURITY_MODEL_TEMPERATURE=0.7
        """
        # Make a deep copy of the config to avoid modifying the original
        config_copy = {}
        
        # Function to recursively update nested dictionaries with env var value
        def update_nested_dict(d, keys, value):
            if len(keys) == 1:
                # Last key, assign the value
                d[keys[0]] = value
            else:
                # Initialize the next level if it doesn't exist
                if keys[0] not in d:
                    d[keys[0]] = {}
                # Recurse to the next level
                update_nested_dict(d[keys[0]], keys[1:], value)
            return d
        
        # Add all existing config
        for key, value in config.items():
            config_copy[key] = value
        
        # Process environment variables
        prefix_len = len(self.env_prefix) + 1  # +1 for the underscore
        for key, value in os.environ.items():
            if key.startswith(f"{self.env_prefix}_"):
                # Convert string value to appropriate type
                try:
                    if value.lower() == 'true':
                        typed_value = True
                    elif value.lower() == 'false':
                        typed_value = False
                    elif value.isdigit():
                        typed_value = int(value)
                    elif '.' in value and all(part.isdigit() for part in value.split('.', 1)):
                        typed_value = float(value)
                    else:
                        typed_value = value
                except (ValueError, AttributeError):
                    # If conversion fails, use the string value
                    typed_value = value
                
                # Extract the keys by splitting the environment variable name
                env_key = key[prefix_len:]
                env_key_parts = env_key.lower().split('_')
                
                # Update the config with this value
                update_nested_dict(config_copy, env_key_parts, typed_value)
        
        return config_copy
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration structure and values."""
        # Required top-level keys
        required_keys = ["version", "agents", "logging"]
        
        for key in required_keys:
            if key not in config:
                raise ConfigurationError(f"Missing required configuration key: {key}")
        
        # Validate agents section
        if not isinstance(config["agents"], dict):
            raise ConfigurationError("Agents configuration must be a dictionary")
        
        for agent_name, agent_config in config["agents"].items():
            self._validate_agent_config(agent_name, agent_config)
        
        return config
    
    def _validate_agent_config(self, agent_name: str, agent_config: Dict[str, Any]) -> None:
        """Validate the configuration for a specific agent."""
        # Required keys for each agent
        required_agent_keys = [
            "active", "description", "core_file", "prompt", 
            "examples", "model"
        ]
        
        for key in required_agent_keys:
            if key not in agent_config:
                raise ConfigurationError(f"Missing required configuration key for agent {agent_name}: {key}")
        
        # Validate core_file, prompt, and examples
        for section in ["core_file", "prompt", "examples"]:
            if "path" not in agent_config[section]:
                raise ConfigurationError(f"Missing path in {section} for agent {agent_name}")
            if "version" not in agent_config[section]:
                raise ConfigurationError(f"Missing version in {section} for agent {agent_name}")
        
        # Validate model configuration
        model_config = agent_config["model"]
        if "name" not in model_config:
            raise ConfigurationError(f"Missing model name for agent {agent_name}")
        if "temperature" not in model_config:
            raise ConfigurationError(f"Missing model temperature for agent {agent_name}")
    
    def save_config(self, file_path: Optional[str] = None) -> None:
        """Save the current configuration to file."""
        # Update the last_updated timestamp
        self._config["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Determine the output path
        output_path = file_path or self.config_path
        
        # Check file extension and save accordingly
        if output_path.endswith('.yaml') or output_path.endswith('.yml'):
            with open(output_path, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)
        elif output_path.endswith('.json'):
            with open(output_path, 'w') as f:
                json.dump(self._config, f, indent=2)
        else:
            raise ConfigurationError(f"Unsupported configuration file format: {output_path}")
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get the configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary containing the agent's configuration
            
        Raises:
            ConfigurationError: If the agent is not found in the configuration
        """
        if agent_name not in self._config["agents"]:
            raise ConfigurationError(f"Agent not found in configuration: {agent_name}")
        
        return self._config["agents"][agent_name]
    
    def get_all_agents(self) -> List[str]:
        """Get a list of all agent names in the configuration."""
        return list(self._config["agents"].keys())
    
    def get_active_agents(self) -> List[str]:
        """Get a list of active agent names."""
        return [
            name for name, config in self._config["agents"].items()
            if config.get("active", False)
        ]
    
    def update_agent_config(self, agent_name: str, agent_config: Dict[str, Any]) -> None:
        """Update the configuration for a specific agent."""
        if agent_name not in self._config["agents"]:
            raise ConfigurationError(f"Agent not found in configuration: {agent_name}")
        
        # Validate the new configuration
        self._validate_agent_config(agent_name, agent_config)
        
        # Update the configuration
        self._config["agents"][agent_name] = agent_config
        
        # Save the updated configuration
        self.save_config()
    
    def add_new_agent(self, agent_name: str, agent_config: Dict[str, Any]) -> None:
        """Add a new agent to the configuration."""
        if agent_name in self._config["agents"]:
            raise ConfigurationError(f"Agent already exists in configuration: {agent_name}")
        
        # Validate the new configuration
        self._validate_agent_config(agent_name, agent_config)
        
        # Add the new agent
        self._config["agents"][agent_name] = agent_config
        
        # Save the updated configuration
        self.save_config()
    
    def remove_agent(self, agent_name: str) -> None:
        """Remove an agent from the configuration."""
        if agent_name not in self._config["agents"]:
            raise ConfigurationError(f"Agent not found in configuration: {agent_name}")
        
        # Remove the agent
        del self._config["agents"][agent_name]
        
        # Save the updated configuration
        self.save_config()
    
    def get_config_value(self, config_key: str, default: Any = None) -> Any:
        """Get a configuration value by key path.
        
        Args:
            config_key: Dot-separated key path (e.g., "logging.level")
            default: Default value to return if the key is not found
            
        Returns:
            Configuration value or default
        """
        keys = config_key.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_config_value(self, config_key: str, value: Any) -> None:
        """Set a configuration value by key path.
        
        Args:
            config_key: Dot-separated key path (e.g., "logging.level")
            value: Value to set
        """
        keys = config_key.split('.')
        config = self._config
        
        # Navigate to the appropriate nested level
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
        
        # Save the updated configuration
        self.save_config()


# Singleton instance
_instance = None

def get_config_manager(config_path: str = DEFAULT_CONFIG_PATH) -> ConfigManager:
    """Get a singleton instance of the configuration manager."""
    global _instance
    if _instance is None or _instance.config_path != config_path:
        _instance = ConfigManager(config_path)
    return _instance


def convert_json_to_yaml(json_path: str, yaml_path: str) -> None:
    """Convert a JSON configuration file to YAML format."""
    try:
        # Load JSON
        with open(json_path, 'r') as f:
            config = json.load(f)
        
        # Save as YAML
        with open(yaml_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        return True
    except Exception as e:
        raise ConfigurationError(f"Failed to convert JSON to YAML: {str(e)}")


if __name__ == "__main__":
    # Simple CLI for testing or conversion
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "convert":
        if len(sys.argv) != 4:
            print("Usage: python config_manager.py convert input.json output.yaml")
            sys.exit(1)
        
        json_path = sys.argv[2]
        yaml_path = sys.argv[3]
        
        try:
            convert_json_to_yaml(json_path, yaml_path)
            print(f"Successfully converted {json_path} to {yaml_path}")
        except ConfigurationError as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
    else:
        # Load and display configuration
        try:
            config_manager = get_config_manager()
            print(f"Configuration loaded from {config_manager.config_path}")
            print(f"Version: {config_manager.get_config_value('version')}")
            print(f"Total agents: {len(config_manager.get_all_agents())}")
            print(f"Active agents: {len(config_manager.get_active_agents())}")
        except ConfigurationError as e:
            print(f"Error: {str(e)}")
            sys.exit(1) 