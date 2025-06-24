"""Configuration module for the application."""
import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class SupabaseConfig:
    url: str
    anon_key: str
    service_role_key: str
    storage_bucket: str
    signed_url_expiry: int

    @classmethod
    def from_env(cls) -> 'SupabaseConfig':
        """Create a SupabaseConfig instance from environment variables."""
        # Load test environment if TEST_MODE is set
        if os.getenv('TEST_MODE') == 'true':
            load_dotenv('.env.test')
        else:
            load_dotenv()

        return cls(
            url=os.getenv('SUPABASE_URL', ''),
            anon_key=os.getenv('SUPABASE_ANON_KEY', ''),
            service_role_key=os.getenv('SUPABASE_SERVICE_ROLE_KEY', ''),
            storage_bucket=os.getenv('SUPABASE_STORAGE_BUCKET', 'policies'),
            signed_url_expiry=int(os.getenv('SIGNED_URL_EXPIRY_SECONDS', '3600'))
        )

@dataclass
class DatabaseConfig:
    url: str

@dataclass
class EncryptionConfig:
    provider: str
    default_key_version: int

@dataclass
class Config:
    supabase: SupabaseConfig
    database: DatabaseConfig
    encryption: EncryptionConfig

def get_database_url() -> str:
    """
    Get database URL with fallback logic:
    1. Use DATABASE_URL_LOCAL if set (local development)
    2. Fall back to DATABASE_URL (Supabase/production)
    3. Return empty string if neither is set
    """
    local_url = os.getenv('DATABASE_URL_LOCAL', '')
    production_url = os.getenv('DATABASE_URL', '')
    
    if local_url:
        print(f"🔧 Using local database: {local_url.split('@')[0]}@[host]")
        return local_url
    elif production_url:
        print(f"🌐 Using production database: {production_url.split('@')[0]}@[host]")
        return production_url
    else:
        print("⚠️  No database URL configured")
        return ''

def get_async_database_url() -> str:
    """Get async database URL by replacing postgresql:// with postgresql+asyncpg://"""
    db_url = get_database_url()
    if db_url and db_url.startswith('postgresql://'):
        return db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    return db_url

def load_config() -> Config:
    """Load configuration from environment variables."""
    # Load test environment if TEST_MODE is set
    if os.getenv('TEST_MODE') == 'true':
        load_dotenv('.env.test')
    else:
        load_dotenv()

    return Config(
        supabase=SupabaseConfig(
            url=os.getenv('SUPABASE_URL', ''),
            anon_key=os.getenv('SUPABASE_ANON_KEY', ''),
            service_role_key=os.getenv('SUPABASE_SERVICE_ROLE_KEY', ''),
            storage_bucket=os.getenv('SUPABASE_STORAGE_BUCKET', 'policies'),
            signed_url_expiry=int(os.getenv('SIGNED_URL_EXPIRY_SECONDS', '3600'))
        ),
        database=DatabaseConfig(
            url=get_database_url()
        ),
        encryption=EncryptionConfig(
            provider=os.getenv('ENCRYPTION_KEY_PROVIDER', 'mock'),
            default_key_version=int(os.getenv('DEFAULT_ENCRYPTION_KEY_VERSION', '1'))
        )
    )

# Global config instance
config = load_config() 