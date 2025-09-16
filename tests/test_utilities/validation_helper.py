"""
Validation Helper for Phase 3 Testing

Provides utilities for validating responses, performance, and error handling.
"""

import logging
from typing import Dict, Any, List, Optional, Union
import time

logger = logging.getLogger(__name__)

def validate_response_structure(
    response_data: Dict[str, Any], 
    required_fields: List[str],
    optional_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Validate that a response has the required structure."""
    validation_result = {
        "valid": True,
        "missing_required": [],
        "present_optional": [],
        "extra_fields": []
    }
    
    # Check required fields
    for field in required_fields:
        if field not in response_data:
            validation_result["missing_required"].append(field)
            validation_result["valid"] = False
    
    # Check optional fields
    if optional_fields:
        for field in optional_fields:
            if field in response_data:
                validation_result["present_optional"].append(field)
    
    # Check for unexpected fields
    expected_fields = set(required_fields + (optional_fields or []))
    actual_fields = set(response_data.keys())
    extra_fields = actual_fields - expected_fields
    validation_result["extra_fields"] = list(extra_fields)
    
    return validation_result

def validate_performance_metrics(
    duration: float, 
    target: float, 
    tolerance: float = 0.1
) -> Dict[str, Any]:
    """Validate performance metrics against targets."""
    acceptable_duration = target * (1 + tolerance)
    
    return {
        "duration": duration,
        "target": target,
        "acceptable_limit": acceptable_duration,
        "passed": duration <= acceptable_duration,
        "performance_ratio": duration / target if target > 0 else float('inf')
    }

def validate_error_handling(
    response_status: int,
    expected_status: Union[int, List[int]],
    response_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate error handling behavior."""
    if isinstance(expected_status, int):
        expected_statuses = [expected_status]
    else:
        expected_statuses = expected_status
    
    validation_result = {
        "status_correct": response_status in expected_statuses,
        "actual_status": response_status,
        "expected_statuses": expected_statuses
    }
    
    # Check for error response structure if provided
    if response_data and response_status >= 400:
        error_fields = ["detail", "message", "error"]
        has_error_info = any(field in response_data for field in error_fields)
        validation_result["has_error_info"] = has_error_info
        validation_result["error_data"] = response_data
    
    return validation_result

def calculate_success_rate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate success rate from test results."""
    if not results:
        return {
            "success_rate": 0.0,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0
        }
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results if result.get("success", False))
    failed_tests = total_tests - passed_tests
    success_rate = passed_tests / total_tests
    
    return {
        "success_rate": success_rate,
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests
    }

def validate_production_readiness(
    test_results: List[Dict[str, Any]], 
    minimum_success_rate: float = 0.85
) -> Dict[str, Any]:
    """Validate overall production readiness based on test results."""
    success_metrics = calculate_success_rate(test_results)
    
    production_ready = success_metrics["success_rate"] >= minimum_success_rate
    
    # Categorize failed tests by severity
    critical_failures = []
    warning_failures = []
    
    for result in test_results:
        if not result.get("success", False):
            test_name = result.get("test_name", "unknown")
            if any(keyword in test_name.lower() for keyword in ["critical", "security", "auth"]):
                critical_failures.append(test_name)
            else:
                warning_failures.append(test_name)
    
    return {
        "production_ready": production_ready,
        "success_metrics": success_metrics,
        "minimum_required": minimum_success_rate,
        "critical_failures": critical_failures,
        "warning_failures": warning_failures,
        "recommendation": _get_production_recommendation(production_ready, critical_failures)
    }

def _get_production_recommendation(production_ready: bool, critical_failures: List[str]) -> str:
    """Get production deployment recommendation."""
    if production_ready and not critical_failures:
        return "READY FOR PRODUCTION - All critical tests passed"
    elif production_ready and critical_failures:
        return "CONDITIONAL READY - High success rate but critical issues need review"
    elif not production_ready and not critical_failures:
        return "NOT READY - Success rate below threshold, non-critical issues need fixing"
    else:
        return "NOT READY - Critical failures must be resolved before production deployment"
