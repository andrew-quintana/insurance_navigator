"""
Communication Agent for Output Processing Workflow.

This agent transforms technical agent outputs into warm, empathetic, user-friendly responses
using the BaseAgent pattern and Claude Sonnet 4.5 LLM.
"""

import logging
import time
import os
from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent
from .types import CommunicationRequest, CommunicationResponse, AgentOutput
from .config import OutputProcessingConfig


def _get_claude_sonnet_llm():
    """
    Return a callable that invokes Claude Sonnet 4.5, or None for mock mode.
    
    We prefer to avoid hard dependency; if Anthropic client isn't available,
    we return None and the agent will run in mock mode.
    """
    try:
        from anthropic import Anthropic
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        
        client = Anthropic(api_key=api_key, timeout=30.0)
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        
        def call_llm(prompt: str) -> str:
            """Call Claude Sonnet 4.5 with the given prompt."""
            try:
                # Add explicit JSON formatting instruction to the prompt
                json_prompt = prompt + "\n\nIMPORTANT: You must respond with ONLY valid JSON. Do not include any other text, explanations, or formatting outside the JSON object."
                
                resp = client.messages.create(
                    model=model,
                    max_tokens=4000,
                    temperature=0.2,
                    messages=[{"role": "user", "content": json_prompt}],
                )
                
                content = resp.content[0].text if getattr(resp, "content", None) else ""
                
                if not content:
                    raise ValueError("Empty response from Claude Sonnet")
                
                # The response should now be plain text, not JSON
                content = content.strip()
                
                # If the response starts with a backtick, extract the content from within
                if content.startswith("```json"):
                    content = content.split("```json")[1].split("```")[0].strip()
                elif content.startswith("```"):
                    content = content.split("```")[1].split("```")[0].strip()
                
                # Check if the response is still JSON format (fallback for old behavior)
                if content.startswith('{'):
                    logging.warning("Claude Sonnet returned JSON format instead of plain text, extracting content...")
                    try:
                        import json
                        parsed_json = json.loads(content)
                        enhanced_content = parsed_json.get("enhanced_content", content)
                        return enhanced_content
                    except json.JSONDecodeError:
                        # If JSON parsing fails, return the content as-is
                        pass
                
                # Return the plain text content directly
                return content
                
            except Exception as e:
                logging.error(f"Claude Sonnet API call failed: {e}")
                raise
        
        return call_llm
        
    except Exception as e:
        logging.warning(f"Failed to initialize Anthropic client: {e}")
        return None


