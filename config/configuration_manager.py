"""
Centralized Configuration Manager for Insurance Navigator System

This module provides a centralized, environment-aware configuration system that handles
all service settings, feature flags, similarity thresholds, database connections, and
external API configurations across different deployment environments.
"""

import os
import logging
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from dotenv import load_dotenv

logger = logging.getLogger("ConfigurationManager")

class Environment(Enum):
    """Supported deployment environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    url: str
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = ""
    database: str = "postgres"
    schema: str = "upload_pipeline"
    
    def validate(self) -> bool:
        """Validate database configuration."""
        if not self.url and not all([self.host, self.user, self.database]):
            logger.error("Database configuration incomplete")
            return False
        return True

@dataclass
class RAGConfig:
    """RAG system configuration settings."""
    similarity_threshold: float = 0.3
    max_chunks: int = 10
    token_budget: int = 4000
    embedding_model: str = "text-embedding-3-small"
    vector_dimension: int = 1536
    enable_duplicate_chunk_check: bool = False
    
    def validate(self) -> bool:
        """Validate RAG configuration."""
        if not 0.0 < self.similarity_threshold <= 1.0:
            logger.error(f"Invalid similarity threshold: {self.similarity_threshold}")
            return False
        if self.max_chunks <= 0:
            logger.error(f"Invalid max_chunks: {self.max_chunks}")
            return False
        if self.token_budget <= 0:
            logger.error(f"Invalid token_budget: {self.token_budget}")
            return False
        return True

@dataclass
class APIConfig:
    """External API configuration settings."""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llamaparse_api_key: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    
    def validate(self) -> bool:
        """Validate API configuration."""
        required_keys = ["openai_api_key", "supabase_url", "supabase_service_role_key"]
        missing_keys = [key for key in required_keys if not getattr(self, key)]
        if missing_keys:
            logger.error(f"Missing required API keys: {missing_keys}")
            return False
        return True

@dataclass
class ServiceConfig:
    """Service-specific configuration settings."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"
    cors_origins: list = field(default_factory=list)
    
    def validate(self) -> bool:
        """Validate service configuration."""
        if self.port <= 0 or self.port > 65535:
            logger.error(f"Invalid port: {self.port}")
            return False
        return True

