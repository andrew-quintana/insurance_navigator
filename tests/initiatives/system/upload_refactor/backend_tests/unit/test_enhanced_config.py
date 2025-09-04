"""
Unit tests for the enhanced configuration management system.

Tests configuration loading, validation, and service mode management.
"""

import pytest
import os
from unittest.mock import patch, Mock
from datetime import datetime

from backend.shared.config.enhanced_config import (
    EnhancedConfig, LlamaParseConfig, OpenAIConfig, CostControlConfig, ServiceHealthConfig,
    ServiceMode, ConfigurationError, ServiceConfigurationError, get_config, reload_config
)


class TestServiceMode:
    """Test cases for ServiceMode enum."""
    
    def test_service_mode_values(self):
        """Test service mode enum values."""
        assert ServiceMode.MOCK.value == "mock"
        assert ServiceMode.REAL.value == "real"
        assert ServiceMode.HYBRID.value == "hybrid"
    
    def test_service_mode_comparison(self):
        """Test service mode comparison."""
        assert ServiceMode.MOCK != ServiceMode.REAL
        assert ServiceMode.HYBRID != ServiceMode.MOCK
        assert ServiceMode.REAL != ServiceMode.HYBRID


class TestLlamaParseConfig:
    """Test cases for LlamaParseConfig dataclass."""
    
    @patch.dict(os.environ, {
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'LLAMAPARSE_BASE_URL': 'https://test.api.com',
        'LLAMAPARSE_WEBHOOK_SECRET': 'test_secret_456',
        'DAILY_COST_LIMIT_LLAMAPARSE': '15.50',
        'HOURLY_RATE_LIMIT_LLAMAPARSE': '150',
        'LLAMAPARSE_TIMEOUT_SECONDS': '600',
        'LLAMAPARSE_RETRY_ATTEMPTS': '5',
        'LLAMAPARSE_RETRY_DELAY_SECONDS': '10'
    })
    def test_from_environment_with_all_values(self):
        """Test LlamaParseConfig creation from environment with all values."""
        config = LlamaParseConfig.from_environment()
        
        assert config.api_key == 'test_key_123'
        assert config.base_url == 'https://test.api.com'
        assert config.webhook_secret == 'test_secret_456'
        assert config.daily_cost_limit_usd == 15.50
        assert config.hourly_rate_limit == 150
        assert config.timeout_seconds == 600
        assert config.retry_attempts == 5
        assert config.retry_delay_seconds == 10
    
    @patch.dict(os.environ, {}, clear=True)
    def test_from_environment_with_defaults(self):
        """Test LlamaParseConfig creation from environment with defaults."""
        config = LlamaParseConfig.from_environment()
        
        assert config.api_key == ''
        assert config.base_url == 'https://api.cloud.llamaindex.ai'
        assert config.webhook_secret == ''
        assert config.daily_cost_limit_usd == 10.00
        assert config.hourly_rate_limit == 100
        assert config.timeout_seconds == 300
        assert config.retry_attempts == 3
        assert config.retry_delay_seconds == 5
    
    def test_validation_success(self):
        """Test successful configuration validation."""
        config = LlamaParseConfig(
            api_key='valid_key',
            base_url='https://valid.url',
            webhook_secret='valid_secret',
            daily_cost_limit_usd=20.00,
            hourly_rate_limit=200
        )
        
        assert config.validate() is True
    
    def test_validation_missing_api_key(self):
        """Test validation failure with missing API key."""
        config = LlamaParseConfig(
            api_key='',
            base_url='https://valid.url',
            webhook_secret='valid_secret'
        )
        
        assert config.validate() is False
    
    def test_validation_missing_base_url(self):
        """Test validation failure with missing base URL."""
        config = LlamaParseConfig(
            api_key='valid_key',
            base_url='',
            webhook_secret='valid_secret'
        )
        
        assert config.validate() is False
    
    def test_validation_invalid_daily_cost_limit(self):
        """Test validation failure with invalid daily cost limit."""
        config = LlamaParseConfig(
            api_key='valid_key',
            base_url='https://valid.url',
            webhook_secret='valid_secret',
            daily_cost_limit_usd=-5.00
        )
        
        assert config.validate() is False
    
    def test_validation_invalid_hourly_rate_limit(self):
        """Test validation failure with invalid hourly rate limit."""
        config = LlamaParseConfig(
            api_key='valid_key',
            base_url='https://valid.url',
            webhook_secret='valid_secret',
            hourly_rate_limit=0
        )
        
        assert config.validate() is False


