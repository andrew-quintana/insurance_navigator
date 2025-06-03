#!/usr/bin/env python3
"""
Fix broken import paths after agent reorganization.
Updates all import statements to match the actual file locations.
"""

import os
import re
import glob

# Mapping of correct import paths based on actual file locations
IMPORT_FIXES = {
    # Patient Navigator - moved to root
    r'from agents\.patient_navigator\.models\.navigator_models import': 'from agents.patient_navigator.navigator_models import',
    
    # Task Requirements - moved to root  
    r'from agents\.task_requirements\.models\.task_models import': 'from agents.task_requirements.task_models import',
    
    # Service Access Strategy - moved to root
    r'from agents\.service_access_strategy\.models\.strategy_models import': 'from agents.service_access_strategy.strategy_models import',
    
    # Chat Communicator - moved to root (and renamed)
    r'from agents\.chat_communicator\.models\.chat_models import': 'from agents.chat_communicator.chat_models import',
    
    # Prompt Security - still in models/ subdirectory (correct)
    # r'from agents\.prompt_security\.models\.security_models import': 'from agents.prompt_security.models.security_models import',
    
    # Regulatory - still in models/ subdirectory (correct)  
    # r'from agents\.regulatory\.models\.evaluation_models import': 'from agents.regulatory.models.evaluation_models import',
}

def fix_imports_in_file(filepath):
    """Fix imports in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        for old_pattern, new_import in IMPORT_FIXES.items():
            if re.search(old_pattern, content):
                content = re.sub(old_pattern, new_import, content)
                changes_made.append(f"  ✅ Fixed: {old_pattern} -> {new_import}")
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"📝 Updated: {filepath}")
            for change in changes_made:
                print(change)
            return True
        return False
        
    except Exception as e:
        print(f"❌ Error fixing {filepath}: {e}")
        return False

def main():
    """Fix all broken imports in the codebase."""
    print("🔧 Fixing broken imports after agent reorganization...")
    
    # Find all Python files in the agents directory and related areas
    patterns = [
        "agents/**/*.py",
        "graph/**/*.py", 
        "scripts/*.py",
        "tests/**/*.py"
    ]
    
    files_to_check = []
    for pattern in patterns:
        files_to_check.extend(glob.glob(pattern, recursive=True))
    
    files_fixed = 0
    total_files = len(files_to_check)
    
    print(f"🔍 Checking {total_files} Python files...")
    
    for filepath in files_to_check:
        if fix_imports_in_file(filepath):
            files_fixed += 1
    
    print(f"\n✅ Import fix complete!")
    print(f"📊 Files processed: {total_files}")
    print(f"📊 Files fixed: {files_fixed}")
    
    if files_fixed > 0:
        print(f"\n🎉 Fixed {files_fixed} files with broken imports!")
    else:
        print(f"\n💡 No broken imports found.")

if __name__ == "__main__":
    main() 