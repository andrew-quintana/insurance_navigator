"""
Example functions and test cases for the Agent/Workflow Prototyping Studio.

This module contains practical examples that demonstrate the capabilities
of the prototyping studio for rapid agent and workflow development.
"""

from typing import Dict, Any, List
from .prototyping_studio import AgentPrototype, WorkflowPrototype, PrototypingLab


def example_simple_agent(lab: PrototypingLab) -> AgentPrototype:
    """Example 1: Create a simple prototype agent."""
    print("\n📝 Example 1: Simple Prototype Agent - Sentiment Analyzer")
    print("=" * 60)
    
    agent = lab.quick_agent(
        name="sentiment_analyzer",
        prompt="Analyze the sentiment of this text and respond with positive, negative, or neutral: {input}",
        model_params={"temperature": 0.3}
    )
    
    # Test it with sample inputs
    test_inputs = [
        "I love this new healthcare system!",
        "This is terrible and confusing.",
        "The weather is okay today."
    ]
    
    print("\n🧪 Testing sentiment analyzer:")
    for test_input in test_inputs:
        result = agent.process(test_input)
        print(f"Input: '{test_input}'")
        print(f"Output: {result['result'][:100]}...")
        print()
    
    return agent


def example_existing_agent(existing_tester) -> Dict[str, Any]:
    """Example 2: Load and test an existing agent."""
    print("\n🤖 Example 2: Existing Agent Testing - Patient Navigator")
    print("=" * 60)
    
    # Load Patient Navigator in mock mode
    agent = existing_tester.load_agent("PatientNavigatorAgent", use_mock=True)
    
    if agent:
        # Test with sample healthcare inputs
        test_inputs = [
            "I need help finding a cardiologist",
            "Does Medicare cover diabetes medication?",
            "I have chest pain and shortness of breath"
        ]
        
        print("\n🧪 Testing Patient Navigator Agent:")
        results = []
        for test_input in test_inputs:
            result = existing_tester.test_agent("PatientNavigatorAgent", test_input)
            results.append(result)
            print(f"Input: '{test_input}'")
            print(f"Success: {result.get('success', False)}")
            if result.get('success'):
                print(f"Result type: {type(result.get('result'))}")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
            print()
        
        return {"agent": "PatientNavigatorAgent", "results": results}
    else:
        return {"error": "Could not load PatientNavigatorAgent"}


def example_workflow_simple(lab: PrototypingLab) -> WorkflowPrototype:
    """Example 3: Create a simple sequential workflow."""
    print("\n🔗 Example 3: Simple Sequential Workflow")
    print("=" * 50)
    
    # Create agents for the workflow
    intake_agent = lab.quick_agent(
        "intake_processor",
        "Process this healthcare intake request and extract key information: {input}"
    )
    
    classification_agent = lab.quick_agent(
        "request_classifier", 
        "Classify this healthcare request as 'urgent', 'routine', or 'informational': {input}"
    )
    
    response_agent = lab.quick_agent(
        "response_generator",
        "Generate an appropriate response based on this classified request: {input}"
    )
    
    # Create workflow
    workflow = lab.quick_workflow("simple_healthcare_workflow")
    workflow.add_agent(intake_agent)
    workflow.add_agent(classification_agent)
    workflow.add_agent(response_agent)
    
    # Visualize the workflow
    workflow.visualize()
    
    # Test the workflow
    test_input = "I need to find a specialist for my diabetes management"
    print(f"\n🚀 Testing workflow with: '{test_input}'")
    result = workflow.execute(test_input)
    
    print(f"\nWorkflow Result:")
    print(f"Steps executed: {result['steps_executed']}")
    print(f"Final result: {result['final_result']}")
    
    return workflow


def example_workflow_conditional(lab: PrototypingLab) -> WorkflowPrototype:
    """Example 4: Create a workflow with conditional branching."""
    print("\n🔀 Example 4: Conditional Branching Workflow - Triage System")
    print("=" * 65)
    
    # Create agents
    triage_agent = lab.quick_agent(
        "triage_classifier",
        "Analyze this healthcare request and determine if it contains emergency keywords. Respond with 'EMERGENCY' or 'ROUTINE': {input}"
    )
    
    emergency_agent = lab.quick_agent(
        "emergency_handler", 
        "Handle this emergency healthcare situation with urgent language and immediate next steps: {input}"
    )
    
    routine_agent = lab.quick_agent(
        "routine_handler",
        "Handle this routine healthcare request with helpful information and standard next steps: {input}"
    )
    
    # Create workflow with conditional branching
    workflow = lab.quick_workflow("triage_workflow")
    workflow.add_agent(triage_agent)
    
    # Define condition function
    def is_emergency(data, state):
        """Check if the triage result indicates an emergency."""
        result_text = str(data).upper()
        return "EMERGENCY" in result_text
    
    # Add conditional branch
    workflow.add_conditional_branch(is_emergency, emergency_agent, routine_agent)
    
    # Visualize the workflow
    workflow.visualize()
    
    # Test with both emergency and routine cases
    test_cases = [
        "I have severe chest pain and can't breathe",
        "I need to schedule a routine checkup",
        "My child has a high fever and is unresponsive"
    ]
    
    print(f"\n🧪 Testing triage workflow:")
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{test_case}'")
        result = workflow.execute(test_case)
        print(f"Path taken: {[log.get('next_path', 'N/A') for log in result['execution_log'] if log['type'] == 'condition']}")
        print(f"Final result: {result['final_result'][:100]}...")
        workflow.clear_state()  # Clear for next test
    
    return workflow


