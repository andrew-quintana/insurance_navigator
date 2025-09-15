import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Load environment variables from .env files
try:
    from dotenv import load_dotenv
    # Load .env.development first, then .env.base as fallback
    # Use relative paths from the backend directory
    load_dotenv('../.env.development')
    load_dotenv('../.env.base', override=False)
except ImportError:
    # dotenv not available, continue without it
    pass

@dataclass
class WorkerConfig:
    """Configuration for BaseWorker with environment variable support"""
    
    # Database configuration
    database_url: str
    
    # Supabase configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    
    # External service configuration
    llamaparse_api_url: str
    llamaparse_api_key: str
    openai_api_url: str
    openai_api_key: str
    openai_model: str
    
    # Worker configuration
    poll_interval: int = 5
    max_retries: int = 3
    retry_base_delay: int = 3
    
    # Rate limiting configuration
    openai_requests_per_minute: int = 3500
    openai_tokens_per_minute: int = 90000
    openai_max_batch_size: int = 256
    
    # Circuit breaker configuration
    failure_threshold: int = 5
    recovery_timeout: int = 60
    
    # Logging configuration
    log_level: str = "INFO"
    
    # Pipeline configuration
    terminal_stage: str = "embedded"  # Stage where processing completes and state becomes 'done'
    
    # Local testing configuration
    use_mock_storage: bool = True  # Default to mock storage for local development
    
    @classmethod
    def from_environment(cls) -> 'WorkerConfig':
        """Create configuration from environment variables"""
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/accessa_dev")
        print(f"DEBUG: WorkerConfig database_url from env: {database_url[:50]}...")
        print(f"DEBUG: WorkerConfig DATABASE_URL env var: {os.getenv('DATABASE_URL', 'NOT_SET')[:50]}...")
        print(f"DEBUG: All env vars with DATABASE: {[k for k in os.environ.keys() if 'DATABASE' in k.upper()]}")
        print(f"DEBUG: All env vars with SUPABASE: {[k for k in os.environ.keys() if 'SUPABASE' in k.upper()]}")
        
        return cls(
            # Database
            database_url=database_url,
            
            # Supabase
            supabase_url=os.getenv("SUPABASE_URL", "https://znvwzkdblknkkztqyfnu.supabase.co"),
            supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
            supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
            
            # LlamaParse
            llamaparse_api_url=os.getenv("LLAMAPARSE_BASE_URL", "https://api.cloud.llamaindex.ai/api/v1"),
            llamaparse_api_key=os.getenv("LLAMACLOUD_API_KEY", os.getenv("LLAMAPARSE_API_KEY", "")),
            
            # OpenAI
            openai_api_url=os.getenv("OPENAI_API_URL", "https://api.openai.com"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "text-embedding-3-small"),
            
            # Worker settings
            poll_interval=int(os.getenv("WORKER_POLL_INTERVAL", "5")),
            max_retries=int(os.getenv("WORKER_MAX_RETRIES", "3")),
            retry_base_delay=int(os.getenv("WORKER_RETRY_BASE_DELAY", "3")),
            
            # Rate limiting
            openai_requests_per_minute=int(os.getenv("OPENAI_REQUESTS_PER_MINUTE", "3500")),
            openai_tokens_per_minute=int(os.getenv("OPENAI_TOKENS_PER_MINUTE", "90000")),
            openai_max_batch_size=int(os.getenv("OPENAI_MAX_BATCH_SIZE", "256")),
            
            # Circuit breaker
            failure_threshold=int(os.getenv("WORKER_FAILURE_THRESHOLD", "5")),
            recovery_timeout=int(os.getenv("WORKER_RECOVERY_TIMEOUT", "60")),
            
            # Logging
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            
            # Pipeline
            terminal_stage=os.getenv("TERMINAL_STAGE", "embedded"),
            
            # Local testing - default to false in production, true in development
            use_mock_storage=os.getenv("USE_MOCK_STORAGE", "false").lower() == "true"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "database_url": self.database_url,
            "supabase_url": self.supabase_url,
            "supabase_anon_key": self.supabase_anon_key,
            "supabase_service_role_key": self.supabase_service_role_key,
            "llamaparse_api_url": self.llamaparse_api_url,
            "llamaparse_api_key": self.llamaparse_api_key,
            "openai_api_url": self.openai_api_url,
            "openai_api_key": self.openai_api_key,
            "openai_model": self.openai_model,
            "poll_interval": self.poll_interval,
            "max_retries": self.max_retries,
            "retry_base_delay": self.retry_base_delay,
            "openai_requests_per_minute": self.openai_requests_per_minute,
            "openai_tokens_per_minute": self.openai_tokens_per_minute,
            "openai_max_batch_size": self.openai_max_batch_size,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "log_level": self.log_level,
            "terminal_stage": self.terminal_stage,
            "use_mock_storage": self.use_mock_storage
        }
    
    def validate(self) -> bool:
        """Validate configuration values"""
        required_fields = [
            "database_url", "supabase_url", "supabase_service_role_key"
        ]
        
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Required configuration field '{field}' is empty")
        
        # Validate numeric fields
        if self.poll_interval <= 0:
            raise ValueError("poll_interval must be positive")
        
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        
        if self.retry_base_delay <= 0:
            raise ValueError("retry_base_delay must be positive")
        
        if self.openai_max_batch_size <= 0:
            raise ValueError("openai_max_batch_size must be positive")
        
        return True
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI-specific configuration"""
        return {
            "api_url": self.openai_api_url,
            "api_key": self.openai_api_key,
            "model": self.openai_model,
            "requests_per_minute": self.openai_requests_per_minute,
            "tokens_per_minute": self.openai_tokens_per_minute,
            "max_batch_size": self.openai_max_batch_size,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }
    
    def get_llamaparse_config(self) -> Dict[str, Any]:
        """Get LlamaParse-specific configuration"""
        return {
            "api_url": self.llamaparse_api_url,
            "api_key": self.llamaparse_api_key,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage-specific configuration"""
        return {
            "storage_url": self.supabase_url,
            "anon_key": self.supabase_anon_key,
            "service_role_key": self.supabase_service_role_key
        }
    
    def get_service_router_config(self) -> Dict[str, Any]:
        """Get service router configuration"""
        # Use REAL mode in production, HYBRID in development
        environment = os.getenv("ENVIRONMENT", "development")
        mode = "REAL" if environment == "production" else "HYBRID"
        
        # Disable fallback in production to prevent silent mock usage
        fallback_enabled = environment != "production"
        
        return {
            "mode": mode,
            "llamaparse_config": self.get_llamaparse_config(),
            "openai_config": self.get_openai_config(),
            "fallback_enabled": fallback_enabled,
            "fallback_timeout": 10
        }