class TestOpenAIConfig:
    """Test cases for OpenAIConfig dataclass."""
    
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'sk-test-key-123',
        'OPENAI_EMBEDDING_MODEL': 'text-embedding-3-large',
        'DAILY_COST_LIMIT_OPENAI': '25.00',
        'HOURLY_RATE_LIMIT_OPENAI': '2000',
        'OPENAI_TIMEOUT_SECONDS': '120',
        'OPENAI_RETRY_ATTEMPTS': '5',
        'OPENAI_RETRY_DELAY_SECONDS': '10',
        'OPENAI_MAX_BATCH_SIZE': '128'
    })
    def test_from_environment_with_all_values(self):
        """Test OpenAIConfig creation from environment with all values."""
        config = OpenAIConfig.from_environment()
        
        assert config.api_key == 'sk-test-key-123'
        assert config.model == 'text-embedding-3-large'
        assert config.daily_cost_limit_usd == 25.00
        assert config.hourly_rate_limit == 2000
        assert config.timeout_seconds == 120
        assert config.retry_attempts == 5
        assert config.retry_delay_seconds == 10
        assert config.max_batch_size == 128
    
    @patch.dict(os.environ, {}, clear=True)
    def test_from_environment_with_defaults(self):
        """Test OpenAIConfig creation from environment with defaults."""
        config = OpenAIConfig.from_environment()
        
        assert config.api_key == ''
        assert config.model == 'text-embedding-3-small'
        assert config.daily_cost_limit_usd == 20.00
        assert config.hourly_rate_limit == 1000
        assert config.timeout_seconds == 60
        assert config.retry_attempts == 3
        assert config.retry_delay_seconds == 5
        assert config.max_batch_size == 256
    
    def test_validation_success(self):
        """Test successful configuration validation."""
        config = OpenAIConfig(
            api_key='valid_key',
            daily_cost_limit_usd=30.00,
            hourly_rate_limit=1500,
            max_batch_size=128
        )
        
        assert config.validate() is True
    
    def test_validation_missing_api_key(self):
        """Test validation failure with missing API key."""
        config = OpenAIConfig(api_key='')
        assert config.validate() is False
    
    def test_validation_invalid_daily_cost_limit(self):
        """Test validation failure with invalid daily cost limit."""
        config = OpenAIConfig(
            api_key='valid_key',
            daily_cost_limit_usd=-10.00
        )
        assert config.validate() is False
    
    def test_validation_invalid_hourly_rate_limit(self):
        """Test validation failure with invalid hourly rate limit."""
        config = OpenAIConfig(
            api_key='valid_key',
            hourly_rate_limit=0
        )
        assert config.validate() is False
    
    def test_validation_invalid_batch_size_zero(self):
        """Test validation failure with zero batch size."""
        config = OpenAIConfig(
            api_key='valid_key',
            max_batch_size=0
        )
        assert config.validate() is False
    
    def test_validation_invalid_batch_size_too_large(self):
        """Test validation failure with batch size too large."""
        config = OpenAIConfig(
            api_key='valid_key',
            max_batch_size=300
        )
        assert config.validate() is False


