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
from typing import Dict, List, Any, Optional, Union

# Setup logging
logger = logging.getLogger("task_requirements_agent")
if not logger.handlers:
    # Create logs directory if it doesn't exist
    log_dir = os.path.join("agents", "task_requirements", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up file handler
    handler = logging.FileHandler(os.path.join(log_dir, "task_requirements_react.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class TaskRequirementsReactAgent:
    """
    Agent that uses a ReAct-based approach to determine and validate
    required documentation for insurance tasks and requests.
    """
    
    def __init__(self, prompt_template_path="agents/task_requirements/prompts/prompt_v0.1.md", 
                 examples_path="agents/task_requirements/prompts/examples/prompt_examples_v0_1.md",
                 use_mock_db=False,
                 patient_navigator_agent=None):
        """
        Initialize the Task Requirements ReAct Agent.
        
        Args:
            prompt_template_path (str): Path to the prompt template file
            examples_path (str): Path to the examples file
            use_mock_db (bool): Whether to use a mock document database for testing
            patient_navigator_agent: Optional reference to the patient navigator agent
        """
        self.prompt_template_path = prompt_template_path
        self.examples_path = examples_path
        self.use_mock_db = use_mock_db
        self.patient_navigator_agent = patient_navigator_agent
        
        # Load prompt template and examples
        self.prompt_template = self._load_file(prompt_template_path)
        self.examples = self._load_file(examples_path)
        
        # Initialize the mock document database if needed
        self.mock_document_db = self._init_mock_document_db() if use_mock_db else None
        
        # Store the last processed input for context
        self.last_input = None
        
        logger.info(f"Task Requirements ReAct Agent initialized with prompt from {prompt_template_path}")
        logger.info(f"Using examples from {examples_path}")

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
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

    def _init_mock_document_db(self) -> Dict[str, Any]:
        """
        Initialize a mock document database for testing.
        
        Returns:
            Dict[str, Any]: Mock document database
        """
        return {
            # Insurance ID cards
            "doc_328uwh": {
                "type": "insurance_id_card",
                "description": "Photo or scan of the user's active insurance card. Confirmed active with UnitedHealthcare, valid through 2026.",
                "date_added": "2025-05-10",
                "validated": True
            },
            "doc_554abc": {
                "type": "insurance_id_card",
                "description": "Photo or scan of the user's active insurance card. Confirmed active with Anthem PPO, valid through 2026.",
                "date_added": "2025-05-11",
                "validated": True
            },
            "doc_abc123": {
                "type": "insurance_id_card",
                "description": "Active Anthem PPO card, valid through 2026.",
                "date_added": "2025-05-11",
                "validated": True
            },
            "doc_4482x": {
                "type": "insurance_id_card",
                "description": "Cigna HMO insurance card valid through 2025",
                "date_added": "2025-05-12",
                "validated": True
            },
            
            # Referral notes
            "muhoh351fxq": {
                "type": "referral_note",
                "description": "Referral from primary care doctor for podiatry",
                "date_added": "2025-05-14",
                "validated": True
            },
            
            # Plan coverage info
            "covcheck_00281": {
                "type": "plan_coverage_info",
                "description": "Plan HMO-X23 requires a referral from a PCP for podiatry.",
                "date_added": "2025-05-13",
                "validated": True
            },
            "covcheck_00312": {
                "type": "plan_coverage_info",
                "description": "Allergy testing is covered with no referral required under Anthem PPO plan.",
                "date_added": "2025-05-13",
                "validated": True
            },
            "covcheck_0333": {
                "type": "plan_coverage_info",
                "description": "Allergy testing is covered under Anthem PPO without referral.",
                "date_added": "2025-05-13",
                "validated": True
            },
            "covcheck_0451": {
                "type": "plan_coverage_info",
                "description": "Plan allows up to 25 physical therapy visits per year.",
                "date_added": "2025-05-13",
                "validated": True
            }
        }

    def _build_prompt(self, input_json: Dict[str, Any]) -> str:
        """
        Build the full prompt by inserting examples into the template.
        
        Args:
            input_json (Dict[str, Any]): The input JSON from the patient navigator
            
        Returns:
            str: The complete prompt with examples inserted
        """
        # Insert examples into the template
        full_prompt = self.prompt_template.replace("{Examples}", self.examples)
        
        # Add the input to the prompt
        full_prompt += f"\nInput:\n```json\n{json.dumps(input_json, indent=2)}\n```\n"
        
        return full_prompt

    def process(self, input_data: Dict[str, Any], llm_client=None) -> Dict[str, Any]:
        """
        Process input from the Patient Navigator and determine document requirements.
        
        Args:
            input_data (Dict[str, Any]): The input data from the Patient Navigator
            llm_client: The LLM client to use for generating responses (optional)
            
        Returns:
            Dict[str, Any]: The processed result with required_context
        """
        # Store the input for context
        self.last_input = input_data
        
        if not llm_client:
            # Just log that we'd use a real LLM in production
            logger.info("No LLM client provided. In production, this would use a real LLM.")
            # For testing purposes, return simulated output based on the input
            result = self._simulate_llm_response(input_data)
            
            # Check if we need to request missing documents
            missing_docs = self._check_for_missing_documents(result["required_context"])
            if missing_docs:
                request_result = self.request_from_patient_navigator(missing_docs)
                if request_result:
                    # In a real implementation, we would wait for a response
                    # For testing, we'll simulate getting the documents
                    result["patient_navigator_request"] = request_result
                    result["required_context"] = self._simulate_document_update(result["required_context"])
            
            return result
        
        # In a real implementation, we would:
        # 1. Build the prompt
        prompt = self._build_prompt(input_data)
        
        # 2. Send the prompt to the LLM
        # llm_response = llm_client.generate(prompt)
        
        # 3. Parse the LLM response to extract the ReAct steps
        # parsed_steps = self._parse_react_output(llm_response)
        
        # 4. Process the steps to determine the final output
        # result = self._process_react_steps(parsed_steps)
        
        # 5. Check if we need to request missing documents
        # missing_docs = self._check_for_missing_documents(result["required_context"])
        # if missing_docs:
        #     self.request_from_patient_navigator(missing_docs)
        
        # 6. Return the result
        # return result
        
        # For now, simulate the response
        return self._simulate_llm_response(input_data)

    def _check_for_missing_documents(self, required_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check for missing documents in the required context.
        
        Args:
            required_context (Dict[str, Any]): The required context with document status
            
        Returns:
            List[Dict[str, Any]]: List of missing documents
        """
        missing_docs = []
        
        for doc_type, doc_info in required_context.items():
            if doc_info.get("present") is None or doc_info.get("present") is False:
                missing_docs.append({
                    "type": doc_type,
                    "description": doc_info.get("description", f"Missing {doc_type}")
                })
        
        return missing_docs

    def request_from_patient_navigator(self, missing_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send a request to the Patient Navigator Agent for missing documents.
        
        Args:
            missing_docs (List[Dict[str, Any]]): List of missing documents
            
        Returns:
            Dict[str, Any]: The request sent to the Patient Navigator
        """
        if not missing_docs:
            return None
        
        # Create the request
        request = {
            "request_type": "document_request",
            "missing_documents": missing_docs,
            "context": {
                "service_intent": self.last_input.get("service_intent", {}),
                "meta_intent": self.last_input.get("meta_intent", {})
            }
        }
        
        logger.info(f"Sending request to Patient Navigator: {json.dumps(request)}")
        
        # If we have a real Patient Navigator agent, send the request
        if self.patient_navigator_agent:
            try:
                response = self.patient_navigator_agent.process_request(request)
                logger.info(f"Received response from Patient Navigator: {json.dumps(response)}")
                return request
            except Exception as e:
                logger.error(f"Error sending request to Patient Navigator: {str(e)}")
                return request
        
        # For testing, just return the request
        return request

    def _simulate_document_update(self, required_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate updating the required context with documents from the Patient Navigator.
        
        Args:
            required_context (Dict[str, Any]): The current required context
            
        Returns:
            Dict[str, Any]: The updated required context
        """
        updated_context = required_context.copy()
        
        # For each document that's missing, simulate getting it
        for doc_type, doc_info in updated_context.items():
            if doc_info.get("present") is None or doc_info.get("present") is False:
                # Find a matching document in the mock database
                for doc_id, mock_doc in self.mock_document_db.items():
                    if mock_doc["type"] == doc_type:
                        updated_context[doc_type] = {
                            "type": "document",
                            "present": True,
                            "validated": True,
                            "source": "user_documents_database",
                            "description": mock_doc["description"],
                            "date_added": mock_doc["date_added"],
                            "document_id": doc_id
                        }
                        break
        
        return updated_context

    def _parse_react_output(self, llm_output: str) -> List[Dict[str, str]]:
        """
        Parse the LLM output to extract the ReAct steps.
        
        Args:
            llm_output (str): The raw output from the LLM
            
        Returns:
            List[Dict[str, str]]: List of parsed ReAct steps
        """
        steps = []
        
        # Pattern to match the Thought-Act-Obs triples
        pattern = r'\*\*Thought (\d+)\*\*:\s*(.*?)(?:\n\*\*Act \1\*\*:\s*(.*?)(?:\n\*\*Obs \1(?:\s*\(.*?\))?\*\*:\s*(.*?))?)?(?=\n\*\*Thought \d+\*\*|\Z)'
        
        matches = re.findall(pattern, llm_output, re.DOTALL)
        
        for match in matches:
            step_num, thought, act, obs = match
            step = {"step": int(step_num), "thought": thought.strip()}
            
            if act:
                # Parse the action and its arguments
                act = act.strip()
                action_match = re.match(r'(\w+)\[(.*)\]', act)
                if action_match:
                    action_name, action_args = action_match.groups()
                    step["action"] = action_name
                    step["action_args"] = action_args
                else:
                    step["action"] = act
                    step["action_args"] = None
            
            if obs:
                step["observation"] = obs.strip()
            
            steps.append(step)
        
        return steps

    def _process_react_steps(self, steps: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Process the parsed ReAct steps to determine the final output.
        
        Args:
            steps (List[Dict[str, str]]): The parsed ReAct steps
            
        Returns:
            Dict[str, Any]: The final output
        """
        required_context = {}
        
        for step in steps:
            if "action" not in step:
                continue
                
            action = step["action"]
            
            if action == "determine_required_context":
                # Extract the required context from the observation
                if "observation" in step:
                    try:
                        required_context = json.loads(step["observation"])
                    except json.JSONDecodeError:
                        # If the observation is not valid JSON, try to extract it
                        json_match = re.search(r'```json\n(.*?)\n```', step["observation"], re.DOTALL)
                        if json_match:
                            try:
                                required_context = json.loads(json_match.group(1))
                            except json.JSONDecodeError:
                                logger.error("Failed to parse JSON from observation")
            
            elif action == "read_document":
                # Update the required context with the document information
                if "action_args" in step and "observation" in step:
                    doc_type = step["action_args"]
                    if doc_type in required_context:
                        required_context[doc_type]["present"] = True
                        required_context[doc_type]["validated"] = True
            
            elif action == "request_user":
                # Process the user request response
                if "observation" in step:
                    try:
                        updated_context = json.loads(step["observation"])
                        required_context.update(updated_context)
                    except json.JSONDecodeError:
                        logger.error("Failed to parse JSON from user request observation")
            
            elif action == "add_doc_unique_ids":
                # Process the unique IDs
                if "observation" in step:
                    try:
                        updated_context = json.loads(step["observation"])
                        required_context.update(updated_context)
                    except json.JSONDecodeError:
                        logger.error("Failed to parse JSON from add_doc_unique_ids observation")
            
            elif action == "trigger_next_agent":
                # We've reached the end of the process
                break
        
        return {"required_context": required_context}

    def _simulate_document_action(self, action: str, doc_type: str) -> Dict[str, Any]:
        """
        Simulate a document-related action for testing.
        
        Args:
            action (str): The action to simulate
            doc_type (str): The document type
            
        Returns:
            Dict[str, Any]: The simulated response
        """
        if not self.use_mock_db:
            return {"error": "Mock database not enabled"}
        
        if action == "read_document":
            # Find a document of the specified type
            for doc_id, doc_info in self.mock_document_db.items():
                if doc_info["type"] == doc_type:
                    return {
                        "type": "document",
                        "present": True,
                        "validated": True,
                        "source": "user_documents_database",
                        "description": doc_info["description"],
                        "date_added": doc_info["date_added"],
                        "document_id": doc_id
                    }
            
            # No document found
            return {
                "type": "document",
                "present": False,
                "validated": False,
                "source": None,
                "description": f"{doc_type} is missing",
                "date_added": None,
                "document_id": None
            }
        
        return {"error": f"Unsupported action: {action}"}

    def _simulate_llm_response(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate an LLM response for testing.
        
        Args:
            input_data (Dict[str, Any]): The input data
            
        Returns:
            Dict[str, Any]: The simulated response
        """
        # Default response structure
        response = {
            "required_context": {}
        }
        
        # Very basic simulation based on the request type and specialty
        meta_intent = input_data.get("meta_intent", {})
        request_type = meta_intent.get("request_type", "")
        
        service_intent = input_data.get("service_intent", {})
        specialty = service_intent.get("specialty", "")
        service = service_intent.get("service", "")
        
        # Simulate different responses based on the request type and specialty
        if request_type == "expert_request" and specialty == "podiatry":
            # Similar to Example 1 - with missing referral for testing
            response["required_context"] = {
                "insurance_id_card": {
                    "type": "document",
                    "present": True,
                    "validated": True,
                    "source": "user_documents_database",
                    "description": "Photo or scan of the user's active insurance card. Confirmed active with UnitedHealthcare, valid through 2026.",
                    "date_added": "2025-05-10",
                    "document_id": "doc_328uwh"
                },
                "referral_note": {
                    "type": "document",
                    "present": None,
                    "validated": False,
                    "source": None,
                    "description": "Referral from primary care doctor for podiatry",
                    "date_added": None,
                    "document_id": None
                },
                "plan_coverage_info": {
                    "type": "document",
                    "present": True,
                    "validated": True,
                    "source": "user_documents_database",
                    "description": "Plan HMO-X23 requires a referral from a PCP for podiatry.",
                    "date_added": "2025-05-13",
                    "document_id": "covcheck_00281"
                }
            }
        elif request_type == "service_request" and specialty == "allergy" and service == "allergy test":
            # Similar to Example 2
            response["required_context"] = {
                "insurance_id_card": {
                    "type": "document",
                    "present": True,
                    "validated": True,
                    "source": "user_documents_database",
                    "description": "Photo or scan of the user's active insurance card. Confirmed active with Anthem PPO, valid through 2026.",
                    "date_added": "2025-05-11",
                    "document_id": "doc_554abc"
                },
                "plan_coverage_info": {
                    "type": "document",
                    "present": True,
                    "validated": True,
                    "source": "user_documents_database",
                    "description": "Allergy testing is covered with no referral required under Anthem PPO plan.",
                    "date_added": "2025-05-13",
                    "document_id": "covcheck_00312"
                }
            }
        elif request_type == "policy_question" and specialty == "physical therapy":
            # Similar to Example 4
            response["required_context"] = {
                "insurance_id_card": {
                    "type": "document",
                    "present": True,
                    "validated": True,
                    "source": "user_documents_database",
                    "description": "Cigna HMO insurance card valid through 2025",
                    "date_added": "2025-05-12",
                    "document_id": "doc_4482x"
                },
                "plan_coverage_info": {
                    "type": "document",
                    "present": True,
                    "validated": True,
                    "source": "user_documents_database",
                    "description": "Plan allows up to 25 physical therapy visits per year.",
                    "date_added": "2025-05-13",
                    "document_id": "covcheck_0451"
                }
            }
        else:
            # Generic response for other cases - with missing documents
            response["required_context"] = {
                "insurance_id_card": {
                    "type": "document",
                    "present": None,
                    "validated": False,
                    "source": None,
                    "description": "Insurance ID card needed",
                    "date_added": None,
                    "document_id": None
                },
                "plan_coverage_info": {
                    "type": "document",
                    "present": None,
                    "validated": False,
                    "source": None,
                    "description": "Plan coverage information needed",
                    "date_added": None,
                    "document_id": None
                }
            }
        
        return response

def test_task_requirements_agent():
    """
    Test function for the Task Requirements Agent.
    
    This function loads test examples and runs them through the agent.
    """
    # Load test examples
    test_examples_path = "agents/task_requirements/tests/data/examples/test_examples_v0_1.md"
    
    try:
        with open(test_examples_path, 'r') as file:
            test_content = file.read()
    except FileNotFoundError:
        logger.error(f"Test examples file not found: {test_examples_path}")
        return
    
    # Extract test inputs using regex
    input_pattern = r'Input:\n```json\n(.*?)\n```'
    test_inputs = re.findall(input_pattern, test_content, re.DOTALL)
    
    if not test_inputs:
        logger.error("No test inputs found in the test examples file")
        return
    
    # Initialize the agent with mock database
    agent = TaskRequirementsReactAgent(use_mock_db=True)
    
    # Run each test input
    for i, input_json_str in enumerate(test_inputs):
        try:
            input_json = json.loads(input_json_str)
            logger.info(f"Running test {i+1} with input: {input_json['meta_intent']['summary']}")
            
            # Process the input
            result = agent.process(input_json)
            
            # Log the result
            logger.info(f"Test {i+1} result: {json.dumps(result, indent=2)}")
            print(f"Test {i+1} result: {json.dumps(result, indent=2)}")
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from test input {i+1}")
        except Exception as e:
            logger.error(f"Error processing test {i+1}: {str(e)}")
    
    logger.info("All tests completed")
    print("All tests completed")

if __name__ == "__main__":
    # Run the test function when the script is executed directly
    test_task_requirements_agent()
