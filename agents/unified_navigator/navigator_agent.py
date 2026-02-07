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
from datetime import datetime

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
    SafetyLevel
)
from .guardrails.input_sanitizer import input_guardrail_node
from .guardrails.output_sanitizer import output_guardrail_node
from .tools.web_search import web_search_node
from .tools.rag_search import rag_search_node, combined_search_node


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
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
        
        # Tool selection weights for heuristic routing
        self.tool_weights = {
            "web_keywords": ["latest", "recent", "news", "current", "2024", "2025", "new", "update"],
            "rag_keywords": ["policy", "document", "coverage", "my", "specific", "plan"],
            "combined_keywords": ["compare", "options", "find", "search", "help"]
        }
    
    def _get_claude_sonnet_llm(self) -> Optional[Callable[[str], str]]:
        """
        Return an async callable for Claude Sonnet, or None for mock mode.
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
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
        
        async with self._anthropic_rate_limiter:
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
                            "Authorization": f"Bearer {self._anthropic_api_key}",
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
                "web_search": "web_search",
                "rag_search": "rag_search",
                "combined_search": "combined_search",
                "error": "response_generator"
            }
        )
        
        # All tools lead to response generation
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
            # Check if input validation failed
            if state.get("input_safety") and not state["input_safety"].is_safe:
                state["tool_choice"] = ToolSelection(
                    selected_tool=ToolType.WEB_SEARCH,  # Default fallback
                    reasoning="Input validation failed, using fallback",
                    confidence_score=0.3
                )
                return state
            
            # Fast heuristic-based tool selection
            query_lower = state["user_query"].lower()
            
            # Calculate scores for each tool type
            web_score = sum(1 for keyword in self.tool_weights["web_keywords"] if keyword in query_lower)
            rag_score = sum(1 for keyword in self.tool_weights["rag_keywords"] if keyword in query_lower)
            combined_score = sum(1 for keyword in self.tool_weights["combined_keywords"] if keyword in query_lower)
            
            # Query characteristics
            query_length = len(state["user_query"].split())
            has_personal_ref = any(word in query_lower for word in ["my", "i", "me", "personal"])
            
            # Decision logic
            if combined_score > 0 or query_length > 15:
                selected_tool = ToolType.COMBINED
                reasoning = "Complex query or comparison request - using both tools"
                confidence = 0.8
            elif rag_score > web_score and has_personal_ref:
                selected_tool = ToolType.RAG_SEARCH
                reasoning = "Personal/document-specific query - using RAG"
                confidence = 0.9
            elif web_score > 0:
                selected_tool = ToolType.WEB_SEARCH
                reasoning = "Current information request - using web search"
                confidence = 0.85
            else:
                # Default to RAG for insurance questions
                selected_tool = ToolType.RAG_SEARCH
                reasoning = "Default insurance query - using RAG"
                confidence = 0.7
            
            state["tool_choice"] = ToolSelection(
                selected_tool=selected_tool,
                reasoning=reasoning,
                confidence_score=confidence,
                fallback_tool=ToolType.RAG_SEARCH if selected_tool != ToolType.RAG_SEARCH else ToolType.WEB_SEARCH
            )
            
            processing_time = (time.time() - start_time) * 1000
            state.node_timings["tool_selector"] = processing_time
            
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
            ToolType.WEB_SEARCH: "web_search",
            ToolType.RAG_SEARCH: "rag_search",
            ToolType.COMBINED: "combined_search"
        }
        
        return tool_mapping.get(state["tool_choice"].selected_tool, "error")
    
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
            
            state["final_response"] = response
            
            processing_time = (time.time() - start_time) * 1000
            state.node_timings["response_generator"] = processing_time
            
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
            
            # Initialize workflow state
            state: UnifiedNavigatorState = {
                "user_query": input_data.user_query,
                "user_id": input_data.user_id,
                "session_id": input_data.session_id,
                "workflow_context": input_data.workflow_context,
                "node_timings": {},
                "processing_start_time": datetime.utcnow(),
                "tool_results": [],
                "tool_choice": None,
                "input_safety": None,
                "final_response": None,
                "output_sanitation": None
            }
            
            # Execute workflow steps directly (bypassing LangGraph due to version issue)
            # Step 1: Input guardrail
            from .guardrails.input_sanitizer import input_guardrail_node
            state = await input_guardrail_node(state)
            
            # Step 2: Tool selection
            state = await self._tool_selection_node(state)
            
            # Step 3: Route to appropriate tool
            tool_choice = state.get("tool_choice")
            if tool_choice:
                if tool_choice.selected_tool == ToolType.WEB_SEARCH:
                    from .tools.web_search import web_search_node
                    state = await web_search_node(state)
                elif tool_choice.selected_tool == ToolType.RAG_SEARCH:
                    from .tools.rag_search import rag_search_node
                    state = await rag_search_node(state)
                elif tool_choice.selected_tool == ToolType.COMBINED:
                    from .tools.rag_search import combined_search_node
                    state = await combined_search_node(state)
            
            # Step 4: Response generation
            state = await self._response_generation_node(state)
            
            # Step 5: Output guardrail
            from .guardrails.output_sanitizer import output_guardrail_node
            state = await output_guardrail_node(state)
            
            # Calculate total processing time
            total_time = (time.time() - start_time) * 1000
            state["total_processing_time_ms"] = total_time
            
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
            user_id=state.get("user_id")
        )