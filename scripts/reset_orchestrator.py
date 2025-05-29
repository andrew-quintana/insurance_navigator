#!/usr/bin/env python3
"""
Script to reset the global orchestrator instance and test chat functionality.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def main():
    """Reset orchestrator and test chat."""
    try:
        # Import and reset the orchestrator
        from graph.agent_orchestrator import reset_orchestrator, get_orchestrator
        
        print("🔄 Resetting global orchestrator instance...")
        reset_orchestrator()
        
        print("✅ Orchestrator reset complete")
        
        # Test creating a new orchestrator
        print("🧪 Testing new orchestrator creation...")
        orchestrator = get_orchestrator()
        
        print(f"✅ New orchestrator created: {type(orchestrator).__name__}")
        print(f"   - Config manager: {type(orchestrator.config_manager).__name__}")
        print(f"   - Chat communicator agent: {type(orchestrator.chat_communicator_agent).__name__}")
        
        # Test if the chat communicator agent has output_parser
        if hasattr(orchestrator.chat_communicator_agent, 'output_parser'):
            print("✅ ChatCommunicatorAgent has output_parser attribute")
        else:
            print("❌ ChatCommunicatorAgent missing output_parser attribute")
            
        print("\n🎯 Orchestrator reset successful! Backend should now work properly.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 