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
            # Load environment variables based on deployment context
            # For worker, we use a simplified approach that works in Docker
            environment = os.getenv("ENVIRONMENT", "development")
            
            # In cloud deployment, environment variables are already available
            # In local development, try to load from .env file
            if not self._is_cloud_deployment():
                from dotenv import load_dotenv
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                env_file = f".env.{environment}"
                env_path = os.path.join(project_root, env_file)
                
                if os.path.exists(env_path):
                    load_dotenv(env_path)
                    logger.info(f"Loaded environment variables from {env_file} (local development)")
                else:
                    logger.info(f"Environment file {env_file} not found, using environment variables directly (cloud deployment)")
            else:
                logger.info(f"Using environment variables directly (cloud deployment)")
            
            # Load configuration from environment
            config = WorkerConfig.from_environment()
            config.validate()
            
            # Additional environment variable validation for critical variables
            self._validate_critical_environment_variables()
            
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
    
    def _is_cloud_deployment(self) -> bool:
        """Detect if we're running in a cloud deployment environment"""
        # Check for common cloud deployment indicators
        cloud_indicators = [
            'RENDER',  # Render platform
            'VERCEL',  # Vercel platform
            'HEROKU',  # Heroku platform
            'AWS_LAMBDA_FUNCTION_NAME',  # AWS Lambda
            'K_SERVICE',  # Google Cloud Run
            'DYNO',  # Heroku dyno
        ]
        
        return any(os.getenv(indicator) for indicator in cloud_indicators)
    
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
    
    def _validate_critical_environment_variables(self):
        """Validate critical environment variables are available"""
        critical_vars = [
            "SUPABASE_SERVICE_ROLE_KEY",
            "SUPABASE_URL",
            "DATABASE_URL"
        ]
        
        missing_vars = []
        for var in critical_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            error_msg = f"Missing critical environment variables: {', '.join(missing_vars)}. Please check your .env.{os.getenv('ENVIRONMENT', 'development')} file."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("All critical environment variables validated successfully")
    
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
