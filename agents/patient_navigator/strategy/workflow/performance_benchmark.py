#!/usr/bin/env python3
"""
Phase 4: Performance Benchmarking Suite

This script provides comprehensive performance benchmarking for the Strategy Evaluation & Validation System MVP.
It measures actual performance against the <30 second target and validates performance characteristics.

Usage:
    python performance_benchmark.py --mock    # Benchmark with mock APIs
    python performance_benchmark.py --real    # Benchmark with real APIs (requires API keys)
    python performance_benchmark.py --stress  # Stress testing with concurrent requests
    python performance_benchmark.py --detailed # Detailed performance analysis
"""

import asyncio
import argparse
import logging
import sys
import time
import statistics
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add the project root to the path for imports
sys.path.append('../../../')

from agents.patient_navigator.strategy.types import PlanConstraints, WorkflowConfig, StrategyWorkflowState
from agents.patient_navigator.strategy.workflow.runner import StrategyWorkflowRunner, run_strategy_workflow

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    test_name: str
    iterations: int
    total_duration: float
    average_duration: float
    median_duration: float
    min_duration: float
    max_duration: float
    std_deviation: float
    success_rate: float
    within_target: bool
    target_seconds: float = 30.0

class PerformanceBenchmark:
    """Comprehensive performance benchmarking for Phase 4."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Test plan constraints
        self.test_plan_constraints = PlanConstraints(
            copay=25,
            deductible=1000,
            network_providers=["Kaiser Permanente", "Sutter Health", "Dignity Health"],
            geographic_scope="Northern California",
            specialty_access=["Cardiology", "Orthopedics", "Neurology"]
        )
        
        # Mock configuration
        self.mock_config = WorkflowConfig(
            use_mock=True,
            timeout_seconds=30,
            enable_logging=False,  # Disable logging for performance testing
            enable_audit_trail=False
        )
        
        # Real configuration
        self.real_config = WorkflowConfig(
            use_mock=False,
            timeout_seconds=30,
            enable_logging=False,  # Disable logging for performance testing
            enable_audit_trail=False
        )
    
    async def benchmark_mock_workflow(self, iterations: int = 10) -> PerformanceMetrics:
        """Benchmark workflow performance with mock APIs."""
        test_name = "Mock Workflow Performance"
        durations = []
        successes = 0
        
        self.logger.info(f"Starting {iterations} iterations of mock workflow benchmarking...")
        
        for i in range(iterations):
            try:
                start_time = time.time()
                
                # Run workflow
                runner = StrategyWorkflowRunner(self.mock_config)
                workflow_state = await runner.run_workflow(self.test_plan_constraints)
                
                duration = time.time() - start_time
                durations.append(duration)
                
                # Validate results
                if (workflow_state.strategies and 
                    len(workflow_state.strategies) == 4 and
                    workflow_state.storage_confirmation and
                    workflow_state.storage_confirmation.storage_status == "success"):
                    successes += 1
                
                self.logger.info(f"Iteration {i+1}/{iterations}: {duration:.2f}s")
                
            except Exception as error:
                self.logger.error(f"Iteration {i+1} failed: {error}")
                durations.append(30.0)  # Count as timeout
        
        return self._calculate_metrics(test_name, durations, successes, iterations)
    
    async def benchmark_real_workflow(self, iterations: int = 5) -> PerformanceMetrics:
        """Benchmark workflow performance with real APIs."""
        test_name = "Real Workflow Performance"
        durations = []
        successes = 0
        
        # Check for required environment variables
        import os
        required_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            self.logger.error(f"Missing required environment variables: {missing_vars}")
            return PerformanceMetrics(
                test_name=test_name,
                iterations=0,
                total_duration=0,
                average_duration=0,
                median_duration=0,
                min_duration=0,
                max_duration=0,
                std_deviation=0,
                success_rate=0,
                within_target=False
            )
        
        self.logger.info(f"Starting {iterations} iterations of real workflow benchmarking...")
        
        for i in range(iterations):
            try:
                start_time = time.time()
                
                # Run workflow
                runner = StrategyWorkflowRunner(self.real_config)
                workflow_state = await runner.run_workflow(self.test_plan_constraints)
                
                duration = time.time() - start_time
                durations.append(duration)
                
                # Validate results
                if (workflow_state.strategies and 
                    len(workflow_state.strategies) == 4 and
                    workflow_state.storage_confirmation and
                    workflow_state.storage_confirmation.storage_status == "success"):
                    successes += 1
                
                self.logger.info(f"Iteration {i+1}/{iterations}: {duration:.2f}s")
                
                # Add delay between real API calls to avoid rate limiting
                if i < iterations - 1:
                    await asyncio.sleep(2)
                
            except Exception as error:
                self.logger.error(f"Iteration {i+1} failed: {error}")
                durations.append(30.0)  # Count as timeout
        
        return self._calculate_metrics(test_name, durations, successes, iterations)
    
    async def stress_test_concurrent_requests(self, concurrent_requests: int = 5) -> PerformanceMetrics:
        """Stress test with concurrent requests."""
        test_name = f"Concurrent Requests Stress Test ({concurrent_requests} requests)"
        durations = []
        successes = 0
        
        self.logger.info(f"Starting stress test with {concurrent_requests} concurrent requests...")
        
        async def run_single_workflow():
            """Run a single workflow instance."""
            try:
                start_time = time.time()
                
                runner = StrategyWorkflowRunner(self.mock_config)
                workflow_state = await runner.run_workflow(self.test_plan_constraints)
                
                duration = time.time() - start_time
                
                # Validate results
                success = (workflow_state.strategies and 
                          len(workflow_state.strategies) == 4 and
                          workflow_state.storage_confirmation and
                          workflow_state.storage_confirmation.storage_status == "success")
                
                return duration, success
                
            except Exception as error:
                self.logger.error(f"Concurrent request failed: {error}")
                return 30.0, False
        
        # Run concurrent requests
        tasks = [run_single_workflow() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for duration, success in results:
            if isinstance(duration, (int, float)):
                durations.append(duration)
                if success:
                    successes += 1
        
        return self._calculate_metrics(test_name, durations, successes, concurrent_requests)
    
    async def benchmark_component_performance(self) -> Dict[str, PerformanceMetrics]:
        """Benchmark individual component performance."""
        self.logger.info("Starting component-level performance benchmarking...")
        
        component_metrics = {}
        
        # Test StrategyMCP performance
        try:
            from agents.patient_navigator.strategy.workflow.orchestrator import StrategyWorkflowOrchestrator
            
            durations = []
            for i in range(5):
                start_time = time.time()
                orchestrator = StrategyWorkflowOrchestrator(self.mock_config)
                context_result = await orchestrator.strategy_mcp.gather_context(self.test_plan_constraints)
                duration = time.time() - start_time
                durations.append(duration)
            
            component_metrics["StrategyMCP"] = self._calculate_metrics(
                "StrategyMCP Component", durations, 5, 5
            )
            
        except Exception as error:
            self.logger.error(f"StrategyMCP benchmarking failed: {error}")
        
        # Test StrategyCreator performance
        try:
            from agents.patient_navigator.strategy.creator.agent import StrategyCreatorAgent
            
            # Create mock context for testing
            mock_context = type('MockContext', (), {
                'web_search_results': [],
                'similar_strategies': [],
                'regulatory_context': []
            })()
            
            durations = []
            for i in range(5):
                start_time = time.time()
                creator_agent = StrategyCreatorAgent(use_mock=True)
                strategies = await creator_agent.generate_strategies(mock_context)
                duration = time.time() - start_time
                durations.append(duration)
            
            component_metrics["StrategyCreator"] = self._calculate_metrics(
                "StrategyCreator Component", durations, 5, 5
            )
            
        except Exception as error:
            self.logger.error(f"StrategyCreator benchmarking failed: {error}")
        
        # Test RegulatoryAgent performance
        try:
            from agents.patient_navigator.strategy.regulatory.agent import RegulatoryAgent
            
            # Create mock strategies for testing
            mock_strategies = [
                type('MockStrategy', (), {
                    'title': f'Test Strategy {i}',
                    'category': 'speed',
                    'approach': 'Test approach',
                    'rationale': 'Test rationale',
                    'actionable_steps': ['Step 1', 'Step 2'],
                    'llm_scores': type('MockScores', (), {
                        'speed': 0.8,
                        'cost': 0.6,
                        'effort': 0.7
                    })()
                })()
                for i in range(4)
            ]
            
            durations = []
            for i in range(5):
                start_time = time.time()
                regulatory_agent = RegulatoryAgent(use_mock=True)
                validation_results = await regulatory_agent.validate_strategies(mock_strategies)
                duration = time.time() - start_time
                durations.append(duration)
            
            component_metrics["RegulatoryAgent"] = self._calculate_metrics(
                "RegulatoryAgent Component", durations, 5, 5
            )
            
        except Exception as error:
            self.logger.error(f"RegulatoryAgent benchmarking failed: {error}")
        
        return component_metrics
    
    def _calculate_metrics(
        self, 
        test_name: str, 
        durations: List[float], 
        successes: int, 
        total_iterations: int
    ) -> PerformanceMetrics:
        """Calculate performance metrics from duration data."""
        if not durations:
            return PerformanceMetrics(
                test_name=test_name,
                iterations=total_iterations,
                total_duration=0,
                average_duration=0,
                median_duration=0,
                min_duration=0,
                max_duration=0,
                std_deviation=0,
                success_rate=0,
                within_target=False
            )
        
        total_duration = sum(durations)
        average_duration = total_duration / len(durations)
        median_duration = statistics.median(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        std_deviation = statistics.stdev(durations) if len(durations) > 1 else 0
        success_rate = (successes / total_iterations) * 100
        within_target = average_duration <= 30.0
        
        return PerformanceMetrics(
            test_name=test_name,
            iterations=total_iterations,
            total_duration=total_duration,
            average_duration=average_duration,
            median_duration=median_duration,
            min_duration=min_duration,
            max_duration=max_duration,
            std_deviation=std_deviation,
            success_rate=success_rate,
            within_target=within_target
        )
    
    def print_metrics(self, metrics: PerformanceMetrics) -> None:
        """Print performance metrics in a formatted way."""
        print(f"\n{'='*60}")
        print(f"PERFORMANCE METRICS: {metrics.test_name}")
        print(f"{'='*60}")
        print(f"Iterations: {metrics.iterations}")
        print(f"Total Duration: {metrics.total_duration:.2f}s")
        print(f"Average Duration: {metrics.average_duration:.2f}s")
        print(f"Median Duration: {metrics.median_duration:.2f}s")
        print(f"Min Duration: {metrics.min_duration:.2f}s")
        print(f"Max Duration: {metrics.max_duration:.2f}s")
        print(f"Standard Deviation: {metrics.std_deviation:.2f}s")
        print(f"Success Rate: {metrics.success_rate:.1f}%")
        print(f"Within 30s Target: {'✅ YES' if metrics.within_target else '❌ NO'}")
        
        if not metrics.within_target:
            print(f"⚠️  Performance exceeds target by {metrics.average_duration - 30:.2f}s")
    
    def generate_performance_report(self, all_metrics: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(all_metrics),
                "tests_within_target": sum(1 for m in all_metrics if m.within_target),
                "overall_success_rate": statistics.mean([m.success_rate for m in all_metrics]) if all_metrics else 0,
                "average_duration": statistics.mean([m.average_duration for m in all_metrics]) if all_metrics else 0
            },
            "detailed_metrics": [
                {
                    "test_name": m.test_name,
                    "iterations": m.iterations,
                    "total_duration": m.total_duration,
                    "average_duration": m.average_duration,
                    "median_duration": m.median_duration,
                    "min_duration": m.min_duration,
                    "max_duration": m.max_duration,
                    "std_deviation": m.std_deviation,
                    "success_rate": m.success_rate,
                    "within_target": m.within_target
                }
                for m in all_metrics
            ]
        }
        
        return report

async def main():
    """Main benchmarking function."""
    parser = argparse.ArgumentParser(description="Phase 4: Performance Benchmarking Suite")
    parser.add_argument("--mock", action="store_true", help="Benchmark with mock APIs")
    parser.add_argument("--real", action="store_true", help="Benchmark with real APIs")
    parser.add_argument("--stress", action="store_true", help="Stress testing with concurrent requests")
    parser.add_argument("--component", action="store_true", help="Component-level benchmarking")
    parser.add_argument("--detailed", action="store_true", help="Detailed performance analysis")
    parser.add_argument("--all", action="store_true", help="Run all benchmarks")
    parser.add_argument("--report", action="store_true", help="Generate detailed report")
    
    args = parser.parse_args()
    
    # If no specific benchmark is selected, run mock benchmark by default
    if not any([args.mock, args.real, args.stress, args.component, args.detailed, args.all]):
        args.mock = True
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create benchmark suite
    benchmark = PerformanceBenchmark()
    all_metrics = []
    
    print("\n" + "="*80)
    print("PHASE 4: PERFORMANCE BENCHMARKING SUITE")
    print("="*80)
    
    # Run benchmarks based on arguments
    if args.mock or args.all:
        print("\n1. Mock Workflow Performance Benchmarking...")
        metrics = await benchmark.benchmark_mock_workflow(iterations=10)
        benchmark.print_metrics(metrics)
        all_metrics.append(metrics)
    
    if args.real or args.all:
        print("\n2. Real Workflow Performance Benchmarking...")
        metrics = await benchmark.benchmark_real_workflow(iterations=5)
        benchmark.print_metrics(metrics)
        all_metrics.append(metrics)
    
    if args.stress or args.all:
        print("\n3. Concurrent Requests Stress Testing...")
        metrics = await benchmark.stress_test_concurrent_requests(concurrent_requests=5)
        benchmark.print_metrics(metrics)
        all_metrics.append(metrics)
    
    if args.component or args.all:
        print("\n4. Component-Level Performance Benchmarking...")
        component_metrics = await benchmark.benchmark_component_performance()
        for component_name, metrics in component_metrics.items():
            print(f"\n{component_name}:")
            benchmark.print_metrics(metrics)
            all_metrics.append(metrics)
    
    # Generate summary
    if all_metrics:
        print("\n" + "="*80)
        print("PERFORMANCE SUMMARY")
        print("="*80)
        
        tests_within_target = sum(1 for m in all_metrics if m.within_target)
        overall_success_rate = statistics.mean([m.success_rate for m in all_metrics])
        average_duration = statistics.mean([m.average_duration for m in all_metrics])
        
        print(f"Total Tests: {len(all_metrics)}")
        print(f"Tests Within 30s Target: {tests_within_target}/{len(all_metrics)}")
        print(f"Overall Success Rate: {overall_success_rate:.1f}%")
        print(f"Average Duration: {average_duration:.2f}s")
        
        if tests_within_target == len(all_metrics):
            print("✅ ALL TESTS MEET PERFORMANCE TARGETS")
        else:
            print("⚠️  SOME TESTS EXCEED PERFORMANCE TARGETS")
        
        # Generate detailed report if requested
        if args.report or args.detailed:
            report = benchmark.generate_performance_report(all_metrics)
            report_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\nDetailed performance report saved to: {report_file}")
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 