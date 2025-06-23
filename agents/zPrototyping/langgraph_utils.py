"""
LangGraph Utilities for Agent Development

This module provides essential utilities for building and prototyping agents with LangGraph:
1. Prompt composition and validation helpers
2. Structured agent input/output validation
3. Dynamic agent discovery and loading
4. Workflow construction and chaining helpers

Author: AI Assistant
Created for: Insurance Navigator Project
"""

import os
import re
import json
import logging
import inspect
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable, Type, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

# Core dependencies
from pydantic import BaseModel, ValidationError, Field
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.message import add_messages
    from langgraph.prebuilt import ToolNode
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("Warning: LangGraph not available. Some functionality will be limited.")

# Add LangChain message imports
try:
    from langchain_core.messages import SystemMessage, HumanMessage
    LANGCHAIN_MESSAGES_AVAILABLE = True
except ImportError:
    LANGCHAIN_MESSAGES_AVAILABLE = False
    # Create mock classes for type hints when LangChain not available
    class SystemMessage:
        def __init__(self, content: str): self.content = content
    class HumanMessage:
        def __init__(self, content: str): self.content = content

# Set up logging
logger = logging.getLogger(__name__)

# ================================
# 1. PROMPT COMPOSITION UTILITIES
# ================================

class PromptMergeError(Exception):
    """Exception raised when prompt merging fails"""
    pass

class PromptTemplate:
    """Template for managing prompt composition with placeholders"""
    
    def __init__(self, template: str, required_placeholders: Optional[List[str]] = None):
        self.template = template
        self.required_placeholders = required_placeholders or []
        self.discovered_placeholders = self._discover_placeholders()
    
    def _discover_placeholders(self) -> List[str]:
        """Discover all placeholders in the template"""
        pattern = r'\{\{(\w+)\}\}'
        return list(set(re.findall(pattern, self.template)))
    
    def validate(self) -> None:
        """Validate that all required placeholders are present"""
        missing = set(self.required_placeholders) - set(self.discovered_placeholders)
        if missing:
            raise PromptMergeError(f"Missing required placeholders: {missing}")
    
    def merge(self, **kwargs) -> str:
        """Merge placeholders with provided values"""
        # Validate required placeholders
        if self.required_placeholders:
            missing = set(self.required_placeholders) - set(kwargs.keys())
            if missing:
                raise PromptMergeError(f"Missing values for required placeholders: {missing}")
        
        # Replace placeholders
        result = self.template
        for key, value in kwargs.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        
        return result

