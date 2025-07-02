"""
Authentication service for handling user authentication and session management.
"""

import logging
import re
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from fastapi import HTTPException, status
from pydantic import BaseModel

from db.services.db_pool import get_db_pool
from db.config import JWTConfig

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling authentication operations."""
    
    def __init__(self, jwt_config: JWTConfig):
        """Initialize the auth service."""
        self.jwt_config = jwt_config
        self.db = get_db_pool()
        self.secret_key = jwt_config.secret
        self.token_expire_minutes = jwt_config.token_expire_minutes
        
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        Create a new JWT access token.
        
        Args:
            data: Data to encode in the token
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm="HS256")
        
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: The token to verify
            
        Returns:
            Decoded token data
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
            
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create a new refresh token with longer expiry.
        
        Args:
            data: Data to encode in the token
            
        Returns:
            Refresh token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)  # 7 day refresh token
        to_encode.update({"exp": expire, "refresh": True})
        return jwt.encode(to_encode, self.secret_key, algorithm="HS256")
        
    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Create a new access token using a refresh token.
        
        Args:
            refresh_token: The refresh token to use
            
        Returns:
            New access token
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=["HS256"])
            if not payload.get("refresh"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            del payload["exp"]
            del payload["refresh"]
            return self.create_access_token(payload)
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

    async def register_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Register a new user."""
        try:
            if not self.validate_email(email):
                raise ValueError("Invalid email format")
            if not self.validate_password(password):
                raise ValueError("Invalid password format")

            result = await self.db.auth.sign_up({
                "email": email,
                "password": password
            })
            return result
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            raise

    async def login_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Login a user."""
        try:
            result = await self.db.auth.sign_in({
                "email": email,
                "password": password
            })
            return result
        except Exception as e:
            logger.error(f"Error logging in user: {str(e)}")
            raise

    async def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """Get the current user from a token."""
        try:
            payload = jwt.decode(
                token,
                self.jwt_config.secret,
                algorithms=[self.jwt_config.algorithm]
            )
            user_id = payload.get("sub")
            if not user_id:
                return None

            result = await self.db.auth.get_user(user_id)
            return result
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.exceptions.DecodeError as e:
            logger.error(f"Error decoding token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            return None

    async def logout_user(self) -> bool:
        """Logout the current user."""
        try:
            await self.db.auth.sign_out()
            return True
        except Exception as e:
            logger.error(f"Error logging out user: {str(e)}")
            return False

    async def refresh_session(self) -> Optional[Dict[str, Any]]:
        """Refresh the current session."""
        try:
            result = await self.db.auth.get_session()
            return result
        except Exception as e:
            logger.error(f"Error refreshing session: {str(e)}")
            return None

    @staticmethod
    def validate_password(password: str) -> bool:
        """Validate password format."""
        if not password or len(password) < 8:
            return False
        
        # Check for at least one uppercase, lowercase, number, and special character
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        return all([has_upper, has_lower, has_digit, has_special])

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        if not email:
            return False
            
        # Basic email format validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) 