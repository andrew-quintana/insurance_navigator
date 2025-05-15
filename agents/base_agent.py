"""
Base Agent Module

This module defines the BaseAgent class which serves as a foundation for all agents in the system.
It provides common functionality like logging, initialization, and error handling.
"""

import os
import time
import logging
import json
import traceback
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

# Add import for agent configuration
from utils.agent_config_manager import get_config_manager

# Add import for dotenv
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Replace hardcoded API key with environment variable
api_key = os.getenv('API_KEY')
# Ensure to set the API_KEY environment variable in your environment or .env file

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
        name: str = None,
        llm: Optional[BaseLanguageModel] = None,
        prompt_loader: Any = None,
        logger: Optional[logging.Logger] = None,
        log_dir: str = None,
        prompt_version: str = "V0.1",
        prompt_description: str = "Base implementation",
        use_mock: bool = False,
        prompt_path: str = None,
        examples_path: str = None
    ):
        """
        Initialize the base agent with common components.
        
        Args:
            name: The name of the agent for logging purposes
            llm: An optional language model to use
            prompt_loader: An optional prompt loader instance
            logger: An optional pre-configured logger
            log_dir: Directory for storing log files
            prompt_version: Version tag for tracking prompt iterations with LangSmith
            prompt_description: Brief description of current version for LangSmith metadata
            use_mock: Whether to use mock responses for testing
            prompt_path: Path to prompt template file
            examples_path: Path to examples file
        """
        self.name = name or self.__class__.__name__
        self.llm = llm or ChatAnthropic(model="claude-3-sonnet-20240229-v1h", temperature=0)
        self.prompt_loader = prompt_loader
        self.use_mock = use_mock
        self.prompt_path = prompt_path
        self.examples_path = examples_path
        
        # Get configuration if name is provided
        try:
            self.config_manager = get_config_manager()
            if name:
                self.agent_config = self.config_manager.get_agent_config(name)
                # Update prompt version from config if available
                if "prompt" in self.agent_config:
                    prompt_version = self.agent_config["prompt"].get("version", prompt_version)
                    prompt_description = self.agent_config["prompt"].get("description", prompt_description)
                    
                    # Get paths from config if not provided
                    if not self.prompt_path and "path" in self.agent_config["prompt"]:
                        self.prompt_path = self.agent_config["prompt"]["path"]
                    
                    if not self.examples_path and "examples" in self.agent_config:
                        self.examples_path = self.agent_config["examples"]["path"]
        except Exception as e:
            if logger:
                logger.error(f"Error loading agent configuration: {str(e)}")
            self.agent_config = {}
            self.config_manager = None
        
        # Set default log directory based on agent name if not provided
        if log_dir is None:
            module_path = os.path.dirname(os.path.dirname(__file__))
            agent_dir = os.path.join(module_path, self.name.lower().replace("agent", ""))
            self.log_dir = os.path.join(agent_dir, "logs")
        else:
            self.log_dir = log_dir
        
        # Set up logging
        self.logger = logger or self._setup_logger(self.name, self.log_dir)
        
        # Enhanced performance tracking
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0,
            "total_response_time": 0,
            "token_usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "by_category": {}
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
            category = kwargs.get("category", "default")
            
            try:
                result = func(self, *args, **kwargs)
                success = True
                
                # Update metrics
                self.update_metrics(
                    success=True,
                    response_time=time.time() - start_time,
                    category=category,
                    prompt_tokens=getattr(result, 'prompt_tokens', 0),
                    completion_tokens=getattr(result, 'completion_tokens', 0)
                )
                
                # Log performance
                self.logger.info(
                    f"{func.__name__} completed in {time.time() - start_time:.2f}s - "
                    f"Avg time: {self.metrics['avg_response_time']:.2f}s"
                )
                
                return result
                
            except Exception as e:
                # Update error metrics
                self.update_metrics(
                    success=False,
                    response_time=time.time() - start_time,
                    category=category,
                    prompt_tokens=0,
                    completion_tokens=0
                )
                
                self.logger.error(f"Error in {func.__name__}: {str(e)}")
                self.logger.error(traceback.format_exc())
                
                # Re-raise the exception
                raise
        
        return wrapper
    
    def update_metrics(self, success: bool, response_time: float, category: str, 
                      prompt_tokens: int, completion_tokens: int) -> None:
        """
        Update performance metrics.
        
        Args:
            success (bool): Whether the request was successful
            response_time (float): The response time in seconds
            category (str): The request category
            prompt_tokens (int): The number of prompt tokens used
            completion_tokens (int): The number of completion tokens used
        """
        # Update overall metrics
        self.metrics["total_requests"] += 1
        
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
        
        self.metrics["total_response_time"] += response_time
        self.metrics["avg_response_time"] = self.metrics["total_response_time"] / self.metrics["total_requests"]
        
        # Update token usage
        self.metrics["token_usage"]["prompt_tokens"] += prompt_tokens
        self.metrics["token_usage"]["completion_tokens"] += completion_tokens
        self.metrics["token_usage"]["total_tokens"] += prompt_tokens + completion_tokens
        
        # Update category metrics
        if category not in self.metrics["by_category"]:
            self.metrics["by_category"][category] = {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "avg_response_time": 0,
                "total_response_time": 0
            }
        
        self.metrics["by_category"][category]["total"] += 1
        
        if success:
            self.metrics["by_category"][category]["successful"] += 1
        else:
            self.metrics["by_category"][category]["failed"] += 1
        
        self.metrics["by_category"][category]["total_response_time"] += response_time
        self.metrics["by_category"][category]["avg_response_time"] = (
            self.metrics["by_category"][category]["total_response_time"] / 
            self.metrics["by_category"][category]["total"]
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get the current performance metrics.
        
        Returns:
            Dict[str, Any]: The performance metrics
        """
        # Calculate additional metrics
        if self.metrics["total_requests"] > 0:
            success_rate = self.metrics["successful_requests"] / self.metrics["total_requests"]
        else:
            success_rate = 0
        
        # Add calculated metrics
        metrics = {
            **self.metrics,
            "success_rate": success_rate,
            "timestamp": datetime.now().isoformat()
        }
        
        return metrics
    
    def save_metrics(self, file_path: Optional[str] = None) -> str:
        """
        Save the current performance metrics to a file.
        
        Args:
            file_path (Optional[str]): The file path to save the metrics to
            
        Returns:
            str: The file path where the metrics were saved
        """
        if file_path is None:
            # Create a metrics directory if it doesn't exist
            metrics_dir = os.path.join("agents", self.name, "metrics")
            os.makedirs(metrics_dir, exist_ok=True)
            
            # Generate a file name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(metrics_dir, f"performance_metrics_{timestamp}.json")
        
        # Get the metrics
        metrics = self.get_metrics()
        
        # Save the metrics to the file
        with open(file_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Update the agent config with the latest metrics run
        if self.config_manager and self.name:
            try:
                self.config_manager.update_metrics_run(self.name, file_path)
            except Exception as e:
                self.logger.error(f"Error updating metrics in agent config: {str(e)}")
        
        self.logger.info(f"Metrics saved to {file_path}")
        
        return file_path
    
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
    
    @staticmethod
    def get_env_variable(variable_name: str, default: str = None) -> str:
        """
        Get an environment variable, returning a default if not found.
        
        Args:
            variable_name: Name of the environment variable
            default: Default value to return if variable is not set
            
        Returns:
            The value of the environment variable or the default
        """
        return os.getenv(variable_name, default)
    
    @staticmethod
    def get_api_key(key_name: str = "ANTHROPIC_API_KEY") -> str:
        """
        Get an API key from environment variables.
        
        Args:
            key_name: Name of the API key environment variable
            
        Returns:
            The API key or None if not found
        """
        api_key = os.getenv(key_name)
        if not api_key:
            raise ValueError(f"API key {key_name} not found in environment variables")
        return api_key
    
    def _load_file(self, file_path: str) -> str:
        """
        Load a file and return its contents as a string.
        
        Args:
            file_path (str): Path to the file to load
            
        Returns:
            str: Contents of the file
        """
        try:
            with open(file_path, 'r') as file:
                return file.read()
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
    
    def _build_prompt(self, template_placeholder: str, example_placeholder: str, input_data: Any, 
                     template_path: str = None, examples_path: str = None) -> str:
        """
        Build a prompt by inserting examples into a template.
        
        Args:
            template_placeholder: Placeholder in the template to replace with examples
            example_placeholder: Optional placeholder for examples in the template
            input_data: The input data to include in the prompt
            template_path: Path to the template file (defaults to self.prompt_path)
            examples_path: Path to examples file (defaults to self.examples_path)
            
        Returns:
            str: The complete prompt
        """
        # Use provided paths or instance paths
        template_path = template_path or self.prompt_path
        examples_path = examples_path or self.examples_path
        
        # Load template and examples
        template = self._load_file(template_path)
        examples = self._load_file(examples_path) if examples_path else ""
        
        # Insert examples into the template if placeholder exists
        if example_placeholder and example_placeholder in template:
            template = template.replace(example_placeholder, examples)
        
        # Format input data
        input_str = ""
        if isinstance(input_data, dict):
            input_str = json.dumps(input_data, indent=2)
        elif isinstance(input_data, str):
            input_str = input_data
        else:
            input_str = str(input_data)
        
        # Add the input to the prompt
        if template_placeholder:
            full_prompt = template.replace(template_placeholder, input_str)
        else:
            full_prompt = f"{template}\n\nInput:\n```\n{input_str}\n```\n"
        
        return full_prompt 