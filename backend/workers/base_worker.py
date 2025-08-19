import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class BaseWorker:
    """Enhanced BaseWorker with comprehensive monitoring"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.worker_id = str(uuid.uuid4())
        self.logger = logging.getLogger(f"base_worker.{self.worker_id}")
        self.metrics = ProcessingMetrics()
        self.running = False
        
        # Initialize components (will be implemented in Phase 3)
        self.db = None
        self.storage = None
        self.llamaparse = None
        self.openai = None
        
        self.logger.info(f"BaseWorker initialized with ID: {self.worker_id}")
    
    async def start(self):
        """Start the worker process"""
        try:
            self.running = True
            self.logger.info("Starting BaseWorker...")
            
            # Initialize components
            await self._initialize_components()
            
            # Start main processing loop
            await self.process_jobs_continuously()
            
        except Exception as e:
            self.logger.error(f"Error starting BaseWorker: {e}")
            raise
        finally:
            self.running = False
    
    async def stop(self):
        """Stop the worker process"""
        self.logger.info("Stopping BaseWorker...")
        self.running = False
        
        # Cleanup components
        await self._cleanup_components()
    
    async def _initialize_components(self):
        """Initialize worker components"""
        # This will be implemented in Phase 3
        self.logger.info("Component initialization placeholder - will be implemented in Phase 3")
    
    async def _cleanup_components(self):
        """Cleanup worker components"""
        # This will be implemented in Phase 3
        self.logger.info("Component cleanup placeholder - will be implemented in Phase 3")
    
    async def process_jobs_continuously(self):
        """Main worker loop with enhanced health monitoring"""
        self.logger.info("Starting job processing loop...")
        
        while self.running:
            try:
                # Get next job (will be implemented in Phase 3)
                job = await self._get_next_job()
                
                if job:
                    await self._process_single_job_with_monitoring(job)
                else:
                    # No jobs available, wait before next poll
                    await asyncio.sleep(5)
                    
            except asyncio.CancelledError:
                self.logger.info("Worker loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(10)
        
        self.logger.info("Job processing loop stopped")
    
    async def _get_next_job(self) -> Optional[Dict[str, Any]]:
        """Get next job from queue (placeholder for Phase 3)"""
        # This will be implemented in Phase 3 with FOR UPDATE SKIP LOCKED
        return None
    
    async def _process_single_job_with_monitoring(self, job: Dict[str, Any]):
        """Process a single job with comprehensive monitoring (placeholder for Phase 3)"""
        # This will be implemented in Phase 3 with state machine processing
        self.logger.info(f"Job processing placeholder for job: {job.get('job_id', 'unknown')}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Worker health check"""
        return {
            "status": "healthy" if self.running else "stopped",
            "worker_id": self.worker_id,
            "running": self.running,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": self.metrics.get_summary()
        }

class ProcessingMetrics:
    """Processing metrics collection for monitoring"""
    
    def __init__(self):
        self.jobs_processed = 0
        self.jobs_failed = 0
        self.processing_time_total = 0.0
        self.last_job_time = None
    
    def record_job_completion(self, success: bool, processing_time: float):
        """Record job completion metrics"""
        if success:
            self.jobs_processed += 1
        else:
            self.jobs_failed += 1
        
        self.processing_time_total += processing_time
        self.last_job_time = datetime.utcnow()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        total_jobs = self.jobs_processed + self.jobs_failed
        success_rate = (self.jobs_processed / total_jobs * 100) if total_jobs > 0 else 0
        avg_processing_time = (self.processing_time_total / total_jobs) if total_jobs > 0 else 0
        
        return {
            "jobs_processed": self.jobs_processed,
            "jobs_failed": self.jobs_failed,
            "total_jobs": total_jobs,
            "success_rate": round(success_rate, 2),
            "avg_processing_time": round(avg_processing_time, 2),
            "last_job_time": self.last_job_time.isoformat() if self.last_job_time else None
        }
