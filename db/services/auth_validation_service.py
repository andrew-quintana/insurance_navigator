"""
Simple authentication validation service for MVP.
Provides basic input validation, duplicate checking, and error handling.
"""

import re
import logging
from typing import Dict, Any, Optional, List
from config.database import get_supabase_service_client

logger = logging.getLogger(__name__)

class AuthValidationService:
    """Simple validation service for authentication endpoints."""
    
    def __init__(self):
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
    def validate_email(self, email: str) -> Dict[str, Any]:
        """Validate email format and return validation result."""
        if not email or not isinstance(email, str):
            return {"valid": False, "error": "Email is required"}
        
        email = email.strip().lower()
        
        if len(email) > 254:  # RFC 5321 limit
            return {"valid": False, "error": "Email is too long"}
        
        if not self.email_pattern.match(email):
            return {"valid": False, "error": "Invalid email format"}
        
        return {"valid": True, "email": email}
    
    def validate_password(self, password: str) -> Dict[str, Any]:
        """Validate password strength for MVP."""
        if not password or not isinstance(password, str):
            return {"valid": False, "error": "Password is required"}
        
        if len(password) < 8:
            return {"valid": False, "error": "Password must be at least 8 characters long"}
        
        if len(password) > 128:
            return {"valid": False, "error": "Password is too long"}
        
        # Basic password requirements for MVP
        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)
        
        if not has_letter:
            return {"valid": False, "error": "Password must contain at least one letter"}
        
        if not has_number:
            return {"valid": False, "error": "Password must contain at least one number"}
        
        return {"valid": True}
    
    def validate_name(self, name: str) -> Dict[str, Any]:
        """Validate name field."""
        if not name or not isinstance(name, str):
            return {"valid": False, "error": "Name is required"}
        
        name = name.strip()
        
        if len(name) < 2:
            return {"valid": False, "error": "Name must be at least 2 characters long"}
        
        if len(name) > 100:
            return {"valid": False, "error": "Name is too long"}
        
        # Check for basic characters (allow unicode for international names)
        if not re.match(r'^[\w\s\-\.\']+$', name):
            return {"valid": False, "error": "Name contains invalid characters"}
        
        return {"valid": True, "name": name}
    
    async def check_email_exists(self, email: str) -> Dict[str, Any]:
        """Check if email already exists in database."""
        try:
            service_client = await get_supabase_service_client()
            
            # Check if user exists with this email
            result = service_client.table("users").select("id").eq("email", email.lower()).execute()
            
            exists = len(result.data) > 0 if result.data else False
            
            return {
                "exists": exists,
                "error": "Email already registered" if exists else None
            }
            
        except Exception as e:
            logger.error(f"Error checking email existence: {str(e)}")
            # For MVP, if we can't check, allow registration to proceed
            return {"exists": False, "error": None}
    
    def validate_registration_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete registration data."""
        errors = []
        validated_data = {}
        
        # Validate email
        email_validation = self.validate_email(data.get("email", ""))
        if not email_validation["valid"]:
            errors.append(email_validation["error"])
        else:
            validated_data["email"] = email_validation["email"]
        
        # Validate password
        password_validation = self.validate_password(data.get("password", ""))
        if not password_validation["valid"]:
            errors.append(password_validation["error"])
        
        # Validate name
        name_validation = self.validate_name(data.get("name", ""))
        if not name_validation["valid"]:
            errors.append(name_validation["error"])
        else:
            validated_data["name"] = name_validation["name"]
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "data": validated_data
        }
    
    def validate_login_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate login data."""
        errors = []
        validated_data = {}
        
        # Validate email
        email_validation = self.validate_email(data.get("email", ""))
        if not email_validation["valid"]:
            errors.append(email_validation["error"])
        else:
            validated_data["email"] = email_validation["email"]
        
        # Validate password (basic check)
        password = data.get("password", "")
        if not password or not isinstance(password, str):
            errors.append("Password is required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "data": validated_data
        }
    
    def create_error_response(self, errors: List[str], status_code: int = 400) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "error": "Validation failed",
            "message": "; ".join(errors),
            "status_code": status_code,
            "details": errors
        }

# Global validation service instance
auth_validation_service = AuthValidationService()