class TestCostControlConfig:
    """Test cases for CostControlConfig dataclass."""
    
    @patch.dict(os.environ, {
        'COST_TRACKING_ENABLED': 'true',
        'DAILY_COST_LIMIT_TOTAL': '50.00',
        'COST_ALERT_THRESHOLD_PERCENT': '90.0',
        'COST_TRACKING_RETENTION_DAYS': '60'
    })
    def test_from_environment_with_all_values(self):
        """Test CostControlConfig creation from environment with all values."""
        config = CostControlConfig.from_environment()
        
        assert config.enabled is True
        assert config.daily_total_limit_usd == 50.00
        assert config.alert_threshold_percent == 90.0
        assert config.tracking_retention_days == 60
    
    @patch.dict(os.environ, {}, clear=True)
    def test_from_environment_with_defaults(self):
        """Test CostControlConfig creation from environment with defaults."""
        config = CostControlConfig.from_environment()
        
        assert config.enabled is True
        assert config.daily_total_limit_usd == 25.00
        assert config.alert_threshold_percent == 80.0
        assert config.tracking_retention_days == 30
    
    def test_validation_success(self):
        """Test successful configuration validation."""
        config = CostControlConfig(
            daily_total_limit_usd=100.00,
            alert_threshold_percent=75.0,
            tracking_retention_days=45
        )
        
        assert config.validate() is True
    
    def test_validation_invalid_daily_limit(self):
        """Test validation failure with invalid daily limit."""
        config = CostControlConfig(daily_total_limit_usd=-10.00)
        assert config.validate() is False
    
    def test_validation_invalid_alert_threshold_zero(self):
        """Test validation failure with zero alert threshold."""
        config = CostControlConfig(alert_threshold_percent=0.0)
        assert config.validate() is False
    
    def test_validation_invalid_alert_threshold_over_100(self):
        """Test validation failure with alert threshold over 100."""
        config = CostControlConfig(alert_threshold_percent=150.0)
        assert config.validate() is False
    
    def test_validation_invalid_retention_days(self):
        """Test validation failure with invalid retention days."""
        config = CostControlConfig(tracking_retention_days=0)
        assert config.validate() is False


class TestServiceHealthConfig:
    """Test cases for ServiceHealthConfig dataclass."""
    
    @patch.dict(os.environ, {
        'SERVICE_HEALTH_MONITORING_ENABLED': 'true',
        'SERVICE_HEALTH_CHECK_INTERVAL': '60',
        'SERVICE_FALLBACK_ENABLED': 'true',
        'SERVICE_FALLBACK_TIMEOUT': '20',
        'SERVICE_HEALTH_CHECK_TIMEOUT': '10'
    })
    def test_from_environment_with_all_values(self):
        """Test ServiceHealthConfig creation from environment with all values."""
        config = ServiceHealthConfig.from_environment()
        
        assert config.enabled is True
        assert config.check_interval_seconds == 60
        assert config.fallback_enabled is True
        assert config.fallback_timeout_seconds == 20
        assert config.health_check_timeout_seconds == 10
    
    @patch.dict(os.environ, {}, clear=True)
    def test_from_environment_with_defaults(self):
        """Test ServiceHealthConfig creation from environment with defaults."""
        config = ServiceHealthConfig.from_environment()
        
        assert config.enabled is True
        assert config.check_interval_seconds == 30
        assert config.fallback_enabled is True
        assert config.fallback_timeout_seconds == 10
        assert config.health_check_timeout_seconds == 5
    
    def test_validation_success(self):
        """Test successful configuration validation."""
        config = ServiceHealthConfig(
            check_interval_seconds=45,
            fallback_timeout_seconds=15,
            health_check_timeout_seconds=8
        )
        
        assert config.validate() is True
    
    def test_validation_invalid_check_interval(self):
        """Test validation failure with invalid check interval."""
        config = ServiceHealthConfig(check_interval_seconds=0)
        assert config.validate() is False
    
    def test_validation_invalid_fallback_timeout(self):
        """Test validation failure with invalid fallback timeout."""
        config = ServiceHealthConfig(fallback_timeout_seconds=-5)
        assert config.validate() is False
    
    def test_validation_invalid_health_check_timeout(self):
        """Test validation failure with invalid health check timeout."""
        config = ServiceHealthConfig(health_check_timeout_seconds=0)
        assert config.validate() is False


