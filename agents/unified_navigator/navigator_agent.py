"""
Unified Navigator Agent.

This module implements the main unified agent that replaces the complex
multi-agent supervisor system. It extends BaseAgent and uses LangGraph
for workflow orchestration with guardrails and tool selection.
"""

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional, Callable
import httpx
from datetime import datetime, timezone

from langgraph.graph import StateGraph, END
from agents.base_agent import BaseAgent
from agents.shared.rate_limiting import get_anthropic_rate_limiter

from .models import (
    UnifiedNavigatorInput,
    UnifiedNavigatorOutput,
    UnifiedNavigatorState,
    ToolType,
    ToolSelection,
    InputSafetyResult,
    SafetyLevel,
    WorkflowStatus
)
from .guardrails.input_sanitizer import input_guardrail_node
from .guardrails.output_sanitizer import output_guardrail_node
from .tools.quick_info_tool import quick_info_node
from .tools.access_strategy_tool import access_strategy_node
from .tools.web_search import web_search_node
from .tools.rag_search import rag_search_node, combined_search_node
from .logging import get_workflow_logger, LLMInteraction


class UnifiedNavigatorAgent(BaseAgent):
    """
    Unified navigator agent extending BaseAgent with LangGraph workflow.
    
    Replaces the complex multi-agent supervisor system with a single agent
    that has guardrails and tool selection capabilities.
    """
    
    def __init__(self, use_mock: bool = False, **kwargs):
        """
        Initialize the unified navigator agent.
        
        Args:
            use_mock: If True, use mock responses for testing
            **kwargs: Additional arguments passed to BaseAgent
        """
        # Auto-detect LLM client if not provided
        llm_client = kwargs.get('llm')
        if llm_client is None and not use_mock:
            llm_client = self._get_claude_sonnet_llm()
            if llm_client:
                logging.info("Auto-detected Claude Sonnet LLM client for UnifiedNavigatorAgent")
            else:
                logging.info("No Claude Sonnet client available, using mock mode")
        
        super().__init__(
            name="unified_navigator",
            prompt="", # Workflow-based, no single prompt
            output_schema=UnifiedNavigatorOutput,
            llm=llm_client,
            mock=use_mock or llm_client is None,
            **kwargs
        )
        
        # Initialize workflow logger
        self.workflow_logger = get_workflow_logger()
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
    
    def _get_claude_sonnet_llm(self) -> Optional[Callable[[str], str]]:
        """
        Return an async callable for Claude Sonnet, or None for mock mode.
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
        rate_limiter = get_anthropic_rate_limiter()
        
        # Store for async use
        self._anthropic_api_key = api_key
        self._anthropic_model = model
        self._anthropic_rate_limiter = rate_limiter
        
        def call_llm_sync(prompt: str) -> str:
            """Synchronous wrapper - should not be called directly."""
            raise RuntimeError("Use async _call_llm_async method instead")
        
        return call_llm_sync
    
    async def _call_llm_async(self, prompt: str) -> str:
        """
        Call Claude Sonnet API using async httpx with rate limiting.
        """
        if self.mock or not hasattr(self, '_anthropic_api_key'):
            return "Mock response from unified navigator agent."
        
        # Rate limit the API call
        await self._anthropic_rate_limiter.acquire()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    json={
                        "model": self._anthropic_model,
                        "max_tokens": 1000,
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": self._anthropic_api_key,
                        "anthropic-version": "2023-06-01"
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Anthropic API error: {response.status_code}")
                
                result = response.json()
                return result["content"][0]["text"]
                    
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            return f"I apologize, but I'm having trouble processing your request right now. Error: {str(e)}"
    
    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow with nodes and routing logic.
        
        Returns:
            Compiled StateGraph for workflow execution
        """
        # Create state graph
        workflow = StateGraph(UnifiedNavigatorState)
        
        # Add nodes (avoid naming conflicts with state fields)
        workflow.add_node("input_guardrail", input_guardrail_node)
        workflow.add_node("tool_selector", self._tool_selection_node)
        workflow.add_node("quick_info", quick_info_node)
        workflow.add_node("access_strategy", access_strategy_node)
        workflow.add_node("web_search", web_search_node)
        workflow.add_node("rag_search", rag_search_node)
        workflow.add_node("combined_search", combined_search_node)
        workflow.add_node("response_generator", self._response_generation_node)
        workflow.add_node("output_guardrail", output_guardrail_node)
        
        # Set entry point and edges  
        workflow.set_entry_point("input_guardrail")
        workflow.add_edge("input_guardrail", "tool_selector")
        
        # Add conditional edges for tool routing
        workflow.add_conditional_edges(
            "tool_selector",
            self._route_to_tool,
            {
                "quick_info": "quick_info",
                "access_strategy": "access_strategy",
                "web_search": "web_search",
                "rag_search": "rag_search",
                "combined_search": "combined_search",
                "error": "response_generator"
            }
        )
        
        # All tools lead to response generation
        workflow.add_edge("quick_info", "response_generator")
        workflow.add_edge("access_strategy", "response_generator")
        workflow.add_edge("web_search", "response_generator")
        workflow.add_edge("rag_search", "response_generator")
        workflow.add_edge("combined_search", "response_generator")
        
        # Response generation leads to output guardrail
        workflow.add_edge("response_generator", "output_guardrail")
        
        # Output guardrail leads to end
        workflow.set_finish_point("output_guardrail")
        
        return workflow.compile(debug=False)
    
    async def _tool_selection_node(self, state: UnifiedNavigatorState) -> UnifiedNavigatorState:
        """
        LangGraph node for tool selection using heuristics.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with tool selection
        """
        start_time = time.time()
        
        try:
            # Log step start and update workflow status
            self.workflow_logger.log_workflow_step(
                step="determining",
                message="Analyzing query and selecting optimal tool",
                correlation_id=state.get("workflow_id")
            )
            
            # Check if input validation failed
            if state.get("input_safety") and not state["input_safety"].is_safe:
                state["tool_choice"] = ToolSelection(
                    selected_tool=ToolType.WEB_SEARCH,  # Default fallback
                    reasoning="Input validation failed, using fallback",
                    confidence_score=0.3
                )
                return state
            
            # Agent-driven tool selection using LLM
            user_query = state["user_query"]
            
            # TODO(human): Implement the tool selection prompt
            # Create a prompt that helps the LLM decide which tool to use based on:
            # - The user's query
            # - The tool_selection_examples showing when to use each tool
            # - Return the tool name (quick_info, web_search, rag_search, access_strategy, or combined)
            # and reasoning for the selection
            
            try:
                # Use LLM to determine best tool for the query
                selected_tool, reasoning, confidence = await self._select_tool_with_llm(user_query)
                
                self.logger.info(f"Agent selected tool: {selected_tool} with reasoning: {reasoning}")
                
            except Exception as e:
                self.logger.warning(f"LLM tool selection failed, using fallback logic: {e}")
                # Fallback to simple heuristic if LLM selection fails
                query_lower = user_query.lower()
                
                if any(word in query_lower for word in ["copay", "deductible", "premium", "what is", "coverage"]):
                    selected_tool = ToolType.QUICK_INFO
                    reasoning = "Fallback: Simple factual query"
                    confidence = 0.7
                elif any(word in query_lower for word in ["how to", "access", "find", "get"]):
                    selected_tool = ToolType.RAG_SEARCH
                    reasoning = "Fallback: Process/procedure query"
                    confidence = 0.7
                elif any(word in query_lower for word in ["latest", "2024", "2025", "current", "regulation"]):
                    selected_tool = ToolType.WEB_SEARCH
                    reasoning = "Fallback: Current information needed"
                    confidence = 0.7
                else:
                    selected_tool = ToolType.RAG_SEARCH
                    reasoning = "Fallback: Default to RAG search"
                    confidence = 0.6
            
            state["tool_choice"] = ToolSelection(
                selected_tool=selected_tool,
                reasoning=reasoning,
                confidence_score=confidence,
                fallback_tool=ToolType.RAG_SEARCH if selected_tool != ToolType.RAG_SEARCH else ToolType.WEB_SEARCH
            )
            
            processing_time = (time.time() - start_time) * 1000
            state["node_timings"]["tool_selector"] = processing_time
            
            self.logger.info(f"Tool selection: {selected_tool} (confidence: {confidence:.2f}) in {processing_time:.1f}ms")
            
            return state
            
        except Exception as e:
            self.logger.error(f"Tool selection error: {e}")
            # Default fallback
            state["tool_choice"] = ToolSelection(
                selected_tool=ToolType.RAG_SEARCH,
                reasoning=f"Tool selection failed: {str(e)}",
                confidence_score=0.5
            )
            return state
    
    def _route_to_tool(self, state: UnifiedNavigatorState) -> str:
        """
        Routing function for tool selection.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node name
        """
        if not state["tool_choice"]:
            return "error"
        
        tool_mapping = {
            ToolType.QUICK_INFO: "quick_info",
            ToolType.ACCESS_STRATEGY: "access_strategy", 
            ToolType.WEB_SEARCH: "web_search",
            ToolType.RAG_SEARCH: "rag_search",
            ToolType.COMBINED: "combined_search"
        }
        
        selected_route = tool_mapping.get(state["tool_choice"].selected_tool, "rag_search")  # Fallback to rag_search
        self.logger.info(f"Routing to: {selected_route} for tool: {state['tool_choice'].selected_tool}")
        return selected_route
    
    async def _response_generation_node(self, state: UnifiedNavigatorState) -> UnifiedNavigatorState:
        """
        LangGraph node for response generation using LLM.
        
        Args:
            state: Current workflow state with tool results
            
        Returns:
            Updated state with generated response
        """
        start_time = time.time()
        
        try:
            # Log step start
            self.workflow_logger.log_workflow_step(
                step="wording",
                message="Generating personalized response",
                correlation_id=state.get("workflow_id")
            )
            # Check if we have tool results
            if not state["tool_results"] or not any(result.success for result in state["tool_results"]):
                state["final_response"] = "I apologize, but I wasn't able to find relevant information for your query. Could you please rephrase your question or provide more details?"
                return state
            
            # Build context from tool results
            context_parts = []
            
            for tool_result in state["tool_results"]:
                if not tool_result.success:
                    continue
                
                if tool_result.tool_type == ToolType.WEB_SEARCH and tool_result.result:
                    web_result = tool_result.result
                    context_parts.append("=== Web Search Results ===")
                    for i, result in enumerate(web_result.results[:3], 1):  # Limit to top 3
                        context_parts.append(f"{i}. {result.get('title', '')}")
                        context_parts.append(f"   {result.get('description', '')[:200]}...")
                        context_parts.append(f"   Source: {result.get('url', '')}")
                
                elif tool_result.tool_type == ToolType.RAG_SEARCH and tool_result.result:
                    rag_result = tool_result.result
                    if rag_result.chunks:
                        context_parts.append("=== Your Documents ===")
                        for i, chunk in enumerate(rag_result.chunks[:3], 1):  # Limit to top 3
                            context_parts.append(f"{i}. {chunk.get('content', '')[:300]}...")
                            if chunk.get('section_title'):
                                context_parts.append(f"   From: {chunk.get('section_title')}")
            
            context = "\n".join(context_parts)
            
            # Generate response using LLM
            prompt = f"""You are an insurance navigation assistant. Based on the following information, provide a helpful, accurate response to the user's question.

User Question: {state["user_query"]}

Available Information:
{context}

Instructions:
1. Provide a clear, helpful response focused on insurance and healthcare
2. Reference specific information from the context when available
3. If information is limited, acknowledge this and suggest next steps
4. Stay professional and focused on insurance topics
5. Keep response concise but comprehensive

Response:"""

            response = await self._call_llm_async(prompt)
            
            # Log LLM interaction
            prompt_tokens = len(prompt.split())
            response_tokens = len(response.split())
            total_tokens = prompt_tokens + response_tokens
            
            llm_interaction = LLMInteraction(
                model=self._anthropic_model if hasattr(self, '_anthropic_model') else "mock",
                prompt_tokens=prompt_tokens,
                completion_tokens=response_tokens,
                total_tokens=total_tokens,
                estimated_cost=total_tokens * 0.003 / 1000,  # Rough estimate for Claude
                processing_time_ms=(time.time() - start_time) * 1000
            )
            
            self.workflow_logger.log_llm_interaction(
                llm_interaction,
                context="response_generation"
            )
            
            state["final_response"] = response
            
            processing_time = (time.time() - start_time) * 1000
            state["node_timings"]["response_generator"] = processing_time
            
            self.logger.info(f"Response generation completed in {processing_time:.1f}ms")
            
            return state
            
        except Exception as e:
            self.logger.error(f"Response generation error: {e}")
            state["final_response"] = "I apologize, but I encountered an error while generating a response. Please try rephrasing your question."
            return state
    
    async def execute(self, input_data: UnifiedNavigatorInput) -> UnifiedNavigatorOutput:
        """
        Execute the unified navigator workflow using direct orchestration.
        
        Args:
            input_data: Input data for the workflow
            
        Returns:
            UnifiedNavigatorOutput with results
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting unified navigator for user {input_data.user_id}")
            
            # Generate workflow ID for correlation
            import uuid
            workflow_id = str(uuid.uuid4())[:8]
            
            # Log workflow start
            self.workflow_logger.log_workflow_start(
                user_id=input_data.user_id,
                query=input_data.user_query,
                session_id=input_data.session_id,
                correlation_id=workflow_id
            )
            
            # Initialize workflow state
            state: UnifiedNavigatorState = {
                "user_query": input_data.user_query,
                "user_id": input_data.user_id,
                "session_id": input_data.session_id,
                "workflow_context": input_data.workflow_context,
                "workflow_id": workflow_id,
                "node_timings": {},
                "processing_start_time": datetime.now(timezone.utc),
                "tool_results": [],
                "tool_choice": None,
                "input_safety": None,
                "final_response": None,
                "output_sanitation": None
            }
            
            # Execute workflow steps directly (bypassing LangGraph due to version issue)
            # Step 1: Input guardrail
            self.workflow_logger.log_workflow_step(
                step="sanitizing",
                message="Validating and sanitizing input",
                correlation_id=workflow_id
            )
            from .guardrails.input_sanitizer import input_guardrail_node
            state = await input_guardrail_node(state)
            
            # Step 2: Tool selection
            state = await self._tool_selection_node(state)
            
            # Step 3: Route to appropriate tool
            tool_choice = state.get("tool_choice")
            if tool_choice:
                if tool_choice.selected_tool == ToolType.QUICK_INFO:
                    self.workflow_logger.log_workflow_step(
                        step="skimming",
                        message="Performing quick policy lookup",
                        correlation_id=workflow_id
                    )
                    from .tools.quick_info_tool import quick_info_node
                    state = await quick_info_node(state)
                elif tool_choice.selected_tool == ToolType.ACCESS_STRATEGY:
                    self.workflow_logger.log_workflow_step(
                        step="thinking",
                        message="Developing comprehensive access strategy",
                        correlation_id=workflow_id
                    )
                    from .tools.access_strategy_tool import access_strategy_node
                    state = await access_strategy_node(state)
                elif tool_choice.selected_tool == ToolType.WEB_SEARCH:
                    self.workflow_logger.log_workflow_step(
                        step="thinking",
                        message="Searching current information",
                        correlation_id=workflow_id
                    )
                    from .tools.web_search import web_search_node
                    state = await web_search_node(state)
                elif tool_choice.selected_tool == ToolType.RAG_SEARCH:
                    self.workflow_logger.log_workflow_step(
                        step="thinking",
                        message="Searching your policy documents",
                        correlation_id=workflow_id
                    )
                    from .tools.rag_search import rag_search_node
                    state = await rag_search_node(state)
                elif tool_choice.selected_tool == ToolType.COMBINED:
                    self.workflow_logger.log_workflow_step(
                        step="thinking",
                        message="Performing comprehensive analysis",
                        correlation_id=workflow_id
                    )
                    from .tools.rag_search import combined_search_node
                    state = await combined_search_node(state)
            
            # Step 4: Response generation
            state = await self._response_generation_node(state)
            
            # Step 5: Output guardrail
            self.workflow_logger.log_workflow_step(
                step="wording",
                message="Finalizing response",
                correlation_id=workflow_id
            )
            from .guardrails.output_sanitizer import output_guardrail_node
            state = await output_guardrail_node(state)
            
            # Calculate total processing time
            total_time = (time.time() - start_time) * 1000
            state["total_processing_time_ms"] = total_time
            
            # Log workflow completion
            self.workflow_logger.log_workflow_completion(
                user_id=input_data.user_id,
                success=bool(state["final_response"]),
                total_time_ms=total_time,
                correlation_id=workflow_id,
                context_data={
                    "tool_used": state["tool_choice"].selected_tool if state["tool_choice"] else "none",
                    "response_length": len(state["final_response"]) if state["final_response"] else 0,
                    "node_timings": state["node_timings"]
                }
            )
            
            # Create output
            output = self._create_output(state)
            
            self.logger.info(f"Unified navigator completed in {total_time:.1f}ms")
            return output
            
        except Exception as e:
            import traceback
            self.logger.error(f"Unified navigator execution failed: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            total_time = (time.time() - start_time) * 1000
            
            # Create error output
            return UnifiedNavigatorOutput(
                response="I apologize, but I encountered an error processing your request. Please try again.",
                success=False,
                tool_used=ToolType.RAG_SEARCH,  # Default
                input_safety_check=InputSafetyResult(
                    is_safe=True,
                    is_insurance_domain=True,
                    safety_level=SafetyLevel.UNCERTAIN,
                    confidence_score=0.5,
                    reasoning="Workflow execution failed"
                ),
                output_sanitized=False,
                total_processing_time_ms=total_time,
                error_message=str(e),
                user_id=input_data.user_id,
                session_id=input_data.session_id
            )
    
    async def _select_tool_with_llm(self, user_query: str) -> tuple[ToolType, str, float]:
        """
        Use LLM to intelligently select the best tool for the user query.
        
        Args:
            user_query: The user's question or request
            
        Returns:
            tuple of (selected_tool, reasoning, confidence_score)
        """
        # Build comprehensive tool selection prompt with examples
        prompt = f"""You are an AI assistant helping users with insurance questions. You need to select the best tool to answer their query.

