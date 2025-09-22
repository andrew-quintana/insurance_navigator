#!/usr/bin/env python3
"""
Simple Missing Dependencies Checker

This tool checks for missing dependencies by trying to import them
and seeing which ones fail.
"""

import sys
import subprocess
from pathlib import Path

def get_requirements_packages(requirements_file: str) -> set:
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

def test_import(module_name: str) -> bool:
    """Test if a module can be imported."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def main():
    """Check for missing dependencies."""
    print("🔍 Checking for missing dependencies...")
    
    # Get requirements packages
    requirements_file = "requirements-api.txt"
    req_packages = get_requirements_packages(requirements_file)
    print(f"📋 Found {len(req_packages)} packages in {requirements_file}")
    
    # Test critical imports that we know are used
    critical_imports = [
        'pydantic_settings',  # This was the missing one
        'fastapi',
        'uvicorn',
        'pydantic',
        'asyncpg',
        'sqlalchemy',
        'psycopg2',  # This might be psycopg2-binary
        'jose',
        'passlib',
        'cryptography',
        'aiohttp',
        'requests',
        'dotenv',
        'openai',
        'langchain',
        'langgraph',
        'anthropic',
        'supabase',
        'tenacity',
    ]
    
    missing = []
    for import_name in critical_imports:
        if not test_import(import_name):
            missing.append(import_name)
            print(f"❌ Missing: {import_name}")
        else:
            print(f"✅ Found: {import_name}")
    
    if missing:
        print(f"\n⚠️  Found {len(missing)} missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        return False
    else:
        print("\n🎉 All critical dependencies are available!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
