"""
Unit tests for the cost tracking system.

Tests cost tracking, budget enforcement, and usage monitoring functionality.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from backend.shared.monitoring.cost_tracker import (
    CostTracker, UsageMetrics, CostLimit, get_cost_tracker, configure_default_limits
)


class TestUsageMetrics:
    """Test cases for UsageMetrics dataclass."""
    
    def test_usage_metrics_creation(self):
        """Test UsageMetrics creation with all parameters."""
        now = datetime.utcnow()
        metrics = UsageMetrics(
            service_name="test_service",
            request_count=10,
            total_cost_usd=5.50,
            total_tokens=1000,
            error_count=2,
            last_request=now,
            first_request=now
        )
        
        assert metrics.service_name == "test_service"
        assert metrics.request_count == 10
        assert metrics.total_cost_usd == 5.50
        assert metrics.total_tokens == 1000
        assert metrics.error_count == 2
        assert metrics.last_request == now
        assert metrics.first_request == now
    
    def test_usage_metrics_defaults(self):
        """Test UsageMetrics creation with default values."""
        metrics = UsageMetrics(service_name="test_service")
        
        assert metrics.service_name == "test_service"
        assert metrics.request_count == 0
        assert metrics.total_cost_usd == 0.0
        assert metrics.total_tokens == 0
        assert metrics.error_count == 0
        assert metrics.last_request is None
        assert metrics.first_request is None
    
    def test_usage_metrics_to_dict(self):
        """Test UsageMetrics serialization to dictionary."""
        now = datetime.utcnow()
        metrics = UsageMetrics(
            service_name="test_service",
            request_count=5,
            total_cost_usd=2.50,
            total_tokens=500,
            first_request=now
        )
        
        metrics_dict = metrics.to_dict()
        assert metrics_dict['service_name'] == "test_service"
        assert metrics_dict['request_count'] == 5
        assert metrics_dict['total_cost_usd'] == 2.50
        assert metrics_dict['total_tokens'] == 500
        assert 'first_request' in metrics_dict


class TestCostLimit:
    """Test cases for CostLimit dataclass."""
    
    def test_cost_limit_creation(self):
        """Test CostLimit creation."""
        cost_limit = CostLimit(
            daily_limit_usd=25.00,
            hourly_rate_limit=100,
            alert_threshold_percent=80.0
        )
        
        assert cost_limit.daily_limit_usd == 25.00
        assert cost_limit.hourly_rate_limit == 100
        assert cost_limit.alert_threshold_percent == 80.0
    
    def test_cost_limit_defaults(self):
        """Test CostLimit creation with default values."""
        cost_limit = CostLimit(daily_limit_usd=10.00, hourly_rate_limit=50)
        
        assert cost_limit.daily_limit_usd == 10.00
        assert cost_limit.hourly_rate_limit == 50
        assert cost_limit.alert_threshold_percent == 80.0
    
    def test_cost_limit_is_exceeded_cost(self):
        """Test cost limit exceeded check for daily cost."""
        cost_limit = CostLimit(daily_limit_usd=10.00, hourly_rate_limit=100)
        
        # Cost exceeded
        assert cost_limit.is_exceeded(current_cost=12.00, current_rate=50) is True
        
        # Cost within limit
        assert cost_limit.is_exceeded(current_cost=8.00, current_rate=50) is False
    
    def test_cost_limit_is_exceeded_rate(self):
        """Test cost limit exceeded check for hourly rate."""
        cost_limit = CostLimit(daily_limit_usd=10.00, hourly_rate_limit=100)
        
        # Rate exceeded
        assert cost_limit.is_exceeded(current_cost=5.00, current_rate=150) is True
        
        # Rate within limit
        assert cost_limit.is_exceeded(current_cost=5.00, current_rate=50) is False


class TestCostTracker:
    """Test cases for CostTracker class."""
    
    @pytest.fixture
    def cost_tracker(self):
        """Create a CostTracker instance for testing."""
        return CostTracker()
    
    def test_initialization(self, cost_tracker):
        """Test CostTracker initialization."""
        assert len(cost_tracker.daily_metrics) == 0
        assert len(cost_tracker.hourly_metrics) == 0
        assert len(cost_tracker.cost_limits) == 0
        assert cost_tracker.alert_threshold_percent == 80.0
        assert len(cost_tracker.alerts_sent) == 0
    
    def test_configure_service_limits(self, cost_tracker):
        """Test service limit configuration."""
        cost_tracker.configure_service_limits(
            service_name="test_service",
            daily_limit_usd=15.00,
            hourly_rate_limit=75,
            alert_threshold_percent=85.0
        )
        
        assert "test_service" in cost_tracker.cost_limits
        limit = cost_tracker.cost_limits["test_service"]
        assert limit.daily_limit_usd == 15.00
        assert limit.hourly_rate_limit == 75
        assert limit.alert_threshold_percent == 85.0
    
    def test_record_request_success(self, cost_tracker):
        """Test recording successful request."""
        cost_tracker.record_request(
            service_name="test_service",
            cost_usd=0.50,
            token_count=100,
            success=True
        )
        
        now = datetime.utcnow()
        date_key = now.strftime("%Y-%m-%d")
        hour_key = now.strftime("%Y-%m-%d-%H")
        
        # Check daily metrics
        assert date_key in cost_tracker.daily_metrics
        assert "test_service" in cost_tracker.daily_metrics[date_key]
        
        daily_metric = cost_tracker.daily_metrics[date_key]["test_service"]
        assert daily_metric.request_count == 1
        assert daily_metric.total_cost_usd == 0.50
        assert daily_metric.total_tokens == 100
        assert daily_metric.error_count == 0
        
        # Check hourly metrics
        assert hour_key in cost_tracker.hourly_metrics
        assert "test_service" in cost_tracker.hourly_metrics[hour_key]
        
        hourly_metric = cost_tracker.hourly_metrics[hour_key]["test_service"]
        assert hourly_metric.request_count == 1
        assert hourly_metric.total_cost_usd == 0.50
        assert hourly_metric.total_tokens == 100
        assert hourly_metric.error_count == 0
    
    def test_record_request_failure(self, cost_tracker):
        """Test recording failed request."""
        cost_tracker.record_request(
            service_name="test_service",
            cost_usd=0.25,
            token_count=50,
            success=False
        )
        
        now = datetime.utcnow()
        date_key = now.strftime("%Y-%m-%d")
        hour_key = now.strftime("%Y-%m-%d-%H")
        
        # Check error count
        daily_metric = cost_tracker.daily_metrics[date_key]["test_service"]
        assert daily_metric.error_count == 1
        
        hourly_metric = cost_tracker.hourly_metrics[hour_key]["test_service"]
        assert hourly_metric.error_count == 1
    
    def test_record_multiple_requests(self, cost_tracker):
        """Test recording multiple requests for the same service."""
        # Record multiple requests
        for i in range(3):
            cost_tracker.record_request(
                service_name="test_service",
                cost_usd=0.10,
                token_count=25,
                success=True
            )
        
        now = datetime.utcnow()
        date_key = now.strftime("%Y-%m-%d")
        hour_key = now.strftime("%Y-%m-%d-%H")
        
        # Check accumulated metrics
        daily_metric = cost_tracker.daily_metrics[date_key]["test_service"]
        assert daily_metric.request_count == 3
        assert abs(daily_metric.total_cost_usd - 0.30) < 0.001  # Use approximate comparison for floating point
        assert daily_metric.total_tokens == 75
        
        hourly_metric = cost_tracker.hourly_metrics[hour_key]["test_service"]
        assert hourly_metric.request_count == 3
        assert abs(hourly_metric.total_cost_usd - 0.30) < 0.001  # Use approximate comparison for floating point
        assert hourly_metric.total_tokens == 75
    
    def test_check_cost_limit_within_limits(self, cost_tracker):
        """Test cost limit check when within limits."""
        cost_tracker.configure_service_limits(
            service_name="test_service",
            daily_limit_usd=10.00,
            hourly_rate_limit=100
        )
        
        # Record some requests
        cost_tracker.record_request("test_service", cost_usd=5.00, token_count=500)
        
        # Check if additional request would exceed limits
        assert cost_tracker.check_cost_limit("test_service", estimated_cost_usd=2.00) is True
    
    def test_check_cost_limit_exceeded(self, cost_tracker):
        """Test cost limit check when limits would be exceeded."""
        cost_tracker.configure_service_limits(
            service_name="test_service",
            daily_limit_usd=10.00,
            hourly_rate_limit=100
        )
        
        # Record requests up to limit
        cost_tracker.record_request("test_service", cost_usd=9.00, token_count=900)
        
        # Check if additional request would exceed daily limit
        assert cost_tracker.check_cost_limit("test_service", estimated_cost_usd=2.00) is False
    
    def test_check_cost_limit_rate_exceeded(self, cost_tracker):
        """Test cost limit check when hourly rate would be exceeded."""
        cost_tracker.configure_service_limits(
            service_name="test_service",
            daily_limit_usd=100.00,
            hourly_rate_limit=5
        )
        
        # Record requests up to hourly limit
        for i in range(5):
            cost_tracker.record_request("test_service", cost_usd=1.00, token_count=100)
        
        # Check if additional request would exceed hourly rate limit
        assert cost_tracker.check_cost_limit("test_service", estimated_cost_usd=1.00) is False
    
    def test_get_service_usage(self, cost_tracker):
        """Test getting service usage statistics."""
        # Record some requests
        cost_tracker.record_request("test_service", cost_usd=1.00, token_count=100, success=True)
        cost_tracker.record_request("test_service", cost_usd=2.00, token_count=200, success=True)
        cost_tracker.record_request("test_service", cost_usd=0.50, token_count=50, success=False)
        
        usage = cost_tracker.get_service_usage("test_service", days=7)
        
        assert usage['service_name'] == "test_service"
        assert usage['period_days'] == 7
        assert usage['total_requests'] == 3
        assert usage['total_cost_usd'] == 3.50
        assert usage['total_tokens'] == 350
        assert usage['total_errors'] == 1
        assert usage['average_cost_per_request'] == 3.50 / 3
        assert usage['error_rate_percent'] == (1 / 3) * 100
        # Note: date range includes both start and end dates, so 7 days = 8 dates
        assert len(usage['daily_breakdown']) == 8
    
    def test_get_all_services_summary(self, cost_tracker):
        """Test getting summary of all services."""
        # Record requests for multiple services
        cost_tracker.record_request("service1", cost_usd=1.00, token_count=100)
        cost_tracker.record_request("service2", cost_usd=2.00, token_count=200)
        cost_tracker.record_request("service1", cost_usd=0.50, token_count=50)
        
        summary = cost_tracker.get_all_services_summary()
        
        assert 'date' in summary
        assert summary['total_cost_usd'] == 3.50
        assert summary['total_requests'] == 3
        assert summary['total_tokens'] == 350
        assert len(summary['services']) == 2
        
        # Check service1 summary
        service1_summary = summary['services']['service1']
        assert service1_summary['requests'] == 2
        assert service1_summary['cost_usd'] == 1.50
        assert service1_summary['tokens'] == 150
        assert service1_summary['errors'] == 0
        
        # Check service2 summary
        service2_summary = summary['services']['service2']
        assert service2_summary['requests'] == 1
        assert service2_summary['cost_usd'] == 2.00
        assert service2_summary['tokens'] == 200
        assert service2_summary['errors'] == 0
    
    def test_get_cost_forecast_with_data(self, cost_tracker):
        """Test cost forecasting with usage data."""
        # Record requests for 7 days
        for i in range(7):
            cost_tracker.record_request("test_service", cost_usd=1.00, token_count=100)
        
        forecast = cost_tracker.get_cost_forecast("test_service", days=30)
        
        assert forecast['service_name'] == "test_service"
        assert forecast['forecast_days'] == 30
        assert forecast['estimated_total_cost'] == 30.00  # 1.00 * 30
        assert forecast['estimated_daily_cost'] == 1.00
        assert forecast['confidence'] in ['high', 'medium', 'low']
        assert forecast['current_daily_average'] == 1.00
        assert forecast['current_daily_requests'] == 1
    
    def test_get_cost_forecast_no_data(self, cost_tracker):
        """Test cost forecasting with no usage data."""
        forecast = cost_tracker.get_cost_forecast("test_service", days=30)
        
        assert forecast['service_name'] == "test_service"
        assert forecast['forecast_days'] == 30
        assert forecast['estimated_total_cost'] == 0.0
        assert forecast['estimated_daily_cost'] == 0.0
        assert forecast['confidence'] == 'low'
        assert forecast['reason'] == 'No usage data available'
    
    def test_export_metrics_json(self, cost_tracker):
        """Test metrics export in JSON format."""
        # Record some data
        cost_tracker.record_request("test_service", cost_usd=1.00, token_count=100)
        
        # Export metrics
        json_data = cost_tracker.export_metrics("json")
        
        # Verify it's valid JSON
        import json
        parsed_data = json.loads(json_data)
        
        assert 'daily_metrics' in parsed_data
        assert 'hourly_metrics' in parsed_data
        assert 'cost_limits' in parsed_data
        assert 'export_timestamp' in parsed_data
    
    def test_export_metrics_invalid_format(self, cost_tracker):
        """Test metrics export with invalid format."""
        with pytest.raises(ValueError):
            cost_tracker.export_metrics("invalid_format")
    
    def test_reset_metrics_specific_service(self, cost_tracker):
        """Test resetting metrics for a specific service."""
        # Record data for multiple services
        cost_tracker.record_request("service1", cost_usd=1.00, token_count=100)
        cost_tracker.record_request("service2", cost_usd=2.00, token_count=200)
        
        # Reset service1
        cost_tracker.reset_metrics("service1")
        
        # Check that service1 is reset but service2 remains
        now = datetime.utcnow()
        date_key = now.strftime("%Y-%m-%d")
        
        assert "service1" not in cost_tracker.daily_metrics[date_key]
        assert "service2" in cost_tracker.daily_metrics[date_key]
    
    def test_reset_metrics_all_services(self, cost_tracker):
        """Test resetting metrics for all services."""
        # Record data
        cost_tracker.record_request("service1", cost_usd=1.00, token_count=100)
        cost_tracker.record_request("service2", cost_usd=2.00, token_count=200)
        
        # Reset all
        cost_tracker.reset_metrics()
        
        # Check that all metrics are cleared
        assert len(cost_tracker.daily_metrics) == 0
        assert len(cost_tracker.hourly_metrics) == 0
        assert len(cost_tracker.alerts_sent) == 0


class TestCostTrackerIntegration:
    """Integration test scenarios for CostTracker."""
    
    @pytest.fixture
    def integration_tracker(self):
        """Create a CostTracker with configured limits for integration testing."""
        tracker = CostTracker()
        
        # Configure limits
        tracker.configure_service_limits("llamaparse", 10.00, 100, 80.0)
        tracker.configure_service_limits("openai", 20.00, 1000, 80.0)
        
        return tracker
    
    def test_complete_workflow(self, integration_tracker):
        """Test complete cost tracking workflow."""
        # Record requests
        integration_tracker.record_request("llamaparse", 0.50, 100, True)
        integration_tracker.record_request("openai", 1.00, 500, True)
        integration_tracker.record_request("llamaparse", 0.25, 50, False)
        
        # Check limits
        assert integration_tracker.check_cost_limit("llamaparse", 5.00) is True
        assert integration_tracker.check_cost_limit("openai", 15.00) is True
        
        # Get usage reports
        llamaparse_usage = integration_tracker.get_service_usage("llamaparse")
        openai_usage = integration_tracker.get_service_usage("openai")
        
        assert llamaparse_usage['total_cost_usd'] == 0.75
        assert llamaparse_usage['total_requests'] == 2
        assert llamaparse_usage['total_errors'] == 1
        
        assert openai_usage['total_cost_usd'] == 1.00
        assert openai_usage['total_requests'] == 1
        assert openai_usage['total_errors'] == 0
        
        # Get summary
        summary = integration_tracker.get_all_services_summary()
        assert summary['total_cost_usd'] == 1.75
        assert summary['total_requests'] == 3
        assert len(summary['services']) == 2
    
    def test_limit_enforcement_workflow(self, integration_tracker):
        """Test cost limit enforcement workflow."""
        # Record requests up to limit
        for i in range(10):
            integration_tracker.record_request("llamaparse", 1.00, 100, True)
        
        # Check if additional request would exceed limit
        assert integration_tracker.check_cost_limit("llamaparse", 1.00) is False
        
        # Check usage
        usage = integration_tracker.get_service_usage("llamaparse")
        assert usage['total_cost_usd'] == 10.00
        assert usage['total_requests'] == 10


class TestGlobalFunctions:
    """Test cases for global functions."""
    
    def test_get_cost_tracker_singleton(self):
        """Test that get_cost_tracker returns the same instance."""
        tracker1 = get_cost_tracker()
        tracker2 = get_cost_tracker()
        
        assert tracker1 is tracker2
    
    def test_configure_default_limits(self):
        """Test default limit configuration."""
        configure_default_limits()
        
        tracker = get_cost_tracker()
        assert "llamaparse" in tracker.cost_limits
        assert "openai" in tracker.cost_limits
        
        llamaparse_limit = tracker.cost_limits["llamaparse"]
        assert llamaparse_limit.daily_limit_usd == 10.00
        assert llamaparse_limit.hourly_rate_limit == 100
        
        openai_limit = tracker.cost_limits["openai"]
        assert openai_limit.daily_limit_usd == 20.00
        assert openai_limit.hourly_rate_limit == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
