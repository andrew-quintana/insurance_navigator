"""
Authentication adapter that provides a unified interface for Supabase authentication.
This simplified version uses only Supabase's built-in authentication system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from db.services.supabase_auth_service import supabase_auth_service

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

class SupabaseAuthBackend(AuthBackend):
    """Supabase authentication backend that uses auth.users directly."""
    
    def __init__(self):
        self.auth_service = supabase_auth_service
    
    async def create_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """Create user using Supabase auth directly."""
        return await self.auth_service.create_user(
            email=email,
            password=password,
            name=name,
            consent_version="1.0",
            consent_timestamp="2025-01-01T00:00:00Z"
        )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user using Supabase auth directly."""
        return await self.auth_service.authenticate_user(email, password)
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate token using Supabase auth."""
        return self.auth_service.validate_token(token)
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user info from auth.users directly."""
        return await self.auth_service.get_user_by_id(user_id)

class AuthAdapter:
    """Main authentication adapter that uses Supabase authentication."""
    
    def __init__(self):
        """Initialize auth adapter with Supabase backend."""
        self.backend_type = "supabase"
        self.backend = SupabaseAuthBackend()
        logger.info("Auth adapter initialized with Supabase backend")
    
    async def create_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """Create a new user using Supabase authentication."""
        return await self.backend.create_user(email, password, name)
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user using Supabase authentication."""
        return await self.backend.authenticate_user(email, password)
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a JWT token using Supabase authentication."""
        return self.backend.validate_token(token)
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information using Supabase authentication."""
        return await self.backend.get_user_info(user_id)

# Global auth adapter instance - always uses Supabase
auth_adapter = AuthAdapter()

# Print auth status on import
print("🔐 Authentication Backend: SUPABASE")
print("📝 Description: Full Supabase authentication for production")
print("🌍 Environment: production")
print("✨ Features:")
print("   • Full Supabase auth integration")
print("   • Database user storage")
print("   • Email verification")
print("   • Password reset")
print("   • Session management")
