"""
Authentication and authorization for the upload pipeline.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

from .config import get_config

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
    Extract and validate user from JWT token.
    
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
        
        # Validate token
        user = await validate_jwt_token(token)
        return user
        
    except InvalidTokenError as e:
        logger.warning("JWT validation failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
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
    Validate JWT token and extract user information.
    
    Args:
        token: JWT token string
        
    Returns:
        User object with extracted information
        
    Raises:
        AuthError: If token validation fails
    """
    try:
        config = get_config()
        
        # Debug logging
        logger.info(f"Attempting to decode JWT token: {token[:50]}...")
        
        # Decode JWT token from main API server
        # Use the same JWT configuration as the main API server
        payload = jwt.decode(
            token,
            "improved-minimal-dev-secret-key",  # Use same secret as main API server
            algorithms=["HS256"],
            options={"verify_aud": False, "verify_iss": False}  # Skip audience and issuer verification for development
        )
        
        logger.info(f"JWT token decoded successfully: {payload}")
        
        # Extract user information
        user_id = payload.get("sub")
        if not user_id:
            raise AuthError("Missing user ID in token")
        
        # Convert string user ID to UUID
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise AuthError("Invalid user ID format in token")
        
        # Extract additional claims
        email = payload.get("email")
        role = payload.get("role", "user")
        
        return User(
            user_id=user_uuid,
            email=email,
            role=role
        )
        
    except JWTError as e:
        logger.warning("JWT decode failed", exc_info=True)
        raise AuthError(f"Invalid JWT token: {str(e)}")
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
