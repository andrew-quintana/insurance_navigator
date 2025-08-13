"""
Communication Agent for Output Processing Workflow.

This agent transforms technical agent outputs into warm, empathetic, user-friendly responses
using the BaseAgent pattern and Claude Haiku LLM.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent
from .types import CommunicationRequest, CommunicationResponse, AgentOutput
from .config import OutputProcessingConfig


class CommunicationAgent(BaseAgent):
    """
    Communication Agent that enhances agent outputs with warm, empathetic communication.
    
    Inherits from BaseAgent following established patterns in the codebase.
    Uses Claude Haiku LLM for consistent performance and cost efficiency.
    """
    
    def __init__(self, llm_client=None, config: Optional[OutputProcessingConfig] = None, **kwargs):
        """
        Initialize the Communication Agent.
        
        Args:
            llm_client: LLM client for Claude Haiku (or None for mock mode)
            config: Configuration for the agent
            **kwargs: Additional arguments passed to BaseAgent
        """
        self.config = config or OutputProcessingConfig.from_environment()
        
        super().__init__(
            name="output_communication",
            prompt="prompts/system_prompt.md",
            output_schema=CommunicationResponse,
            llm=llm_client,  # Claude Haiku client
            mock=llm_client is None,
            **kwargs
        )
        
        self.logger = logging.getLogger(f"agent.{self.name}")
        self.logger.info(f"Initialized Communication Agent with config: {self.config.to_dict()}")
    
    def mock_output(self, user_input: str) -> CommunicationResponse:
        """
        Generate a realistic mock output for testing.
        Overrides BaseAgent's mock_output method.
        """
        # Create a realistic mock response based on the input
        if "denied" in user_input.lower() or "exclusion" in user_input.lower():
            enhanced_content = (
                "I understand this is frustrating news. Your claim was denied due to a policy exclusion. "
                "This means the insurance company determined the condition or treatment isn't covered under your current policy.\n\n"
                "**What this means:** Your policy has specific exclusions that prevent coverage for this situation.\n\n"
                "**Next steps you can take:**\n"
                "1. Review the denial letter for specific details\n"
                "2. Consider appealing if you believe this is an error\n"
                "3. Contact your insurance company to discuss options\n"
                "4. Ask about alternative benefits that might be available\n\n"
                "Remember, many denials can be successfully appealed. Would you like help understanding the appeals process?"
            )
        elif "benefits" in user_input.lower() or "coverage" in user_input.lower():
            enhanced_content = (
                "Great news! Here's what your insurance plan covers:\n\n"
                "**Your Coverage Summary:**\n"
                "• In-network services: 80% coverage after meeting your deductible\n"
                "• Out-of-network services: 60% coverage after meeting your deductible\n"
                "• Deductible: $500 for in-network, $1000 for out-of-network\n\n"
                "**What this means for you:**\n"
                "You have comprehensive coverage that will help significantly with your healthcare costs. "
                "The deductible is the amount you pay before insurance starts covering your care.\n\n"
                "**Next steps:**\n"
                "1. Keep track of your healthcare expenses\n"
                "2. Try to use in-network providers when possible\n"
                "3. Save receipts and explanation of benefits statements"
            )
        else:
            enhanced_content = (
                "Based on the information provided, here's what I can tell you:\n\n"
                "**Summary:** The details from your insurance analysis have been reviewed and processed.\n\n"
                "**Key Points:**\n"
                "• Your coverage status has been confirmed\n"
                "• All relevant policy information has been analyzed\n"
                "• Recommendations are based on your specific plan details\n\n"
                "**Next Steps:**\n"
                "1. Review the information provided\n"
                "2. Contact your insurance company if you have questions\n"
                "3. Keep this information for future reference"
            )
        
        return CommunicationResponse(
            enhanced_content=enhanced_content,
            original_sources=["mock_agent_1", "mock_agent_2"],
            processing_time=0.5,
            metadata={
                "mock_response": True,
                "input_analyzed": True,
                "tone_applied": "warm_empathetic"
            }
        )
    
    async def enhance_response(self, request: CommunicationRequest) -> CommunicationResponse:
        """
        Process agent outputs and return enhanced response with warm, empathetic communication.
        
        Args:
            request: CommunicationRequest containing agent outputs and user context
            
        Returns:
            CommunicationResponse with enhanced content and metadata
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Processing communication request with {len(request.agent_outputs)} agent outputs")
            
            # Validate input
            self._validate_request(request)
            
            # Prepare input for LLM
            formatted_input = self._format_agent_outputs(request)
            
            # Call the agent (inherited from BaseAgent)
            response = self(formatted_input, user_context=request.user_context)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Extract original sources
            original_sources = [output.agent_id for output in request.agent_outputs]
            
            # Create enhanced response
            enhanced_response = CommunicationResponse(
                enhanced_content=response.enhanced_content,
                original_sources=original_sources,
                processing_time=processing_time,
                metadata={
                    "config_used": self.config.to_dict(),
                    "input_agent_count": len(request.agent_outputs),
                    "user_context_provided": request.user_context is not None
                }
            )
            
            self.logger.info(f"Successfully enhanced response in {processing_time:.2f}s")
            return enhanced_response
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Error enhancing response: {e}")
            
            if self.config.enable_fallback and self.config.fallback_to_original:
                return self._create_fallback_response(request, processing_time, str(e))
            else:
                raise
    
    def _validate_request(self, request: CommunicationRequest) -> None:
        """Validate the communication request."""
        if not request.agent_outputs:
            raise ValueError("At least one agent output is required")
        
        if len(request.agent_outputs) > self.config.max_agent_outputs:
            raise ValueError(f"Too many agent outputs: {len(request.agent_outputs)} > {self.config.max_agent_outputs}")
        
        total_content_length = sum(len(output.content) for output in request.agent_outputs)
        if total_content_length > self.config.max_input_length:
            raise ValueError(f"Total content length too long: {total_content_length} > {self.config.max_input_length}")
    
    def _format_agent_outputs(self, request: CommunicationRequest) -> str:
        """Format agent outputs into a single input string for the LLM."""
        formatted_parts = []
        
        for i, output in enumerate(request.agent_outputs, 1):
            formatted_parts.append(f"Agent {i} ({output.agent_id}):")
            formatted_parts.append(output.content)
            if output.metadata:
                formatted_parts.append(f"Metadata: {output.metadata}")
            formatted_parts.append("")  # Empty line for separation
        
        if request.user_context:
            formatted_parts.append("User Context:")
            formatted_parts.append(str(request.user_context))
        
        return "\n".join(formatted_parts)
    
    def _create_fallback_response(self, request: CommunicationRequest, processing_time: float, error_message: str) -> CommunicationResponse:
        """Create a fallback response when enhancement fails."""
        self.logger.warning("Creating fallback response due to enhancement failure")
        
        # Combine original agent outputs into a simple consolidated response
        fallback_content = self._consolidate_original_outputs(request.agent_outputs)
        
        return CommunicationResponse(
            enhanced_content=fallback_content,
            original_sources=[output.agent_id for output in request.agent_outputs],
            processing_time=processing_time,
            metadata={
                "fallback_used": True,
                "error_message": error_message,
                "original_content_consolidated": True
            }
        )
    
    def _consolidate_original_outputs(self, agent_outputs: List[AgentOutput]) -> str:
        """Create a simple consolidation of original agent outputs."""
        if len(agent_outputs) == 1:
            return agent_outputs[0].content
        
        consolidated = "Based on the information provided:\n\n"
        for i, output in enumerate(agent_outputs, 1):
            consolidated += f"{i}. {output.content}\n\n"
        
        consolidated += "Note: This is a basic consolidation of the original agent outputs."
        return consolidated
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the agent for monitoring/debugging."""
        return {
            "name": self.name,
            "config": self.config.to_dict(),
            "prompt_length": len(self.prompt) if self.prompt else 0,
            "mock_mode": self.mock,
            "llm_available": self.llm is not None
        }
