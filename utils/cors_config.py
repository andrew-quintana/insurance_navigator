"""
Centralized CORS Configuration
"""
from typing import Dict, Any
from fastapi import Request

class CORSConfig:
    """Centralized CORS configuration management"""
    
    def __init__(self):
        """Initialize CORS configuration."""
        self.allowed_origins = [
            "http://localhost:3000",
            "http://localhost:8080",
            "https://insurance-navigator.vercel.app",
            "https://insurance-navigator-staging.vercel.app",
            "https://insurance-navigator-hr7oebcu2-andrew-quintanas-projects.vercel.app"
        ]
        self.allow_credentials = True
        self.allow_methods = ["*"]
        self.allow_headers = ["*"]
        self.max_age = 600

    def get_fastapi_cors_middleware_config(self) -> Dict[str, Any]:
        """Get FastAPI CORS middleware configuration."""
        return {
            "allow_origins": self.allowed_origins,
            "allow_credentials": self.allow_credentials,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
            "allow_headers": ["*"],
            "max_age": self.max_age,
            "expose_headers": ["*"]
        }

# Global CORS configuration instance
cors_config = CORSConfig() 