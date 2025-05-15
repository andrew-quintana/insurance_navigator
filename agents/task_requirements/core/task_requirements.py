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
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import the agent config manager
from utils.agent_config_manager import get_config_manager

# Import the BaseAgent class
from agents.base_agent import BaseAgent

# Setup logging
logger = logging.getLogger("task_requirements_agent")
if not logger.handlers:
    # Create logs directory if it doesn't exist
    log_dir = os.path.join("agents", "task_requirements", "logs")
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
                 prompt_path=None,
                 examples_path=None,
                 use_mock=False):
        """
        Initialize the Task Requirements Agent.
        
        Args:
            llm: The language model to use for generating responses
            document_manager: The document manager agent to use for document operations
            output_agent: The agent to pass finished tasks to
            prompt_path (str): Optional path to the prompt template file (overrides config)
            examples_path (str): Optional path to the examples file (overrides config)
            use_mock (bool): Whether to use mock responses for testing
        """
        # Initialize the BaseAgent
        super().__init__(
            name="task_requirements",
            llm=llm,
            use_mock=use_mock,
            prompt_path=prompt_path,
            examples_path=examples_path
        )
        
        # Store additional components
        self.document_manager = document_manager
        self.output_agent = output_agent
        
        # Get paths from config if not provided
        if not self.prompt_path:
            self.prompt_path = self.agent_config["prompt"]["path"]
        if not self.examples_path:
            self.examples_path = self.agent_config["examples"]["path"]
        self.test_examples_path = self.agent_config["test_examples"]["path"]
        
        # Load prompt template and examples
        self.prompt_template = self._load_file(self.prompt_path)
        self.examples = self._load_file(self.examples_path)
        
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
        
        # Store the last processed input for context
        self.last_input = None
        self.last_required_context = None
        
        self.logger.info(f"Task Requirements Agent initialized with prompt from {self.prompt_path}")
        self.logger.info(f"Using examples from {self.examples_path}")

    def _build_specific_prompt(self, input_json: Dict[str, Any]) -> str:
        """
        Build the full prompt by inserting examples into the template.
        
        Args:
            input_json (Dict[str, Any]): The input JSON from the patient navigator
            
        Returns:
            str: The complete prompt with examples inserted
        """
        return self._build_prompt(
            template_placeholder=None,
            example_placeholder="{Examples}",
            input_data=input_json,
            template_path=self.prompt_path,
            examples_path=self.examples_path
        )

    def _determine_required_context(self, service_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine the required context based on the service intent.
        
        Args:
            service_intent (Dict[str, Any]): The service intent from the input
            
        Returns:
            Dict[str, Any]: The required context
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
                return {}
        
        # Default empty response if no document manager is available
        return {}

    def _read_document(self, document_type: str) -> Dict[str, Any]:
        """
        Read a document from the document manager.
        
        Args:
            document_type (str): The type of document to read
            
        Returns:
            Dict[str, Any]: The document data
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
                return {
                    "type": "document",
                    "present": False,
                    "user_validated": False,
                    "source": None,
                    "description": f"Error reading {document_type}",
                    "date_added": None,
                    "document_id": None
                }
        
        # Default response if no document manager is available
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
            required_context (Dict[str, Any]): The required context
            
        Returns:
            Dict[str, Any]: The updated required context with validation status
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
                return required_context
        
        # Default response if no document manager is available
        return required_context

    def _request_information_validation(self, required_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request information validation from the document manager.
        
        Args:
            required_context (Dict[str, Any]): The required context
            
        Returns:
            Dict[str, Any]: The updated required context with validation status
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
                return required_context
        
        # Default response if no document manager is available
        return required_context

    def _request_user(self, missing_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request missing information from the user.
        
        Args:
            missing_context (Dict[str, Any]): The missing context
            
        Returns:
            Dict[str, Any]: The updated context with user-provided information
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
                return missing_context
        
        # Default response if no output agent is available
        return missing_context

    def _add_doc_unique_ids(self, required_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add unique IDs to documents in the required context.
        
        Args:
            required_context (Dict[str, Any]): The required context
            
        Returns:
            Dict[str, Any]: The updated required context with unique IDs
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
                return required_context
        
        # Default response if no document manager is available
        return required_context

    def _finish(self, data: Tuple[Dict[str, Any], Dict[str, Any]]) -> Dict[str, Any]:
        """
        Finish processing and return the result.
        
        Args:
            data (Tuple[Dict[str, Any], Dict[str, Any]]): The input and required context
            
        Returns:
            Dict[str, Any]: The result
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
        
        return result

    def _parse_react_output(self, llm_output: str) -> List[Dict[str, str]]:
        """
        Parse the output from the LLM into a list of ReAct steps.
        
        Args:
            llm_output (str): The output from the LLM
            
        Returns:
            List[Dict[str, str]]: The parsed ReAct steps
        """
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

    def _process_react_steps(self, steps: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Process the ReAct steps and execute the actions.
        
        Args:
            steps (List[Dict[str, str]]): The ReAct steps
            
        Returns:
            Dict[str, Any]: The result of processing the steps
        """
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
        
        return {
            "required_context": required_context,
            **result
        }
    
    @BaseAgent.track_performance
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input from the Patient Navigator and determine document requirements.
        
        Args:
            input_data (Dict[str, Any]): The input data from the Patient Navigator
            
        Returns:
            Dict[str, Any]: The processed result with required_context
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
                    
                    self.logger.info(f"LLM response received, length: {len(llm_text)}")
                    
                    # Parse the response
                    react_steps = self._parse_react_output(llm_text)
                    
                    # Process the steps
                    result = self._process_react_steps(react_steps)
                    
                    return result
                except Exception as e:
                    self.logger.error(f"Error processing LLM response: {str(e)}")
                    self.logger.error(traceback.format_exc())
                    
                    return {
                        "error": f"Error processing LLM response: {str(e)}",
                        "status": "failed"
                    }
            else:
                logger.warning("No LLM provided. Cannot process input.")
                
                return {
                    "error": "No LLM provided",
                    "status": "failed"
                }
        except Exception as e:
            logger.error(f"Error processing input: {str(e)}")
            logger.error(traceback.format_exc())
            
            return {
                "error": str(e),
                "status": "failed"
            }

    def _simulate_mock_response(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate a mock response for testing.
        
        Args:
            input_data (Dict[str, Any]): The input data
            
        Returns:
            Dict[str, Any]: The simulated response
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
    config_manager = get_config_manager()
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
    config_manager = get_config_manager()
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
