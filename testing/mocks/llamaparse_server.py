from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
import asyncio
import httpx
import hashlib
import hmac
import os
from datetime import datetime
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock LlamaParse Service", version="1.0.0")

# Configuration from environment variables
MOCK_PROCESSING_DELAY = int(os.getenv("MOCK_LLAMAPARSE_DELAY", "2"))
MOCK_FAILURE_RATE = float(os.getenv("MOCK_LLAMAPARSE_FAILURE_RATE", "0.0"))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mock-llamaparse", "timestamp": datetime.utcnow().isoformat()}

@app.post("/parse")
async def submit_parse_job(
    background_tasks: BackgroundTasks,
    request: Request
):
    """Mock LlamaParse job submission with webhook callback"""
    try:
        body = await request.json()
        job_id = body.get("job_id")
        source_url = body.get("source_url")
        webhook_url = body.get("webhook_url")
        
        if not all([job_id, source_url, webhook_url]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Simulate async processing with callback
        background_tasks.add_task(
            simulate_parse_and_callback,
            job_id, source_url, webhook_url
        )
        
        logger.info(f"Parse job submitted: {job_id}")
        
        return {
            "parse_job_id": f"mock-parse-{job_id}",
            "status": "queued",
            "estimated_completion": MOCK_PROCESSING_DELAY
        }
        
    except Exception as e:
        logger.error(f"Error submitting parse job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def simulate_parse_and_callback(job_id: str, source_url: str, webhook_url: str):
    """Simulate parsing delay and webhook callback"""
    try:
        # Simulate processing time
        logger.info(f"Starting mock parsing for job: {job_id}")
        await asyncio.sleep(MOCK_PROCESSING_DELAY)
        
        # Check if we should simulate failure
        if MOCK_FAILURE_RATE > 0 and asyncio.get_event_loop().time() % 10 < MOCK_FAILURE_RATE * 10:
            logger.warning(f"Simulating parse failure for job: {job_id}")
            await send_webhook_callback(webhook_url, job_id, "failed", None)
            return
        
        # Generate mock parsed content
        parsed_content = generate_mock_content(job_id)
        content_sha256 = hashlib.sha256(parsed_content.encode('utf-8')).hexdigest()
        
        # Send webhook callback
        await send_webhook_callback(webhook_url, job_id, "parsed", {
            "content": parsed_content,
            "sha256": content_sha256,
            "bytes": len(parsed_content.encode('utf-8'))
        })
        
        logger.info(f"Mock parsing completed for job: {job_id}")
        
    except Exception as e:
        logger.error(f"Error in mock parsing for job {job_id}: {e}")
        # Try to send failure webhook
        try:
            await send_webhook_callback(webhook_url, job_id, "failed", {"error": str(e)})
        except Exception as webhook_error:
            logger.error(f"Failed to send failure webhook: {webhook_error}")

def generate_mock_content(document_id: str) -> str:
    """Generate deterministic mock content for testing"""
    return f"""# Mock Document {document_id}

This is deterministic mock content for testing purposes.
Content is based on document_id for reproducible testing.

## Section 1: Introduction
This document contains mock content that will be processed through the complete pipeline.
The content is designed to generate consistent chunks for testing chunking algorithms.

## Section 2: Technical Details
- Document ID: {document_id}
- Generated at: {datetime.utcnow().isoformat()}
- Content type: Mock markdown
- Purpose: Testing pipeline functionality

## Section 3: Content Structure
This section demonstrates how the mock content is structured to test various aspects of the processing pipeline.

### Subsection 3.1: Chunking
The content is designed to generate multiple chunks when processed by the chunking algorithm.
This allows testing of chunk generation, storage, and retrieval functionality.

### Subsection 3.2: Embedding
The text content will be converted to vector embeddings for similarity search testing.
The mock content provides sufficient text for meaningful embedding generation.

## Section 4: Testing Scenarios
This mock document supports testing of:
- Document parsing and validation
- Chunk generation and storage
- Vector embedding creation
- Complete pipeline processing
- Error handling and recovery

## Section 5: Conclusion
This mock document serves as a reliable test fixture for the upload pipeline.
The deterministic content ensures consistent testing results across multiple runs.
"""

async def send_webhook_callback(webhook_url: str, job_id: str, status: str, data: Dict[str, Any]):
    """Send webhook callback to the specified URL"""
    try:
        payload = {
            "job_id": job_id,
            "document_id": job_id,  # Using job_id as document_id for simplicity
            "status": status,
            "artifacts": []
        }
        
        if status == "parsed" and data:
            payload["artifacts"] = [{
                "type": "markdown",
                "content": data["content"],
                "sha256": data["sha256"],
                "bytes": data["bytes"]
            }]
        
        payload["meta"] = {
            "parser_name": "llamaparse",
            "parser_version": "2025-08-01"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
            
        logger.info(f"Webhook callback sent successfully for job: {job_id}")
        
    except Exception as e:
        logger.error(f"Failed to send webhook callback for job {job_id}: {e}")

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get mock job status"""
    return {
        "job_id": job_id,
        "status": "completed",
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
