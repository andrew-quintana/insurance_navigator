#!/usr/bin/env python3
"""
Startup script for Enhanced Worker
Runs the enhanced worker with correct Python path and imports
"""

import asyncio
import os
import sys
import logging

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.workers.enhanced_base_worker import EnhancedBaseWorker
from backend.shared.config import WorkerConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def start_worker():
    """Start the enhanced worker."""
    try:
        # Load configuration
        config = WorkerConfig.from_environment()
        logger.info("Configuration loaded successfully")
        
        # Create and initialize worker
        worker = EnhancedBaseWorker(config)
        await worker.initialize()
        logger.info("✅ Enhanced worker initialized successfully")
        
        # Start the worker
        await worker.start()
        logger.info("✅ Enhanced worker started successfully")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, stopping worker...")
            await worker.stop()
            logger.info("Enhanced worker stopped")
            
    except Exception as e:
        logger.error(f"Failed to start enhanced worker: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(start_worker())
