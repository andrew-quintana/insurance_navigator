#!/usr/bin/env python3
"""
Test script for centralized CORS configuration
"""

import os
import sys
sys.path.append('.')

from utils.cors_config import cors_config, get_cors_headers, is_origin_allowed

def test_origin_validation():
    """Test origin validation logic"""
    print("🧪 Testing Origin Validation")
    
    # Test cases
    test_cases = [
        # Should be allowed
        ("http://localhost:3000", True, "Localhost development"),
        ("http://127.0.0.1:3001", True, "Localhost IP"),
        ("https://insurance-navigator.vercel.app", True, "Production Vercel"),
        ("https://insurance-navigator-e3j4jn4xj-andrew-quintanas-projects.vercel.app", True, "Vercel preview"),
        ("https://some-other-app-abc123def-user-projects.vercel.app", True, "Generic Vercel"),
        
        # Should be rejected
        ("https://malicious-site.com", False, "Malicious site"),
        ("http://evil.localhost.com", False, "Fake localhost"),
        ("", False, "Empty origin"),
    ]
    
    for origin, expected, description in test_cases:
        result = is_origin_allowed(origin)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {description}: {origin} -> {result}")
        
        if result != expected:
            print(f"    Expected: {expected}, Got: {result}")

def test_cors_headers():
    """Test CORS header generation"""
    print("\n🧪 Testing CORS Headers")
    
    # Test with allowed origin
    allowed_origin = "https://insurance-navigator.vercel.app"
    headers = get_cors_headers(allowed_origin)
    
    print(f"  Headers for {allowed_origin}:")
    for key, value in headers.items():
        print(f"    {key}: {value}")
    
    # Test with disallowed origin
    disallowed_origin = "https://malicious-site.com"
    headers_disallowed = get_cors_headers(disallowed_origin)
    
    print(f"\n  Headers for disallowed origin {disallowed_origin}:")
    for key, value in headers_disallowed.items():
        print(f"    {key}: {value}")

def test_environment_loading():
    """Test environment variable loading"""
    print("\n🧪 Testing Environment Loading")
    
    print(f"  Allowed origins: {cors_config.allowed_origins}")
    print(f"  Pattern compilation: {cors_config.patterns}")
    
    # Test environment override
    original_origins = os.getenv('CORS_ALLOWED_ORIGINS', '')
    print(f"  Current CORS_ALLOWED_ORIGINS: {original_origins}")

def test_fastapi_middleware_config():
    """Test FastAPI middleware configuration"""
    print("\n🧪 Testing FastAPI Middleware Config")
    
    config = cors_config.get_fastapi_cors_middleware_config()
    
    print("  FastAPI CORSMiddleware configuration:")
    for key, value in config.items():
        print(f"    {key}: {value}")

def main():
    """Run all tests"""
    print("🎯 Centralized CORS Configuration Test")
    print("=" * 50)
    
    test_origin_validation()
    test_cors_headers()
    test_environment_loading()
    test_fastapi_middleware_config()
    
    print("\n✅ All tests completed!")
    print("\n📋 Configuration Summary:")
    print(f"  - Total allowed origins: {len(cors_config.allowed_origins)}")
    print(f"  - Credentials enabled: {cors_config.allow_credentials}")
    print(f"  - Max age: {cors_config.max_age} seconds")
    print(f"  - Allowed methods: {', '.join(cors_config.allowed_methods)}")

if __name__ == "__main__":
    main() 