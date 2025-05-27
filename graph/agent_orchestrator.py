"""
LangGraph Agent Orchestrator for Medicare Navigator
Handles orchestration of multiple agents based on intent routing.
"""

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

logger = logging.getLogger(__name__)

class AgentState:
    """State object for LangGraph workflow"""
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
        
class AgentOrchestrator:
    """Orchestrates multiple agents using LangGraph workflows"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self._initialize_agents()
        self._build_workflows()
        
    def _initialize_agents(self):
        """Initialize all required agents"""
        try:
            self.prompt_security_agent = PromptSecurityAgent()
            self.patient_navigator_agent = PatientNavigatorAgent()
            self.task_requirements_agent = TaskRequirementsAgent()
            self.service_access_strategy_agent = ServiceAccessStrategyAgent()
            self.regulatory_agent = RegulatoryAgent()
            self.chat_communicator_agent = ChatCommunicatorAgent()
            
            logger.info("All agents initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agents: {str(e)}")
            raise AgentException(f"Agent initialization failed: {str(e)}")
    
    def _build_workflows(self):
        """Build LangGraph workflows for different scenarios"""
        # Strategy request workflow: Security → Navigator → Task → Strategy → Regulatory → Chat
        self.strategy_workflow = StateGraph(AgentState)
        
        # Add nodes
        self.strategy_workflow.add_node("security_check", self._security_check_node)
        self.strategy_workflow.add_node("navigator_analysis", self._navigator_analysis_node)
        self.strategy_workflow.add_node("task_requirements", self._task_requirements_node)
        self.strategy_workflow.add_node("service_strategy", self._service_strategy_node)
        self.strategy_workflow.add_node("regulatory_check", self._regulatory_check_node)
        self.strategy_workflow.add_node("chat_response", self._chat_response_node)
        
        # Add edges for strategy workflow
        self.strategy_workflow.add_edge("security_check", "navigator_analysis")
        self.strategy_workflow.add_edge("navigator_analysis", "task_requirements")
        self.strategy_workflow.add_edge("task_requirements", "service_strategy")
        self.strategy_workflow.add_edge("service_strategy", "regulatory_check")
        self.strategy_workflow.add_edge("regulatory_check", "chat_response")
        
        # Set entry point
        self.strategy_workflow.set_entry_point("security_check")
        
        # Navigator-only workflow: Security → Navigator → Chat
        self.navigator_workflow = StateGraph(AgentState)
        
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
    
    async def process_message(
        self, 
        message: str, 
        user_id: str, 
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing user messages
        Routes to appropriate workflow based on intent
        """
        if not conversation_id:
            conversation_id = f"conv_{uuid4().hex[:8]}"
            
        try:
            # Initialize state
            state = AgentState()
            state.message = message
            state.user_id = user_id
            state.conversation_id = conversation_id
            
            # Determine workflow type based on message content
            workflow_type = self._determine_workflow_type(message)
            state.workflow_type = workflow_type
            
            logger.info(f"Processing message with {workflow_type} workflow for user {user_id}")
            
            # Execute appropriate workflow
            if workflow_type == "strategy_request":
                final_state = await self._execute_strategy_workflow(state)
            else:
                final_state = await self._execute_navigator_workflow(state)
            
            # Handle errors
            if final_state.error:
                logger.error(f"Workflow error: {final_state.error}")
                return self._create_error_response(final_state.error, conversation_id)
            
            # Return successful response
            return {
                "text": final_state.response_text,
                "metadata": final_state.metadata,
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
            "network", "referral", "appointment", "help me", "need to", "how do i"
        ]
        
        # Check if message contains strategy-related keywords
        if any(keyword in message_lower for keyword in strategy_keywords):
            return "strategy_request"
        
        return "navigator_only"
    
    async def _execute_strategy_workflow(self, state: AgentState) -> AgentState:
        """Execute the strategy request workflow"""
        try:
            result = await self.compiled_strategy_workflow.ainvoke({"state": state})
            return result["state"]
        except Exception as e:
            state.error = f"Strategy workflow error: {str(e)}"
            return state
    
    async def _execute_navigator_workflow(self, state: AgentState) -> AgentState:
        """Execute the navigator-only workflow"""
        try:
            result = await self.compiled_navigator_workflow.ainvoke({"state": state})
            return result["state"]
        except Exception as e:
            state.error = f"Navigator workflow error: {str(e)}"
            return state
    
    # Workflow node implementations
    async def _security_check_node(self, state: AgentState) -> AgentState:
        """Prompt security agent node"""
        try:
            logger.info("Executing security check")
            security_result = await self.prompt_security_agent.check_prompt_security(
                state.message, state.user_id
            )
            
            if security_result.is_safe:
                state.security_check_passed = True
                state.metadata["security_check"] = "passed"
                logger.info("Security check passed")
            else:
                state.error = "Message failed security validation"
                state.metadata["security_check"] = "failed"
                logger.warning("Security check failed")
                
        except Exception as e:
            logger.error(f"Security check error: {str(e)}")
            state.error = f"Security check error: {str(e)}"
            
        return state
    
    async def _navigator_analysis_node(self, state: AgentState) -> AgentState:
        """Patient navigator agent node for strategy workflow"""
        try:
            if not state.security_check_passed:
                state.error = "Security check must pass before navigation"
                return state
                
            logger.info("Executing navigator analysis")
            navigator_result = await self.patient_navigator_agent.analyze_request(
                state.message, state.conversation_id
            )
            
            state.intent = navigator_result.intent_type
            state.metadata["navigator_analysis"] = {
                "intent": navigator_result.intent_type,
                "confidence": navigator_result.confidence_score
            }
            
        except Exception as e:
            logger.error(f"Navigator analysis error: {str(e)}")
            state.error = f"Navigator analysis error: {str(e)}"
            
        return state
    
    async def _navigator_qa_node(self, state: AgentState) -> AgentState:
        """Patient navigator agent node for simple Q&A"""
        try:
            if not state.security_check_passed:
                state.error = "Security check must pass before navigation"
                return state
                
            logger.info("Executing navigator Q&A")
            qa_result = await self.patient_navigator_agent.answer_question(
                state.message, state.conversation_id
            )
            
            state.response_text = qa_result.answer
            state.metadata["navigator_qa"] = {
                "question_type": qa_result.question_type,
                "confidence": qa_result.confidence_score
            }
            
        except Exception as e:
            logger.error(f"Navigator Q&A error: {str(e)}")
            state.error = f"Navigator Q&A error: {str(e)}"
            
        return state
    
    async def _task_requirements_node(self, state: AgentState) -> AgentState:
        """Task requirements agent node"""
        try:
            logger.info("Executing task requirements analysis")
            task_result = await self.task_requirements_agent.analyze_requirements(
                state.message, state.intent
            )
            
            state.metadata["task_requirements"] = {
                "requirements_identified": task_result.requirements_count,
                "documents_needed": task_result.documents_needed
            }
            
        except Exception as e:
            logger.error(f"Task requirements error: {str(e)}")
            state.error = f"Task requirements error: {str(e)}"
            
        return state
    
    async def _service_strategy_node(self, state: AgentState) -> AgentState:
        """Service access strategy agent node"""
        try:
            logger.info("Executing service strategy development")
            strategy_result = await self.service_access_strategy_agent.develop_strategy(
                state.message, state.intent
            )
            
            state.metadata["service_strategy"] = {
                "strategy_type": strategy_result.strategy_type,
                "action_steps": len(strategy_result.action_steps)
            }
            
        except Exception as e:
            logger.error(f"Service strategy error: {str(e)}")
            state.error = f"Service strategy error: {str(e)}"
            
        return state
    
    async def _regulatory_check_node(self, state: AgentState) -> AgentState:
        """Regulatory agent node"""
        try:
            logger.info("Executing regulatory compliance check")
            regulatory_result = await self.regulatory_agent.check_compliance(
                state.message, state.metadata.get("service_strategy", {})
            )
            
            state.metadata["regulatory_check"] = {
                "compliance_status": regulatory_result.status,
                "regulations_checked": regulatory_result.regulations_count
            }
            
        except Exception as e:
            logger.error(f"Regulatory check error: {str(e)}")
            state.error = f"Regulatory check error: {str(e)}"
            
        return state
    
    async def _chat_response_node(self, state: AgentState) -> AgentState:
        """Chat communicator agent node - final response generation"""
        try:
            logger.info("Generating final chat response")
            
            # Prepare context for chat communicator
            context = {
                "original_message": state.message,
                "workflow_type": state.workflow_type,
                "metadata": state.metadata
            }
            
            chat_result = await self.chat_communicator_agent.generate_response(
                context, state.conversation_id
            )
            
            state.response_text = chat_result.response_text
            state.metadata["chat_response"] = {
                "response_type": chat_result.response_type,
                "confidence": chat_result.confidence_score
            }
            
        except Exception as e:
            logger.error(f"Chat response error: {str(e)}")
            state.error = f"Chat response error: {str(e)}"
            
        return state
    
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


# Global orchestrator instance
orchestrator = None

def get_orchestrator() -> AgentOrchestrator:
    """Get or create the global agent orchestrator"""
    global orchestrator
    if orchestrator is None:
        orchestrator = AgentOrchestrator()
    return orchestrator

async def run_workflow(message: str, user_id: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to run workflow"""
    orch = get_orchestrator()
    return await orch.process_message(message, user_id, conversation_id) 