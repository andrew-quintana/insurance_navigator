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
    
    async def _call_llm_async(self, prompt: str, model: Optional[str] = None, max_tokens: int = 1000) -> str:
        """
        Call Claude API using async httpx with rate limiting.

        Args:
            prompt: The prompt to send
            model: Model override (defaults to configured model, usually Sonnet)
            max_tokens: Max response tokens
        """
        if self.mock or not hasattr(self, '_anthropic_api_key'):
            return "Mock response from unified navigator agent."

        # Rate limit the API call
        await self._anthropic_rate_limiter.acquire()

        use_model = model or self._anthropic_model

        try:
            if not hasattr(self, '_http_client') or self._http_client is None:
                self._http_client = httpx.AsyncClient(
                    timeout=60.0,
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": self._anthropic_api_key,
                        "anthropic-version": "2023-06-01"
                    }
                )

            response = await self._http_client.post(
                "https://api.anthropic.com/v1/messages",
                json={
                    "model": use_model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )

            if response.status_code != 200:
                raise Exception(f"Anthropic API error: {response.status_code}")

            result = response.json()
            return result["content"][0]["text"]

        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            return f"I apologize, but I'm having trouble processing your request right now. Error: {str(e)}"

    async def _call_haiku(self, prompt: str, max_tokens: int = 500) -> str:
        """Call Haiku for fast, cheap operations like routing."""
        return await self._call_llm_async(prompt, model="claude-haiku-4-5-20251001", max_tokens=max_tokens)

    async def _call_sonnet(self, prompt: str, max_tokens: int = 2000) -> str:
        """Call Sonnet for high-quality response generation."""
        return await self._call_llm_async(prompt, max_tokens=max_tokens)
    
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
    
    async def _context_gathering_agent(self, state: UnifiedNavigatorState, feedback: Optional[str] = None) -> UnifiedNavigatorState:
        """
        Context Gathering Agent (Haiku).

        Decides how to gather context for the user's question:
        - Select a tool (quick_info, rag_search, web_search, etc.) to retrieve context
        - Or provide a direct answer from LLM knowledge when no tool is needed

        Args:
            state: Current workflow state
            feedback: Optional feedback from the Response Agent requesting more context

        Returns:
            Updated state with tool selection (or direct LLM context)
        """
        start_time = time.time()

        try:
            self.workflow_logger.log_workflow_step(
                step="determining",
                message="Analyzing query and selecting context strategy",
                correlation_id=state.get("workflow_id")
            )

            # Check if input validation failed
            if state.get("input_safety") and not state["input_safety"].is_safe:
                state["tool_choice"] = ToolSelection(
                    selected_tool=ToolType.WEB_SEARCH,
                    reasoning="Input validation failed, using fallback",
                    confidence_score=0.3
                )
                return state

            try:
                selected_tool, reasoning, confidence = await self._context_agent_decide(state, feedback)
                self.logger.info(f"Context agent selected: {selected_tool} — {reasoning}")
            except Exception as e:
                self.logger.warning(f"Context agent primary failed: {e}, trying fallback")
                try:
                    selected_tool, reasoning, confidence = await self._fallback_routing_llm(state)
                    self.logger.info(f"Fallback router selected: {selected_tool} — {reasoning}")
                except Exception as fallback_err:
                    self.logger.warning(f"Fallback also failed: {fallback_err}, defaulting to quick_info")
                    selected_tool = ToolType.QUICK_INFO
                    reasoning = "Both routers failed, defaulting to quick_info"
                    confidence = 0.5

            if selected_tool is not None:
                state["tool_choice"] = ToolSelection(
                    selected_tool=selected_tool,
                    reasoning=reasoning,
                    confidence_score=confidence,
                    fallback_tool=ToolType.RAG_SEARCH if selected_tool != ToolType.RAG_SEARCH else ToolType.WEB_SEARCH
                )
            else:
                # no_tool — clear tool_choice so execute loop knows to skip retrieval
                state["tool_choice"] = None
            
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
    
    async def _execute_tool(self, state: UnifiedNavigatorState, tool_choice: ToolSelection, workflow_id: str):
        """Execute the selected tool and update state with results."""
        tool_status_map = {
            ToolType.QUICK_INFO: ("skimming", "Searching policy documents"),
            ToolType.RAG_SEARCH: ("thinking", "Deep searching your policy documents"),
            ToolType.WEB_SEARCH: ("thinking", "Searching current information"),
            ToolType.ACCESS_STRATEGY: ("thinking", "Developing comprehensive access strategy"),
            ToolType.COMBINED: ("thinking", "Performing comprehensive analysis"),
        }

        step, message = tool_status_map.get(
            tool_choice.selected_tool, ("thinking", "Gathering context")
        )
        self.workflow_logger.log_workflow_step(
            step=step, message=message, correlation_id=workflow_id
        )

        if tool_choice.selected_tool == ToolType.QUICK_INFO:
            state = await quick_info_node(state)
        elif tool_choice.selected_tool == ToolType.ACCESS_STRATEGY:
            state = await access_strategy_node(state)
        elif tool_choice.selected_tool == ToolType.WEB_SEARCH:
            state = await web_search_node(state)
        elif tool_choice.selected_tool == ToolType.RAG_SEARCH:
            state = await rag_search_node(state)
        elif tool_choice.selected_tool == ToolType.COMBINED:
            state = await combined_search_node(state)

    def _route_to_tool(self, state: UnifiedNavigatorState) -> str:
        """
        Routing function for tool selection (used by LangGraph workflow).

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
    
    def _build_context_string(self, state: UnifiedNavigatorState) -> str:
        """Build a context string from all tool results accumulated in state."""
        context_parts = []

        for tool_result in (state.get("tool_results") or []):
            if not tool_result.success:
                continue

            if tool_result.tool_type == ToolType.QUICK_INFO and tool_result.result:
                qi_result = tool_result.result
                if qi_result.relevant_sections:
                    context_parts.append("=== Policy Document Sections ===")
                    for i, section in enumerate(qi_result.relevant_sections[:5], 1):
                        context_parts.append(f"{i}. {section.get('content', '')[:300]}...")
                        if section.get('title'):
                            context_parts.append(f"   Section: {section.get('title')}")

            elif tool_result.tool_type == ToolType.WEB_SEARCH and tool_result.result:
                web_result = tool_result.result
                context_parts.append("=== Web Search Results ===")
                for i, result in enumerate(web_result.results[:3], 1):
                    context_parts.append(f"{i}. {result.get('title', '')}")
                    context_parts.append(f"   {result.get('description', '')[:200]}...")
                    context_parts.append(f"   Source: {result.get('url', '')}")

            elif tool_result.tool_type == ToolType.RAG_SEARCH and tool_result.result:
                rag_result = tool_result.result
                if rag_result.chunks:
                    context_parts.append("=== Your Policy Documents (Deep Search) ===")
                    for i, chunk in enumerate(rag_result.chunks[:3], 1):
                        context_parts.append(f"{i}. {chunk.get('content', '')[:300]}...")
                        if chunk.get('section_title'):
                            context_parts.append(f"   From: {chunk.get('section_title')}")

        # Include any direct LLM context from the context agent
        if state.get("llm_context"):
            context_parts.append("=== General Knowledge ===")
            context_parts.append(state["llm_context"])

        return "\n".join(context_parts)

    async def _response_determination_agent(self, state: UnifiedNavigatorState) -> tuple[bool, str, Optional[str]]:
        """
        Response Determination Agent (Sonnet).

        Evaluates gathered context and either:
        - Generates a final response if context is sufficient
        - Returns feedback requesting more context from the Context Gathering Agent

        Args:
            state: Current workflow state with accumulated tool results

        Returns:
            tuple of (is_sufficient, response_or_feedback, None)
            - If sufficient: (True, final_response, None)
            - If insufficient: (False, feedback_for_context_agent, None)
        """
        start_time = time.time()

        self.workflow_logger.log_workflow_step(
            step="wording",
            message="Evaluating gathered context",
            correlation_id=state.get("workflow_id")
        )

        context = self._build_context_string(state)

        doc_context = ""
        if state.get("has_user_documents"):
            doc_context = "\n- This user has uploaded their insurance policy document(s). When answering, reference information found in their documents rather than suggesting they check their plan separately."

        tools_used = [tr.tool_type.value for tr in (state.get("tool_results") or []) if tr.success]
        tools_summary = ", ".join(tools_used) if tools_used else "none"
        has_llm_context = bool(state.get("llm_context"))

        prompt = f"""You are an insurance navigation assistant. You have been given context gathered from various sources to answer the user's question.

User Question: {state["user_query"]}

Gathered Context:
{context if context else "(no context gathered)"}

Tools already used: {tools_summary}
{"Direct LLM knowledge was also provided." if has_llm_context else ""}

User Context:{doc_context if doc_context else " No policy documents uploaded."}

DECISION: First, decide if you have enough context to provide a helpful, accurate answer.

If YES — write your final response directly. Start your response with "RESPONSE:" followed by your answer.

If NO — you may request additional context. Start with "NEED_CONTEXT:" followed by a brief description of what additional information would help (e.g., "Need to search user's policy documents for specific deductible amounts" or "Need web search for current Medicare enrollment deadlines"). Only request more context if the current context is genuinely insufficient — do not request more just to be thorough.

Guidelines for your response:
1. Provide a clear, helpful response focused on insurance and healthcare navigation
2. Reference specific information from the context when available
3. If the user has uploaded documents, ground your answer in what was found in their documents
4. Stay professional and focused on insurance topics
5. Keep response concise but comprehensive
6. Do NOT provide medical diagnoses, treatment recommendations, or healthcare decisions"""

        # Time-based status messages during Sonnet generation
        timed_messages = [
            (5, "Writing response..."),
            (12, "Reviewing details..."),
            (20, "Polishing response..."),
            (30, "Almost done..."),
        ]
        workflow_id = state.get("workflow_id")

        async def _send_timed_updates():
            elapsed = 0
            msg_index = 0
            while msg_index < len(timed_messages):
                delay, msg = timed_messages[msg_index]
                wait = delay - elapsed
                if wait > 0:
                    await asyncio.sleep(wait)
                elapsed = delay
                self.workflow_logger.log_workflow_step(
                    step="wording",
                    message=msg,
                    correlation_id=workflow_id
                )
                msg_index += 1

        self.workflow_logger.log_workflow_step(
            step="wording",
            message="Generating personalized response",
            correlation_id=workflow_id
        )

        timer_task = asyncio.create_task(_send_timed_updates())
        try:
            response = await self._call_sonnet(prompt)
        finally:
            timer_task.cancel()
            try:
                await timer_task
            except asyncio.CancelledError:
                pass

        # Log LLM interaction
        prompt_tokens = len(prompt.split())
        response_tokens = len(response.split())
        total_tokens = prompt_tokens + response_tokens

        llm_interaction = LLMInteraction(
            model=self._anthropic_model if hasattr(self, '_anthropic_model') else "mock",
            prompt_tokens=prompt_tokens,
            completion_tokens=response_tokens,
            total_tokens=total_tokens,
            estimated_cost=total_tokens * 0.003 / 1000,
            processing_time_ms=(time.time() - start_time) * 1000
        )

        self.workflow_logger.log_llm_interaction(
            llm_interaction,
            context="response_determination"
        )

        processing_time = (time.time() - start_time) * 1000
        state["node_timings"]["response_agent"] = state.get("node_timings", {}).get("response_agent", 0) + processing_time

        # Parse the response
        response_stripped = response.strip()
        if response_stripped.startswith("NEED_CONTEXT:"):
            feedback = response_stripped[len("NEED_CONTEXT:"):].strip()
            self.logger.info(f"Response agent requests more context: {feedback}")
            return False, feedback, None
        else:
            # Strip "RESPONSE:" prefix if present
            final = response_stripped
            if final.startswith("RESPONSE:"):
                final = final[len("RESPONSE:"):].strip()
            self.logger.info(f"Response agent generated final response ({len(final)} chars)")
            return True, final, None
    
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
            
            # Use provided workflow ID or generate one for correlation
            import uuid
            workflow_id = input_data.workflow_id or str(uuid.uuid4())[:8]
            
            # Log workflow start
            self.workflow_logger.log_workflow_start(
                user_id=input_data.user_id,
                query=input_data.user_query,
                session_id=input_data.session_id,
                correlation_id=workflow_id
            )
            
            # Check if user has uploaded policy documents
            has_user_documents = False
            try:
                from agents.tooling.rag.database_manager import get_db_connection, release_db_connection
                conn = await get_db_connection()
                try:
                    schema = os.getenv("DATABASE_SCHEMA", "upload_pipeline")
                    row = await conn.fetchrow(
                        f"SELECT 1 FROM {schema}.documents WHERE user_id = $1 LIMIT 1",
                        input_data.user_id
                    )
                    has_user_documents = row is not None
                finally:
                    await release_db_connection(conn)
            except Exception as doc_check_err:
                self.logger.warning(f"Could not check user documents: {doc_check_err}")

            # Initialize workflow state
            state: UnifiedNavigatorState = {
                "user_query": input_data.user_query,
                "user_id": input_data.user_id,
                "session_id": input_data.session_id,
                "workflow_context": input_data.workflow_context,
                "workflow_id": workflow_id,
                "has_user_documents": has_user_documents,
                "llm_context": None,
                "node_timings": {},
                "processing_start_time": datetime.now(timezone.utc),
                "tool_results": [],
                "tool_choice": None,
                "input_safety": None,
                "final_response": None,
                "output_sanitation": None
            }

            # Step 1: Input guardrail
            self.workflow_logger.log_workflow_step(
                step="sanitizing",
                message="Validating and sanitizing input",
                correlation_id=workflow_id
            )
            state = await input_guardrail_node(state)

            # Step 2-3: Context Gathering Agent + Response Determination Agent loop
            max_iterations = 3
            feedback = None

            for iteration in range(max_iterations):
                # Context Gathering Agent (Haiku) — picks a tool or no_tool
                state = await self._context_gathering_agent(state, feedback=feedback)

                tool_choice = state.get("tool_choice")

                if tool_choice and tool_choice.selected_tool is not None:
                    # Execute the selected tool
                    await self._execute_tool(state, tool_choice, workflow_id)
                else:
                    # no_tool: context agent says LLM knowledge is sufficient
                    self.workflow_logger.log_workflow_step(
                        step="thinking",
                        message="Answering from general knowledge",
                        correlation_id=workflow_id
                    )
                    self.logger.info("Context agent chose no_tool, skipping retrieval")

                # Response Determination Agent (Sonnet) — evaluate and respond or request more
                is_sufficient, result, _ = await self._response_determination_agent(state)

                if is_sufficient:
                    state["final_response"] = result
                    break
                else:
                    # Response agent wants more context — loop back
                    feedback = result
                    self.workflow_logger.log_workflow_step(
                        step="determining",
                        message="Gathering additional context",
                        correlation_id=workflow_id
                    )
                    self.logger.info(f"Response agent iteration {iteration + 1}: requesting more context")
            else:
                # Exhausted iterations — use whatever we got on the last pass
                if not state.get("final_response"):
                    _, result, _ = await self._response_determination_agent(state)
                    state["final_response"] = result

            # Step 4: Output guardrail
            self.workflow_logger.log_workflow_step(
                step="wording",
                message="Finalizing response",
                correlation_id=workflow_id
            )
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
    
    def _parse_tool_selection_response(self, llm_response: str) -> tuple[ToolType, str, float]:
        """
        Parse an LLM response into a tool selection result.

        Tries JSON extraction first, then plain-text tool name detection.

        Args:
            llm_response: Raw text from the LLM

        Returns:
            tuple of (selected_tool, reasoning, confidence_score)
        """
        import json
        import re

        self.logger.debug(f"Raw LLM response: {llm_response}")

        response_data = None

        # Method 1: Extract JSON object from response
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        json_matches = re.findall(json_pattern, llm_response)

        for match in json_matches:
            try:
                response_data = json.loads(match)
                if 'tool' in response_data:
                    break
            except json.JSONDecodeError:
                continue

        # Method 2: Try parsing the entire response as JSON
        if not response_data:
            try:
                response_data = json.loads(llm_response.strip())
            except json.JSONDecodeError:
                pass

        # Method 3: Look for a tool name mentioned in plain text
        if not response_data:
            tool_names = ["quick_info", "web_search", "rag_search", "access_strategy", "combined"]
            llm_lower = llm_response.lower()
            for name in tool_names:
                if name in llm_lower:
                    response_data = {
                        "tool": name,
                        "reasoning": f"Extracted tool name from response text",
                        "confidence": 0.6
                    }
                    break

        if not response_data:
            raise ValueError(f"Could not extract tool selection from response: {llm_response}")

        tool_name = response_data.get("tool", "").lower()
        reasoning = response_data.get("reasoning", "LLM selection")
        confidence = float(response_data.get("confidence", 0.7))

        # no_tool is a special sentinel — we map it to None and handle in the caller
        if tool_name == "no_tool":
            self.logger.info(f"Context agent chose no_tool: {reasoning}")
            return None, reasoning, min(max(confidence, 0.0), 1.0)

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

    async def _context_agent_decide(self, state: UnifiedNavigatorState, feedback: Optional[str] = None) -> tuple[ToolType, str, float]:
        """
        Context Gathering Agent decision (Haiku).

        Decides which retrieval strategy to use, or whether the response agent
        can answer directly from its own knowledge without calling a tool.

        Args:
            state: Current workflow state
            feedback: Optional feedback from Response Agent requesting specific context

        Returns:
            tuple of (selected_tool, reasoning, confidence_score)
            Returns a special NO_TOOL sentinel when no retrieval is needed.
        """
        user_query = state["user_query"]
        has_docs = state.get("has_user_documents", False)

        doc_section = "- Insurance policy document(s): AVAILABLE" if has_docs else "- Insurance policy document(s): NOT AVAILABLE"

        feedback_section = ""
        if feedback:
            feedback_section = f"\n\nThe response agent reviewed the previously gathered context and determined it was insufficient. Their feedback:\n\"{feedback}\"\n\nSelect a DIFFERENT strategy to gather the missing context."

        prompt = f"""You are the context-gathering stage of an insurance navigation agent. Your job is to decide the best way to gather context for the user's question. You do NOT answer the question — a separate response agent will use whatever context you provide.

ROUTING POLICY:
- For general insurance questions (terminology, how insurance works, what a concept means): use quick_info. If the user has policy documents, their plan will be used as real-world examples.
- For questions specifically about the user's own plan (their deductible, their coverage, their benefits): use rag_search for deep semantic search of their uploaded documents.
- For questions about other insurance policies, carriers, or external healthcare topics not in the user's docs: use web_search.
- For strategic cost/benefit optimization questions: use access_strategy.
- For complex multi-source questions: use combined.
- If the question is simple enough that general LLM knowledge is sufficient (e.g., a basic greeting, a very simple definition, or a clarifying question), you may choose "no_tool" to skip retrieval entirely.

RETRIEVAL STRATEGIES:
1. quick_info — Fast keyword search over the user's documents.
2. rag_search — Deep semantic search over the user's uploaded documents.
3. web_search — Live internet search for external information.
4. access_strategy — Multi-source strategic analysis.
5. combined — Runs multiple strategies together.
6. no_tool — Skip retrieval. The response agent answers from its own knowledge.

DOCUMENTS AVAILABLE FOR THIS USER:
{doc_section}
{feedback_section}

USER QUERY: "{user_query}"

Respond with ONLY this JSON:
{{"tool": "tool_name", "reasoning": "brief explanation", "confidence": 0.85}}

Where tool_name is one of: quick_info, web_search, rag_search, access_strategy, combined, no_tool"""

        llm_response = await self._call_haiku(prompt)
        return self._parse_tool_selection_response(llm_response)

    async def _fallback_routing_llm(self, state: UnifiedNavigatorState) -> tuple[ToolType, str, float]:
        """
        Fallback routing LLM (Haiku) with step-by-step reasoning.

        Called when the primary context agent decision fails.

        Args:
            state: Current workflow state

        Returns:
            tuple of (selected_tool, reasoning, confidence_score)
        """
        user_query = state["user_query"]
        has_docs = state.get("has_user_documents", False)

        prompt = f"""You are a fallback context-routing agent. The primary router failed. Think step by step.

QUESTION: "{user_query}"

USER HAS UPLOADED POLICY DOCUMENTS: {"Yes" if has_docs else "No"}

STEP 1 — Is this a general insurance concept/terminology question?
  → choose "quick_info" (searches user's docs so their plan can be used as examples)

STEP 2 — Is this about the user's OWN plan specifics?
  → choose "rag_search"

STEP 3 — Is this about external topics (other carriers, regulations, medical facts)?
  → choose "web_search"

STEP 4 — Strategic cost/benefit planning?
  → choose "access_strategy"

STEP 5 — Multi-source needed?
  → choose "combined"

STEP 6 — Simple enough for LLM knowledge alone (greeting, trivial question)?
  → choose "no_tool"

DEFAULT — choose "quick_info"

Respond with ONLY this JSON:
{{"tool": "tool_name", "reasoning": "one sentence", "confidence": 0.7}}"""

        llm_response = await self._call_haiku(prompt)
        return self._parse_tool_selection_response(llm_response)
    
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