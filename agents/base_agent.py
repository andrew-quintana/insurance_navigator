import os
import logging
from typing import Any, Callable, Optional, Type, Dict
from pydantic import BaseModel, ValidationError

class BaseAgent:
    """
    BaseAgent for LangGraph-based agent nodes (no LangChain dependency).

    - Callable: implements __call__(user_input, **kwargs)
    - Prompt, output_schema, and llm (callable or None) are required.
    - Validates output using the provided Pydantic schema.
    - Designed for stateless, single-step agent logic (not orchestration).
    - Subclass for custom logic or prompt formatting.
    """
    def __init__(
        self,
        name: str,
        prompt: str,
        output_schema: Type[BaseModel],
        llm: Optional[Callable[[str], Any]] = None,
        mock: bool = False,
        examples: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        db_manager: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Args:
            name: Agent name (for logging/identification)
            prompt: Prompt template (string or path to file)
            output_schema: Pydantic BaseModel subclass for output validation
            llm: Callable that takes a prompt and returns a string (or dict)
            mock: If True, always return mock output
            examples: Optional examples (string or path)
            logger: Optional logger (defaults to stdlib logger)
            db_manager: Database manager instance for data operations
            config: Configuration dictionary for agent settings
        """
        self.name = name
        self.prompt = self._load_if_path(prompt)
        self.output_schema = output_schema
        self.llm = llm
        self.mock = mock
        self.examples = self._load_if_path(examples) if examples else None
        self.logger = logger or logging.getLogger(f"agent.{name}")
        self.db_manager = db_manager
        self.config = config or {}

    def _load_if_path(self, value: Optional[str]) -> Optional[str]:
        if value and os.path.isfile(value):
            with open(value, "r", encoding="utf-8") as f:
                return f.read()
        return value

    def format_prompt(self, user_input: str, **kwargs) -> str:
        """
        Format the prompt with user input and optional examples.
        Subclass to customize prompt composition.
        """
        prompt = self.prompt
        # Insert examples if present
        if self.examples:
            prompt = prompt.replace("{{examples}}", self.examples)
        # Insert user input
        prompt = prompt.replace("{{input}}", user_input)
        # Allow additional formatting via kwargs
        if kwargs:
            try:
                prompt = prompt.format(**kwargs)
            except Exception:
                pass  # Ignore formatting errors for extra keys
        return prompt

    def validate_output(self, output: Any) -> BaseModel:
        """
        Validate and parse output using the Pydantic schema.
        Subclass to customize validation/parsing.
        """
        if isinstance(output, self.output_schema):
            return output
        try:
            if isinstance(output, dict):
                return self.output_schema.model_validate(output)
            elif isinstance(output, str):
                return self.output_schema.model_validate_json(output)
            else:
                raise TypeError(f"Unsupported output type: {type(output)}")
        except ValidationError as e:
            self.logger.error(f"[{self.name}] Output validation failed: {e}")
            raise

    def mock_output(self, user_input: str) -> BaseModel:
        """
        Generate a mock output matching the schema (for testing).
        Subclass for more realistic mocks.
        """
        # Minimal mock: fill all fields with placeholder values
        fields = self.output_schema.model_fields
        mock_data = {k: f"mock_{k}" for k in fields}
        return self.output_schema.model_validate(mock_data)

    def __call__(self, user_input: str, **kwargs) -> BaseModel:
        """
        Run the agent: format prompt, call LLM (or mock), validate output.
        """
        prompt = self.format_prompt(user_input, **kwargs)
        self.logger.info(f"[{self.name}] Running agent with input: {user_input[:80]}")
        if self.mock or self.llm is None:
            self.logger.info(f"[{self.name}] Using mock output mode.")
            output = self.mock_output(user_input)
        else:
            try:
                llm_result = self.llm(prompt)
                output = self.validate_output(llm_result)
            except Exception as e:
                self.logger.error(f"[{self.name}] LLM call or validation failed: {e}")
                raise
        self.logger.info(f"[{self.name}] Agent completed successfully.")
        return output

    # Extension point: override for custom LLM call logic
    def call_llm(self, prompt: str) -> Any:
        if self.llm is None:
            raise RuntimeError("No LLM provided.")
        return self.llm(prompt)

    # Extension point: override for custom logging
    def log(self, message: str, level: int = logging.INFO):
        self.logger.log(level, f"[{self.name}] {message}")
    
    # Dependency injection support methods
    async def initialize(self) -> None:
        """Initialize the agent with injected dependencies."""
        self.logger.info(f"Initializing agent: {self.name}")
        # Override in subclasses for custom initialization
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the agent."""
        try:
            # Basic health check - override in subclasses for specific checks
            return {
                "status": "healthy",
                "agent_name": self.name,
                "mock_mode": self.mock,
                "has_llm": self.llm is not None,
                "has_db_manager": self.db_manager is not None
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_name": self.name,
                "error": str(e)
            }
    
    async def shutdown(self) -> None:
        """Shutdown the agent and cleanup resources."""
        self.logger.info(f"Shutting down agent: {self.name}")
        # Override in subclasses for custom shutdown logic
        pass 