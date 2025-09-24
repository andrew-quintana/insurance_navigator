#!/usr/bin/env python3
"""
Fix YAML environment variable substitution
"""

import os
import re
import yaml

def substitute_env_vars(text):
    """Substitute environment variables in text like ${VAR_NAME}"""
    def replace_var(match):
        var_name = match.group(1)
        return os.getenv(var_name, match.group(0))
    
    # Use raw string for the pattern
    pattern = r'\$\{([^}]+)\}'
    return re.sub(pattern, replace_var, text)

def process_yaml_file(file_path):
    """Process a YAML file to substitute environment variables"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Substitute environment variables
    processed_content = substitute_env_vars(content)
    
    # Write back to file
    with open(file_path, 'w') as f:
        f.write(processed_content)
    
    print(f"Processed {file_path}")

def main():
    """Main function"""
    # Process development.yaml
    yaml_file = "config/environment/development.yaml"
    if os.path.exists(yaml_file):
        process_yaml_file(yaml_file)
    else:
        print(f"File {yaml_file} not found")

if __name__ == "__main__":
    main()
