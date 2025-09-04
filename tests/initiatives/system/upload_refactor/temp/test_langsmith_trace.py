"""
Test script to verify LangSmith tracing functionality.
"""

import os
import logging
from langsmith import Client
from langsmith.run_helpers import traceable
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@traceable(run_type="chain", name="test_trace_function")
def traced_function(input_text: str) -> Dict[str, Any]:
    """A test function with tracing enabled."""
    logger.info(f"Processing input: {input_text}")
    
    # Simulate some processing
    output = {
        "input": input_text,
        "processed": input_text.upper(),
        "length": len(input_text)
    }
    
    logger.info(f"Generated output: {output}")
    return output

def test_langsmith_tracing():
    """Test LangSmith tracing functionality."""
    logger.info("Testing LangSmith tracing...")
    
    # Check if API key is set
    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        logger.error("LANGCHAIN_API_KEY environment variable is not set")
        return False
    
    try:
        # Initialize client
        client = Client()
        logger.info("LangSmith client initialized")
        
        # Add metadata for the trace
        metadata = {
            "test_name": "tracing_test",
            "component": "patient_navigator",
            "environment": "test"
        }
        
        # Call the traced function
        result = traced_function("Hello, LangSmith tracing!")
        logger.info(f"Traced function result: {result}")
        
        logger.info("Trace should now be available in the LangSmith UI")
        return True
    except Exception as e:
        logger.error(f"Error in LangSmith tracing: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_langsmith_tracing()
    if success:
        print("✅ LangSmith tracing test completed")
    else:
        print("❌ LangSmith tracing test failed") 