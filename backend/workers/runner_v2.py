#!/usr/bin/env python3
"""
Enhanced BaseWorker V2 runner script for production deployment
"""

import asyncio
import signal
import sys
import logging
from typing import Optional

from enhanced_base_worker import EnhancedBaseWorker
from shared.config import WorkerConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class WorkerRunnerV2:
    """Runner for EnhancedBaseWorker with graceful shutdown handling"""
    
    def __init__(self):
        self.worker: Optional[EnhancedBaseWorker] = None
        self.shutdown_event = asyncio.Event()
        
    async def start(self):
        """Start the worker runner"""
        try:
            # Load configuration from environment
            config = WorkerConfig.from_environment()
            config.validate()
            
            logger.info(f"Configuration loaded and validated, config_keys={list(config.to_dict().keys())}")
            
            # Create and initialize worker
            self.worker = EnhancedBaseWorker(config)
            await self.worker.initialize()
            
            # Set up signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            # Start the worker (don't await - it runs in background)
            await self.worker.start()
            
            # Wait a moment to ensure the worker is fully started
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Failed to start worker runner: {str(e)}")
            sys.exit(1)
    
    async def stop(self):
        """Stop the worker runner"""
        logger.info("Stopping worker runner...")
        
        if self.worker:
            await self.worker.stop()
        
        self.shutdown_event.set()
        logger.info("Worker runner stopped")
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown")
            asyncio.create_task(self.stop())
        
        # Handle SIGTERM and SIGINT
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    async def run(self):
        """Run the worker until shutdown"""
        try:
            # Start the worker
            await self.start()
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Error in worker runner: {str(e)}")
            raise
        finally:
            await self.stop()

async def main():
    """Main entry point"""
    runner = WorkerRunnerV2()
    
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
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Failed to run worker: {str(e)}")
        sys.exit(1)
