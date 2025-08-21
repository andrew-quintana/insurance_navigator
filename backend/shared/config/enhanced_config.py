"""
Enhanced configuration management for real service integration.

This module provides secure configuration management for external service
credentials, cost limits, and service mode settings.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceMode(Enum):
    """Service operation modes."""
    MOCK = "mock"
    REAL = "real"
    HYBRID = "hybrid"


@dataclass
class LlamaParseConfig:
    """LlamaParse service configuration."""
    api_key: str
    base_url: str
    webhook_secret: str
    daily_cost_limit_usd: float = 10.00
    hourly_rate_limit: int = 100
    timeout_seconds: int = 300
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    
    @classmethod
    def from_environment(cls) -> 'LlamaParseConfig':
        """Create configuration from environment variables."""
        return cls(
            api_key=os.getenv('LLAMAPARSE_API_KEY', ''),
            base_url=os.getenv('LLAMAPARSE_BASE_URL', 'https://api.cloud.llamaindex.ai'),
            webhook_secret=os.getenv('LLAMAPARSE_WEBHOOK_SECRET', ''),
            daily_cost_limit_usd=float(os.getenv('DAILY_COST_LIMIT_LLAMAPARSE', '10.00')),
            hourly_rate_limit=int(os.getenv('HOURLY_RATE_LIMIT_LLAMAPARSE', '100')),
            timeout_seconds=int(os.getenv('LLAMAPARSE_TIMEOUT_SECONDS', '300')),
            retry_attempts=int(os.getenv('LLAMAPARSE_RETRY_ATTEMPTS', '3')),
            retry_delay_seconds=int(os.getenv('LLAMAPARSE_RETRY_DELAY_SECONDS', '5'))
        )
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        if not self.api_key:
            logger.error("LlamaParse API key is required")
            return False
        
        if not self.base_url:
            logger.error("LlamaParse base URL is required")
            return False
        
        if self.daily_cost_limit_usd <= 0:
            logger.error("Daily cost limit must be positive")
            return False
        
        if self.hourly_rate_limit <= 0:
            logger.error("Hourly rate limit must be positive")
            return False
        
        return True


@dataclass
class OpenAIConfig:
    """OpenAI service configuration."""
    api_key: str
    model: str = "text-embedding-3-small"
    daily_cost_limit_usd: float = 20.00
    hourly_rate_limit: int = 1000
    timeout_seconds: int = 60
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    max_batch_size: int = 256
    
    @classmethod
    def from_environment(cls) -> 'OpenAIConfig':
        """Create configuration from environment variables."""
        return cls(
            api_key=os.getenv('OPENAI_API_KEY', ''),
            model=os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small'),
            daily_cost_limit_usd=float(os.getenv('DAILY_COST_LIMIT_OPENAI', '20.00')),
            hourly_rate_limit=int(os.getenv('HOURLY_RATE_LIMIT_OPENAI', '1000')),
            timeout_seconds=int(os.getenv('OPENAI_TIMEOUT_SECONDS', '60')),
            retry_attempts=int(os.getenv('OPENAI_RETRY_ATTEMPTS', '3')),
            retry_delay_seconds=int(os.getenv('OPENAI_RETRY_DELAY_SECONDS', '5')),
            max_batch_size=int(os.getenv('OPENAI_MAX_BATCH_SIZE', '256'))
        )
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        if not self.api_key:
            logger.error("OpenAI API key is required")
            return False
        
        if self.daily_cost_limit_usd <= 0:
            logger.error("Daily cost limit must be positive")
            return False
        
        if self.hourly_rate_limit <= 0:
            logger.error("Hourly rate limit must be positive")
            return False
        
        if self.max_batch_size <= 0 or self.max_batch_size > 256:
            logger.error("Max batch size must be between 1 and 256")
            return False
        
        return True


@dataclass
class CostControlConfig:
    """Cost control configuration."""
    enabled: bool = True
    daily_total_limit_usd: float = 25.00
    alert_threshold_percent: float = 80.0
    tracking_retention_days: int = 30
    
    @classmethod
    def from_environment(cls) -> 'CostControlConfig':
        """Create configuration from environment variables."""
        return cls(
            enabled=os.getenv('COST_TRACKING_ENABLED', 'true').lower() == 'true',
            daily_total_limit_usd=float(os.getenv('DAILY_COST_LIMIT_TOTAL', '25.00')),
            alert_threshold_percent=float(os.getenv('COST_ALERT_THRESHOLD_PERCENT', '80.0')),
            tracking_retention_days=int(os.getenv('COST_TRACKING_RETENTION_DAYS', '30'))
        )
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        if self.daily_total_limit_usd <= 0:
            logger.error("Daily total cost limit must be positive")
            return False
        
        if not (0 < self.alert_threshold_percent <= 100):
            logger.error("Alert threshold must be between 0 and 100")
            return False
        
        if self.tracking_retention_days <= 0:
            logger.error("Tracking retention days must be positive")
            return False
        
        return True


@dataclass
class ServiceHealthConfig:
    """Service health monitoring configuration."""
    enabled: bool = True
    check_interval_seconds: int = 30
    fallback_enabled: bool = True
    timeout_seconds: int = 10
    max_retries: int = 3
    
    @classmethod
    def from_environment(cls) -> 'ServiceHealthConfig':
        """Create configuration from environment variables."""
        return cls(
            enabled=os.getenv('SERVICE_HEALTH_ENABLED', 'true').lower() == 'true',
            check_interval_seconds=int(os.getenv('SERVICE_HEALTH_CHECK_INTERVAL_SECONDS', '30')),
            fallback_enabled=os.getenv('SERVICE_HEALTH_FALLBACK_ENABLED', 'true').lower() == 'true',
            timeout_seconds=int(os.getenv('SERVICE_HEALTH_TIMEOUT_SECONDS', '10')),
            max_retries=int(os.getenv('SERVICE_HEALTH_MAX_RETRIES', '3'))
        )
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        if self.check_interval_seconds <= 0:
            logger.error("Service health check interval must be positive")
            return False
        
        if self.timeout_seconds <= 0:
            logger.error("Service health timeout must be positive")
            return False
        
        if self.max_retries < 0:
            logger.error("Service health max retries must be non-negative")
            return False
        
        return True


@dataclass
class UploadConfig:
    """Upload configuration for document processing."""
    max_file_size_bytes: int = 25 * 1024 * 1024  # 25MB
    max_pages: int = 100
    max_concurrent_jobs_per_user: int = 2
    max_uploads_per_day_per_user: int = 30
    supported_mime_types: list = None
    
    def __post_init__(self):
        if self.supported_mime_types is None:
            self.supported_mime_types = ["application/pdf"]
    
    @classmethod
    def from_environment(cls) -> 'UploadConfig':
        """Create configuration from environment variables."""
        return cls(
            max_file_size_bytes=int(os.getenv('MAX_FILE_SIZE_BYTES', '26214400')),  # 25MB
            max_pages=int(os.getenv('MAX_PAGES', '100')),
            max_concurrent_jobs_per_user=int(os.getenv('MAX_CONCURRENT_JOBS_PER_USER', '2')),
            max_uploads_per_day_per_user=int(os.getenv('MAX_UPLOADS_PER_DAY_PER_USER', '30'))
        )
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        if self.max_file_size_bytes <= 0:
            logger.error("Max file size must be positive")
            return False
        
        if self.max_pages <= 0:
            logger.error("Max pages must be positive")
            return False
        
        if self.max_concurrent_jobs_per_user <= 0:
            logger.error("Max concurrent jobs per user must be positive")
            return False
        
        if self.max_uploads_per_day_per_user <= 0:
            logger.error("Max uploads per day per user must be positive")
            return False
        
        return True


@dataclass
class StorageConfig:
    """Storage configuration for document storage."""
    url: str = "http://localhost:5000"
    anon_key: str = ""
    service_role_key: str = ""
    raw_bucket: str = "raw"
    parsed_bucket: str = "parsed"
    signed_url_ttl_seconds: int = 300  # 5 minutes
    timeout: int = 60
    
    @classmethod
    def from_environment(cls) -> 'StorageConfig':
        """Create configuration from environment variables."""
        return cls(
            url=os.getenv('SUPABASE_URL', 'http://localhost:5000'),
            anon_key=os.getenv('SUPABASE_ANON_KEY', ''),
            service_role_key=os.getenv('SUPABASE_SERVICE_ROLE_KEY', ''),
            raw_bucket=os.getenv('STORAGE_RAW_BUCKET', 'raw'),
            parsed_bucket=os.getenv('STORAGE_PARSED_BUCKET', 'parsed'),
            signed_url_ttl_seconds=int(os.getenv('STORAGE_SIGNED_URL_TTL_SECONDS', '300')),
            timeout=int(os.getenv('STORAGE_TIMEOUT_SECONDS', '60'))
        )
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        if not self.url:
            logger.error("Storage URL is required")
            return False
        
        if self.signed_url_ttl_seconds <= 0:
            logger.error("Signed URL TTL must be positive")
            return False
        
        if self.timeout <= 0:
            logger.error("Storage timeout must be positive")
            return False
        
        return True


@dataclass
class DatabaseConfig:
    """Database configuration for document processing."""
    url: str = "postgresql://postgres:postgres@localhost:5432/accessa_dev"
    max_connections: int = 10
    connection_timeout: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    @classmethod
    def from_environment(cls) -> 'DatabaseConfig':
        """Create configuration from environment variables."""
        return cls(
            url=os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/accessa_dev'),
            max_connections=int(os.getenv('DATABASE_MAX_CONNECTIONS', '10')),
            connection_timeout=int(os.getenv('DATABASE_CONNECTION_TIMEOUT', '30')),
            pool_timeout=int(os.getenv('DATABASE_POOL_TIMEOUT', '30')),
            pool_recycle=int(os.getenv('DATABASE_POOL_RECYCLE', '3600'))
        )
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        if not self.url:
            logger.error("Database URL is required")
            return False
        
        if self.max_connections <= 0:
            logger.error("Max connections must be positive")
            return False
        
        if self.connection_timeout <= 0:
            logger.error("Connection timeout must be positive")
            return False
        
        if self.pool_timeout <= 0:
            logger.error("Pool timeout must be positive")
            return False
        
        return True


class EnhancedConfig:
    """
    Enhanced configuration manager for real service integration.
    
    Provides secure configuration management with validation and
    environment variable integration.
    """
    
    def __init__(self):
        self.service_mode = self._get_service_mode()
        self.llamaparse = LlamaParseConfig.from_environment()
        self.openai = OpenAIConfig.from_environment()
        self.cost_control = CostControlConfig.from_environment()
        self.service_health = ServiceHealthConfig.from_environment()
        self.upload = UploadConfig.from_environment()
        self.storage = StorageConfig.from_environment()
        self.database = DatabaseConfig.from_environment()
        
        # Validate configuration
        self._validate_configuration()
        
        # Configure logging
        self._configure_logging()
    
    def _get_service_mode(self) -> ServiceMode:
        """Get service mode from environment variables."""
        mode_str = os.getenv('SERVICE_MODE', 'hybrid').lower()
        
        try:
            return ServiceMode(mode_str)
        except ValueError:
            logger.warning(f"Invalid service mode '{mode_str}', defaulting to HYBRID")
            return ServiceMode.HYBRID
    
    def _validate_configuration(self) -> None:
        """Validate all configuration components."""
        validation_errors = []
        
        # Validate service mode
        if self.service_mode not in ServiceMode:
            validation_errors.append(f"Invalid service mode: {self.service_mode}")
        
        # Validate service configurations
        if not self.llamaparse.validate():
            validation_errors.append("LlamaParse configuration validation failed")
        
        if not self.openai.validate():
            validation_errors.append("OpenAI configuration validation failed")
        
        if not self.cost_control.validate():
            validation_errors.append("Cost control configuration validation failed")
        
        if not self.service_health.validate():
            validation_errors.append("Service health configuration validation failed")
        
        if not self.upload.validate():
            validation_errors.append("Upload configuration validation failed")
        
        if not self.storage.validate():
            validation_errors.append("Storage configuration validation failed")
        
        if not self.database.validate():
            validation_errors.append("Database configuration validation failed")
        
        # Check for configuration conflicts
        if self.service_mode == ServiceMode.REAL:
            if not self.llamaparse.api_key or not self.openai.api_key:
                validation_errors.append("API keys required for REAL service mode")
        
        if validation_errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(validation_errors)
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        
        logger.info("Configuration validation passed")
    
    def _configure_logging(self) -> None:
        """Configure logging based on service mode."""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # Set more verbose logging for development
        if self.service_mode == ServiceMode.HYBRID:
            log_level = max(log_level, 'DEBUG')
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logger.info(f"Logging configured at {log_level} level")
        logger.info(f"Service mode: {self.service_mode.value}")
    
    def get_service_urls(self) -> Dict[str, str]:
        """Get service URLs based on current mode."""
        if self.service_mode == ServiceMode.MOCK:
            return {
                'llamaparse': 'http://mock-llamaparse:8001',
                'openai': 'http://mock-openai:8002'
            }
        elif self.service_mode == ServiceMode.REAL:
            return {
                'llamaparse': self.llamaparse.base_url,
                'openai': 'https://api.openai.com'
            }
        else:  # HYBRID mode
            return {
                'llamaparse': self.llamaparse.base_url,
                'openai': 'https://api.openai.com'
            }
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for a specific service."""
        if service_name == 'llamaparse':
            return {
                'api_key': self.llamaparse.api_key,
                'base_url': self.llamaparse.base_url,
                'webhook_secret': self.llamaparse.webhook_secret,
                'timeout_seconds': self.llamaparse.timeout_seconds,
                'retry_attempts': self.llamaparse.retry_attempts,
                'retry_delay_seconds': self.llamaparse.retry_delay_seconds
            }
        elif service_name == 'openai':
            return {
                'api_key': self.openai.api_key,
                'model': self.openai.model,
                'timeout_seconds': self.openai.timeout_seconds,
                'retry_attempts': self.openai.retry_attempts,
                'retry_delay_seconds': self.openai.retry_delay_seconds,
                'max_batch_size': self.openai.max_batch_size
            }
        else:
            raise ValueError(f"Unknown service: {service_name}")
    
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode."""
        return self.service_mode == ServiceMode.MOCK
    
    def is_real_mode(self) -> bool:
        """Check if running in real mode."""
        return self.service_mode == ServiceMode.REAL
    
    def is_hybrid_mode(self) -> bool:
        """Check if running in hybrid mode."""
        return self.service_mode == ServiceMode.HYBRID
    
    def can_use_real_service(self, service_name: str) -> bool:
        """Check if real service can be used."""
        if self.service_mode == ServiceMode.MOCK:
            return False
        
        if service_name == 'llamaparse':
            return bool(self.llamaparse.api_key)
        elif service_name == 'openai':
            return bool(self.openai.api_key)
        else:
            return False
    
    def get_cost_limits(self) -> Dict[str, Dict[str, Any]]:
        """Get cost limits for all services."""
        return {
            'llamaparse': {
                'daily_limit_usd': self.llamaparse.daily_cost_limit_usd,
                'hourly_rate_limit': self.llamaparse.hourly_rate_limit
            },
            'openai': {
                'daily_limit_usd': self.openai.daily_cost_limit_usd,
                'hourly_rate_limit': self.openai.hourly_rate_limit
            },
            'total': {
                'daily_limit_usd': self.cost_control.daily_total_limit_usd,
                'alert_threshold_percent': self.cost_control.alert_threshold_percent
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return {
            'service_mode': self.service_mode.value,
            'cost_control': {
                'enabled': self.cost_control.enabled,
                'daily_total_limit_usd': self.cost_control.daily_total_limit_usd,
                'alert_threshold_percent': self.cost_control.alert_threshold_percent
            },
            'service_health': {
                'enabled': self.service_health.enabled,
                'check_interval_seconds': self.service_health.check_interval_seconds,
                'fallback_enabled': self.service_health.fallback_enabled
            },
            'llamaparse': {
                'base_url': self.llamaparse.base_url,
                'daily_cost_limit_usd': self.llamaparse.daily_cost_limit_usd,
                'hourly_rate_limit': self.llamaparse.hourly_rate_limit,
                'timeout_seconds': self.llamaparse.timeout_seconds,
                'retry_attempts': self.llamaparse.retry_attempts
            },
            'openai': {
                'model': self.openai.model,
                'daily_cost_limit_usd': self.openai.daily_cost_limit_usd,
                'hourly_rate_limit': self.openai.hourly_rate_limit,
                'timeout_seconds': self.openai.timeout_seconds,
                'retry_attempts': self.openai.retry_attempts,
                'max_batch_size': self.openai.max_batch_size
            }
        }


# Exception classes

class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


class ServiceConfigurationError(Exception):
    """Raised when service-specific configuration is invalid."""
    pass


# Global configuration instance
_config_instance = None


def get_config() -> EnhancedConfig:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = EnhancedConfig()
    return _config_instance


def reload_config() -> EnhancedConfig:
    """Reload configuration from environment variables."""
    global _config_instance
    _config_instance = EnhancedConfig()
    return _config_instance
