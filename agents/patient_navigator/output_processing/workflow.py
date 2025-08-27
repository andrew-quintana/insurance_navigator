"""
Output Workflow for Output Processing.

This module provides a simple workflow wrapper around the Communication Agent
for integration with existing agent workflow patterns.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from .agent import CommunicationAgent
from .types import CommunicationRequest, CommunicationResponse, AgentOutput
from .config import OutputProcessingConfig


class OutputWorkflow:
    """
    Simple workflow wrapper for the Output Communication Agent.
    
    Provides basic orchestration and integration points for existing
    agent workflow patterns in the codebase.
    """
    
    def __init__(self, config: Optional[OutputProcessingConfig] = None, llm_client=None):
        """
        Initialize the Output Workflow.
        
        Args:
            config: Configuration for the workflow
            llm_client: LLM client for Claude Haiku
        """
        self.config = config or OutputProcessingConfig.from_environment()
        self.communication_agent = CommunicationAgent(
            llm_client=llm_client,
            config=self.config
        )
        self.logger = logging.getLogger(f"workflow.{self.__class__.__name__}")
        
        self.logger.info(f"Initialized Output Workflow with config: {self.config.to_dict()}")
    
    async def process_request(self, request: CommunicationRequest) -> CommunicationResponse:
        """
        Process a communication request through the workflow.
        
        Args:
            request: CommunicationRequest containing agent outputs and user context
            
        Returns:
            CommunicationResponse with enhanced content and metadata
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Processing workflow request with {len(request.agent_outputs)} agent outputs")
            
            # Basic validation
            self._validate_workflow_request(request)
            
            # Call the communication agent
            response = await self.communication_agent.enhance_response(request)
            
            # Add workflow-level metadata
            workflow_time = time.time() - start_time
            response.metadata.update({
                "workflow_processing_time": workflow_time,
                "workflow_version": "1.0.0",
                "workflow_success": True
            })
            
            self.logger.info(f"Workflow completed successfully in {workflow_time:.2f}s")
            return response
            
        except Exception as e:
            workflow_time = time.time() - start_time
            self.logger.error(f"Workflow processing failed: {e}")
            
            # Create error response with fallback content
            error_response = self._create_error_response(request, workflow_time, str(e))
            return error_response
    
    def _validate_workflow_request(self, request: CommunicationRequest) -> None:
        """Validate the workflow request."""
        if not request.agent_outputs:
            raise ValueError("At least one agent output is required")
        
        # Additional workflow-level validation can be added here
        self.logger.debug(f"Workflow validation passed for {len(request.agent_outputs)} agent outputs")
    
    def _create_error_response(self, request: CommunicationRequest, processing_time: float, error_message: str) -> CommunicationResponse:
        """Create an error response when workflow processing fails."""
        self.logger.warning("Creating error response due to workflow failure")
        
        # Use the agent's fallback mechanism
        try:
            return self.communication_agent._create_fallback_response(
                request, processing_time, error_message
            )
        except Exception as fallback_error:
            self.logger.error(f"Even fallback response creation failed: {fallback_error}")
            
            # Ultimate fallback: return minimal response
            return CommunicationResponse(
                enhanced_content="I'm sorry, but I encountered an error while processing your request. Please try again or contact support if the problem persists.",
                original_sources=[output.agent_id for output in request.agent_outputs],
                processing_time=processing_time,
                metadata={
                    "workflow_error": True,
                    "error_message": error_message,
                    "fallback_creation_failed": True,
                    "ultimate_fallback": True
                }
            )
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the workflow for monitoring/debugging."""
        return {
            "workflow_type": "output_processing",
            "config": self.config.to_dict(),
            "agent_info": self.communication_agent.get_agent_info(),
            "workflow_version": "1.0.0"
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the workflow components."""
        health_status = {
            "workflow": "healthy",
            "agent": "healthy",
            "config": "valid",
            "timestamp": time.time()
        }
        
        try:
            # Validate configuration
            self.config.validate()
        except Exception as e:
            health_status["config"] = f"invalid: {str(e)}"
            health_status["workflow"] = "unhealthy"
        
        try:
            # Check agent health
            agent_info = self.communication_agent.get_agent_info()
            if not agent_info["llm_available"] and not agent_info["mock_mode"]:
                health_status["agent"] = "unhealthy: no LLM available"
                health_status["workflow"] = "unhealthy"
        except Exception as e:
            health_status["agent"] = f"unhealthy: {str(e)}"
            health_status["workflow"] = "unhealthy"
        
        return health_status
