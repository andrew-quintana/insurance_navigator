#!/usr/bin/env python3
"""
Comprehensive import test to catch missing dependencies
before deployment.
"""

import sys
import traceback

def test_import(module_name, package_name=None):
    """Test if a module can be imported."""
    try:
        __import__(module_name)
        print(f"✅ {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {module_name}: {e}")
        if package_name:
            print(f"   Install with: pip install {package_name}")
        return False
    except Exception as e:
        print(f"⚠️  {module_name}: {e}")
        return False

def main():
    print("🔍 COMPREHENSIVE IMPORT TEST")
    print("=" * 50)
    
    # Core application imports
    print("\n📦 Core Application Imports:")
    print("-" * 30)
    
    core_imports = [
        ("main", "main.py"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pydantic", "pydantic"),
        ("openai", "openai"),
        ("asyncpg", "asyncpg"),
        ("jwt", "PyJWT"),
        ("supabase", "supabase"),
        ("httpx", "httpx"),
        ("aiohttp", "aiohttp"),
        ("requests", "requests"),
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("scipy", "scipy"),
        ("sklearn", "scikit-learn"),
        ("sentence_transformers", "sentence-transformers"),  # Only available in testing environment
        ("langchain", "langchain"),
        ("llama_index", "llama-index"),
    ]
    
    missing_imports = []
    for module, package in core_imports:
        if not test_import(module, package):
            missing_imports.append((module, package))
    
    # Database and auth imports
    print("\n🔐 Database and Auth Imports:")
    print("-" * 30)
    
    db_imports = [
        ("db.services.auth_adapter", "auth_adapter"),
        ("core.database", "database"),
        ("api.upload_pipeline.database", "upload_pipeline_database"),
    ]
    
    for module, description in db_imports:
        if not test_import(module):
            missing_imports.append((module, "application module"))
    
    # RAG and AI imports
    print("\n🤖 RAG and AI Imports:")
    print("-" * 30)
    
    rag_imports = [
        ("agents.tooling.rag.core", "RAGTool"),
        ("agents.tooling.rag.observability", "RAGObservability"),
        ("agents.patient_navigator.strategy.workflow.llm_integration", "LLMIntegration"),
    ]
    
    for module, description in rag_imports:
        if not test_import(module):
            missing_imports.append((module, "application module"))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 IMPORT TEST SUMMARY")
    print("=" * 50)
    
    if missing_imports:
        print(f"❌ {len(missing_imports)} missing imports found:")
        for module, package in missing_imports:
            print(f"   - {module} (install: {package})")
        return False
    else:
        print("✅ All imports successful!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