class TestEnhancedConfig:
    """Test cases for EnhancedConfig class."""
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'hybrid',
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'LLAMAPARSE_BASE_URL': 'https://test.api.com',
        'LLAMAPARSE_WEBHOOK_SECRET': 'test_secret_456',
        'OPENAI_API_KEY': 'sk-test-key-123',
        'COST_TRACKING_ENABLED': 'true',
        'DAILY_COST_LIMIT_TOTAL': '50.00'
    })
    def test_initialization_success(self):
        """Test successful configuration initialization."""
        config = EnhancedConfig()
        
        assert config.service_mode == ServiceMode.HYBRID
        assert config.llamaparse.api_key == 'test_key_123'
        assert config.openai.api_key == 'sk-test-key-123'
        assert config.cost_control.enabled is True
        assert config.service_health.enabled is True
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'invalid_mode',
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'OPENAI_API_KEY': 'sk-test-key-123'
    })
    def test_initialization_invalid_service_mode(self):
        """Test initialization with invalid service mode."""
        config = EnhancedConfig()
        
        # Should default to HYBRID mode
        assert config.service_mode == ServiceMode.HYBRID
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'real',
        'LLAMAPARSE_API_KEY': '',  # Missing API key
        'OPENAI_API_KEY': 'sk-test-key-123'
    })
    def test_initialization_missing_api_keys_real_mode(self):
        """Test initialization with missing API keys in REAL mode."""
        with pytest.raises(ConfigurationError):
            EnhancedConfig()
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'mock',
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'OPENAI_API_KEY': 'sk-test-key-123'
    })
    def test_initialization_mock_mode(self):
        """Test initialization in MOCK mode."""
        config = EnhancedConfig()
        
        assert config.service_mode == ServiceMode.MOCK
        assert config.is_mock_mode() is True
        assert config.is_real_mode() is False
        assert config.is_hybrid_mode() is False
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'real',
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'OPENAI_API_KEY': 'sk-test-key-123'
    })
    def test_initialization_real_mode(self):
        """Test initialization in REAL mode."""
        config = EnhancedConfig()
        
        assert config.service_mode == ServiceMode.REAL
        assert config.is_mock_mode() is False
        assert config.is_real_mode() is True
        assert config.is_hybrid_mode() is False
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'hybrid',
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'OPENAI_API_KEY': 'sk-test-key-123'
    })
    def test_initialization_hybrid_mode(self):
        """Test initialization in HYBRID mode."""
        config = EnhancedConfig()
        
        assert config.service_mode == ServiceMode.HYBRID
        assert config.is_mock_mode() is False
        assert config.is_real_mode() is False
        assert config.is_hybrid_mode() is True
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'hybrid',
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'OPENAI_API_KEY': 'sk-test-key-123'
    })
    def test_can_use_real_service(self):
        """Test real service availability checking."""
        config = EnhancedConfig()
        
        assert config.can_use_real_service('llamaparse') is True
        assert config.can_use_real_service('openai') is True
        assert config.can_use_real_service('unknown_service') is False
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'mock',
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'OPENAI_API_KEY': 'sk-test-key-123'
    })
    def test_can_use_real_service_mock_mode(self):
        """Test real service availability in MOCK mode."""
        config = EnhancedConfig()
        
        assert config.can_use_real_service('llamaparse') is False
        assert config.can_use_real_service('openai') is False
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'hybrid',
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'LLAMAPARSE_BASE_URL': 'https://test.api.com',
        'OPENAI_API_KEY': 'sk-test-key-123'
    })
    def test_get_service_urls(self):
        """Test service URL retrieval."""
        config = EnhancedConfig()
        
        urls = config.get_service_urls()
        
        assert 'llamaparse' in urls
        assert 'openai' in urls
        assert urls['llamaparse'] == 'https://test.api.com'
        assert urls['openai'] == 'https://api.openai.com'
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'mock',
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'OPENAI_API_KEY': 'sk-test-key-123'
    })
    def test_get_service_urls_mock_mode(self):
        """Test service URL retrieval in MOCK mode."""
        config = EnhancedConfig()
        
        urls = config.get_service_urls()
        
        assert urls['llamaparse'] == 'http://mock-llamaparse:8001'
        assert urls['openai'] == 'http://mock-openai:8002'
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'hybrid',
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'LLAMAPARSE_BASE_URL': 'https://test.api.com',
        'LLAMAPARSE_WEBHOOK_SECRET': 'test_secret_456',
        'OPENAI_API_KEY': 'sk-test-key-123'
    })
    def test_get_service_config(self):
        """Test service configuration retrieval."""
        config = EnhancedConfig()
        
        llamaparse_config = config.get_service_config('llamaparse')
        assert llamaparse_config['api_key'] == 'test_key_123'
        assert llamaparse_config['base_url'] == 'https://test.api.com'
        assert llamaparse_config['webhook_secret'] == 'test_secret_456'
        
        openai_config = config.get_service_config('openai')
        assert openai_config['api_key'] == 'sk-test-key-123'
        assert openai_config['model'] == 'text-embedding-3-small'
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'hybrid',
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'OPENAI_API_KEY': 'sk-test-key-123'
    })
    def test_get_service_config_unknown_service(self):
        """Test service configuration retrieval for unknown service."""
        config = EnhancedConfig()
        
        with pytest.raises(ValueError):
            config.get_service_config('unknown_service')
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'hybrid',
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'OPENAI_API_KEY': 'sk-test-key-123'
    })
    def test_get_cost_limits(self):
        """Test cost limits retrieval."""
        config = EnhancedConfig()
        
        cost_limits = config.get_cost_limits()
        
        assert 'llamaparse' in cost_limits
        assert 'openai' in cost_limits
        assert 'total' in cost_limits
        
        assert cost_limits['llamaparse']['daily_limit_usd'] == 10.00
        assert cost_limits['openai']['daily_limit_usd'] == 20.00
        assert cost_limits['total']['daily_limit_usd'] == 25.00
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'hybrid',
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'OPENAI_API_KEY': 'sk-test-key-123'
    })
    def test_to_dict(self):
        """Test configuration serialization to dictionary."""
        config = EnhancedConfig()
        
        config_dict = config.to_dict()
        
        assert config_dict['service_mode'] == 'hybrid'
        assert 'cost_control' in config_dict
        assert 'service_health' in config_dict
        assert 'llamaparse' in config_dict
        assert 'openai' in config_dict
        
        # Verify sensitive data is not exposed
        assert 'api_key' not in config_dict['llamaparse']
        assert 'api_key' not in config_dict['openai']
        assert 'webhook_secret' not in config_dict['llamaparse']


