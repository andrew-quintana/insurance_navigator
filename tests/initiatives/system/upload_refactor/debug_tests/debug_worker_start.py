#!/usr/bin/env python3
"""
Debug script to test BaseWorker start method and identify hanging issue
"""

import asyncio
import logging
import sys
import os

# Add app directory to path
sys.path.insert(0, '/app')

from base_worker import BaseWorker
from shared.config import WorkerConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_worker_start():
    """Test worker start method step by step"""
    try:
        print("🔧 Loading configuration...")
        config = WorkerConfig.from_environment()
        config.validate()
        print("✅ Configuration loaded and validated")
        
        print("🔧 Creating BaseWorker...")
        worker = BaseWorker(config)
        print("✅ BaseWorker created")
        
        print("🔧 Starting BaseWorker...")
        print("   This should complete and return immediately...")
        
        # Start the worker
        start_task = asyncio.create_task(worker.start())
        
        # Wait for start to complete with timeout
        try:
            await asyncio.wait_for(start_task, timeout=30.0)
            print("✅ Worker start completed successfully!")
        except asyncio.TimeoutError:
            print("❌ Worker start timed out after 30 seconds!")
            print("   This indicates the start() method is hanging")
            return False
        
        # Wait a moment to see if the worker is running
        print("🔧 Waiting 5 seconds to see if worker is operational...")
        await asyncio.sleep(5)
        
        print("🔧 Checking worker status...")
        if worker.running:
            print("✅ Worker is running successfully!")
        else:
            print("❌ Worker is not running!")
            return False
        
        print("🔧 Stopping worker...")
        await worker.stop()
        print("✅ Worker stopped successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main entry point"""
    print("🚀 Starting BaseWorker start method debug test...")
    print("=" * 60)
    
    success = await test_worker_start()
    
    print("=" * 60)
    if success:
        print("🎉 Test completed successfully!")
    else:
        print("💥 Test failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
