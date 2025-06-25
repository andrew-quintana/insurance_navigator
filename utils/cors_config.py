"""
Centralized CORS Configuration
"""
from typing import Dict, Any
import os

class CORSConfig:
    """Centralized CORS configuration management"""
    
    def __init__(self):
        """Initialize CORS configuration."""
        # Base allowed origins
        base_origins = [
            "http://localhost:3000",
            "http://localhost:8080",
            "https://insurance-navigator.vercel.app",
            "https://insurance-navigator-staging.vercel.app",
            "https://insurance-navigator-7ehumqaks-andrew-quintanas-projects.vercel.app"
        ]
        
        # Add any additional origins from environment variable
        env_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
        self.allowed_origins = list(set(base_origins + [origin.strip() for origin in env_origins if origin.strip()]))
        
        # Standard CORS settings following Supabase best practices
        self.allow_credentials = True
        self.allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"]
        self.allow_headers = [
            "authorization",
            "x-client-info",
            "apikey",
            "content-type",
            "x-webhook-signature",
            "x-user-id",
            "accept",
            "origin",
            "x-requested-with"
        ]
        self.expose_headers = ["content-length", "content-range"]
        self.max_age = 7200  # 2 hours, following Supabase's practice

    def get_fastapi_cors_middleware_config(self) -> Dict[str, Any]:
        """Get FastAPI CORS middleware configuration."""
        return {
            "allow_origins": self.allowed_origins,
            "allow_credentials": self.allow_credentials,
            "allow_methods": self.allow_methods,
            "allow_headers": self.allow_headers,
            "expose_headers": self.expose_headers,
            "max_age": self.max_age
        }

    def get_headers_for_origin(self, origin: str | None) -> Dict[str, str]:
        """Get CORS headers for a specific origin."""
        if not origin or origin not in self.allowed_origins:
            # Default to first allowed origin if none matches
            origin = self.allowed_origins[0]
        
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": str(self.allow_credentials).lower(),
            "Access-Control-Allow-Methods": ", ".join(self.allow_methods),
            "Access-Control-Allow-Headers": ", ".join(self.allow_headers),
            "Access-Control-Expose-Headers": ", ".join(self.expose_headers),
            "Access-Control-Max-Age": str(self.max_age),
            "Vary": "Origin"
        }

# Global CORS configuration instance
cors_config = CORSConfig()