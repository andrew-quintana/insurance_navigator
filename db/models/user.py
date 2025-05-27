"""
User model and authentication utilities for Medicare Navigator
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import jwt
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration imports - secure configuration module
from utils.security_config import get_security_config

# Database setup
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get security configuration
security_config = get_security_config()

# JWT configuration - now loaded from centralized security config
SECRET_KEY = security_config.jwt_secret_key
ALGORITHM = security_config.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = security_config.access_token_expire_minutes

class User(Base):
    """User model for authentication and session management"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}', full_name='{self.full_name}')>"

class UserAuthentication:
    """Handles user authentication operations"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            raise ValueError("Invalid token")
    
    @staticmethod
    def extract_user_email(token: str) -> str:
        """Extract user email from token"""
        payload = UserAuthentication.verify_token(token)
        email = payload.get("sub")
        if email is None:
            raise ValueError("Token missing user information")
        return email

class UserService:
    """Service class for user operations"""
    
    def __init__(self):
        # For now, using in-memory storage
        # In production, this would use the database
        self.users_storage: Dict[str, Dict[str, Any]] = {}
    
    def create_user(self, email: str, password: str, full_name: str) -> Dict[str, Any]:
        """Create a new user"""
        if email in self.users_storage:
            raise ValueError("User already exists")
        
        user_id = f"user_{len(self.users_storage) + 1}"
        hashed_password = UserAuthentication.get_password_hash(password)
        
        user_data = {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow()
        }
        
        self.users_storage[email] = user_data
        
        # Return user data without password
        return {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "created_at": user_data["created_at"]
        }
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        user_data = self.users_storage.get(email)
        if not user_data:
            return None
        
        if not UserAuthentication.verify_password(password, user_data["hashed_password"]):
            return None
        
        # Return user data without password
        return {
            "id": user_data["id"],
            "email": user_data["email"],
            "full_name": user_data["full_name"],
            "created_at": user_data["created_at"]
        }
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        user_data = self.users_storage.get(email)
        if not user_data:
            return None
        
        # Return user data without password
        return {
            "id": user_data["id"],
            "email": user_data["email"],
            "full_name": user_data["full_name"],
            "created_at": user_data["created_at"]
        }
    
    def create_session(self, email: str) -> str:
        """Create a new session for user"""
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = UserAuthentication.create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        return access_token
    
    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate user session token"""
        try:
            email = UserAuthentication.extract_user_email(token)
            return self.get_user_by_email(email)
        except ValueError:
            return None

# Global user service instance
user_service = UserService()

def get_user_service() -> UserService:
    """Get the global user service instance"""
    return user_service 