"""
LangGraph Utilities Sandbox

A comprehensive utility module for LangGraph agent development and structured prototyping.

This package provides essential utilities for building and prototyping agents with LangGraph:
1. Prompt composition and validation helpers
2. Structured agent input/output validation
3. Dynamic agent discovery and loading
4. Workflow construction and chaining helpers

Quick start:
    from agents.sandbox.langgraph_utils import (
        merge_prompt_with_examples,
        create_validator,
        AgentDiscovery,
        quick_agent_prototype
    )

For full documentation, see README.md or run the demonstration notebook.
"""

from .langgraph_utils import (
    # Prompt utilities
    PromptTemplate,
    PromptMergeError,
    load_prompt_file,
    load_examples_file,
    convert_examples_to_markdown,
    merge_prompt_with_examples,
    
    # Validation utilities
    ValidationMode,
    StructuredValidator,
    create_validator,
    
    # Agent discovery
    AgentInfo,
    AgentDiscovery,
    
    # Workflow utilities
    WorkflowState,
    WorkflowBuilder,
    WorkflowChainer,
    
    # Convenience functions
    quick_agent_prototype,
    setup_logging,
    
    # Example schemas
    ExampleAgentOutput,
    ChainOfThoughtOutput
)

__version__ = "0.1.0"
__author__ = "Insurance Navigator Team"
__description__ = "LangGraph utilities for agent development and prototyping"

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
    "setup_logging",
    
    # Example schemas
    "ExampleAgentOutput",
    "ChainOfThoughtOutput"
] 