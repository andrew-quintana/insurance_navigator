"""
LangGraph Agent Orchestrator for Medicare Navigator
Handles orchestration of multiple agents based on intent routing.
Integrates with persistent conversation service for workflow state management.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from uuid import uuid4

# LangGraph imports
from langgraph.graph import StateGraph, Graph
from langgraph.graph.message import add_messages

# Agent imports - now consistent imports from main agents module
from agents import (
    PromptSecurityAgent,
    PatientNavigatorAgent,
    TaskRequirementsAgent,
    ServiceAccessStrategyAgent,
    ChatCommunicatorAgent,
    RegulatoryAgent,
)

# Exception imports
from agents.common.exceptions import (
    AgentException,
    PromptSecurityException,
    PatientNavigatorException
)

# Configuration import
from utils.config_manager import ConfigManager

# Database conversation service import
from db.services.conversation_service import get_conversation_service

logger = logging.getLogger(__name__)

def _get_default_bypass_security() -> bool:
    """Get default bypass_security setting from environment or default to True for development"""
    return os.getenv("BYPASS_SECURITY", "true").lower() in ("true", "1", "yes", "on")

class AgentState:
    """State object for LangGraph workflow with database persistence"""
    def __init__(self):
        self.message: str = ""
        self.conversation_id: str = ""
        self.user_id: str = ""
        self.intent: str = ""
        self.workflow_type: str = ""
        self.response_text: str = ""
        self.metadata: Dict[str, Any] = {}
        self.security_check_passed: bool = False
        self.error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for persistence."""
        return {
            "message": self.message,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "intent": self.intent,
            "workflow_type": self.workflow_type,
            "response_text": self.response_text,
            "metadata": self.metadata,
            "security_check_passed": self.security_check_passed,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentState':
        """Create state from dictionary for persistence."""
        state = cls()
        for key, value in data.items():
            if hasattr(state, key):
                setattr(state, key, value)
        return state
        
class AgentOrchestrator:
    """Orchestrates multiple agents using LangGraph workflows with persistent state"""
    
    def __init__(self, bypass_security: Optional[bool] = None):  # Use None to allow env default
        self.config_manager = ConfigManager()
        self.conversation_service = None
        self._conversation_service_initialized = False
        self.bypass_security = bypass_security if bypass_security is not None else _get_default_bypass_security()
        self._initialize_agents()
        self._build_workflows()
    
    async def _ensure_conversation_service(self) -> None:
        """Ensure conversation service is initialized."""
        if not self._conversation_service_initialized:
            try:
                self.conversation_service = await get_conversation_service()
                self._conversation_service_initialized = True
                logger.info("Conversation service initialized in orchestrator")
            except Exception as e:
                logger.error(f"Failed to initialize conversation service: {e}")
                self.conversation_service = None
        
    def _initialize_agents(self):
        """Initialize all required agents"""
        try:
            # Agents that don't accept config_manager parameter
            self.prompt_security_agent = PromptSecurityAgent(bypass_security=self.bypass_security)
            self.regulatory_agent = RegulatoryAgent()
            
            # Agents that accept config_manager parameter
            self.patient_navigator_agent = PatientNavigatorAgent(config_manager=self.config_manager)
            self.task_requirements_agent = TaskRequirementsAgent(config_manager=self.config_manager)
            self.service_access_strategy_agent = ServiceAccessStrategyAgent(config_manager=self.config_manager)
            self.chat_communicator_agent = ChatCommunicatorAgent(config_manager=self.config_manager, use_mock=True)
            
            if self.bypass_security:
                logger.warning("🚫 ORCHESTRATOR: Security bypass is ENABLED for all workflows")
            else:
                logger.info("🔒 ORCHESTRATOR: Security checks are ENABLED")
                
            logger.info("All agents initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agents: {str(e)}")
            raise AgentException(f"Agent initialization failed: {str(e)}")
    
    def _build_workflows(self):
        """Build LangGraph workflows"""
        from langgraph.graph import StateGraph
        
        # Strategy request workflow: Security → Navigator → Task Requirements → Strategy/Regulatory OR Chat (if insufficient info)
        self.strategy_workflow = StateGraph(dict)
        
        # Add nodes
        self.strategy_workflow.add_node("security_check", self._security_check_node)
        self.strategy_workflow.add_node("navigator_analysis", self._navigator_analysis_node)
        self.strategy_workflow.add_node("task_requirements", self._task_requirements_node)
        self.strategy_workflow.add_node("service_strategy", self._service_strategy_node)
        self.strategy_workflow.add_node("regulatory_check", self._regulatory_check_node)
        self.strategy_workflow.add_node("chat_response", self._chat_response_node)
        
        # Add edges for strategy workflow with conditional logic
        self.strategy_workflow.add_edge("security_check", "navigator_analysis")
        self.strategy_workflow.add_edge("navigator_analysis", "task_requirements")
        
        # Conditional edge from task_requirements - this is now the gatekeeper
        self.strategy_workflow.add_conditional_edges(
            "task_requirements",
            self._task_requirements_decision,
            {
                "insufficient_info": "chat_response",      # Skip to chat if insufficient info
                "continue": "service_strategy",         # Continue normal flow
                "urgent": "service_strategy"            # Continue for urgent cases
            }
        )
        
        self.strategy_workflow.add_edge("service_strategy", "regulatory_check")
        self.strategy_workflow.add_edge("regulatory_check", "chat_response")
        
        # Set entry point
        self.strategy_workflow.set_entry_point("security_check")
        
        # Navigator-only workflow: Security → Navigator → Chat
        self.navigator_workflow = StateGraph(dict)
        
        # Add nodes
        self.navigator_workflow.add_node("security_check", self._security_check_node)
        self.navigator_workflow.add_node("navigator_qa", self._navigator_qa_node)
        self.navigator_workflow.add_node("chat_response", self._chat_response_node)
        
        # Add edges for navigator workflow
        self.navigator_workflow.add_edge("security_check", "navigator_qa")
        self.navigator_workflow.add_edge("navigator_qa", "chat_response")
        
        # Set entry point
        self.navigator_workflow.set_entry_point("security_check")
        
        # Compile workflows
        self.compiled_strategy_workflow = self.strategy_workflow.compile()
        self.compiled_navigator_workflow = self.navigator_workflow.compile()
        
        logger.info("LangGraph workflows built successfully")
    
    def _navigation_decision(self, state_dict: Dict[str, Any]) -> str:
        """
        Decision function to determine next step after navigator analysis.
        
        Args:
            state_dict: Current workflow state
            
        Returns:
            String indicating next step: "continue", or "urgent"
        """
        # Navigator now only handles intent classification, no sufficiency checks
        navigator_result = state_dict.get("navigator_result", {})
        meta_intent = navigator_result.get("meta_intent", {})
        
        # Check for urgent/emergency cases that should skip task requirements
        if meta_intent.get("emergency", False):
            logger.info("Navigation decision: urgent - emergency detected, proceeding with full workflow")
            return "urgent"
        
        # Default to continue with normal workflow (go to Task Requirements)
        logger.info("Navigation decision: continue - proceeding to task requirements")
        return "continue"
    
    def _task_requirements_decision(self, state_dict: Dict[str, Any]) -> str:
        """
        Decision function to determine next step after Task Requirements analysis.
        
        Args:
            state_dict: Current workflow state
            
        Returns:
            String indicating next step: "continue" (sufficient info), "insufficient_info" (need more info)
        """
        # Check Task Requirements result for information sufficiency
        task_result = state_dict.get("task_requirements_result")
        if task_result and isinstance(task_result, dict):
            status = task_result.get("status")
            if status == "insufficient_information":
                logger.info("Task Requirements determined insufficient information - requesting more details")
                return "insufficient_info"
            elif status == "sufficient_information":
                logger.info("Task Requirements confirmed sufficient information - proceeding to strategy")
                return "continue"
        
        # Fallback to Navigator result if Task Requirements didn't provide clear status
        navigator_result = state_dict.get("navigator_result", {})
        meta_intent = navigator_result.get("meta_intent", {})
        
        # Check for emergency cases that should skip task requirements
        if meta_intent.get("emergency", False):
            logger.info("Emergency case detected - proceeding immediately")
            return "continue"
        
        # Default to continue if we can't determine otherwise
        logger.info("Task Requirements decision: continuing (default)")
        return "continue"
    
    async def process_message(
        self, 
        message: str, 
        user_id: str, 
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing user messages
        Routes to appropriate workflow based on intent with persistent state management
        """
        if not conversation_id:
            conversation_id = f"conv_{uuid4().hex[:8]}"
        
        try:
            # Ensure conversation service is available
            await self._ensure_conversation_service()
            
            # Create or load conversation
            if self.conversation_service:
                await self.conversation_service.create_conversation(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    metadata={"orchestrator": "langgraph"}
                )
            
            # Initialize state
            state = {}
            state["message"] = message
            state["user_id"] = user_id
            state["conversation_id"] = conversation_id
            state["intent"] = ""
            state["workflow_type"] = ""
            state["response_text"] = ""
            state["metadata"] = {}
            state["security_check_passed"] = False
            state["error"] = None
            
            # Try to load existing workflow state
            if self.conversation_service:
                try:
                    existing_state = await self.conversation_service.get_workflow_state(conversation_id)
                    if existing_state:
                        # Resume from existing state
                        state = existing_state["state_data"]
                        state["message"] = message  # Update with new message
                        logger.info(f"Resumed workflow from step: {existing_state['current_step']}")
                except Exception as e:
                    logger.warning(f"Could not load existing workflow state: {e}")
            
            # Determine workflow type based on message content
            workflow_type = self._determine_workflow_type(message)
            state["workflow_type"] = workflow_type
            
            logger.info(f"Processing message with {workflow_type} workflow for user {user_id}")
            
            # Save initial workflow state
            if self.conversation_service:
                await self.conversation_service.save_workflow_state(
                    conversation_id=conversation_id,
                    workflow_type=workflow_type,
                    current_step="initialized",
                    state_data=state,
                    user_id=user_id
                )
            
            # Execute appropriate workflow
            if workflow_type == "strategy_request":
                final_state = await self._execute_strategy_workflow(state)
            else:
                final_state = await self._execute_navigator_workflow(state)
            
            # Save final workflow state
            if self.conversation_service:
                await self.conversation_service.save_workflow_state(
                    conversation_id=conversation_id,
                    workflow_type=workflow_type,
                    current_step="completed",
                    state_data=final_state,
                    user_id=user_id
                )
            
            # Handle errors
            if final_state.get("error"):
                logger.error(f"Workflow error: {final_state['error']}")
                return self._create_error_response(final_state["error"], conversation_id)
            
            # Return successful response
            return {
                "text": final_state["response_text"],
                "metadata": final_state["metadata"],
                "conversation_id": conversation_id,
                "workflow_type": workflow_type
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return self._create_error_response(str(e), conversation_id)
    
    def _determine_workflow_type(self, message: str) -> str:
        """Determine which workflow to use based on message content"""
        message_lower = message.lower()
        
        # Keywords that indicate strategy request workflow
        strategy_keywords = [
            "find", "search", "locate", "doctor", "specialist", "physician",
            "provider", "access", "care", "treatment", "insurance", "coverage",
            "network", "referral", "appointment", "help me", "need", "cardiologist",
            "dentist", "therapist", "clinic", "hospital", "medical", "healthcare",
            "x-ray", "xray", "scan", "test", "procedure", "screening", "imaging",
            "mri", "ct", "ultrasound", "mammogram", "colonoscopy", "blood work",
            "lab", "diagnostic", "examination", "check-up", "physical"
        ]
        
        # Check if message contains strategy-related keywords
        if any(keyword in message_lower for keyword in strategy_keywords):
            return "strategy_request"
        
        return "navigator_only"
    
    async def _execute_strategy_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the strategy request workflow with state persistence"""
        try:
            # Save workflow state at strategy execution
            if self.conversation_service:
                await self.conversation_service.save_workflow_state(
                    conversation_id=state["conversation_id"],
                    workflow_type=state["workflow_type"],
                    current_step="strategy_workflow",
                    state_data=state,
                    user_id=state["user_id"]
                )
            
            # LangGraph expects dict state, so pass state as dict
            result = await self.compiled_strategy_workflow.ainvoke(state)
            
            # Convert result back to dict
            return result
        except Exception as e:
            state["error"] = f"Strategy workflow error: {str(e)}"
            return state
    
    async def _execute_navigator_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the navigator-only workflow with state persistence"""
        try:
            # Save workflow state at navigator execution
            if self.conversation_service:
                await self.conversation_service.save_workflow_state(
                    conversation_id=state["conversation_id"],
                    workflow_type=state["workflow_type"],
                    current_step="navigator_workflow",
                    state_data=state,
                    user_id=state["user_id"]
                )
            
            # LangGraph expects dict state, so pass state as dict
            result = await self.compiled_navigator_workflow.ainvoke(state)
            
            # Convert result back to dict
            return result
        except Exception as e:
            state["error"] = f"Navigator workflow error: {str(e)}"
            return state
    
    # Workflow node implementations
    async def _security_check_node(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Prompt security agent node"""
        try:
            logger.info("Executing security check")
            
            security_result = await self.prompt_security_agent.check_prompt_security(
                state_dict["message"], state_dict["user_id"]
            )
            
            # Save agent state with detailed results
            if self.conversation_service:
                await self.conversation_service.save_agent_state(
                    conversation_id=state_dict["conversation_id"],
                    agent_name="prompt_security",
                    state_data={
                        "step": "security_check", 
                        "message": state_dict["message"],
                        "result": {
                            "is_safe": security_result.is_safe,
                            "passed": security_result.is_safe
                        }
                    },
                    workflow_step="security_check"
                )
            
            if security_result.is_safe:
                state_dict["security_check_passed"] = True
                state_dict["metadata"]["security_check"] = "passed"
                logger.info("Security check passed")
            else:
                state_dict["error"] = "Message failed security validation"
                state_dict["metadata"]["security_check"] = "failed"
                logger.warning("Security check failed")
                
        except Exception as e:
            logger.error(f"Security check error: {str(e)}")
            state_dict["error"] = f"Security check error: {str(e)}"
            
        return state_dict
    
    async def _navigator_analysis_node(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Patient navigator agent node for strategy workflow"""
        try:
            if not state_dict.get("security_check_passed"):
                state_dict["error"] = "Security check must pass before navigation"
                return state_dict
                
            logger.info("Executing navigator analysis")
            
            navigator_result = await self.patient_navigator_agent.analyze_request(
                state_dict["message"], state_dict["conversation_id"]
            )
            
            # Check if navigator identified insufficient information
            analysis_details = navigator_result.analysis_details
            meta_intent = analysis_details.get("meta_intent", {})
            
            # Check for insufficient information indicators
            information_sufficiency = meta_intent.get("information_sufficiency", "sufficient")
            missing_information = meta_intent.get("missing_information", [])
            
            # Set flags for workflow control
            if information_sufficiency == "insufficient" or missing_information:
                state_dict["needs_more_information"] = True
                state_dict["missing_information"] = missing_information
                state_dict["skip_strategy_agents"] = True
                logger.info(f"Navigator identified insufficient information: {missing_information}")
                
                # Set response text from navigator for immediate user feedback
                user_response = analysis_details.get("metadata", {}).get("user_response_created", "")
                if user_response and "I'll need" in user_response or "please provide" in user_response.lower():
                    state_dict["response_text"] = user_response
            else:
                state_dict["needs_more_information"] = False
                state_dict["skip_strategy_agents"] = False
            
            # Save agent state with detailed results
            if self.conversation_service:
                await self.conversation_service.save_agent_state(
                    conversation_id=state_dict["conversation_id"],
                    agent_name="patient_navigator",
                    state_data={
                        "step": "analysis", 
                        "message": state_dict["message"],
                        "needs_more_information": state_dict["needs_more_information"],
                        "missing_information": state_dict.get("missing_information", []),
                        "result": {
                            "intent_type": navigator_result.intent_type,
                            "confidence_score": navigator_result.confidence_score,
                            "analysis_details": navigator_result.analysis_details
                        }
                    },
                    workflow_step="navigator_analysis"
                )
            
            # Store the navigator result for use by Task Requirements
            state_dict["navigator_result"] = navigator_result.analysis_details
            
            state_dict["intent"] = navigator_result.intent_type
            state_dict["metadata"]["navigator_analysis"] = {
                "intent": navigator_result.intent_type,
                "confidence": navigator_result.confidence_score,
                "needs_more_information": state_dict["needs_more_information"]
            }
            
        except Exception as e:
            logger.error(f"Navigator analysis error: {str(e)}")
            state_dict["error"] = f"Navigator analysis error: {str(e)}"
            
        return state_dict
    
    async def _navigator_qa_node(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Patient navigator agent node for simple Q&A"""
        try:
            if not state_dict.get("security_check_passed"):
                state_dict["error"] = "Security check must pass before navigation"
                return state_dict
                
            logger.info("Executing navigator Q&A")
            
            # Save agent state
            if self.conversation_service:
                await self.conversation_service.save_agent_state(
                    conversation_id=state_dict["conversation_id"],
                    agent_name="patient_navigator",
                    state_data={"step": "qa", "message": state_dict["message"]},
                    workflow_step="navigator_qa"
                )
            
            qa_result = await self.patient_navigator_agent.answer_question(
                state_dict["message"], state_dict["conversation_id"]
            )
            
            state_dict["response_text"] = qa_result.answer
            state_dict["metadata"]["navigator_qa"] = {
                "question_type": qa_result.question_type,
                "confidence": qa_result.confidence_score
            }
            
        except Exception as e:
            logger.error(f"Navigator Q&A error: {str(e)}")
            state_dict["error"] = f"Navigator Q&A error: {str(e)}"
            
        return state_dict
    
    async def _task_requirements_node(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Task requirements agent node"""
        try:
            logger.info("Executing task requirements analysis")
            
            # Save agent state
            if self.conversation_service:
                await self.conversation_service.save_agent_state(
                    conversation_id=state_dict["conversation_id"],
                    agent_name="task_requirements",
                    state_data={"step": "requirements_analysis", "intent": state_dict["intent"]},
                    workflow_step="task_requirements"
                )
            
            # Get the navigator result which contains structured information
            navigator_result = state_dict.get("navigator_result", {})
            
            # Call Task Requirements agent with structured navigator output
            task_result = await self.task_requirements_agent.analyze_requirements_structured(
                navigator_result, state_dict["message"]
            )
            
            # Convert result to dict for JSON serialization and store for decision making
            task_result_dict = {
                "requirements_count": task_result.requirements_count,
                "documents_needed": task_result.documents_needed,
                "status": getattr(task_result, 'status', 'complete'),
                "missing_context": getattr(task_result, 'missing_context', []),
                "message_for_patient_navigator": getattr(task_result, 'message_for_patient_navigator', ''),
                "analysis_details": getattr(task_result, 'analysis_details', {})
            }
            state_dict["task_requirements_result"] = task_result_dict
            
            state_dict["metadata"]["task_requirements"] = {
                "requirements_identified": task_result.requirements_count,
                "documents_needed": task_result.documents_needed,
                "status": getattr(task_result, 'status', 'complete'),
                "missing_context": getattr(task_result, 'missing_context', []),
                "message_for_patient_navigator": getattr(task_result, 'message_for_patient_navigator', '')
            }
            
        except Exception as e:
            logger.error(f"Task requirements error: {str(e)}")
            state_dict["error"] = f"Task requirements error: {str(e)}"
            
        return state_dict
    
    async def _service_strategy_node(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Service access strategy agent node"""
        try:
            logger.info("Executing service strategy development")
            
            # Save agent state
            if self.conversation_service:
                await self.conversation_service.save_agent_state(
                    conversation_id=state_dict["conversation_id"],
                    agent_name="service_access_strategy",
                    state_data={"step": "strategy_development", "intent": state_dict["intent"]},
                    workflow_step="service_strategy"
                )
            
            # Get extracted information from navigator result
            navigator_result = state_dict.get("navigator_result", {})
            meta_intent = navigator_result.get("meta_intent", {})
            
            # Extract location and insurance from navigator
            extracted_location = meta_intent.get("location")
            extracted_insurance = meta_intent.get("insurance")
            
            # Prepare required parameters with all available info including extracted data
            patient_info = {
                "user_id": state_dict["user_id"],
                "conversation_id": state_dict["conversation_id"],
                "intent": state_dict.get("intent", ""),
                "original_message": state_dict["message"],
                "workflow_type": state_dict.get("workflow_type", ""),
                "metadata": state_dict.get("metadata", {}),
                "location": extracted_location,
                "insurance": extracted_insurance
            }
            
            medical_need = state_dict["message"]
            
            # Use extracted insurance information to build policy_info
            policy_info = {
                "policy_type": extracted_insurance or "Medicare",  # Use extracted insurance or default
                "plan_name": extracted_insurance or "Medicare Plan",
                "coverage_focus": "policy_navigation",
                "user_context": patient_info
            }
            
            # Check if we have sufficient information for demo-friendly response
            if extracted_location and extracted_insurance:
                logger.info(f"Using demo strategy response with location: {extracted_location}, insurance: {extracted_insurance}")
                # Use demo-friendly strategy response
                strategy_result = self._generate_demo_strategy_response(
                    state_dict["message"], 
                    extracted_location, 
                    extracted_insurance
                )
            else:
                # Fall back to the Service Access Strategy agent
                logger.info("Using Service Access Strategy agent (insufficient demo info)")
                strategy_result = self.service_access_strategy_agent.develop_strategy(
                    patient_info=patient_info,
                    medical_need=medical_need, 
                    policy_info=policy_info,
                    location=extracted_location,  # Pass extracted location
                    constraints=""  # Using default empty string
                )
            
            # Store the full strategy result for use by chat agent
            state_dict["strategy_result"] = strategy_result
            
            # Save agent state with detailed results
            if self.conversation_service:
                await self.conversation_service.save_agent_state(
                    conversation_id=state_dict["conversation_id"],
                    agent_name="service_access_strategy",
                    state_data={
                        "step": "strategy_development", 
                        "intent": state_dict["intent"],
                        "result": {
                            "strategy_summary": strategy_result,
                            "recommended_service": strategy_result.get("recommended_service"),
                            "action_plan": strategy_result.get("action_plan", []),
                            "estimated_timeline": strategy_result.get("estimated_timeline"),
                            "matched_services": strategy_result.get("matched_services", [])
                        }
                    },
                    workflow_step="service_strategy"
                )
            
            state_dict["metadata"]["service_strategy"] = {
                "strategy_type": strategy_result.get("recommended_service", "healthcare_guidance"),
                "action_steps": len(strategy_result.get("action_plan", []))
            }
            
        except Exception as e:
            logger.error(f"Service strategy error: {str(e)}")
            state_dict["error"] = f"Service strategy error: {str(e)}"
            
        return state_dict
    
    async def _regulatory_check_node(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Regulatory agent node"""
        try:
            logger.info("Executing regulatory compliance check")
            
            # Save agent state
            if self.conversation_service:
                await self.conversation_service.save_agent_state(
                    conversation_id=state_dict["conversation_id"],
                    agent_name="regulatory",
                    state_data={"step": "compliance_check", "strategy": state_dict["metadata"].get("service_strategy", {})},
                    workflow_step="regulatory_check"
                )
            
            regulatory_result = await self.regulatory_agent.check_compliance(
                state_dict["message"], state_dict["metadata"].get("service_strategy", {})
            )
            
            # Handle both dict and object responses
            if isinstance(regulatory_result, dict):
                state_dict["metadata"]["regulatory_check"] = {
                    "compliance_status": regulatory_result.get("status", "unknown"),
                    "regulations_checked": regulatory_result.get("regulations_count", 0)
                }
            else:
                # Handle object response
                state_dict["metadata"]["regulatory_check"] = {
                    "compliance_status": getattr(regulatory_result, 'status', 'unknown'),
                    "regulations_checked": getattr(regulatory_result, 'regulations_count', 0)
                }
            
        except Exception as e:
            logger.error(f"Regulatory check error: {str(e)}")
            state_dict["error"] = f"Regulatory check error: {str(e)}"
            
        return state_dict
    
    async def _chat_response_node(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Chat communicator agent node - final response generation"""
        try:
            logger.info("Generating final chat response")
            
            # Save agent state
            if self.conversation_service:
                await self.conversation_service.save_agent_state(
                    conversation_id=state_dict["conversation_id"],
                    agent_name="chat_communicator",
                    state_data={"step": "response_generation", "workflow_type": state_dict["workflow_type"]},
                    workflow_step="chat_response"
                )
            
            # Priority 1: Check if Task Requirements identified insufficient information
            task_result = state_dict.get("metadata", {}).get("task_requirements", {})
            if task_result.get("status") == "insufficient_information":
                logger.info("Generating information request based on Task Requirements feedback")
                
                missing_context = task_result.get("missing_context", [])
                message_for_navigator = task_result.get("message_for_patient_navigator", "")
                
                # Generate user-friendly request for missing information
                response_text = self._generate_information_request(missing_context, message_for_navigator, state_dict["message"])
                state_dict["response_text"] = response_text
                state_dict["metadata"]["chat_response"] = {
                    "response_type": "information_request",
                    "confidence": 0.9,
                    "has_strategy_data": False,
                    "reason": "insufficient_information_from_task_requirements",
                    "missing_items": missing_context
                }
                return state_dict
            
            # Priority 2: Check if we already have a response text from navigator (legacy insufficient info case)
            if state_dict.get("response_text") and state_dict.get("needs_more_information", False):
                logger.info("Using navigator response for insufficient information case")
                state_dict["metadata"]["chat_response"] = {
                    "response_type": "information_request",
                    "confidence": 0.9,
                    "has_strategy_data": False,
                    "reason": "insufficient_information_legacy"
                }
                return state_dict
            
            # Priority 3: Check if we have strategy results to work with
            strategy_result = state_dict.get("strategy_result")
            workflow_type = state_dict.get("workflow_type", "")
            
            if strategy_result and workflow_type == "strategy_request":
                # Generate response based on actual strategy data
                response_text = self._format_strategy_response(state_dict["message"], strategy_result)
                state_dict["response_text"] = response_text
                state_dict["metadata"]["chat_response"] = {
                    "response_type": "strategy_guidance",
                    "confidence": strategy_result.get("confidence", 0.8),
                    "has_strategy_data": True
                }
            elif self.chat_communicator_agent.use_mock:
                # Use mock response for simple Q&A
                from agents.chat_communicator.chat_models import ChatInput
                from agents.patient_navigator.navigator_models import NavigatorOutput, MetaIntent, ClinicalContext, ServiceIntent, Metadata, BodyLocation
                
                # Create a proper mock NavigatorOutput
                mock_navigator = NavigatorOutput(
                    meta_intent=MetaIntent(
                        request_type="policy_question",
                        summary=f"User question: {state_dict['message']}",
                        emergency=False
                    ),
                    clinical_context=ClinicalContext(
                        symptom=None,
                        body=BodyLocation(),
                        onset=None,
                        duration=None
                    ),
                    service_intent=ServiceIntent(
                        specialty="general",
                        service="information",
                        plan_detail_type="coverage"
                    ),
                    metadata=Metadata(
                        raw_user_text=state_dict["message"],
                        user_response_created="Processing your request...",
                        timestamp=datetime.utcnow().isoformat() + "Z"
                    )
                )
                
                mock_input = ChatInput(
                    source_type="navigator_output",
                    data=mock_navigator,
                    user_id=state_dict["user_id"],
                    session_id=state_dict["conversation_id"]
                )
                
                chat_result = self.chat_communicator_agent._generate_mock_response(mock_input)
                
                state_dict["response_text"] = chat_result.message
                state_dict["metadata"]["chat_response"] = {
                    "response_type": chat_result.response_type,
                    "confidence": chat_result.confidence,
                    "has_strategy_data": False
                }
            else:
                # Fallback response
                state_dict["response_text"] = f"Thank you for your question about '{state_dict['message']}'. I'm here to help you navigate your healthcare options."
                state_dict["metadata"]["chat_response"] = {
                    "response_type": "informational",
                    "confidence": 0.8,
                    "has_strategy_data": False
                }
            
        except Exception as e:
            logger.error(f"Chat response error: {str(e)}")
            state_dict["error"] = f"Chat response error: {str(e)}"
            
        return state_dict
    
    def _format_strategy_response(self, user_message: str, strategy_result: Dict[str, Any]) -> str:
        """Format the strategy result into a user-friendly response."""
        try:
            recommended_service = strategy_result.get("recommended_service", "healthcare guidance")
            action_plan = strategy_result.get("action_plan", [])
            estimated_timeline = strategy_result.get("estimated_timeline", "Contact your provider for timeline")
            matched_services = strategy_result.get("matched_services", [])
            
            # Start building the response
            response_parts = []
            
            # Introduction
            response_parts.append(f"I can help you with accessing {user_message.lower()}. Here's your personalized strategy:")
            response_parts.append("")
            
            # Recommended approach
            response_parts.append(f"**Recommended Approach:** {recommended_service}")
            response_parts.append("")
            
            # Service information
            if matched_services:
                service = matched_services[0]  # Take the first matched service
                if service.get("is_covered"):
                    response_parts.append("✅ **Coverage Status:** This service is typically covered under your plan")
                    coverage_details = service.get("coverage_details", {})
                    if coverage_details:
                        response_parts.append(f"   • Cost: {coverage_details.get('copay', 'Contact insurance for details')}")
                else:
                    response_parts.append("⚠️  **Coverage Status:** Please verify coverage with your insurance")
                response_parts.append("")
            
            # Action steps
            if action_plan:
                response_parts.append("**Step-by-Step Action Plan:**")
                for i, step in enumerate(action_plan, 1):
                    step_desc = step.get("step_description", f"Step {i}")
                    timeline = step.get("expected_timeline", "")
                    response_parts.append(f"{i}. {step_desc}")
                    if timeline:
                        response_parts.append(f"   ⏱ Timeline: {timeline}")
                    
                    resources = step.get("required_resources", [])
                    if resources:
                        response_parts.append(f"   📋 You'll need: {', '.join(resources)}")
                    response_parts.append("")
            
            # Timeline
            response_parts.append(f"**Estimated Timeline:** {estimated_timeline}")
            response_parts.append("")
            
            # Additional guidance
            guidance_notes = strategy_result.get("guidance_notes", [])
            if guidance_notes:
                response_parts.append("**Additional Guidance:**")
                for note in guidance_notes:
                    response_parts.append(f"• {note}")
                response_parts.append("")
            
            # Closing
            response_parts.append("Would you like me to explain any of these steps in more detail or help you with the next action?")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error formatting strategy response: {str(e)}")
            return f"I can help you with {user_message}. Please contact your healthcare provider to get started with accessing this service. They can guide you through the process and verify your insurance coverage."
    
    def _generate_information_request(self, missing_context: list, navigator_message: str, original_query: str) -> str:
        """Generate a user-friendly request for missing information based on Task Requirements analysis"""
        response_parts = ["I'd be happy to help you with your request!"]
        
        # Parse the missing context to create user-friendly requests
        missing_items = []
        for item in missing_context:
            if "insurance" in item.lower():
                missing_items.append("your insurance plan or coverage type")
            elif "location" in item.lower():
                missing_items.append("your location or preferred area")
            elif "plan_details" in item.lower():
                missing_items.append("specific details about your insurance plan")
            else:
                missing_items.append(item.replace("_", " "))
        
        if missing_items:
            if len(missing_items) == 1:
                response_parts.append(f"To provide you with the most accurate guidance, I'll need to know {missing_items[0]}.")
            else:
                response_parts.append(f"To provide you with the most accurate guidance, I'll need to know:")
                for item in missing_items:
                    response_parts.append(f"• {item.capitalize()}")
        
        # Add specific guidance based on common missing items
        if any("insurance" in item.lower() for item in missing_context):
            response_parts.append("\nFor insurance information, please share your insurance provider (like Blue Cross, Aetna, Medicare, etc.) and plan type if you know it.")
        
        if any("location" in item.lower() for item in missing_context):
            response_parts.append("\nFor location, please share your city and state, or ZIP code.")
        
        response_parts.append(f"\nOnce I have this information, I can help you find the best options for: {original_query}")
        
        return "\n".join(response_parts)
    
    def _create_error_response(self, error_message: str, conversation_id: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "text": "I apologize, but I'm experiencing some technical difficulties. Please try rephrasing your question or contact support if the issue persists.",
            "metadata": {
                "error": error_message,
                "timestamp": datetime.utcnow().isoformat()
            },
            "conversation_id": conversation_id,
            "workflow_type": "error"
        }

    def _generate_demo_strategy_response(self, user_message: str, extracted_location: str, extracted_insurance: str) -> Dict[str, Any]:
        """Generate a demo-friendly strategy response when we have sufficient information"""
        location_text = extracted_location or "your area"
        insurance_text = extracted_insurance or "your insurance plan"
        
        # Extract the medical need from the message
        medical_need = user_message.lower()
        service_type = "healthcare service"
        if "cardiologist" in medical_need:
            service_type = "cardiology consultation"
        elif "x-ray" in medical_need:
            service_type = "X-ray imaging"
        elif "doctor" in medical_need:
            service_type = "medical consultation"
        
        return {
            "patient_need": user_message,
            "matched_services": [
                {
                    "service_name": service_type.title(),
                    "service_type": service_type,
                    "service_description": f"Access to {service_type} in {location_text}",
                    "is_covered": True,
                    "coverage_details": {
                        "copay": "$15-40",
                        "requires_referral": "Depends on plan type",
                        "prior_authorization": False,
                        "coverage_notes": [f"Covered under {insurance_text}"]
                    },
                    "estimated_cost": "$15-40 copay",
                    "required_documentation": ["Insurance card", "ID"],
                    "prerequisites": ["Active insurance plan"],
                    "alternatives": ["Telehealth consultation", "Urgent care"],
                    "compliance_score": 0.9
                }
            ],
            "recommended_service": f"In-network {service_type} in {location_text}",
            "action_plan": [
                {
                    "step_number": 1,
                    "step_description": f"Contact your {insurance_text} to find in-network providers in {location_text}",
                    "expected_timeline": "1-2 days",
                    "required_resources": ["Insurance card", "Provider directory"],
                    "potential_obstacles": ["Limited availability"],
                    "contingency_plan": "Expand search radius or consider telehealth options"
                },
                {
                    "step_number": 2,
                    "step_description": f"Schedule appointment with recommended provider",
                    "expected_timeline": "1-3 weeks",
                    "required_resources": ["Insurance card", "Referral if needed"],
                    "potential_obstacles": ["Wait times"],
                    "contingency_plan": "Ask to be placed on cancellation list"
                },
                {
                    "step_number": 3,
                    "step_description": "Prepare for your appointment",
                    "expected_timeline": "Before appointment",
                    "required_resources": ["Medical history", "List of questions"],
                    "potential_obstacles": ["Missing records"],
                    "contingency_plan": "Contact previous providers for records"
                }
            ],
            "estimated_timeline": "2-4 weeks",
            "provider_options": [
                {
                    "name": f"Healthcare Provider in {location_text}",
                    "address": f"{location_text} Medical Center",
                    "distance": "2-5 miles",
                    "in_network": True,
                    "specialties": [service_type],
                    "availability": "Appointments available"
                }
            ],
            "compliance_assessment": {
                "is_compliant": True,
                "compliance_notes": ["Follows standard care guidelines"]
            },
            "guidance_notes": [
                f"Your {insurance_text} plan should cover this service",
                f"We've identified options in {location_text}",
                "Verify coverage details before scheduling"
            ],
            "confidence": 0.9
        }


# Global orchestrator instance
orchestrator = None

def get_orchestrator(bypass_security: Optional[bool] = None) -> AgentOrchestrator:
    """Get or create the global agent orchestrator"""
    global orchestrator
    if orchestrator is None:
        orchestrator = AgentOrchestrator(bypass_security=bypass_security)
    return orchestrator

def reset_orchestrator() -> None:
    """Reset the global orchestrator instance to force re-initialization"""
    global orchestrator
    orchestrator = None

async def run_workflow(message: str, user_id: str, conversation_id: Optional[str] = None, bypass_security: Optional[bool] = None) -> Dict[str, Any]:
    """Convenience function to run workflow"""
    orch = get_orchestrator(bypass_security=bypass_security)
    return await orch.process_message(message, user_id, conversation_id) 