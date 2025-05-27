"""
Prompt Security Agent Implementation

This module contains the core logic for the prompt security agent, including:
1. Security check schema and validation
2. Agent initialization and configuration
3. Input processing and threat detection
4. LangSmith integration for tracing and evaluation
"""

import os
import json
import time
import logging
import re
import subprocess
from typing import Dict, List, Any, Tuple, Optional, Union, Literal
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableSerializable
from langchain_core.language_models import BaseLanguageModel
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, field_validator, constr, ConfigDict
from langsmith import Client, RunTree

from agents.base_agent import BaseAgent
from agents.prompt_security.core.models.security_models import SecurityCheck
from agents.common.exceptions import (
    PromptSecurityException,
    PromptInjectionDetected,
    PromptSecurityValidationError
)
from utils.prompt_loader import load_prompt
from utils.langsmith_config import get_langsmith_client, traceable
from utils.agent_config_manager import get_config_manager
from utils.error_handling import ValidationError, SecurityError, ProcessingError

# Setup logging
logger = logging.getLogger("prompt_security_agent")
if not logger.handlers:
    # Create logs directory if it doesn't exist
    log_dir = os.path.join("logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up file handler
    handler = logging.FileHandler(os.path.join(log_dir, "prompt_security.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Using the SecurityCheck model from models.security_models for output schema

class PromptSecurityAgent(BaseAgent):
    """Agent responsible for ensuring prompt security and content safety using prompt chaining."""
    
    def __init__(
        self,
        name: str = "prompt_security",
        llm: Optional[BaseLanguageModel] = None,
        logger: Optional[logging.Logger] = None,
        use_mock: bool = False
    ):
        """Initialize the prompt security agent."""
        super().__init__(
            name=name,
            llm=llm,
            logger=logger,
            use_mock=use_mock
        )
    
    def _initialize_agent(self):
        """Initialize agent-specific components."""
        # Create parser for the agent output
        self.parser = PydanticOutputParser(pydantic_object=SecurityCheck)
        
        # Load security patterns for quick check
        self.injection_patterns = [
            r"ignore previous instructions",
            r"disregard (all|previous|your) instructions",
            r"ignore everything (above|before)",
            r"forget your instructions",
            r"don't follow your instructions",
            r"system prompt",
            r"you are now",
            r"your new role",
        ]
        
        # Compile regex patterns
        self.injection_regex = re.compile("|".join(self.injection_patterns), re.IGNORECASE)
        
        # Load the main system prompt from file
        try:
            # Try to load the prompt from configured path
            self.security_system_prompt = self._load_prompt()
        except Exception as e:
            # If there's an error, log it and attempt to load from a default location
            self.logger.error(f"Error loading security prompt: {e}")
            self.security_system_prompt = self._load_prompt("agents/prompt_security/prompts/security_prompt_v0_1.md")
        
        # Load examples
        try:
            self.examples = self._load_examples()
        except Exception as e:
            self.logger.warning(f"Failed to load examples: {e}")
            self.examples = []
    
    def _validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the input data before processing.
        
        Args:
            input_data: The input data to validate
            
        Returns:
            The validated input data
            
        Raises:
            ValidationError: If validation fails
        """
        # Check if user_input is in the input data
        if "user_input" not in input_data:
            raise ValidationError(
                message="Missing required field: user_input",
                field="user_input",
                value=None
            )
        
        # Check if user_input is a string
        if not isinstance(input_data["user_input"], str):
            raise ValidationError(
                message="user_input must be a string",
                field="user_input",
                value=input_data["user_input"]
            )
        
        # Check if user_input is empty
        if not input_data["user_input"].strip():
            raise ValidationError(
                message="user_input cannot be empty",
                field="user_input",
                value=input_data["user_input"]
            )
        
        return input_data
    
    def _process_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the validated input data.
        
        Args:
            input_data: The validated input data
            
        Returns:
            The processed data
            
        Raises:
            ProcessingError: If processing fails
        """
        user_input = input_data["user_input"]
        
        try:
            # First do a quick check with regex
            quick_check_result = self.quick_check(user_input)
            
            # If quick check detects a potential issue, do a more thorough check
            if quick_check_result:
                self.logger.info("Quick check detected potential issue, performing thorough check")
            
            # Do the thorough check with LLM
            security_check = self.check_input(user_input)
            
            return {
                "security_check": security_check,
                "original_input": user_input
            }
        
        except Exception as e:
            raise ProcessingError(
                message=f"Error processing security check: {str(e)}",
                stage="security_check"
            )
    
    def _format_output(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the processed data for output.
        
        Args:
            processed_data: The processed data
            
        Returns:
            The formatted output data
        """
        security_check = processed_data["security_check"]
        original_input = processed_data["original_input"]
        
        # Extract the key fields from the security check
        is_safe = security_check["is_safe"]
        sanitized_input = security_check["sanitized_input"]
        
        # Add a security warning if needed
        if not is_safe:
            threat_type = security_check["threat_type"]
            threat_severity = security_check["threat_severity"]
            reasoning = security_check["reasoning"]
            
            security_warning = (
                f"Security threat detected: {threat_type} ({threat_severity})\n"
                f"Reasoning: {reasoning}"
            )
        else:
            security_warning = None
        
        # Construct the final output
        return {
            "is_safe": is_safe,
            "sanitized_input": sanitized_input,
            "original_input": original_input,
            "security_warning": security_warning,
            "security_check": security_check
        }
    
    @traceable(run_type="chain")
    def quick_check(self, user_input: str) -> bool:
        """Perform a quick check for obvious security issues using regex."""
        return bool(self.injection_regex.search(user_input))
    
    @traceable(run_type="chain")
    def check_input(self, user_input: str) -> Dict[str, Any]:
        """
        Perform a thorough security check on the user input using the LLM.
        
        Args:
            user_input: The user input to check
            
        Returns:
            Dictionary containing the security check results
            
        Raises:
            SecurityError: If the security check fails
        """
        try:
            if self.use_mock:
                # For testing, return a mock response
                return {
                    "is_safe": True,
                    "threat_detected": False,
                    "threat_type": "none",
                    "threat_severity": "none_detected",
                    "sanitized_input": user_input,
                    "confidence": 0.95,
                    "reasoning": "This input appears to be a standard query without any attempt to manipulate the system."
                }
            
            # Create the prompt
            system_prompt = self.security_system_prompt
            
            # Add examples if available
            if self.examples:
                examples_text = "\n\nExamples:\n\n"
                for i, example in enumerate(self.examples[:3], 1):
                    examples_text += f"Example {i}:\nInput: {example.get('input', '')}\nOutput: {example.get('output', '')}\n\n"
                system_prompt += examples_text
            
            # Create messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input)
            ]
            
            # Get the response from the LLM
            response = self.llm.invoke(messages)
            content = response.content
            
            # Try to parse the response as JSON
            try:
                # Strip any explanatory text before the JSON
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    check_result = json.loads(json_str)
                else:
                    raise ValueError("Could not find JSON in response")
                
                # Validate against our schema
                check_result = self.parser.parse(json_str)
                check_result = check_result.model_dump()
                
                return check_result
                
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract structured information from the text
                self.logger.warning(f"Failed to parse LLM response as JSON: {content}")
                
                # Extract key information using regex patterns
                is_safe = "safe" in content.lower() and not "unsafe" in content.lower()
                threat_detected = "threat" in content.lower() or "unsafe" in content.lower()
                
                # Create a fallback response
                fallback_response = {
                    "is_safe": is_safe,
                    "threat_detected": threat_detected,
                    "threat_type": "unknown" if threat_detected else "none",
                    "threat_severity": "borderline" if threat_detected else "none_detected",
                    "sanitized_input": "[POTENTIALLY UNSAFE CONTENT]" if threat_detected else user_input,
                    "confidence": 0.5,
                    "reasoning": f"This input appears to be {'potentially unsafe' if threat_detected else 'safe'} based on fallback analysis."
                }
                
                return fallback_response
                
        except Exception as e:
            # If any error occurs, fail safe by blocking the input
            self.logger.error(f"Error during security check: {str(e)}")
            
            raise SecurityError(
                message=f"Error during security check: {str(e)}",
                threat_type="unknown",
                threat_severity="borderline"
            )
    
    @traceable(run_type="chain")
    def process(self, user_input: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Process user input and check for security issues.
        
        This method provides a simpler interface than the standard process method,
        accepting a string instead of a dictionary and returning a tuple of results.
        
        Args:
            user_input: The user input to check
            
        Returns:
            Tuple of (is_safe, sanitized_input, security_check_details)
        """
        # Call the standard process method with a dictionary input
        result = super().process({"user_input": user_input})
        
        # Extract the key results
        is_safe = result["is_safe"]
        sanitized_input = result["sanitized_input"]
        security_check = result["security_check"]
        
        return is_safe, sanitized_input, security_check 