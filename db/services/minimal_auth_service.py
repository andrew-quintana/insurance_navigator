"""
Minimal authentication service for development that bypasses all database operations.
This is a temporary solution to get the project working.
"""

import hashlib
import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MinimalAuthService:
    """Minimal authentication service that bypasses all database operations."""
    
    def __init__(self):
        self.secret_key = "minimal-dev-secret-key"
        
    def generate_token(self, user_id: str, email: str) -> str:
        """Generate a simple token for development."""
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": int((datetime.now() + timedelta(hours=24)).timestamp()),
            "iat": int(datetime.now().timestamp())
        }
        
        # Simple token generation
        token_data = f"{user_id}:{email}:{payload['exp']}"
        token = hashlib.sha256(f"{token_data}:{self.secret_key}".encode()).hexdigest()
        return f"minimal.{token}"
    
    async def create_user_minimal(
        self,
        email: str,
        password: str,
        consent_version: str,
        consent_timestamp: str,
        name: str = None
    ) -> Dict[str, Any]:
        """Create a user using minimal authentication (no database operations)."""
        try:
            logger.info(f"Creating user with MINIMAL auth: {email}")
            
            # Generate a simple user ID
            user_id = f"minimal_{secrets.token_hex(16)}"
            
            # Generate token
            token = self.generate_token(user_id, email)
            
            logger.info(f"✅ Minimal user created successfully: {email}")
            return {
                "user": {
                    "id": user_id,
                    "email": email,
                    "name": name or email.split("@")[0]
                },
                "access_token": token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Error in create_user_minimal: {str(e)}")
            raise Exception(f"Failed to create minimal user: {str(e)}")
    
    async def authenticate_user_minimal(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user using minimal method (always succeeds for development)."""
        try:
            logger.info(f"Authenticating minimal user: {email}")
            
            # For development, always succeed
            user_id = f"minimal_{secrets.token_hex(16)}"
            token = self.generate_token(user_id, email)
            
            logger.info(f"✅ Minimal user authenticated: {email}")
            return {
                "user": {
                    "id": user_id,
                    "email": email,
                    "name": email.split("@")[0]
                },
                "access_token": token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Error in authenticate_user_minimal: {str(e)}")
            return None

# Global minimal auth service instance
minimal_auth_service = MinimalAuthService()
