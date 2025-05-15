"""
Performance Metrics Utility

A generic framework for measuring agent performance across different tasks.
Provides standardized metrics for:
- Response time/latency
- Success rates
- Classification metrics (precision, recall, F1)
- Token usage
- Memory usage
"""

import time
import json
import tracemalloc
from typing import Dict, List, Any, Callable, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict

@dataclass
class TestCase:
    """A single test case for agent evaluation."""
    input: Any
    expected_output: Any
    category: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TestResult:
    """Result of a single test case execution."""
    input: Any
    expected_output: Any
    actual_output: Any
    category: str
    is_correct: bool
    response_time: float  # in seconds
    token_count: int = 0
    turn_count: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics for an agent."""
    # General metrics
    total_cases: int = 0
    successful_cases: int = 0
    success_rate: float = 0.0
    
    # Timing metrics
    total_response_time: float = 0.0
    avg_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    
    # Resource usage
    total_tokens: int = 0
    avg_tokens: float = 0.0
    memory_peak_mb: float = 0.0
    
    # Turn metrics
    total_turns: int = 0
    avg_turns: float = 0.0
    
    # Classification metrics
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    accuracy: float = 0.0
    
    # Metrics by category
    categories: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to a dictionary."""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert metrics to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def save_to_file(self, filepath: str) -> None:
        """Save metrics to a JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())

class PerformanceEvaluator:
    """Evaluates agent performance using standardized metrics."""
    
    def __init__(self, agent_name: str, track_memory: bool = True):
        """Initialize the evaluator.
        
        Args:
            agent_name: Name of the agent being evaluated
            track_memory: Whether to track memory usage
        """
        self.agent_name = agent_name
        self.track_memory = track_memory
        self.results: List[TestResult] = []
    
    def run_test_case(
        self, 
        test_case: TestCase, 
        process_func: Callable,
        is_correct_func: Optional[Callable[[Any, Any], bool]] = None,
        token_counter: Optional[Callable[[Any], int]] = None
    ) -> TestResult:
        """Run a single test case and record metrics.
        
        Args:
            test_case: The test case to run
            process_func: Function that processes the input and returns output
            is_correct_func: Optional function to determine if the output is correct
            token_counter: Optional function to count tokens in the output
            
        Returns:
            TestResult object with metrics
        """
        # Start timing
        start_time = time.time()
        
        # Process the input
        actual_output = process_func(test_case.input)
        
        # End timing
        end_time = time.time()
        response_time = end_time - start_time
        
        # Determine if the output is correct
        if is_correct_func:
            is_correct = is_correct_func(actual_output, test_case.expected_output)
        else:
            # Default to simple equality check
            is_correct = actual_output == test_case.expected_output
        
        # Count tokens if a counter is provided
        token_count = 0
        if token_counter:
            token_count = token_counter(actual_output)
        
        # Create and return the test result
        result = TestResult(
            input=test_case.input,
            expected_output=test_case.expected_output,
            actual_output=actual_output,
            category=test_case.category,
            is_correct=is_correct,
            response_time=response_time,
            token_count=token_count,
            metadata=test_case.metadata.copy()
        )
        
        self.results.append(result)
        return result
    
    def run_test_cases(
        self, 
        test_cases: List[TestCase], 
        process_func: Callable,
        is_correct_func: Optional[Callable[[Any, Any], bool]] = None,
        token_counter: Optional[Callable[[Any], int]] = None,
        progress_interval: int = 10
    ) -> List[TestResult]:
        """Run multiple test cases and record metrics.
        
        Args:
            test_cases: List of test cases to run
            process_func: Function that processes the input and returns output
            is_correct_func: Optional function to determine if the output is correct
            token_counter: Optional function to count tokens in the output
            progress_interval: How often to print progress (0 to disable)
            
        Returns:
            List of TestResult objects
        """
        results = []
        
        # Start memory tracking if enabled
        if self.track_memory:
            tracemalloc.start()
        
        # Process each test case
        for i, test_case in enumerate(test_cases):
            result = self.run_test_case(
                test_case, 
                process_func, 
                is_correct_func, 
                token_counter
            )
            results.append(result)
            
            # Print progress if enabled
            if progress_interval > 0 and (i + 1) % progress_interval == 0:
                print(f"Processed {i + 1}/{len(test_cases)} test cases")
        
        # Stop memory tracking if enabled
        if self.track_memory:
            current, peak = tracemalloc.get_traced_memory()
            self.memory_peak = peak / (1024 * 1024)  # Convert to MB
            tracemalloc.stop()
        else:
            self.memory_peak = 0
        
        return results
    
    def calculate_metrics(self) -> PerformanceMetrics:
        """Calculate performance metrics from the test results."""
        metrics = PerformanceMetrics()
        
        # Skip if no results
        if not self.results:
            return metrics
        
        # General metrics
        metrics.total_cases = len(self.results)
        metrics.successful_cases = sum(1 for r in self.results if r.is_correct)
        metrics.success_rate = metrics.successful_cases / metrics.total_cases if metrics.total_cases > 0 else 0
        
        # Timing metrics
        metrics.total_response_time = sum(r.response_time for r in self.results)
        metrics.avg_response_time = metrics.total_response_time / metrics.total_cases
        metrics.min_response_time = min(r.response_time for r in self.results)
        metrics.max_response_time = max(r.response_time for r in self.results)
        
        # Resource usage
        metrics.total_tokens = sum(r.token_count for r in self.results)
        metrics.avg_tokens = metrics.total_tokens / metrics.total_cases if metrics.total_cases > 0 else 0
        metrics.memory_peak_mb = self.memory_peak
        
        # Turn metrics
        metrics.total_turns = sum(r.turn_count for r in self.results)
        metrics.avg_turns = metrics.total_turns / metrics.total_cases if metrics.total_cases > 0 else 0
        
        # Classification metrics
        # Assuming binary classification where True is positive and False is negative
        for result in self.results:
            expected = result.expected_output
            actual = result.actual_output
            
            # Handle different output formats
            if isinstance(expected, bool) and isinstance(actual, bool):
                # Direct boolean comparison
                if expected and actual:
                    metrics.true_positives += 1
                elif not expected and not actual:
                    metrics.true_negatives += 1
                elif not expected and actual:
                    metrics.false_positives += 1
                elif expected and not actual:
                    metrics.false_negatives += 1
            elif isinstance(expected, tuple) and len(expected) > 0 and isinstance(expected[0], bool):
                # Tuple with boolean as first element
                expected_bool = expected[0]
                actual_bool = actual[0] if isinstance(actual, tuple) and len(actual) > 0 else False
                
                if expected_bool and actual_bool:
                    metrics.true_positives += 1
                elif not expected_bool and not actual_bool:
                    metrics.true_negatives += 1
                elif not expected_bool and actual_bool:
                    metrics.false_positives += 1
                elif expected_bool and not actual_bool:
                    metrics.false_negatives += 1
            elif isinstance(expected, dict) and 'is_safe' in expected:
                # Dictionary with 'is_safe' key (common in security checks)
                expected_bool = expected.get('is_safe', False)
                actual_bool = actual.get('is_safe', False) if isinstance(actual, dict) else False
                
                if expected_bool and actual_bool:
                    metrics.true_positives += 1
                elif not expected_bool and not actual_bool:
                    metrics.true_negatives += 1
                elif not expected_bool and actual_bool:
                    metrics.false_positives += 1
                elif expected_bool and not actual_bool:
                    metrics.false_negatives += 1
        
        # Calculate derived classification metrics
        if metrics.true_positives + metrics.false_positives > 0:
            metrics.precision = metrics.true_positives / (metrics.true_positives + metrics.false_positives)
        
        if metrics.true_positives + metrics.false_negatives > 0:
            metrics.recall = metrics.true_positives / (metrics.true_positives + metrics.false_negatives)
        
        if metrics.precision + metrics.recall > 0:
            metrics.f1_score = 2 * (metrics.precision * metrics.recall) / (metrics.precision + metrics.recall)
        
        if metrics.total_cases > 0:
            metrics.accuracy = (metrics.true_positives + metrics.true_negatives) / metrics.total_cases
        
        # Metrics by category
        categories = set(r.category for r in self.results)
        for category in categories:
            category_results = [r for r in self.results if r.category == category]
            successful = sum(1 for r in category_results if r.is_correct)
            total_time = sum(r.response_time for r in category_results)
            total_tokens = sum(r.token_count for r in category_results)
            total_turns = sum(r.turn_count for r in category_results)
            
            metrics.categories[category] = {
                "total_cases": len(category_results),
                "successful_cases": successful,
                "success_rate": successful / len(category_results) if category_results else 0,
                "avg_response_time": total_time / len(category_results) if category_results else 0,
                "avg_tokens": total_tokens / len(category_results) if category_results else 0,
                "avg_turns": total_turns / len(category_results) if category_results else 0
            }
        
        return metrics
    
    def print_metrics_report(self, metrics: Optional[PerformanceMetrics] = None) -> None:
        """Print a formatted metrics report."""
        if metrics is None:
            metrics = self.calculate_metrics()
        
        print("\n" + "=" * 50)
        print(f"{self.agent_name.upper()} PERFORMANCE REPORT")
        print("=" * 50)
        
        # General metrics
        print("\n--- GENERAL METRICS ---")
        print(f"Total test cases: {metrics.total_cases}")
        print(f"Success rate: {metrics.success_rate:.2%} ({metrics.successful_cases}/{metrics.total_cases})")
        
        # Timing metrics
        print("\n--- TIMING METRICS ---")
        print(f"Average response time: {metrics.avg_response_time:.4f} seconds")
        print(f"Min response time: {metrics.min_response_time:.4f} seconds")
        print(f"Max response time: {metrics.max_response_time:.4f} seconds")
        
        # Resource usage
        print("\n--- RESOURCE USAGE ---")
        print(f"Average tokens per request: {metrics.avg_tokens:.2f}")
        print(f"Memory peak usage: {metrics.memory_peak_mb:.2f} MB")
        print(f"Average turns per test case: {metrics.avg_turns:.2f}")
        
        # Classification metrics
        print("\n--- CLASSIFICATION METRICS ---")
        print(f"True positives: {metrics.true_positives}")
        print(f"False positives: {metrics.false_positives}")
        print(f"True negatives: {metrics.true_negatives}")
        print(f"False negatives: {metrics.false_negatives}")
        print(f"Precision: {metrics.precision:.4f}")
        print(f"Recall: {metrics.recall:.4f}")
        print(f"F1 Score: {metrics.f1_score:.4f}")
        print(f"Accuracy: {metrics.accuracy:.4f}")
        
        # Metrics by category
        print("\n--- METRICS BY CATEGORY ---")
        for category, stats in metrics.categories.items():
            print(f"\n{category}:")
            print(f"  Total cases: {stats['total_cases']}")
            print(f"  Success rate: {stats['success_rate']:.2%} ({stats['successful_cases']}/{stats['total_cases']})")
            print(f"  Average response time: {stats['avg_response_time']:.4f} seconds")
            print(f"  Average tokens: {stats['avg_tokens']:.2f}")
            print(f"  Average turns: {stats['avg_turns']:.2f}")

def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a string using a simple heuristic.
    
    This is a very rough approximation. For more accurate counts, use a tokenizer.
    """
    if not text:
        return 0
    
    # Rough approximation: 1 token ≈ 4 characters for English text
    return len(text) // 4 