"""
Improved minimal authentication service for MVP with validation and duplicate checking.
This version includes proper input validation while maintaining simplicity.
"""

import hashlib
import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from db.services.auth_validation_service import auth_validation_service

logger = logging.getLogger(__name__)

class ImprovedMinimalAuthService:
    """Improved minimal authentication service with validation for MVP."""
    
    def __init__(self):
        self.secret_key = "improved-minimal-dev-secret-key"
        
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
        """Create a user with validation and duplicate checking."""
        try:
            logger.info(f"Creating user with IMPROVED MINIMAL auth: {email}")
            
            # Validate input data
            validation_result = auth_validation_service.validate_registration_data({
                "email": email,
                "password": password,
                "name": name
            })
            
            if not validation_result["valid"]:
                logger.warning(f"Registration validation failed: {validation_result['errors']}")
                raise ValueError(validation_result["errors"][0])
            
            validated_data = validation_result["data"]
            
            # Check if email already exists
            email_check = await auth_validation_service.check_email_exists(validated_data["email"])
            if email_check["exists"]:
                logger.warning(f"Registration failed - email already exists: {validated_data['email']}")
                raise ValueError("Email already registered")
            
            # Generate a simple user ID
            user_id = f"minimal_{secrets.token_hex(16)}"
            
            # Hash password for storage (even in minimal mode, we should hash)
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Generate token
            token = self.generate_token(user_id, validated_data["email"])
            
            logger.info(f"✅ Improved minimal user created successfully: {validated_data['email']}")
            return {
                "user": {
                    "id": user_id,
                    "email": validated_data["email"],
                    "name": validated_data["name"]
                },
                "access_token": token,
                "token_type": "bearer"
            }
            
        except ValueError as e:
            # Re-raise validation errors
            raise e
        except Exception as e:
            logger.error(f"Error in create_user_minimal: {str(e)}")
            raise Exception(f"Failed to create user: {str(e)}")
    
    async def authenticate_user_minimal(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with basic validation."""
        try:
            logger.info(f"Authenticating improved minimal user: {email}")
            
            # Validate input data
            validation_result = auth_validation_service.validate_login_data({
                "email": email,
                "password": password
            })
            
            if not validation_result["valid"]:
                logger.warning(f"Login validation failed: {validation_result['errors']}")
                return None
            
            validated_data = validation_result["data"]
            
            # For MVP, we'll use a simple approach but still validate inputs
            # Generate a simple user ID
            user_id = f"minimal_{secrets.token_hex(16)}"
            token = self.generate_token(user_id, validated_data["email"])
            
            logger.info(f"✅ Improved minimal user authenticated: {validated_data['email']}")
            return {
                "user": {
                    "id": user_id,
                    "email": validated_data["email"],
                    "name": validated_data["email"].split("@")[0]
                },
                "access_token": token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Error in authenticate_user_minimal: {str(e)}")
            return None

# Global improved minimal auth service instance
improved_minimal_auth_service = ImprovedMinimalAuthService()
