"""
Environment Configuration Loader.

This module provides centralized environment variable loading with automatic
detection of the appropriate .env file based on environment or explicit selection.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class EnvironmentLoader:
    """
    Centralized environment configuration loader.
    
    Automatically detects and loads the appropriate .env file based on:
    1. Explicit env_file parameter
    2. ENVIRONMENT environment variable
    3. NODE_ENV environment variable  
    4. Fallback to .env.development
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the environment loader.
        
        Args:
            project_root: Path to project root. If None, auto-detects.
        """
        self.project_root = project_root or self._find_project_root()
        self._loaded_env_file: Optional[str] = None
        self._is_loaded = False
    
    def _find_project_root(self) -> Path:
        """
        Find the project root directory by looking for key files.
        
        Returns:
            Path to project root directory
        """
        current = Path(__file__).parent
        
        # Look for common project root indicators
        indicators = [
            "requirements.txt",
            "pyproject.toml", 
            ".git",
            ".env.development",
            ".env.production",
            "agents"  # Our specific project structure
        ]
        
        # Walk up the directory tree
        for parent in [current] + list(current.parents):
            if any((parent / indicator).exists() for indicator in indicators):
                return parent
        
        # Fallback to current directory's parent
        return current.parent
    
    def get_env_file_path(self, env_file: Optional[str] = None) -> Optional[Path]:
        """
        Determine which .env file to use based on priority.
        
        Args:
            env_file: Explicit env file name (e.g., ".env.development", "production")
            
        Returns:
            Path to the .env file to load, or None if not found
        """
        candidates = []
        
        # Priority 1: Explicit env_file parameter
        if env_file:
            if env_file.startswith('.env.'):
                candidates.append(env_file)
            else:
                candidates.append(f'.env.{env_file}')
        
        # Priority 2: ENVIRONMENT variable
        environment = os.getenv('ENVIRONMENT')
        if environment:
            candidates.append(f'.env.{environment}')
        
        # Priority 3: NODE_ENV variable
        node_env = os.getenv('NODE_ENV')
        if node_env:
            candidates.append(f'.env.{node_env}')
        
        # Priority 4: Default fallbacks
        candidates.extend([
            '.env.development',  # Default for development
            '.env.local',        # Local overrides
            '.env'               # Standard .env file
        ])
        
        # Check which files exist
        for candidate in candidates:
            env_path = self.project_root / candidate
            if env_path.exists():
                return env_path
        
        return None
    
    def load_environment(self, env_file: Optional[str] = None, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load environment variables from the appropriate .env file.
        
        Args:
            env_file: Specific env file to load (optional)
            force_reload: Force reload even if already loaded
            
        Returns:
            Dictionary with loading information
        """
        if self._is_loaded and not force_reload:
            return {
                "status": "already_loaded",
                "env_file": self._loaded_env_file,
                "project_root": str(self.project_root)
            }
        
        env_path = self.get_env_file_path(env_file)
        
        if not env_path:
            logger.warning("No .env file found in project root")
            return {
                "status": "no_env_file",
                "project_root": str(self.project_root),
                "searched_files": [
                    ".env.development",
                    ".env.production", 
                    ".env.local",
                    ".env"
                ]
            }
        
        try:
            # Load the environment file
            load_dotenv(env_path, override=True)
            
            self._loaded_env_file = env_path.name
            self._is_loaded = True
            
            logger.info(f"Loaded environment from: {env_path}")
            
            return {
                "status": "loaded",
                "env_file": env_path.name,
                "env_path": str(env_path),
                "project_root": str(self.project_root)
            }
            
        except Exception as e:
            logger.error(f"Failed to load environment file {env_path}: {e}")
            return {
                "status": "error",
                "env_file": env_path.name,
                "error": str(e),
                "project_root": str(self.project_root)
            }
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current configuration.
        
        Returns:
            Dictionary with configuration summary
        """
        return {
            "project_root": str(self.project_root),
            "loaded_env_file": self._loaded_env_file,
            "is_loaded": self._is_loaded,
            "environment": os.getenv('ENVIRONMENT'),
            "node_env": os.getenv('NODE_ENV'),
            "available_env_files": [
                f.name for f in self.project_root.glob('.env.*')
                if f.is_file()
            ]
        }


# Global instance for easy access
_global_loader: Optional[EnvironmentLoader] = None


def get_env_loader() -> EnvironmentLoader:
    """
    Get the global environment loader instance.
    
    Returns:
        EnvironmentLoader instance
    """
    global _global_loader
    if _global_loader is None:
        _global_loader = EnvironmentLoader()
    return _global_loader


def load_environment(env_file: Optional[str] = None, force_reload: bool = False) -> Dict[str, Any]:
    """
    Convenience function to load environment using global loader.
    
    Args:
        env_file: Specific env file to load (optional)
        force_reload: Force reload even if already loaded
        
    Returns:
        Dictionary with loading information
    """
    loader = get_env_loader()
    return loader.load_environment(env_file, force_reload)


def ensure_environment_loaded(env_file: Optional[str] = None) -> None:
    """
    Ensure environment is loaded, but don't reload if already loaded.
    
    Args:
        env_file: Specific env file to load (optional)
    """
    result = load_environment(env_file, force_reload=False)
    if result["status"] == "error":
        raise RuntimeError(f"Failed to load environment: {result.get('error')}")


# Auto-load on import (unless NO_AUTO_LOAD is set)
if not os.getenv('NO_AUTO_LOAD_ENV'):
    try:
        load_environment()
    except Exception as e:
        logger.warning(f"Auto-load of environment failed: {e}")


# Convenience functions for common environment checks
def is_development() -> bool:
    """Check if running in development environment."""
    env = os.getenv('ENVIRONMENT', '').lower()
    node_env = os.getenv('NODE_ENV', '').lower()
    return env == 'development' or node_env == 'development' or env == 'dev'


def is_production() -> bool:
    """Check if running in production environment."""
    env = os.getenv('ENVIRONMENT', '').lower()
    node_env = os.getenv('NODE_ENV', '').lower()
    return env == 'production' or node_env == 'production' or env == 'prod'


def is_testing() -> bool:
    """Check if running in testing environment."""
    env = os.getenv('ENVIRONMENT', '').lower()
    node_env = os.getenv('NODE_ENV', '').lower()
    return env == 'test' or node_env == 'test' or env == 'testing'


def get_environment() -> str:
    """Get the current environment name."""
    return (
        os.getenv('ENVIRONMENT') or 
        os.getenv('NODE_ENV') or 
        'development'
    ).lower()