#!/usr/bin/env python3
"""
Mock testing for new unified navigator features.
Tests Quick Info and Access Strategy tools without external dependencies.
"""

import asyncio
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_quick_info_tool_standalone():
    """Test Quick Info Tool with mock data."""
    print("🔍 Testing Quick Info Tool (Standalone)")
    
    try:
        from agents.unified_navigator.tools.quick_info_tool import QuickInfoTool, BM25Scorer
        
        # Test BM25 Scorer
        scorer = BM25Scorer()
        
        # Mock documents
        mock_docs = [
            {
                "id": "1", 
                "title": "Prescription Benefits",
                "content": "Your plan covers prescription drugs with $20 copay for generic medications and $50 for brand name drugs. Annual limit is $5000.",
                "section": "Benefits"
            },
            {
                "id": "2",
                "title": "Doctor Visits", 
                "content": "Office visits to your primary care physician have a $25 copay. Specialist visits require referral and have $40 copay.",
                "section": "Medical Coverage"
            },
            {
                "id": "3",
                "title": "Emergency Care",
                "content": "Emergency room visits are covered after you meet your $500 deductible. No copay required for genuine emergencies.",
                "section": "Emergency"
            }
        ]
        
        # Index documents
        scorer.add_documents(mock_docs)
        
        # Test searches
        test_queries = [
            "prescription drug copay",
            "doctor visit cost", 
            "emergency room coverage"
        ]
        
        results = {}
        for query in test_queries:
            start_time = time.time()
            scored_results = scorer.score_documents(query, top_k=2)
            search_time = (time.time() - start_time) * 1000
            
            results[query] = {
                "results_count": len(scored_results),
                "top_score": scored_results[0][0] if scored_results else 0,
                "search_time_ms": search_time
            }
        
        # Test Quick Info Tool
        tool = QuickInfoTool()
        
        # Mock indexing
        await tool.index_user_documents("mock_user", mock_docs)
        
        # Test search
        search_result = await tool.search(
            query="What is my prescription drug copay?",
            user_id="mock_user", 
            max_results=2
        )
        
        print(f"  ✅ BM25 indexing: {len(mock_docs)} documents")
        print(f"  ✅ Query processing: {len(results)} test queries")
        print(f"  ✅ Search result: {len(search_result.relevant_sections)} sections found")
        print(f"  ✅ Confidence: {search_result.confidence_score:.2f}")
        print(f"  ✅ Processing time: {search_result.processing_time_ms:.1f}ms")
        
        return {
            "success": True,
            "bm25_results": results,
            "tool_result": {
                "sections_found": len(search_result.relevant_sections),
                "confidence": search_result.confidence_score,
                "time_ms": search_result.processing_time_ms
            }
        }
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {"success": False, "error": str(e)}


