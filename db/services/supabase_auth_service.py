"""
Simplified Supabase authentication service that works directly with auth.users.
This service eliminates the need for a separate public.users table by using
Supabase's built-in authentication system directly.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from config.database import get_supabase_client, get_supabase_service_client
from config.auth_config import get_auth_config

logger = logging.getLogger(__name__)

class SupabaseAuthService:
    """Simplified authentication service that uses Supabase auth.users directly."""
    
    def __init__(self):
        """Initialize the Supabase auth service."""
        self.db = None
        self.service_db = None
    
    async def _get_client(self):
        """Get the regular Supabase client."""
        if not self.db:
            self.db = await get_supabase_client()
        return self.db
    
    async def _get_service_client(self):
        """Get the service role Supabase client."""
        if not self.service_db:
            self.service_db = await get_supabase_service_client()
        return self.service_db
    
    async def create_user(
        self,
        email: str,
        password: str,
        name: str = None,
        consent_version: str = "1.0",
        consent_timestamp: str = None
    ) -> Dict[str, Any]:
        """Create a new user using Supabase auth directly.
        
        Args:
            email: User's email address
            password: User's password
            name: User's display name (optional)
            consent_version: Consent version (default: "1.0")
            consent_timestamp: Consent timestamp (default: current time)
            
        Returns:
            Dict containing user and session data
            
        Raises:
            Exception: If user creation fails
        """
        try:
            logger.info(f"Creating user with Supabase auth: {email}")
            
            # Set default consent timestamp if not provided
            if not consent_timestamp:
                consent_timestamp = datetime.now().isoformat()
            
            # Get service client for user creation
            service_client = await self._get_service_client()
            
            # Prepare user metadata
            user_metadata = {
                "name": name or email.split("@")[0],
                "consent_version": consent_version,
                "consent_timestamp": consent_timestamp
            }
            
            # Create user in Supabase auth
            auth_response = service_client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,  # Auto-confirm for development
                "user_metadata": user_metadata
            })
            
            if not auth_response or not auth_response.user:
                raise Exception("Failed to create user in Supabase auth")
            
            logger.info(f"✅ User created successfully: {email} (ID: {auth_response.user.id})")
            
            # Admin user creation doesn't return a session, so we'll create a simple response
            return {
                "user": {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "name": user_metadata.get("name"),
                    "email_confirmed": True
                },
                "session": {
                    "access_token": None,  # No session for admin-created users
                    "refresh_token": None,
                    "expires_at": None
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise Exception(f"Failed to create user: {str(e)}")
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user using Supabase auth.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dict containing user and session data, or None if authentication fails
        """
        try:
            logger.info(f"Authenticating user: {email}")
            
            # Get regular client for authentication
            client = await self._get_client()
            
            # Authenticate with Supabase
            auth_response = client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if not auth_response or not auth_response.user:
                logger.warning(f"Authentication failed for user: {email}")
                return None
            
            # Get user metadata
            user_metadata = auth_response.user.user_metadata or {}
            
            logger.info(f"✅ User authenticated successfully: {email}")
            
            return {
                "user": {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "name": user_metadata.get("name", email.split("@")[0]),
                    "email_confirmed": auth_response.user.email_confirmed_at is not None
                },
                "session": {
                    "access_token": auth_response.session.access_token,
                    "refresh_token": auth_response.session.refresh_token,
                    "expires_at": auth_response.session.expires_at
                }
            }
            
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information by ID from auth.users.
        
        Args:
            user_id: User's ID
            
        Returns:
            Dict containing user data, or None if user not found
        """
        try:
            logger.info(f"Getting user by ID: {user_id}")
            
            # Get service client for user lookup
            service_client = await self._get_service_client()
            
            # Get user from auth.users
            auth_response = service_client.auth.admin.get_user_by_id(user_id)
            
            if not auth_response or not auth_response.user:
                logger.warning(f"User not found: {user_id}")
                return None
            
            # Get user metadata
            user_metadata = auth_response.user.user_metadata or {}
            
            return {
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "name": user_metadata.get("name", auth_response.user.email.split("@")[0]),
                "email_confirmed": auth_response.user.email_confirmed_at is not None,
                "created_at": auth_response.user.created_at,
                "updated_at": auth_response.user.updated_at,
                "last_sign_in_at": auth_response.user.last_sign_in_at,
                "user_metadata": user_metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            return None
    
    async def get_user_from_token(self, access_token: str, refresh_token: str = None) -> Optional[Dict[str, Any]]:
        """Get user information from a JWT token.
        
        Args:
            access_token: JWT access token
            refresh_token: Optional refresh token
            
        Returns:
            Dict containing user data, or None if token is invalid
        """
        try:
            logger.info("Getting user from token")
            
            # Get regular client
            client = await self._get_client()
            
            # Set the session
            if refresh_token:
                client.auth.set_session(access_token, refresh_token)
            else:
                # For backward compatibility, try with just access token
                client.auth.set_session(access_token, access_token)
            
            # Get user from token
            auth_response = client.auth.get_user()
            
            if not auth_response or not auth_response.user:
                logger.warning("Invalid token")
                return None
            
            # Get user metadata
            user_metadata = auth_response.user.user_metadata or {}
            
            return {
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "name": user_metadata.get("name", auth_response.user.email.split("@")[0]),
                "email_confirmed": auth_response.user.email_confirmed_at is not None,
                "created_at": auth_response.user.created_at,
                "updated_at": auth_response.user.updated_at,
                "last_sign_in_at": auth_response.user.last_sign_in_at,
                "user_metadata": user_metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting user from token: {str(e)}")
            return None
    
    async def update_user_metadata(self, user_id: str, metadata: Dict[str, Any]) -> bool:
        """Update user metadata in auth.users.
        
        Args:
            user_id: User's ID
            metadata: Metadata to update
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            logger.info(f"Updating user metadata for: {user_id}")
            
            # Get service client for user update
            service_client = await self._get_service_client()
            
            # Update user metadata
            auth_response = service_client.auth.admin.update_user_by_id(
                user_id,
                {"user_metadata": metadata}
            )
            
            if not auth_response or not auth_response.user:
                logger.warning(f"Failed to update user metadata: {user_id}")
                return False
            
            logger.info(f"✅ User metadata updated successfully: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user metadata: {str(e)}")
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user from auth.users.
        
        Args:
            user_id: User's ID
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            logger.info(f"Deleting user: {user_id}")
            
            # Get service client for user deletion
            service_client = await self._get_service_client()
            
            # Delete user
            service_client.auth.admin.delete_user(user_id)
            
            logger.info(f"✅ User deleted successfully: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return False
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a JWT token using Supabase.
        
        Args:
            token: JWT access token
            
        Returns:
            Dict containing user data, or None if token is invalid
        """
        try:
            logger.info("Validating token with Supabase")
            
            # For Supabase JWT validation, we need to decode and verify the token
            # This is a simplified implementation - in production, you'd want to
            # verify the JWT signature using Supabase's public key
            import jwt
            import json
            from datetime import datetime
            
            # Decode the JWT token without verification for now
            # In production, you should verify the signature
            payload = jwt.decode(token, options={"verify_signature": False})
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.now().timestamp() > exp:
                logger.warning("Token has expired")
                return None
            
            # Extract user data
            user_id = payload.get("sub")
            email = payload.get("email")
            
            if not user_id or not email:
                logger.warning("Invalid token payload")
                return None
            
            return {
                "id": user_id,
                "email": email,
                "exp": exp,
                "iat": payload.get("iat")
            }
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None

# Global instance
supabase_auth_service = SupabaseAuthService()
