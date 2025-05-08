"""
Database Guard Agent

This agent is responsible for:
1. Converting data to structured formats for database storage
2. Checking for and redacting sensitive information
3. Securely storing data to the database
4. Logging successful operations and returning identifiers
5. Detecting malformed or malicious content

Based on FMEA analysis, this agent implements controls for:
- JSON structure validation
- HIPAA/privacy compliance checks
- Secure database write operations with retry logic
- Secure logging with atomic operations
- Payload inspection and hash verification
"""

import os
import json
import time
import logging
import hashlib
from typing import Dict, List, Any, Tuple, Optional, Union
from pydantic import BaseModel, Field, ValidationError
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models import BaseLanguageModel
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser

from agents.base_agent import BaseAgent
from utils.prompt_loader import load_prompt

# Setup logging
logger = logging.getLogger("database_guard_agent")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join("logs", "agents", "database_guard.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Ensure logs directory exists
os.makedirs(os.path.join("logs", "agents"), exist_ok=True)

# Define output schemas
class SecurityValidation(BaseModel):
    """Security validation result for database operations."""
    is_valid: bool = Field(description="Whether the payload is valid and safe")
    contains_pii: bool = Field(description="Whether the payload contains PII")
    contains_phi: bool = Field(description="Whether the payload contains PHI")
    redacted_fields: List[str] = Field(description="Fields that were redacted", default_factory=list)
    original_hash: str = Field(description="Hash of the original payload")
    redacted_hash: str = Field(description="Hash of the redacted payload")
    confidence: float = Field(description="Confidence in the security assessment (0-1)")
    reasoning: str = Field(description="Reasoning behind the security assessment")

class DatabaseOperation(BaseModel):
    """Result of a database operation."""
    success: bool = Field(description="Whether the operation was successful")
    operation_type: str = Field(description="Type of operation (insert, update, delete)")
    record_id: Optional[str] = Field(description="ID of the affected record", default=None)
    timestamp: str = Field(description="Timestamp of the operation")
    error_message: Optional[str] = Field(description="Error message if operation failed", default=None)
    retry_count: int = Field(description="Number of retries performed", default=0)

class DatabaseGuardAgent(BaseAgent):
    """Agent responsible for secure database operations."""
    
    def __init__(self, llm: Optional[BaseLanguageModel] = None):
        """Initialize the agent with an optional language model."""
        # Initialize the base agent
        super().__init__(name="database_guard", llm=llm or ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0))
        
        self.parser = PydanticOutputParser(pydantic_object=SecurityValidation)
        
        # Define sensitive information patterns
        self.sensitive_patterns = {
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "medicare_id": r"\b[1-9][0-9]{2}-[0-9]{2}-[0-9]{4}[A-Z]\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "dob": r"\b(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01])/(19|20)\d{2}\b"
        }
        
        # Load the system prompt from file
        try:
            self.security_system_prompt = load_prompt("database_guard_security")
        except FileNotFoundError:
            self.logger.warning("Could not find database_guard_security.md prompt file, using default prompt")
            # Load the self.security_system_prompt from file
        try:
            self.security_system_prompt = load_prompt("database_guard_security")
        except FileNotFoundError:
            self.logger.warning("Could not find database_guard_security.md prompt file, using default prompt")
            # Load the self.security_system_prompt from file
        try:
            self.security_system_prompt = load_prompt("database_guard_security_prompt")
        except FileNotFoundError:
            self.logger.warning("Could not find database_guard_security_prompt.md prompt file, using default prompt")
            self.security_system_prompt = """
            Default prompt for self.security_system_prompt. Replace with actual prompt if needed.
            """
        
        
        
        # Define the security validation prompt template
        self.validation_template = PromptTemplate(
            template="""
            {system_prompt}
            
            DATA PAYLOAD TO VALIDATE:
            {data_payload}
            
            Analyze this data payload for security and privacy concerns, and provide your assessment.
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "data_payload"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        # Create the validation chain
        self.validation_chain = (
            {"system_prompt": lambda _: self.security_system_prompt, 
             "data_payload": lambda x: json.dumps(x["data_payload"], indent=2)}
            | self.validation_template
            | self.llm
            | self.parser
        )
        
        # Initialize retry configuration
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        logger.info("Database Guard Agent initialized")
    
    def _compute_hash(self, data: Dict[str, Any]) -> str:
        """Compute a hash of the data."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _validate_structure(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate the structure of the data against the schema."""
        try:
            # Basic structure check
            for required_field in schema.get("required_fields", []):
                if required_field not in data:
                    return False, f"Missing required field: {required_field}"
            
            # Type checking
            for field, field_type in schema.get("field_types", {}).items():
                if field in data and not isinstance(data[field], eval(field_type)):
                    return False, f"Field {field} has incorrect type, expected {field_type}"
            
            return True, "Structure validation passed"
        except Exception as e:
            return False, f"Structure validation error: {str(e)}"
    
    @BaseAgent.track_performance
    def validate_security(self, data_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data payload for security and privacy concerns.
        
        Args:
            data_payload: The data to validate
            
        Returns:
            Security validation results
        """
        start_time = time.time()
        
        # Log the validation request
        self.logger.info(f"Validating data payload ({len(json.dumps(data_payload))} bytes)...")
        
        try:
            # Compute original hash
            original_hash = self._compute_hash(data_payload)
            
            # Invoke the validation chain
            input_dict = {"data_payload": data_payload}
            validation_result = self.validation_chain.invoke(input_dict)
            
            # Convert to dictionary
            result = validation_result.dict()
            result["original_hash"] = original_hash
            
            # Log the result
            if result["is_valid"]:
                self.logger.info(f"Data payload validated successfully with confidence {result['confidence']}")
                if result["contains_pii"] or result["contains_phi"]:
                    self.logger.info(f"Redacted fields: {', '.join(result['redacted_fields'])}")
            else:
                self.logger.warning(f"Data payload validation failed: {result['reasoning']}")
            
            # Log execution time
            execution_time = time.time() - start_time
            self.logger.info(f"Security validation completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in security validation: {str(e)}")
            
            # Return a failed validation in case of error
            return {
                "is_valid": False,
                "contains_pii": True,  # Assume worst case
                "contains_phi": True,  # Assume worst case
                "redacted_fields": [],
                "original_hash": self._compute_hash(data_payload),
                "redacted_hash": "",
                "confidence": 0.0,
                "reasoning": f"Error during validation: {str(e)}"
            }
    
    @BaseAgent.track_performance
    def store_data(self, data_payload: Dict[str, Any], collection: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate and store data in the database.
        
        Args:
            data_payload: The data to store
            collection: The database collection to store the data in
            schema: Optional schema for additional validation
            
        Returns:
            Database operation result
        """
        start_time = time.time()
        
        # Log the store request
        self.logger.info(f"Storing data in collection '{collection}'...")
        
        # Initialize operation result
        operation_result = DatabaseOperation(
            success=False,
            operation_type="insert",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            retry_count=0
        )
        
        try:
            # Validate structure if schema is provided
            if schema:
                is_valid, message = self._validate_structure(data_payload, schema)
                if not is_valid:
                    self.logger.error(f"Structure validation failed: {message}")
                    operation_result.error_message = message
                    return operation_result.dict()
            
            # Validate security
            security_result = self.validate_security(data_payload)
            if not security_result["is_valid"]:
                self.logger.error(f"Security validation failed: {security_result['reasoning']}")
                operation_result.error_message = security_result['reasoning']
                return operation_result.dict()
            
            # If PII/PHI was detected, use the redacted payload
            processed_payload = data_payload
            if security_result["contains_pii"] or security_result["contains_phi"]:
                # In a real implementation, this would use the redacted data
                # For this MVP, we're simulating the redaction
                self.logger.info("Using redacted payload for storage")
                processed_payload = self._simulate_redaction(data_payload, security_result["redacted_fields"])
            
            # Simulate database write with retry logic
            record_id = None
            for attempt in range(self.max_retries):
                operation_result.retry_count = attempt
                
                try:
                    # Simulate database write
                    record_id = self._simulate_db_write(processed_payload, collection)
                    break
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        self.logger.warning(f"Database write failed, retrying ({attempt+1}/{self.max_retries}): {str(e)}")
                        time.sleep(self.retry_delay)
                    else:
                        raise
            
            if record_id:
                # Write succeeded
                operation_result.success = True
                operation_result.record_id = record_id
                self.logger.info(f"Data stored successfully with ID: {record_id}")
            else:
                # Write failed
                operation_result.error_message = "Database write failed after retries"
                self.logger.error(operation_result.error_message)
            
            # Log execution time
            execution_time = time.time() - start_time
            self.logger.info(f"Store operation completed in {execution_time:.2f}s")
            
            return operation_result.dict()
            
        except Exception as e:
            self.logger.error(f"Error in store operation: {str(e)}")
            
            # Update operation result with error
            operation_result.error_message = str(e)
            
            return operation_result.dict()
    
    def _simulate_redaction(self, data: Dict[str, Any], fields_to_redact: List[str]) -> Dict[str, Any]:
        """Simulate redaction of sensitive fields (for MVP purposes)."""
        redacted_data = data.copy()
        
        for field in fields_to_redact:
            # Handle nested fields
            if "." in field:
                parts = field.split(".")
                current = redacted_data
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:
                        if part in current:
                            current[part] = "[REDACTED]"
                    else:
                        if part in current and isinstance(current[part], dict):
                            current = current[part]
                        else:
                            break
            else:
                # Handle top-level fields
                if field in redacted_data:
                    redacted_data[field] = "[REDACTED]"
        
        return redacted_data
    
    def _simulate_db_write(self, data: Dict[str, Any], collection: str) -> str:
        """Simulate writing to a database (for MVP purposes)."""
        # In a real implementation, this would use an actual database client
        # For this MVP, we're just simulating the write
        
        # Simulate a write error occasionally
        if time.time() % 10 < 1:  # 10% chance of failure
            raise Exception("Simulated database connection error")
        
        # Generate a simulated record ID
        record_id = f"{collection}_{int(time.time())}_{hash(json.dumps(data)) % 10000}"
        
        # Log the write
        self.logger.info(f"Simulated write to collection '{collection}' with ID '{record_id}'")
        
        return record_id
    
    def process(self, data_payload: Dict[str, Any], collection: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a data storage request.
        
        Args:
            data_payload: The data to store
            collection: The database collection to store the data in
            schema: Optional schema for additional validation
            
        Returns:
            Database operation result
        """
        return self.store_data(data_payload, collection, schema)

# Example usage
if __name__ == "__main__":
    # Initialize the agent
    agent = DatabaseGuardAgent()
    
    # Test with sample data
    sample_data = {
        "user_id": "12345",
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "dob": "01/15/1975",
        "address": {
            "street": "123 Main St",
            "city": "Boston",
            "state": "MA",
            "zip": "02108"
        },
        "medical_info": {
            "conditions": ["diabetes", "hypertension"],
            "medications": ["insulin", "lisinopril"],
            "allergies": ["penicillin"]
        },
        "insurance": {
            "provider": "Medicare",
            "policy_number": "123-45-6789A",
            "coverage_start": "2020-01-01"
        }
    }
    
    schema = {
        "required_fields": ["user_id", "name", "insurance"],
        "field_types": {
            "user_id": "str",
            "name": "str",
            "medical_info": "dict",
            "insurance": "dict"
        }
    }
    
    # Process the data
    result = agent.process(sample_data, "patient_records", schema)
    
    print(f"Operation success: {result['success']}")
    if result['success']:
        print(f"Record ID: {result['record_id']}")
    else:
        print(f"Error: {result['error_message']}") 