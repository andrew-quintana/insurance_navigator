#!/usr/bin/env python3
"""
Dynamic Config Manager

Automatically detects agent files based on naming patterns.
This makes the config version-agnostic and self-updating.
"""

import os
import glob
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
import logging

logger = logging.getLogger(__name__)


class DynamicConfigManager:
    """
    Manages configuration by auto-detecting agent files based on patterns.
    """
    
    def __init__(self, base_path: str = "agents"):
        """
        Initialize the dynamic config manager.
        
        Args:
            base_path: Base path to the agents directory
        """
        self.base_path = Path(base_path)
        self.agents_dir = Path(base_path)
        
    def find_agent_files(self, agent_name: str) -> Dict[str, Optional[str]]:
        """
        Find agent files based on naming patterns.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary with found file paths
        """
        agent_dir = self.agents_dir / agent_name
        
        if not agent_dir.exists():
            logger.warning(f"Agent directory not found: {agent_dir}")
            return {}
        
        # Define search patterns
        patterns = {
            'core_file': [
                f"{agent_name}.py",
                f"*{agent_name}*.py"
            ],
            'prompt': [
                f"prompt_{agent_name}*.md",
                f"prompt_*{agent_name}*.md",
                f"current_prompt.md",
                f"{agent_name}_prompt*.md"
            ],
            'examples': [
                f"prompt_examples_{agent_name}*.json",
                f"examples_{agent_name}*.json", 
                f"current_example.json",
                f"{agent_name}_examples*.json"
            ],
            'models': [
                f"{agent_name}_models.py",
                f"models/{agent_name}_models.py",
                f"models.py"
            ]
        }
        
        found_files = {}
        
        for file_type, pattern_list in patterns.items():
            found_file = None
            
            for pattern in pattern_list:
                # Search in agent root directory first
                matches = list(agent_dir.glob(pattern))
                if matches:
                    found_file = str(matches[0].relative_to(Path('.')))
                    break
                
                # Search in subdirectories if not found in root
                if not matches and '/' not in pattern:
                    matches = list(agent_dir.rglob(pattern))
                    if matches:
                        found_file = str(matches[0].relative_to(Path('.')))
                        break
            
            found_files[file_type] = found_file
            
            if found_file:
                logger.debug(f"Found {file_type} for {agent_name}: {found_file}")
            else:
                logger.warning(f"No {file_type} found for {agent_name}")
        
        return found_files
    
    def scan_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        Scan all agent directories and detect their files.
        
        Returns:
            Dictionary of agent configurations
        """
        if not self.agents_dir.exists():
            logger.error(f"Agents directory not found: {self.agents_dir}")
            return {}
        
        agents_config = {}
        
        # Find all agent directories
        for item in self.agents_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name not in ['common', '__pycache__']:
                agent_name = item.name
                logger.info(f"Scanning agent: {agent_name}")
                
                # Find files for this agent
                found_files = self.find_agent_files(agent_name)
                
                if found_files.get('core_file'):
                    # Determine agent type and description
                    agent_info = self._get_agent_info(agent_name)
                    
                    agents_config[agent_name] = {
                        'active': True,
                        'description': agent_info['description'],
                        'core_file': {
                            'path': found_files['core_file'],
                            'version': 'auto-detected'
                        },
                        'prompt': {
                            'version': 'auto-detected',
                            'path': found_files['prompt'],
                            'description': f"{agent_info['description']} prompt"
                        } if found_files['prompt'] else None,
                        'examples': {
                            'version': 'auto-detected',
                            'path': found_files['examples']
                        } if found_files['examples'] else None,
                        'models': {
                            'path': found_files['models']
                        } if found_files['models'] else None,
                        'model': agent_info['model'],
                        'metrics': {
                            'latest_run': f"agents/{agent_name}/metrics/performance_metrics_latest.json"
                        }
                    }
                    
                    # Clean up None values
                    agents_config[agent_name] = {k: v for k, v in agents_config[agent_name].items() if v is not None}
                else:
                    logger.warning(f"No core file found for {agent_name}, skipping")
        
        return agents_config
    
    def _get_agent_info(self, agent_name: str) -> Dict[str, Any]:
        """
        Get agent-specific information like description and model settings.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary with agent information
        """
        # Default agent information
        agent_info = {
            'prompt_security': {
                'description': 'Agent responsible for ensuring prompt security and content safety',
                'model': {
                    'name': 'claude-sonnet-4-5',
                    'temperature': 0.0
                }
            },
            'patient_navigator': {
                'description': 'Agent responsible for guiding patients through insurance processes',
                'model': {
                    'name': 'claude-sonnet-4-5',
                    'temperature': 0.7
                }
            },
            'task_requirements': {
                'description': 'Agent responsible for determining required documentation for tasks',
                'model': {
                    'name': 'claude-sonnet-4-5',
                    'temperature': 0.2
                }
            },
            'service_access_strategy': {
                'description': 'Agent responsible for coming up with strategies for accessing services',
                'model': {
                    'name': 'claude-3-7-sonnet-20250219',
                    'temperature': 0.2
                }
            },
            'chat_communicator': {
                'description': 'Agent responsible for communicating with users in conversational language',
                'model': {
                    'name': 'claude-sonnet-4-5',
                    'temperature': 0.2
                }
            },
            'regulatory': {
                'description': 'Agent responsible for regulatory research and compliance analysis',
                'model': {
                    'name': 'claude-sonnet-4-5',
                    'temperature': 0.1
                }
            }
        }
        
        return agent_info.get(agent_name, {
            'description': f'Agent for {agent_name} functionality',
            'model': {
                'name': 'claude-sonnet-4-5',
                'temperature': 0.2
            }
        })
    
    def generate_config(self, output_file: str = "config/config.yaml") -> Dict[str, Any]:
        """
        Generate a complete configuration file with auto-detected agent files.
        
        Args:
            output_file: Path to output the configuration file
            
        Returns:
            The generated configuration dictionary
        """
        # Load existing config for non-agent settings
        existing_config = {}
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r') as f:
                    existing_config = yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Could not load existing config: {e}")
        
        # Scan agents
        agents_config = self.scan_all_agents()
        
        # Build complete config
        config = {
            'version': existing_config.get('version', '1.0.0'),
            'last_updated': existing_config.get('last_updated', '2025-01-01'),
            'agents': agents_config,
            'performance_metrics': existing_config.get('performance_metrics', {
                'enabled': True,
                'save_directory': 'metrics',
                'track_memory': True,
                'track_tokens': True
            }),
            'logging': existing_config.get('logging', {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'save_directory': 'logs',
                'file_rotation': 'daily',
                'max_file_size': 10485760
            }),
            'security': existing_config.get('security', {
                'validate_inputs': True,
                'sanitize_outputs': True,
                'max_token_limit': 4096,
                'blocked_patterns': [
                    'ignore previous instructions',
                    'disregard all instructions',
                    'system prompt'
                ]
            }),
            'authentication': existing_config.get('authentication', {
                'jwt': {
                    'algorithm': 'HS256',
                    'access_token_expire_minutes': 1440
                }
            })
        }
        
        # Write config file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Generated dynamic config with {len(agents_config)} agents")
        logger.info(f"Config written to: {output_file}")
        
        return config
    
    def validate_config(self, config_file: str = "config/config.yaml") -> List[str]:
        """
        Validate that all files referenced in config actually exist.
        
        Args:
            config_file: Path to the config file to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            return [f"Could not load config file: {e}"]
        
        agents = config.get('agents', {})
        
        for agent_name, agent_config in agents.items():
            # Check core file
            core_file = agent_config.get('core_file', {}).get('path')
            if core_file and not os.path.exists(core_file):
                errors.append(f"{agent_name}: Core file not found: {core_file}")
            
            # Check prompt file
            prompt_file = agent_config.get('prompt', {}).get('path')
            if prompt_file and not os.path.exists(prompt_file):
                errors.append(f"{agent_name}: Prompt file not found: {prompt_file}")
            
            # Check examples file
            examples_file = agent_config.get('examples', {}).get('path')
            if examples_file and not os.path.exists(examples_file):
                errors.append(f"{agent_name}: Examples file not found: {examples_file}")
            
            # Check models file
            models_file = agent_config.get('models', {}).get('path')
            if models_file and not os.path.exists(models_file):
                errors.append(f"{agent_name}: Models file not found: {models_file}")
        
        return errors


def main():
    """Main function to regenerate config."""
    print("🔍 Dynamic Config Generator")
    print("=" * 50)
    
    # Create dynamic config manager
    config_manager = DynamicConfigManager()
    
    # Generate new config
    config = config_manager.generate_config()
    
    # Validate the generated config
    errors = config_manager.validate_config()
    
    if errors:
        print(f"\n⚠️  Validation errors found:")
        for error in errors:
            print(f"   • {error}")
    else:
        print(f"\n✅ Config validation passed!")
    
    print(f"\n📊 Generated config for {len(config['agents'])} agents:")
    for agent_name in config['agents'].keys():
        print(f"   • {agent_name}")
    
    print(f"\n🎉 Dynamic config generation complete!")


if __name__ == "__main__":
    main() 