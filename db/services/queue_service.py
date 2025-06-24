import logging
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime
import json
import uuid

logger = logging.getLogger(__name__)

class Job:
    def __init__(
        self,
        job_id: str,
        job_type: str,
        payload: Dict[str, Any],
        status: str = "pending"
    ):
        self.id = job_id
        self.type = job_type
        self.payload = payload
        self.status = status
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None

class QueueService:
    def __init__(self, pool):
        self.pool = pool
        self.active_jobs: Dict[str, Job] = {}
        self.job_events: Dict[str, asyncio.Event] = {}
        
    async def enqueue_job(
        self,
        job_type: str,
        payload: Dict[str, Any]
    ) -> Job:
        """
        Add a job to the queue and store in database.
        """
        job_id = str(uuid.uuid4())
        job = Job(job_id, job_type, payload)
        
        # Store in memory
        self.active_jobs[job_id] = job
        self.job_events[job_id] = asyncio.Event()
        
        # Store in database
        async with self.pool.get_connection() as conn:
            await conn.execute("""
                INSERT INTO processing_jobs (
                    id, job_type, payload, status, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
            job_id, job_type, json.dumps(payload), job.status,
            job.created_at, job.updated_at
            )
            
        return job
        
    async def complete_job(
        self,
        job_id: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        Mark a job as completed or failed.
        """
        if job_id not in self.active_jobs:
            return
            
        job = self.active_jobs[job_id]
        job.status = "completed" if result else "failed"
        job.result = result
        job.error = error
        job.completed_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        
        # Update database
        async with self.pool.get_connection() as conn:
            await conn.execute("""
                UPDATE processing_jobs
                SET status = $2,
                    result = $3,
                    error = $4,
                    completed_at = $5,
                    updated_at = $6
                WHERE id = $1
            """,
            job_id, job.status,
            json.dumps(result) if result else None,
            error,
            job.completed_at,
            job.updated_at
            )
            
        # Notify waiters
        if job_id in self.job_events:
            self.job_events[job_id].set()
            
    async def wait_for_job(
        self,
        job_id: str,
        timeout: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for a job to complete with optional timeout.
        """
        if job_id not in self.active_jobs:
            return None
            
        if job_id not in self.job_events:
            self.job_events[job_id] = asyncio.Event()
            
        try:
            await asyncio.wait_for(
                self.job_events[job_id].wait(),
                timeout=timeout
            )
            
            job = self.active_jobs[job_id]
            if job.status == "completed":
                return job.result
            return None
            
        except asyncio.TimeoutError:
            return None
            
        finally:
            # Cleanup
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
            if job_id in self.job_events:
                del self.job_events[job_id]
                
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a job.
        """
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            return {
                "id": job.id,
                "type": job.type,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "result": job.result,
                "error": job.error
            }
            
        # Check database for completed jobs
        async with self.pool.get_connection() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM processing_jobs WHERE id = $1
            """, job_id)
            
            if row:
                return {
                    "id": row["id"],
                    "type": row["job_type"],
                    "status": row["status"],
                    "created_at": row["created_at"].isoformat(),
                    "updated_at": row["updated_at"].isoformat(),
                    "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None,
                    "result": json.loads(row["result"]) if row["result"] else None,
                    "error": row["error"]
                }
                
        return None 