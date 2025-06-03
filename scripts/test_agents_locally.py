#!/usr/bin/env python3
"""
Test script to verify all agents and orchestrator work correctly.
Runs comprehensive tests on each component to catch issues before deployment.
"""

import os
import sys
import traceback
import asyncio
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_agent_imports():
    """Test that all agents can be imported successfully."""
    print("🔍 Testing agent imports...")
    
    tests = [
        ("AgentOrchestrator", "from graph.agent_orchestrator import AgentOrchestrator"),
        ("PromptSecurityAgent", "from agents.prompt_security.prompt_security import PromptSecurityAgent"),
        ("PatientNavigatorAgent", "from agents.patient_navigator.patient_navigator import PatientNavigatorAgent"),
        ("TaskRequirementsAgent", "from agents.task_requirements.task_requirements import TaskRequirementsAgent"),
        ("ServiceAccessStrategyAgent", "from agents.service_access_strategy.service_access_strategy import ServiceAccessStrategyAgent"),
        ("ChatCommunicatorAgent", "from agents.chat_communicator.chat_communicator import ChatCommunicatorAgent"),
        ("RegulatoryAgent", "from agents.regulatory.regulatory import RegulatoryAgent"),
    ]
    
    results = {}
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"  ✅ {name}: Import successful")
            results[name] = {"status": "success", "error": None}
        except Exception as e:
            print(f"  ❌ {name}: Import failed - {str(e)}")
            results[name] = {"status": "failed", "error": str(e)}
    
    return results

def test_agent_initialization():
    """Test that all agents can be initialized."""
    print("\n🔧 Testing agent initialization...")
    
    results = {}
    
    # Test PromptSecurityAgent
    try:
        from agents.prompt_security.prompt_security import PromptSecurityAgent
        agent = PromptSecurityAgent(bypass_security=True)
        print(f"  ✅ PromptSecurityAgent: Initialized successfully")
        results["PromptSecurityAgent"] = {"status": "success", "error": None}
    except Exception as e:
        print(f"  ❌ PromptSecurityAgent: Failed - {str(e)}")
        results["PromptSecurityAgent"] = {"status": "failed", "error": str(e)}
    
    # Test PatientNavigatorAgent
    try:
        from agents.patient_navigator.patient_navigator import PatientNavigatorAgent
        from utils.config_manager import ConfigManager
        config = ConfigManager()
        agent = PatientNavigatorAgent(config_manager=config)
        print(f"  ✅ PatientNavigatorAgent: Initialized successfully")
        results["PatientNavigatorAgent"] = {"status": "success", "error": None}
    except Exception as e:
        print(f"  ❌ PatientNavigatorAgent: Failed - {str(e)}")
        results["PatientNavigatorAgent"] = {"status": "failed", "error": str(e)}
    
    # Test TaskRequirementsAgent
    try:
        from agents.task_requirements.task_requirements import TaskRequirementsAgent
        agent = TaskRequirementsAgent(config_manager=config)
        print(f"  ✅ TaskRequirementsAgent: Initialized successfully")
        results["TaskRequirementsAgent"] = {"status": "success", "error": None}
    except Exception as e:
        print(f"  ❌ TaskRequirementsAgent: Failed - {str(e)}")
        results["TaskRequirementsAgent"] = {"status": "failed", "error": str(e)}
    
    # Test ServiceAccessStrategyAgent
    try:
        from agents.service_access_strategy.service_access_strategy import ServiceAccessStrategyAgent
        agent = ServiceAccessStrategyAgent(config_manager=config)
        print(f"  ✅ ServiceAccessStrategyAgent: Initialized successfully")
        results["ServiceAccessStrategyAgent"] = {"status": "success", "error": None}
    except Exception as e:
        print(f"  ❌ ServiceAccessStrategyAgent: Failed - {str(e)}")
        results["ServiceAccessStrategyAgent"] = {"status": "failed", "error": str(e)}
    
    # Test ChatCommunicatorAgent
    try:
        from agents.chat_communicator.chat_communicator import ChatCommunicatorAgent
        agent = ChatCommunicatorAgent(config_manager=config, use_mock=True)
        print(f"  ✅ ChatCommunicatorAgent: Initialized successfully")
        results["ChatCommunicatorAgent"] = {"status": "success", "error": None}
    except Exception as e:
        print(f"  ❌ ChatCommunicatorAgent: Failed - {str(e)}")
        results["ChatCommunicatorAgent"] = {"status": "failed", "error": str(e)}
    
    # Test RegulatoryAgent
    try:
        from agents.regulatory.regulatory import RegulatoryAgent
        agent = RegulatoryAgent()
        print(f"  ✅ RegulatoryAgent: Initialized successfully")
        results["RegulatoryAgent"] = {"status": "success", "error": None}
    except Exception as e:
        print(f"  ❌ RegulatoryAgent: Failed - {str(e)}")
        results["RegulatoryAgent"] = {"status": "failed", "error": str(e)}
    
    return results