class TestGlobalFunctions:
    """Test cases for global functions."""
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'hybrid',
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'LLAMAPARSE_BASE_URL': 'https://test.api.com',
        'LLAMAPARSE_WEBHOOK_SECRET': 'test_secret_456',
        'OPENAI_API_KEY': 'sk-test-key-123'
    })
    def test_get_config_singleton(self):
        """Test that get_config returns the same instance."""
        # Clear any existing instance
        import backend.shared.config.enhanced_config as config_module
        config_module._config_instance = None
        
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'hybrid',
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'OPENAI_API_KEY': 'sk-test-key-123'
    })
    def test_reload_config(self):
        """Test configuration reloading."""
        # Get initial config
        config1 = get_config()
        
        # Reload config
        config2 = reload_config()
        
        # Should be different instances
        assert config1 is not config2
        
        # But should have same values
        assert config1.service_mode == config2.service_mode
        assert config1.llamaparse.api_key == config2.llamaparse.api_key


class TestConfigurationErrorHandling:
    """Test error handling scenarios."""
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'hybrid',
        'LLAMAPARSE_API_KEY': '',  # Missing API key
        'OPENAI_API_KEY': 'sk-test-key-123'
    })
    def test_llamaparse_validation_failure(self):
        """Test configuration validation failure for LlamaParse."""
        with pytest.raises(ConfigurationError) as exc_info:
            EnhancedConfig()
        
        error_message = str(exc_info.value)
        assert "LlamaParse configuration validation failed" in error_message
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'hybrid',
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'OPENAI_API_KEY': '',  # Missing API key
        'DAILY_COST_LIMIT_OPENAI': '-10.00'  # Invalid cost limit
    })
    def test_openai_validation_failure(self):
        """Test configuration validation failure for OpenAI."""
        with pytest.raises(ConfigurationError) as exc_info:
            EnhancedConfig()
        
        error_message = str(exc_info.value)
        assert "OpenAI configuration validation failed" in error_message
    
    @patch.dict(os.environ, {
        'SERVICE_MODE': 'hybrid',
        'LLAMAPARSE_API_KEY': 'test_key_123',
        'OPENAI_API_KEY': 'sk-test-key-123',
        'DAILY_COST_LIMIT_TOTAL': '-5.00'  # Invalid total cost limit
    })
    def test_cost_control_validation_failure(self):
        """Test configuration validation failure for cost control."""
        with pytest.raises(ConfigurationError) as exc_info:
            EnhancedConfig()
        
        error_message = str(exc_info.value)
        assert "Cost control configuration validation failed" in error_message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