AVAILABLE TOOLS:

1. quick_info: For straightforward factual questions about insurance terms, definitions, and basic policy information.
   Examples:
   - "What is a copay?"
   - "What is my deductible?"
   - "Am I covered for ambulances?"
   - "What does coinsurance mean?"
   - "What is the difference between HMO and PPO?"

2. web_search: For current information, regulations, or medical/procedural details unlikely to be in policy documents.
   Examples:
   - "What is a standard vs non-standard imaging procedure?"
   - "What is the difference between a CT scan and an MRI?"
   - "What are the latest healthcare regulations for 2024?"
   - "Current Medicare enrollment deadlines"

3. rag_search: For complex questions about accessing care, finding providers, or interpreting plan benefits that require reasoning through plan documents.
   Examples:
   - "How would I get access to mental health services?"
   - "How would I get a physical therapist?"
   - "What specialists can I see without a referral?"
   - "How do I appeal a denied claim?"

4. access_strategy: For strategic questions about maximizing benefits, optimizing healthcare costs, or planning care approaches.
   Examples:
   - "How can I minimize my out-of-pocket costs for surgery?"
   - "What's the best way to get coverage for this treatment?"
   - "How should I plan for ongoing therapy costs?"

5. combined: For complex, multi-faceted questions that need multiple types of information or analysis.
   Examples:
   - "I need surgery - what will it cost and how can I minimize expenses?"
   - "Compare my options for getting mental health care and find the most cost-effective approach"

