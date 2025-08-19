#!/usr/bin/env python3
"""
BaseWorker runner script for local development
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.workers.base_worker import BaseWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WorkerRunner:
    """Worker process runner with signal handling"""
    
    def __init__(self):
        self.worker: Optional[BaseWorker] = None
        self.shutdown_event = asyncio.Event()
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown_event.set()
    
    async def run(self):
        """Run the worker process"""
        try:
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Load configuration
            config = self._load_config()
            
            # Create and start worker
            self.worker = BaseWorker(config)
            
            # Start worker in background task
            worker_task = asyncio.create_task(self.worker.start())
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
            # Stop worker
            if self.worker:
                await self.worker.stop()
            
            # Cancel worker task
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass
            
            logger.info("Worker shutdown complete")
            
        except Exception as e:
            logger.error(f"Error in worker runner: {e}")
            raise
    
    def _load_config(self) -> Dict[str, Any]:
        """Load worker configuration from environment"""
        config = {
            "database_url": os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/accessa_dev"),
            "supabase_url": os.getenv("SUPABASE_URL", "http://localhost:5000"),
            "supabase_anon_key": os.getenv("SUPABASE_ANON_KEY"),
            "supabase_service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            "llamaparse_api_url": os.getenv("LLAMAPARSE_API_URL", "http://localhost:8001"),
            "openai_api_url": os.getenv("OPENAI_API_URL", "http://localhost:8002"),
            "environment": os.getenv("UPLOAD_PIPELINE_ENVIRONMENT", "local"),
            "worker_config": {
                "polling_interval": 5,  # seconds
                "max_retries": 3,
                "batch_size": 256,
                "timeout": 300,  # seconds
            }
        }
        
        logger.info(f"Loaded configuration for environment: {config['environment']}")
        return config

async def main():
    """Main entry point"""
    runner = WorkerRunner()
    await runner.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)
