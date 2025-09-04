"""
Simple authentication service v2 that uses Supabase client instead of direct database access.
This version is more compatible with the existing infrastructure.
"""

import hashlib
import secrets
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from config.database import get_supabase_service_client

logger = logging.getLogger(__name__)

class SimpleAuthServiceV2:
    """Simple authentication service that uses Supabase client for database operations."""
    
    def __init__(self):
        self.secret_key = "simple-dev-secret-key-v2"  # TODO: Move to env var
        
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
        return f"simple.{token}"
    
    async def create_user_simple(
        self,
        email: str,
        password: str,
        consent_version: str,
        consent_timestamp: str,
        name: str = None
    ) -> Dict[str, Any]:
        """Create a user using simple database-only authentication."""
        try:
            logger.info(f"Creating user with SIMPLE auth v2: {email}")
            
            # Generate a unique user ID
            user_id = f"simple_{secrets.token_hex(16)}"
            
            # Hash password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Get Supabase service client for database operations
            service_client = await get_supabase_service_client()
            
            # Create user record directly in database using Supabase client
            user_data = {
                "id": user_id,
                "email": email,
                "name": name or email.split("@")[0],
                "consent_version": consent_version,
                "consent_timestamp": consent_timestamp,
                "is_active": True,
                "email_confirmed": True,  # Always confirmed in dev mode
                "auth_method": "simple_auth_v2",
                "created_at": datetime.now().isoformat(),
                "password_hash": password_hash
            }
            
            logger.info(f"Inserting simple user data: {user_data}")
            
            # Insert user using Supabase client
            result = service_client.table("users").insert(user_data).execute()
            logger.info(f"Simple user insert result: {result}")
            
            if not result.data:
                raise Exception("Failed to create simple user record")
            
            # Generate token
            token = self.generate_token(user_id, email)
            
            logger.info(f"✅ Simple user created successfully: {email}")
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
            logger.error(f"Error in create_user_simple: {str(e)}")
            raise Exception(f"Failed to create simple user: {str(e)}")
    
    async def authenticate_user_simple(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user using simple database lookup."""
        try:
            logger.info(f"Authenticating simple user: {email}")
            
            # Hash password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Get Supabase service client
            service_client = await get_supabase_service_client()
            
            # Find user in database using Supabase client
            result = service_client.table("users").select("*").eq("email", email).eq("password_hash", password_hash).eq("is_active", True).execute()
            
            if not result.data:
                logger.warning(f"User not found or invalid password: {email}")
                return None
            
            user = result.data[0]
            
            # Generate token
            token = self.generate_token(user["id"], user["email"])
            
            logger.info(f"✅ Simple user authenticated: {email}")
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
            logger.error(f"Error in authenticate_user_simple: {str(e)}")
            return None

# Global simple auth service instance
simple_auth_service_v2 = SimpleAuthServiceV2()