def example_with_models(Models) -> Dict[str, Any]:
    """Example 5: Using existing model classes."""
    print("\n📦 Example 5: Using Existing Model Classes")
    print("=" * 50)
    
    examples = {}
    
    try:
        # Create a sample NavigatorOutput
        navigator_output = Models.NavigatorOutput(
            meta_intent=Models.MetaIntent(
                request_type="policy_question",
                summary="Medicare cardiology coverage question",
                emergency=False
            ),
            clinical_context=Models.ClinicalContext(),
            service_intent=Models.ServiceIntent(
                specialty="cardiology",
                service="consultation"
            ),
            metadata=Models.Metadata(
                raw_user_text="Does Medicare cover cardiology visits?",
                user_response_created="Yes, typically covered under Part B"
            )
        )
        
        print(f"✅ Created NavigatorOutput:")
        print(f"   Request type: {navigator_output.meta_intent.request_type}")
        print(f"   Summary: {navigator_output.meta_intent.summary}")
        print(f"   Emergency: {navigator_output.meta_intent.emergency}")
        print(f"   Specialty: {navigator_output.service_intent.specialty}")
        examples["navigator_output"] = navigator_output.model_dump()
        
    except Exception as e:
        print(f"❌ Error creating NavigatorOutput: {e}")
        examples["navigator_output_error"] = str(e)
    
    try:
        # Create a sample ChatResponse
        chat_response = Models.ChatResponse(
            message="I can help you understand Medicare coverage for cardiology visits.",
            response_type="informational",
            next_steps=["Check your Medicare plan details", "Contact your provider"],
            requires_action=True,
            urgency_level="normal",
            confidence=0.9
        )
        
        print(f"\n✅ Created ChatResponse:")
        print(f"   Message: {chat_response.message}")
        print(f"   Type: {chat_response.response_type}")
        print(f"   Next steps: {len(chat_response.next_steps)} items")
        print(f"   Confidence: {chat_response.confidence}")
        examples["chat_response"] = chat_response.model_dump()
        
    except Exception as e:
        print(f"❌ Error creating ChatResponse: {e}")
        examples["chat_response_error"] = str(e)
    
    try:
        # Create a sample ServiceAccessStrategy
        service_strategy = Models.ServiceAccessStrategy(
            patient_need="Cardiology consultation for routine checkup",
            recommended_service="In-network cardiologist consultation",
            action_plan=[
                Models.ActionStep(
                    step_number=1,
                    step_description="Contact primary care for referral",
                    expected_timeline="1-3 business days",
                    required_resources=["Primary care contact info"],
                    potential_obstacles=["Scheduling delays"]
                )
            ],
            estimated_timeline="2-4 weeks",
            confidence=0.85
        )
        
        print(f"\n✅ Created ServiceAccessStrategy:")
        print(f"   Patient need: {service_strategy.patient_need}")
        print(f"   Recommended service: {service_strategy.recommended_service}")
        print(f"   Action plan steps: {len(service_strategy.action_plan)}")
        print(f"   Confidence: {service_strategy.confidence}")
        examples["service_strategy"] = service_strategy.model_dump()
        
    except Exception as e:
        print(f"❌ Error creating ServiceAccessStrategy: {e}")
        examples["service_strategy_error"] = str(e)
    
    return examples


def example_config_hot_swap(lab: PrototypingLab, config_panel) -> None:
    """Example 6: Hot-swapping configurations."""
    print("\n⚙️ Example 6: Hot-Swapping Agent Configurations")
    print("=" * 55)
    
    # Create an agent to experiment with
    agent = lab.quick_agent(
        "test_agent",
        "Respond to this input: {input}",
        model_params={"temperature": 0.5}
    )
    
    # Show initial config
    print("\n📊 Initial Configuration:")
    config_panel.show_current_config("test_agent")
    
    # Test initial behavior
    test_input = "What's the weather like?"
    print(f"\n🧪 Initial test with: '{test_input}'")
    result1 = agent.process(test_input, use_model=False)  # Use mock for demo
    print(f"Result: {result1['result']}")
    
    # Hot-swap the prompt
    new_prompt = "You are a helpful healthcare assistant. Respond professionally to: {input}"
    print(f"\n🔄 Hot-swapping prompt...")
    config_panel.edit_agent_prompt("test_agent", new_prompt)
    
    # Hot-swap model parameters
    print(f"\n🔄 Hot-swapping model parameters...")
    config_panel.edit_model_params("test_agent", temperature=0.9, max_tokens=500)
    
    # Add some memory
    print(f"\n🔄 Adding memory...")
    config_panel.edit_memory("test_agent", {"user_preference": "concise_responses", "context": "healthcare_discussion"})
    
    # Show updated config
    print(f"\n📊 Updated Configuration:")
    config_panel.show_current_config("test_agent")
    
    # Test updated behavior
    print(f"\n🧪 Updated test with: '{test_input}'")
    result2 = agent.process(test_input, use_model=False)  # Use mock for demo
    print(f"Result: {result2['result']}")
    
    print(f"\n✅ Configuration hot-swap demonstration complete!")


