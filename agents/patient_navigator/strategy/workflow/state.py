import logging
from typing import List, Optional
from datetime import datetime

from ..types import (
    StrategyWorkflowState, 
    PlanConstraints, 
    ContextRetrievalResult, 
    Strategy, 
    ValidationResult, 
    StorageResult
)

class StrategyWorkflowStateManager:
    """
    Workflow State Management for Strategy Generation
    
    Manages the state transitions in the workflow:
    1. Context Gathering → 2. Strategy Generation → 3. Regulatory Validation → 4. Storage
    """
    
    def __init__(self, initial_constraints: PlanConstraints):
        """
        Initialize the state manager with initial plan constraints.
        
        Args:
            initial_constraints: User's insurance plan constraints
        """
        self.state = StrategyWorkflowState(
            plan_constraints=initial_constraints,
            errors=[]
        )
        self.logger = logging.getLogger(__name__)
    
    def update_context_result(self, context_result: ContextRetrievalResult) -> None:
        """Update context gathering results."""
        self.state.context_result = context_result
        self.logger.debug(f"Updated context result with {len(context_result.web_search_results)} web results")
    
    def update_strategies(self, strategies: List[Strategy]) -> None:
        """Update generated strategies."""
        self.state.strategies = strategies
        self.logger.debug(f"Updated strategies with {len(strategies)} strategies")
    
    def update_validation_results(self, validation_results: List[ValidationResult]) -> None:
        """Update validation results."""
        self.state.validation_results = validation_results
        self.logger.debug(f"Updated validation results with {len(validation_results)} validations")
    
    def update_storage_confirmation(self, storage_confirmation: StorageResult) -> None:
        """Update storage confirmation."""
        self.state.storage_confirmation = storage_confirmation
        self.logger.debug(f"Updated storage confirmation: {storage_confirmation.storage_status}")
    
    def add_error(self, error: str) -> None:
        """Add error to state."""
        if not self.state.errors:
            self.state.errors = []
        self.state.errors.append(error)
        self.logger.error(f"Added error to state: {error}")
    
    def get_state(self) -> StrategyWorkflowState:
        """Get current state."""
        return self.state
    
    def has_errors(self) -> bool:
        """Check if workflow has errors."""
        return bool(self.state.errors and len(self.state.errors) > 0)
    
    def get_errors(self) -> List[str]:
        """Get all errors."""
        return self.state.errors or []
    
    def validate_state(self) -> bool:
        """Validate state completeness."""
        return (
            bool(self.state.plan_constraints) and
            bool(self.state.context_result) and
            bool(self.state.strategies) and
            bool(self.state.validation_results) and
            bool(self.state.storage_confirmation)
        )
    
    def get_state_summary(self) -> dict:
        """Get a summary of the current state for logging."""
        return {
            "has_context": bool(self.state.context_result),
            "context_results_count": len(self.state.context_result.web_search_results) if self.state.context_result else 0,
            "strategies_count": len(self.state.strategies) if self.state.strategies else 0,
            "validation_results_count": len(self.state.validation_results) if self.state.validation_results else 0,
            "has_storage_confirmation": bool(self.state.storage_confirmation),
            "errors_count": len(self.state.errors) if self.state.errors else 0,
            "is_complete": self.validate_state()
        } 