def load_prompt_file(file_path: str) -> str:
    """Load prompt from .md or .txt file"""
    if not os.path.exists(file_path):
        raise PromptMergeError(f"Prompt file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise PromptMergeError(f"Error reading prompt file {file_path}: {str(e)}")

def load_examples_file(file_path: str) -> Union[List[Dict], str]:
    """Load examples from .json file or return raw content for .md/.txt"""
    if not os.path.exists(file_path):
        raise PromptMergeError(f"Examples file not found: {file_path}")
    
    try:
        if file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        raise PromptMergeError(f"Error reading examples file {file_path}: {str(e)}")

def convert_examples_to_markdown(examples: List[Dict]) -> str:
    """Convert JSON examples to key-value format without headers"""
    if not examples:
        return ""
    
    markdown_parts = []
    for i, example in enumerate(examples):
        # Add example number as simple key-value
        markdown_parts.append(f"example {i + 1}:")
        
        if 'input' in example:
            markdown_parts.append("input:")
            if isinstance(example['input'], dict):
                markdown_parts.append(f"```json\n{json.dumps(example['input'], indent=2)}\n```")
            else:
                markdown_parts.append(str(example['input']))
        
        if 'output' in example:
            markdown_parts.append("output:")
            if isinstance(example['output'], dict):
                markdown_parts.append(f"```json\n{json.dumps(example['output'], indent=2)}\n```")
            else:
                markdown_parts.append(str(example['output']))
        
        if 'explanation' in example:
            markdown_parts.append(f"explanation:")
            markdown_parts.append(str(example['explanation']))

        def format_dict_to_markdown(d: Dict, prefix: str = "", depth: int = 0) -> List[str]:
            lines = []
            indent = "  " * depth
            for k, v in d.items():
                if isinstance(v, dict):
                    lines.append(f"{indent}{k}:")
                    lines.extend(format_dict_to_markdown(v, prefix, depth + 1))
                else:
                    lines.append(f"{indent}{k}: {v}")
            return lines

        other_keys = [k for k in example.keys() if k not in ['input', 'output', 'explanation']]
        if other_keys:
            context_dict = {k: example[k] for k in other_keys}
            markdown_parts.extend(format_dict_to_markdown(context_dict))
        
        markdown_parts.append("")  # Double line break between sections
        markdown_parts.append("")
    
    return "\n".join(markdown_parts)

def merge_prompt_with_examples(
    prompt_path: str,
    examples_path: Optional[str] = None,
    user_input: Optional[str] = None,
    **additional_placeholders
) -> str:
    """
    Main function to merge prompt with examples and user input
    
    Args:
        prompt_path: Path to prompt template file
        examples_path: Optional path to examples file
        user_input: Optional user input to insert
        **additional_placeholders: Additional values for placeholders
        
    Returns:
        Merged prompt string
        
    Raises:
        PromptMergeError: If merging fails
    """
    try:
        # Load prompt template
        prompt_content = load_prompt_file(prompt_path)
        template = PromptTemplate(prompt_content, required_placeholders=['input'])
        
        # Prepare merge values
        merge_values = additional_placeholders.copy()
        
        # Handle examples
        if examples_path:
            examples_data = load_examples_file(examples_path)
            if isinstance(examples_data, list):
                # Convert JSON examples to markdown
                examples_md = convert_examples_to_markdown(examples_data)
                merge_values['examples'] = examples_md
            else:
                # Already a string (from .md or .txt)
                merge_values['examples'] = examples_data
        else:
            merge_values['examples'] = "No examples provided."
        
        # Handle user input
        if user_input:
            merge_values['input'] = user_input
        elif 'input' not in merge_values:
            merge_values['input'] = "[User input will be provided here]"
        
        # Merge and return
        return template.merge(**merge_values)
        
    except Exception as e:
        raise PromptMergeError(f"Error merging prompt: {str(e)}")

# ================================
# 2. STRUCTURED OUTPUT VALIDATION
# ================================

class ValidationMode(Enum):
    LENIENT = "lenient"
    PEDANTIC = "pedantic"

class StructuredValidator:
    """Validator for structured agent outputs"""
    
    def __init__(self, schema: Type[BaseModel], mode: ValidationMode = ValidationMode.LENIENT):
        self.schema = schema
        self.mode = mode
    
    def validate(self, data: Union[str, Dict, Any]) -> Tuple[bool, Any, Optional[str]]:
        """
        Validate data against schema
        
        Returns:
            Tuple of (is_valid, validated_data, error_message)
        """
        try:
            # Parse JSON string if needed
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError as e:
                    return False, None, f"Invalid JSON: {str(e)}"
            
            # Validate with Pydantic
            if self.mode == ValidationMode.PEDANTIC:
                # Strict validation - no extra fields allowed
                validated = self.schema.model_validate(data, strict=True)
            else:
                # Lenient validation - extra fields ignored
                validated = self.schema.model_validate(data)
            
            return True, validated, None
            
        except ValidationError as e:
            error_msg = self._format_validation_error(e)
            return False, None, error_msg
        except Exception as e:
            return False, None, f"Unexpected validation error: {str(e)}"
    
    def _format_validation_error(self, error: ValidationError) -> str:
        """Format Pydantic validation error for readability"""
        errors = []
        for err in error.errors():
            field = " -> ".join(str(x) for x in err['loc']) if err['loc'] else 'root'
            errors.append(f"Field '{field}': {err['msg']}")
        
        return "Validation errors:\n" + "\n".join(f"  - {err}" for err in errors)

def create_validator(schema: Type[BaseModel], pedantic: bool = False) -> StructuredValidator:
    """Convenience function to create a validator"""
    mode = ValidationMode.PEDANTIC if pedantic else ValidationMode.LENIENT
    return StructuredValidator(schema, mode)

# ================================
# 3. DYNAMIC AGENT LOADER
# ================================

@dataclass
class AgentInfo:
    """Information about a discovered agent"""
    name: str
    path: str
    module_path: str
    agent_class: Optional[Type] = None
    factory_function: Optional[Callable] = None
    init_error: Optional[str] = None
    description: Optional[str] = None

class AgentDiscovery:
    """Dynamic agent discovery and loading"""
    
    def __init__(self, base_path: str = "agents", exclude_dirs: Optional[List[str]] = None):
        self.base_path = base_path
        self.exclude_dirs = exclude_dirs or ['__pycache__', '.git', 'sandbox', 'common']
        self.discovered_agents: Dict[str, AgentInfo] = {}
        self.logger = logging.getLogger(f"{__name__}.AgentDiscovery")
    
    def discover_agents(self, rescan: bool = False) -> Dict[str, AgentInfo]:
        """
        Discover all agents in the base path
        
        Args:
            rescan: If True, rescan even if already discovered
            
        Returns:
            Dictionary of agent_name -> AgentInfo
        """
        if self.discovered_agents and not rescan:
            return self.discovered_agents
        
        self.discovered_agents.clear()
        
        if not os.path.exists(self.base_path):
            self.logger.warning(f"Base path does not exist: {self.base_path}")
            return self.discovered_agents
        
        # Recursively scan directories
        for root, dirs, files in os.walk(self.base_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            # Look for agent files
            agent_info = self._analyze_directory(root, files)
            if agent_info:
                self.discovered_agents[agent_info.name] = agent_info
        
        self.logger.info(f"Discovered {len(self.discovered_agents)} agents")
        return self.discovered_agents
    
    def _analyze_directory(self, directory: str, files: List[str]) -> Optional[AgentInfo]:
        """Analyze a directory for agent files"""
        # Skip if no Python files
        py_files = [f for f in files if f.endswith('.py')]
        if not py_files:
            return None
        
        # Determine agent name from directory
        agent_name = os.path.basename(directory)
        if agent_name == self.base_path or agent_name in self.exclude_dirs:
            return None
        
        # Look for main agent file
        main_file = None
        potential_files = [
            f"{agent_name}.py",
            "agent.py",
            "__init__.py"
        ]
        
        for potential in potential_files:
            if potential in files:
                main_file = potential
                break
        
        if not main_file:
            # Try to find file with "agent" in the name
            agent_files = [f for f in py_files if 'agent' in f.lower()]
            if agent_files:
                main_file = agent_files[0]
        
        if not main_file:
            return None
        
        # Create module path
        rel_path = os.path.relpath(directory, ".")
        module_path = rel_path.replace(os.sep, '.')
        if main_file != "__init__.py":
            module_name = main_file[:-3]  # Remove .py
            module_path = f"{module_path}.{module_name}"
        
        agent_info = AgentInfo(
            name=agent_name,
            path=os.path.join(directory, main_file),
            module_path=module_path
        )
        
        # Try to load and analyze the module
        try:
            self._load_agent_info(agent_info)
        except Exception as e:
            agent_info.init_error = str(e)
            self.logger.warning(f"Error loading agent {agent_name}: {str(e)}")
        
        return agent_info
    
    def _load_agent_info(self, agent_info: AgentInfo) -> None:
        """Load agent class and factory function from module"""
        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(
                agent_info.module_path, 
                agent_info.path
            )
            if not spec or not spec.loader:
                raise ImportError(f"Could not load spec for {agent_info.path}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for agent class
            agent_classes = []
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (name.endswith('Agent') and 
                    obj.__module__ == module.__name__ and
                    name != 'BaseAgent'):
                    agent_classes.append(obj)
            
            if agent_classes:
                agent_info.agent_class = agent_classes[0]  # Take the first one
            
            # Look for factory function
            factory_functions = []
            for name, obj in inspect.getmembers(module, inspect.isfunction):
                if (name.startswith('create_') or 
                    name.startswith('get_') or
                    name.endswith('_agent')):
                    factory_functions.append(obj)
            
            if factory_functions:
                agent_info.factory_function = factory_functions[0]
            
            # Try to get description from docstring
            if hasattr(module, '__doc__') and module.__doc__:
                agent_info.description = module.__doc__.strip().split('\n')[0]
            elif agent_info.agent_class and agent_info.agent_class.__doc__:
                agent_info.description = agent_info.agent_class.__doc__.strip().split('\n')[0]
                
        except Exception as e:
            raise ImportError(f"Error loading module {agent_info.module_path}: {str(e)}")
    
    def load_agent(self, agent_name: str, **kwargs) -> Any:
        """
        Load and instantiate an agent
        
        Args:
            agent_name: Name of the agent to load
            **kwargs: Arguments to pass to agent constructor
            
        Returns:
            Instantiated agent
            
        Raises:
            ValueError: If agent not found or cannot be loaded
        """
        if agent_name not in self.discovered_agents:
            # Try discovering first
            self.discover_agents()
        
        if agent_name not in self.discovered_agents:
            raise ValueError(f"Agent '{agent_name}' not found")
        
        agent_info = self.discovered_agents[agent_name]
        
        if agent_info.init_error:
            raise ValueError(f"Agent '{agent_name}' has initialization error: {agent_info.init_error}")
        
        try:
            # Try factory function first
            if agent_info.factory_function:
                return agent_info.factory_function(**kwargs)
            
            # Try agent class
            if agent_info.agent_class:
                return agent_info.agent_class(**kwargs)
            
            raise ValueError(f"No instantiation method found for agent '{agent_name}'")
            
        except Exception as e:
            raise ValueError(f"Error instantiating agent '{agent_name}': {str(e)}")
    
    def list_agents(self) -> List[str]:
        """List all discovered agent names"""
        self.discover_agents()
        return list(self.discovered_agents.keys())
    
    def get_agent_info(self, agent_name: str) -> Optional[AgentInfo]:
        """Get information about a specific agent"""
        self.discover_agents()
        return self.discovered_agents.get(agent_name)
    
    def print_discovery_report(self) -> None:
        """Print a formatted report of discovered agents"""
        self.discover_agents()
        
        print(f"\n🔍 Agent Discovery Report")
        print(f"Base Path: {os.path.abspath(self.base_path)}")
        print(f"Agents Found: {len(self.discovered_agents)}")
        print("=" * 50)
        
        for name, info in self.discovered_agents.items():
            print(f"\n📦 {name}")
            print(f"   Path: {info.path}")
            print(f"   Module: {info.module_path}")
            
            if info.description:
                print(f"   Description: {info.description}")
            
            if info.agent_class:
                print(f"   ✅ Agent Class: {info.agent_class.__name__}")
            
            if info.factory_function:
                print(f"   ✅ Factory Function: {info.factory_function.__name__}")
            
            if info.init_error:
                print(f"   ❌ Error: {info.init_error}")
            
            if not info.agent_class and not info.factory_function and not info.init_error:
                print(f"   ⚠️  No instantiation method found")

# =======================================
# 4. WORKFLOW CONSTRUCTION HELPERS
# =======================================

if LANGGRAPH_AVAILABLE:
    
    @dataclass
    class WorkflowState:
        """Base state for LangGraph workflows"""
        messages: List[Union[HumanMessage, AIMessage, SystemMessage]] = field(default_factory=list)
        context: Dict[str, Any] = field(default_factory=dict)
        metadata: Dict[str, Any] = field(default_factory=dict)
        
        def add_message(self, message: Union[str, HumanMessage, AIMessage, SystemMessage]) -> None:
            """Add a message to the state"""
            if isinstance(message, str):
                message = HumanMessage(content=message)
            self.messages.append(message)
        
        def get_last_message(self) -> Optional[str]:
            """Get the content of the last message"""
            if self.messages:
                return self.messages[-1].content
            return None
    
    class WorkflowBuilder:
        """Helper for building LangGraph workflows"""
        
        def __init__(self, name: str = "workflow", enable_logging: bool = True):
            self.name = name
            self.enable_logging = enable_logging
            self.logger = logging.getLogger(f"{__name__}.{name}")
            self.graph = StateGraph(WorkflowState)
            self.nodes: Dict[str, Callable] = {}
            
        def add_node(self, name: str, func: Callable, description: str = "") -> 'WorkflowBuilder':
            """Add a node to the workflow"""
            if self.enable_logging:
                # Wrap function with logging
                wrapped_func = self._wrap_with_logging(func, name, description)
            else:
                wrapped_func = func
            
            self.nodes[name] = wrapped_func
            self.graph.add_node(name, wrapped_func)
            
            if self.enable_logging:
                self.logger.info(f"Added node '{name}': {description}")
            
            return self
        
        def add_edge(self, from_node: str, to_node: str) -> 'WorkflowBuilder':
            """Add an edge between nodes"""
            self.graph.add_edge(from_node, to_node)
            
            if self.enable_logging:
                self.logger.info(f"Added edge: {from_node} -> {to_node}")
            
            return self
        
        def add_conditional_edge(
            self, 
            from_node: str, 
            condition_func: Callable,
            condition_map: Dict[str, str],
            description: str = ""
        ) -> 'WorkflowBuilder':
            """Add a conditional edge"""
            if self.enable_logging:
                wrapped_condition = self._wrap_condition_with_logging(condition_func, description)
            else:
                wrapped_condition = condition_func
                
            self.graph.add_conditional_edges(from_node, wrapped_condition, condition_map)
            
            if self.enable_logging:
                self.logger.info(f"Added conditional edge from '{from_node}': {description}")
            
            return self
        
        def set_entry_point(self, node_name: str) -> 'WorkflowBuilder':
            """Set the entry point of the workflow"""
            self.graph.set_entry_point(node_name)
            
            if self.enable_logging:
                self.logger.info(f"Set entry point: {node_name}")
            
            return self
        
        def build(self) -> Any:
            """Build and return the compiled workflow"""
            workflow = self.graph.compile()
            
            if self.enable_logging:
                self.logger.info(f"Workflow '{self.name}' built successfully with {len(self.nodes)} nodes")
            
            return workflow
        
        def _wrap_with_logging(self, func: Callable, name: str, description: str) -> Callable:
            """Wrap a function with logging"""
            def wrapper(state: WorkflowState) -> WorkflowState:
                if self.enable_logging:
                    self.logger.info(f"🏃 Executing node '{name}': {description}")
                    self.logger.debug(f"Input state: {len(state.messages)} messages, context keys: {list(state.context.keys())}")
                
                try:
                    result = func(state)
                    
                    if self.enable_logging:
                        self.logger.info(f"✅ Node '{name}' completed successfully")
                        if hasattr(result, 'messages'):
                            self.logger.debug(f"Output state: {len(result.messages)} messages")
                    
                    return result
                    
                except Exception as e:
                    if self.enable_logging:
                        self.logger.error(f"❌ Node '{name}' failed: {str(e)}")
                    raise
            
            return wrapper
        
        def _wrap_condition_with_logging(self, condition_func: Callable, description: str) -> Callable:
            """Wrap a condition function with logging"""
            def wrapper(state: WorkflowState) -> str:
                if self.enable_logging:
                    self.logger.info(f"🤔 Evaluating condition: {description}")
                
                try:
                    result = condition_func(state)
                    
                    if self.enable_logging:
                        self.logger.info(f"✅ Condition result: {result}")
                    
                    return result
                    
                except Exception as e:
                    if self.enable_logging:
                        self.logger.error(f"❌ Condition evaluation failed: {str(e)}")
                    raise
            
            return wrapper
    
    class WorkflowChainer:
        """Helper for chaining multiple workflows together"""
        
        def __init__(self, name: str = "chained_workflow", enable_logging: bool = True):
            self.name = name
            self.enable_logging = enable_logging
            self.logger = logging.getLogger(f"{__name__}.{name}")
            self.workflows: List[Tuple[str, Any]] = []
        
        def add_workflow(self, name: str, workflow: Any) -> 'WorkflowChainer':
            """Add a workflow to the chain"""
            self.workflows.append((name, workflow))
            
            if self.enable_logging:
                self.logger.info(f"Added workflow to chain: {name}")
            
            return self
        
        def build_sequential_chain(self) -> Callable:
            """Build a sequential chain of workflows"""
            def sequential_executor(initial_state: WorkflowState) -> WorkflowState:
                current_state = initial_state
                
                for name, workflow in self.workflows:
                    if self.enable_logging:
                        self.logger.info(f"🔗 Executing workflow: {name}")
                    
                    try:
                        # Execute workflow
                        result = workflow.invoke(current_state)
                        
                        # Handle different result formats
                        if isinstance(result, dict) and 'messages' in result:
                            # Update state from dict result
                            current_state.messages = result.get('messages', current_state.messages)
                            current_state.context.update(result.get('context', {}))
                            current_state.metadata.update(result.get('metadata', {}))
                        elif hasattr(result, 'messages'):
                            # Result is already a WorkflowState
                            current_state = result
                        else:
                            # Result is something else, add to context
                            current_state.context[f"{name}_result"] = result
                        
                        if self.enable_logging:
                            self.logger.info(f"✅ Workflow '{name}' completed")
                        
                    except Exception as e:
                        if self.enable_logging:
                            self.logger.error(f"❌ Workflow '{name}' failed: {str(e)}")
                        raise
                
                return current_state
            
            return sequential_executor
        
        def build_parallel_chain(self) -> Callable:
            """Build a parallel chain of workflows (executes all simultaneously)"""
            def parallel_executor(initial_state: WorkflowState) -> WorkflowState:
                results = {}
                
                if self.enable_logging:
                    self.logger.info(f"🚀 Executing {len(self.workflows)} workflows in parallel")
                
                for name, workflow in self.workflows:
                    try:
                        result = workflow.invoke(initial_state)
                        results[name] = result
                        
                        if self.enable_logging:
                            self.logger.info(f"✅ Parallel workflow '{name}' completed")
                            
                    except Exception as e:
                        if self.enable_logging:
                            self.logger.error(f"❌ Parallel workflow '{name}' failed: {str(e)}")
                        results[name] = {"error": str(e)}
                
                # Merge results into final state
                final_state = WorkflowState(
                    messages=initial_state.messages.copy(),
                    context=initial_state.context.copy(),
                    metadata=initial_state.metadata.copy()
                )
                
                final_state.context["parallel_results"] = results
                
                return final_state
            
            return parallel_executor

else:
    # Placeholder classes when LangGraph is not available
    class WorkflowState:
        def __init__(self):
            raise ImportError("LangGraph not available. Please install langgraph to use workflow features.")
    
    class WorkflowBuilder:
        def __init__(self, *args, **kwargs):
            raise ImportError("LangGraph not available. Please install langgraph to use workflow features.")
    
    class WorkflowChainer:
        def __init__(self, *args, **kwargs):
            raise ImportError("LangGraph not available. Please install langgraph to use workflow features.")

# ================================
# 5. CONVENIENCE FUNCTIONS
# ================================

def _generate_mock_data_for_schema(schema: Type[BaseModel], agent_name: str, user_input: str) -> Dict[str, Any]:
    """
    Generate mock data that matches a Pydantic schema
    
    Args:
        schema: The Pydantic schema to match
        agent_name: Name of the agent for personalized mock data
        user_input: User input to reference in mock response
        
    Returns:
        Dictionary with mock data matching the schema
    """
    mock_data = {}
    
    for field_name, field_info in schema.model_fields.items():
        if field_name == "response":
            # Generate contextual response
            mock_data[field_name] = f"Mock response from {agent_name}: I can help you with '{user_input[:50]}...'. This is a simulated response for testing purposes."
        elif field_name == "confidence":
            # Generate realistic confidence score
            mock_data[field_name] = 0.8
        elif field_name == "metadata":
            # Generate useful metadata
            mock_data[field_name] = {
                "mock": True,
                "agent": agent_name,
                "input_length": len(user_input),
                "timestamp": "mock_timestamp"
            }
        elif field_name == "thinking":
            # For chain-of-thought schemas
            mock_data[field_name] = f"Mock reasoning process: The user asked about '{user_input[:30]}...', so I should provide helpful guidance."
        elif field_name == "conclusion":
            mock_data[field_name] = f"Mock conclusion based on the query about '{user_input[:30]}...'"
        elif field_name == "steps":
            mock_data[field_name] = [
                "Step 1: Analyze the user's request",
                "Step 2: Generate appropriate response",
                "Step 3: Provide helpful guidance"
            ]
        # Document Requirements Agent specific fields
        elif field_name == "required_documents":
            mock_data[field_name] = ["insurance_policy_document", "benefits_summary"]
        elif field_name == "optional_documents":
            mock_data[field_name] = ["provider_network_directory"]
        elif field_name == "missing_information":
            mock_data[field_name] = []
        elif field_name == "document_categories":
            mock_data[field_name] = {
                "insurance_policy_document": "required",
                "benefits_summary": "required",
                "provider_network_directory": "optional"
            }
        elif field_name == "readiness_assessment":
            mock_data[field_name] = "ready"
        elif field_name == "reasoning":
            mock_data[field_name] = f"Mock analysis for {agent_name}: Based on the request '{user_input[:30]}...', specific documents would be required."
        # Workflow Prescription Agent specific fields
        elif field_name == "workflows":
            mock_data[field_name] = ["information_retrieval"]
        elif field_name == "priority":
            mock_data[field_name] = "medium"
        else:
            # Generate appropriate mock data based on field type annotation
            field_type = field_info.annotation
            if field_type == str or (hasattr(field_type, '__origin__') and field_type.__origin__ is str):
                mock_data[field_name] = f"Mock {field_name} value"
            elif field_type == float or (hasattr(field_type, '__origin__') and field_type.__origin__ is float):
                mock_data[field_name] = 0.75
            elif field_type == int or (hasattr(field_type, '__origin__') and field_type.__origin__ is int):
                mock_data[field_name] = 42
            elif field_type == bool or (hasattr(field_type, '__origin__') and field_type.__origin__ is bool):
                mock_data[field_name] = True
            elif hasattr(field_type, '__origin__') and field_type.__origin__ is list:
                mock_data[field_name] = [f"Mock item 1", f"Mock item 2"]
            elif hasattr(field_type, '__origin__') and field_type.__origin__ is dict:
                mock_data[field_name] = {"mock_key": "mock_value"}
            else:
                mock_data[field_name] = f"Mock {field_name}"
    
    return mock_data

def quick_agent_prototype(
    name: str,
    prompt_path: str,
    examples_path: Optional[str] = None,
    output_schema: Optional[Type[BaseModel]] = None,
    pedantic_validation: bool = False,
    llm: Optional[BaseLanguageModel] = None
) -> Callable:
    """
    Quickly prototype an agent with structured input/output
    
    Args:
        name: Agent name
        prompt_path: Path to prompt template
        examples_path: Optional path to examples
        output_schema: Optional Pydantic schema for output validation
        pedantic_validation: Whether to use strict validation
        llm: Language model to use (if None, generates valid mock JSON)
        
    Returns:
        Callable agent function
    """
    # Create validator if schema provided
    validator = None
    if output_schema:
        validator = create_validator(output_schema, pedantic_validation)
    
    def agent_function(user_input: str, **kwargs) -> Dict[str, Any]:
        """Generated agent function"""
        try:
            # Merge prompt
            merged_prompt = merge_prompt_with_examples(
                prompt_path=prompt_path,
                examples_path=examples_path,
                user_input=user_input,
                **kwargs
            )
            
            # Get LLM response or generate structured mock
            if llm:
                # Use actual LLM
                response = llm.invoke(merged_prompt)
                if hasattr(response, 'content'):
                    output = response.content
                else:
                    output = str(response)
            else:
                # Generate structured mock response
                if output_schema:
                    # Generate valid JSON that matches the schema
                    mock_data = _generate_mock_data_for_schema(output_schema, name, user_input)
                    output = json.dumps(mock_data, indent=2)
                else:
                    # Plain text mock if no schema
                    output = f"[Mock response for agent '{name}' with input: {user_input[:50]}...]"
            
            # Validate output if schema provided
            result = {
                "agent_name": name,
                "input": user_input,
                "raw_output": output,
                "validation_passed": True,
                "validation_error": None,
                "structured_output": None
            }
            
            if validator:
                is_valid, validated_data, error_msg = validator.validate(output)
                result["validation_passed"] = is_valid
                result["validation_error"] = error_msg
                result["structured_output"] = validated_data
            
            return result
            
        except Exception as e:
            return {
                "agent_name": name,
                "input": user_input,
                "error": str(e),
                "validation_passed": False,
                "validation_error": f"Agent function error: {str(e)}"
            }
    
    # Add metadata to function
    agent_function.__name__ = f"{name}_agent"
    agent_function.__doc__ = f"Auto-generated agent function for '{name}' with {'structured' if output_schema else 'unstructured'} output"
    
    return agent_function

def setup_logging(level: str = "INFO", enable_workflow_logging: bool = True) -> None:
    """Setup logging for LangGraph utilities"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('langgraph_utils.log')
        ]
    )
    
    # Configure specific loggers
    if not enable_workflow_logging:
        logging.getLogger(f"{__name__}.WorkflowBuilder").setLevel(logging.WARNING)
        logging.getLogger(f"{__name__}.WorkflowChainer").setLevel(logging.WARNING)

# ================================
# EXAMPLE SCHEMAS
# ================================

class ExampleAgentOutput(BaseModel):
    """Example output schema for testing"""
    response: str = Field(description="The agent's response")
    confidence: float = Field(description="Confidence score", ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class ChainOfThoughtOutput(BaseModel):
    """Example schema for chain-of-thought reasoning"""
    thinking: str = Field(description="The agent's reasoning process")
    conclusion: str = Field(description="The final conclusion")
    confidence: float = Field(description="Confidence in the conclusion", ge=0.0, le=1.0)
    steps: List[str] = Field(description="Individual reasoning steps")

# ================================
# MODULE INITIALIZATION
# ================================

__all__ = [
    # Prompt utilities
    "PromptTemplate",
    "PromptMergeError", 
    "load_prompt_file",
    "load_examples_file",
    "convert_examples_to_markdown",
    "merge_prompt_with_examples",
    
    # Validation utilities
    "ValidationMode",
    "StructuredValidator",
    "create_validator",
    
    # Agent discovery
    "AgentInfo",
    "AgentDiscovery",
    
    # Workflow utilities
    "WorkflowState",
    "WorkflowBuilder", 
    "WorkflowChainer",
    
    # Convenience functions
    "quick_agent_prototype",
    "create_langchain_structured_agent",  # NEW: LangChain best practice
    "_generate_mock_data_for_schema", 
    "setup_logging",
    
    # Example schemas
    "ExampleAgentOutput",
    "ChainOfThoughtOutput"
]

# Initialize module
if __name__ == "__main__":
    print("LangGraph Utilities Module")
    print(f"LangGraph Available: {LANGGRAPH_AVAILABLE}")
    print(f"Available functions: {len(__all__)}")

def create_langchain_structured_agent(
    name: str,
    prompt_path: str,
    examples_path: str, 
    output_schema: Type[BaseModel],
    llm: Optional[Any] = None,
    system_message: Optional[str] = None,
    **kwargs
) -> Callable:
    """
    Create an agent using LangChain's recommended structured output pattern with proper message handling.
    
    This follows LangChain's best practices from:
    - https://python.langchain.com/docs/concepts/structured_outputs/
    - https://python.langchain.com/docs/concepts/messages/
    
    Args:
        name: Agent name
        prompt_path: Path to prompt template file
        examples_path: Path to examples JSON file
        output_schema: Pydantic schema for structured output
        llm: LangChain LLM instance (ChatOpenAI, ChatAnthropic, etc.)
        system_message: Optional custom system message. If None, uses prompt+examples
        **kwargs: Additional arguments for with_structured_output()
        
    Returns:
        Callable agent function that returns structured Pydantic objects
        
    Example:
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        agent = create_langchain_structured_agent(
            name="HealthcareHelper",
            prompt_path="prompts/healthcare.md",
            examples_path="examples/healthcare.json",
            output_schema=HealthcareResponse,
            llm=llm,
            system_message="You are a helpful healthcare assistant."
        )
        
        # Returns Pydantic object directly, no JSON parsing needed
        result = agent("Find me a dermatologist")
        print(result.response)  # Direct access to fields
    """
    logger.info(f"Creating LangChain structured agent: {name}")
    
    if not LANGCHAIN_MESSAGES_AVAILABLE:
        logger.warning("LangChain messages not available, using basic implementation")
    
    # Load and prepare system message
    try:
        if system_message is None:
            # Use prompt and examples as system message
            system_content = merge_prompt_with_examples(prompt_path, examples_path)
            # Remove the {{input}} placeholder since user input goes in HumanMessage
            system_content = system_content.replace("{{input}}", "").strip()
        else:
            system_content = system_message
    except Exception as e:
        logger.error(f"Failed to load prompt/examples: {e}")
        raise PromptMergeError(f"Could not create agent {name}: {e}")
    
    if llm is None:
        # Mock mode - simulate LangChain pattern
        logger.warning(f"No LLM provided, using mock mode for {name}")
        
        def mock_structured_agent(user_input: str) -> BaseModel:
            """Mock agent that returns structured output like LangChain would"""
            mock_data = _generate_mock_data_for_schema(output_schema, name, user_input)
            return output_schema.model_validate(mock_data)
        
        mock_structured_agent.__name__ = f"{name}_langchain_agent"
        mock_structured_agent.__doc__ = f"""
        {name} agent using LangChain structured output pattern (MOCK MODE)
        
        Input: User query string
        Output: {output_schema.__name__} Pydantic object
        
        System Message: {system_content[:100]}...
        Schema: {output_schema.__name__}
        Message Format: SystemMessage + HumanMessage
        """
        
        return mock_structured_agent
    
    else:
        # Real LangChain implementation with proper message handling
        logger.info(f"Creating real LangChain agent with {type(llm).__name__}")
        
        # This is the LangChain recommended pattern
        try:
            # Bind schema to model using with_structured_output()
            structured_model = llm.with_structured_output(output_schema, **kwargs)
            
            def langchain_structured_agent(user_input: str) -> BaseModel:
                """Agent using LangChain's with_structured_output() method with proper messages"""
                
                # Create proper LangChain message structure
                messages = [
                    SystemMessage(content=system_content),
                    HumanMessage(content=user_input)
                ]
                
                # Invoke structured model with message list - returns Pydantic object directly
                result = structured_model.invoke(messages)
                
                logger.info(f"Agent {name} generated structured output: {type(result)}")
                return result
            
            langchain_structured_agent.__name__ = f"{name}_langchain_agent"
            langchain_structured_agent.__doc__ = f"""
            {name} agent using LangChain structured output pattern with proper message handling
            
            Input: User query string  
            Output: {output_schema.__name__} Pydantic object
            
            System Message: {system_content[:100]}...
            Schema: {output_schema.__name__}
            LLM: {type(llm).__name__}
            Message Format: SystemMessage + HumanMessage
            
            Uses LangChain's with_structured_output() method and proper message structure.
            """
            
            return langchain_structured_agent
            
        except Exception as e:
            logger.error(f"Failed to create LangChain structured agent: {e}")
            raise RuntimeError(f"Could not bind schema to LLM: {e}")

# ================================
# UNIFIED AGENT CREATION FUNCTION
# ================================

def create_agent(
    name: str,
    prompt_path: Optional[str] = None,
    examples_path: Optional[str] = None,
    human_message_path: Optional[str] = None,
    output_schema: Optional[Type[BaseModel]] = None,
    llm: Optional[BaseLanguageModel] = None,
    
    # Message pattern toggles
    use_human_message: bool = True,
    use_system_message: bool = True,
    custom_system_message: Optional[str] = None,
    
    # Structured output toggles
    use_structured_output: bool = True,
    pedantic_validation: bool = False,
    
    # Prompt composition toggles
    merge_examples: bool = True,
    convert_examples_to_markdown: bool = True,
    
    # Agent pattern toggles
    use_langchain_pattern: bool = True,
    use_mock_mode: bool = False,
    
    # Validation and error handling
    enable_validation_wrapper: bool = False,
    return_raw_output: bool = False,
    
    # Additional options
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs
) -> Callable:
    """
    Unified agent creation function with all features toggleable.
    
    This function combines all the patterns from the LangGraph utilities:
    - LangChain structured output pattern (recommended)
    - Legacy validation wrapper pattern
    - Mock mode for testing
    - Flexible message patterns
    - Configurable prompt composition
    
    Args:
        name: Agent name for identification
        prompt_path: Path to prompt template file (.md/.txt)
        examples_path: Path to examples file (.json/.md/.txt)
        output_schema: Pydantic schema for structured output
        llm: LangChain LLM instance (ChatOpenAI, ChatAnthropic, etc.)
        
        # Message Pattern Options
        use_human_message: Whether to use HumanMessage for user input
        use_system_message: Whether to use SystemMessage for prompt
        custom_system_message: Override system message (ignores prompt_path)
        
        # Structured Output Options
        use_structured_output: Whether to enforce structured output
        pedantic_validation: Whether to use strict Pydantic validation
        
        # Prompt Composition Options
        merge_examples: Whether to merge examples into prompt
        convert_examples_to_markdown: Whether to convert JSON examples to markdown
        
        # Agent Pattern Options
        use_langchain_pattern: Use LangChain's with_structured_output() (recommended)
        use_mock_mode: Force mock mode even if LLM provided
        
        # Validation Options
        enable_validation_wrapper: Return validation details (legacy mode)
        return_raw_output: Include raw LLM output in response
        
        # LLM Options
        temperature: Override LLM temperature
        max_tokens: Override max tokens
        **kwargs: Additional arguments for with_structured_output()
        
    Returns:
        Callable agent function with configurable behavior
        
    Examples:
        # Basic structured agent (recommended)
        agent = create_agent(
            name="HealthcareHelper",
            prompt_path="healthcare.md",
            examples_path="examples.json", 
            output_schema=HealthcareResponse,
            llm=ChatOpenAI(model="gpt-4")
        )
        result = agent("Find me a doctor")  # Returns HealthcareResponse object
        
        # Mock mode for testing
        agent = create_agent(
            name="TestAgent",
            prompt_path="test.md",
            output_schema=TestSchema,
            use_mock_mode=True
        )
        
        # Legacy validation wrapper
        agent = create_agent(
            name="LegacyAgent", 
            prompt_path="legacy.md",
            output_schema=Schema,
            use_langchain_pattern=False,
            enable_validation_wrapper=True
        )
        
        # Plain text agent (no structure)
        agent = create_agent(
            name="PlainAgent",
            prompt_path="plain.md",
            use_structured_output=False,
            llm=llm
        )
        
        # Custom system message
        agent = create_agent(
            name="CustomAgent",
            custom_system_message="You are a helpful assistant.",
            output_schema=Schema,
            llm=llm
        )
    """
    logger.info(f"Creating unified agent: {name}")
    
    # Validate inputs
    if not prompt_path and not custom_system_message:
        raise ValueError("Must provide either prompt_path or custom_system_message")
    
    if use_structured_output and not output_schema:
        raise ValueError("output_schema required when use_structured_output=True")
    
    # Force mock mode if no LLM provided
    if llm is None:
        use_mock_mode = True
        logger.warning(f"No LLM provided for {name}, using mock mode")

    # Prepare human message
    if human_message_path:
        human_message_template = load_prompt_file(human_message_path)
    else:
        human_message_template = f"{{input}}"
    
    # Prepare system message
    try:
        if custom_system_message:
            system_content = custom_system_message
        elif prompt_path:
            if merge_examples and examples_path:
                # Merge prompt with examples
                system_content = merge_prompt_with_examples(
                    prompt_path=prompt_path,
                    examples_path=examples_path
                )
            else:
                # Just load the prompt
                system_content = load_prompt_file(prompt_path)
        else:
            system_content = f"You are {name}, a helpful AI assistant."
            
    except Exception as e:
        logger.error(f"Failed to prepare system message for {name}: {e}")
        raise PromptMergeError(f"Could not create agent {name}: {e}")
    
    # Create validator if needed
    validator = None
    if use_structured_output and output_schema and not use_langchain_pattern:
        validator = create_validator(output_schema, pedantic_validation)
    
    # Configure LLM if provided
    if llm and not use_mock_mode:
        # Apply temperature/max_tokens if specified
        llm_config = {}
        if temperature is not None:
            llm_config['temperature'] = temperature
        if max_tokens is not None:
            llm_config['max_tokens'] = max_tokens
        
        if llm_config:
            # Create new LLM instance with updated config
            llm = llm.__class__(**{**llm.dict(), **llm_config})
    
    # Choose agent creation pattern
    if use_mock_mode:
        return _create_mock_agent(
            name=name,
            system_content=system_content,
            human_message=human_message_template,
            output_schema=output_schema if use_structured_output else None,
            use_langchain_pattern=use_langchain_pattern,
            use_human_message=use_human_message,
            use_system_message=use_system_message,
            enable_validation_wrapper=enable_validation_wrapper,
            return_raw_output=return_raw_output,
            validator=validator
        )
    
    elif use_langchain_pattern and use_structured_output:
        return _create_langchain_structured_agent(
            name=name,
            system_content=system_content,
            human_message=human_message_template,
            output_schema=output_schema,
            llm=llm,
            use_human_message=use_human_message,
            use_system_message=use_system_message,
            return_raw_output=return_raw_output,
            **kwargs
        )
    
    elif use_structured_output:
        return _create_legacy_structured_agent(
            name=name,
            system_content=system_content,
            human_message=human_message_template,
            output_schema=output_schema,
            llm=llm,
            validator=validator,
            use_human_message=use_human_message,
            use_system_message=use_system_message,
            enable_validation_wrapper=enable_validation_wrapper,
            return_raw_output=return_raw_output
        )
    
    else:
        return _create_plain_text_agent(
            name=name,
            system_content=system_content,
            human_message=human_message_template,
            llm=llm,
            use_human_message=use_human_message,
            use_system_message=use_system_message,
            return_raw_output=return_raw_output
        )

def _create_mock_agent(
    name: str,
    system_content: str,
    human_message: str,
    output_schema: Optional[Type[BaseModel]],
    use_langchain_pattern: bool,
    use_human_message: bool,
    use_system_message: bool,
    enable_validation_wrapper: bool,
    return_raw_output: bool,
    validator: Optional[StructuredValidator]
) -> Callable:
    """Create mock agent for testing"""
    
    def mock_agent(user_input: str) -> Union[BaseModel, Dict[str, Any], str]:
        """Mock agent that generates appropriate responses"""
        
        if output_schema and use_langchain_pattern:
            # LangChain pattern - return Pydantic object directly
            mock_data = _generate_mock_data_for_schema(output_schema, name, user_input)
            result = output_schema.model_validate(mock_data)
            
            if return_raw_output:
                return {
                    "structured_output": result,
                    "raw_output": json.dumps(mock_data, indent=2),
                    "agent_name": name,
                    "pattern": "langchain_mock"
                }
            return result
            
        elif output_schema and enable_validation_wrapper:
            # Legacy pattern - return validation wrapper
            mock_data = _generate_mock_data_for_schema(output_schema, name, user_input)
            raw_output = json.dumps(mock_data, indent=2)
            
            is_valid, validated_data, error_msg = validator.validate(raw_output)
            
            return {
                "agent_name": name,
                "input": user_input,
                "raw_output": raw_output,
                "validation_passed": is_valid,
                "validation_error": error_msg,
                "structured_output": validated_data,
                "pattern": "legacy_mock"
            }
            
        elif output_schema:
            # Simple structured mock
            mock_data = _generate_mock_data_for_schema(output_schema, name, user_input)
            result = output_schema.model_validate(mock_data)
            
            if return_raw_output:
                return {
                    "structured_output": result,
                    "raw_output": json.dumps(mock_data, indent=2)
                }
            return result
            
        else:
            # Plain text mock
            response = f"Mock response from {name}: I can help you with '{user_input[:50]}...'. This is a simulated response for testing purposes."
            
            if return_raw_output:
                return {
                    "response": response,
                    "raw_output": response,
                    "agent_name": name
                }
            return response
    
    mock_agent.__name__ = f"{name}_mock_agent"
    mock_agent.__doc__ = f"Mock agent for {name} (pattern: {'langchain' if use_langchain_pattern else 'legacy'})"
    
    return mock_agent

def _create_langchain_structured_agent(
    name: str,
    system_content: str,
    human_message: str,
    output_schema: Type[BaseModel],
    llm: BaseLanguageModel,
    use_human_message: bool,
    use_system_message: bool,
    return_raw_output: bool,
    **kwargs
) -> Callable:
    """Create LangChain structured agent with with_structured_output()"""
    
    try:
        # Bind schema to model using LangChain's with_structured_output()
        structured_model = llm.with_structured_output(output_schema, **kwargs)
        
        def langchain_agent(user_input: str) -> Union[BaseModel, Dict[str, Any]]:
            """LangChain structured agent with proper message handling"""
            
            # Create message list based on toggles
            messages = []
            
            if use_system_message:
                messages.append(SystemMessage(content=system_content))
            
            if use_human_message:
                # Handle human message template substitution properly
                if "{{input}}" in human_message:
                    # Use PromptTemplate for consistent placeholder handling
                    human_template = PromptTemplate(human_message, required_placeholders=['input'])
                    human_content = human_template.merge(input=user_input)
                elif "{input}" in human_message:
                    # Handle legacy format
                    human_content = human_message.format(input=user_input)
                else:
                    # No placeholder, append user input
                    human_content = f"{human_message}\n\nUser Input: {user_input}"
                
                messages.append(HumanMessage(content=human_content))
            else:
                # Append user input to system message if not using HumanMessage
                if use_system_message:
                    messages[-1].content += f"\n\nUser Input: {user_input}"
                else:
                    messages.append(HumanMessage(content=f"{system_content}\n\nUser Input: {user_input}"))
            
            # Invoke structured model - returns Pydantic object directly
            result = structured_model.invoke(messages)
            
            logger.info(f"Agent {name} generated structured output: {type(result)}")
            
            if return_raw_output:
                return {
                    "structured_output": result,
                    "raw_output": str(result.model_dump()),
                    "agent_name": name,
                    "pattern": "langchain_structured"
                }
            
            return result
        
        langchain_agent.__name__ = f"{name}_langchain_agent"
        langchain_agent.__doc__ = f"""
        {name} agent using LangChain structured output pattern
        
        Input: User query string
        Output: {output_schema.__name__} Pydantic object
        
        System Message: {system_content[:100]}...
        Schema: {output_schema.__name__}
        LLM: {type(llm).__name__}
        Message Pattern: {'SystemMessage + ' if use_system_message else ''}{'HumanMessage' if use_human_message else 'Combined'}
        """
        
        return langchain_agent
        
    except Exception as e:
        logger.error(f"Failed to create LangChain structured agent: {e}")
        raise RuntimeError(f"Could not bind schema to LLM: {e}")

def _create_legacy_structured_agent(
    name: str,
    system_content: str,
    human_message: str,
    output_schema: Type[BaseModel],
    llm: BaseLanguageModel,
    validator: StructuredValidator,
    use_human_message: bool,
    use_system_message: bool,
    enable_validation_wrapper: bool,
    return_raw_output: bool
) -> Callable:
    """Create legacy structured agent with validation wrapper"""
    
    def legacy_agent(user_input: str) -> Union[BaseModel, Dict[str, Any]]:
        """Legacy structured agent with validation wrapper"""
        
        # Create prompt based on message pattern
        if use_system_message and use_human_message:
            # Handle human message template substitution properly
            if "{{input}}" in human_message:
                # Use PromptTemplate for consistent placeholder handling
                human_template = PromptTemplate(human_message, required_placeholders=['input'])
                human_content = human_template.merge(input=user_input)
            elif "{input}" in human_message:
                # Handle legacy format
                human_content = human_message.format(input=user_input)
            else:
                # No placeholder, append user input
                human_content = f"{human_message}\n\nUser Input: {user_input}"
            
            # Use ChatPromptTemplate for proper message structure
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", system_content),
                ("human", human_content)
            ])
            formatted_prompt = prompt_template.format()
        else:
            # Combine into single prompt
            formatted_prompt = f"{system_content}\n\nUser Input: {user_input}"
        
        # Get LLM response
        response = llm.invoke(formatted_prompt)
        if hasattr(response, 'content'):
            output = response.content
        else:
            output = str(response)
        
        # Validate output
        is_valid, validated_data, error_msg = validator.validate(output)
        
        if enable_validation_wrapper:
            return {
                "agent_name": name,
                "input": user_input,
                "raw_output": output,
                "validation_passed": is_valid,
                "validation_error": error_msg,
                "structured_output": validated_data,
                "pattern": "legacy_structured"
            }
        
        if not is_valid:
            raise ValidationError(f"Agent {name} output validation failed: {error_msg}")
        
        if return_raw_output:
            return {
                "structured_output": validated_data,
                "raw_output": output,
                "agent_name": name
            }
        
        return validated_data
    
    legacy_agent.__name__ = f"{name}_legacy_agent"
    legacy_agent.__doc__ = f"Legacy structured agent for {name} with validation wrapper"
    
    return legacy_agent

def _create_plain_text_agent(
    name: str,
    system_content: str,
    human_message: str,
    llm: BaseLanguageModel,
    use_human_message: bool,
    use_system_message: bool,
    return_raw_output: bool
) -> Callable:
    """Create plain text agent without structured output"""
    
    def plain_agent(user_input: str) -> Union[str, Dict[str, Any]]:
        """Plain text agent without structured output"""
        
        # Create message structure
        if use_system_message and use_human_message:
            # Handle human message template substitution properly
            if "{{input}}" in human_message:
                # Use PromptTemplate for consistent placeholder handling
                human_template = PromptTemplate(human_message, required_placeholders=['input'])
                human_content = human_template.merge(input=user_input)
            elif "{input}" in human_message:
                # Handle legacy format
                human_content = human_message.format(input=user_input)
            else:
                # No placeholder, append user input
                human_content = f"{human_message}\n\nUser Input: {user_input}"
            
            messages = [
                SystemMessage(content=system_content),
                HumanMessage(content=human_content)
            ]
            response = llm.invoke(messages)
        else:
            # Single prompt
            prompt = f"{system_content}\n\nUser Input: {user_input}"
            response = llm.invoke(prompt)
        
        # Extract content
        if hasattr(response, 'content'):
            output = response.content
        else:
            output = str(response)
        
        if return_raw_output:
            return {
                "response": output,
                "raw_output": output,
                "agent_name": name,
                "pattern": "plain_text"
            }
        
        return output
    
    plain_agent.__name__ = f"{name}_plain_agent"
    plain_agent.__doc__ = f"Plain text agent for {name}"
    
    return plain_agent

# Update __all__ to include the new function
__all__.append("create_agent")