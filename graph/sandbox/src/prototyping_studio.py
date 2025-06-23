"""
Insurance Navigator - Agent/Workflow Prototyping Studio
======================================================
Implementation classes for rapid agent and workflow prototyping.

This module provides:
• Auto-discovery of existing agents and model classes
• Lightweight agent creation with hot-swappable configurations  
• Local workflow design with conditional branching
• Session-only changes (no file modifications)
• Testing interfaces for existing agents
"""

import os
import sys
import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from pydantic import BaseModel, Field, field_validator
import json
from datetime import datetime
import logging
import traceback
import asyncio
from uuid import uuid4

# LangGraph imports
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages


class AgentDiscovery:
    """Automatically discover all agents and models in the project."""
    
    def __init__(self):
        self.agents = {}
        self.models = {}
        self.project_root = Path.cwd()
        self._setup_path()
        self.discover_all()
    
    def _setup_path(self):
        """Ensure project root is in Python path."""
        if str(self.project_root) not in sys.path:
            sys.path.insert(0, str(self.project_root))
    
    def discover_all(self):
        """Discover all agents and models."""
        print("🔍 Discovering agents and models...")
        self.discover_agents()
        self.discover_models()
        print(f"✅ Found {len(self.agents)} agents and {len(self.models)} model classes")
    
    def discover_agents(self):
        """Discover all existing agents."""
        try:
            # Import the main agents module
            import agents
            
            # Get all agent classes from the main __init__.py
            agent_classes = [
                'BaseAgent', 'PromptSecurityAgent', 'PatientNavigatorAgent',
                'TaskRequirementsAgent', 'ServiceAccessStrategyAgent', 
                'ChatCommunicatorAgent', 'RegulatoryAgent'
            ]
            
            for agent_name in agent_classes:
                if hasattr(agents, agent_name):
                    self.agents[agent_name] = getattr(agents, agent_name)
                    
        except Exception as e:
            print(f"⚠️ Error discovering agents: {e}")
    
    def discover_models(self):
        """Discover all model classes from agent directories."""
        model_files = [
            ('agents.chat_communicator.chat_models', ['ChatInput', 'ChatResponse', 'ConversationContext', 'CommunicationPreferences']),
            ('agents.patient_navigator.navigator_models', ['NavigatorOutput', 'MetaIntent', 'ClinicalContext', 'ServiceIntent', 'Metadata', 'BodyLocation']),
            ('agents.service_access_strategy.strategy_models', ['ServiceAccessStrategy', 'ServiceMatch', 'ActionStep']),
            ('agents.task_requirements.task_models', ['TaskProcessingResult', 'DocumentStatus', 'ReactStep']),
            ('agents.prompt_security.security_models', ['SecurityCheck'])
        ]
        
        for module_name, model_names in model_files:
            try:
                module = importlib.import_module(module_name)
                for model_name in model_names:
                    if hasattr(module, model_name):
                        self.models[model_name] = getattr(module, model_name)
            except Exception as e:
                print(f"⚠️ Could not import {module_name}: {e}")
    
    def create_models_namespace(self):
        """Create convenient namespace for all discovered models."""
        class Models:
            """Convenient namespace for all discovered models."""
            pass

        # Add all models to the Models class
        for name, model_class in self.models.items():
            setattr(Models, name, model_class)
        
        return Models


class AgentPrototype:
    """Lightweight agent for rapid prototyping without BaseAgent inheritance."""
    
    def __init__(self, name: str, prompt_template: str, model_params: Optional[Dict] = None, system_prompt: Optional[str] = None):
        self.name = name
        self.prompt_template = prompt_template
        self.system_prompt = system_prompt  # Separate system prompt
        self.model_params = model_params or {
            "model_name": "claude-3-haiku-20240307",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        self.memory = {}  # Local memory storage
        self.tools = []
        self.conversation_history = []
        
        # Import LangChain for LLM functionality
        try:
            from langchain_anthropic import ChatAnthropic
            # Convert model_params to proper LangChain parameters
            llm_params = self._prepare_llm_params(self.model_params)
            self.llm = ChatAnthropic(**llm_params)
            model_name = self.model_params.get('model_name', 'claude-3-haiku-20240307')
            print(f"✅ Created prototype agent '{name}' with {model_name}")
        except Exception as e:
            print(f"⚠️ Could not initialize LLM: {e}")
            self.llm = None
    
    def _prepare_llm_params(self, model_params: Dict) -> Dict:
        """Convert model_params to proper LangChain ChatAnthropic parameters."""
        llm_params = {}
        
        # Map common parameters to LangChain ChatAnthropic expected parameters
        param_mapping = {
            'model_name': 'model_name',
            'model': 'model_name',  # Support both for flexibility
            'temperature': 'temperature',
            'max_tokens': 'max_tokens',
            'api_key': 'anthropic_api_key'
        }
        
        for key, value in model_params.items():
            if key in param_mapping:
                langchain_key = param_mapping[key]
                llm_params[langchain_key] = value
        
        # Ensure model_name is set
        if 'model_name' not in llm_params:
            llm_params['model_name'] = 'claude-3-haiku-20240307'
        
        return llm_params
    
    def update_config(self, **kwargs):
        """Hot-swap any configuration (session-only)."""
        updated = []
        
        if 'prompt_template' in kwargs:
            self.prompt_template = kwargs['prompt_template']
            updated.append('prompt')
        
        if 'system_prompt' in kwargs:
            self.system_prompt = kwargs['system_prompt']
            updated.append('system_prompt')
        
        if 'model_params' in kwargs:
            self.model_params.update(kwargs['model_params'])
            # Reinitialize LLM with new params
            try:
                from langchain_anthropic import ChatAnthropic
                llm_params = self._prepare_llm_params(self.model_params)
                self.llm = ChatAnthropic(**llm_params)
                updated.append('model')
            except Exception as e:
                print(f"⚠️ Could not update LLM: {e}")
        
        if 'memory' in kwargs:
            self.memory.update(kwargs['memory'])
            updated.append('memory')
            
        print(f"🔄 Updated {', '.join(updated)} for agent '{self.name}'")
    
    def add_tool(self, tool_func: Callable, description: str):
        """Add a tool function to this agent."""
        self.tools.append({"func": tool_func, "description": description})
        print(f"🔧 Added tool '{tool_func.__name__}' to {self.name}")
    
    def process(self, input_data: Any, use_model: bool = True) -> Dict[str, Any]:
        """Process input data with optional model inference."""
        try:
            # Store in conversation history
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "input": str(input_data)[:200],  # Truncate for memory
                "type": "input"
            })
            
            if use_model and self.llm:
                # Use LLM for processing with system/user prompt structure
                if self.system_prompt:
                    # Use system + user prompt structure
                    from langchain_core.messages import SystemMessage, HumanMessage
                    
                    # Format the user prompt with input data
                    formatted_user_prompt = self.prompt_template.format(
                        input=input_data,
                        memory=json.dumps(self.memory, indent=2),
                        conversation_history=self.conversation_history[-5:]  # Last 5 interactions
                    )
                    
                    messages = [
                        SystemMessage(content=self.system_prompt),
                        HumanMessage(content=formatted_user_prompt)
                    ]
                    
                    response = self.llm.invoke(messages)
                else:
                    # Use single prompt template (legacy behavior)
                    formatted_prompt = self.prompt_template.format(
                        input=input_data,
                        memory=json.dumps(self.memory, indent=2),
                        conversation_history=self.conversation_history[-5:]  # Last 5 interactions
                    )
                    
                    response = self.llm.invoke(formatted_prompt)
                
                result = response.content if hasattr(response, 'content') else str(response)
            else:
                # Mock processing
                result = f"Mock response for '{input_data}' from {self.name}"
            
            # Store response
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "output": str(result)[:200],  # Truncate for memory
                "type": "output"
            })
            
            return {
                "agent": self.name,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "model_used": use_model and self.llm is not None
            }
            
        except Exception as e:
            error_result = {
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "model_used": False
            }
            print(f"❌ Error in {self.name}: {e}")
            return error_result
    
    def get_memory(self) -> Dict:
        """Get current memory state."""
        return self.memory.copy()
    
    def clear_memory(self):
        """Clear memory and conversation history."""
        self.memory.clear()
        self.conversation_history.clear()
        print(f"🧹 Cleared memory for {self.name}")
    
    def __repr__(self):
        system_info = " + system_prompt" if self.system_prompt else ""
        return f"AgentPrototype(name='{self.name}', tools={len(self.tools)}, memory_items={len(self.memory)}{system_info})"


