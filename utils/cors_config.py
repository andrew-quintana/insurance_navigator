"""
Centralized CORS Configuration
Similar to Supabase's cors.ts approach but for FastAPI
"""
import os
import re
from typing import List, Dict, Any
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware


class CORSConfig:
    """Centralized CORS configuration management"""
    
    def __init__(self):
        self.allowed_origins = [
            "http://localhost:3000",
            "https://insurance-navigator.vercel.app",
            "https://insurance-navigator-staging.vercel.app",
            "https://insurance-navigator-dev.vercel.app",
            # Add any additional origins as needed
        ]
        
        # Allow any origin in development
        if os.getenv("ENVIRONMENT") == "development":
            self.allowed_origins.append("*")
            
        self.allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"]
        self.allowed_headers = [
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "Accept",
            "Origin",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers",
            "X-CSRF-Token",
            "X-Socket-ID",  # For WebSocket connections
            "X-Client-Version",
            "X-Device-ID"
        ]
        self.expose_headers = [
            "Content-Length",
            "Content-Range",
            "X-Total-Count",
            "X-Processing-Status"  # For document processing status
        ]
        self.max_age = 600  # 10 minutes
        
    def get_fastapi_cors_middleware_config(self) -> Dict[str, Any]:
        """Get CORS middleware configuration for FastAPI."""
        return {
            "allow_origins": self.allowed_origins,
            "allow_credentials": True,
            "allow_methods": self.allowed_methods,
            "allow_headers": self.allowed_headers,
            "expose_headers": self.expose_headers,
            "max_age": self.max_age
        }
    
    def create_preflight_response(self, origin: str) -> Dict[str, str]:
        """Create CORS preflight response headers."""
        return {
            "Access-Control-Allow-Origin": origin if origin in self.allowed_origins else self.allowed_origins[0],
            "Access-Control-Allow-Methods": ", ".join(self.allowed_methods),
            "Access-Control-Allow-Headers": ", ".join(self.allowed_headers),
            "Access-Control-Expose-Headers": ", ".join(self.expose_headers),
            "Access-Control-Max-Age": str(self.max_age),
            "Access-Control-Allow-Credentials": "true"
        }
    
    def add_cors_headers(self, headers: Dict[str, str], origin: str) -> Dict[str, str]:
        """Add CORS headers to response."""
        headers.update({
            "Access-Control-Allow-Origin": origin if origin in self.allowed_origins else self.allowed_origins[0],
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Expose-Headers": ", ".join(self.expose_headers)
        })
        return headers


# Global CORS configuration instance
cors_config = CORSConfig()

# Convenience functions for easy import/use
def get_cors_headers(origin: str = None) -> Dict[str, str]:
    """Get CORS headers for manual response handling"""
    return cors_config.get_cors_headers(origin)

def add_cors_headers(response: Response, origin: str = None):
    """Add CORS headers to a response"""
    cors_config.add_cors_headers(response, origin)

def create_preflight_response(origin: str = None) -> Response:
    """Create a preflight response"""
    return cors_config.create_preflight_response(origin)

def is_origin_allowed(origin: str) -> bool:
    """Check if origin is allowed"""
    return origin in cors_config.allowed_origins 