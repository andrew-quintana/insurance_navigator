"""
Simple FastAPI monitoring service for Phase 1 testing
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
import time
from datetime import datetime

app = FastAPI(title="Phase 1 Monitoring Service", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "phase1-monitoring",
            "version": "1.0.0"
        }
    )

@app.get("/metrics")
async def get_metrics():
    """Basic metrics endpoint"""
    return JSONResponse(
        status_code=200,
        content={
            "uptime": time.time(),
            "timestamp": datetime.now().isoformat(),
            "environment": os.getenv("MONITORING_ENVIRONMENT", "workflow_testing"),
            "postgres_connected": bool(os.getenv("POSTGRES_URL"))
        }
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse(
        status_code=200,
        content={
            "message": "Phase 1 Monitoring Service",
            "version": "1.0.0",
            "endpoints": ["/health", "/metrics"]
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
