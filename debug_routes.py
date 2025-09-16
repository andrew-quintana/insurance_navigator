#!/usr/bin/env python3
"""
Debug script to check FastAPI routes and router inclusion.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app

print("=== FastAPI App Routes ===")
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        print(f"{route.path}: {list(route.methods)}")
    elif hasattr(route, 'path'):
        print(f"{route.path}: {type(route).__name__}")

print("\n=== Upload Pipeline Routes ===")
for route in app.routes:
    if hasattr(route, 'path') and 'upload-pipeline' in route.path:
        print(f"{route.path}: {list(route.methods) if hasattr(route, 'methods') else 'No methods'}")

print("\n=== Router Inclusion Test ===")
try:
    from api.upload_pipeline.endpoints.upload import router as upload_router
    print(f"Upload router imported successfully")
    print(f"Upload router routes: {[route.path for route in upload_router.routes]}")
except Exception as e:
    print(f"Error importing upload router: {e}")

print("\n=== Webhook Router Test ===")
try:
    from api.upload_pipeline.webhooks import router as webhook_router
    print(f"Webhook router imported successfully")
    print(f"Webhook router routes: {[route.path for route in webhook_router.routes]}")
except Exception as e:
    print(f"Error importing webhook router: {e}")