class CommunicationAgent(BaseAgent):
    """
    Communication Agent that enhances agent outputs with warm, empathetic communication.
    
    Inherits from BaseAgent following established patterns in the codebase.
    Uses Claude Sonnet 4.5 LLM for high-quality response generation.
    """
    
    def __init__(self, llm_client=None, config: Optional[OutputProcessingConfig] = None, **kwargs):
        """
        Initialize the Communication Agent.
        
        Args:
            llm_client: LLM client for Claude Sonnet 4.5 (or None for auto-detection)
            config: Configuration for the agent
            **kwargs: Additional arguments passed to BaseAgent
        """
        # Store the original config before BaseAgent initialization
        original_config = config or OutputProcessingConfig.from_environment()
        
        # Auto-detect LLM client if not provided
        if llm_client is None:
            llm_client = _get_claude_sonnet_llm()
            if llm_client:
                logging.info("Auto-detected Claude Sonnet 4.5 LLM client")
            else:
                logging.info("No Claude Sonnet client available, using mock mode")
        
        super().__init__(
            name="output_communication",
            prompt=os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.md"),
            output_schema=CommunicationResponse,
            llm=llm_client,  # Claude Sonnet 4.5 client or None for mock mode
            mock=llm_client is None,
            config=original_config.to_dict(),  # Pass config as dictionary to BaseAgent
            **kwargs
        )
        
        # Restore the original config object after BaseAgent initialization
        self.config = original_config
        
        self.logger = logging.getLogger(f"agent.{self.name}")
        self.logger.info(f"Initialized Communication Agent with config: {self.config.to_dict()}")
    
    def __call__(self, user_input: str, **kwargs) -> CommunicationResponse:
        """
        Override BaseAgent.__call__ to handle plain text responses instead of JSON.
        
        Args:
            user_input: Formatted input containing agent outputs
            **kwargs: Additional arguments (user_context, etc.)
            
        Returns:
            CommunicationResponse with enhanced content
        """
        self.logger.info(f"[{self.name}] Starting agent execution")
        self.logger.info(f"[{self.name}] Input length: {len(user_input)} characters")
        
        prompt = self.format_prompt(user_input, **kwargs)
        self.logger.info(f"[{self.name}] Prompt formatted, length: {len(prompt)} characters")
        
        if self.mock or self.llm is None:
            self.logger.info(f"[{self.name}] Using mock output mode.")
            return self.mock_output(user_input)
        else:
            try:
                self.logger.info(f"[{self.name}] Calling LLM...")
                llm_result = self.llm(prompt)
                self.logger.info(f"[{self.name}] LLM call completed, result length: {len(str(llm_result))} characters")
                
                # Handle plain text response instead of JSON
                enhanced_content = str(llm_result).strip()
                
                # Extract user_context if provided
                user_context = kwargs.get('user_context', {})
                
                # Create CommunicationResponse with plain text content
                response = CommunicationResponse(
                    enhanced_content=enhanced_content,
                    original_sources=["unknown"],  # Will be set by caller
                    processing_time=0.0,  # Will be calculated by caller
                    metadata={
                        "tone_applied": "warm_empathetic",
                        "content_type": "enhanced_response",
                        "enhancement_quality": "high"
                    }
                )
                
                self.logger.info(f"[{self.name}] Response created successfully")
                return response
                
            except Exception as e:
                self.logger.error(f"[{self.name}] LLM call failed: {e}")
                raise
        
        # Log LLM status
        if llm_client:
            self.logger.info("Claude Sonnet 4.5 LLM client initialized successfully")
        else:
            self.logger.info("Running in mock mode - no LLM client available")
    
    def mock_output(self, user_input: str) -> CommunicationResponse:
        """
        Generate a realistic mock output for testing.
        Overrides BaseAgent's mock_output method.
        """
        # Create a realistic mock response based on the input
        if "denied" in user_input.lower() or "exclusion" in user_input.lower() or "claim denied" in user_input.lower():
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
        elif "benefits" in user_input.lower() or "coverage" in user_input.lower() or "80%" in user_input.lower() or "deductible" in user_input.lower():
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
        elif "eligibility" in user_input.lower() or "active coverage" in user_input.lower() or "member" in user_input.lower():
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
        self.logger.info("=== COMMUNICATION AGENT ENHANCE_RESPONSE CALLED ===")
        start_time = time.time()
        
        try:
            self.logger.info(f"Processing communication request with {len(request.agent_outputs)} agent outputs")
            self.logger.info(f"Agent outputs: {[output.agent_id for output in request.agent_outputs]}")
            self.logger.info(f"User context: {request.user_context}")
            
            # Validate input
            self.logger.info("Step 1: Validating request")
            self._validate_request(request)
            self.logger.info("Request validation passed")
            
            # Prepare input for LLM
            self.logger.info("Step 2: Formatting agent outputs for LLM")
            formatted_input = self._format_agent_outputs(request)
            self.logger.info(f"Formatted input length: {len(formatted_input)} characters")
            
            # Call the agent (inherited from BaseAgent) with async timeout handling
            self.logger.info("Step 3: Calling LLM with async timeout handling")
            import asyncio
            import concurrent.futures
            import psutil
            import os
            
            # Use asyncio.run_in_executor for proper async handling
            loop = asyncio.get_event_loop()
            
            # Production environment detection and resource monitoring
            is_production = os.getenv("ENVIRONMENT", "").lower() in ["production", "prod"]
            if is_production:
                self.logger.info("=== PRODUCTION ENVIRONMENT DETECTED ===")
                # Log system resources for production debugging
                try:
                    memory_info = psutil.virtual_memory()
                    self.logger.info(f"Memory usage: {memory_info.percent}% ({memory_info.available / 1024 / 1024:.1f}MB available)")
                    cpu_percent = psutil.cpu_percent(interval=1)
                    self.logger.info(f"CPU usage: {cpu_percent}%")
                except Exception as e:
                    self.logger.warning(f"Could not get system metrics: {e}")
            else:
                self.logger.info("=== DEVELOPMENT ENVIRONMENT DETECTED ===")
            
            def llm_call():
                try:
                    self.logger.info("Executor started for Communication Agent LLM call")
                    # Make the actual LLM call
                    response = self(formatted_input, user_context=request.user_context)
                    self.logger.info("Executor completed Communication Agent LLM call successfully")
                    return response
                except Exception as e:
                    self.logger.error(f"Executor failed with exception: {e}")
                    raise
            
            # Run LLM call in thread pool with timeout and production-optimized settings
            try:
                self.logger.info("Starting LLM call with 60-second timeout")
                
                # Use a dedicated thread pool executor for better resource management
                with concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="comm_agent") as executor:
                    response = await asyncio.wait_for(
                        loop.run_in_executor(executor, llm_call),
                        timeout=60.0
                    )
                
                self.logger.info("=== CLAUDE API RESPONSE RECEIVED ===")
                self.logger.info(f"Response type: {type(response)}")
                self.logger.info(f"Response length: {len(str(response))}")
                self.logger.info("=== STARTING POST-PROCESSING ===")
            except asyncio.TimeoutError:
                self.logger.error("Communication Agent LLM call timed out after 60 seconds")
                # Add production-specific timeout handling
                self.logger.warning("Production timeout detected - this may indicate resource constraints")
                raise asyncio.TimeoutError("Communication Agent LLM call timed out after 60 seconds")
            except Exception as e:
                self.logger.error(f"Communication Agent LLM call failed: {e}")
                # Add production-specific error handling
                self.logger.warning(f"Production error detected: {type(e).__name__}")
                raise
            
            # Calculate processing time
            processing_time = time.time() - start_time
            self.logger.info(f"=== CALCULATING PROCESSING TIME ===")
            self.logger.info(f"Processing time: {processing_time:.2f}s")
            
            # Extract original sources
            original_sources = [output.agent_id for output in request.agent_outputs]
            self.logger.info(f"=== EXTRACTING ORIGINAL SOURCES ===")
            self.logger.info(f"Original sources: {original_sources}")
            
            # Create enhanced response
            self.logger.info("=== CREATING ENHANCED RESPONSE ===")
            enhanced_response = CommunicationResponse(
                enhanced_content=response.enhanced_content,
                original_sources=original_sources,
                processing_time=processing_time,
                metadata={
                    "config_used": self.config.to_dict(),
                    "input_agent_count": len(request.agent_outputs),
                    "user_context_provided": request.user_context is not None,
                    "llm_used": not self.mock,
                    "model_used": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022") if not self.mock else "mock"
                }
            )
            self.logger.info("=== ENHANCED RESPONSE CREATED ===")
            
            self.logger.info(f"Successfully enhanced response in {processing_time:.2f}s")
            return enhanced_response
            
        except asyncio.TimeoutError:
            processing_time = time.time() - start_time
            self.logger.error(f"Communication agent timed out after 30 seconds")
            
            if self.config.enable_fallback and self.config.fallback_to_original:
                return self._create_fallback_response(request, processing_time, "Communication agent timeout after 30 seconds")
            else:
                raise
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
            "llm_available": self.llm is not None,
            "claude_sonnet_ready": self.llm is not None
        }
