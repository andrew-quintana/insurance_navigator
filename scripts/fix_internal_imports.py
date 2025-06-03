#!/usr/bin/env python3
"""
Script to fix internal imports that still reference the old core directory structure.
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern to match imports like: from agents.{agent_name}.core.{module} import ...
    pattern = r'from agents\.(\w+)\.core\.(\w+) import'
    replacement = r'from agents.\1.\2 import'
    content = re.sub(pattern, replacement, content)
    
    # Pattern to match imports like: from agents.{agent_name}.core.models.{model} import ...
    pattern = r'from agents\.(\w+)\.core\.models\.(\w+) import'
    replacement = r'from agents.\1.models.\2 import'
    content = re.sub(pattern, replacement, content)
    
    # Pattern to match imports like: from agents.{agent_name}.core.search.{module} import ...
    pattern = r'from agents\.(\w+)\.core\.search\.(\w+) import'
    replacement = r'from agents.\1.search.\2 import'
    content = re.sub(pattern, replacement, content)
    
    # Pattern to match imports like: from agents.{agent_name}.core.logic import ...
    pattern = r'from agents\.(\w+)\.core\.logic import'
    replacement = r'from agents.\1.logic import'
    content = re.sub(pattern, replacement, content)
    
    # If content changed, write it back
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed imports in {file_path}")
        return True
    return False

def find_and_fix_python_files():
    """Find all Python files and fix their imports"""
    fixed_count = 0
    
    # Find all Python files in the project
    for root, dirs, files in os.walk('.'):
        # Skip .venv, __pycache__, .git directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                if fix_imports_in_file(file_path):
                    fixed_count += 1
    
    return fixed_count

def main():
    """Main function to fix all internal imports"""
    print("Fixing internal imports that reference old core structure...")
    
    fixed_count = find_and_fix_python_files()
    
    print(f"\nFixed imports in {fixed_count} files!")

if __name__ == "__main__":
    main() 