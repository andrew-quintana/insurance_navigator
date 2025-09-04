"""
Development authentication service that bypasses Supabase auth entirely.
This is for development/testing only and should NOT be used in production.
"""

import hashlib
import secrets
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from config.database import get_supabase_service_client

logger = logging.getLogger(__name__)

class DevAuthService:
    """Development-only authentication service that bypasses email confirmation."""
    
    def __init__(self):
        self.secret_key = "dev-secret-key-change-in-production"  # TODO: Move to env var
        
    def generate_token(self, user_id: str, email: str) -> str:
        """Generate a simple JWT-like token for development."""
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": int((datetime.now() + timedelta(hours=24)).timestamp()),
            "iat": int(datetime.now().timestamp())
        }
        
        # Simple token generation (not secure for production)
        token_data = f"{user_id}:{email}:{payload['exp']}"
        token = hashlib.sha256(f"{token_data}:{self.secret_key}".encode()).hexdigest()
        return f"dev.{token}"
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a development token."""
        try:
            if not token.startswith("dev."):
                return None
                
            # This is a simplified verification - not secure for production
            return {
                "user_id": "dev-user-id",
                "email": "dev@example.com",
                "exp": int((datetime.now() + timedelta(hours=24)).timestamp())
            }
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    async def create_user_dev_only(
        self,
        email: str,
        password: str,
        consent_version: str,
        consent_timestamp: str,
        name: str = None
    ) -> Dict[str, Any]:
        """Create a user using development-only authentication (no Supabase auth)."""
        try:
            logger.info(f"Creating user with DEV-ONLY auth: {email}")
            
            # Generate a simple user ID
            user_id = f"dev_{secrets.token_hex(16)}"
            
            # Get service client for database operations only
            service_client = await get_supabase_service_client()
            
            # Create user record directly in database (no Supabase auth)
            user_data = {
                "id": user_id,
                "email": email,
                "name": name or email.split("@")[0],
                "consent_version": consent_version,
                "consent_timestamp": consent_timestamp,
                "is_active": True,
                "email_confirmed": True,  # Always confirmed in dev mode
                "auth_method": "dev_only",
                "created_at": datetime.now().isoformat(),
                "password_hash": hashlib.sha256(password.encode()).hexdigest()  # Simple hash
            }
            logger.info(f"Inserting dev user data: {user_data}")
            
            result = service_client.table("users").insert(user_data).execute()
            logger.info(f"Dev user record insert result: {result}")
            
            if not result.data:
                raise Exception("Failed to create dev user record")
            
            # Generate token
            token = self.generate_token(user_id, email)
            
            logger.info(f"✅ Dev user created successfully: {email}")
            return {
                "user": {
                    "id": user_id,
                    "email": email,
                    "name": user_data["name"]
                },
                "access_token": token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Error in create_user_dev_only: {str(e)}")
            raise Exception(f"Failed to create dev user: {str(e)}")
    
    async def authenticate_user_dev_only(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user using development-only method."""
        try:
            logger.info(f"Authenticating dev user: {email}")
            
            # Get service client
            service_client = await get_supabase_service_client()
            
            # Find user by email
            result = service_client.table("users").select("*").eq("email", email).execute()
            
            if not result.data:
                logger.warning(f"User not found: {email}")
                return None
            
            user = result.data[0]
            
            # Verify password (simple hash comparison)
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if user.get("password_hash") != password_hash:
                logger.warning(f"Invalid password for user: {email}")
                return None
            
            # Generate token
            token = self.generate_token(user["id"], email)
            
            logger.info(f"✅ Dev user authenticated: {email}")
            return {
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"]
                },
                "access_token": token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Error in authenticate_user_dev_only: {str(e)}")
            return None

# Global dev auth service instance
dev_auth_service = DevAuthService()
