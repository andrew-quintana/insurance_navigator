#!/usr/bin/env python3
"""
EnhancedBaseWorker runner script for development with real service integration
"""

import asyncio
import signal
import sys
import logging
import os
from typing import Optional

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.workers.enhanced_base_worker import EnhancedBaseWorker
from backend.shared.config import WorkerConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class EnhancedWorkerRunner:
    """Runner for EnhancedBaseWorker with graceful shutdown handling"""
    
    def __init__(self):
        self.worker: Optional[EnhancedBaseWorker] = None
        self.shutdown_event = asyncio.Event()
        
    async def start(self):
        """Start the enhanced worker runner"""
        try:
            # Load configuration from environment
            config = WorkerConfig.from_environment()
            config.validate()
            
            logger.info(f"Enhanced worker configuration loaded and validated, config_keys={list(config.to_dict().keys())}")
            
            # Create and initialize enhanced worker
            self.worker = EnhancedBaseWorker(config)
            await self.worker.initialize()
            
            # Set up signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            # Start the enhanced worker in background (don't await - it runs forever)
            self.worker_task = asyncio.create_task(self.worker.start())
            
            # Wait a moment to ensure the worker is fully started
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Failed to start enhanced worker runner: {str(e)}")
            sys.exit(1)
    
    async def stop(self):
        """Stop the enhanced worker runner"""
        logger.info("Stopping enhanced worker runner...")
        
        if self.worker:
            await self.worker.stop()
        
        if hasattr(self, 'worker_task') and self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                logger.info("Worker task cancelled successfully")
        
        self.shutdown_event.set()
        logger.info("Enhanced worker runner stopped")
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown")
            asyncio.create_task(self.stop())
        
        # Handle SIGTERM and SIGINT
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    async def run(self):
        """Run the enhanced worker until shutdown"""
        try:
            # Start the enhanced worker
            await self.start()
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Error in enhanced worker runner: {str(e)}")
            raise
        finally:
            await self.stop()

async def main():
    """Main entry point"""
    runner = EnhancedWorkerRunner()
    
    try:
        await runner.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Enhanced worker stopped by user")
    except Exception as e:
        logger.error(f"Failed to run enhanced worker: {str(e)}")
        sys.exit(1)
