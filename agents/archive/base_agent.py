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
from typing import Dict, Any, Optional, List, Union, Callable, Tuple
from functools import wraps
from datetime import datetime

# LangChain imports
from langchain_core.language_models import BaseLanguageModel
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool

# Import LangSmith for tracing
import os
from langsmith import Client
from langsmith.run_helpers import traceable

# Import error handling
from utils.error_handling import (
    AgentError, ValidationError, ProcessingError, 
    SecurityError, ConfigurationError
)

# Import new config manager
from utils.config_manager import get_config_manager

# Import dotenv
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
        description: str,
        api_key: Optional[str] = None,
        tools: Optional[List[BaseTool]] = None,
    ):
        """
        Initialize base agent.
        
        Args:
            name: Agent name
            description: Agent description
            api_key: Optional API key
            tools: Optional list of tools
        """
        self.name = name
        self.description = description
        self.api_key = api_key
        self.tools = tools or []
    
    async def run(self, **kwargs: Dict[str, Any]) -> Any:
        """
        Run the agent.
        
        Args:
            **kwargs: Keyword arguments
            
        Returns:
            Agent result
        """
        raise NotImplementedError("Subclasses must implement run()")
    
    async def add_tool(self, tool: BaseTool) -> None:
        """
        Add a tool to the agent.
        
        Args:
            tool: Tool to add
        """
        self.tools.append(tool)
    
    async def remove_tool(self, tool_name: str) -> None:
        """
        Remove a tool from the agent.
        
        Args:
            tool_name: Name of tool to remove
        """
        self.tools = [t for t in self.tools if t.name != tool_name]

    def _initialize_agent(self) -> None:
        """
        Initialize agent-specific components.
        
        This method is meant to be overridden by subclasses to perform
        any agent-specific initialization, such as loading tools, setting up
        memory, or initializing other components.
        """
        pass
    
    def _setup_logger(self, name: str) -> logging.Logger:
        """Set up a logger for the agent."""
        # Ensure centralized logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Create logger
        logger = logging.getLogger(f"agent.{name}")
        
        # Add file handler if none exists
        if not logger.handlers:
            log_file = os.path.join("logs", f"{name}.log")
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
                    f"{func.__name__} completed in {time.time() - start_time:.2f}s"
                )
                
                return result
            except Exception as e:
                # Update metrics with failure
                self.update_metrics(
                    success=False,
                    response_time=time.time() - start_time,
                    category=category,
                    error=str(e)
                )
                
                # Log error
                self.logger.error(
                    f"Error in {func.__name__}: {str(e)}"
                )
                self.logger.error(traceback.format_exc())
                
                # Re-raise the exception
                raise
        
        return wrapper
    
    def update_metrics(
        self, 
        success: bool, 
        response_time: float, 
        category: str = "default", 
        prompt_tokens: int = 0, 
        completion_tokens: int = 0,
        error: str = None
    ) -> None:
        """Update performance metrics."""
        # Update total requests
        self.metrics["total_requests"] += 1
        
        # Update success/failure counts
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
        
        # Update response time metrics
        self.metrics["total_response_time"] += response_time
        self.metrics["avg_response_time"] = (
            self.metrics["total_response_time"] / self.metrics["total_requests"]
        )
        
        # Update token usage
        self.metrics["token_usage"]["prompt_tokens"] += prompt_tokens
        self.metrics["token_usage"]["completion_tokens"] += completion_tokens
        self.metrics["token_usage"]["total_tokens"] += (prompt_tokens + completion_tokens)
        
        # Update category-specific metrics
        if category not in self.metrics["by_category"]:
            self.metrics["by_category"][category] = {
                "requests": 0,
                "successful": 0,
                "failed": 0,
                "avg_response_time": 0,
                "total_response_time": 0,
                "errors": []
            }
        
        cat_metrics = self.metrics["by_category"][category]
        cat_metrics["requests"] += 1
        
        if success:
            cat_metrics["successful"] += 1
        else:
            cat_metrics["failed"] += 1
            if error:
                cat_metrics["errors"].append(error)
        
        cat_metrics["total_response_time"] += response_time
        cat_metrics["avg_response_time"] = (
            cat_metrics["total_response_time"] / cat_metrics["requests"]
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get the current performance metrics."""
        return self.metrics
    
    def save_metrics(self, file_path: Optional[str] = None) -> str:
        """
        Save the current metrics to a file.
        
        Args:
            file_path: Optional path to save the metrics to. If not provided,
                     a default path will be used.
            
        Returns:
            The path to the saved metrics file.
        """
        # Determine the output path
        if file_path is None:
            # Use centralized metrics directory structure
            metrics_dir = os.path.join("metrics", self.name.lower().replace("agent", ""))
            os.makedirs(metrics_dir, exist_ok=True)
            
            # Create a timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(metrics_dir, f"performance_metrics_{timestamp}.json")
        
        # Add metadata
        metrics_with_metadata = {
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "prompt_version": self.prompt_version,
            "metrics": self.metrics
        }
        
        # Save the metrics
        with open(file_path, "w") as f:
            json.dump(metrics_with_metadata, f, indent=2)
        
        # Log the save
        self.logger.info(f"Metrics saved to {file_path}")
        
        # Update the latest metrics path in the agent configuration
        if self.config_manager and self.name in self.config_manager.get_all_agents():
            try:
                agent_config = self.agent_config.copy()
                agent_config["metrics"]["latest_run"] = file_path
                self.config_manager.update_agent_config(self.name, agent_config)
            except Exception as e:
                self.logger.error(f"Error updating metrics path in configuration: {str(e)}")
        
        return file_path
    
    def get_langsmith_metadata(self) -> Dict[str, str]:
        """Get metadata for LangSmith tracing."""
        return {
            "agent_name": self.name,
            "prompt_version": self.prompt_version,
            "prompt_description": self.prompt_description
        }
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data through the standard pipeline.
        
        This method implements a standard processing pipeline that:
        1. Validates the input data
        2. Processes the validated data
        3. Formats the processed data for output
        
        Subclasses should override the _validate_input, _process_data, and
        _format_output methods rather than this method.
        
        Args:
            input_data: The input data to process
            
        Returns:
            The processed output data
            
        Raises:
            ValidationError: If input validation fails
            ProcessingError: If data processing fails
            AgentError: For other errors
        """
        try:
            # Step 1: Validate input
            self.logger.info(f"Processing input: {str(input_data)[:100]}...")
            validated_input = self._validate_input(input_data)
            
            # Step 2: Process data
            self.logger.info("Input validated, processing data...")
            processed_data = self._process_data(validated_input)
            
            # Step 3: Format output
            self.logger.info("Data processed, formatting output...")
            output = self._format_output(processed_data)
            
            self.logger.info("Processing complete")
            return output
            
        except ValidationError as e:
            self.logger.error(f"Validation error: {str(e)}")
            raise
        except ProcessingError as e:
            self.logger.error(f"Processing error: {str(e)}")
            raise
        except AgentError as e:
            self.logger.error(f"Agent error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise AgentError(f"Unexpected error: {str(e)}")
    
    def _validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate input data before processing.
        
        This method should be overridden by subclasses to implement
        agent-specific input validation logic.
        
        Args:
            input_data: The input data to validate
            
        Returns:
            The validated input data
            
        Raises:
            ValidationError: If validation fails
        """
        # Default implementation just returns the input data
        return input_data
    
    def _process_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the validated input data.
        
        This method should be overridden by subclasses to implement
        agent-specific data processing logic.
        
        Args:
            input_data: The validated input data
            
        Returns:
            The processed data
            
        Raises:
            ProcessingError: If processing fails
        """
        # Default implementation raises NotImplementedError
        raise NotImplementedError("Subclasses must implement _process_data")
    
    def _format_output(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the processed data for output.
        
        This method should be overridden by subclasses to implement
        agent-specific output formatting logic.
        
        Args:
            processed_data: The processed data
            
        Returns:
            The formatted output data
        """
        # Default implementation returns the processed data as is
        return processed_data
    
    def create_prompt(
        self, 
        system_message: str,
        human_template: str = "{input}"
    ) -> ChatPromptTemplate:
        """Create a ChatPromptTemplate with the given system message."""
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=human_template)
        ]
        return ChatPromptTemplate.from_messages(messages)
    
    def save_state(self, state: Dict[str, Any]) -> None:
        """Save the current state of the agent."""
        state_with_timestamp = {
            "timestamp": datetime.now().isoformat(),
            "state": state
        }
        self.state_history.append(state_with_timestamp)
        self.logger.debug(f"State saved: {str(state)[:100]}...")
        
    def load_state(self) -> Dict[str, Any]:
        """Load the most recent state of the agent."""
        if not self.state_history:
            return {}
        return self.state_history[-1]["state"]
    
    def _load_prompt(self, prompt_path: Optional[str] = None) -> str:
        """
        Load a prompt from a file.
        
        Args:
            prompt_path: Path to the prompt file. If not provided, the agent's
                       default prompt path will be used.
                       
        Returns:
            The loaded prompt as a string
            
        Raises:
            ConfigurationError: If the prompt file is not found or cannot be read
        """
        path = prompt_path or self.prompt_path
        if not path:
            raise ConfigurationError("No prompt path specified")
        
        try:
            with open(path, 'r') as f:
                prompt_text = f.read()
                self.logger.info(f"Successfully loaded prompt from {path}")
                return prompt_text
        except FileNotFoundError:
            self.logger.error(f"Prompt file not found: {path}")
            raise ConfigurationError(f"Prompt file not found: {path}")
        except Exception as e:
            self.logger.error(f"Error reading prompt file {path}: {str(e)}")
            raise ConfigurationError(f"Error reading prompt file {path}: {str(e)}")
    
    def _load_examples(self, examples_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load examples from a file.
        
        Args:
            examples_path: Path to the examples file. If not provided, the agent's
                         default examples path will be used. If no path is available,
                         returns an empty list.
                         
        Returns:
            The loaded examples as a list of dictionaries, or an empty list if no path is specified
            
        Raises:
            ConfigurationError: If the examples file is specified but not found or is invalid
        """
        path = examples_path or self.examples_path
        if not path:
            self.logger.info("No examples path specified, returning empty examples list")
            return []
        
        try:
            with open(path, 'r') as f:
                # Check file extension and load accordingly
                if path.endswith('.json'):
                    examples = json.load(f)
                    self.logger.info(f"Successfully loaded {len(examples)} examples from {path}")
                    return examples
                elif path.endswith('.md'):
                    # Parse markdown examples - this is a simple implementation
                    # and may need to be adjusted based on your markdown format
                    examples = []
                    current_example = {}
                    
                    for line in f:
                        line = line.strip()
                        if line.startswith('# Example'):
                            if current_example:
                                examples.append(current_example)
                                current_example = {}
                        elif line.startswith('## Input'):
                            current_example['input'] = ''
                        elif line.startswith('## Output'):
                            current_example['output'] = ''
                        elif 'input' in current_example and 'output' not in current_example:
                            current_example['input'] += line + '\n'
                        elif 'output' in current_example:
                            current_example['output'] += line + '\n'
                    
                    if current_example:
                        examples.append(current_example)
                    
                    self.logger.info(f"Successfully loaded {len(examples)} examples from {path}")
                    return examples
                else:
                    raise ConfigurationError(f"Unsupported examples file format: {path}")
        except FileNotFoundError:
            self.logger.error(f"Examples file not found: {path}")
            raise ConfigurationError(f"Examples file not found: {path}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in examples file: {path}")
            raise ConfigurationError(f"Invalid JSON in examples file: {path}")
        except Exception as e:
            self.logger.error(f"Error reading examples file {path}: {str(e)}")
            raise ConfigurationError(f"Error reading examples file {path}: {str(e)}")
    
    @staticmethod
    def get_env_variable(variable_name: str, default: str = None) -> str:
        """
        Get an environment variable.
        
        Args:
            variable_name: The name of the environment variable
            default: The default value to return if the variable is not set
            
        Returns:
            The value of the environment variable, or the default if not set
        """
        return os.environ.get(variable_name, default)
    
    @staticmethod
    def get_api_key(key_name: str = "ANTHROPIC_API_KEY") -> str:
        """
        Get an API key from the environment.
        
        Args:
            key_name: The name of the environment variable containing the API key
            
        Returns:
            The API key
            
        Raises:
            ConfigurationError: If the API key is not set
        """
        api_key = os.environ.get(key_name)
        if not api_key:
            raise ConfigurationError(f"API key not set: {key_name}")
        return api_key