class ConfigurationManager:
    """
    Centralized configuration manager for the Insurance Navigator system.
    
    Provides environment-aware configuration loading, validation, and hot-reloading
    capabilities for all system components.
    """
    
    def __init__(self, environment: Optional[str] = None, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            environment: Target environment (development, testing, staging, production)
            config_path: Path to configuration files (defaults to project root)
        """
        self.environment = self._determine_environment(environment)
        self.config_path = config_path or os.getcwd()
        self._config_cache: Dict[str, Any] = {}
        
        # Load environment-specific configuration
        self._load_environment_config()
        
        # Initialize configuration sections
        self.database = self._load_database_config()
        self.rag = self._load_rag_config()
        self.api = self._load_api_config()
        self.service = self._load_service_config()
        
        # Validate all configurations
        self._validate_all_configs()
        
        logger.info(f"Configuration manager initialized for environment: {self.environment.value}")
    
    def _determine_environment(self, environment: Optional[str]) -> Environment:
        """Determine the target environment."""
        if environment:
            try:
                return Environment(environment.lower())
            except ValueError:
                logger.warning(f"Invalid environment '{environment}', defaulting to development")
                return Environment.DEVELOPMENT
        
        # Try to determine from environment variables
        env_var = os.getenv("NODE_ENV", "").lower()
        if env_var in [e.value for e in Environment]:
            return Environment(env_var)
        
        # Default to development
        return Environment.DEVELOPMENT
    
    def _load_environment_config(self) -> None:
        """Load environment-specific configuration files."""
        # Load base configuration
        base_env_file = os.path.join(self.config_path, ".env")
        if os.path.exists(base_env_file):
            load_dotenv(base_env_file)
            logger.debug(f"Loaded base configuration from {base_env_file}")
        
        # Load environment-specific configuration
        env_file = os.path.join(self.config_path, f".env.{self.environment.value}")
        if os.path.exists(env_file):
            load_dotenv(env_file, override=True)
            logger.debug(f"Loaded {self.environment.value} configuration from {env_file}")
        
        # Load production configuration if in production or testing
        # Testing environment uses production database as bridge between dev and prod
        if self.environment in [Environment.PRODUCTION, Environment.TESTING]:
            prod_env_file = os.path.join(self.config_path, ".env.production")
            if os.path.exists(prod_env_file):
                load_dotenv(prod_env_file, override=True)
                logger.debug(f"Loaded production configuration from {prod_env_file}")
        
        # Override with environment-specific defaults if not set in env files
        self._apply_environment_defaults()
    
    def _apply_environment_defaults(self) -> None:
        """Apply environment-specific defaults for critical settings."""
        # Force environment-specific values regardless of env files
        if self.environment == Environment.TESTING:
            os.environ["LOG_LEVEL"] = "WARNING"
            os.environ["DEBUG"] = "false"
        elif self.environment == Environment.DEVELOPMENT:
            os.environ["LOG_LEVEL"] = "DEBUG"
            os.environ["DEBUG"] = "true"
        elif self.environment == Environment.PRODUCTION:
            os.environ["LOG_LEVEL"] = "ERROR"
            os.environ["DEBUG"] = "false"
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration."""
        database_url = os.getenv("DATABASE_URL", "")
        
        if database_url:
            # For testing environment, use production database but test schema
            if self.environment == Environment.TESTING:
                # Override schema for testing to use test schema
                schema = os.getenv("TEST_DATABASE_SCHEMA", "upload_pipeline_test")
                return DatabaseConfig(url=database_url, schema=schema)
            return DatabaseConfig(url=database_url)
        
        # Fallback to individual parameters
        # For testing, use production database parameters but test schema
        if self.environment == Environment.TESTING:
            schema = os.getenv("TEST_DATABASE_SCHEMA", "upload_pipeline_test")
        else:
            schema = os.getenv("DATABASE_SCHEMA", "upload_pipeline")
            
        return DatabaseConfig(
            url="",
            host=os.getenv("SUPABASE_DB_HOST", "localhost"),
            port=int(os.getenv("SUPABASE_DB_PORT", "5432")),
            user=os.getenv("SUPABASE_DB_USER", "postgres"),
            password=os.getenv("SUPABASE_DB_PASSWORD", ""),
            database=os.getenv("SUPABASE_DB_NAME", "postgres"),
            schema=schema
        )
    
    def _load_rag_config(self) -> RAGConfig:
        """Load RAG configuration."""
        # Set environment-specific defaults
        if self.environment == Environment.TESTING:
            # Testing uses production-like settings but with reduced limits for faster testing
            default_max_chunks = "8"
            default_token_budget = "3000"
        elif self.environment == Environment.DEVELOPMENT:
            # Development uses standard settings
            default_max_chunks = "10"
            default_token_budget = "4000"
        else:  # PRODUCTION
            # Production uses optimized settings
            default_max_chunks = "10"
            default_token_budget = "4000"
            
        return RAGConfig(
            similarity_threshold=float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.3")),
            max_chunks=int(os.getenv("RAG_MAX_CHUNKS", default_max_chunks)),
            token_budget=int(os.getenv("RAG_TOKEN_BUDGET", default_token_budget)),
            embedding_model=os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-3-small"),
            vector_dimension=int(os.getenv("RAG_VECTOR_DIMENSION", "1536")),
            enable_duplicate_chunk_check=os.getenv("RAG_ENABLE_DUPLICATE_CHUNK_CHECK", "false").lower() == "true"
        )
    
    def _load_api_config(self) -> APIConfig:
        """Load API configuration."""
        return APIConfig(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            llamaparse_api_key=os.getenv("LLAMAPARSE_API_KEY", ""),
            supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        )
    
    def _load_service_config(self) -> ServiceConfig:
        """Load service configuration."""
        # Set environment-specific defaults
        if self.environment == Environment.TESTING:
            default_port = "8001"  # Different port for testing
            default_debug = "false"
            default_log_level = "WARNING"  # Less verbose logging for testing
        elif self.environment == Environment.DEVELOPMENT:
            default_port = "8000"
            default_debug = "true"
            default_log_level = "DEBUG"
        else:  # PRODUCTION
            default_port = "8000"
            default_debug = "false"
            default_log_level = "ERROR"
            
        return ServiceConfig(
            host=os.getenv("SERVICE_HOST", "0.0.0.0"),
            port=int(os.getenv("SERVICE_PORT", default_port)),
            debug=os.getenv("DEBUG", default_debug).lower() == "true",
            log_level=os.getenv("LOG_LEVEL", default_log_level),
            cors_origins=os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
        )
    
    def _validate_all_configs(self) -> None:
        """Validate all configuration sections."""
        configs = [
            ("database", self.database),
            ("rag", self.rag),
            ("api", self.api),
            ("service", self.service)
        ]
        
        for name, config in configs:
            if not config.validate():
                raise ValueError(f"Invalid {name} configuration")
        
        logger.info("All configurations validated successfully")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'rag.similarity_threshold')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if key in self._config_cache:
            return self._config_cache[key]
        
        # Support dot notation for nested access
        keys = key.split(".")
        value = self._config_cache
        
        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value[k]
                else:
                    value = getattr(value, k)
            return value
        except (KeyError, AttributeError):
            return default
    
    def set_config(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config_cache[key] = value
        logger.debug(f"Set configuration {key} = {value}")
    
    def reload_config(self) -> bool:
        """
        Reload configuration from environment files.
        
        Returns:
            True if reload successful, False otherwise
        """
        try:
            # Clear cache
            self._config_cache.clear()
            
            # Reload environment configuration
            self._load_environment_config()
            
            # Reload all configuration sections
            self.database = self._load_database_config()
            self.rag = self._load_rag_config()
            self.api = self._load_api_config()
            self.service = self._load_service_config()
            
            # Validate all configurations
            self._validate_all_configs()
            
            logger.info("Configuration reloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False
    
    def get_environment(self) -> Environment:
        """Get the current environment."""
        return self.environment
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == Environment.TESTING
    
    def get_database_url(self) -> str:
        """Get the database connection URL."""
        if self.database.url:
            return self.database.url
        
        # Construct URL from individual parameters
        return f"postgresql://{self.database.user}:{self.database.password}@{self.database.host}:{self.database.port}/{self.database.database}"
    
    def get_rag_similarity_threshold(self) -> float:
        """Get the RAG similarity threshold."""
        return self.rag.similarity_threshold
    
    def set_rag_similarity_threshold(self, threshold: float) -> None:
        """Set the RAG similarity threshold."""
        if not 0.0 < threshold <= 1.0:
            raise ValueError("Similarity threshold must be in (0, 1]")
        
        self.rag.similarity_threshold = threshold
        self.set_config("rag.similarity_threshold", threshold)
        logger.info(f"RAG similarity threshold updated to {threshold}")
    
    def get_duplicate_chunk_check_enabled(self) -> bool:
        """Get whether duplicate chunk checking is enabled."""
        return self.rag.enable_duplicate_chunk_check
    
    def set_duplicate_chunk_check_enabled(self, enabled: bool) -> None:
        """Set whether duplicate chunk checking is enabled."""
        self.rag.enable_duplicate_chunk_check = enabled
        self.set_config("rag.enable_duplicate_chunk_check", enabled)
        logger.info(f"Duplicate chunk check {'enabled' if enabled else 'disabled'}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "environment": self.environment.value,
            "database": {
                "url": self.database.url or "constructed",
                "host": self.database.host,
                "port": self.database.port,
                "user": self.database.user,
                "database": self.database.database,
                "schema": self.database.schema
            },
            "rag": {
                "similarity_threshold": self.rag.similarity_threshold,
                "max_chunks": self.rag.max_chunks,
                "token_budget": self.rag.token_budget,
                "embedding_model": self.rag.embedding_model,
                "vector_dimension": self.rag.vector_dimension,
                "enable_duplicate_chunk_check": self.rag.enable_duplicate_chunk_check
            },
            "api": {
                "openai_configured": bool(self.api.openai_api_key),
                "anthropic_configured": bool(self.api.anthropic_api_key),
                "llamaparse_configured": bool(self.api.llamaparse_api_key),
                "supabase_configured": bool(self.api.supabase_url and self.api.supabase_service_role_key)
            },
            "service": {
                "host": self.service.host,
                "port": self.service.port,
                "debug": self.service.debug,
                "log_level": self.service.log_level,
                "cors_origins": self.service.cors_origins
            }
        }

# Global configuration instance
_config_manager: Optional[ConfigurationManager] = None

def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager

def initialize_config(environment: Optional[str] = None) -> ConfigurationManager:
    """Initialize the global configuration manager."""
    global _config_manager
    _config_manager = ConfigurationManager(environment)
    return _config_manager
