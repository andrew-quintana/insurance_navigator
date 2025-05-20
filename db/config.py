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

def load_config() -> Config:
    """Load configuration from environment variables."""
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
            url=os.getenv('DATABASE_URL', '')
        ),
        encryption=EncryptionConfig(
            provider=os.getenv('ENCRYPTION_KEY_PROVIDER', 'mock'),
            default_key_version=int(os.getenv('DEFAULT_ENCRYPTION_KEY_VERSION', '1'))
        )
    )

# Global config instance
config = load_config() 