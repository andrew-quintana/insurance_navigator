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
from pydantic import BaseModel
import json
from datetime import datetime
import logging
import traceback


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


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""
    agent: Union[AgentPrototype, str]  # Agent instance or name
    condition: Optional[Callable] = None  # Condition function for branching
    true_path: Optional['WorkflowStep'] = None  # Next step if condition is True
    false_path: Optional['WorkflowStep'] = None  # Next step if condition is False
    next_step: Optional['WorkflowStep'] = None  # Next step for sequential flow


class WorkflowPrototype:
    """Lightweight workflow engine for prototyping agent chains."""
    
    def __init__(self, name: str):
        self.name = name
        self.steps = []
        self.current_step = 0
        self.state = {}  # Workflow-wide state
        self.execution_log = []
        
    def add_agent(self, agent: Union[AgentPrototype, str], condition: Optional[Callable] = None):
        """Add an agent to the workflow sequence."""
        step = WorkflowStep(agent=agent, condition=condition)
        
        # Link to previous step
        if self.steps:
            self.steps[-1].next_step = step
        
        self.steps.append(step)
        agent_name = agent.name if hasattr(agent, 'name') else str(agent)
        print(f"➕ Added {agent_name} to workflow '{self.name}'")
        return step
    
    def add_conditional_branch(self, condition_func: Callable, true_agent: Union[AgentPrototype, str], false_agent: Union[AgentPrototype, str]):
        """Add a conditional branch to the workflow."""
        true_step = WorkflowStep(agent=true_agent)
        false_step = WorkflowStep(agent=false_agent)
        branch_step = WorkflowStep(agent=None, condition=condition_func, true_path=true_step, false_path=false_step)
        
        # Link to previous step
        if self.steps:
            self.steps[-1].next_step = branch_step
        
        self.steps.append(branch_step)
        print(f"🔀 Added conditional branch to workflow '{self.name}'")
        return branch_step
    
    def execute(self, input_data: Any, max_steps: int = 20) -> Dict[str, Any]:
        """Execute the workflow with the given input."""
        print(f"🚀 Executing workflow '{self.name}'")
        
        current_data = input_data
        current_step = self.steps[0] if self.steps else None
        step_count = 0
        
        while current_step and step_count < max_steps:
            step_count += 1
            
            # Handle conditional branching
            if current_step.condition:
                try:
                    condition_result = current_step.condition(current_data, self.state)
                    next_step = current_step.true_path if condition_result else current_step.false_path
                    
                    self.execution_log.append({
                        "step": step_count,
                        "type": "condition",
                        "condition_result": condition_result,
                        "next_path": "true" if condition_result else "false"
                    })
                    
                    current_step = next_step
                    continue
                    
                except Exception as e:
                    self.execution_log.append({
                        "step": step_count,
                        "type": "condition_error",
                        "error": str(e)
                    })
                    break
            
            # Execute agent step
            if current_step.agent:
                try:
                    # Handle both prototype and existing agents
                    if isinstance(current_step.agent, AgentPrototype):
                        result = current_step.agent.process(current_data)
                    elif isinstance(current_step.agent, str):
                        # This would need the existing agent tester passed in
                        result = {"error": "Existing agent testing requires ExistingAgentTester instance"}
                    else:
                        # Direct agent call
                        result = current_step.agent.process(current_data)
                    
                    self.execution_log.append({
                        "step": step_count,
                        "type": "agent_execution",
                        "agent": getattr(current_step.agent, 'name', str(current_step.agent)),
                        "result": result
                    })
                    
                    # Update current data for next step
                    if isinstance(result, dict) and 'result' in result:
                        current_data = result['result']
                    else:
                        current_data = result
                        
                except Exception as e:
                    self.execution_log.append({
                        "step": step_count,
                        "type": "agent_error",
                        "agent": getattr(current_step.agent, 'name', str(current_step.agent)),
                        "error": str(e)
                    })
                    break
            
            # Move to next step
            current_step = current_step.next_step
        
        return {
            "workflow": self.name,
            "final_result": current_data,
            "steps_executed": step_count,
            "execution_log": self.execution_log,
            "final_state": self.state
        }
    
    def visualize(self):
        """Show a text-based visualization of the workflow."""
        print(f"\n📋 Workflow: {self.name}")
        print("=" * 40)
        
        for i, step in enumerate(self.steps):
            if step.condition:
                print(f"{i+1}. [BRANCH] Condition check")
                if step.true_path:
                    true_agent = getattr(step.true_path.agent, 'name', str(step.true_path.agent))
                    print(f"   ✅ True  → {true_agent}")
                if step.false_path:
                    false_agent = getattr(step.false_path.agent, 'name', str(step.false_path.agent))
                    print(f"   ❌ False → {false_agent}")
            else:
                agent_name = getattr(step.agent, 'name', str(step.agent))
                print(f"{i+1}. [AGENT] {agent_name}")
            
            if i < len(self.steps) - 1:
                print("   ↓")
    
    def clear_state(self):
        """Clear workflow state and execution log."""
        self.state.clear()
        self.execution_log.clear()
        print(f"🧹 Cleared state for workflow '{self.name}'")


class PrototypingLab:
    """Central hub for all prototyping activities."""
    
    def __init__(self, discovery: AgentDiscovery, existing_tester: ExistingAgentTester):
        self.discovery = discovery
        self.existing_tester = existing_tester
        self.agents = {}
        self.workflows = {}
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
            print(f"⚠️ No prompts provided for '{name}', using defaults")
        
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
        
        # Show configuration info
        if final_system_prompt:
            print(f"   📋 System prompt: {final_system_prompt[:50]}...")
            print(f"   💬 User template: {final_prompt_template[:50]}...")
        else:
            print(f"   💬 Prompt template: {final_prompt_template[:50]}...")
            
        return agent
    
    def quick_workflow(self, name: str) -> WorkflowPrototype:
        """Quickly create and register a workflow."""
        workflow = WorkflowPrototype(name)
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
            print(f"   • {name} ({len(workflow.steps)} steps)")
        
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