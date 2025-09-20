#!/usr/bin/env python3
"""
Debug script to check environment variables in Render
"""
import os

print("=== Environment Variables Debug ===")
print(f"PORT: {os.getenv('PORT', 'NOT SET')}")
print(f"API_HOST: {os.getenv('API_HOST', 'NOT SET')}")
print(f"API_PORT: {os.getenv('API_PORT', 'NOT SET')}")
print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'NOT SET')}")

print("\n=== All Environment Variables ===")
for key, value in sorted(os.environ.items()):
    if 'PORT' in key or 'API' in key or 'ENV' in key:
        print(f"{key}: {value}")

print("\n=== Port Configuration ===")
port = int(os.getenv("PORT", "8000"))
print(f"Using port: {port}")
print(f"Port type: {type(port)}")
