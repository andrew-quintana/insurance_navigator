#!/usr/bin/env python3
"""
Simple API Keep-Alive Script
Lightweight version for continuous operation
"""

import requests
import time
import logging
from datetime import datetime

# Configure simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

def keep_alive(api_url: str, interval: int = 300):
    """Simple keep-alive function"""
    request_count = 0
    success_count = 0
    
    logger.info(f"🚀 Starting simple keep-alive for {api_url}")
    logger.info(f"⏰ Interval: {interval} seconds")
    
    while True:
        try:
            request_count += 1
            logger.info(f"🔄 Keep-alive #{request_count}")
            
            # Try health check
            response = requests.get(f"{api_url}/health", timeout=30)
            
            if response.status_code == 200:
                success_count += 1
                logger.info("✅ API is healthy")
            else:
                logger.warning(f"⚠️ API returned status {response.status_code}")
            
            # Calculate success rate
            success_rate = (success_count / request_count) * 100
            logger.info(f"📊 Success rate: {success_rate:.1f}% ({success_count}/{request_count})")
            
            # Wait for next cycle
            time.sleep(interval)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request failed: {e}")
            time.sleep(60)  # Wait 1 minute on error
        except KeyboardInterrupt:
            logger.info("🛑 Stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    import sys
    
    api_url = "***REMOVED***"
    interval = 300  # 5 minutes
    
    if len(sys.argv) > 1:
        api_url = sys.argv[1]
    if len(sys.argv) > 2:
        interval = int(sys.argv[2])
    
    keep_alive(api_url, interval)
