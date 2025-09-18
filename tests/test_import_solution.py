#!/usr/bin/env python3
"""
Test Import Solution for Insurance Navigator

This script demonstrates how to prevent "No module named 'agents'" errors
using the comprehensive import utilities and path management system.
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_old_way():
    """Test the old way that causes import errors"""
    print("Testing Old Way (causes import errors):")
    print("-" * 50)
    
    try:
        # This will fail if not run from project root
        from agents.tooling.rag.core import RAGTool
        print("✅ RAGTool imported successfully")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
    
    try:
        from agents.patient_navigator.information_retrieval import InformationRetrievalAgent
        print("✅ InformationRetrievalAgent imported successfully")
    except ImportError as e:
        print(f"❌ Import failed: {e}")


def test_new_way():
    """Test the new way using import utilities"""
    print("\nTesting New Way (using import utilities):")
    print("-" * 50)
    
    # Import the utilities
    from utils.import_utilities import (
        safe_import_rag_tool,
        safe_import_information_retrieval_agent,
        safe_import_information_retrieval_input,
        safe_import_information_retrieval_output,
        validate_agents_imports,
        get_import_status_report
    )
    
    # Test individual imports
    RAGTool = safe_import_rag_tool()
    if RAGTool:
        print("✅ RAGTool imported successfully")
    else:
        print("❌ RAGTool import failed")
    
    InformationRetrievalAgent = safe_import_information_retrieval_agent()
    if InformationRetrievalAgent:
        print("✅ InformationRetrievalAgent imported successfully")
    else:
        print("❌ InformationRetrievalAgent import failed")
    
    InformationRetrievalInput = safe_import_information_retrieval_input()
    if InformationRetrievalInput:
        print("✅ InformationRetrievalInput imported successfully")
    else:
        print("❌ InformationRetrievalInput import failed")
    
    InformationRetrievalOutput = safe_import_information_retrieval_output()
    if InformationRetrievalOutput:
        print("✅ InformationRetrievalOutput imported successfully")
    else:
        print("❌ InformationRetrievalOutput import failed")
    
    # Test comprehensive validation
    print("\nComprehensive Import Validation:")
    print("-" * 30)
    
    validation_results = validate_agents_imports()
    for module, success in validation_results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {module}")
    
    # Get detailed report
    report = get_import_status_report()
    print(f"\nImport Status Report:")
    print(f"  Total Imports: {report['total_imports']}")
    print(f"  Successful: {report['successful_imports']}")
    print(f"  Failed: {report['failed_imports']}")
    print(f"  Success Rate: {report['success_rate']:.2%}")
    
    if report['recommendations']:
        print(f"\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")


def test_path_manager():
    """Test the Python path manager"""
    print("\nTesting Python Path Manager:")
    print("-" * 50)
    
    from utils.python_path_manager import setup_python_path, validate_project_imports
    
    # Setup paths
    path_manager = setup_python_path()
    
    # Get path info
    path_info = path_manager.get_path_info()
    print(f"Project Root: {path_info['project_root']}")
    print(f"Current Working Directory: {path_info['current_working_dir']}")
    print(f"Python Path Count: {path_info['python_path_count']}")
    
    # Validate project imports
    validation = validate_project_imports()
    print(f"\nAll Critical Modules Available: {validation['all_critical_available']}")
    
    if validation['recommendations']:
        print(f"\nRecommendations:")
        for rec in validation['recommendations']:
            print(f"  - {rec}")


def test_rag_functionality():
    """Test RAG functionality with safe imports"""
    print("\nTesting RAG Functionality:")
    print("-" * 50)
    
    from utils.import_utilities import (
        safe_import_rag_tool,
        safe_import_retrieval_config,
        safe_import_information_retrieval_agent,
        safe_import_information_retrieval_input
    )
    
    try:
        # Import required classes
        RAGTool = safe_import_rag_tool()
        RetrievalConfig = safe_import_retrieval_config()
        InformationRetrievalAgent = safe_import_information_retrieval_agent()
        InformationRetrievalInput = safe_import_information_retrieval_input()
        
        if not all([RAGTool, RetrievalConfig, InformationRetrievalAgent, InformationRetrievalInput]):
            print("❌ Some required classes could not be imported")
            return
        
        print("✅ All required classes imported successfully")
        
        # Test RAG tool initialization
        user_id = "test-user-123"
        config = RetrievalConfig(similarity_threshold=0.1, max_chunks=5)
        rag_tool = RAGTool(user_id, config)
        print("✅ RAGTool initialized successfully")
        
        # Test Information Retrieval Agent initialization
        agent = InformationRetrievalAgent()
        print("✅ InformationRetrievalAgent initialized successfully")
        
        print("✅ RAG functionality test completed successfully")
        
    except Exception as e:
        print(f"❌ RAG functionality test failed: {e}")
        import traceback
        traceback.print_exc()


def test_worker_functionality():
    """Test worker functionality with safe imports"""
    print("\nTesting Worker Functionality:")
    print("-" * 50)
    
    from utils.import_utilities import (
        safe_import_worker_config,
        safe_import_enhanced_service_client,
        safe_import_error_handler
    )
    
    try:
        # Import required classes
        WorkerConfig = safe_import_worker_config()
        EnhancedServiceClient = safe_import_enhanced_service_client()
        WorkerErrorHandler = safe_import_error_handler()
        
        if not all([WorkerConfig, EnhancedServiceClient, WorkerErrorHandler]):
            print("❌ Some required worker classes could not be imported")
            return
        
        print("✅ All required worker classes imported successfully")
        
        # Test error handler initialization
        error_handler = WorkerErrorHandler("test_worker")
        print("✅ WorkerErrorHandler initialized successfully")
        
        print("✅ Worker functionality test completed successfully")
        
    except Exception as e:
        print(f"❌ Worker functionality test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main test function"""
    print("Insurance Navigator Import Solution Test")
    print("=" * 60)
    
    # Test old way (will likely fail)
    test_old_way()
    
    # Test new way (should work)
    test_new_way()
    
    # Test path manager
    test_path_manager()
    
    # Test specific functionality
    test_rag_functionality()
    test_worker_functionality()
    
    print("\n" + "=" * 60)
    print("Import Solution Test Completed")
    print("=" * 60)


if __name__ == "__main__":
    main()
