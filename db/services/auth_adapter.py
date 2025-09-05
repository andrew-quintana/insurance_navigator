"""
Authentication adapter that provides a unified interface for different auth backends.
This allows switching between minimal auth (development) and Supabase auth (production).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from db.services.improved_minimal_auth_service import improved_minimal_auth_service
from db.services.user_service import get_user_service

logger = logging.getLogger(__name__)

class AuthBackend(ABC):
    """Abstract base class for authentication backends."""
    
    @abstractmethod
    async def create_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """Create a new user."""
        pass
    
    @abstractmethod
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user."""
        pass
    
    @abstractmethod
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a JWT token."""
        pass
    
    @abstractmethod
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information by ID."""
        pass

class MinimalAuthBackend(AuthBackend):
    """Minimal authentication backend for development."""
    
    def __init__(self):
        self.auth_service = improved_minimal_auth_service
    
    async def create_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """Create user using minimal auth service."""
        return await self.auth_service.create_user_minimal(
            email=email,
            password=password,
            consent_version="1.0",
            consent_timestamp="2025-01-01T00:00:00Z",
            name=name
        )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user using minimal auth service."""
        return await self.auth_service.authenticate_user_minimal(email, password)
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate token using minimal auth service."""
        return self.auth_service.validate_token(token)
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user info from token validation (no database lookup needed)."""
        # For minimal auth, we don't need to fetch from database
        # The user info is already in the token
        return None

class SupabaseAuthBackend(AuthBackend):
    """Supabase authentication backend for production."""
    
    def __init__(self):
        self.user_service = None
    
    async def _get_user_service(self):
        """Lazy load user service."""
        if not self.user_service:
            self.user_service = await get_user_service()
        return self.user_service
    
    async def create_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """Create user using Supabase auth."""
        user_service = await self._get_user_service()
        return await user_service.create_user(
            email=email,
            password=password,
            consent_version="1.0",
            consent_timestamp="2025-01-01T00:00:00Z",
            name=name
        )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user using Supabase auth."""
        user_service = await self._get_user_service()
        return await user_service.authenticate_user(email, password)
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate token using Supabase auth."""
        # This would need to be implemented for Supabase JWT validation
        # For now, we'll use the minimal auth validation
        return improved_minimal_auth_service.validate_token(token)
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user info from Supabase database."""
        user_service = await self._get_user_service()
        return await user_service.get_user_by_id(user_id)

class AuthAdapter:
    """Main authentication adapter that switches between backends."""
    
    def __init__(self, backend_type: str = "minimal"):
        """
        Initialize auth adapter with specified backend.
        
        Args:
            backend_type: "minimal" for development, "supabase" for production
        """
        self.backend_type = backend_type
        if backend_type == "minimal":
            self.backend = MinimalAuthBackend()
        elif backend_type == "supabase":
            self.backend = SupabaseAuthBackend()
        else:
            raise ValueError(f"Unknown backend type: {backend_type}")
        
        logger.info(f"Auth adapter initialized with {backend_type} backend")
    
    async def create_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """Create a new user using the configured backend."""
        return await self.backend.create_user(email, password, name)
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user using the configured backend."""
        return await self.backend.authenticate_user(email, password)
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a JWT token using the configured backend."""
        return self.backend.validate_token(token)
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information using the configured backend."""
        return await self.backend.get_user_info(user_id)
    
    def switch_backend(self, backend_type: str):
        """Switch to a different auth backend."""
        self.backend_type = backend_type
        if backend_type == "minimal":
            self.backend = MinimalAuthBackend()
        elif backend_type == "supabase":
            self.backend = SupabaseAuthBackend()
        else:
            raise ValueError(f"Unknown backend type: {backend_type}")
        
        logger.info(f"Auth adapter switched to {backend_type} backend")

# Global auth adapter instance
# Can be configured via environment variable or config
from config.auth_config import get_auth_backend, print_auth_status

# Initialize with configured backend
auth_backend_type = get_auth_backend()
auth_adapter = AuthAdapter(auth_backend_type)

# Print auth status on import
print_auth_status()
