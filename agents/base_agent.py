"""
Base Agent Module

This module defines the BaseAgent class which serves as a foundation for all agents in the system.
It provides common functionality like logging, initialization, and error handling.
"""

import os
import time
import logging
import json
from typing import Dict, Any, Optional, List, Union, Callable
from functools import wraps
from langchain_core.language_models import BaseLanguageModel
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import BaseOutputParser
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from datetime import datetime

# Add imports for LangSmith
import os
from langsmith import Client
from langsmith.run_helpers import traceable

# Initialize LangSmith client if API key is available
langsmith_client = None
if os.environ.get("LANGCHAIN_API_KEY"):
    try:
        langsmith_client = Client()
    except Exception as e:
        pass

class BaseAgent:
    """Base class for all agents in the system."""
    
    def __init__(
        self,
        name: str,
        llm: Optional[BaseLanguageModel] = None,
        logger: Optional[logging.Logger] = None,
        log_dir: str = "logs/agents",
        prompt_version: str = "V0.1",
        prompt_description: str = "Base implementation"
    ):
        """
        Initialize the base agent with common components.
        
        Args:
            name: The name of the agent for logging purposes
            llm: An optional language model to use
            logger: An optional pre-configured logger
            log_dir: Directory for storing log files
            prompt_version: Version tag for tracking prompt iterations with LangSmith
            prompt_description: Brief description of current version for LangSmith metadata
        """
        self.name = name
        self.llm = llm or ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0)
        
        # Set up logging
        self.logger = logger or self._setup_logger(name, log_dir)
        
        # Performance tracking
        self.metrics = {
            "requests": 0,
            "errors": 0,
            "total_time": 0,
            "avg_time": 0,
        }
        
        # LangSmith tracking metadata
        self.prompt_version = prompt_version
        self.prompt_description = prompt_description
        
        # Initialize state history for tracking
        self.state_history = []
        self.tools = []
        self.memory = None
        self.human_in_loop = False
        
        self.logger.info(f"{self.name} agent initialized with prompt version {self.prompt_version}")
    
    def _setup_logger(self, name: str, log_dir: str) -> logging.Logger:
        """Set up a logger for the agent."""
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Create logger
        logger = logging.getLogger(f"agent.{name}")
        
        # Add file handler if none exists
        if not logger.handlers:
            log_file = os.path.join(log_dir, f"{name}.log")
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    @staticmethod
    def track_performance(func: Callable) -> Callable:
        """
        Decorator to track performance metrics for agent operations.
        
        Args:
            func: The function to track
            
        Returns:
            Wrapped function with performance tracking
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(self, *args, **kwargs)
                
                # Update metrics
                self.metrics["requests"] += 1
                execution_time = time.time() - start_time
                self.metrics["total_time"] += execution_time
                self.metrics["avg_time"] = self.metrics["total_time"] / self.metrics["requests"]
                
                # Log performance
                self.logger.info(
                    f"{func.__name__} completed in {execution_time:.2f}s - "
                    f"Avg time: {self.metrics['avg_time']:.2f}s"
                )
                
                return result
                
            except Exception as e:
                # Update error metrics
                self.metrics["errors"] += 1
                self.logger.error(f"Error in {func.__name__}: {str(e)}")
                
                # Re-raise the exception
                raise
        
        return wrapper
    
    def get_langsmith_metadata(self) -> Dict[str, str]:
        """Get metadata for LangSmith tracking."""
        return {
            "agent_name": self.name,
            "prompt_version": self.prompt_version,
            "prompt_description": self.prompt_description,
        }
    
    @traceable(run_type="llm", name="process_input")
    def process(self, *args, **kwargs) -> Any:
        """
        Process a request (to be implemented by subclasses).
        This method is decorated with @traceable to track runs in LangSmith.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Processing result (varies by agent)
        """
        raise NotImplementedError("Subclasses must implement the process method")
        
    def create_prompt(self, system_message: str) -> ChatPromptTemplate:
        """Create a prompt template with system message and available tools."""
        messages = [
            ("system", system_message)
        ]
        
        if self.tools:
            tool_descriptions = "\n".join([
                f"- {tool.name}: {tool.description}"
                for tool in self.tools
            ])
            messages[0] = (
                "system",
                f"{system_message}\n\nAvailable tools:\n{tool_descriptions}"
            )
        
        return ChatPromptTemplate.from_messages(messages)
    
    def save_state(self, state: Dict[str, Any]) -> None:
        """Save the current state to history."""
        state_with_metadata = {
            **state,
            "timestamp": datetime.now().isoformat(),
            "agent_name": self.name,
            "prompt_version": self.prompt_version
        }
        self.state_history.append(state_with_metadata)
        
    def load_state(self) -> Dict[str, Any]:
        """Load the most recent state."""
        if not self.state_history:
            return {}
        return self.state_history[-1]
    
    @traceable(run_type="chain", name="agent_run")
    def run(self, prompt: ChatPromptTemplate, input_text: str) -> str:
        """Run the agent with the given prompt and input."""
        # Add LangSmith metadata
        metadata = self.get_langsmith_metadata()
        
        if self.human_in_loop:
            return input("Enter your feedback: ")
            
        # Save state
        current_state = {
            "input": input_text,
            "prompt": str(prompt)
        }
        self.save_state(current_state)
        
        # Update memory if available
        if self.memory:
            self.memory.save_context(
                {"input": input_text},
                {"output": f"Agent {self.name} processed: {input_text}"}
            )
        
        return f"Agent {self.name} processed: {input_text}"
    
    def export_state_history(self, filepath: str) -> None:
        """Export state history to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.state_history, f, indent=2)
            
    def import_state_history(self, filepath: str) -> None:
        """Import state history from a JSON file."""
        with open(filepath, 'r') as f:
            self.state_history = json.load(f) 