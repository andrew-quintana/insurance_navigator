"""
Test script to verify LangSmith API connectivity.
"""

import os
from langsmith import Client
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_langsmith_connection():
    """Test connection to LangSmith API."""
    logger.info("Testing LangSmith API connection...")

    # Check if API key is set
    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        logger.error("LANGCHAIN_API_KEY environment variable is not set")
        return False

    try:
        # Initialize client
        client = Client()
        logger.info(f"LangSmith client initialized with API key ending in ...{api_key[-4:]}")
        
        # Test API connection by listing projects
        projects = client.list_projects()
        project_list = list(projects)
        logger.info(f"Successfully retrieved {len(project_list)} projects from LangSmith")
        for i, project in enumerate(project_list):
            logger.info(f"Project {i+1}: {project.name} (ID: {project.id})")
        
        return True
    except Exception as e:
        logger.error(f"Error connecting to LangSmith API: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_langsmith_connection()
    if success:
        print("✅ LangSmith API connection successful")
    else:
        print("❌ LangSmith API connection failed") 