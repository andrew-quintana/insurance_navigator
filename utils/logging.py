import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
AGENT_LOGS_DIR = LOGS_DIR / "agents"
PROMPT_LOGS_DIR = LOGS_DIR / "prompts"

for directory in [LOGS_DIR, AGENT_LOGS_DIR, PROMPT_LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

class StructuredLogger:
    def __init__(self, name: str, log_dir: Path):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
    
    def log(self, level: int, message: str, **kwargs):
        """Log a message with structured data."""
        log_data = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.logger.log(level, json.dumps(log_data))

class AgentLogger(StructuredLogger):
    def __init__(self, agent_name: str):
        super().__init__(f"agent_{agent_name}", AGENT_LOGS_DIR)
    
    def log_interaction(
        self,
        input_text: str,
        response: str,
        tools_used: Optional[list] = None,
        state: Optional[Dict[str, Any]] = None
    ):
        """Log an agent interaction."""
        self.log(
            logging.INFO,
            "Agent interaction",
            input=input_text,
            response=response,
            tools_used=tools_used,
            state=state
        )
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log an agent error."""
        self.log(
            logging.ERROR,
            str(error),
            error_type=type(error).__name__,
            context=context
        )

class PromptLogger(StructuredLogger):
    def __init__(self, prompt_name: str):
        super().__init__(f"prompt_{prompt_name}", PROMPT_LOGS_DIR)
    
    def log_prompt(
        self,
        prompt_template: str,
        variables: Dict[str, Any],
        response: Optional[str] = None
    ):
        """Log a prompt execution."""
        self.log(
            logging.INFO,
            "Prompt execution",
            template=prompt_template,
            variables=variables,
            response=response
        )
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log a prompt error."""
        self.log(
            logging.ERROR,
            str(error),
            error_type=type(error).__name__,
            context=context
        ) 