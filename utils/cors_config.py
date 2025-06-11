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
        self.is_development = os.getenv('NODE_ENV', 'development') != 'production'
        self.allowed_origins = self._load_allowed_origins()
        self.allowed_headers = [
            "authorization", 
            "x-client-info", 
            "apikey", 
            "content-type",
            "accept",
            "origin",
            "x-requested-with"
        ]
        self.allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"]
        self.expose_headers = ["*"]
        self.max_age = 86400  # 24 hours
        self.allow_credentials = True
        
        # Compile regex patterns for efficient matching
        self.patterns = self._compile_patterns()
    
    def _load_allowed_origins(self) -> List[str]:
        """Load allowed origins from environment variables"""
        # Get explicit origins from environment
        cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
        cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]
        
        # Add default localhost origins for development
        default_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000", 
            "http://127.0.0.1:3001"
        ]
        
        # Add known production/staging origins
        production_origins = [
            "https://insurance-navigator-staging.vercel.app",
            "https://insurance-navigator.vercel.app",
            # Add specific problematic URLs that were reported
            "https://insurance-navigator-ajzpmcvgz-andrew-quintanas-projects.vercel.app",
            "https://insurance-navigator-cwtwocttv-andrew-quintanas-projects.vercel.app"
        ]
        
        # Combine and deduplicate
        all_origins = list(set(cors_origins + default_origins + production_origins))
        return all_origins
    
    def _compile_patterns(self) -> Dict[str, Any]:
        """Compile regex patterns for dynamic origin matching"""
        # More flexible Vercel pattern that handles all deployment variations
        vercel_pattern = os.getenv(
            'CORS_VERCEL_PREVIEW_PATTERN', 
            'insurance-navigator-[a-z0-9]+-andrew-quintanas-projects\.vercel\.app'
        )
        
        return {
            'localhost': re.compile(r'^(localhost|127\.0\.0\.1)(:\d+)?$'),
            'vercel_preview': re.compile(f'^{vercel_pattern}$'),
            'vercel_all': re.compile(r'^[a-z0-9-]+\.vercel\.app$'),
            # More flexible pattern for insurance navigator preview deployments
            'insurance_navigator_vercel': re.compile(r'^insurance-navigator-[a-z0-9]+[a-z0-9\-]*-andrew-quintanas-projects\.vercel\.app$'),
        }
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Check if an origin is allowed"""
        if not origin:
            return False
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(origin)
            domain = parsed.netloc.lower()
            
            # Check explicit allowed origins
            if origin in self.allowed_origins or f"https://{domain}" in self.allowed_origins:
                return True
            
            # Check localhost patterns
            if self.patterns['localhost'].match(domain):
                return True
            
            # Check Vercel preview pattern
            if self.patterns['vercel_preview'].match(domain):
                return True
            
            # Check insurance navigator specific pattern
            if self.patterns['insurance_navigator_vercel'].match(domain):
                return True
            
            # In development mode, be more permissive with Vercel deployments
            if self.is_development and domain.endswith('.vercel.app'):
                # Allow any insurance-navigator related Vercel deployment in development
                if 'insurance-navigator' in domain and 'andrew-quintanas-projects' in domain:
                    return True
            
            # Check any Vercel deployment (broader fallback)
            if self.patterns['vercel_all'].match(domain):
                return True
                
        except Exception as e:
            print(f"CORS origin validation error for {origin}: {e}")
            return False
        
        return False
    
    def get_cors_headers(self, origin: str = None) -> Dict[str, str]:
        """Get CORS headers for response"""
        headers = {
            "Access-Control-Allow-Methods": ", ".join(self.allowed_methods),
            "Access-Control-Allow-Headers": ", ".join(self.allowed_headers),
            "Access-Control-Expose-Headers": ", ".join(self.expose_headers),
            "Access-Control-Max-Age": str(self.max_age),
        }
        
        if self.allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"
        
        # Set origin-specific header
        if origin and self.is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin
        else:
            # Fallback for development (be more restrictive in production)
            headers["Access-Control-Allow-Origin"] = "*"
        
        return headers
    
    def add_cors_headers(self, response: Response, origin: str = None):
        """Add CORS headers to a response"""
        headers = self.get_cors_headers(origin)
        for key, value in headers.items():
            response.headers[key] = value
    
    def create_preflight_response(self, origin: str = None) -> Response:
        """Create a preflight (OPTIONS) response"""
        response = Response()
        self.add_cors_headers(response, origin)
        return response
    
    def get_fastapi_cors_middleware_config(self) -> Dict[str, Any]:
        """Get configuration for FastAPI's CORSMiddleware"""
        # More flexible regex that handles all Vercel deployment variations
        vercel_regex = r"https://(insurance-navigator-[a-z0-9]+-andrew-quintanas-projects\.vercel\.app|[a-z0-9-]+\.vercel\.app)"
        
        return {
            "allow_origins": self.allowed_origins,
            "allow_origin_regex": vercel_regex,
            "allow_credentials": self.allow_credentials,
            "allow_methods": self.allowed_methods,
            "allow_headers": self.allowed_headers,
            "expose_headers": self.expose_headers,
            "max_age": self.max_age,
        }


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
    return cors_config.is_origin_allowed(origin) 