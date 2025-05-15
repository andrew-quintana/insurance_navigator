# Agent Performance Metrics Framework

This framework provides standardized performance testing and metrics collection for all agents in the insurance navigator system.

## Features

- **Standardized Metrics**: Consistent metrics across all agents
- **Classification Metrics**: TP, FP, TN, FN, precision, recall, F1 score, accuracy
- **Performance Metrics**: Response time, token usage, memory usage
- **Category-based Analysis**: Break down metrics by test categories
- **JSON Export**: Save metrics for later analysis or visualization

## How to Use

### Basic Usage

```python
from utils.performance_metrics import PerformanceEvaluator, TestCase

# 1. Create test cases
test_cases = [
    TestCase(
        input="What does my insurance cover?",
        expected_output=True,  # Expected output depends on your agent
        category="general_query"
    ),
    # Add more test cases...
]

# 2. Initialize your agent
agent = YourAgent()

# 3. Create evaluator
evaluator = PerformanceEvaluator("Your Agent Name")

# 4. Define the process function (how to call your agent)
process_func = lambda input_text: agent.process(input_text)

# 5. Run the tests
evaluator.run_test_cases(
    test_cases=test_cases,
    process_func=process_func
)

# 6. Calculate and print metrics
metrics = evaluator.calculate_metrics()
evaluator.print_metrics_report(metrics)

# 7. Save metrics to file
metrics.save_to_file("your_agent_metrics.json")
```

### Custom Correctness Function

If your agent's output format doesn't match the expected output directly, provide a custom function:

```python
def is_correct_func(actual_output, expected_output):
    """Custom function to determine if the output is correct."""
    # Example for an agent that returns a tuple (is_safe, sanitized_input, details)
    if isinstance(actual_output, tuple) and len(actual_output) >= 1:
        return actual_output[0] == expected_output
    return False

# Then pass it to run_test_cases
evaluator.run_test_cases(
    test_cases=test_cases,
    process_func=process_func,
    is_correct_func=is_correct_func
)
```

### Token Counting

To track token usage:

```python
from utils.performance_metrics import estimate_tokens

def token_counter(output):
    """Count tokens in the output."""
    # Adapt this to your agent's output format
    return estimate_tokens(str(output))

# Then pass it to run_test_cases
evaluator.run_test_cases(
    test_cases=test_cases,
    process_func=process_func,
    token_counter=token_counter
)
```

## Metrics Provided

### General Metrics
- Total test cases
- Success rate

### Timing Metrics
- Average response time
- Min/max response time

### Resource Usage
- Average tokens per request
- Memory peak usage
- Average turns per test case

### Classification Metrics
- True positives/negatives
- False positives/negatives
- Precision
- Recall
- F1 Score
- Accuracy

### Category-based Metrics
- Metrics broken down by test category

## Example Implementation

See `agents/prompt_security/tests/test_performance.py` for a complete example of how to use this framework.

## Best Practices

1. **Organize test cases by category** to get more detailed insights
2. **Use consistent test data** across different agent versions for valid comparisons
3. **Save metrics to files** with version information for tracking improvements over time
4. **Run tests in mock mode** during development for faster iteration
5. **Run tests with real API calls** for final validation before deployment 