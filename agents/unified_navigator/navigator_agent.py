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
        LangGraph node for tool selection using LLM-based routing.

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

            try:
                # Primary: LLM-based tool selection
                selected_tool, reasoning, confidence = await self._select_tool_with_llm(state)
                self.logger.info(f"Agent selected tool: {selected_tool} with reasoning: {reasoning}")

            except Exception as e:
                self.logger.warning(f"Primary tool selection failed: {e}, trying fallback router")
                try:
                    # Fallback: dedicated routing LLM with more context
                    selected_tool, reasoning, confidence = await self._fallback_routing_llm(state)
                    self.logger.info(f"Fallback router selected tool: {selected_tool} with reasoning: {reasoning}")
                except Exception as fallback_err:
                    self.logger.warning(f"Fallback router also failed: {fallback_err}, defaulting to rag_search")
                    selected_tool = ToolType.RAG_SEARCH
                    reasoning = "Both routers failed, defaulting to document search"
                    confidence = 0.5

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
                message="Preparing response",
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

            self.workflow_logger.log_workflow_step(
                step="wording",
                message="Generating personalized response",
                correlation_id=state.get("workflow_id")
            )

            # Generate response using LLM with time-based status updates
            # Add user document context to the prompt
            doc_context = ""
            if state.get("has_user_documents"):
                doc_context = "\n- This user has uploaded their insurance policy document(s). When answering, reference information found in their documents rather than suggesting they check their plan separately."

            prompt = f"""You are an insurance navigation assistant. Based on the following information, provide a helpful, accurate response to the user's question.

User Question: {state["user_query"]}

Available Information:
{context}

User Context:{doc_context if doc_context else " No policy documents uploaded."}

Instructions:
1. Provide a clear, helpful response focused on insurance and healthcare
2. Reference specific information from the context when available
3. If the user has uploaded documents, ground your answer in what was found in their documents
4. If information is limited, acknowledge this and suggest next steps
5. Stay professional and focused on insurance topics
6. Keep response concise but comprehensive

Response:"""

            # Time-based status messages during LLM generation
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

            timer_task = asyncio.create_task(_send_timed_updates())
            try:
                response = await self._call_llm_async(prompt)
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

    async def _select_tool_with_llm(self, state: UnifiedNavigatorState) -> tuple[ToolType, str, float]:
        """
        Use LLM to intelligently select the best tool for the user query.

        Args:
            state: Current workflow state (includes query, user context)

        Returns:
            tuple of (selected_tool, reasoning, confidence_score)
        """
        user_query = state["user_query"]
        has_docs = state.get("has_user_documents", False)

        # Build document availability context
        doc_lines = []
        if has_docs:
            doc_lines.append("- Insurance policy document(s): AVAILABLE — the user has uploaded their plan documents, which can be searched for plan-specific details like deductibles, copays, covered services, provider networks, and claims procedures.")
        else:
            doc_lines.append("- Insurance policy document(s): NOT AVAILABLE — the user has not uploaded any plan documents.")
        doc_section = "\n".join(doc_lines)

        prompt = f"""You are the context-gathering stage of an insurance navigation agent. Your job is to decide which retrieval strategy will produce the best context for the user's question. You do NOT answer the question yourself — a separate response generation step will synthesize the gathered context into a final answer.

Choose the single retrieval strategy that will surface the most relevant context for this question.

ROUTING POLICY:
- For general insurance questions (terminology, how insurance works, what a concept means): ALWAYS use quick_info first. If the user has policy documents, their plan will be used as real-world examples in the answer. This is the default for any insurance-related educational question.
- For questions specifically about the user's own plan (their deductible, their coverage, their benefits, what they personally are covered for): use rag_search to do a deep semantic search of their uploaded documents.
- For questions about OTHER insurance policies, plans, or carriers that the user does not have uploaded: use web_search.
- For general healthcare questions (not insurance-specific) that are unlikely to be answered by the user's policy documents: use web_search.
- For strategic planning questions about optimizing costs or navigating complex care situations: use access_strategy.
- For complex multi-part questions that clearly require multiple sources: use combined.

RETRIEVAL STRATEGIES:

1. quick_info — Fast keyword search over the user's documents. Use this as the default for general insurance questions. Even for generic concepts, this searches the user's own policy so the response can include real examples from their plan.

2. rag_search — Deep semantic search over the user's uploaded documents. Use this when the user is asking about their specific coverage, benefits, costs, or plan rules — questions whose answers live in their policy document.

3. web_search — Live internet search. Use this for questions about external topics: other insurance companies/plans, current regulations, medical procedure details, healthcare news, or factual information not found in any policy document.

4. access_strategy — Deep research combining web search and document retrieval with strategic analysis. Use this when the user needs help planning an approach across multiple factors — minimizing costs, comparing care options, or navigating a complex situation.

5. combined — Runs multiple retrieval strategies together. Use this ONLY when the question clearly requires context from multiple different sources that no single strategy can cover.

DOCUMENTS AVAILABLE FOR THIS USER:
{doc_section}

USER QUERY: "{user_query}"

Select the single best retrieval strategy. Respond with ONLY this JSON:
{{"tool": "tool_name", "reasoning": "brief explanation of what context this will gather", "confidence": 0.85}}

Where tool_name is one of: quick_info, web_search, rag_search, access_strategy, combined"""

        llm_response = await self._call_llm_async(prompt)
        return self._parse_tool_selection_response(llm_response)

    async def _fallback_routing_llm(self, state: UnifiedNavigatorState) -> tuple[ToolType, str, float]:
        """
        Fallback routing LLM with more context and a more deliberate prompt.

        Called when the primary tool selection fails. Uses a slower, more
        descriptive prompt to ensure correct routing.

        Args:
            state: Current workflow state

        Returns:
            tuple of (selected_tool, reasoning, confidence_score)
        """
        user_query = state["user_query"]
        has_docs = state.get("has_user_documents", False)

        prompt = f"""You are a fallback context-routing agent for an insurance navigation system. The primary router failed, so you must decide which retrieval strategy to use. Think step by step.

A separate response generation step will use whatever context you gather to write the final answer. Your job is only to pick the best source of context.

QUESTION: "{user_query}"

USER HAS UPLOADED POLICY DOCUMENTS: {"Yes" if has_docs else "No"}

STEP 1 — Is this a general question about insurance concepts, terminology, or how insurance works?
  → If yes: choose "quick_info". This searches the user's own documents so their plan can be used as examples, even for general questions.

STEP 2 — Is this specifically about the user's OWN plan (their deductible, their coverage, their benefits, how they can access a service under their plan)?
  → If yes: choose "rag_search" for deep semantic search of their policy documents.

STEP 3 — Is this about OTHER insurance policies/carriers, current regulations, medical procedures, or healthcare facts not found in any policy document?
  → If yes: choose "web_search" to gather external context.

STEP 4 — Is the user asking for strategic planning across multiple factors (cost optimization, care planning, benefit maximization)?
  → If yes: choose "access_strategy" to gather multi-source strategic context.

STEP 5 — Does this question clearly need context from multiple different sources combined?
  → If yes: choose "combined".

DEFAULT — If unclear: choose "quick_info".

Respond with ONLY this JSON:
{{"tool": "tool_name", "reasoning": "one sentence about what context this gathers", "confidence": 0.7}}"""

        llm_response = await self._call_llm_async(prompt)
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