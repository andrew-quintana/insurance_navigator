"""
Configuration package for centralized environment management.

This package provides centralized environment variable loading with automatic
detection of the appropriate .env file based on environment or explicit selection.
"""

from .env_loader import (
    EnvironmentLoader,
    get_env_loader,
    load_environment,
    ensure_environment_loaded,
    is_development,
    is_production,
    is_testing,
    get_environment
)

__all__ = [
    'EnvironmentLoader',
    'get_env_loader',
    'load_environment',
    'ensure_environment_loaded',
    'is_development',
    'is_production', 
    'is_testing',
    'get_environment'
]