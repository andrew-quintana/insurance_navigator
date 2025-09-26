"""
Authentication and authorization for the upload pipeline.
Updated to use Supabase authentication via auth adapter.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Import auth adapter for Supabase authentication
from db.services.auth_adapter import auth_adapter

logger = logging.getLogger(__name__)

# JWT token scheme
security = HTTPBearer(auto_error=False)


class User(BaseModel):
    """User model extracted from JWT token."""
    
    user_id: UUID
    email: Optional[str] = None
    role: Optional[str] = None


class AuthError(Exception):
    """Authentication error."""
    pass


async def get_current_user(request: Request) -> User:
    """
    Extract and validate user from JWT token using Supabase auth.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User object with extracted information
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Get authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Extract token
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Validate token using auth adapter
        user_data = auth_adapter.validate_token(token)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Convert to User model
        user = User(
            user_id=UUID(user_data["id"]),
            email=user_data.get("email"),
            role="user"  # Default role
        )
        
        return user
        
    except ValueError as e:
        logger.warning("Invalid user ID format", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error("Authentication error", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def validate_jwt_token(token: str) -> User:
    """
    Validate JWT token and extract user information using Supabase auth.
    
    Args:
        token: JWT token string
        
    Returns:
        User object with extracted information
        
    Raises:
        AuthError: If token validation fails
    """
    try:
        # Use auth adapter for token validation
        user_data = auth_adapter.validate_token(token)
        if not user_data:
            raise AuthError("Invalid token")
        
        # Convert string user ID to UUID
        try:
            user_uuid = UUID(user_data["id"])
        except ValueError:
            raise AuthError("Invalid user ID format in token")
        
        # Extract additional claims
        email = user_data.get("email")
        role = "user"  # Default role
        
        return User(
            user_id=user_uuid,
            email=email,
            role=role
        )
        
    except Exception as e:
        logger.error("Token validation error", exc_info=True)
        raise AuthError(f"Token validation failed: {str(e)}")


async def get_optional_user(request: Request) -> Optional[User]:
    """
    Extract user from JWT token if present, return None if missing.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User object if token is valid, None otherwise
    """
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


async def require_user(request: Request) -> User:
    """
    Dependency for endpoints that require authentication.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User object if authentication succeeds
        
    Raises:
        HTTPException: If authentication fails
    """
    return await get_current_user(request)


async def optional_user(request: Request) -> Optional[User]:
    """
    Dependency for endpoints that optionally use authentication.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User object if authentication succeeds, None otherwise
    """
    return await get_optional_user(request)