def example_agent_comparison(lab: PrototypingLab) -> Dict[str, Any]:
    """Example 7: Comparing multiple agents on the same inputs."""
    print("\n🏆 Example 7: Agent Comparison - Different Prompt Strategies")
    print("=" * 65)
    
    # Create multiple agents with different approaches
    formal_agent = lab.quick_agent(
        "formal_responder",
        "Provide a formal, professional response to this healthcare query: {input}"
    )
    
    casual_agent = lab.quick_agent(
        "casual_responder",
        "Provide a friendly, conversational response to this healthcare query: {input}"
    )
    
    detailed_agent = lab.quick_agent(
        "detailed_responder",
        "Provide a comprehensive, detailed response with steps and explanations to this healthcare query: {input}"
    )
    
    # Test inputs
    test_inputs = [
        "How do I find a good doctor?",
        "What should I bring to my appointment?",
        "Is telehealth covered by insurance?"
    ]
    
    # Compare agents
    print(f"\n🧪 Comparing agents on {len(test_inputs)} test inputs:")
    comparison_results = lab.compare_agents(
        ["formal_responder", "casual_responder", "detailed_responder"],
        test_inputs
    )
    
    # Display results
    for agent_name, results in comparison_results.items():
        print(f"\n📊 Results for {agent_name}:")
        for i, result in enumerate(results):
            print(f"   Input {i+1}: {result['result'][:60]}...")
    
    return comparison_results


def example_test_suite(lab: PrototypingLab) -> Dict[str, Any]:
    """Example 8: Running a comprehensive test suite."""
    print("\n🧪 Example 8: Comprehensive Test Suite")
    print("=" * 45)
    
    # Create some agents for testing
    validator_agent = lab.quick_agent(
        "input_validator",
        "Validate if this is a valid healthcare question. Respond with 'VALID' or 'INVALID': {input}"
    )
    
    # Create a simple workflow
    workflow = lab.quick_workflow("validation_workflow")
    workflow.add_agent(validator_agent)
    
    # Define test cases
    test_cases = [
        {
            "name": "Valid Healthcare Question",
            "type": "agent",
            "agent": "input_validator",
            "input": "What are the symptoms of diabetes?"
        },
        {
            "name": "Invalid Input",
            "type": "agent",
            "agent": "input_validator",
            "input": "What's the capital of France?"
        },
        {
            "name": "Workflow Test",
            "type": "workflow",
            "workflow": "validation_workflow",
            "input": "How can I manage high blood pressure?"
        }
    ]
    
    # Run the test suite
    print(f"\n🚀 Running test suite with {len(test_cases)} test cases:")
    suite_results = lab.run_test_suite(test_cases)
    
    # Display summary
    print(f"\n📊 Test Suite Summary:")
    print(f"   Total tests: {suite_results['total_tests']}")
    successful_tests = sum(1 for result in suite_results['results'] if result['success'])
    print(f"   Successful: {successful_tests}")
    print(f"   Failed: {suite_results['total_tests'] - successful_tests}")
    
    return suite_results


def run_all_examples(studio_components: Dict[str, Any]) -> Dict[str, Any]:
    """Run all examples in sequence."""
    print("\n🎯 Running All Prototyping Studio Examples")
    print("=" * 50)
    
    # Extract components
    lab = studio_components['lab']
    existing_tester = studio_components['existing_tester']
    config_panel = studio_components['config_panel']
    Models = studio_components['Models']
    
    results = {}
    
    try:
        # Run examples
        results['simple_agent'] = example_simple_agent(lab)
        results['existing_agent'] = example_existing_agent(existing_tester)
        results['simple_workflow'] = example_workflow_simple(lab)
        results['conditional_workflow'] = example_workflow_conditional(lab)
        results['model_usage'] = example_with_models(Models)
        example_config_hot_swap(lab, config_panel)
        results['agent_comparison'] = example_agent_comparison(lab)
        results['test_suite'] = example_test_suite(lab)
        
        print("\n🎉 All examples completed successfully!")
        
        # Show final dashboard
        lab.dashboard()
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        results['error'] = str(e)
    
    return results 