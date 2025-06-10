"""
Examples of using centralized CORS configuration
Similar to Supabase's approach but for FastAPI
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from utils.cors_config import cors_config, get_cors_headers, add_cors_headers, create_preflight_response
import json

# Example 1: Manual response handling (like Supabase's approach)
def manual_cors_example():
    """Example of manually adding CORS headers to responses"""
    
    app = FastAPI()
    
    @app.get("/api/data")
    async def get_data(request: Request):
        origin = request.headers.get("origin")
        
        # Your API logic here
        data = {"message": "Hello from API"}
        
        # Create response with CORS headers
        response = Response(
            content=json.dumps(data),
            media_type="application/json"
        )
        
        # Add CORS headers using centralized config
        add_cors_headers(response, origin)
        
        return response
    
    @app.options("/api/data")
    async def preflight_data(request: Request):
        """Handle preflight requests"""
        origin = request.headers.get("origin")
        return create_preflight_response(origin)


# Example 2: Using FastAPI's built-in CORSMiddleware with centralized config
def middleware_cors_example():
    """Example of using FastAPI CORSMiddleware with centralized configuration"""
    
    app = FastAPI()
    
    # Apply centralized CORS configuration to FastAPI middleware
    cors_config_dict = cors_config.get_fastapi_cors_middleware_config()
    app.add_middleware(CORSMiddleware, **cors_config_dict)
    
    @app.get("/api/data")
    async def get_data():
        return {"message": "CORS handled by middleware"}


# Example 3: Custom middleware (current approach in main.py)
def custom_middleware_example():
    """Example of custom CORS middleware using centralized configuration"""
    
    from starlette.middleware.base import BaseHTTPMiddleware
    
    class CustomCORSMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            origin = request.headers.get("origin")
            
            # Handle preflight requests
            if request.method == "OPTIONS":
                return create_preflight_response(origin)
            
            # Process request and add CORS headers to response
            response = await call_next(request)
            add_cors_headers(response, origin)
            
            return response
    
    app = FastAPI()
    app.add_middleware(CustomCORSMiddleware)


# Example 4: Edge function style (inspired by Supabase)
def edge_function_style_example():
    """Example mimicking Supabase's edge function CORS handling"""
    
    app = FastAPI()
    
    @app.api_route("/api/function", methods=["GET", "POST", "OPTIONS"])
    async def my_function(request: Request):
        origin = request.headers.get("origin")
        
        # Handle preflight like Supabase edge functions
        if request.method == "OPTIONS":
            return create_preflight_response(origin)
        
        try:
            # Your function logic here
            if request.method == "GET":
                data = {"message": "Hello from function"}
            else:  # POST
                request_data = await request.json()
                name = request_data.get("name", "World")
                data = {"message": f"Hello {name}!"}
            
            # Create response with CORS headers (Supabase style)
            headers = get_cors_headers(origin)
            headers["Content-Type"] = "application/json"
            
            return Response(
                content=json.dumps(data),
                headers=headers,
                status_code=200
            )
            
        except Exception as error:
            # Error handling with CORS headers
            headers = get_cors_headers(origin)
            headers["Content-Type"] = "application/json"
            
            return Response(
                content=json.dumps({"error": str(error)}),
                headers=headers,
                status_code=400
            )


# Example 5: Environment-based configuration
def environment_configuration_example():
    """Example showing how the configuration adapts to different environments"""
    
    import os
    
    # In development
    os.environ["CORS_ALLOWED_ORIGINS"] = "http://localhost:3000,http://localhost:3001"
    
    # In production  
    os.environ["CORS_ALLOWED_ORIGINS"] = "https://myapp.vercel.app,https://myapp.com"
    
    # With Vercel preview pattern
    os.environ["CORS_VERCEL_PREVIEW_PATTERN"] = "myapp-[a-z0-9]+-user-projects\.vercel\.app"
    
    # The configuration automatically loads these values
    print(f"Loaded origins: {cors_config.allowed_origins}")
    print(f"Origin check for localhost:3000: {cors_config.is_origin_allowed('http://localhost:3000')}")


if __name__ == "__main__":
    # Test the configuration
    environment_configuration_example() 