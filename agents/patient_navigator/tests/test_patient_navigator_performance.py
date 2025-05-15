"""
Test Patient Navigator Performance

This script tests the performance of the Patient Navigator Agent and saves metrics.
"""

import os
import json
import logging
from typing import Dict, Any
from datetime import datetime

from agents.patient_navigator import PatientNavigatorAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_patient_navigator_performance")

def run_performance_test() -> None:
    """Run a performance test on the Patient Navigator Agent."""
    logger.info("Initializing Patient Navigator Agent")
    agent = PatientNavigatorAgent()
    
    # Sample queries for testing
    test_queries = [
        "I need to find a doctor who specializes in diabetes.",
        "My knee has been hurting for three weeks, what should I do?",
        "I'm turning 65 next month and need to sign up for Medicare.",
        "Can you help me understand how to manage my diabetes medication?",
        "I need a referral to a cardiologist.",
    ]
    
    # Process each query and track performance
    logger.info(f"Processing {len(test_queries)} test queries")
    for i, query in enumerate(test_queries):
        logger.info(f"Processing query {i+1}/{len(test_queries)}")
        
        # Generate a unique user and session ID for each test
        user_id = f"test_user_{i}"
        session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"
        
        # Process the query
        try:
            response_text, result = agent.process(query, user_id, session_id)
            logger.info(f"Query processed successfully: {query[:30]}...")
            logger.info(f"Response: {response_text[:50]}...")
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
    
    # Save the metrics
    try:
        metrics_path = agent.save_metrics()
        logger.info(f"Metrics saved to {metrics_path}")
        
        # Display summary of metrics
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
            
        logger.info(f"Performance Summary:")
        logger.info(f"Total Requests: {metrics['total_requests']}")
        logger.info(f"Successful Requests: {metrics['successful_requests']}")
        logger.info(f"Failed Requests: {metrics['failed_requests']}")
        logger.info(f"Average Response Time: {metrics['avg_response_time']:.2f}s")
        logger.info(f"Success Rate: {metrics['success_rate'] * 100:.1f}%")
        
        # The metrics path should now be updated in the agent config
    except Exception as e:
        logger.error(f"Error saving metrics: {str(e)}")

if __name__ == "__main__":
    run_performance_test() 