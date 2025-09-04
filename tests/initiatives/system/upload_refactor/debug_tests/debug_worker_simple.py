#!/usr/bin/env python3
"""
Simple debug script to test if worker stays running
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

async def test_worker_lifecycle():
    """Test worker lifecycle"""
    try:
        print("🔧 Loading configuration...")
        config = WorkerConfig.from_environment()
        config.validate()
        print("✅ Configuration loaded and validated")
        
        print("🔧 Creating BaseWorker...")
        worker = BaseWorker(config)
        print("✅ BaseWorker created")
        
        print("🔧 Starting BaseWorker...")
        await worker.start()
        print("✅ Worker start completed")
        
        print("🔧 Checking worker status immediately after start...")
        print(f"   running flag: {worker.running}")
        print(f"   has _processing_task: {hasattr(worker, '_processing_task')}")
        if hasattr(worker, '_processing_task'):
            print(f"   task done: {worker._processing_task.done()}")
            print(f"   task cancelled: {worker._processing_task.cancelled()}")
        
        print("🔧 Waiting 10 seconds to see if worker stays alive...")
        for i in range(10):
            await asyncio.sleep(1)
            print(f"   Second {i+1}: running={worker.running}, task_done={worker._processing_task.done() if hasattr(worker, '_processing_task') else 'N/A'}")
            
            if not worker.running:
                print("❌ Worker stopped running!")
                break
        
        print("🔧 Stopping worker...")
        await worker.stop()
        print("✅ Worker stopped")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main entry point"""
    print("🚀 Starting simple worker lifecycle test...")
    print("=" * 60)
    
    success = await test_worker_lifecycle()
    
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
