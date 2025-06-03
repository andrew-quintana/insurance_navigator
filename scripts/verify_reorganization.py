#!/usr/bin/env python3
"""
Script to verify that the agent reorganization was successful.
Tests imports and config file updates.
"""

import sys
import yaml
from pathlib import Path

def test_agent_imports():
    """Test that all agents can be imported successfully"""
    print("Testing agent imports after reorganization:")
    
    agents_to_test = [
        ('agents.patient_navigator.patient_navigator', 'PatientNavigatorAgent'),
        ('agents.prompt_security.prompt_security', 'PromptSecurityAgent'),
        ('agents.task_requirements.task_requirements', 'TaskRequirementsAgent'),
        ('agents.service_access_strategy.service_access_strategy', 'ServiceAccessStrategyAgent'),
    ]
    
    success_count = 0
    for module_path, class_name in agents_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            print(f'✓ {class_name} import successful')
            success_count += 1
        except Exception as e:
            print(f'✗ {class_name} import failed: {e}')
    
    return success_count, len(agents_to_test)

def test_config_updates():
    """Test that config file has been updated with new paths"""
    print("\nTesting config file access:")
    
    try:
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        success_count = 0
        total_count = 0
        
        for agent_name in ['patient_navigator', 'prompt_security', 'task_requirements']:
            total_count += 1
            try:
                agent_config = config['agents'][agent_name]
                core_file_path = agent_config['core_file']['path']
                prompt_path = agent_config['prompt']['path']
                
                # Check that paths don't contain 'core'
                if 'core' not in core_file_path and 'core' not in prompt_path:
                    print(f'✓ {agent_name} config paths updated correctly:')
                    print(f'  Core file: {core_file_path}')
                    print(f'  Prompt: {prompt_path}')
                    success_count += 1
                else:
                    print(f'✗ {agent_name} config still contains old core paths')
                    
            except Exception as e:
                print(f'✗ {agent_name} config test failed: {e}')
        
        return success_count, total_count
        
    except Exception as e:
        print(f'✗ Config file test failed: {e}')
        return 0, 1

def test_file_structure():
    """Test that files are in the expected locations"""
    print("\nTesting file structure:")
    
    agents = ['patient_navigator', 'prompt_security', 'task_requirements']
    success_count = 0
    total_count = 0
    
    for agent in agents:
        agent_dir = Path(f'agents/{agent}')
        
        # Check for key files at root level
        expected_files = [
            f'{agent}.py',
            'current_prompt.md',
            'models',  # directory
        ]
        
        for expected_file in expected_files:
            total_count += 1
            file_path = agent_dir / expected_file
            if file_path.exists():
                print(f'✓ {agent}/{expected_file} exists')
                success_count += 1
            else:
                print(f'✗ {agent}/{expected_file} missing')
    
    return success_count, total_count

def main():
    """Main verification function"""
    print("=" * 50)
    print("AGENT REORGANIZATION VERIFICATION")
    print("=" * 50)
    
    # Test imports
    import_success, import_total = test_agent_imports()
    
    # Test config updates
    config_success, config_total = test_config_updates()
    
    # Test file structure
    structure_success, structure_total = test_file_structure()
    
    # Summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)
    print(f"Agent imports: {import_success}/{import_total} successful")
    print(f"Config updates: {config_success}/{config_total} successful")
    print(f"File structure: {structure_success}/{structure_total} successful")
    
    total_success = import_success + config_success + structure_success
    total_tests = import_total + config_total + structure_total
    
    print(f"\nOverall: {total_success}/{total_tests} tests passed")
    
    if total_success == total_tests:
        print("🎉 Reorganization completed successfully!")
    else:
        print("⚠️  Some issues found. Please review the output above.")

if __name__ == "__main__":
    main() 