"""
Authentication configuration for switching between different auth backends.
"""

import os
from typing import Literal

# Auth backend types
AuthBackendType = Literal["minimal", "supabase"]

def get_auth_backend() -> AuthBackendType:
    """
    Get the authentication backend type from environment variables.
    
    Returns:
        "minimal" for development (bypasses Supabase auth)
        "supabase" for production (uses full Supabase auth)
    """
    backend = os.getenv("AUTH_BACKEND", "minimal").lower()
    
    if backend not in ["minimal", "supabase"]:
        print(f"⚠️ Invalid AUTH_BACKEND: {backend}. Defaulting to 'minimal'")
        return "minimal"
    
    return backend

def is_minimal_auth() -> bool:
    """Check if using minimal auth backend."""
    return get_auth_backend() == "minimal"

def is_supabase_auth() -> bool:
    """Check if using Supabase auth backend."""
    return get_auth_backend() == "supabase"

# Environment-specific configurations
AUTH_CONFIG = {
    "minimal": {
        "description": "Minimal authentication for development",
        "features": [
            "Input validation",
            "JWT token generation",
            "No database user storage",
            "Fast development iteration"
        ],
        "environment": "development"
    },
    "supabase": {
        "description": "Full Supabase authentication for production",
        "features": [
            "Full Supabase auth integration",
            "Database user storage",
            "Email verification",
            "Password reset",
            "Session management"
        ],
        "environment": "production"
    }
}

def get_auth_config() -> dict:
    """Get configuration for the current auth backend."""
    backend = get_auth_backend()
    return AUTH_CONFIG.get(backend, AUTH_CONFIG["minimal"])

def print_auth_status():
    """Print current authentication configuration."""
    backend = get_auth_backend()
    config = get_auth_config()
    
    print(f"🔐 Authentication Backend: {backend.upper()}")
    print(f"📝 Description: {config['description']}")
    print(f"🌍 Environment: {config['environment']}")
    print(f"✨ Features:")
    for feature in config['features']:
        print(f"   • {feature}")