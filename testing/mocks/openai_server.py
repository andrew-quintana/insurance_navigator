from fastapi import FastAPI, HTTPException, Request
import numpy as np
import hashlib
import os
import time
import asyncio
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock OpenAI Service", version="1.0.0")

# Configuration from environment variables
MOCK_OPENAI_DELAY = float(os.getenv("MOCK_OPENAI_DELAY", "1"))
MOCK_OPENAI_FAILURE_RATE = float(os.getenv("MOCK_OPENAI_FAILURE_RATE", "0.0"))

# Rate limiting simulation
request_times = []

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mock-openai", "timestamp": time.time()}

@app.post("/v1/embeddings")
async def create_embeddings(request: Request):
    """Mock OpenAI embeddings endpoint"""
    try:
        body = await request.json()
        input_texts = body.get("input", [])
        model = body.get("model", "text-embedding-3-small")
        
        if not input_texts:
            raise HTTPException(status_code=400, detail="No input texts provided")
        
        # Simulate rate limiting
        current_time = time.time()
        request_times.append(current_time)
        
        # Keep only requests from last minute
        request_times[:] = [t for t in request_times if current_time - t < 60]
        
        # Simulate rate limit (60 requests per minute)
        if len(request_times) > 60:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Simulate processing delay
        await asyncio.sleep(MOCK_OPENAI_DELAY)
        
        # Check if we should simulate failure
        if MOCK_OPENAI_FAILURE_RATE > 0 and np.random.random() < MOCK_OPENAI_FAILURE_RATE:
            logger.warning("Simulating OpenAI API failure")
            raise HTTPException(status_code=500, detail="Mock API failure")
        
        # Generate deterministic embeddings
        embeddings = []
        for i, text in enumerate(input_texts):
            embedding = generate_mock_embedding(text, i)
            embeddings.append({
                "object": "embedding",
                "embedding": embedding,
                "index": i
            })
        
        # Calculate usage
        total_tokens = sum(len(text.split()) for text in input_texts)
        
        response = {
            "object": "list",
            "data": embeddings,
            "model": model,
            "usage": {
                "prompt_tokens": total_tokens,
                "total_tokens": total_tokens
            }
        }
        
        logger.info(f"Generated {len(embeddings)} embeddings for {len(input_texts)} texts")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_mock_embedding(text: str, index: int) -> List[float]:
    """Generate deterministic mock embedding for consistent testing"""
    # Create deterministic seed from text content and index
    text_hash = hashlib.md5(f"{text}:{index}".encode()).hexdigest()
    seed = int(text_hash[:8], 16)
    
    # Set numpy seed for deterministic generation
    np.random.seed(seed)
    
    # Generate 1536-dimensional vector (text-embedding-3-small)
    embedding = np.random.normal(0, 1, 1536).tolist()
    
    # Normalize to unit vector for consistency
    embedding_array = np.array(embedding)
    normalized = embedding_array / np.linalg.norm(embedding_array)
    
    return normalized.tolist()

@app.get("/v1/models")
async def list_models():
    """Mock models endpoint"""
    return {
        "object": "list",
        "data": [
            {
                "id": "text-embedding-3-small",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "openai",
                "permission": [],
                "root": "text-embedding-3-small",
                "parent": None
            }
        ]
    }

@app.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    """Mock model details endpoint"""
    if model_id == "text-embedding-3-small":
        return {
            "id": "text-embedding-3-small",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "openai",
            "permission": [],
            "root": "text-embedding-3-small",
            "parent": None
        }
    else:
        raise HTTPException(status_code=404, detail="Model not found")

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple rate limiting middleware"""
    current_time = time.time()
    
    # Clean old request times
    request_times[:] = [t for t in request_times if current_time - t < 60]
    
    # Check rate limit
    if len(request_times) > 60:
        return HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Add current request
    request_times.append(current_time)
    
    response = await call_next(request)
    return response

if __name__ == "__main__":
    import uvicorn
    import asyncio
    uvicorn.run(app, host="0.0.0.0", port=8002)
