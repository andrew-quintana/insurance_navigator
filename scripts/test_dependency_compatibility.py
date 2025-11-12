#!/usr/bin/env python3
"""
Dependency Compatibility Test

Tests that all critical imports work correctly, especially after dependency updates.
This helps catch import errors before deployment.

Usage:
    python scripts/test_dependency_compatibility.py
"""

import sys
import importlib
from typing import List, Tuple

def test_import(module_name: str, item_name: str = None) -> Tuple[bool, str]:
    """
    Test importing a module or specific item from a module.
    
    Args:
        module_name: Name of the module to import
        item_name: Optional specific item to import from the module
        
    Returns:
        Tuple of (success: bool, error_message: str)
    """
    try:
        module = importlib.import_module(module_name)
        if item_name:
            if not hasattr(module, item_name):
                return False, f"Module {module_name} does not have attribute {item_name}"
            getattr(module, item_name)
        return True, "OK"
    except ImportError as e:
        return False, f"ImportError: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_pydantic_version() -> Tuple[bool, str]:
    """Test that pydantic version supports with_config decorator."""
    try:
        import pydantic
        version = pydantic.__version__
        major, minor = map(int, version.split('.')[:2])
        
        if major > 2 or (major == 2 and minor >= 6):
            # Test that with_config is available
            if hasattr(pydantic, 'with_config'):
                return True, f"OK (version {version}, with_config available)"
            else:
                return False, f"Version {version} should have with_config but it's missing"
        else:
            return False, f"Version {version} is too old (need >=2.6.0)"
    except Exception as e:
        return False, f"Error checking pydantic version: {str(e)}"

def test_supabase_imports() -> Tuple[bool, str]:
    """Test that supabase and supabase_auth can be imported."""
    try:
        # Test supabase main module
        import supabase
        # Test supabase_auth (this is where the with_config import happens)
        from supabase_auth import errors
        return True, "OK"
    except ImportError as e:
        return False, f"ImportError: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_critical_application_imports() -> Tuple[bool, str]:
    """Test that critical application modules can be imported."""
    critical_imports = [
        ('config.environment_loader', None),
        ('config.configuration_manager', None),
        ('config.database', None),
        ('db.services.auth_adapter', None),
        ('db.services.supabase_auth_service', None),
    ]
    
    failures = []
    for module_name, item_name in critical_imports:
        success, message = test_import(module_name, item_name)
        if not success:
            failures.append(f"  - {module_name}: {message}")
    
    if failures:
        return False, "\n".join(failures)
    return True, "OK"

def main():
    """Run all dependency compatibility tests."""
    print("=" * 70)
    print("Dependency Compatibility Test")
    print("=" * 70)
    print()
    
    tests = [
        ("Pydantic Version Check", test_pydantic_version),
        ("Supabase Imports", test_supabase_imports),
        ("Critical Application Imports", test_critical_application_imports),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Testing: {test_name}...", end=" ")
        success, message = test_func()
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ FAILED")
            print(f"  {message}")
        results.append((test_name, success, message))
        print()
    
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, message in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Dependencies are compatible.")
        return 0
    else:
        print("✗ Some tests failed! Please fix dependency issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