class ExistingAgentTester:
    """Testing interface for existing agents with mock/real toggle."""
    
    def __init__(self, discovery: AgentDiscovery):
        self.discovery = discovery
        self.loaded_agents = {}
        self.agent_configs = {}
    
    def load_agent(self, agent_name: str, use_mock: bool = True, **kwargs):
        """Load an existing agent with mock/real toggle."""
        if agent_name not in self.discovery.agents:
            print(f"❌ Agent '{agent_name}' not found")
            return None
        
        try:
            agent_class = self.discovery.agents[agent_name]
            
            # Initialize with mock/real mode
            if agent_name == 'BaseAgent':
                print("⚠️ BaseAgent is abstract, skipping...")
                return None
            
            agent = agent_class(use_mock=use_mock, **kwargs)
            self.loaded_agents[agent_name] = agent
            self.agent_configs[agent_name] = {"use_mock": use_mock, **kwargs}
            
            mode = "mock" if use_mock else "real"
            print(f"✅ Loaded {agent_name} in {mode} mode")
            return agent
            
        except Exception as e:
            print(f"❌ Error loading {agent_name}: {e}")
            return None
    
    def toggle_mode(self, agent_name: str):
        """Toggle between mock and real mode for an agent."""
        if agent_name not in self.loaded_agents:
            print(f"❌ Agent '{agent_name}' not loaded")
            return
        
        current_config = self.agent_configs[agent_name]
        new_mock_mode = not current_config["use_mock"]
        
        # Reload agent with toggled mode
        other_kwargs = {k: v for k, v in current_config.items() if k != "use_mock"}
        self.load_agent(agent_name, use_mock=new_mock_mode, **other_kwargs)
    
    def test_agent(self, agent_name: str, test_input: Any) -> Dict[str, Any]:
        """Test an existing agent with input."""
        if agent_name not in self.loaded_agents:
            print(f"❌ Agent '{agent_name}' not loaded")
            return {}
        
        agent = self.loaded_agents[agent_name]
        
        try:
            # Different agents have different process methods
            if hasattr(agent, 'process') and callable(agent.process):
                if agent_name == 'PatientNavigatorAgent':
                    # Patient Navigator needs user_id and session_id
                    result = agent.process(test_input, "test_user", "test_session")
                elif agent_name == 'ChatCommunicatorAgent':
                    # Chat Communicator has async process methods
                    import asyncio
                    loop = asyncio.get_event_loop()
                    result = loop.run_until_complete(
                        agent.process_navigator_output(test_input, "test_user", "test_session")
                    )
                else:
                    # Standard process method
                    result = agent.process(test_input)
                
                return {
                    "agent": agent_name,
                    "success": True,
                    "result": result,
                    "mode": "mock" if self.agent_configs[agent_name]["use_mock"] else "real"
                }
            else:
                return {
                    "agent": agent_name,
                    "success": False,
                    "error": "No process method found"
                }
                
        except Exception as e:
            return {
                "agent": agent_name,
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def list_loaded_agents(self):
        """List all loaded agents and their modes."""
        if not self.loaded_agents:
            print("No agents loaded")
            return
        
        print("Loaded Agents:")
        for name, agent in self.loaded_agents.items():
            config = self.agent_configs[name]
            mode = "mock" if config["use_mock"] else "real"
            print(f"  • {name} ({mode} mode)")


class WorkflowPrototype:
    """LangGraph-based workflow engine matching agent_orchestrator.py patterns."""
    
    def __init__(self, name: str):
        self.name = name
        self.graph = StateGraph(dict)  # Exact match to agent_orchestrator.py
        self.nodes = {}  # Track nodes by name
        self.agents = {}  # Track agents by node name
        self.edges = {}  # Track edges between nodes
        self.entry_point = None
        self.compiled_workflow = None
        self.execution_log = []
        self.use_model = True  # Default to using real models
        
    def set_model_usage(self, use_model: bool):
        """Set whether to use real models or mock responses."""
        self.use_model = use_model
        mode = "real Claude models" if use_model else "mock responses"
        print(f"🔧 Workflow '{self.name}' set to use {mode}")
    
    def add_agent(self, agent: AgentPrototype, node_name: str) -> str:
        """Add an agent as a node using LangGraph patterns."""
        
        # Create async node function (exact match to agent_orchestrator.py)
        async def agent_node(state: dict) -> dict:
            """Async node function for LangGraph execution."""
            try:
                input_data = state.get("input", state.get("messages", ""))
                
                # Execute agent
                if hasattr(agent, 'aprocess'):
                    result = await agent.aprocess(input_data)
                else:
                    # Use sync process wrapped in async
                    result = agent.process(input_data, use_model=False)  # Mock mode for demo
                
                # Log execution with detailed intermediate information
                self.execution_log.append({
                    "type": "agent_execution",
                    "node": node_name,
                    "agent": agent.name,
                    "input": str(input_data)[:200],  # Log input to this step
                    "output": result.get('result', str(result))[:200] if isinstance(result, dict) else str(result)[:200],  # Log output
                    "full_result": result,  # Store full result for detailed inspection
                    "timestamp": datetime.now().isoformat(),
                    "success": True,
                    "step_number": len(self.execution_log)
                })
                
                # Update state (exact match to agent_orchestrator.py)
                return {
                    **state,
                    "messages": result.get('result', str(result)),
                    "last_agent": agent.name,
                    "last_node": node_name
                }
                
            except Exception as e:
                self.execution_log.append({
                    "type": "agent_error", 
                    "node": node_name,
                    "agent": agent.name,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                
                return {
                    **state,
                    "error": str(e),
                    "last_agent": agent.name,
                    "last_node": node_name
                }
        
        # Add node to graph (exact match to agent_orchestrator.py)
        self.graph.add_node(node_name, agent_node)
        self.nodes[node_name] = agent_node
        self.agents[node_name] = agent
        
        agent_name = agent.name if hasattr(agent, 'name') else str(agent)
        print(f"➕ Added {agent_name} to workflow '{self.name}'")
        return node_name
    
    def add_edge(self, from_node: str, to_node: str):
        """Add sequential edge between nodes (exact match to agent_orchestrator.py)."""
        self.graph.add_edge(from_node, to_node)
        # Track edges for execution flow
        if from_node not in self.edges:
            self.edges[from_node] = []
        self.edges[from_node].append(to_node)
        print(f"🔗 Added edge: {from_node} → {to_node}")
        return f"{from_node}->{to_node}"
    
    def add_conditional_edge(self, from_node: str, decision_function: Callable, edge_mapping: Dict[str, str]):
        """Add conditional edge with decision function (exact match to agent_orchestrator.py)."""
        self.graph.add_conditional_edges(from_node, decision_function, edge_mapping)
        print(f"🔀 Added conditional edge from {from_node}")
    
    def set_entry_point(self, node_name: str):
        """Set workflow entry point (exact match to agent_orchestrator.py)."""
        self.graph.set_entry_point(node_name)
        self.entry_point = node_name
        print(f"🚀 Set entry point: {node_name}")
    
    def compile(self):
        """Compile the LangGraph workflow (exact match to agent_orchestrator.py)."""
        try:
            self.compiled_workflow = self.graph.compile()
            print(f"✅ Compiled workflow '{self.name}' successfully")
            return self.compiled_workflow
        except Exception as e:
            print(f"❌ Error compiling workflow '{self.name}': {e}")
            return None
    
    async def aexecute(self, input_data: Any) -> Dict[str, Any]:
        """Execute workflow using LangGraph async patterns."""
        if not self.compiled_workflow:
            return {
                "success": False,
                "error": "Workflow not compiled",
                "workflow": self.name
            }
        
        try:
            # Prepare initial state (exact match to agent_orchestrator.py)
            initial_state = {
                "input": input_data,
                "messages": input_data,
                "workflow_id": str(uuid4()),
                "started_at": datetime.now().isoformat()
            }
            
            # Execute using LangGraph ainvoke (exact match to agent_orchestrator.py)
            result = await self.compiled_workflow.ainvoke(initial_state)
            
            return {
                "success": True,
                "final_result": result.get("messages", ""),
                "steps_executed": len(self.execution_log),
                "execution_log": self.execution_log.copy(),
                "final_state": result,
                "workflow": self.name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "steps_executed": len(self.execution_log),
                "execution_log": self.execution_log.copy(),
                "workflow": self.name
            }
    
    def execute(self, input_data: Any, use_model: bool = None) -> Dict[str, Any]:
        """Synchronous wrapper for async execution with model control."""
        if not self.compiled_workflow:
            return {
                "success": False,
                "error": "Workflow not compiled",
                "workflow": self.name
            }
        
        # Use workflow default if not specified
        if use_model is None:
            use_model = self.use_model
        
        try:
            # Clear previous execution log
            self.execution_log.clear()
            
            # For now, use a simplified mock execution until LangGraph is fully integrated
            # This ensures the demo works while we maintain the LangGraph interface
            
            print(f"🚀 Executing workflow '{self.name}' with {len(self.nodes)} nodes")
            
            current_data = input_data
            step_count = 0
            
            # Execute nodes in order based on entry point and edges
            if self.entry_point and self.entry_point in self.agents:
                current_node = self.entry_point
                
                while current_node and step_count < 10:  # Prevent infinite loops
                    step_count += 1
                    agent = self.agents[current_node]
                    
                    try:
                        # Execute agent
                        result = agent.process(current_data, use_model=use_model)
                        
                        # Log execution with detailed intermediate information
                        self.execution_log.append({
                            "type": "agent_execution",
                            "node": current_node,
                            "agent": agent.name,
                            "input": str(current_data)[:200],  # Log input to this step
                            "output": result.get('result', str(result))[:200] if isinstance(result, dict) else str(result)[:200],  # Log output
                            "full_result": result,  # Store full result for detailed inspection
                            "timestamp": datetime.now().isoformat(),
                            "success": True,
                            "step_number": step_count
                        })
                        
                        # Update data for next step
                        if isinstance(result, dict) and 'result' in result:
                            current_data = result['result']
                        else:
                            current_data = str(result)
                        
                        print(f"   ✓ Executed {current_node} ({agent.name})")
                        
                        # Find next node by following edges
                        if current_node in self.edges and self.edges[current_node]:
                            current_node = self.edges[current_node][0]  # Take first edge
                        else:
                            current_node = None  # End execution
                        
                    except Exception as e:
                        self.execution_log.append({
                            "type": "agent_error",
                            "node": current_node,
                            "agent": agent.name,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        })
                        break
            
            return {
                "success": True,
                "final_result": current_data,
                "steps_executed": step_count,
                "execution_log": self.execution_log.copy(),
                "workflow": self.name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error: {str(e)}",
                "workflow": self.name,
                "steps_executed": len(self.execution_log),
                "execution_log": self.execution_log.copy()
            }
    
    def visualize(self):
        """Show workflow structure."""
        print(f"\n📋 LangGraph Workflow: {self.name}")
        print("=" * 40)
        
        if not self.nodes:
            print("   (No nodes added)")
            return
        
        print(f"🚀 Entry Point: {self.entry_point or 'Not set'}")
        print(f"🔧 Compiled: {'Yes' if self.compiled_workflow else 'No'}")
        print(f"\n📊 Nodes ({len(self.nodes)}):")
        
        for node_name, agent in self.agents.items():
            agent_name = getattr(agent, 'name', 'Unknown')
            print(f"   • {node_name}: {agent_name}")
        
        if self.execution_log:
            print(f"\n📋 Recent Execution Log ({len(self.execution_log)} entries):")
            for entry in self.execution_log[-5:]:  # Show last 5
                if entry['type'] == 'agent_execution':
                    print(f"   ✓ {entry['node']} ({entry['agent']})")
                else:
                    print(f"   ✗ {entry['node']}: {entry.get('error', 'Unknown error')}")
    
    def clear_state(self):
        """Clear execution log."""
        self.execution_log.clear()
        print(f"🧹 Cleared execution log for workflow '{self.name}'")

    def get_intermediate_steps(self) -> List[Dict[str, Any]]:
        """Get detailed information about each intermediate step in the workflow execution."""
        return [log for log in self.execution_log if log['type'] == 'agent_execution']
    
    def show_step_details(self, step_number: int = None):
        """Show detailed information about a specific step or all steps."""
        intermediate_steps = self.get_intermediate_steps()
        
        if not intermediate_steps:
            print("No execution steps found. Run the workflow first.")
            return
        
        if step_number is not None:
            # Show specific step
            if 1 <= step_number <= len(intermediate_steps):
                step = intermediate_steps[step_number - 1]
                self._display_step_details(step, step_number)
            else:
                print(f"❌ Step {step_number} not found. Available steps: 1-{len(intermediate_steps)}")
        else:
            # Show all steps
            print(f"\n📋 Detailed Step Information ({len(intermediate_steps)} steps)")
            print("=" * 60)
            for i, step in enumerate(intermediate_steps, 1):
                self._display_step_details(step, i)
                if i < len(intermediate_steps):
                    print("   ↓")
    
    def _display_step_details(self, step: Dict[str, Any], step_number: int):
        """Display detailed information for a single step."""
        print(f"\n🔍 Step {step_number}: {step['node']} ({step['agent']})")
        print(f"   ⏰ Timestamp: {step['timestamp']}")
        print(f"   📥 Input: {step.get('input', 'No input logged')}")
        print(f"   📤 Output: {step.get('output', 'No output logged')}")
        
        # Show additional metadata if available
        full_result = step.get('full_result', {})
        if isinstance(full_result, dict):
            if 'model_used' in full_result:
                print(f"   🤖 Model used: {full_result['model_used']}")
            if 'timestamp' in full_result:
                print(f"   📊 Agent timestamp: {full_result['timestamp']}")
    
    def get_step_output(self, step_number: int) -> Any:
        """Get the output from a specific step."""
        intermediate_steps = self.get_intermediate_steps()
        if 1 <= step_number <= len(intermediate_steps):
            step = intermediate_steps[step_number - 1]
            return step.get('full_result', {}).get('result', step.get('output'))
        else:
            raise ValueError(f"Step {step_number} not found. Available steps: 1-{len(intermediate_steps)}")
    
    def get_step_input(self, step_number: int) -> Any:
        """Get the input to a specific step."""
        intermediate_steps = self.get_intermediate_steps()
        if 1 <= step_number <= len(intermediate_steps):
            step = intermediate_steps[step_number - 1]
            return step.get('input', 'No input logged')
        else:
            raise ValueError(f"Step {step_number} not found. Available steps: 1-{len(intermediate_steps)}")
    
    def export_execution_trace(self) -> Dict[str, Any]:
        """Export complete execution trace for analysis."""
        return {
            "workflow_name": self.name,
            "total_steps": len(self.get_intermediate_steps()),
            "nodes": list(self.nodes.keys()),
            "agents": {node: agent.name for node, agent in self.agents.items()},
            "edges": self.edges,
            "entry_point": self.entry_point,
            "execution_log": self.execution_log,
            "intermediate_steps": self.get_intermediate_steps(),
            "export_timestamp": datetime.now().isoformat()
        }


class PrototypingLab:
    """Central hub for all prototyping activities."""
    
    def __init__(self, discovery: AgentDiscovery, existing_tester: ExistingAgentTester):
        self.discovery = discovery
        self.existing_tester = existing_tester
        self.agents = {}
        self.workflows = {}
        self.execution_history = []
        self.created_agents = []  # Track agent names
        self.created_workflows = []  # Track workflow names
        self.test_results = []
    
    def quick_agent(self, name: str, prompt: str = None, system_prompt: str = None, user_prompt: str = None, **model_params) -> AgentPrototype:
        """Quickly create and register a prototype agent.
        
        Args:
            name: Agent name
            prompt: Legacy single prompt (for backward compatibility)  
            system_prompt: System prompt (instructions for the AI)
            user_prompt: User prompt template (should contain {input})
            **model_params: Model configuration parameters
            
        Usage examples:
            # Legacy style (backward compatible):
            agent = lab.quick_agent("test", "You are helpful. Respond to: {input}")
            
            # New system + user prompt style:
            agent = lab.quick_agent("test", 
                system_prompt="You are a helpful healthcare assistant.",
                user_prompt="Please help with: {input}")
                
            # Mixed style (system + legacy prompt):
            agent = lab.quick_agent("test", 
                prompt="Please help with: {input}",
                system_prompt="You are a helpful healthcare assistant.")
        """
        # Handle different prompt configurations
        if system_prompt and user_prompt:
            # New style: separate system and user prompts
            final_system_prompt = system_prompt
            final_prompt_template = user_prompt
        elif system_prompt and prompt:
            # Mixed style: system prompt + legacy prompt template
            final_system_prompt = system_prompt
            final_prompt_template = prompt
        elif prompt:
            # Legacy style: single prompt template
            final_system_prompt = None
            final_prompt_template = prompt
        elif user_prompt:
            # User prompt only (no system prompt)
            final_system_prompt = None
            final_prompt_template = user_prompt
        else:
            # Default template if nothing provided
            final_system_prompt = "You are a helpful AI assistant."
            final_prompt_template = "Please help with: {input}"
        
        # Ensure the prompt template has {input} placeholder
        if "{input}" not in final_prompt_template:
            print(f"⚠️ Warning: prompt template for '{name}' doesn't contain {{input}} placeholder")
        
        # Set default model parameters if none provided
        if not model_params:
            model_params = {
                "model_name": "claude-3-haiku-20240307",
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
        agent = AgentPrototype(name, final_prompt_template, model_params, final_system_prompt)
        self.agents[name] = agent
        
        # Track created agent
        if name not in self.created_agents:
            self.created_agents.append(name)
        
        # Show configuration info
        if final_system_prompt:
            print(f"   📋 System prompt: {final_system_prompt[:50]}...")
            print(f"   💬 User template: {final_prompt_template[:50]}...")
        else:
            print(f"   💬 Prompt template: {final_prompt_template[:50]}...")
            
        return agent
    
    def quick_workflow(self, name: str, use_model: bool = True) -> WorkflowPrototype:
        """Create a new workflow with LangGraph patterns."""
        workflow = WorkflowPrototype(name)
        workflow.set_model_usage(use_model)
        
        # Track created workflow
        if name not in self.created_workflows:
            self.created_workflows.append(name)
        
        # Store workflow
        self.workflows[name] = workflow
        return workflow
    
    def compare_agents(self, agent_names: List[str], test_inputs: List[Any]) -> Dict[str, Any]:
        """Compare multiple agents on the same inputs."""
        results = {}
        
        for agent_name in agent_names:
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                agent_results = []
                
                for test_input in test_inputs:
                    result = agent.process(test_input)
                    agent_results.append(result)
                
                results[agent_name] = agent_results
            elif agent_name in self.existing_tester.loaded_agents:
                agent_results = []
                
                for test_input in test_inputs:
                    result = self.existing_tester.test_agent(agent_name, test_input)
                    agent_results.append(result)
                
                results[agent_name] = agent_results
        
        return results
    
    def run_test_suite(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run a comprehensive test suite."""
        suite_results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(test_cases),
            "results": []
        }
        
        for i, test_case in enumerate(test_cases):
            print(f"Running test {i+1}/{len(test_cases)}: {test_case.get('name', 'Unnamed')}")
            
            test_result = {
                "test_name": test_case.get('name', f'Test_{i+1}'),
                "test_type": test_case.get('type', 'unknown'),
                "success": True,
                "details": {}
            }
            
            try:
                if test_case['type'] == 'agent':
                    agent_name = test_case['agent']
                    test_input = test_case['input']
                    
                    if agent_name in self.agents:
                        result = self.agents[agent_name].process(test_input)
                    else:
                        result = self.existing_tester.test_agent(agent_name, test_input)
                    
                    test_result['details'] = result
                    
                elif test_case['type'] == 'workflow':
                    workflow_name = test_case['workflow']
                    test_input = test_case['input']
                    
                    if workflow_name in self.workflows:
                        result = self.workflows[workflow_name].execute(test_input)
                        test_result['details'] = result
                    else:
                        test_result['success'] = False
                        test_result['details'] = {"error": f"Workflow '{workflow_name}' not found"}
                
            except Exception as e:
                test_result['success'] = False
                test_result['details'] = {"error": str(e)}
            
            suite_results['results'].append(test_result)
        
        self.test_results.append(suite_results)
        return suite_results
    
    def dashboard(self):
        """Show a quick dashboard of all prototypes."""
        print("\n🎛️ Prototyping Lab Dashboard")
        print("=" * 50)
        
        print(f"📦 Prototype Agents: {len(self.agents)}")
        for name, agent in self.agents.items():
            print(f"   • {name} (memory: {len(agent.memory)} items)")
        
        print(f"\n🔗 Workflows: {len(self.workflows)}")
        for name, workflow in self.workflows.items():
            print(f"   • {name} ({len(workflow.nodes)} nodes)" + (" - compiled" if getattr(workflow, 'compiled_workflow', False) else ""))
        
        print(f"\n🧪 Existing Agents Loaded: {len(self.existing_tester.loaded_agents)}")
        for name in self.existing_tester.loaded_agents.keys():
            mode = "mock" if self.existing_tester.agent_configs[name]["use_mock"] else "real"
            print(f"   • {name} ({mode})")
        
        print(f"\n📊 Test Suites Run: {len(self.test_results)}")


class ConfigPanel:
    """Interactive configuration panel for hot-swapping settings."""
    
    def __init__(self, lab: PrototypingLab):
        self.lab = lab
        self.active_configs = {}
    
    def edit_agent_prompt(self, agent_name: str, new_prompt: str = None, new_system_prompt: str = None):
        """Hot-swap an agent's prompt template and/or system prompt."""
        if agent_name in self.lab.agents:
            agent = self.lab.agents[agent_name]
            
            if new_prompt:
                old_prompt = agent.prompt_template
                agent.update_config(prompt_template=new_prompt)
                print(f"🔄 Updated user prompt for {agent_name}")
                print(f"   Old: {old_prompt[:50]}...")
                print(f"   New: {new_prompt[:50]}...")
            
            if new_system_prompt:
                old_system = agent.system_prompt or "None"
                agent.update_config(system_prompt=new_system_prompt)
                print(f"🔄 Updated system prompt for {agent_name}")
                print(f"   Old: {str(old_system)[:50]}...")
                print(f"   New: {new_system_prompt[:50]}...")
                
            if not new_prompt and not new_system_prompt:
                print(f"⚠️ No prompt updates provided for {agent_name}")
        else:
            print(f"❌ Agent '{agent_name}' not found in lab")

    def edit_system_prompt(self, agent_name: str, new_system_prompt: str):
        """Hot-swap an agent's system prompt specifically."""
        self.edit_agent_prompt(agent_name, new_system_prompt=new_system_prompt)

    def edit_user_prompt(self, agent_name: str, new_user_prompt: str):
        """Hot-swap an agent's user prompt template specifically."""
        self.edit_agent_prompt(agent_name, new_prompt=new_user_prompt)
    
    def edit_model_params(self, agent_name: str, **params):
        """Hot-swap model parameters."""
        if agent_name in self.lab.agents:
            agent = self.lab.agents[agent_name]
            agent.update_config(model_params=params)
        else:
            print(f"❌ Agent '{agent_name}' not found in lab")
    
    def edit_memory(self, agent_name: str, memory_updates: Dict):
        """Hot-swap agent memory."""
        if agent_name in self.lab.agents:
            agent = self.lab.agents[agent_name]
            agent.update_config(memory=memory_updates)
        else:
            print(f"❌ Agent '{agent_name}' not found in lab")
    
    def update_agent_config(self, agent_name: str, **config_updates):
        """Update multiple configuration aspects of an agent at once."""
        if agent_name not in self.lab.agents:
            print(f"❌ Agent '{agent_name}' not found in lab")
            return
        
        agent = self.lab.agents[agent_name]
        
        # Track what was updated
        updated_items = []
        
        # Handle system prompt update
        if 'system_prompt' in config_updates:
            old_system = agent.system_prompt or "None"
            agent.update_config(system_prompt=config_updates['system_prompt'])
            updated_items.append("system prompt")
            print(f"🔄 Updated system prompt for {agent_name}")
            print(f"   Old: {str(old_system)[:50]}...")
            print(f"   New: {config_updates['system_prompt'][:50]}...")
        
        # Handle user prompt template update
        if 'prompt' in config_updates or 'user_prompt' in config_updates:
            prompt_key = 'prompt' if 'prompt' in config_updates else 'user_prompt'
            old_prompt = agent.prompt_template
            agent.update_config(prompt_template=config_updates[prompt_key])
            updated_items.append("user prompt")
            print(f"🔄 Updated user prompt for {agent_name}")
            print(f"   Old: {old_prompt[:50]}...")
            print(f"   New: {config_updates[prompt_key][:50]}...")
        
        # Handle model parameters update
        model_params = {}
        for key in ['temperature', 'max_tokens', 'model_name', 'model']:
            if key in config_updates:
                model_params[key] = config_updates[key]
        
        if model_params:
            old_params = agent.model_params.copy()
            agent.update_config(model_params=model_params)
            updated_items.append("model parameters")
            print(f"🔄 Updated model parameters for {agent_name}")
            for key, value in model_params.items():
                old_val = old_params.get(key, 'Not set')
                print(f"   {key}: {old_val} → {value}")
        
        # Handle memory update
        if 'memory' in config_updates:
            agent.update_config(memory=config_updates['memory'])
            updated_items.append("memory")
            print(f"🔄 Updated memory for {agent_name}")
        
        if updated_items:
            print(f"✅ Updated {', '.join(updated_items)} for {agent_name}")
        else:
            print(f"⚠️ No valid configuration updates provided for {agent_name}")
    
    def show_current_config(self, agent_name: str):
        """Show current configuration for an agent."""
        if agent_name in self.lab.agents:
            agent = self.lab.agents[agent_name]
            print(f"\n⚙️ Current Config for {agent_name}:")
            print(f"   Model: {agent.model_params}")
            
            if agent.system_prompt:
                print(f"   System prompt: {agent.system_prompt[:100]}...")
                print(f"   User template: {agent.prompt_template[:100]}...")
            else:
                print(f"   Prompt template: {agent.prompt_template[:100]}...")
            
            print(f"   Memory items: {len(agent.memory)}")
            print(f"   Tools: {len(agent.tools)}")
            print(f"   Conversation history: {len(agent.conversation_history)}")
        else:
            print(f"❌ Agent '{agent_name}' not found in lab")


# Factory functions for convenience
def create_agent(name: str, prompt_template: str = None, system_prompt: str = None, user_prompt: str = None, **model_params) -> AgentPrototype:
    """Quick agent creation helper with system prompt support."""
    
    # Handle different prompt configurations
    if system_prompt and user_prompt:
        final_system_prompt = system_prompt
        final_prompt_template = user_prompt
    elif system_prompt and prompt_template:
        final_system_prompt = system_prompt
        final_prompt_template = prompt_template
    elif prompt_template:
        final_system_prompt = None
        final_prompt_template = prompt_template
    elif user_prompt:
        final_system_prompt = None
        final_prompt_template = user_prompt
    else:
        final_system_prompt = "You are a helpful AI assistant."
        final_prompt_template = "Please help with: {input}"
    
    # Set default model parameters if none provided
    if not model_params:
        model_params = {
            "model_name": "claude-3-haiku-20240307",
            "temperature": 0.7,
            "max_tokens": 1000
        }
    return AgentPrototype(name, final_prompt_template, model_params, final_system_prompt)


def create_workflow(name: str) -> WorkflowPrototype:
    """Quick workflow creation helper."""
    return WorkflowPrototype(name)


# Main initialization function
def initialize_prototyping_studio():
    """Initialize the complete prototyping studio."""
    print("🚀 Initializing Insurance Navigator - Agent/Workflow Prototyping Studio")
    print("=" * 70)
    
    # Initialize discovery
    discovery = AgentDiscovery()
    
    # Create models namespace
    Models = discovery.create_models_namespace()
    
    # Initialize existing agent tester
    existing_tester = ExistingAgentTester(discovery)
    
    # Initialize lab
    lab = PrototypingLab(discovery, existing_tester)
    
    # Initialize config panel
    config_panel = ConfigPanel(lab)
    
    print(f"\n📦 Available models: {', '.join(discovery.models.keys())}")
    print(f"🤖 Available agents: {', '.join(discovery.agents.keys())}")
    print("\n✅ Prototyping Studio ready!")
    
    return {
        'discovery': discovery,
        'Models': Models,
        'existing_tester': existing_tester,
        'lab': lab,
        'config_panel': config_panel
    }


# ==========================================
# JSON MODEL TESTING UTILITIES
# ==========================================

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Type
import json


class JSONModelUtilities:
    """Utility class for JSON model testing and validation."""
    
    @staticmethod
    def create_json_aware_agent(lab: PrototypingLab, name: str, input_schema: str, output_schema: str, 
                               specialist_type: str, temperature: float = 0.3, max_tokens: int = 400) -> AgentPrototype:
        """Create an agent that expects and produces specific JSON schemas."""
        system_prompt = f"""You are a {specialist_type} that processes {input_schema} JSON and produces {output_schema} JSON.
Always respond with valid JSON matching the {output_schema} schema.
Focus on providing structured, accurate data in the expected format."""
        
        return lab.quick_agent(
            name,
            system_prompt=system_prompt,
            prompt=f"Process this structured input: {{input}}",
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    @staticmethod
    def validate_json_output(output: str, expected_model: Type[BaseModel], agent_name: str = "Agent") -> Dict[str, Any]:
        """Validate JSON output against expected Pydantic model."""
        validation_result = {
            "is_valid": False,
            "model_name": expected_model.__name__,
            "agent_name": agent_name,
            "field_count": 0,
            "parsed_data": None,
            "error": None
        }
        
        try:
            if isinstance(output, str) and output.strip().startswith('{'):
                parsed_output = json.loads(output)
                
                # Validate against expected model schema
                validated_model = expected_model.model_validate(parsed_output)
                
                validation_result.update({
                    "is_valid": True,
                    "field_count": len(parsed_output.keys()),
                    "parsed_data": parsed_output
                })
                
            else:
                validation_result["error"] = "Non-JSON output detected"
                
        except json.JSONDecodeError as e:
            validation_result["error"] = f"Invalid JSON format: {e}"
        except Exception as e:
            validation_result["error"] = f"Schema validation failed: {e}"
        
        return validation_result
    
    @staticmethod
    def display_validation_result(validation_result: Dict[str, Any]):
        """Display JSON validation results in a formatted way."""
        agent_name = validation_result["agent_name"]
        model_name = validation_result["model_name"]
        
        if validation_result["is_valid"]:
            field_count = validation_result["field_count"]
            print(f"   ✅ Valid {model_name} JSON with {field_count} fields")
        else:
            error = validation_result["error"]
            print(f"   ❌ {agent_name}: {error}")
    
    @staticmethod
    def compare_json_structures(original_output: str, updated_output: str, comparison_name: str = "Comparison"):
        """Compare two JSON outputs and display differences."""
        try:
            if (original_output.strip().startswith('{') and updated_output.strip().startswith('{')):
                orig_json = json.loads(original_output)
                upd_json = json.loads(updated_output)
                
                print(f"\n📊 {comparison_name}:")
                print(f"   Original fields: {len(orig_json.keys())}")
                print(f"   Updated fields: {len(upd_json.keys())}")
                
                # Look for common array fields to compare lengths
                for key in orig_json.keys():
                    if key in upd_json and isinstance(orig_json[key], list) and isinstance(upd_json[key], list):
                        orig_len = len(orig_json[key])
                        upd_len = len(upd_json[key])
                        if orig_len != upd_len:
                            print(f"   {key}: {orig_len} → {upd_len} items")
                
        except Exception as e:
            print(f"⚠️  Could not compare JSON structures: {e}")


class MarkdownTemplateUtilities:
    """Utilities for inserting JSON data into markdown templates."""
    
    @staticmethod
    def insert_json_into_markdown(
        markdown_template: str, 
        json_data: Union[Dict, List, str, BaseModel], 
        placeholder: str = "examples",
        indent: int = 2,
        format_as_code_block: bool = True,
        code_block_language: str = "json"
    ) -> str:
        """
        Insert JSON data into a markdown template by replacing placeholders.
        
        Args:
            markdown_template: The markdown template with placeholders
            json_data: The JSON data to insert (dict, list, JSON string, or Pydantic model)
            placeholder: The placeholder name to look for (default: "examples")
            indent: Indentation for JSON formatting (default: 2)
            format_as_code_block: Whether to wrap JSON in code block (default: True)
            code_block_language: Language for code block syntax highlighting (default: "json")
            
        Returns:
            Markdown string with JSON data inserted
            
        Examples:
            # Basic usage
            template = "Here are some examples: {{examples}}"
            data = {"key": "value"}
            result = MarkdownTemplateUtilities.insert_json_into_markdown(template, data)
            
            # Custom placeholder
            template = "Input data: {{input}}"
            result = MarkdownTemplateUtilities.insert_json_into_markdown(
                template, data, placeholder="input"
            )
            
            # Multiple replacements
            template = "Examples: {{examples}} and Input: {{input}}"
            result = MarkdownTemplateUtilities.insert_json_into_markdown(
                template, {"examples": [1,2,3], "input": {"test": True}}
            )
        """
        try:
            # Convert input data to JSON string
            if isinstance(json_data, BaseModel):
                json_str = json_data.model_dump_json(indent=indent)
            elif isinstance(json_data, str):
                # Assume it's already JSON, validate and reformat
                parsed = json.loads(json_data)
                json_str = json.dumps(parsed, indent=indent)
            else:
                json_str = json.dumps(json_data, indent=indent)
            
            # Format as code block if requested
            if format_as_code_block:
                formatted_json = f"```{code_block_language}\n{json_str}\n```"
            else:
                formatted_json = json_str
            
            # Replace placeholders - support both {{placeholder}} and {placeholder} formats
            placeholder_patterns = [
                f"{{{{{placeholder}}}}}",  # {{placeholder}}
                f"{{{placeholder}}}",      # {placeholder}
            ]
            
            result = markdown_template
            for pattern in placeholder_patterns:
                result = result.replace(pattern, formatted_json)
            
            return result
            
        except Exception as e:
            print(f"❌ Error inserting JSON into markdown: {e}")
            return markdown_template
    
    @staticmethod
    def insert_data_into_template(
        template: str,
        data: Any,
        placeholder: str = "input",
        auto_detect_format: bool = True,
        force_json: bool = False,
        format_as_code_block: bool = None,
        code_block_language: str = None,
        indent: int = 2
    ) -> str:
        """
        Insert any type of data into a template, intelligently formatting based on data type.
        
        This is a more flexible version that handles various input types without forcing JSON.
        
        Args:
            template: The template with placeholders
            data: Any data to insert (string, number, dict, list, etc.)
            placeholder: The placeholder name to look for (default: "input")
            auto_detect_format: Whether to auto-detect formatting (default: True)
            force_json: Force JSON formatting even for simple types (default: False)
            format_as_code_block: Whether to wrap in code block (auto-detected if None)
            code_block_language: Language for syntax highlighting (auto-detected if None)
            indent: Indentation for structured data (default: 2)
            
        Returns:
            Template with data inserted
            
        Examples:
            # Simple string - no code block
            template = "User asked: {{input}}"
            result = insert_data_into_template(template, "What is the copay?")
            # Result: "User asked: What is the copay?"
            
            # Dictionary - JSON code block
            template = "Config: {{config}}"
            result = insert_data_into_template(template, {"temp": 0.1, "model": "claude"})
            # Result: "Config: ```json\n{\"temp\": 0.1, \"model\": \"claude\"}\n```"
            
            # Force simple formatting
            template = "Query: {{query}}"
            result = insert_data_into_template(template, {"q": "help"}, force_json=False)
            # Result: "Query: {'q': 'help'}"
        """
        try:
            # Handle different data types intelligently
            if auto_detect_format and not force_json:
                formatted_data = MarkdownTemplateUtilities._format_data_intelligently(
                    data, format_as_code_block, code_block_language, indent
                )
            else:
                # Force JSON formatting
                formatted_data = MarkdownTemplateUtilities._format_as_json(
                    data, format_as_code_block, code_block_language, indent
                )
            
            # Replace placeholders - support both {{placeholder}} and {placeholder} formats
            placeholder_patterns = [
                f"{{{{{placeholder}}}}}",  # {{placeholder}}
                f"{{{placeholder}}}",      # {placeholder}
            ]
            
            result = template
            for pattern in placeholder_patterns:
                result = result.replace(pattern, formatted_data)
            
            return result
            
        except Exception as e:
            print(f"❌ Error inserting data into template: {e}")
            return template
    
    @staticmethod
    def _format_data_intelligently(
        data: Any,
        format_as_code_block: bool = None,
        code_block_language: str = None,
        indent: int = 2
    ) -> str:
        """Intelligently format data based on its type."""
        
        # Simple string - return as-is (most common case)
        if isinstance(data, str):
            # Check if it's already JSON
            try:
                json.loads(data)
                # It's JSON string, format it properly
                return MarkdownTemplateUtilities._format_as_json(
                    data, format_as_code_block, code_block_language, indent
                )
            except (json.JSONDecodeError, TypeError):
                # Regular string, return as-is
                return data
        
        # Numbers - return as string
        elif isinstance(data, (int, float, bool)):
            return str(data)
        
        # None - return empty string
        elif data is None:
            return ""
        
        # Pydantic models - format as JSON
        elif isinstance(data, BaseModel):
            formatted_json = data.model_dump_json(indent=indent)
            code_block = format_as_code_block if format_as_code_block is not None else True
            language = code_block_language if code_block_language is not None else "json"
            
            if code_block:
                return f"```{language}\n{formatted_json}\n```"
            else:
                return formatted_json
        
        # Complex data (dict, list) - format as JSON with code block
        elif isinstance(data, (dict, list, tuple, set)):
            return MarkdownTemplateUtilities._format_as_json(
                data, 
                format_as_code_block if format_as_code_block is not None else True,
                code_block_language if code_block_language is not None else "json",
                indent
            )
        
        # Everything else - convert to string
        else:
            return str(data)
    
    @staticmethod
    def _format_as_json(
        data: Any,
        format_as_code_block: bool = None,
        code_block_language: str = None,
        indent: int = 2
    ) -> str:
        """Format data as JSON."""
        if isinstance(data, BaseModel):
            json_str = data.model_dump_json(indent=indent)
        elif isinstance(data, str):
            # Assume it's already JSON, validate and reformat
            parsed = json.loads(data)
            json_str = json.dumps(parsed, indent=indent)
        else:
            json_str = json.dumps(data, indent=indent)
        
        # Apply code block formatting
        code_block = format_as_code_block if format_as_code_block is not None else True
        language = code_block_language if code_block_language is not None else "json"
        
        if code_block:
            return f"```{language}\n{json_str}\n```"
        else:
            return json_str
    
    @staticmethod
    def insert_multiple_json_into_markdown(
        markdown_template: str,
        json_data_dict: Dict[str, Union[Dict, List, str, BaseModel]],
        indent: int = 2,
        format_as_code_block: bool = True,
        code_block_language: str = "json"
    ) -> str:
        """
        Insert multiple JSON data sets into a markdown template.
        
        Args:
            markdown_template: The markdown template with multiple placeholders
            json_data_dict: Dictionary mapping placeholder names to JSON data
            indent: Indentation for JSON formatting
            format_as_code_block: Whether to wrap JSON in code blocks
            code_block_language: Language for code block syntax highlighting
            
        Returns:
            Markdown string with all JSON data inserted
            
        Example:
            template = '''
            # Examples
            {{examples}}
            
            # Input Schema
            {{input}}
            
            # Expected Output
            {{output}}
            '''
            
            data = {
                "examples": [{"name": "John", "age": 30}],
                "input": {"user_query": "string"},
                "output": {"result": "string", "confidence": "float"}
            }
            
            result = MarkdownTemplateUtilities.insert_multiple_json_into_markdown(template, data)
        """
        result = markdown_template
        
        for placeholder, json_data in json_data_dict.items():
            result = MarkdownTemplateUtilities.insert_json_into_markdown(
                result, 
                json_data, 
                placeholder=placeholder,
                indent=indent,
                format_as_code_block=format_as_code_block,
                code_block_language=code_block_language
            )
        
        return result
    
    @staticmethod
    def create_prompt_with_examples(
        base_prompt: str,
        examples: List[Dict[str, Any]],
        examples_placeholder: str = "examples",
        format_examples: bool = True
    ) -> str:
        """
        Create a prompt template with examples inserted.
        
        Args:
            base_prompt: Base prompt template with examples placeholder
            examples: List of example dictionaries
            examples_placeholder: Placeholder name for examples
            format_examples: Whether to format examples nicely
            
        Returns:
            Complete prompt with examples inserted
            
        Example:
            prompt_template = '''
            You are a helpful assistant. Here are some examples:
            
            {{examples}}
            
            Please follow similar patterns in your response.
            '''
            
            examples = [
                {"input": "Hello", "output": "Hi there!"},
                {"input": "Goodbye", "output": "See you later!"}
            ]
            
            result = MarkdownTemplateUtilities.create_prompt_with_examples(
                prompt_template, examples
            )
        """
        if format_examples:
            # Format examples in a more readable way
            formatted_examples = []
            for i, example in enumerate(examples, 1):
                formatted_example = f"Example {i}:\n"
                for key, value in example.items():
                    if isinstance(value, (dict, list)):
                        value_str = json.dumps(value, indent=2)
                    else:
                        value_str = str(value)
                    formatted_example += f"{key.capitalize()}: {value_str}\n"
                formatted_examples.append(formatted_example)
            
            examples_text = "\n".join(formatted_examples)
        else:
            examples_text = json.dumps(examples, indent=2)
        
        return MarkdownTemplateUtilities.insert_json_into_markdown(
            base_prompt,
            examples_text,
            placeholder=examples_placeholder,
            format_as_code_block=False
        )
    
    @staticmethod
    def extract_placeholders(markdown_template: str) -> List[str]:
        """
        Extract all placeholder names from a markdown template.
        
        Args:
            markdown_template: The markdown template to analyze
            
        Returns:
            List of placeholder names found
            
        Example:
            template = "Here is {{examples}} and {{input}} data"
            placeholders = MarkdownTemplateUtilities.extract_placeholders(template)
            # Returns: ["examples", "input"]
        """
        import re
        
        # Find both {{placeholder}} and {placeholder} patterns
        patterns = [
            r'\{\{([^}]+)\}\}',  # {{placeholder}}
            r'\{([^}]+)\}',      # {placeholder} (but avoid double braces)
        ]
        
        placeholders = set()
        for pattern in patterns:
            matches = re.findall(pattern, markdown_template)
            for match in matches:
                # Skip if it's part of a double brace pattern
                if '{{' + match + '}}' not in markdown_template or pattern == patterns[0]:
                    placeholders.add(match.strip())
        
        return sorted(list(placeholders))
    
    @staticmethod
    def validate_template(
        markdown_template: str,
        required_placeholders: List[str],
        available_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate that a template has the required placeholders and data is available.
        
        Args:
            markdown_template: The template to validate
            required_placeholders: List of required placeholder names
            available_data: Dictionary of available data keys
            
        Returns:
            Validation result with details
            
        Example:
            template = "Examples: {{examples}} Input: {{input}}"
            required = ["examples", "input"]
            data = {"examples": [], "input": {}}
            
            result = MarkdownTemplateUtilities.validate_template(template, required, data)
        """
        found_placeholders = MarkdownTemplateUtilities.extract_placeholders(markdown_template)
        
        missing_placeholders = [p for p in required_placeholders if p not in found_placeholders]
        extra_placeholders = [p for p in found_placeholders if p not in required_placeholders]
        missing_data = [p for p in required_placeholders if p not in available_data]
        
        is_valid = len(missing_placeholders) == 0 and len(missing_data) == 0
        
        return {
            "is_valid": is_valid,
            "found_placeholders": found_placeholders,
            "missing_placeholders": missing_placeholders,
            "extra_placeholders": extra_placeholders,
            "missing_data": missing_data,
            "summary": f"Found {len(found_placeholders)} placeholders, {len(missing_placeholders)} missing, {len(missing_data)} without data"
        }


# Insurance-specific JSON Models for Testing

class PatientIntakeInput(BaseModel):
    """Structured input model for patient intake processing."""
    patient_id: Optional[str] = Field(default=None, description="Patient identifier")
    age: Optional[int] = Field(default=None, description="Patient age")
    medical_conditions: List[str] = Field(default_factory=list, description="Known medical conditions")
    insurance_status: str = Field(description="Current insurance status")
    medications: List[str] = Field(default_factory=list, description="Current medications")
    monthly_costs: Dict[str, float] = Field(default_factory=dict, description="Monthly healthcare costs")
    questions: List[str] = Field(default_factory=list, description="Patient questions/concerns")
    raw_text: str = Field(description="Original patient inquiry text")


class IntakeAnalysis(BaseModel):
    """Output model for intake processing step."""
    patient_summary: str = Field(description="Summary of patient situation")
    key_conditions: List[str] = Field(default_factory=list, description="Identified medical conditions")
    insurance_gaps: List[str] = Field(default_factory=list, description="Identified insurance gaps")
    priority_needs: List[str] = Field(default_factory=list, description="Priority healthcare needs")
    cost_concerns: Dict[str, float] = Field(default_factory=dict, description="Cost analysis")
    urgency_level: str = Field(description="Urgency assessment (low/medium/high)")


class CoverageAnalysis(BaseModel):
    """Output model for coverage analysis step."""
    recommended_plans: List[Dict[str, Any]] = Field(default_factory=list, description="Recommended insurance plans")
    coverage_options: Dict[str, Any] = Field(default_factory=dict, description="Coverage details")
    cost_comparison: Dict[str, float] = Field(default_factory=dict, description="Cost comparisons")
    provider_networks: List[str] = Field(default_factory=list, description="Provider network information")
    benefits_summary: List[str] = Field(default_factory=list, description="Key benefits")


class PatientGuidance(BaseModel):
    """Final output model for patient guidance."""
    action_plan: List[Dict[str, str]] = Field(default_factory=list, description="Step-by-step action plan")
    immediate_steps: List[str] = Field(default_factory=list, description="Immediate actions needed")
    resources: List[Dict[str, str]] = Field(default_factory=list, description="Helpful resources")
    timeline: Dict[str, str] = Field(default_factory=dict, description="Expected timelines")
    cost_savings_tips: List[str] = Field(default_factory=list, description="Ways to reduce costs")
    follow_up_actions: List[str] = Field(default_factory=list, description="Follow-up recommendations")


class MedicalCaseInput(BaseModel):
    """Input model for medical case analysis."""
    patient_condition: str = Field(description="Primary medical condition")
    treatment_needed: str = Field(description="Required medical treatment")
    insurance_issue: str = Field(description="Insurance-related problem")
    cost_concern: float = Field(description="Monthly cost if not covered")
    timeline_pressure: str = Field(description="Time constraints")
    prior_attempts: List[str] = Field(default_factory=list, description="Previous attempts at resolution")
    documentation_status: str = Field(description="Current documentation status")


class ClinicalAnalysis(BaseModel):
    """Output model for clinical specialist analysis."""
    medical_necessity_score: float = Field(description="Medical necessity rating (0-10)")
    clinical_justification: List[str] = Field(default_factory=list, description="Clinical justifications")
    diagnostic_codes: List[str] = Field(default_factory=list, description="Relevant diagnostic codes")
    treatment_alternatives: List[Dict[str, str]] = Field(default_factory=list, description="Alternative treatments")
    evidence_requirements: List[str] = Field(default_factory=list, description="Required evidence")
    specialist_recommendations: List[str] = Field(default_factory=list, description="Specialist recommendations")


class AdvocacyAnalysis(BaseModel):
    """Output model for patient advocacy analysis."""
    patient_rights: List[str] = Field(default_factory=list, description="Relevant patient rights")
    advocacy_strategies: List[Dict[str, str]] = Field(default_factory=list, description="Advocacy approaches")
    appeal_options: List[str] = Field(default_factory=list, description="Available appeal options")
    support_resources: List[Dict[str, str]] = Field(default_factory=list, description="Support resources")
    urgency_actions: List[str] = Field(default_factory=list, description="Immediate actions needed")
    emotional_support_notes: str = Field(description="Supportive messaging for patient")


class RegulatoryAnalysis(BaseModel):
    """Output model for regulatory specialist analysis."""
    applicable_regulations: List[Dict[str, str]] = Field(default_factory=list, description="Relevant regulations")
    compliance_requirements: List[str] = Field(default_factory=list, description="Compliance obligations")
    legal_remedies: List[str] = Field(default_factory=list, description="Available legal remedies")
    regulatory_citations: List[str] = Field(default_factory=list, description="Specific regulatory citations")
    enforcement_mechanisms: List[str] = Field(default_factory=list, description="Enforcement options")
    regulatory_timeline: Dict[str, str] = Field(default_factory=dict, description="Regulatory timelines")

class WorkflowPrescriptionOutput(BaseModel):
    """Output model for workflow prescription - requires a simple list of workflow names."""
    workflows: List[str] = Field(
        description="List of required workflows for the user request. Must be one or more of: 'information_retrieval', 'service_access_strategy', 'determine_eligibility', 'form_preparation'",
        examples=[
            ["information_retrieval"],
            ["service_access_strategy", "form_preparation"],
            ["determine_eligibility", "information_retrieval"]
        ],
        min_items=1,
        max_items=4
    )
    
    @field_validator('workflows')
    @classmethod
    def validate_workflows(cls, v):
        """Validate that all workflows are from the allowed set."""
        allowed_workflows = {
            'information_retrieval',
            'service_access_strategy', 
            'determine_eligibility',
            'form_preparation'
        }
        
        for workflow in v:
            if workflow not in allowed_workflows:
                raise ValueError(f"Invalid workflow '{workflow}'. Must be one of: {', '.join(allowed_workflows)}")
        
        return v
    
    @classmethod
    def from_list(cls, workflow_list: List[str]) -> 'WorkflowPrescriptionOutput':
        """Create WorkflowPrescriptionOutput from a simple list of workflows."""
        return cls(workflows=workflow_list)
    
    @classmethod
    def parse_output(cls, output: Union[str, List[str], Dict]) -> 'WorkflowPrescriptionOutput':
        """Parse various output formats into WorkflowPrescriptionOutput."""
        if isinstance(output, list):
            # Direct list format like ["information_retrieval"]
            return cls.from_list(output)
        elif isinstance(output, str):
            # Try to parse as JSON
            try:
                import json
                parsed = json.loads(output)
                if isinstance(parsed, list):
                    return cls.from_list(parsed)
                elif isinstance(parsed, dict) and 'workflows' in parsed:
                    return cls(**parsed)
                else:
                    raise ValueError("String output must be a JSON list or dict with 'workflows' key")
            except json.JSONDecodeError:
                raise ValueError("String output must be valid JSON")
        elif isinstance(output, dict):
            # Dictionary format
            return cls(**output)
        else:
            raise ValueError(f"Unsupported output format: {type(output)}")

# Convenience class for simpler parsing
class SimpleWorkflowOutput(BaseModel):
    """Ultra-simple workflow output that accepts just a list of strings."""
    workflows: List[str]
    
    def __init__(self, **data):
        if isinstance(data, list):
            # Handle direct list input
            super().__init__(workflows=data)
        elif len(data) == 1 and isinstance(list(data.values())[0], list):
            # Handle single key with list value
            super().__init__(workflows=list(data.values())[0])
        else:
            super().__init__(**data)


# Test Case Factories

class JSONTestCaseFactory:
    """Factory for creating test cases with structured JSON data."""
    
    @staticmethod
    def create_workflow_test_case() -> Dict[str, Any]:
        """Create a complete workflow test case with structured input."""
        patient_scenario = """I'm a 45-year-old with diabetes who recently lost my job and COBRA insurance. 
I need to find new coverage for my insulin and regular endocrinologist visits. 
I'm looking at marketplace plans but don't understand deductibles, copays, and if my current doctor is covered. 
My monthly insulin costs about $300 without insurance. What should I do?"""
        
        structured_input = PatientIntakeInput(
            age=45,
            medical_conditions=["diabetes"],
            insurance_status="recently_lost_cobra",
            medications=["insulin"],
            monthly_costs={"insulin": 300.0},
            questions=[
                "How do deductibles work?",
                "What are copays?", 
                "Is my current doctor covered?",
                "How to find affordable coverage?"
            ],
            raw_text=patient_scenario
        )
        
        return {
            "input": structured_input,
            "models": [IntakeAnalysis, CoverageAnalysis, PatientGuidance],
            "scenario_name": "Diabetes Insurance Loss"
        }
    
    @staticmethod
    def create_agent_comparison_test_case() -> Dict[str, Any]:
        """Create a test case for comparing different agent types."""
        lupus_case = MedicalCaseInput(
            patient_condition="Systemic Lupus Erythematosus (SLE)",
            treatment_needed="Benlysta (belimumab) infusions",
            insurance_issue="Prior authorization denied multiple times",
            cost_concern=5000.0,
            timeline_pressure="Appeal deadline in 5 days",
            prior_attempts=[
                "Initial prior auth request", 
                "First appeal with rheumatologist letter",
                "Second appeal with additional documentation"
            ],
            documentation_status="Extensive medical records and specialist recommendations available"
        )
        
        simple_case = MedicalCaseInput(
            patient_condition="Diabetes",
            treatment_needed="Insulin coverage",
            insurance_issue="High copay",
            cost_concern=200.0,
            timeline_pressure="None",
            prior_attempts=[],
            documentation_status="Basic documentation"
        )
        
        return {
            "complex_case": lupus_case,
            "simple_case": simple_case,
            "models": {
                "clinical": ClinicalAnalysis,
                "advocacy": AdvocacyAnalysis,
                "regulatory": RegulatoryAnalysis
            },
            "agent_configs": [
                ("clinical", 0.1, 500),
                ("advocacy", 0.7, 450),
                ("regulatory", 0.05, 600)
            ]
        }


# Convenience function to get all utilities
def get_json_utilities():
    """Get all JSON testing utilities in one convenient object."""
    return {
        'utils': JSONModelUtilities,
        'markdown_utils': MarkdownTemplateUtilities,
        'models': {
            'workflow': {
                'input': PatientIntakeInput,
                'steps': [IntakeAnalysis, CoverageAnalysis, PatientGuidance]
            },
            'agents': {
                'input': MedicalCaseInput,
                'outputs': {
                    'clinical': ClinicalAnalysis,
                    'advocacy': AdvocacyAnalysis,
                    'regulatory': RegulatoryAnalysis
                }
            }
        },
        'factory': JSONTestCaseFactory
    }


# Convenience function for notebook usage
def insert_json_into_markdown(
    markdown_template: str, 
    json_data: Union[Dict, List, str, BaseModel], 
    placeholder: str = "examples",
    **kwargs
) -> str:
    """
    Convenient function for inserting JSON into markdown templates in notebooks.
    
    Args:
        markdown_template: The markdown template with placeholders
        json_data: The JSON data to insert
        placeholder: The placeholder name to look for (default: "examples")
        **kwargs: Additional formatting options (indent, format_as_code_block, etc.)
        
    Returns:
        Markdown string with JSON data inserted
        
    Example:
        template = "Here are some examples: {{examples}}"
        data = {"key": "value"}
        result = insert_json_into_markdown(template, data)
        print(result)
    """
    return MarkdownTemplateUtilities.insert_json_into_markdown(
        markdown_template, json_data, placeholder, **kwargs
    )


# Input-agnostic convenience function  
def insert_data_into_template(
    template: str,
    data: Any,
    placeholder: str = "input",
    **kwargs
) -> str:
    """
    Input-agnostic function for inserting any data type into templates.
    
    This function intelligently handles strings, numbers, dicts, lists, etc.
    without forcing JSON formatting for simple types.
    
    Args:
        template: The template with placeholders
        data: Any data to insert (string, number, dict, list, etc.)
        placeholder: The placeholder name to look for (default: "input")
        **kwargs: Additional formatting options
        
    Returns:
        Template with data inserted
        
    Examples:
        # Simple string - no code block
        template = "User asked: {{input}}"
        result = insert_data_into_template(template, "What is the copay?")
        # Result: "User asked: What is the copay?"
        
        # Dictionary - JSON code block  
        template = "Config: {{config}}"
        result = insert_data_into_template(template, {"temp": 0.1})
        # Result: "Config: ```json\n{\"temp\": 0.1}\n```"
    """
    return MarkdownTemplateUtilities.insert_data_into_template(
        template, data, placeholder, **kwargs
    )


class EnhancedJSONModelUtilities:
    """Enhanced JSON utilities with better Pydantic integration and agent patterns."""
    
    @staticmethod
    def create_structured_agent(
        lab: PrototypingLab, 
        name: str,
        system_prompt: str,
        user_prompt_template: str,
        output_model: Type[BaseModel],
        temperature: float = 0.1,
        max_tokens: int = 300
    ) -> AgentPrototype:
        """
        Create an agent with structured output using custom prompts and Pydantic validation.
        Models the pattern used in /agents directory.
        """
        
        # Enhanced system prompt with JSON output instructions
        json_enhanced_system_prompt = f"""{system_prompt}

CRITICAL OUTPUT FORMAT REQUIREMENTS:
You must respond with valid JSON that matches this exact structure:
{output_model.model_json_schema()}

VALIDATION RULES:
- Always validate your JSON against the schema above
- Include all required fields
- Respect field constraints and descriptions
- Respond ONLY with the JSON object, no additional text

Example valid response:
{json.dumps(output_model.model_validate(output_model.model_construct()).model_dump(), indent=2)}
"""
        
        # Create the agent with enhanced prompt
        agent = lab.quick_agent(
            name,
            system_prompt=json_enhanced_system_prompt,
            prompt=user_prompt_template,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Add structured validation method
        def validate_and_process(self, input_data):
            """Process input and validate JSON output against Pydantic model."""
            try:
                # Get raw response
                response = self.process(input_data)
                raw_result = response.get('result', str(response))
                
                # Try to parse as JSON
                import json
                import re
                
                try:
                    json_data = json.loads(raw_result)
                except json.JSONDecodeError:
                    # Try to extract JSON from text response
                    json_match = re.search(r'\{.*\}', raw_result, re.DOTALL)
                    if json_match:
                        json_data = json.loads(json_match.group())
                    else:
                        # Try alternative extraction patterns
                        lines = raw_result.strip().split('\n')
                        for line in lines:
                            line = line.strip()
                            if line.startswith('{') and line.endswith('}'):
                                json_data = json.loads(line)
                                break
                        else:
                            raise ValueError("No valid JSON found in response")
                
                # Validate with Pydantic
                validated_output = output_model(**json_data)
                
                return {
                    'success': True,
                    'validated_output': validated_output,
                    'raw_response': raw_result,
                    'json_data': json_data,
                    **validated_output.model_dump()
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'raw_response': raw_result if 'raw_result' in locals() else 'No response',
                    'validation_error': True,
                    'error_type': type(e).__name__
                }
        
        # Bind the validation method to the agent instance
        import types
        agent.validate_and_process = types.MethodType(validate_and_process, agent)
        agent.output_model = output_model
        
        return agent
    
    @staticmethod
    def create_workflow_prescription_agent(
        lab: PrototypingLab,
        project_root: str,
        name: str = "workflow_prescription_agent",
        temperature: float = 0.1
    ) -> AgentPrototype:
        """
        Create a workflow prescription agent using the /agents pattern.
        Loads prompts from files and uses structured output.
        """
        
        # Load system prompt and examples
        try:
            with open(f"{project_root}/agents/workflow_prescription/prompt_system_workflow_prescription_v0_1.md") as f:
                system_prompt_template = f.read()
            
            with open(f"{project_root}/agents/workflow_prescription/examples_prompt_workflow_prescription_v0_1.md") as f:
                examples = f.read()
            
            with open(f"{project_root}/agents/workflow_prescription/prompt_human_workflow_prescription_v0_1.md") as f:
                user_prompt_template = f.read()
        except FileNotFoundError as e:
            print(f"Warning: Could not load prompt files: {e}")
            # Fallback to basic prompts
            system_prompt_template = """You are an expert triage agent for public healthcare access workflows.
Your task is to classify user requests into workflows: information_retrieval, service_access_strategy, determine_eligibility, form_preparation.

{examples}

Always output valid JSON with workflows and reasoning."""
            
            examples = """Example: "What is my deductible?" → ["information_retrieval"]
Example: "How do I apply for Medicaid?" → ["service_access_strategy"]"""
            
            user_prompt_template = "Classify this request: {input}"
        
        # Insert examples into system prompt
        system_prompt = MarkdownTemplateUtilities.insert_data_into_template(
            system_prompt_template,
            examples,
            placeholder="examples"
        )
        
        # Create structured agent
        agent = EnhancedJSONModelUtilities.create_structured_agent(
            lab=lab,
            name=name,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            output_model=WorkflowPrescriptionOutput,
            temperature=temperature
        )
        
        return agent
    
    @staticmethod
    def create_agent_from_directory(
        lab: PrototypingLab,
        agent_directory: str,
        agent_name: str,
        output_model: Type[BaseModel],
        temperature: float = 0.1,
        prompt_version: str = "v0_1"
    ) -> AgentPrototype:
        """
        Create an agent from an /agents directory structure.
        Follows the standard pattern of system prompt, examples, and user template.
        """
        
        # Load prompts following /agents pattern
        try:
            # Try different prompt file patterns
            prompt_files = [
                f"{agent_directory}/prompt_system_{agent_name}_{prompt_version}.md",
                f"{agent_directory}/prompts/prompt_{agent_name}_{prompt_version}.md",
                f"{agent_directory}/prompt_{agent_name}_{prompt_version}.md"
            ]
            
            system_prompt = None
            for prompt_file in prompt_files:
                try:
                    with open(prompt_file) as f:
                        system_prompt = f.read()
                        break
                except FileNotFoundError:
                    continue
            
            if not system_prompt:
                raise FileNotFoundError(f"No system prompt found in {agent_directory}")
            
            # Try to load examples
            example_files = [
                f"{agent_directory}/examples_prompt_{agent_name}_{prompt_version}.md",
                f"{agent_directory}/prompt_examples_{agent_name}_{prompt_version}.json",
                f"{agent_directory}/examples_{agent_name}_{prompt_version}.md"
            ]
            
            examples = ""
            for example_file in example_files:
                try:
                    with open(example_file) as f:
                        examples = f.read()
                        break
                except FileNotFoundError:
                    continue
            
            # Try to load user prompt template
            user_template_files = [
                f"{agent_directory}/prompt_human_{agent_name}_{prompt_version}.md",
                f"{agent_directory}/user_prompt_{agent_name}_{prompt_version}.md"
            ]
            
            user_template = "Process this input: {input}"
            for template_file in user_template_files:
                try:
                    with open(template_file) as f:
                        user_template = f.read()
                        break
                except FileNotFoundError:
                    continue
            
            # Insert examples if available
            if examples and "{examples}" in system_prompt:
                system_prompt = MarkdownTemplateUtilities.insert_data_into_template(
                    system_prompt,
                    examples,
                    placeholder="examples"
                )
            
            # Create structured agent
            agent = EnhancedJSONModelUtilities.create_structured_agent(
                lab=lab,
                name=f"{agent_name}_structured",
                system_prompt=system_prompt,
                user_prompt_template=user_template,
                output_model=output_model,
                temperature=temperature
            )
            
            return agent
            
        except Exception as e:
            raise ValueError(f"Failed to create agent from directory {agent_directory}: {e}")
    
    @staticmethod
    def batch_validate_outputs(
        agent: AgentPrototype,
        test_cases: List[str],
        expected_model: Type[BaseModel]
    ) -> Dict[str, Any]:
        """
        Batch validate agent outputs against expected model.
        Returns comprehensive validation report.
        """
        
        results = []
        successful_validations = 0
        
        for i, test_case in enumerate(test_cases):
            try:
                if hasattr(agent, 'validate_and_process'):
                    result = agent.validate_and_process(test_case)
                else:
                    # Fallback to manual validation
                    response = agent.process(test_case)
                    raw_result = response.get('result', str(response))
                    result = JSONModelUtilities.validate_json_output(
                        raw_result, expected_model, f"test_case_{i}"
                    )
                
                results.append({
                    'test_case': test_case,
                    'result': result,
                    'success': result.get('success', False)
                })
                
                if result.get('success', False):
                    successful_validations += 1
                    
            except Exception as e:
                results.append({
                    'test_case': test_case,
                    'result': {'success': False, 'error': str(e)},
                    'success': False
                })
        
        return {
            'total_tests': len(test_cases),
            'successful_validations': successful_validations,
            'success_rate': successful_validations / len(test_cases) if test_cases else 0,
            'results': results,
            'model_schema': expected_model.model_json_schema()
        }


class AgentPatternUtilities:
    """Utilities for following /agents directory patterns in prototyping."""
    
    @staticmethod
    def discover_agent_prompts(agents_directory: str) -> Dict[str, Dict[str, str]]:
        """
        Discover all prompt files in /agents directory structure.
        Returns organized mapping of agent -> prompt type -> file path.
        """
        import os
        import glob
        
        agent_prompts = {}
        
        # Look for agent directories
        for agent_dir in glob.glob(f"{agents_directory}/*/"):
            agent_name = os.path.basename(agent_dir.rstrip('/'))
            
            # Skip common directories
            if agent_name in ['common', '__pycache__']:
                continue
            
            agent_prompts[agent_name] = {}
            
            # Look for different types of prompt files
            prompt_patterns = {
                'system': ['prompt_system_*.md', 'prompt_*.md', 'prompts/prompt_*.md'],
                'examples': ['examples_*.md', 'prompt_examples_*.json', '*_examples.md'],
                'human': ['prompt_human_*.md', 'user_prompt_*.md'],
                'templates': ['prompts/templates/*.md']
            }
            
            for prompt_type, patterns in prompt_patterns.items():
                for pattern in patterns:
                    files = glob.glob(f"{agent_dir}/{pattern}")
                    if files:
                        agent_prompts[agent_name][prompt_type] = files
        
        return agent_prompts
    
    @staticmethod
    def create_agent_from_pattern(
        lab: PrototypingLab,
        agents_directory: str,
        agent_name: str,
        output_model: Type[BaseModel] = None,
        **kwargs
    ) -> AgentPrototype:
        """
        Create an agent following the discovered /agents pattern.
        """
        
        agent_prompts = AgentPatternUtilities.discover_agent_prompts(agents_directory)
        
        if agent_name not in agent_prompts:
            raise ValueError(f"Agent {agent_name} not found in {agents_directory}")
        
        prompts = agent_prompts[agent_name]
        
        # Load system prompt
        system_prompt = ""
        if 'system' in prompts and prompts['system']:
            with open(prompts['system'][0]) as f:
                system_prompt = f.read()
        
        # Load examples
        examples = ""
        if 'examples' in prompts and prompts['examples']:
            example_files = prompts['examples']
            for example_file in example_files:
                with open(example_file) as f:
                    examples = f.read()
        
        # Load user prompt template
        user_template = "Process this input: {input}"
        if 'human' in prompts and prompts['human']:
            with open(prompts['human'][0]) as f:
                user_template = f.read()
        
        # Insert examples if available
        if examples and "{examples}" in system_prompt:
            system_prompt = MarkdownTemplateUtilities.insert_data_into_template(
                system_prompt,
                examples,
                placeholder="examples"
            )
        
        # Create agent
        if output_model:
            agent = EnhancedJSONModelUtilities.create_structured_agent(
                lab=lab,
                name=f"{agent_name}_from_pattern",
                system_prompt=system_prompt,
                user_prompt_template=user_template,
                output_model=output_model,
                **kwargs
            )
        else:
            agent = lab.quick_agent(
                f"{agent_name}_from_pattern",
                system_prompt=system_prompt,
                prompt=user_template,
                **kwargs
            )
        
        return agent


def get_enhanced_json_utilities():
    """
    Get enhanced JSON utilities for structured agent creation.
    Returns utilities that follow /agents directory patterns.
    """
    return {
        'enhanced_utils': EnhancedJSONModelUtilities,
        'pattern_utils': AgentPatternUtilities,
        'models': {
            'WorkflowPrescriptionOutput': WorkflowPrescriptionOutput,
            # Add other models as needed
        },
        'markdown_utils': MarkdownTemplateUtilities,
        'create_workflow_prescription_agent': EnhancedJSONModelUtilities.create_workflow_prescription_agent,
        'create_structured_agent': EnhancedJSONModelUtilities.create_structured_agent,
        'create_agent_from_directory': EnhancedJSONModelUtilities.create_agent_from_directory,
        'discover_agent_prompts': AgentPatternUtilities.discover_agent_prompts
    } 