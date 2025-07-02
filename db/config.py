"""
Database configuration module.
"""

import os
from typing import Optional
from dataclasses import dataclass
from supabase import create_client, Client

@dataclass
class SupabaseConfig:
    """Configuration for Supabase client with HIPAA compliance settings."""
    url: str
    service_role_key: str
    anon_key: str
    jwt_secret: Optional[str] = None
    jwt_expiry: int = 3600
    encryption_key: Optional[str] = None
    audit_logging: bool = True
    data_retention_days: int = 365  # HIPAA requires minimum 6 years
    ssl_enforce: bool = True
    network_restrictions: bool = True
    point_in_time_recovery: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.url:
            raise ValueError("Invalid Supabase URL")
        if not self.service_role_key or not self.anon_key:
            raise ValueError("Service role key and anon key cannot be empty")
        if self.jwt_expiry <= 0:
            raise ValueError("JWT expiry must be positive")
        
        # In test environment, don't require encryption key
        is_test = os.getenv("NODE_ENV") == "test"
        if self.audit_logging and not self.encryption_key and not is_test:
            raise ValueError("Encryption key is required when audit logging is enabled")
    
    @classmethod
    def from_env(cls) -> 'SupabaseConfig':
        """Create config from environment variables."""
        is_test = os.getenv('NODE_ENV') == 'test'
        url = os.getenv('SUPABASE_TEST_URL') if is_test else (os.getenv('SUPABASE_DB_URL') or os.getenv('SUPABASE_URL'))
        if not url:
            raise ValueError("SUPABASE_URL environment variable is required")

        service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        if not service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")

        anon_key = os.getenv('SUPABASE_TEST_KEY') if is_test else os.getenv('SUPABASE_ANON_KEY')
        if not anon_key:
            raise ValueError("SUPABASE_ANON_KEY environment variable is required")

        jwt_secret = os.getenv('SUPABASE_JWT_SECRET')
        jwt_expiry = int(os.getenv('JWT_EXPIRY', '3600'))
        encryption_key = os.getenv('DOCUMENT_ENCRYPTION_KEY')
        audit_logging = os.getenv('AUDIT_LOGGING_ENABLED', 'true').lower() == 'true'
        data_retention_days = int(os.getenv('DATA_RETENTION_DAYS', '365'))
        ssl_enforce = os.getenv('SSL_ENFORCE', 'true').lower() == 'true'
        network_restrictions = os.getenv('NETWORK_RESTRICTIONS', 'true').lower() == 'true'
        point_in_time_recovery = os.getenv('POINT_IN_TIME_RECOVERY', 'true').lower() == 'true'
        
        return cls(
            url=url,
            service_role_key=service_role_key,
            anon_key=anon_key,
            jwt_secret=jwt_secret,
            jwt_expiry=jwt_expiry,
            encryption_key=encryption_key,
            audit_logging=audit_logging,
            data_retention_days=data_retention_days,
            ssl_enforce=ssl_enforce,
            network_restrictions=network_restrictions,
            point_in_time_recovery=point_in_time_recovery
        )
    
    def get_client_options(self) -> dict:
        """Get Supabase client options with proper configuration."""
        options = {
            'headers': {
                'Authorization': f'Bearer {self.service_role_key}',
                'apikey': self.anon_key
            },
            'auto_refresh_token': True,
            'persist_session': True
        }
        # Explicitly exclude proxy settings to avoid issues with Supabase client 2.3.4
        return options

    def get_client(self) -> Client:
        """Create a Supabase client instance."""
        return create_client(
            self.url,
            self.anon_key if not self.service_role_key else self.service_role_key
        )

@dataclass
class PostgresConfig:
    """PostgreSQL configuration class."""
    host: str
    port: int
    database: str
    user: str
    password: str
    
    @classmethod
    def from_env(cls) -> 'PostgresConfig':
        """
        Create configuration from environment variables.
        
        Returns:
            PostgresConfig instance
        
        Raises:
            ValueError: If required environment variables are missing
        """
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = int(os.getenv("POSTGRES_PORT", "54322"))
        database = os.getenv("POSTGRES_DB", "postgres")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        
        return cls(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
    
    @property
    def connection_string(self) -> str:
        """
        Get PostgreSQL connection string.
        
        Returns:
            Connection string
        """
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class JWTConfig:
    """Configuration for JWT handling."""
    secret: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    token_expire_minutes: int = 30  # Alias for access_token_expire_minutes for backward compatibility

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.secret:
            raise ValueError("JWT secret cannot be empty")
        if self.access_token_expire_minutes <= 0:
            raise ValueError("Access token expiry must be positive")

    @classmethod
    def from_env(cls) -> 'JWTConfig':
        """Create config from environment variables."""
        secret = os.getenv('JWT_SECRET')
        if not secret:
            raise ValueError("JWT_SECRET environment variable is required")

        algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
        expire_minutes = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))

        return cls(
            secret=secret,
            algorithm=algorithm,
            access_token_expire_minutes=expire_minutes,
            token_expire_minutes=expire_minutes
        )

class DatabaseConfig:
    """Database configuration settings."""
    
    host: str
    port: int
    database: str
    user: str
    password: str
    
    # Supabase specific
    supabase: Optional[SupabaseConfig] = None
    
    # Connection pool settings
    min_connections: int
    max_connections: int
    
    def __init__(self, host, port, database, user, password, supabase, min_connections, max_connections):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.supabase = supabase
        self.min_connections = min_connections
        self.max_connections = max_connections

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """
        Create configuration from environment variables.
        
        Returns:
            DatabaseConfig instance
        
        Raises:
            ValueError: If required environment variables are missing
        """
        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", "5432"))
        database = os.getenv("DB_NAME", "insurance_navigator")
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "postgres")
        
        supabase = SupabaseConfig.from_env() if os.getenv("SUPABASE_DB_URL") else None
        min_connections = int(os.getenv("DB_MIN_CONNECTIONS", "1"))
        max_connections = int(os.getenv("DB_MAX_CONNECTIONS", "10"))
        
        return cls(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            supabase=supabase,
            min_connections=min_connections,
            max_connections=max_connections
        )

def get_supabase_test_config() -> SupabaseConfig:
    """Get Supabase test environment configuration."""
    return SupabaseConfig(
        url=os.getenv("SUPABASE_TEST_URL", "http://127.0.0.1:54321"),
        service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        anon_key=os.getenv("SUPABASE_TEST_KEY"),
        jwt_secret=os.getenv("SUPABASE_JWT_SECRET"),
        encryption_key=os.getenv("DOCUMENT_ENCRYPTION_KEY"),
    )

# Create default config instance lazily
_config = None

def get_config() -> DatabaseConfig:
    """Get the database configuration instance."""
    global _config
    if _config is None:
        _config = DatabaseConfig.from_env()
    return _config 