USER QUERY: "{user_query}"

Select the single best tool for this query. Respond with ONLY this JSON format:
{{"tool": "tool_name", "reasoning": "brief explanation why this tool is best", "confidence": 0.85}}

Where tool_name is one of: quick_info, web_search, rag_search, access_strategy, combined"""

        try:
            # Get LLM response
            llm_response = await self._call_llm_async(prompt)
            
            # Parse JSON response
            import json
            import re
            
            self.logger.debug(f"Raw LLM response: {llm_response}")
            
            # Try multiple JSON extraction methods
            response_data = None
            
            # Method 1: Look for JSON in response
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            json_matches = re.findall(json_pattern, llm_response)
            
            for match in json_matches:
                try:
                    response_data = json.loads(match)
                    if 'tool' in response_data:  # Valid tool selection format
                        break
                except json.JSONDecodeError:
                    continue
            
            # Method 2: If no valid JSON found, try parsing the entire response as JSON
            if not response_data:
                try:
                    response_data = json.loads(llm_response.strip())
                except json.JSONDecodeError:
                    pass
            
            # Method 3: Look for tool name in plain text as fallback
            if not response_data:
                tool_keywords = {
                    'quick_info': ['quick', 'info', 'definition', 'basic'],
                    'web_search': ['web', 'search', 'current', 'latest'],
                    'rag_search': ['document', 'policy', 'plan', 'coverage'],
                    'access_strategy': ['strategy', 'minimize', 'optimize', 'best'],
                    'combined': ['complex', 'multi', 'multiple', 'both']
                }
                
                llm_response_lower = llm_response.lower()
                best_tool = None
                max_matches = 0
                
                for tool_name, keywords in tool_keywords.items():
                    matches = sum(1 for keyword in keywords if keyword in llm_response_lower)
                    if matches > max_matches:
                        max_matches = matches
                        best_tool = tool_name
                
                if best_tool:
                    response_data = {
                        "tool": best_tool,
                        "reasoning": f"Extracted from text analysis of: {llm_response[:100]}...",
                        "confidence": 0.6
                    }
                else:
                    raise ValueError(f"Could not extract tool selection from response: {llm_response}")
            
            # Extract values
            tool_name = response_data.get("tool", "").lower()
            reasoning = response_data.get("reasoning", "LLM selection")
            confidence = float(response_data.get("confidence", 0.7))
            
            # Convert tool name to ToolType enum
            tool_mapping = {
                "quick_info": ToolType.QUICK_INFO,
                "web_search": ToolType.WEB_SEARCH, 
                "rag_search": ToolType.RAG_SEARCH,
                "access_strategy": ToolType.ACCESS_STRATEGY,
                "combined": ToolType.COMBINED
            }
            
            selected_tool = tool_mapping.get(tool_name, ToolType.RAG_SEARCH)
            
            self.logger.info(f"LLM selected tool: {tool_name} -> {selected_tool} (confidence: {confidence})")
            self.logger.info(f"Reasoning: {reasoning}")
            
            return selected_tool, reasoning, min(max(confidence, 0.0), 1.0)
            
        except Exception as e:
            self.logger.warning(f"LLM tool selection failed: {e}, using fallback")
            
            # Smart fallback based on query analysis (useful for mock mode)
            query_lower = user_query.lower()
            
            # Combined patterns (check first for complex multi-part queries)
            if ((any(word in query_lower for word in ["compare", "options", "and find", "both"]) 
                 and len(query_lower.split()) > 12
                 and any(word in query_lower for word in ["cost", "minimize", "approach", "care"]))
                or ("surgery" in query_lower and "cost" in query_lower and "minimize" in query_lower)
                or ("what will it cost" in query_lower and any(word in query_lower for word in ["minimize", "expenses"]))):
                return ToolType.COMBINED, f"Fallback: Complex multi-part query detected", 0.6
                
            # Web search patterns (current info, comparisons, medical procedures) - check before quick_info
            elif any(word in query_lower for word in ["difference between", " vs ", "latest", "2024", "2025", "current", "regulation", "ct scan", "mri"]):
                return ToolType.WEB_SEARCH, f"Fallback: Current info query detected", 0.6
            
            # Quick info patterns (basic facts and definitions)
            elif any(word in query_lower for word in ["what is", "define", "meaning", "copay", "deductible", "premium", "coinsurance", "am i covered"]):
                return ToolType.QUICK_INFO, f"Fallback: Quick info query detected", 0.6
                
            # Access strategy patterns (optimization and strategy)
            elif any(word in query_lower for word in ["minimize", "maximize", "best way", "optimize", "strategy", "costs", "expenses"]):
                return ToolType.ACCESS_STRATEGY, f"Fallback: Strategy query detected", 0.6
                
            # RAG search patterns (accessing care, procedures, plan details)
            elif any(word in query_lower for word in ["how would i", "access", "get", "appeal", "specialists", "without referral"]):
                return ToolType.RAG_SEARCH, f"Fallback: Document/process query detected", 0.6
                
            # Default to RAG search
            else:
                return ToolType.RAG_SEARCH, f"Fallback: Default to document search", 0.5
    
    def _create_output(self, state: UnifiedNavigatorState) -> UnifiedNavigatorOutput:
        """
        Create output from final workflow state.
        
        Args:
            state: Final workflow state
            
        Returns:
            UnifiedNavigatorOutput
        """
        # Extract tool results
        web_search_results = None
        rag_search_results = None
        tool_used = ToolType.RAG_SEARCH  # Default
        
        if state["tool_results"]:
            for result in state["tool_results"]:
                if result.tool_type == ToolType.WEB_SEARCH and result.result:
                    web_search_results = result.result
                    tool_used = ToolType.WEB_SEARCH
                elif result.tool_type == ToolType.RAG_SEARCH and result.result:
                    rag_search_results = result.result
                    tool_used = ToolType.RAG_SEARCH
                elif result.tool_type == ToolType.COMBINED:
                    tool_used = ToolType.COMBINED
        
        # Extract tool used from tool selection if available
        if state["tool_choice"]:
            tool_used = state["tool_choice"].selected_tool
        
        return UnifiedNavigatorOutput(
            response=state["final_response"] or "I apologize, but I couldn't generate a response.",
            success=bool(state["final_response"] and not state.get("error_message")),
            web_search_results=web_search_results,
            rag_search_results=rag_search_results,
            tool_used=tool_used,
            input_safety_check=state.get("input_safety") or InputSafetyResult(
                is_safe=True,
                is_insurance_domain=True,
                safety_level=SafetyLevel.UNCERTAIN,
                confidence_score=0.5,
                reasoning="No safety check performed"
            ),
            output_sanitized=bool(state.get("output_sanitation") and state.get("output_sanitation").was_modified),
            total_processing_time_ms=state.get("total_processing_time_ms") or 0,
            error_message=state.get("error_message"),
            warnings=state.get("output_sanitation").warnings if state.get("output_sanitation") else [],
            session_id=state.get("session_id"),
            user_id=state.get("user_id"),
            workflow_id=state.get("workflow_id")
        )