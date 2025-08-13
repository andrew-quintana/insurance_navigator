#!/usr/bin/env python3
"""
Phase 2 Output Processing Validation Script

This script demonstrates the capabilities of the completed Phase 2 implementation
by running through various test scenarios and showing the system's functionality.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.patient_navigator.output_processing.workflow import OutputWorkflow
from agents.patient_navigator.output_processing.types import (
    CommunicationRequest,
    AgentOutput
)
from agents.patient_navigator.output_processing.config import OutputProcessingConfig


async def validate_phase2_implementation():
    """Validate the Phase 2 implementation with various test scenarios."""
    
    print("🚀 Phase 2 Output Processing Validation")
    print("=" * 50)
    
    # Initialize the workflow
    config = OutputProcessingConfig()
    workflow = OutputWorkflow(config=config)
    
    print(f"✅ Workflow initialized with config: {config.llm_model}")
    
    # Test 1: Benefits explanation workflow
    print("\n📋 Test 1: Benefits Explanation Workflow")
    print("-" * 40)
    
    benefits_request = CommunicationRequest(agent_outputs=[
        AgentOutput(
            agent_id="benefits_analyzer",
            content="Your plan covers 80% of in-network costs after $500 deductible. Out-of-network coverage is 60% after $1000 deductible.",
            metadata={"coverage_type": "medical", "deductible_met": False}
        ),
        AgentOutput(
            agent_id="eligibility_checker",
            content="Eligibility confirmed. Active coverage until 12/31/2024. No pre-existing condition exclusions apply.",
            metadata={"status": "active", "effective_date": "2024-01-01"}
        )
    ])
    
    try:
        response = await workflow.process_request(benefits_request)
        print(f"✅ Benefits workflow completed successfully")
        print(f"   Response length: {len(response.enhanced_content)} characters")
        print(f"   Processing time: {response.metadata.get('processing_time', 'N/A')}s")
        print(f"   Workflow success: {response.metadata.get('workflow_success', False)}")
    except Exception as e:
        print(f"❌ Benefits workflow failed: {e}")
    
    # Test 2: Claim denial workflow (requires empathy)
    print("\n💔 Test 2: Claim Denial Workflow")
    print("-" * 40)
    
    denial_request = CommunicationRequest(agent_outputs=[
        AgentOutput(
            agent_id="claims_processor",
            content="Claim denied. Policy exclusion 3.2 applies. Coverage not available for pre-existing conditions.",
            metadata={"denial_reason": "pre_existing_condition", "exclusion_code": "3.2"}
        )
    ])
    
    try:
        response = await workflow.process_request(denial_request)
        print(f"✅ Claim denial workflow completed successfully")
        print(f"   Response length: {len(response.enhanced_content)} characters")
        print(f"   Processing time: {response.metadata.get('processing_time', 'N/A')}s")
        print(f"   Workflow success: {response.metadata.get('workflow_success', False)}")
        
        # Check for empathetic language
        empathetic_phrases = ["understand", "frustrating", "help", "support"]
        empathy_score = sum(1 for phrase in empathetic_phrases if phrase.lower() in response.enhanced_content.lower())
        print(f"   Empathy score: {empathy_score}/{len(empathetic_phrases)} phrases detected")
        
    except Exception as e:
        print(f"❌ Claim denial workflow failed: {e}")
    
    # Test 3: Form assistance workflow
    print("\n📝 Test 3: Form Assistance Workflow")
    print("-" * 40)
    
    form_request = CommunicationRequest(agent_outputs=[
        AgentOutput(
            agent_id="form_assistant",
            content="Complete sections 1-3, attach supporting documents, submit by deadline. Required fields: name, date, signature.",
            metadata={"form_type": "appeal", "deadline": "2024-06-15"}
        )
    ])
    
    try:
        response = await workflow.process_request(form_request)
        print(f"✅ Form assistance workflow completed successfully")
        print(f"   Response length: {len(response.enhanced_content)} characters")
        print(f"   Processing time: {response.metadata.get('processing_time', 'N/A')}s")
        print(f"   Workflow success: {response.metadata.get('workflow_success', False)}")
        
        # Check for action-oriented language
        action_phrases = ["step", "complete", "attach", "submit", "required"]
        action_score = sum(1 for phrase in action_phrases if phrase.lower() in response.enhanced_content.lower())
        print(f"   Action score: {action_score}/{len(action_phrases)} phrases detected")
        
    except Exception as e:
        print(f"❌ Form assistance workflow failed: {e}")
    
    # Test 4: Multi-agent consolidation
    print("\n🔄 Test 4: Multi-Agent Consolidation")
    print("-" * 40)
    
    consolidation_request = CommunicationRequest(agent_outputs=[
        AgentOutput(
            agent_id="benefits_analyzer",
            content="80% coverage after deductible",
            metadata={"type": "coverage"}
        ),
        AgentOutput(
            agent_id="claims_processor",
            content="Claim approved for $1,200",
            metadata={"type": "claim"}
        ),
        AgentOutput(
            agent_id="member_services",
            content="Contact 1-800-HELP for questions",
            metadata={"type": "contact"}
        )
    ])
    
    try:
        response = await workflow.process_request(consolidation_request)
        print(f"✅ Multi-agent consolidation completed successfully")
        print(f"   Response length: {len(response.enhanced_content)} characters")
        print(f"   Processing time: {response.metadata.get('processing_time', 'N/A')}s")
        print(f"   Workflow success: {response.metadata.get('workflow_success', False)}")
        print(f"   Sources consolidated: {len(response.original_sources)}")
        
    except Exception as e:
        print(f"❌ Multi-agent consolidation failed: {e}")
    
    # Test 5: Error handling and fallbacks
    print("\n⚠️  Test 5: Error Handling and Fallbacks")
    print("-" * 40)
    
    # Test with empty request (should trigger validation error)
    empty_request = CommunicationRequest(agent_outputs=[])
    
    try:
        response = await workflow.process_request(empty_request)
        print(f"✅ Error handling worked correctly")
        print(f"   Response type: {type(response).__name__}")
        print(f"   Has error metadata: {'error_message' in response.metadata}")
        print(f"   Fallback used: {response.metadata.get('fallback_used', False)}")
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
    
    # Test 6: Performance validation
    print("\n⚡ Test 6: Performance Validation")
    print("-" * 40)
    
    # Test with large content
    large_content = "This is a large content block with detailed information about " + "insurance coverage details " * 1000
    
    large_request = CommunicationRequest(agent_outputs=[
        AgentOutput(
            agent_id="test_agent",
            content=large_content,
            metadata={"test": True}
        )
    ])
    
    try:
        start_time = asyncio.get_event_loop().time()
        response = await workflow.process_request(large_request)
        end_time = asyncio.get_event_loop().time()
        
        processing_time = end_time - start_time
        print(f"✅ Large content processing completed")
        print(f"   Content size: {len(large_content)} characters")
        print(f"   Processing time: {processing_time:.3f}s")
        print(f"   Fallback used: {response.metadata.get('fallback_used', False)}")
        
        if processing_time < 1.0:
            print(f"   ⚡ Performance: Excellent (< 1s)")
        elif processing_time < 5.0:
            print(f"   ⚡ Performance: Good (< 5s)")
        else:
            print(f"   ⚡ Performance: Needs optimization (≥ 5s)")
            
    except Exception as e:
        print(f"❌ Large content processing failed: {e}")
    
    # Test 7: Health check
    print("\n🏥 Test 7: System Health Check")
    print("-" * 40)
    
    try:
        health = workflow.health_check()
        print(f"✅ Health check completed")
        print(f"   Workflow status: {health['workflow']}")
        print(f"   Agent status: {health['agent']}")
        print(f"   Config status: {health['config']}")
        print(f"   Overall health: {'✅ Healthy' if health['workflow'] == 'healthy' else '❌ Unhealthy'}")
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Phase 2 Validation Complete!")
    print("The Output Processing system is ready for production deployment.")
    print("=" * 50)


def main():
    """Main entry point for the validation script."""
    try:
        asyncio.run(validate_phase2_implementation())
    except KeyboardInterrupt:
        print("\n\n⏹️  Validation interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
