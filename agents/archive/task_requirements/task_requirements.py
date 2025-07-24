"""
Task Requirements Agent with ReAct-based Processing

This agent is responsible for:
1. Receiving input from the Patient Navigator Agent
2. Determining required documentation for user requests
3. Checking for document availability
4. Requesting missing information from users when needed
5. Forwarding validated tasks to the Service Access Strategy Agent

Uses a ReAct (Reasoning+Acting) framework to reason about documentation requirements
and take appropriate actions to validate them.
"""

import os
import json
import re
import logging
import time
import traceback
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

# Import base agent and exceptions
from agents.base_agent import BaseAgent
from agents.common.exceptions import (
    TaskRequirementsException,
    TaskRequirementsProcessingError,
    DocumentValidationError,
    ReactProcessingError
)

# Import configuration handling
from utils.config_manager import ConfigManager

# Import models
from agents.task_requirements.task_models import (
    DocumentStatus,
    ReactStep,
    TaskProcessingResult
)

# Setup logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Create logs directory if it doesn't exist
    log_dir = os.path.join("logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up file handler
    handler = logging.FileHandler(os.path.join(log_dir, "task_requirements.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class TaskRequirementsAgent(BaseAgent):
    """
    Agent that uses a ReAct-based approach to determine and validate
    required documentation for insurance tasks and requests.
    """
    
    def __init__(self,
                 llm=None,
                 document_manager=None,
                 output_agent=None,
                 config_manager: Optional[ConfigManager] = None,
                 use_mock: bool = False):
        """
        Initialize the Task Requirements Agent.
        
        Args:
            llm: The language model to use for generating responses
            document_manager: The document manager agent to use for document operations
            output_agent: The agent to pass finished tasks to
            config_manager: Configuration manager instance
            use_mock: Whether to use mock responses for testing
        """
        # Get configuration manager if not provided
        self.config_manager = config_manager or ConfigManager()
        
        # Get agent configuration
        agent_config = self.config_manager.get_agent_config("task_requirements")
        
        # Get model configuration
        model_config = agent_config.get("model", {})
        model_name = model_config.get("name", "claude-3-sonnet-20240229")
        temperature = model_config.get("temperature", 0.0)
        
        # Get prompt configuration
        self.custom_prompt_path = agent_config.get("prompt", {}).get("path")
        self.custom_examples_path = agent_config.get("examples", {}).get("path")
        self.custom_test_examples_path = agent_config.get("test_examples", {}).get("path")
        
        # Initialize the BaseAgent
        super().__init__(
            name="task_requirements",
            llm=llm,
            use_mock=use_mock
        )
        
        # Store additional components
        self.document_manager = document_manager
        self.output_agent = output_agent
        self.use_mock = use_mock
        
        # Store the last processed input for context
        self.last_input = None
        self.last_required_context = None
        
        # Define available actions
        self.available_actions = {
            "determine_required_context": self._determine_required_context,
            "read_document": self._read_document,
            "request_document_validation": self._request_document_validation,
            "request_information_validation": self._request_information_validation,
            "request_user": self._request_user,
            "add_doc_unique_ids": self._add_doc_unique_ids,
            "finish": self._finish
        }
        
        # Initialize agent-specific components
        self._initialize_agent()
        
        logger.info(f"Task Requirements Agent initialized with model {model_name}")

    def _initialize_agent(self):
        """Initialize agent-specific components."""
        # Load prompt template and examples using BaseAgent's methods
        try:
            self.prompt_template = self._load_prompt(self.custom_prompt_path)
        except Exception as e:
            self.logger.error(f"Failed to load prompt template: {e}")
            # Use minimal fallback to prevent system crash, but log an error
            self.prompt_template = "Error: Failed to load prompt template"
        
        try:
            self.examples = self._load_examples(self.custom_examples_path)
        except Exception as e:
            self.logger.warning(f"Failed to load examples: {e}")
            self.examples = []  # Should be empty list, not empty string

    def _format_examples_for_prompt(self, examples: List[Dict[str, Any]]) -> str:
        """
        Format the examples list into a string suitable for prompt insertion.
        
        Args:
            examples: List of example dictionaries
            
        Returns:
            Formatted examples string
        """
        if not examples:
            return ""
        
        formatted_examples = []
        for i, example in enumerate(examples):
            example_name = example.get("example_name", f"example_{i+1}")
            input_data = example.get("input", {})
            expected_output = example.get("expected_output", {})
            
            formatted_example = f"## Example {i+1}: {example_name}\n\n"
            formatted_example += f"**Input:**\n```json\n{json.dumps(input_data, indent=2)}\n```\n\n"
            formatted_example += f"**Expected Output:**\n```json\n{json.dumps(expected_output, indent=2)}\n```\n"
            formatted_examples.append(formatted_example)
        
        return "\n".join(formatted_examples)

    def _build_specific_prompt(self, input_json: Dict[str, Any]) -> str:
        """
        Build the full prompt by inserting examples into the template.
        
        Args:
            input_json: The input JSON from the patient navigator
            
        Returns:
            The complete prompt with examples inserted
            
        Raises:
            TaskRequirementsException: If there's an error building the prompt
        """
        try:
            if "{Examples}" in self.prompt_template and self.examples:
                # Format examples as string for prompt replacement
                examples_string = self._format_examples_for_prompt(self.examples)
                prompt = self.prompt_template.replace("{Examples}", examples_string)
            else:
                prompt = self.prompt_template
                
            # Add the input to the prompt
            if input_json:
                prompt += f"\n\nInput:\n```json\n{json.dumps(input_json, indent=2)}\n```"
                
            return prompt
        except Exception as e:
            logger.error(f"Error building prompt: {str(e)}")
            raise TaskRequirementsException(f"Failed to build prompt: {str(e)}")

    def _determine_required_context(self, service_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine the required context based on the service intent.
        
        Args:
            service_intent: The service intent from the input
            
        Returns:
            The required context
            
        Raises:
            DocumentValidationError: If there's an error determining the required context
        """
        if self.use_mock:
            # Return mock required context
            return {
                "insurance_id_card": {
                    "type": "document",
                    "present": None,
                    "source": None,
                    "user_validated": False,
                    "description": "Photo or scan of the user's active insurance card",
                    "date_added": None,
                    "document_id": None
                },
                "insurance_plan": {
                    "type": "document",
                    "present": None,
                    "source": None,
                    "user_validated": False,
                    "description": "System must confirm services are covered under user plan",
                    "date_added": None,
                    "document_id": None
                }
            }
        
        # In a real implementation, this would query the document manager
        # to determine what documents are required based on the service intent
        if self.document_manager:
            try:
                return self.document_manager.determine_required_context(service_intent)
            except Exception as e:
                logger.error(f"Error determining required context: {str(e)}")
                logger.error(traceback.format_exc())
                raise DocumentValidationError(f"Failed to determine required context: {str(e)}")
        
        # Default empty response if no document manager is available
        logger.warning("No document manager available to determine required context")
        return {}

    def _read_document(self, document_type: str) -> Dict[str, Any]:
        """
        Read a document from the document manager.
        
        Args:
            document_type: The type of document to read
            
        Returns:
            The document data
            
        Raises:
            DocumentValidationError: If there's an error reading the document
        """
        if self.use_mock:
            # Return mock document data
            return {
                "type": "document",
                "present": True,
                "user_validated": False,
                "source": "user_documents_database",
                "description": f"Mock {document_type} document",
                "date_added": datetime.now().strftime("%Y-%m-%d"),
                "document_id": f"mock_{document_type}_id"
            }
        
        # In a real implementation, this would query the document manager
        if self.document_manager:
            try:
                return self.document_manager.read_document(document_type)
            except Exception as e:
                logger.error(f"Error reading document: {str(e)}")
                logger.error(traceback.format_exc())
                raise DocumentValidationError(f"Failed to read document {document_type}: {str(e)}")
        
        # Default response if no document manager is available
        logger.warning(f"No document manager available to read {document_type}")
        return {
            "type": "document",
            "present": False,
            "user_validated": False,
            "source": None,
            "description": f"No document manager available to read {document_type}",
            "date_added": None,
            "document_id": None
        }

    def _request_document_validation(self, required_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request document validation from the document manager.
        
        Args:
            required_context: The required context
            
        Returns:
            The updated required context with validation status
            
        Raises:
            DocumentValidationError: If there's an error validating the documents
        """
        if self.use_mock:
            # Return mock validation results
            updated_context = required_context.copy()
            for key in updated_context:
                if "document" in key:
                    updated_context[key]["present"] = True
                    updated_context[key]["user_validated"] = True
            return updated_context
        
        # In a real implementation, this would query the document manager
        if self.document_manager:
            try:
                return self.document_manager.validate_documents(required_context)
            except Exception as e:
                logger.error(f"Error validating documents: {str(e)}")
                logger.error(traceback.format_exc())
                raise DocumentValidationError(f"Failed to validate documents: {str(e)}")
        
        # Default response if no document manager is available
        logger.warning("No document manager available to validate documents")
        return required_context

    def _request_information_validation(self, required_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request information validation from the document manager.
        
        Args:
            required_context: The required context
            
        Returns:
            The updated required context with validation status
            
        Raises:
            DocumentValidationError: If there's an error validating the information
        """
        if self.use_mock:
            # Return mock validation results
            updated_context = required_context.copy()
            for key in updated_context:
                if "information" in key:
                    updated_context[key]["present"] = True
                    updated_context[key]["user_validated"] = True
            return updated_context
        
        # In a real implementation, this would query the document manager
        if self.document_manager:
            try:
                return self.document_manager.validate_information(required_context)
            except Exception as e:
                logger.error(f"Error validating information: {str(e)}")
                logger.error(traceback.format_exc())
                raise DocumentValidationError(f"Failed to validate information: {str(e)}")
        
        # Default response if no document manager is available
        logger.warning("No document manager available to validate information")
        return required_context

    def _request_user(self, missing_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request missing information from the user.
        
        Args:
            missing_context: The missing context
            
        Returns:
            The updated context with user-provided information
            
        Raises:
            TaskRequirementsException: If there's an error requesting information from the user
        """
        if self.use_mock:
            # Return mock user response
            updated_context = missing_context.copy()
            for key in updated_context:
                updated_context[key]["present"] = True
                updated_context[key]["user_validated"] = True
                updated_context[key]["source"] = "user_input"
            return updated_context
        
        # In a real implementation, this would query the output agent
        if self.output_agent:
            try:
                return self.output_agent.request_user_information(missing_context)
            except Exception as e:
                logger.error(f"Error requesting user information: {str(e)}")
                logger.error(traceback.format_exc())
                raise TaskRequirementsException(f"Failed to request user information: {str(e)}")
        
        # Default response if no output agent is available
        logger.warning("No output agent available to request user information")
        return missing_context

    def _add_doc_unique_ids(self, required_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add unique IDs to documents in the required context.
        
        Args:
            required_context: The required context
            
        Returns:
            The updated required context with unique IDs
            
        Raises:
            DocumentValidationError: If there's an error adding unique IDs
        """
        if self.use_mock:
            # Return mock unique IDs
            updated_context = required_context.copy()
            for key in updated_context:
                if updated_context[key].get("present") and not updated_context[key].get("document_id"):
                    updated_context[key]["document_id"] = f"mock_id_{key}"
            return updated_context
        
        # In a real implementation, this would query the document manager
        if self.document_manager:
            try:
                return self.document_manager.add_unique_ids(required_context)
            except Exception as e:
                logger.error(f"Error adding unique IDs: {str(e)}")
                logger.error(traceback.format_exc())
                raise DocumentValidationError(f"Failed to add unique IDs: {str(e)}")
        
        # Default response if no document manager is available
        logger.warning("No document manager available to add unique IDs")
        return required_context

    def _finish(self, data: Tuple[Dict[str, Any], Dict[str, Any]]) -> Dict[str, Any]:
        """
        Finish processing and return the result.
        
        Args:
            data: The input and required context
            
        Returns:
            The result
            
        Raises:
            TaskRequirementsException: If there's an error finishing the task
        """
        input_data, required_context = data
        
        result = {
            "input": input_data,
            "required_context": required_context,
            "status": "complete",
            "timestamp": datetime.now().isoformat()
        }
        
        if self.output_agent and not self.use_mock:
            try:
                self.output_agent.process_task(result)
            except Exception as e:
                logger.error(f"Error processing task: {str(e)}")
                logger.error(traceback.format_exc())
                raise TaskRequirementsException(f"Failed to process task: {str(e)}")
        
        return result

    def _parse_react_output(self, llm_output: str) -> List[Dict[str, str]]:
        """
        Parse the output from the LLM into a list of ReAct steps.
        
        Args:
            llm_output: The output from the LLM
            
        Returns:
            The parsed ReAct steps
            
        Raises:
            ReactProcessingError: If there's an error parsing the output
        """
        try:
            steps = []
            
            # Define regex patterns to extract thought-act-obs triplets
            thought_pattern = r"\*\*Thought\s+(\d+)\*\*:\s+(.*?)(?=\*\*Act|\Z)"
            act_pattern = r"\*\*Act\s+(\d+)\*\*:\s+(.*?)(?=\*\*Obs|\Z)"
            obs_pattern = r"\*\*Obs\s+(\d+)(?:\s+\([^)]*\))?\*\*:\s+(.*?)(?=\*\*Thought|\Z)"
            
            # Extract thoughts, acts, and observations
            thoughts = re.findall(thought_pattern, llm_output, re.DOTALL)
            acts = re.findall(act_pattern, llm_output, re.DOTALL)
            observations = re.findall(obs_pattern, llm_output, re.DOTALL)
            
            # Match them up by step number
            for i in range(len(thoughts)):
                step = {}
                
                # Add thought if available
                if i < len(thoughts):
                    step_num, thought_text = thoughts[i]
                    step["thought"] = thought_text.strip()
                
                # Add act if available
                if i < len(acts):
                    step_num, act_text = acts[i]
                    step["act"] = act_text.strip()
                    
                    # Parse the action and arguments
                    action_match = re.match(r"(\w+)\[(.*)\]", act_text.strip())
                    if action_match:
                        action_name, args_str = action_match.groups()
                        step["action_name"] = action_name
                        step["action_args"] = args_str
                
                # Add observation if available
                if i < len(observations):
                    step_num, obs_text = observations[i]
                    step["observation"] = obs_text.strip()
                
                steps.append(step)
            
            return steps
        except Exception as e:
            logger.error(f"Error parsing ReAct output: {str(e)}")
            raise ReactProcessingError(f"Failed to parse ReAct output: {str(e)}")

    def _process_react_steps(self, steps: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Process the ReAct steps and execute the actions.
        
        Args:
            steps: The ReAct steps
            
        Returns:
            The result of processing the steps
            
        Raises:
            ReactProcessingError: If there's an error processing the steps
        """
        try:
            result = {}
            required_context = {}
            
            for step in steps:
                if "action_name" not in step or "action_args" not in step:
                    continue
                
                action_name = step["action_name"]
                action_args = step["action_args"]
                
                # Skip if the action is not available
                if action_name not in self.available_actions:
                    logger.warning(f"Action not available: {action_name}")
                    continue
                
                # Parse the arguments
                try:
                    if action_name == "determine_required_context":
                        # Extract service_intent from the input
                        args = self.last_input.get("service_intent", {})
                        result = self.available_actions[action_name](args)
                        required_context = result
                        self.last_required_context = required_context
                    elif action_name == "read_document":
                        # Extract document type from the arguments
                        document_type = action_args.strip()
                        doc_result = self.available_actions[action_name](document_type)
                        if required_context and document_type in required_context:
                            required_context[document_type].update(doc_result)
                        else:
                            required_context[document_type] = doc_result
                    elif action_name == "request_document_validation":
                        # Pass the required context
                        required_context = self.available_actions[action_name](required_context)
                    elif action_name == "request_information_validation":
                        # Pass the required context
                        required_context = self.available_actions[action_name](required_context)
                    elif action_name == "request_user":
                        # Pass the required context
                        required_context = self.available_actions[action_name](required_context)
                    elif action_name == "add_doc_unique_ids":
                        # Pass the required context
                        required_context = self.available_actions[action_name](required_context)
                    elif action_name == "finish":
                        # Pass the input and required context
                        result = self.available_actions[action_name]((self.last_input, required_context))
                except Exception as e:
                    logger.error(f"Error processing action {action_name}: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise ReactProcessingError(f"Failed to process action {action_name}: {str(e)}")
            
            return {
                "required_context": required_context,
                **result
            }
        except Exception as e:
            logger.error(f"Error processing ReAct steps: {str(e)}")
            raise ReactProcessingError(f"Failed to process ReAct steps: {str(e)}")
    
    @BaseAgent.track_performance
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input from the Patient Navigator and determine document requirements.
        
        Args:
            input_data: The input data from the Patient Navigator
            
        Returns:
            The processed result with required_context
            
        Raises:
            TaskRequirementsProcessingError: If there's an error processing the input
            ReactProcessingError: If there's an error in the ReAct framework
            DocumentValidationError: If there's an error validating documents
        """
        start_time = time.time()
        
        try:
            # Store the input for context
            self.last_input = input_data
            
            # Get the category for metrics
            category = input_data.get("meta_intent", {}).get("request_type", "unknown")
            
            # If using mock mode, return simulated output
            if self.use_mock:
                mock_result = self._simulate_mock_response(input_data)
                return mock_result
            
            # Build the prompt using the helper method
            prompt = self._build_specific_prompt(input_data)
            
            # Call the LLM
            if self.llm:
                try:
                    # Check whether to use invoke (newer) or generate (older) method
                    if hasattr(self.llm, 'invoke'):
                        # Newer LangChain interface
                        llm_response = self.llm.invoke(prompt)
                        
                        # Handle different response formats
                        if hasattr(llm_response, 'content'):
                            # AIMessage with content attribute
                            llm_text = llm_response.content
                        else:
                            # Fallback, try to convert to string
                            llm_text = str(llm_response)
                    else:
                        # Older LangChain interface
                        llm_response = self.llm.generate(prompt)
                        
                        # Handle different response formats
                        if hasattr(llm_response, 'text'):
                            # Standard response with text attribute
                            llm_text = llm_response.text
                        elif hasattr(llm_response, 'generations') and len(llm_response.generations) > 0:
                            # LangChain format with generations
                            llm_text = llm_response.generations[0][0].text
                        else:
                            # Fallback, try to convert to string
                            llm_text = str(llm_response)
                    
                    logger.info(f"LLM response received, length: {len(llm_text)}")
                    
                    # Parse the response
                    try:
                        react_steps = self._parse_react_output(llm_text)
                    except ReactProcessingError as e:
                        logger.error(f"Error parsing ReAct output: {str(e)}")
                        raise
                    
                    # Process the steps
                    try:
                        result = self._process_react_steps(react_steps)
                    except ReactProcessingError as e:
                        logger.error(f"Error processing ReAct steps: {str(e)}")
                        raise
                    
                    return result
                except (ReactProcessingError, DocumentValidationError):
                    # Re-raise specific exceptions
                    raise
                except Exception as e:
                    logger.error(f"Error processing LLM response: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise TaskRequirementsProcessingError(f"Error processing LLM response: {str(e)}")
            else:
                logger.warning("No LLM provided. Cannot process input.")
                raise TaskRequirementsProcessingError("No LLM provided. Cannot process input.")
        except TaskRequirementsException:
            # Re-raise specific exceptions
            raise
        except Exception as e:
            logger.error(f"Error processing input: {str(e)}")
            logger.error(traceback.format_exc())
            raise TaskRequirementsProcessingError(f"Error processing input: {str(e)}")

    def _simulate_mock_response(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate a mock response for testing.
        
        Args:
            input_data: The input data
            
        Returns:
            The simulated response
        """
        # Get the request type
        request_type = input_data.get("meta_intent", {}).get("request_type", "unknown")
        
        # Create a basic required context
        required_context = {
            "insurance_id_card": {
                "type": "document",
                "present": True,
                "user_validated": True,
                "source": "user_documents_database",
                "description": "Mock insurance ID card",
                "date_added": datetime.now().strftime("%Y-%m-%d"),
                "document_id": "mock_insurance_id"
            }
        }
        
        # Add additional context based on request type
        if request_type == "expert_request":
            required_context["referral_note"] = {
                "type": "document",
                "present": True,
                "user_validated": True,
                "source": "user_documents_database",
                "description": "Mock referral note",
                "date_added": datetime.now().strftime("%Y-%m-%d"),
                "document_id": "mock_referral_id"
            }
        elif request_type == "service_request":
            required_context["insurance_plan"] = {
                "type": "document",
                "present": True,
                "user_validated": True,
                "source": "user_documents_database",
                "description": "Mock insurance plan",
                "date_added": datetime.now().strftime("%Y-%m-%d"),
                "document_id": "mock_plan_id"
            }
        elif request_type == "policy_question":
            required_context["insurance_plan"] = {
                "type": "document",
                "present": True,
                "user_validated": True,
                "source": "user_documents_database",
                "description": "Mock insurance plan",
                "date_added": datetime.now().strftime("%Y-%m-%d"),
                "document_id": "mock_plan_id"
            }
        
        return {
            "input": input_data,
            "required_context": required_context,
            "status": "complete",
            "timestamp": datetime.now().isoformat()
        }

    def reset(self) -> None:
        """Reset the agent's state."""
        self.last_input = None
        self.last_required_context = None
        logger.info("Reset TaskRequirementsAgent state")

    async def analyze_requirements(self, message: str, intent: str) -> 'TaskRequirementsResult':
        """
        Analyze task requirements based on user message and intent.
        
        Args:
            message: The user's message
            intent: The determined intent type
            
        Returns:
            TaskRequirementsResult with requirements analysis
        """
        try:
            # Create a mock input structure for the process method
            input_data = {
                "meta_intent": {
                    "request_type": intent,
                    "summary": message
                },
                "clinical_context": {},
                "service_intent": {
                    "specialty": "general",
                    "service": "consultation"
                },
                "metadata": {
                    "raw_user_text": message
                }
            }
            
            # Use existing process method
            result = self.process(input_data)
            
            # Extract requirements information
            required_context = result.get("required_context", {})
            requirements_count = len(required_context)
            documents_needed = [k for k, v in required_context.items() if v.get("type") == "document"]
            
            # Create result object
            class TaskRequirementsResult:
                def __init__(self, requirements_count: int, documents_needed: List[str], analysis_details: Dict[str, Any] = None):
                    self.requirements_count = requirements_count
                    self.documents_needed = documents_needed
                    self.analysis_details = analysis_details or {}
            
            return TaskRequirementsResult(
                requirements_count=requirements_count,
                documents_needed=documents_needed,
                analysis_details=result
            )
            
        except Exception as e:
            logger.error(f"Error analyzing requirements: {str(e)}")
            
            # Return fallback result
            class TaskRequirementsResult:
                def __init__(self, requirements_count: int, documents_needed: List[str], analysis_details: Dict[str, Any] = None):
                    self.requirements_count = requirements_count
                    self.documents_needed = documents_needed
                    self.analysis_details = analysis_details or {}
            
            return TaskRequirementsResult(
                requirements_count=0,
                documents_needed=[],
                analysis_details={"error": str(e)}
            )

    async def analyze_requirements_structured(self, navigator_result: Dict[str, Any], original_message: str) -> 'TaskRequirementsResult':
        """
        Analyze task requirements using structured navigator output.
        
        Args:
            navigator_result: The structured output from Patient Navigator
            original_message: The original user message
            
        Returns:
            TaskRequirementsResult with requirements analysis including sufficiency determination
        """
        try:
            # Extract structured information from navigator result
            meta_intent = navigator_result.get("meta_intent", {})
            clinical_context = navigator_result.get("clinical_context", {})
            service_intent = navigator_result.get("service_intent", {})
            
            # Create proper input structure that matches our examples
            input_data = {
                "meta_intent": {
                    "request_type": meta_intent.get("request_type", "service_request"),
                    "information_sufficiency": "unknown",  # To be determined
                    "specific_need": service_intent.get("specialty") or meta_intent.get("summary", ""),
                    "location": meta_intent.get("location"),
                    "insurance": meta_intent.get("insurance"),
                    "urgency": meta_intent.get("urgency", "routine"),
                    "missing_information": []
                },
                "clinical_context": clinical_context,
                "service_context": {
                    "specialty": service_intent.get("specialty", "general"),
                    "service_type": service_intent.get("service_type", "consultation")
                },
                "metadata": {
                    "original_query": original_message,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Use existing process method with proper input structure
            result = self.process(input_data)
            
            # Parse the result to determine sufficiency
            required_context = result.get("required_context", {})
            status = result.get("status", "complete")
            
            # Determine if information is sufficient based on our new logic
            missing_context = []
            message_for_navigator = ""
            
            # Check for missing critical information based on request type
            request_type = input_data["meta_intent"]["request_type"]
            
            if request_type in ["service_request", "expert_request"]:
                # For provider searches, check mandatory requirements
                if not input_data["meta_intent"]["location"]:
                    missing_context.append("location")
                if not input_data["meta_intent"]["insurance"]:
                    missing_context.append("insurance_type")
                if not input_data["meta_intent"]["specific_need"]:
                    missing_context.append("specialty_or_service")
            
            # Determine status based on missing information
            if missing_context:
                status = "insufficient_information"
                message_for_navigator = f"Need to ask user for: {', '.join(missing_context)}"
            else:
                status = "sufficient_information"
            
            # Create result object with sufficiency determination
            class TaskRequirementsResult:
                def __init__(self, requirements_count: int, documents_needed: List[str], 
                           analysis_details: Dict[str, Any] = None, status: str = "complete",
                           missing_context: List[str] = None, message_for_patient_navigator: str = ""):
                    self.requirements_count = requirements_count
                    self.documents_needed = documents_needed
                    self.analysis_details = analysis_details or {}
                    self.status = status
                    self.missing_context = missing_context or []
                    self.message_for_patient_navigator = message_for_patient_navigator
            
            return TaskRequirementsResult(
                requirements_count=len(required_context),
                documents_needed=[k for k, v in required_context.items() if v.get("type") == "document"],
                analysis_details=result,
                status=status,
                missing_context=missing_context,
                message_for_patient_navigator=message_for_navigator
            )
            
        except Exception as e:
            logger.error(f"Error analyzing requirements with structured input: {str(e)}")
            
            # Return fallback result
            class TaskRequirementsResult:
                def __init__(self, requirements_count: int, documents_needed: List[str], 
                           analysis_details: Dict[str, Any] = None, status: str = "complete",
                           missing_context: List[str] = None, message_for_patient_navigator: str = ""):
                    self.requirements_count = requirements_count
                    self.documents_needed = documents_needed
                    self.analysis_details = analysis_details or {}
                    self.status = status
                    self.missing_context = missing_context or []
                    self.message_for_patient_navigator = message_for_patient_navigator
            
            return TaskRequirementsResult(
                requirements_count=0,
                documents_needed=[],
                analysis_details={"error": str(e)},
                status="error",
                missing_context=[],
                message_for_patient_navigator="Error processing requirements"
            )

def test_with_anthropic():
    """
    Test the TaskRequirementsAgent with the real Anthropic model.
    This function uses a real language model for testing, so it will make API calls.
    """
    # Check if the ANTHROPIC_API_KEY environment variable is set
    try:
        api_key = BaseAgent.get_api_key("ANTHROPIC_API_KEY")
    except ValueError as e:
        print(f"Error: {str(e)}")
        print("Please add your Anthropic API key to the .env file.")
        print("Example: ANTHROPIC_API_KEY=your-api-key")
        return
    
    # Get the test examples path from agent config
    config_manager = ConfigManager()
    agent_config = config_manager.get_agent_config("task_requirements")
    test_examples_path = agent_config["test_examples"]["path"]
    model_config = agent_config["model"]
    
    # Initialize the Anthropic model
    try:
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model=model_config["name"], temperature=model_config["temperature"])
        print(f"Testing with Anthropic model: {model_config['name']}")
    except Exception as e:
        print(f"Error initializing Anthropic model: {str(e)}")
        return
    
    try:
        with open(test_examples_path, 'r') as file:
            test_content = file.read()
    except FileNotFoundError:
        logger.error(f"Test examples file not found: {test_examples_path}")
        print(f"Test examples file not found: {test_examples_path}")
        return
    
    # Extract just the first test input to avoid excessive API calls
    input_pattern = r'\*\*Input:\*\*\n```json\n(.*?)\n```'
    test_inputs = re.findall(input_pattern, test_content, re.DOTALL)
    
    if not test_inputs:
        logger.error("No test inputs found in the test examples file")
        print("No test inputs found in the test examples file")
        return
    
    # Use just the first test to avoid excessive API calls
    test_input = test_inputs[0]
    
    try:
        input_json = json.loads(test_input)
        print(f"Running test with real Anthropic model for input: {input_json['meta_intent']['summary']}")
        
        # Initialize the agent with the real model
        agent = TaskRequirementsAgent(llm=llm, use_mock=False)
        
        # Process the input
        start_time = time.time()
        result = agent.process(input_json)
        end_time = time.time()
        
        # Log and print the result
        print(f"Test completed in {end_time - start_time:.2f} seconds")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Save metrics
        metrics_file = agent.save_metrics()
        print(f"Metrics saved to {metrics_file}")
        
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON from test input")
        print("Failed to parse JSON from test input")
    except Exception as e:
        logger.error(f"Error processing test: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"Error processing test: {str(e)}")
        print(f"See log file for full traceback: {os.path.join('agents', 'task_requirements', 'logs', 'task_requirements.log')}")

def test_task_requirements_agent():
    """
    Test function for the Task Requirements Agent.
    
    This function loads test examples and runs them through the agent.
    """
    # Get the test examples path from agent config
    config_manager = ConfigManager()
    agent_config = config_manager.get_agent_config("task_requirements")
    test_examples_path = agent_config["test_examples"]["path"]
    
    try:
        with open(test_examples_path, 'r') as file:
            test_content = file.read()
    except FileNotFoundError:
        logger.error(f"Test examples file not found: {test_examples_path}")
        return
    
    # Extract test inputs using regex - fix pattern to match the actual format in examples
    # The pattern in the file uses **Input:** and triple backticks
    input_pattern = r'\*\*Input:\*\*\n```json\n(.*?)\n```'
    test_inputs = re.findall(input_pattern, test_content, re.DOTALL)
    
    if not test_inputs:
        logger.error("No test inputs found in the test examples file")
        logger.error(f"File content length: {len(test_content)} characters")
        logger.error(f"First 100 chars: {test_content[:100]}")
        return
    
    # Initialize the agent with mock database
    agent = TaskRequirementsAgent(use_mock=True)
    
    # Run each test input
    for i, input_json_str in enumerate(test_inputs):
        try:
            input_json = json.loads(input_json_str)
            logger.info(f"Running test {i+1} with input: {input_json['meta_intent']['summary']}")
            
            # Process the input with category for metrics tracking
            result = agent.process(input_json)
            
            # Log the result
            logger.info(f"Test {i+1} result: {json.dumps(result, indent=2)}")
            print(f"Test {i+1} result: {json.dumps(result, indent=2)}")
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from test input {i+1}")
            logger.error(f"JSON string: {input_json_str[:100]}...")
        except Exception as e:
            logger.error(f"Error processing test {i+1}: {str(e)}")
            logger.error(traceback.format_exc())
    
    # Save metrics using BaseAgent's save_metrics method
    metrics_file = agent.save_metrics()
    logger.info(f"Metrics saved to {metrics_file}")
    print(f"Metrics saved to {metrics_file}")
    
    logger.info("All tests completed")
    print("All tests completed")

if __name__ == "__main__":
    # Run the test function when the script is executed directly
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--anthropic":
        # Test with Anthropic if --anthropic flag is provided
        test_with_anthropic()
    else:
        # Otherwise run with mock
        test_task_requirements_agent()
