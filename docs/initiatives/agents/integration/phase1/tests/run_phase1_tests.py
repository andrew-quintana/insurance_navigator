#!/usr/bin/env python3
"""
Phase 1 Test Runner
Runs Phase 1 integration tests with proper environment setup.

This script:
1. Sets up the environment for real LLM/embedding services
2. Runs the simple integration test
3. Optionally runs the comprehensive test
4. Generates a test report
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
sys.path.append(project_root)

def setup_environment():
    """Set up environment for testing with real services."""
    print("🔧 Setting up environment for Phase 1 testing...")
    
    # Set environment variables to ensure real services are used
    os.environ["USE_MOCK_SERVICES"] = "false"
    os.environ["MOCK_LLM"] = "false"
    os.environ["MOCK_EMBEDDINGS"] = "false"
    
    # Ensure we're in the project root
    os.chdir(project_root)
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Check if required files exist
    required_files = [
        "main.py",
        "agents/patient_navigator/chat_interface.py",
        "examples/test_insurance_document.pdf"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Required file not found: {file_path}")
            return False
        else:
            print(f"✅ Found: {file_path}")
    
    print("✅ Environment setup complete")
    return True

async def run_simple_test():
    """Run the simple integration test."""
    print("\n🧪 Running Simple Integration Test...")
    print("=" * 50)
    
    try:
        from phase1_simple_integration_test import test_basic_chat_functionality
        success = await test_basic_chat_functionality()
        return success
    except Exception as e:
        print(f"❌ Simple test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def run_comprehensive_test():
    """Run the comprehensive integration test."""
    print("\n🧪 Running Comprehensive Integration Test...")
    print("=" * 50)
    
    try:
        from phase1_comprehensive_integration_test import Phase1IntegrationTester
        
        tester = Phase1IntegrationTester()
        report = await tester.run_comprehensive_tests()
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"phase1_comprehensive_results_{timestamp}.json"
        
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📊 Comprehensive test report saved to: {report_filename}")
        
        return report.get("phase1_integration_test_report", {}).get("overall_status") == "PASSED"
        
    except Exception as e:
        print(f"❌ Comprehensive test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test runner."""
    print("🚀 Phase 1 Integration Test Runner")
    print("=" * 60)
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed")
        return False
    
    # Run simple test
    simple_success = await run_simple_test()
    
    # Ask user if they want to run comprehensive test
    print(f"\n📊 Simple test result: {'PASSED' if simple_success else 'FAILED'}")
    
    if simple_success:
        print("\n🎯 Simple test passed! Would you like to run the comprehensive test?")
        print("(This will take longer but provides detailed analysis)")
        
        # For automated runs, skip the comprehensive test
        # In interactive mode, you could add user input here
        run_comprehensive = False  # Set to True to run comprehensive test
        
        if run_comprehensive:
            comprehensive_success = await run_comprehensive_test()
            print(f"\n📊 Comprehensive test result: {'PASSED' if comprehensive_success else 'FAILED'}")
            
            overall_success = simple_success and comprehensive_success
        else:
            print("⏭️ Skipping comprehensive test (set run_comprehensive=True to enable)")
            overall_success = simple_success
    else:
        print("❌ Simple test failed, skipping comprehensive test")
        overall_success = False
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 PHASE 1 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"🎯 Overall Status: {'PASSED' if overall_success else 'FAILED'}")
    print(f"✅ Simple Test: {'PASSED' if simple_success else 'FAILED'}")
    
    if overall_success:
        print("\n🎉 Phase 1 Integration Testing Complete!")
        print("✅ Chat interface is working with real services")
        print("✅ Full responses are generated (not truncated)")
        print("✅ Ready for Phase 2 testing")
    else:
        print("\n💥 Phase 1 Integration Testing Failed!")
        print("❌ Please check the error messages above")
        print("❌ Fix issues before proceeding to Phase 2")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
