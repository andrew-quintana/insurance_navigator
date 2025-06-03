"""
Simple script to demonstrate how to run the TaskRequirementsReactAgent.

This script creates an instance of the agent with mock data and runs
test examples through it to show how it processes inputs and requests
missing documents from the patient navigator when needed.

Usage:
    python test_run_agent.py
"""

import json
import sys
import os
from unittest.mock import MagicMock

# Add the project root to the path so we can import the agent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.task_requirements.task_requirements import TaskRequirementsReactAgent

class MockPatientNavigator:
    """Mock Patient Navigator Agent for testing."""
    
    def process_request(self, request):
        """Process a request from the Task Requirements Agent."""
        print(f"\nPatient Navigator received request:")
        print(json.dumps(request, indent=2))
        
        # Simulate a response
        response = {
            "status": "success",
            "message": "Request processed successfully",
            "documents_requested": [doc["type"] for doc in request.get("missing_documents", [])]
        }
        
        print(f"Patient Navigator response:")
        print(json.dumps(response, indent=2))
        
        return response

def main():
    """Run the agent with test examples."""
    print("Initializing TaskRequirementsReactAgent...")
    
    # Create a mock patient navigator
    patient_navigator = MockPatientNavigator()
    
    # Initialize the agent with mock database and patient navigator
    agent = TaskRequirementsReactAgent(
        use_mock_db=True,
        patient_navigator_agent=patient_navigator
    )
    
    # Define test examples
    test_examples = [
        # Expert Request - Podiatrist (with missing referral)
        {
            "meta_intent": {
                "request_type": "expert_request",
                "summary": "User is requesting to see a podiatrist.",
                "emergency": False
            },
            "clinical_context": {
                "symptom": None,
                "body": {
                    "region": "foot",
                    "side": None,
                    "subpart": None
                },
                "onset": None,
                "duration": None
            },
            "service_intent": {
                "specialty": "podiatry",
                "service": None,
                "plan_detail_type": None
            },
            "metadata": {
                "raw_user_text": "Can I book an appointment with a podiatrist?",
                "user_response_created": "Sure! I'll help you figure out how to get support from a podiatrist based on your insurance.",
                "timestamp": "2025-05-13T15:51:00Z"
            }
        },
        # Service Request — Allergy Test
        {
            "meta_intent": {
                "request_type": "service_request",
                "summary": "User wants to get an allergy test.",
                "emergency": False
            },
            "clinical_context": {
                "symptom": None,
                "body": {
                    "region": None,
                    "side": None,
                    "subpart": None
                },
                "onset": None,
                "duration": None
            },
            "service_intent": {
                "specialty": "allergy",
                "service": "allergy test",
                "plan_detail_type": None
            },
            "metadata": {
                "raw_user_text": "I want to get an allergy test.",
                "user_response_created": "Got it — I'll check your plan and try to help you access an allergy test near you.",
                "timestamp": "2025-05-13T15:41:00Z"
            }
        },
        # Generic request with missing documents
        {
            "meta_intent": {
                "request_type": "generic_request",
                "summary": "User wants information about healthcare services.",
                "emergency": False
            },
            "clinical_context": {
                "symptom": None,
                "body": {
                    "region": None,
                    "side": None,
                    "subpart": None
                },
                "onset": None,
                "duration": None
            },
            "service_intent": {
                "specialty": "general",
                "service": "information",
                "plan_detail_type": None
            },
            "metadata": {
                "raw_user_text": "What healthcare services are available to me?",
                "user_response_created": "I'll check what healthcare services are available under your plan.",
                "timestamp": "2025-05-13T15:45:00Z"
            }
        }
    ]
    
    # Process each test example
    for i, example in enumerate(test_examples):
        print(f"\n\n=== Processing Example {i+1}: {example['meta_intent']['summary']} ===")
        
        # Display the input
        print(f"\nInput:")
        print(json.dumps(example, indent=2))
        
        # Process the input
        result = agent.process(example)
        
        # Display the result
        print(f"\nOutput:")
        print(json.dumps(result, indent=2))
        
        # Check if a request was sent to the patient navigator
        if "patient_navigator_request" in result:
            print(f"\n>>> Patient Navigator Request was sent for missing documents <<<")
            
            # Check if documents were updated after the request
            print("\nDocuments after update:")
            for doc_type, doc_info in result["required_context"].items():
                status = "✓ Present" if doc_info.get("present") else "✗ Missing"
                print(f"- {doc_type}: {status}")
        
        print("\n" + "="*80)
    
    print("\nAll examples processed successfully!")

if __name__ == "__main__":
    main() 