def test_orchestrator():
    """Test AgentOrchestrator initialization and basic functionality."""
    print("\n🎯 Testing AgentOrchestrator...")
    
    try:
        from graph.agent_orchestrator import AgentOrchestrator
        
        # Test initialization
        orchestrator = AgentOrchestrator(bypass_security=True)
        print(f"  ✅ AgentOrchestrator: Initialized successfully")
        
        # Test workflow determination
        test_messages = [
            "I need help finding a cardiologist",
            "What does Medicare cover?",
            "I need an X-ray, where can I get one?"
        ]
        
        for msg in test_messages:
            workflow_type = orchestrator._determine_workflow_type(msg)
            print(f"  📝 Message: '{msg}' → Workflow: {workflow_type}")
        
        return {"status": "success", "error": None}
        
    except Exception as e:
        print(f"  ❌ AgentOrchestrator: Failed - {str(e)}")
        print(f"  📋 Full traceback:")
        traceback.print_exc()
        return {"status": "failed", "error": str(e)}

async def test_simple_workflow():
    """Test a simple end-to-end workflow."""
    print("\n🚀 Testing simple workflow...")
    
    try:
        from graph.agent_orchestrator import AgentOrchestrator
        
        orchestrator = AgentOrchestrator(bypass_security=True)
        
        # Test a simple message
        test_message = "I need help finding a doctor in my area"
        user_id = "test_user_123"
        conversation_id = "test_conv_456"
        
        print(f"  📤 Testing message: '{test_message}'")
        
        # Process the message
        result = await orchestrator.process_message(
            message=test_message,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        print(f"  ✅ Workflow completed successfully!")
        print(f"  📊 Response length: {len(result.get('text', ''))} characters")
        print(f"  📊 Workflow type: {result.get('workflow_type', 'unknown')}")
        print(f"  📊 Metadata keys: {list(result.get('metadata', {}).keys())}")
        
        # Show a preview of the response
        response_text = result.get('text', '')
        if response_text:
            preview = response_text[:200] + "..." if len(response_text) > 200 else response_text
            print(f"  💬 Response preview: {preview}")
        
        return {"status": "success", "error": None, "result": result}
        
    except Exception as e:
        print(f"  ❌ Workflow test failed: {str(e)}")
        print(f"  📋 Full traceback:")
        traceback.print_exc()
        return {"status": "failed", "error": str(e)}

def print_summary(results):
    """Print a summary of all test results."""
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for category, tests in results.items():
        print(f"\n🔹 {category.upper()}:")
        
        if isinstance(tests, dict) and "status" in tests:
            # Single test result
            total_tests += 1
            if tests["status"] == "success":
                passed_tests += 1
                print(f"  ✅ Passed")
            else:
                failed_tests.append(f"{category}: {tests['error']}")
                print(f"  ❌ Failed: {tests['error']}")
        else:
            # Multiple test results
            for test_name, test_result in tests.items():
                total_tests += 1
                if test_result["status"] == "success":
                    passed_tests += 1
                    print(f"  ✅ {test_name}: Passed")
                else:
                    failed_tests.append(f"{test_name}: {test_result['error']}")
                    print(f"  ❌ {test_name}: Failed - {test_result['error']}")
    
    print(f"\n📈 OVERALL RESULTS:")
    print(f"  Total tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {len(failed_tests)}")
    print(f"  Success rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
    
    if failed_tests:
        print(f"\n❌ FAILURES REQUIRING RCA:")
        for i, failure in enumerate(failed_tests, 1):
            print(f"  {i}. {failure}")
    else:
        print(f"\n🎉 ALL TESTS PASSED! Ready for deployment! 🚀")
    
    return len(failed_tests) == 0

async def main():
    """Run all tests."""
    print("🧪 COMPREHENSIVE AGENT AND ORCHESTRATOR TEST")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # Test 1: Agent Imports
    results["import_tests"] = test_agent_imports()
    
    # Test 2: Agent Initialization
    results["initialization_tests"] = test_agent_initialization()
    
    # Test 3: Orchestrator
    results["orchestrator_test"] = test_orchestrator()
    
    # Test 4: Simple Workflow (async)
    results["workflow_test"] = await test_simple_workflow()
    
    # Print summary
    all_passed = print_summary(results)
    
    if not all_passed:
        print(f"\n🔧 Some tests failed. Please review the failures above for RCA.")
        print(f"💡 Common issues to check:")
        print(f"  - Missing dependencies or API keys")
        print(f"  - Configuration file issues")
        print(f"  - Database connectivity problems")
        print(f"  - Import path issues")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test script crashed: {str(e)}")
        traceback.print_exc()
        sys.exit(1) 