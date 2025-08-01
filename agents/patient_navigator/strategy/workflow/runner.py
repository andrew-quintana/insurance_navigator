import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..types import PlanConstraints, WorkflowConfig, StrategyWorkflowState
from .orchestrator import StrategyWorkflowOrchestrator
from .llm_integration import LLMIntegration
from .database_integration import DatabaseIntegration

class StrategyWorkflowRunner:
    """
    Strategy Workflow Runner
    
    Provides a simple interface to execute the complete strategy workflow
    with configuration options for mock/real APIs and comprehensive logging.
    """
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        """
        Initialize the workflow runner.
        
        Args:
            config: Workflow configuration (defaults to production config)
        """
        self.config = config or WorkflowConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.orchestrator = StrategyWorkflowOrchestrator(self.config)
        self.llm_integration = LLMIntegration(use_mock=self.config.use_mock)
        self.database_integration = DatabaseIntegration(use_mock=self.config.use_mock)
        
        # Setup logging
        if self.config.enable_logging:
            self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup structured logging for the workflow."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Set specific log levels
        logging.getLogger('agents.patient_navigator.strategy').setLevel(logging.INFO)
        logging.getLogger('agents.tooling.mcp.strategy').setLevel(logging.INFO)
    
    async def run_workflow(
        self,
        plan_constraints: PlanConstraints
    ) -> StrategyWorkflowState:
        """
        Run the complete strategy workflow.
        
        Args:
            plan_constraints: User's insurance plan constraints
            
        Returns:
            Complete workflow state with results and any errors
        """
        start_time = datetime.now()
        self.logger.info(f"Starting strategy workflow at {start_time}")
        self.logger.info(f"Configuration: mock={self.config.use_mock}, timeout={self.config.timeout_seconds}s")
        
        try:
            # Execute workflow
            workflow_state = await self.orchestrator.execute_workflow(plan_constraints)
            
            # Log results
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info(f"Workflow completed in {duration:.2f}s")
            self._log_workflow_summary(workflow_state, duration)
            
            return workflow_state
            
        except Exception as error:
            self.logger.error(f"Workflow execution failed: {error}")
            raise
    
    def _log_workflow_summary(
        self,
        workflow_state: StrategyWorkflowState,
        duration: float
    ) -> None:
        """Log a summary of the workflow execution."""
        summary = {
            "duration_seconds": duration,
            "within_timeout": duration <= self.config.timeout_seconds,
            "has_errors": workflow_state.errors is not None and len(workflow_state.errors) > 0,
            "error_count": len(workflow_state.errors) if workflow_state.errors else 0,
            "strategies_generated": len(workflow_state.strategies) if workflow_state.strategies else 0,
            "strategies_validated": len(workflow_state.validation_results) if workflow_state.validation_results else 0,
            "storage_success": workflow_state.storage_confirmation and workflow_state.storage_confirmation.storage_status == "success"
        }
        
        self.logger.info("=== Workflow Summary ===")
        for key, value in summary.items():
            self.logger.info(f"{key}: {value}")
        
        if workflow_state.errors:
            self.logger.error("=== Workflow Errors ===")
            for error in workflow_state.errors:
                self.logger.error(f"  - {error}")
        
        self.logger.info("=== End Summary ===")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all system components."""
        return {
            "workflow_config": {
                "use_mock": self.config.use_mock,
                "timeout_seconds": self.config.timeout_seconds,
                "max_retries": self.config.max_retries,
                "enable_logging": self.config.enable_logging,
                "enable_audit_trail": self.config.enable_audit_trail
            },
            "llm_integration": self.llm_integration.get_rate_limit_status(),
            "database_integration": self.database_integration.get_database_status(),
            "orchestrator_performance": self.orchestrator.get_performance_summary()
        }
    
    async def test_workflow_with_mocks(self) -> StrategyWorkflowState:
        """
        Test the workflow with mock data and mock APIs.
        
        Returns:
            Workflow state from test execution
        """
        self.logger.info("Running workflow test with mock data and APIs")
        
        # Create test plan constraints
        test_constraints = PlanConstraints(
            copay=25,
            deductible=1000,
            network_providers=["Provider A", "Provider B"],
            geographic_scope="California",
            specialty_access=["Cardiology", "Orthopedics"]
        )
        
        # Create test config with mocks enabled
        test_config = WorkflowConfig(
            use_mock=True,
            timeout_seconds=30,
            enable_logging=True
        )
        
        # Create test runner
        test_runner = StrategyWorkflowRunner(test_config)
        
        # Run test workflow
        return await test_runner.run_workflow(test_constraints)
    
    async def validate_workflow_components(self) -> Dict[str, bool]:
        """
        Validate that all workflow components are properly configured.
        
        Returns:
            Dictionary of component validation results
        """
        validation_results = {}
        
        try:
            # Test LLM integration
            test_prompt = "Test prompt for validation"
            response = await self.llm_integration.generate_completion(test_prompt)
            validation_results["llm_integration"] = bool(response)
        except Exception as error:
            self.logger.error(f"LLM integration validation failed: {error}")
            validation_results["llm_integration"] = False
        
        try:
            # Test database integration
            status = self.database_integration.get_database_status()
            validation_results["database_integration"] = status["connection_status"] in ["connected", "mock"]
        except Exception as error:
            self.logger.error(f"Database integration validation failed: {error}")
            validation_results["database_integration"] = False
        
        try:
            # Test orchestrator
            validation_results["orchestrator"] = self.orchestrator is not None
        except Exception as error:
            self.logger.error(f"Orchestrator validation failed: {error}")
            validation_results["orchestrator"] = False
        
        return validation_results


# Convenience function for easy workflow execution
async def run_strategy_workflow(
    plan_constraints: PlanConstraints,
    use_mock: bool = False,
    timeout_seconds: int = 30
) -> StrategyWorkflowState:
    """
    Convenience function to run the strategy workflow.
    
    Args:
        plan_constraints: User's insurance plan constraints
        use_mock: If True, use mock APIs instead of real ones
        timeout_seconds: Maximum execution time in seconds
        
    Returns:
        Complete workflow state with results
    """
    config = WorkflowConfig(
        use_mock=use_mock,
        timeout_seconds=timeout_seconds,
        enable_logging=True
    )
    
    runner = StrategyWorkflowRunner(config)
    return await runner.run_workflow(plan_constraints) 