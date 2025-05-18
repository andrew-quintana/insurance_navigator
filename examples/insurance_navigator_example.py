"""
Insurance Navigator Example

This script demonstrates how to set up and use the Insurance Navigator system
with all its agents working together.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import agents
from agents import (
    PromptSecurityAgent,
    PatientNavigatorAgent,
    TaskRequirementsAgent,
    ServiceAccessStrategyAgent
)

# Import configuration
from utils.config_manager import ConfigManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

def main():
    """Run a full Insurance Navigator example."""
    
    # Initialize ConfigManager
    config_manager = ConfigManager()
    
    # Initialize agents
    prompt_security = PromptSecurityAgent(
        config_manager=config_manager
    )
    
    patient_navigator = PatientNavigatorAgent(
        prompt_security_agent=prompt_security,
        config_manager=config_manager
    )
    
    task_requirements = TaskRequirementsAgent(
        config_manager=config_manager
    )
    
    service_access_strategy = ServiceAccessStrategyAgent(
        config_manager=config_manager
    )
    
    # Process a user query
    user_query = "I'm turning 65 next month and need to sign up for Medicare. Can you help me understand my options?"
    user_id = "example_user_123"
    session_id = "example_session_456"
    
    print("\n1. User Query:", user_query)
    
    # First, check if the query is safe
    is_safe, sanitized_query, security_details = prompt_security.process(user_query)
    
    if not is_safe:
        print("\nSecurity check failed!")
        print("Reason:", security_details.get("reasoning", "Unknown security issue"))
        return
    
    print("\n2. Security Check Passed")
    
    # Process with the Patient Navigator
    response_text, navigator_result = patient_navigator.process(sanitized_query, user_id, session_id)
    
    print("\n3. Patient Navigator Response:")
    print(response_text)
    print("\nMeta Intent:", navigator_result["meta_intent"]["request_type"])
    print("Summary:", navigator_result["meta_intent"]["summary"])
    
    # Process with Task Requirements (if this were a real flow)
    if navigator_result["meta_intent"]["request_type"] in ["service_request", "expert_request"]:
        print("\n4. Task Requirements (would normally process):")
        print("Required documents would be determined here")
        
        # Process with Service Access Strategy (if this were a real flow)
        print("\n5. Service Access Strategy (would normally process):")
        print("A strategy would be developed here")
        
        # Sample data for demonstration purposes
        patient_info = {
            "name": "Example User",
            "age": 65,
            "gender": "Female",
            "medical_conditions": [],
            "medication_allergies": []
        }
        
        medical_need = "Medicare enrollment consultation"
        
        policy_info = {
            "policy_type": "Medicare",
            "plan_name": "Medicare Part A & B",
            "effective_date": "2025-07-01"
        }
        
        location = "Seattle, WA"
        
        # Process with Service Access Strategy
        strategy, providers = service_access_strategy.process(
            patient_info,
            medical_need,
            policy_info,
            location
        )
        
        print("\nRecommended Service:", strategy["recommended_service"])
        print("Estimated Timeline:", strategy["estimated_timeline"])
        print("Action Plan Steps:", len(strategy["action_plan"]))
        print("Provider Options:", len(providers))
    
    # Clean up
    patient_navigator.end_conversation(user_id, session_id)
    
    print("\nExample complete!")

if __name__ == "__main__":
    main() 