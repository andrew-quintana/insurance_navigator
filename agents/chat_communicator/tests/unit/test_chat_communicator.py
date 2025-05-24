"""
Unit tests for the Chat Communicator Agent.

These tests verify that the Chat Communicator Agent correctly processes
both NavigatorOutput and ServiceAccessStrategy inputs and generates
appropriate conversational responses.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime

from agents.chat_communicator.core.chat_communicator import ChatCommunicatorAgent, ChatCommunicatorException
from agents.chat_communicator.core.models.chat_models import (
    ChatInput, ChatResponse, ConversationContext
)
from agents.patient_navigator.core.models.navigator_models import (
    NavigatorOutput, MetaIntent, ClinicalContext, ServiceIntent, Metadata, BodyLocation
)
from agents.service_access_strategy.core.models.strategy_models import (
    ServiceAccessStrategy, ServiceMatch, ActionStep
)


class TestChatCommunicatorAgent(unittest.TestCase):
    """Test suite for the Chat Communicator Agent."""
    
    def setUp(self):
        """Set up test environment."""
        # Create mock LLM
        self.mock_llm = Mock()
        
        # Create mock config manager
        self.mock_config_manager = Mock()
        self.mock_config_manager.get_agent_config.return_value = {
            "model": {
                "name": "test-model",
                "temperature": 0.2
            },
            "prompt": {
                "path": "test_prompt.md"
            },
            "examples": {
                "path": "test_examples.json"
            }
        }
        
        # Create agent with mocks (using mock mode to avoid LLM calls)
        with patch('agents.chat_communicator.core.chat_communicator.ConfigManager', 
                   return_value=self.mock_config_manager):
            self.agent = ChatCommunicatorAgent(
                llm=self.mock_llm,
                config_manager=self.mock_config_manager,
                use_mock=True
            )
    
    def test_agent_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertEqual(self.agent.name, "chat_communicator")
        self.assertTrue(self.agent.use_mock)
        self.assertIsNotNone(self.agent.output_parser)
        self.assertEqual(self.agent.active_conversations, {})
    
    def test_process_navigator_output_normal(self):
        """Test processing of normal NavigatorOutput."""
        # Create test navigator output
        navigator_output = NavigatorOutput(
            meta_intent=MetaIntent(
                request_type="policy_question",
                summary="Medicare coverage question",
                emergency=False
            ),
            clinical_context=ClinicalContext(
                symptom=None,
                body=BodyLocation(),
                onset=None,
                duration=None
            ),
            service_intent=ServiceIntent(
                specialty="cardiology",
                service="office_visit",
                plan_detail_type="coverage"
            ),
            metadata=Metadata(
                raw_user_text="Does Medicare cover cardiology visits?",
                user_response_created="Medicare Part B covers cardiology visits.",
                timestamp="2025-01-20T14:30:00Z"
            )
        )
        
        # Process the navigator output
        result = self.agent.process_navigator_output(
            navigator_output,
            user_id="test_user",
            session_id="test_session"
        )
        
        # Verify response structure
        self.assertIn("message", result)
        self.assertIn("response_type", result)
        self.assertIn("next_steps", result)
        self.assertEqual(result["response_type"], "informational")
        self.assertEqual(result["urgency_level"], "normal")
        self.assertFalse(result["requires_action"])
    
    def test_process_navigator_output_emergency(self):
        """Test processing of emergency NavigatorOutput."""
        # Create test emergency navigator output
        navigator_output = NavigatorOutput(
            meta_intent=MetaIntent(
                request_type="symptom_report",
                summary="Severe chest pain",
                emergency=True
            ),
            clinical_context=ClinicalContext(
                symptom="severe chest pain",
                body=BodyLocation(region="chest", side="left"),
                onset="30 minutes ago",
                duration="ongoing"
            ),
            service_intent=ServiceIntent(
                specialty="emergency",
                service="emergency_care",
                plan_detail_type=None
            ),
            metadata=Metadata(
                raw_user_text="I have severe chest pain",
                user_response_created="This requires immediate emergency care.",
                timestamp="2025-01-20T15:45:00Z"
            )
        )
        
        # Process the emergency navigator output
        result = self.agent.process_navigator_output(
            navigator_output,
            user_id="test_user",
            session_id="test_session"
        )
        
        # Verify emergency response
        self.assertEqual(result["response_type"], "emergency")
        self.assertEqual(result["urgency_level"], "emergency")
        self.assertTrue(result["requires_action"])
        self.assertIn("911", result["message"])
        self.assertIn("Call 911", result["next_steps"])
    
    def test_process_service_strategy(self):
        """Test processing of ServiceAccessStrategy."""
        # Create test service strategy
        service_strategy = ServiceAccessStrategy(
            patient_need="diabetes management consultation",
            matched_services=[
                ServiceMatch(
                    service_name="Endocrinology Consultation",
                    service_type="specialist_consultation",
                    service_description="Diabetes evaluation and management",
                    is_covered=True,
                    coverage_details={"copay": "$40"},
                    compliance_score=0.95
                )
            ],
            recommended_service="Endocrinology consultation",
            action_plan=[
                ActionStep(
                    step_number=1,
                    step_description="Get referral from primary care",
                    expected_timeline="1-2 business days",
                    required_resources=["primary_care_contact"]
                )
            ],
            estimated_timeline="4-6 weeks",
            provider_options=[
                {
                    "name": "Metro Diabetes Center",
                    "address": "123 Medical Plaza",
                    "distance": "2.3 miles",
                    "in_network": True
                }
            ],
            compliance_assessment={"is_compliant": True},
            guidance_notes=["Bring medications list"],
            confidence=0.92
        )
        
        # Process the service strategy
        result = self.agent.process_service_strategy(
            service_strategy,
            user_id="test_user",
            session_id="test_session"
        )
        
        # Verify response structure
        self.assertEqual(result["response_type"], "guidance")
        self.assertEqual(result["urgency_level"], "normal")
        self.assertTrue(result["requires_action"])
        self.assertIsInstance(result["next_steps"], list)
        self.assertGreater(len(result["next_steps"]), 0)
    
    def test_input_validation_dict_navigator(self):
        """Test input validation for NavigatorOutput as dict."""
        navigator_dict = {
            "meta_intent": {
                "request_type": "policy_question",
                "summary": "Test summary",
                "emergency": False
            },
            "clinical_context": {
                "symptom": None,
                "body": {"region": None, "side": None, "subpart": None},
                "onset": None,
                "duration": None
            },
            "service_intent": {
                "specialty": "cardiology",
                "service": "office_visit",
                "plan_detail_type": "coverage"
            },
            "metadata": {
                "raw_user_text": "Test query",
                "user_response_created": "Test response",
                "timestamp": "2025-01-20T14:30:00Z"
            }
        }
        
        # Validate input
        validated_input = self.agent._validate_input(navigator_dict)
        
        # Verify validation
        self.assertIsInstance(validated_input, ChatInput)
        self.assertEqual(validated_input.source_type, "navigator_output")
        self.assertIsInstance(validated_input.data, NavigatorOutput)
    
    def test_input_validation_dict_strategy(self):
        """Test input validation for ServiceAccessStrategy as dict."""
        strategy_dict = {
            "patient_need": "test need",
            "matched_services": [],
            "recommended_service": "test service",
            "action_plan": [],
            "estimated_timeline": "1 week",
            "provider_options": [],
            "compliance_assessment": {},
            "guidance_notes": [],
            "confidence": 0.8
        }
        
        # Validate input
        validated_input = self.agent._validate_input(strategy_dict)
        
        # Verify validation
        self.assertIsInstance(validated_input, ChatInput)
        self.assertEqual(validated_input.source_type, "service_strategy")
        self.assertIsInstance(validated_input.data, ServiceAccessStrategy)
    
    def test_input_validation_invalid(self):
        """Test input validation with invalid data."""
        invalid_input = {"invalid": "data"}
        
        # Expect validation error
        with self.assertRaises(ChatCommunicatorException):
            self.agent._validate_input(invalid_input)
    
    def test_conversation_context_management(self):
        """Test conversation context management."""
        user_id = "test_user"
        session_id = "test_session"
        
        # Initially no conversation history
        history = self.agent.get_conversation_history(user_id, session_id)
        self.assertEqual(len(history), 0)
        
        # Update conversation context
        self.agent.update_conversation_context(
            user_id, session_id, "test message", "test response"
        )
        
        # Check conversation was created
        conversation_key = f"{user_id}_{session_id}"
        self.assertIn(conversation_key, self.agent.active_conversations)
        
        context = self.agent.active_conversations[conversation_key]
        self.assertEqual(context.user_id, user_id)
        self.assertEqual(context.session_id, session_id)
        self.assertEqual(context.interaction_count, 1)
        
        # Get history
        history = self.agent.get_conversation_history(user_id, session_id)
        self.assertEqual(len(history), 1)
        self.assertIn("interaction_count", history[0])
        
        # Clear conversation
        self.agent.clear_conversation(user_id, session_id)
        self.assertNotIn(conversation_key, self.agent.active_conversations)
    
    def test_reset_agent(self):
        """Test agent reset functionality."""
        # Add some conversation context
        self.agent.update_conversation_context(
            "user1", "session1", "message", "response"
        )
        self.assertEqual(len(self.agent.active_conversations), 1)
        
        # Reset agent
        self.agent.reset()
        
        # Verify reset
        self.assertEqual(len(self.agent.active_conversations), 0)
    
    def test_mock_response_generation(self):
        """Test mock response generation."""
        # Test normal navigator input
        normal_input = ChatInput(
            source_type="navigator_output",
            data=NavigatorOutput(
                meta_intent=MetaIntent(
                    request_type="policy_question",
                    summary="Test",
                    emergency=False
                ),
                clinical_context=ClinicalContext(),
                service_intent=ServiceIntent(),
                metadata=Metadata(
                    raw_user_text="test",
                    user_response_created="test response"
                )
            )
        )
        
        response = self.agent._generate_mock_response(normal_input)
        self.assertEqual(response.response_type, "informational")
        self.assertEqual(response.urgency_level, "normal")
        
        # Test emergency navigator input
        emergency_input = ChatInput(
            source_type="navigator_output",
            data=NavigatorOutput(
                meta_intent=MetaIntent(
                    request_type="symptom_report",
                    summary="Emergency",
                    emergency=True
                ),
                clinical_context=ClinicalContext(),
                service_intent=ServiceIntent(),
                metadata=Metadata(
                    raw_user_text="emergency",
                    user_response_created="emergency response"
                )
            )
        )
        
        response = self.agent._generate_mock_response(emergency_input)
        self.assertEqual(response.response_type, "emergency")
        self.assertEqual(response.urgency_level, "emergency")
        
        # Test service strategy input
        strategy_input = ChatInput(
            source_type="service_strategy",
            data=ServiceAccessStrategy(
                patient_need="test need",
                recommended_service="test service",
                action_plan=[],
                estimated_timeline="1 week",
                provider_options=[],
                compliance_assessment={},
                guidance_notes=[],
                confidence=0.8
            )
        )
        
        response = self.agent._generate_mock_response(strategy_input)
        self.assertEqual(response.response_type, "guidance")
        self.assertTrue(response.requires_action)


if __name__ == '__main__':
    unittest.main() 