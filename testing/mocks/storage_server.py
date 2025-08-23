"""
Mock Storage Service for Local Development
This service simulates the Supabase storage API for local testing.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import logging
from datetime import datetime, timedelta
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock Storage Service", version="1.0.0")

# In-memory storage for testing
storage_buckets = {
    "raw": {},
    "parsed": {},
    "files": {}
}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mock-storage", "timestamp": datetime.utcnow().isoformat()}

@app.get("/storage/v1/object/upload/{path:path}")
async def get_upload_url(path: str):
    """Mock endpoint for file uploads - returns a success response"""
    logger.info(f"Mock upload request for path: {path}")
    
    # Store the path for later retrieval
    file_id = str(uuid.uuid4())
    storage_buckets["files"][file_id] = {
        "path": path,
        "uploaded_at": datetime.utcnow().isoformat(),
        "status": "uploaded"
    }
    
    return {
        "message": "Mock upload endpoint - file would be uploaded here",
        "file_id": file_id,
        "path": path,
        "status": "ready_for_upload"
    }

@app.post("/storage/v1/object/sign/{bucket}/{path:path}")
async def create_signed_url(bucket: str, path: str):
    """Mock signed URL creation"""
    logger.info(f"Mock signed URL request for bucket: {bucket}, path: {path}")
    
    # Generate a mock signed URL
    signed_url = f"http://localhost:5001/storage/v1/object/download/{bucket}/{path}?signed=true&ttl=300"
    
    return {
        "signedUrl": signed_url,
        "expiresAt": (datetime.utcnow() + timedelta(seconds=300)).isoformat()
    }

@app.get("/storage/v1/object/download/{bucket}/{path:path}")
async def download_file(bucket: str, path: str):
    """Mock file download endpoint"""
    logger.info(f"Mock download request for bucket: {bucket}, path: {path}")
    
    # Return mock file content
    mock_content = f"Mock file content for {bucket}/{path}\nGenerated at: {datetime.utcnow().isoformat()}"
    
    return JSONResponse(
        content={"content": mock_content, "bucket": bucket, "path": path},
        status_code=200
    )

@app.get("/storage/v1/bucket/{bucket}/object/list")
async def list_objects(bucket: str):
    """Mock object listing endpoint"""
    logger.info(f"Mock list request for bucket: {bucket}")
    
    if bucket not in storage_buckets:
        return {"data": [], "error": f"Bucket {bucket} not found"}
    
    objects = []
    for file_id, file_info in storage_buckets[bucket].items():
        objects.append({
            "id": file_id,
            "name": file_info["path"].split("/")[-1],
            "path": file_info["path"],
            "created_at": file_info["uploaded_at"]
        })
    
    return {"data": objects}

@app.delete("/storage/v1/object/{bucket}/{path:path}")
async def delete_file(bucket: str, path: str):
    """Mock file deletion endpoint"""
    logger.info(f"Mock delete request for bucket: {bucket}, path: {path}")
    
    # Remove from storage
    for file_id, file_info in list(storage_buckets.get(bucket, {}).items()):
        if file_info["path"] == path:
            del storage_buckets[bucket][file_id]
            break
    
    return {"message": f"File {path} deleted from bucket {bucket}"}

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Mock Storage Service",
        "version": "1.0.0",
        "description": "Local development storage service for testing",
        "endpoints": {
            "health": "/health",
            "upload": "/storage/v1/object/upload/{path}",
            "download": "/storage/v1/object/download/{bucket}/{path}",
            "signed_url": "/storage/v1/object/sign/{bucket}/{path}",
            "list": "/storage/v1/bucket/{bucket}/object/list",
            "delete": "/storage/v1/object/{bucket}/{path}"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
