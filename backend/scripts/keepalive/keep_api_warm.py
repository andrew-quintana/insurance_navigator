#!/usr/bin/env python3
"""
API Service Keep-Alive Script
Prevents the API service from spinning down due to inactivity on Render.com
"""

import asyncio
import httpx
import time
import logging
from datetime import datetime
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_keepalive.log')
    ]
)
logger = logging.getLogger(__name__)

class APIKeeper:
    def __init__(self, api_url: str, interval: int = 300):  # 5 minutes default
        self.api_url = api_url
        self.interval = interval
        self.running = True
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    async def health_check(self) -> bool:
        """Perform a health check on the API service"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.api_url}/health")
                
                if response.status_code == 200:
                    health_data = response.json()
                    logger.info(f"✅ Health check passed - Status: {health_data.get('status', 'unknown')}")
                    return True
                else:
                    logger.warning(f"⚠️ Health check failed - Status: {response.status_code}")
                    return False
                    
        except httpx.TimeoutException:
            logger.error("❌ Health check timed out")
            return False
        except httpx.ConnectError:
            logger.error("❌ Health check connection failed")
            return False
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False
    
    async def test_endpoint(self) -> bool:
        """Test a simple endpoint to keep the service active"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Test the upload limits endpoint (read-only, safe to call)
                response = await client.get(f"{self.api_url}/api/v2/upload/limits")
                
                if response.status_code == 200:
                    logger.info("✅ Endpoint test passed")
                    return True
                else:
                    logger.warning(f"⚠️ Endpoint test failed - Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Endpoint test error: {e}")
            return False
    
    async def keep_alive_cycle(self):
        """Single keep-alive cycle"""
        self.request_count += 1
        cycle_start = time.time()
        
        logger.info(f"🔄 Keep-alive cycle #{self.request_count} starting...")
        
        # Try health check first
        health_success = await self.health_check()
        
        if health_success:
            self.success_count += 1
        else:
            self.error_count += 1
            # If health check fails, try endpoint test as fallback
            logger.info("🔄 Health check failed, trying endpoint test...")
            endpoint_success = await self.test_endpoint()
            if endpoint_success:
                self.success_count += 1
                self.error_count -= 1  # Adjust counts
        
        cycle_time = time.time() - cycle_start
        success_rate = (self.success_count / self.request_count) * 100
        
        logger.info(f"📊 Cycle #{self.request_count} completed in {cycle_time:.2f}s - Success rate: {success_rate:.1f}%")
        
        return health_success
    
    async def run(self):
        """Main keep-alive loop"""
        logger.info(f"🚀 Starting API keep-alive service for {self.api_url}")
        logger.info(f"⏰ Interval: {self.interval} seconds")
        logger.info("Press Ctrl+C to stop")
        
        while self.running:
            try:
                await self.keep_alive_cycle()
                
                if self.running:
                    logger.info(f"⏳ Waiting {self.interval} seconds until next cycle...")
                    await asyncio.sleep(self.interval)
                    
            except asyncio.CancelledError:
                logger.info("🛑 Keep-alive service cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error in keep-alive loop: {e}")
                if self.running:
                    logger.info(f"⏳ Waiting {self.interval} seconds before retry...")
                    await asyncio.sleep(self.interval)
        
        # Final statistics
        logger.info("📊 Final Statistics:")
        logger.info(f"   Total requests: {self.request_count}")
        logger.info(f"   Successful: {self.success_count}")
        logger.info(f"   Failed: {self.error_count}")
        if self.request_count > 0:
            final_success_rate = (self.success_count / self.request_count) * 100
            logger.info(f"   Success rate: {final_success_rate:.1f}%")
        
        logger.info("👋 API keep-alive service stopped")

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Keep API service warm to prevent spin-down")
    parser.add_argument(
        "--url", 
        default="***REMOVED***",
        help="API service URL (default: ***REMOVED***)"
    )
    parser.add_argument(
        "--interval", 
        type=int, 
        default=300,
        help="Keep-alive interval in seconds (default: 300 = 5 minutes)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create and run keeper
    keeper = APIKeeper(args.url, args.interval)
    
    try:
        await keeper.run()
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
