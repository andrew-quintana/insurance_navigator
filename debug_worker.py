#!/usr/bin/env python3
"""
Debug script to test background task creation
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_task():
    """Test task that runs in background"""
    print("🚀 Test task started")
    for i in range(5):
        print(f"🔄 Test task iteration {i+1}")
        await asyncio.sleep(1)
    print("✅ Test task completed")

async def test_background_task():
    """Test creating and managing background task"""
    print("🔧 Testing background task creation...")
    
    try:
        # Create background task
        task = asyncio.create_task(test_task())
        print(f"✅ Background task created: {task}")
        
        # Wait a moment to see if task starts
        await asyncio.sleep(2)
        
        # Check task status
        print(f"📊 Task status: {task.done()}")
        
        # Wait for task to complete
        await task
        print("✅ Task awaited successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function"""
    print("🧪 Starting background task test...")
    
    try:
        await test_background_task()
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Failed to run test: {e}")
        import traceback
        traceback.print_exc()
