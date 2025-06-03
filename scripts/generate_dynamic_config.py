#!/usr/bin/env python3
"""
Generate dynamic config based on actual agent files
"""

import os
import glob
import yaml
from pathlib import Path

def find_files_by_pattern(agent_dir, patterns):
    """Find files matching patterns in agent directory"""
    for pattern in patterns:
        # Search in root directory
        matches = list(Path(agent_dir).glob(pattern))
        if matches:
            return str(matches[0].relative_to('.'))
        
        # Search in subdirectories
        matches = list(Path(agent_dir).rglob(pattern))
        if matches:
            return str(matches[0].relative_to('.'))
    
    return None

def scan_agent(agent_name):
    """Scan a single agent directory for files"""
    agent_dir = f"agents/{agent_name}"
    
    if not os.path.exists(agent_dir):
        return None
    
    # Define patterns to search for
    patterns = {
        'core_file': [f"{agent_name}.py"],
        'prompt': [f"prompt_{agent_name}*.md", f"*{agent_name}*.md"],
        'examples': [f"prompt_examples_{agent_name}*.json", f"*examples*{agent_name}*.json"],
        'models': [f"{agent_name}_models.py", f"*models.py"]
    }
    
    found_files = {}
    for file_type, pattern_list in patterns.items():
        found_files[file_type] = find_files_by_pattern(agent_dir, pattern_list)
    
    return found_files

def get_agent_info(agent_name):
    """Get agent-specific configuration"""
    agent_configs = {
        'prompt_security': {
            'description': 'Agent responsible for ensuring prompt security and content safety',
            'model': {'name': 'claude-3-7-sonnet-20250219', 'temperature': 0.0}
        },
        'patient_navigator': {
            'description': 'Agent responsible for guiding patients through insurance processes',
            'model': {'name': 'claude-3-7-sonnet-20250219', 'temperature': 0.7}
        },
        'task_requirements': {
            'description': 'Agent responsible for determining required documentation for tasks',
            'model': {'name': 'claude-3-7-sonnet-20250219', 'temperature': 0.2}
        },
        'service_access_strategy': {
            'description': 'Agent responsible for coming up with strategies for accessing services',
            'model': {'name': 'claude-3-7-sonnet-20250219', 'temperature': 0.2}
        },
        'chat_communicator': {
            'description': 'Agent responsible for communicating with users in conversational language',
            'model': {'name': 'claude-3-sonnet-20240229-v1h', 'temperature': 0.2}
        },
        'regulatory': {
            'description': 'Agent responsible for regulatory research and compliance analysis',
            'model': {'name': 'claude-3-7-sonnet-20250219', 'temperature': 0.1}
        }
    }
    
    return agent_configs.get(agent_name, {
        'description': f'Agent for {agent_name} functionality',
        'model': {'name': 'claude-3-7-sonnet-20250219', 'temperature': 0.2}
    })

def generate_config():
    """Generate the complete configuration"""
    
    # Scan agents directory
    agents_dir = Path("agents")
    agent_names = [d.name for d in agents_dir.iterdir() 
                   if d.is_dir() and not d.name.startswith('.') 
                   and d.name not in ['common', '__pycache__']]
    
    print(f"Found agent directories: {agent_names}")
    
    agents_config = {}
    
    for agent_name in agent_names:
        print(f"\nScanning {agent_name}...")
        found_files = scan_agent(agent_name)
        
        if found_files and found_files.get('core_file'):
            agent_info = get_agent_info(agent_name)
            
            config = {
                'active': True,
                'description': agent_info['description'],
                'core_file': {
                    'path': found_files['core_file'],
                    'version': 'auto-detected'
                },
                'model': agent_info['model'],
                'metrics': {
                    'latest_run': f"agents/{agent_name}/metrics/performance_metrics_latest.json"
                }
            }
            
            # Add optional fields if files exist
            if found_files.get('prompt'):
                config['prompt'] = {
                    'version': 'auto-detected',
                    'path': found_files['prompt'],
                    'description': f"{agent_info['description']} prompt"
                }
                print(f"  ✅ Prompt: {found_files['prompt']}")
            else:
                print(f"  ❌ No prompt file found")
            
            if found_files.get('examples'):
                config['examples'] = {
                    'version': 'auto-detected',
                    'path': found_files['examples']
                }
                print(f"  ✅ Examples: {found_files['examples']}")
            else:
                print(f"  ❌ No examples file found")
            
            if found_files.get('models'):
                config['models'] = {
                    'path': found_files['models']
                }
                print(f"  ✅ Models: {found_files['models']}")
            else:
                print(f"  ❌ No models file found")
            
            agents_config[agent_name] = config
            print(f"  ✅ Core: {found_files['core_file']}")
        
        else:
            print(f"  ❌ No core file found, skipping {agent_name}")
    
    # Build complete config
    config = {
        'version': '1.0.0',
        'last_updated': '2025-01-01',
        'agents': agents_config,
        'performance_metrics': {
            'enabled': True,
            'save_directory': 'metrics',
            'track_memory': True,
            'track_tokens': True
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'save_directory': 'logs',
            'file_rotation': 'daily',
            'max_file_size': 10485760
        },
        'security': {
            'validate_inputs': True,
            'sanitize_outputs': True,
            'max_token_limit': 4096,
            'blocked_patterns': [
                'ignore previous instructions',
                'disregard all instructions',
                'system prompt'
            ]
        },
        'authentication': {
            'jwt': {
                'algorithm': 'HS256',
                'access_token_expire_minutes': 1440
            }
        }
    }
    
    # Write config
    with open('config/config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"\n🎉 Generated config for {len(agents_config)} agents!")
    print(f"📝 Config written to config/config.yaml")
    
    # Validate files exist
    errors = []
    for agent_name, agent_config in agents_config.items():
        for section in ['core_file', 'prompt', 'examples', 'models']:
            if section in agent_config and 'path' in agent_config[section]:
                path = agent_config[section]['path']
                if not os.path.exists(path):
                    errors.append(f"{agent_name}: {section} file not found: {path}")
    
    if errors:
        print(f"\n⚠️  Validation errors:")
        for error in errors:
            print(f"   • {error}")
    else:
        print(f"\n✅ All referenced files exist!")
    
    return config

if __name__ == "__main__":
    print("🔍 Dynamic Config Generator")
    print("=" * 50)
    generate_config() 