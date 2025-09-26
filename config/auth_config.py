"""
Authentication configuration for Supabase authentication.
This simplified version uses only Supabase's built-in authentication system.
"""

import os
from typing import Literal

# Auth backend types - only Supabase now
AuthBackendType = Literal["supabase"]

def get_auth_backend() -> AuthBackendType:
    """
    Get the authentication backend type from environment variables.
    
    Returns:
        "supabase" for all environments (uses full Supabase auth)
    """
    backend = os.getenv("AUTH_BACKEND", "supabase").lower()
    
    if backend not in ["supabase"]:
        print(f"⚠️ Invalid AUTH_BACKEND: {backend}. Defaulting to 'supabase'")
        return "supabase"
    
    return backend

def is_supabase_auth() -> bool:
    """Check if using Supabase auth backend."""
    return True  # Always true now

# Environment-specific configurations
AUTH_CONFIG = {
    "supabase": {
        "description": "Full Supabase authentication for all environments",
        "features": [
            "Full Supabase auth integration",
            "Database user storage in auth.users",
            "Email verification",
            "Password reset",
            "Session management",
            "RLS integration"
        ],
        "environment": "all"
    }
}

def get_auth_config() -> dict:
    """Get configuration for the current auth backend."""
    return AUTH_CONFIG["supabase"]

def print_auth_status():
    """Print current authentication configuration."""
    config = get_auth_config()
    
    print(f"🔐 Authentication Backend: SUPABASE")
    print(f"📝 Description: {config['description']}")
    print(f"🌍 Environment: {config['environment']}")
    print(f"✨ Features:")
    for feature in config['features']:
        print(f"   • {feature}")