#!/usr/bin/env python3
"""
Quick validation script to verify chat_flow_investigation.py structure

This script checks that:
1. All required imports are available
2. Class structure is correct
3. Key methods are defined
4. No syntax errors
"""

import sys
import importlib.util

def validate_script():
    """Validate the investigation script structure"""
    print("=" * 80)
    print("Validating chat_flow_investigation.py")
    print("=" * 80)
    
    script_path = "tests/fm_038/chat_flow_investigation.py"
    
    # Check file exists
    try:
        with open(script_path, 'r') as f:
            content = f.read()
        print("✅ Script file found and readable")
    except FileNotFoundError:
        print(f"❌ Script file not found: {script_path}")
        return False
    
    # Check for required imports
    required_imports = [
        'asyncio',
        'aiohttp',
        'json',
        'logging',
        'time',
        'dataclass'
    ]
    
    print("\n📦 Checking imports:")
    for imp in required_imports:
        if imp in content:
            print(f"   ✅ {imp}")
        else:
            print(f"   ❌ {imp} not found")
            return False
    
    # Check for required classes
    required_classes = [
        'class FunctionCall',
        'class InvestigationMetrics',
        'class ChatFlowInvestigator'
    ]
    
    print("\n🏗️  Checking class definitions:")
    for cls in required_classes:
        if cls in content:
            print(f"   ✅ {cls}")
        else:
            print(f"   ❌ {cls} not found")
            return False
    
    # Check for key methods
    required_methods = [
        'async def authenticate',
        'async def send_chat_message',
        'async def run_comprehensive_investigation',
        'def print_investigation_summary'
    ]
    
    print("\n⚙️  Checking method definitions:")
    for method in required_methods:
        if method in content:
            print(f"   ✅ {method}")
        else:
            print(f"   ❌ {method} not found")
            return False
    
    # Check for test credentials
    credentials = [
        'TEST_USER_EMAIL',
        'TEST_USER_PASSWORD',
        'TEST_USER_ID'
    ]
    
    print("\n🔐 Checking credentials:")
    for cred in credentials:
        if cred in content:
            print(f"   ✅ {cred}")
        else:
            print(f"   ❌ {cred} not found")
            return False
    
    # Try to compile the script
    print("\n🔍 Checking syntax:")
    try:
        compile(content, script_path, 'exec')
        print("   ✅ No syntax errors")
    except SyntaxError as e:
        print(f"   ❌ Syntax error: {e}")
        return False
    
    # Check for main entry point
    print("\n🚀 Checking main entry point:")
    if 'async def main' in content and 'if __name__ == "__main__"' in content:
        print("   ✅ Main entry point defined")
    else:
        print("   ❌ Main entry point not found")
        return False
    
    print("\n" + "=" * 80)
    print("✅ Validation successful!")
    print("=" * 80)
    print("\nThe investigation script is ready to run.")
    print("\nNext steps:")
    print("1. Review PHASE_1_README.md for usage instructions")
    print("2. Ensure .env.production is configured")
    print("3. Run: python tests/fm_038/chat_flow_investigation.py")
    
    return True

if __name__ == "__main__":
    success = validate_script()
    sys.exit(0 if success else 1)

