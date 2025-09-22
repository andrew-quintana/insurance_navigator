#!/usr/bin/env python3
"""
Comprehensive Dependency Detection Tool

This tool scans all Python files in the project to detect missing dependencies
that might not be caught by simple import tests.
"""

import os
import sys
import ast
import importlib
from pathlib import Path
from typing import Set, Dict, List, Tuple
import subprocess

def find_python_files(directory: str) -> List[Path]:
    """Find all Python files in the directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', '.pytest_cache', 'venv', 'env'}]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    return python_files

def extract_imports(file_path: Path) -> Set[str]:
    """Extract all import statements from a Python file."""
    imports = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    
    except Exception as e:
        print(f"⚠️  Error parsing {file_path}: {e}")
    
    return imports

def get_installed_packages() -> Set[str]:
    """Get list of currently installed packages."""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True)
        packages = set()
        for line in result.stdout.split('\n')[2:]:  # Skip header lines
            if line.strip():
                package_name = line.split()[0].lower().replace('_', '-')
                packages.add(package_name)
        return packages
    except Exception as e:
        print(f"⚠️  Error getting installed packages: {e}")
        return set()

def get_requirements_packages(requirements_file: str) -> Set[str]:
    """Get packages from requirements file."""
    packages = set()
    try:
        with open(requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    # Extract package name (before ==, >=, etc.)
                    package_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].split('!=')[0]
                    packages.add(package_name.lower().replace('_', '-'))
    except FileNotFoundError:
        print(f"⚠️  Requirements file not found: {requirements_file}")
    return packages

def map_import_to_package(import_name: str) -> str:
    """Map import name to package name."""
    # Common mappings
    mappings = {
        'sklearn': 'scikit-learn',
        'PIL': 'Pillow',
        'cv2': 'opencv-python',
        'yaml': 'PyYAML',
        'dateutil': 'python-dateutil',
        'dotenv': 'python-dotenv',
        'jose': 'python-jose',
        'multipart': 'python-multipart',
        'pydantic_settings': 'pydantic-settings',
        'psycopg2': 'psycopg2-binary',
        'bs4': 'beautifulsoup4',
        'requests_toolbelt': 'requests-toolbelt',
    }
    
    return mappings.get(import_name, import_name)

def detect_missing_dependencies(project_dir: str, requirements_file: str) -> Dict[str, List[str]]:
    """Detect missing dependencies by scanning all Python files."""
    print(f"🔍 Scanning Python files in {project_dir}")
    print(f"📋 Checking against requirements file: {requirements_file}")
    print("=" * 60)
    
    # Find all Python files
    python_files = find_python_files(project_dir)
    print(f"Found {len(python_files)} Python files")
    
    # Get requirements packages
    requirements_packages = get_requirements_packages(requirements_file)
    print(f"Found {len(requirements_packages)} packages in requirements file")
    
    # Get installed packages
    installed_packages = get_installed_packages()
    print(f"Found {len(installed_packages)} installed packages")
    
    # Collect all imports
    all_imports = set()
    file_imports = {}
    
    for file_path in python_files:
        imports = extract_imports(file_path)
        all_imports.update(imports)
        file_imports[str(file_path)] = imports
    
    print(f"Found {len(all_imports)} unique import statements")
    
    # Check for missing dependencies
    missing_dependencies = []
    potentially_missing = []
    
    for import_name in all_imports:
        # Skip standard library modules
        if import_name in sys.builtin_module_names:
            continue
        
        # Skip local modules (assume they start with project-specific prefixes)
        if import_name.startswith(('api', 'core', 'db', 'agents', 'config', 'utils', 'backend')):
            continue
        
        # Map import name to package name
        package_name = map_import_to_package(import_name)
        
        # Check if package is in requirements
        if package_name not in requirements_packages:
            # Check if it's installed (might be a transitive dependency)
            if package_name not in installed_packages:
                missing_dependencies.append((import_name, package_name))
            else:
                potentially_missing.append((import_name, package_name))
    
    # Find files that use missing dependencies
    missing_usage = {}
    for missing_import, missing_package in missing_dependencies:
        usage_files = []
        for file_path, imports in file_imports.items():
            if missing_import in imports:
                usage_files.append(file_path)
        missing_usage[missing_import] = usage_files
    
    return {
        'missing_dependencies': missing_dependencies,
        'potentially_missing': potentially_missing,
        'missing_usage': missing_usage,
        'all_imports': all_imports,
        'requirements_packages': requirements_packages
    }

def main():
    """Main function."""
    project_dir = "/Users/aq_home/1Projects/accessa/insurance_navigator"
    requirements_file = "requirements-api.txt"
    
    print("🚀 COMPREHENSIVE DEPENDENCY DETECTION")
    print("=" * 60)
    
    results = detect_missing_dependencies(project_dir, requirements_file)
    
    print("\n📊 DEPENDENCY ANALYSIS RESULTS")
    print("=" * 60)
    
    if results['missing_dependencies']:
        print("❌ MISSING DEPENDENCIES:")
        for import_name, package_name in results['missing_dependencies']:
            print(f"  • {import_name} -> {package_name}")
            if import_name in results['missing_usage']:
                print(f"    Used in: {len(results['missing_usage'][import_name])} files")
                for file_path in results['missing_usage'][import_name][:3]:  # Show first 3 files
                    print(f"      - {file_path}")
                if len(results['missing_usage'][import_name]) > 3:
                    print(f"      ... and {len(results['missing_usage'][import_name]) - 3} more files")
        print()
    else:
        print("✅ No missing dependencies found!")
    
    if results['potentially_missing']:
        print("⚠️  POTENTIALLY MISSING (installed but not in requirements):")
        for import_name, package_name in results['potentially_missing']:
            print(f"  • {import_name} -> {package_name}")
        print()
    
    print(f"📈 SUMMARY:")
    print(f"  • Total imports found: {len(results['all_imports'])}")
    print(f"  • Missing dependencies: {len(results['missing_dependencies'])}")
    print(f"  • Potentially missing: {len(results['potentially_missing'])}")
    print(f"  • Requirements packages: {len(results['requirements_packages'])}")
    
    if results['missing_dependencies']:
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("1. Add missing dependencies to requirements file:")
        for import_name, package_name in results['missing_dependencies']:
            print(f"   {package_name}>=1.0.0")
        print("\n2. Test the updated requirements file")
        print("3. Re-run this detection tool to verify")
        
        return False
    else:
        print("\n🎉 All dependencies are properly declared!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
