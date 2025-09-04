"""
Simple authentication service that completely bypasses Supabase for development.
This creates users directly in the database without any Supabase auth integration.
"""

import hashlib
import secrets
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import psycopg2
from config.database import db_pool

logger = logging.getLogger(__name__)

class SimpleAuthService:
    """Simple authentication service that bypasses Supabase entirely."""
    
    def __init__(self):
        self.secret_key = "simple-dev-secret-key"  # TODO: Move to env var
        
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
            logger.info(f"Creating user with SIMPLE auth: {email}")
            
            # Generate a unique user ID
            user_id = f"simple_{secrets.token_hex(16)}"
            
            # Hash password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Create user record directly in database
            async with db_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    # Insert user directly into users table
                    await cur.execute("""
                        INSERT INTO public.users (
                            id, email, name, consent_version, consent_timestamp, 
                            is_active, email_confirmed, auth_method, created_at, password_hash
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        user_id,
                        email,
                        name or email.split("@")[0],
                        consent_version,
                        consent_timestamp,
                        True,  # is_active
                        True,  # email_confirmed
                        "simple_auth",
                        datetime.now(),
                        password_hash
                    ))
                    
                    await conn.commit()
                    logger.info(f"User inserted into database: {user_id}")
            
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
            
            # Find user in database
            async with db_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        SELECT id, email, name, password_hash 
                        FROM public.users 
                        WHERE email = %s AND password_hash = %s AND is_active = true
                    """, (email, password_hash))
                    
                    result = await cur.fetchone()
                    
                    if not result:
                        logger.warning(f"User not found or invalid password: {email}")
                        return None
                    
                    user_id, user_email, user_name, _ = result
            
            # Generate token
            token = self.generate_token(user_id, user_email)
            
            logger.info(f"✅ Simple user authenticated: {email}")
            return {
                "user": {
                    "id": user_id,
                    "email": user_email,
                    "name": user_name
                },
                "access_token": token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Error in authenticate_user_simple: {str(e)}")
            return None

# Global simple auth service instance
simple_auth_service = SimpleAuthService()