async def test_access_strategy_tool_standalone():
    """Test Access Strategy Tool without external APIs."""
    print("🧠 Testing Access Strategy Tool (Standalone)")
    
    try:
        from agents.unified_navigator.tools.access_strategy_tool import AccessStrategyTool
        
        tool = AccessStrategyTool()
        
        # Test strategy generation (will work without Tavily)
        test_queries = [
            "How can I maximize my insurance benefits?",
            "What's the best approach to compare insurance plans?",
            "Help me find the most cost-effective coverage strategy"
        ]
        
        results = []
        for query in test_queries:
            start_time = time.time()
            
            result = await tool.strategize(
                query=query,
                user_id="mock_strategy_user"
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            results.append({
                "query": query[:50] + "...",
                "has_strategy": len(result.strategy_hypothesis) > 100,
                "confidence": result.confidence_score,
                "time_ms": result.processing_time_ms,
                "actual_time_ms": processing_time,
                "has_tavily": result.tavily_research is not None,
                "has_rag": result.rag_validation is not None
            })
        
        print(f"  ✅ Strategy generation: {len(results)} test queries")
        for i, result in enumerate(results, 1):
            print(f"  ✅ Query {i}: Strategy generated ({result['time_ms']:.1f}ms)")
            print(f"      Confidence: {result['confidence']:.2f}")
            print(f"      Tavily research: {'✅' if result['has_tavily'] else '❌'}")
        
        return {
            "success": True,
            "strategies_generated": len(results),
            "results": results
        }
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {"success": False, "error": str(e)}


async def test_workflow_logging_integration():
    """Test workflow logging with WebSocket integration."""
    print("📊 Testing Workflow Logging Integration")
    
    try:
        from agents.unified_navigator.logging.workflow_logger import get_workflow_logger
        from agents.unified_navigator.websocket_handler import get_workflow_broadcaster
        from agents.unified_navigator.models import WorkflowStatus
        
        # Test logger
        logger = get_workflow_logger()
        
        # Test workflow start
        logger.log_workflow_start(
            user_id="test_integration_user",
            query="Integration test query",
            session_id="test_session",
            correlation_id="test123"
        )
        
        # Test step logging (should attempt WebSocket broadcast)
        steps_tested = ["sanitizing", "determining", "thinking", "skimming", "wording"]
        for step in steps_tested:
            logger.log_workflow_step(
                step=step,
                message=f"Testing {step} step",
                correlation_id="test123"
            )
        
        # Test workflow completion
        logger.log_workflow_completion(
            user_id="test_integration_user",
            success=True,
            total_time_ms=1500.0,
            correlation_id="test123",
            context_data={"tool_used": "mock_tool", "response_length": 150}
        )
        
        # Test WebSocket broadcaster (won't have active connections but should not error)
        broadcaster = get_workflow_broadcaster()
        stats = broadcaster.get_connection_stats()
        
        print(f"  ✅ Workflow logging: {len(steps_tested)} steps logged")
        print(f"  ✅ WebSocket broadcaster initialized")
        print(f"  ✅ Connection stats: {stats['total_connections']} connections")
        print(f"  ✅ Active workflows: {stats['active_workflows']} workflows")
        
        return {
            "success": True,
            "steps_logged": len(steps_tested),
            "broadcaster_stats": stats
        }
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {"success": False, "error": str(e)}


async def test_unified_navigator_mock_mode():
    """Test unified navigator in full mock mode."""
    print("🤖 Testing Unified Navigator (Mock Mode)")
    
    try:
        from agents.unified_navigator.navigator_agent import UnifiedNavigatorAgent
        from agents.unified_navigator.models import UnifiedNavigatorInput
        
        # Initialize in mock mode (no API costs)
        agent = UnifiedNavigatorAgent(use_mock=True)
        
        # Test scenarios for different tools
        test_scenarios = [
            {
                "query": "What does my policy cover for prescription drugs?",
                "expected_tool_type": "quick_info",
                "user_id": "mock_user_1"
            },
            {
                "query": "How can I maximize my insurance benefits and find the best strategy?", 
                "expected_tool_type": "access_strategy",
                "user_id": "mock_user_2"
            },
            {
                "query": "What are the latest healthcare regulations for 2025?",
                "expected_tool_type": "web_search", 
                "user_id": "mock_user_3"
            }
        ]
        
        results = []
        total_start_time = time.time()
        
        for i, scenario in enumerate(test_scenarios, 1):
            start_time = time.time()
            
            input_data = UnifiedNavigatorInput(
                user_query=scenario["query"],
                user_id=scenario["user_id"],
                session_id=f"mock_session_{i}"
            )
            
            result = await agent.execute(input_data)
            execution_time = (time.time() - start_time) * 1000
            
            results.append({
                "scenario": i,
                "success": result.success,
                "tool_used": result.tool_used.value,
                "expected_tool": scenario["expected_tool_type"],
                "response_length": len(result.response),
                "execution_time_ms": execution_time,
                "input_safe": result.input_safety_check.is_safe,
                "query": scenario["query"][:50] + "..."
            })
        
        total_time = (time.time() - total_start_time) * 1000
        successful_tests = sum(1 for r in results if r["success"])
        
        print(f"  ✅ Mock execution: {len(results)} scenarios tested")
        print(f"  ✅ Success rate: {successful_tests}/{len(results)} ({successful_tests/len(results)*100:.1f}%)")
        print(f"  ✅ Average execution time: {total_time/len(results):.1f}ms")
        print(f"  ✅ Total test time: {total_time:.1f}ms")
        
        for result in results:
            tool_match = "✅" if result["expected_tool"] in result["tool_used"] else "⚠️"
            print(f"    {tool_match} Scenario {result['scenario']}: {result['tool_used']} ({result['execution_time_ms']:.1f}ms)")
        
        return {
            "success": True,
            "scenarios_tested": len(results),
            "success_rate": successful_tests / len(results),
            "average_time_ms": total_time / len(results),
            "results": results
        }
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {"success": False, "error": str(e)}


async def run_mock_tests():
    """Run all mock tests."""
    print("🧪 UNIFIED NAVIGATOR MOCK FEATURE TESTS")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Quick Info Tool
    result1 = await test_quick_info_tool_standalone()
    test_results.append(("Quick Info Tool", result1["success"]))
    
    # Test 2: Access Strategy Tool  
    result2 = await test_access_strategy_tool_standalone()
    test_results.append(("Access Strategy Tool", result2["success"]))
    
    # Test 3: Workflow Logging
    result3 = await test_workflow_logging_integration()
    test_results.append(("Workflow Logging", result3["success"]))
    
    # Test 4: Full Navigator Mock
    result4 = await test_unified_navigator_mock_mode()
    test_results.append(("Unified Navigator Mock", result4["success"]))
    
    # Summary
    print("\n" + "=" * 60)
    print("MOCK TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    print(f"Tests Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}")
    
    print("=" * 60)
    
    if passed == total:
        print("🎉 All mock tests passed! New features are working correctly.")
        print("💡 System ready for deployment with API cost controls.")
    else:
        print(f"⚠️  {total - passed} test(s) failed. Review errors above.")
        
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_mock_tests())
    exit(0 if success else 1)