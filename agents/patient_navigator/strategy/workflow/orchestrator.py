import asyncio
import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..types import (
    PlanConstraints, 
    ContextRetrievalResult, 
    Strategy, 
    ValidationResult, 
    StorageResult,
    StrategyWorkflowState,
    WorkflowConfig
)
from ..workflow.state import StrategyWorkflowStateManager
from ..creator.agent import StrategyCreatorAgent
from ..regulatory.agent import RegulatoryAgent
from ..memory.workflow import StrategyMemoryLiteWorkflow
from agents.tooling.mcp.strategy.core import StrategyMCPTool

class StrategyWorkflowOrchestrator:
    """
    Strategy Evaluation & Validation System Workflow Orchestrator
    
    Implements the complete workflow: StrategyMCP → StrategyCreator → RegulatoryAgent → StrategyMemoryLiteWorkflow
    with dual mode operation (mock/real APIs) and comprehensive error handling.
    """
    
    def __init__(self, config: WorkflowConfig):
        """
        Initialize the workflow orchestrator.
        
        Args:
            config: Workflow configuration including mock mode and timeouts
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components with mock/real mode
        self.strategy_mcp = StrategyMCPTool(use_mock=config.use_mock)
        self.strategy_creator = StrategyCreatorAgent(use_mock=config.use_mock)
        self.regulatory_agent = RegulatoryAgent(use_mock=config.use_mock)
        self.strategy_memory = StrategyMemoryLiteWorkflow(use_mock=config.use_mock)
        
        # Performance tracking
        self.start_time: Optional[float] = None
        self.step_times: Dict[str, float] = {}
        
    async def execute_workflow(
        self, 
        plan_constraints: PlanConstraints
    ) -> StrategyWorkflowState:
        """
        Execute the complete strategy workflow.
        
        Args:
            plan_constraints: User's insurance plan constraints
            
        Returns:
            Complete workflow state with results and any errors
        """
        self.start_time = time.time()
        state_manager = StrategyWorkflowStateManager(plan_constraints)
        
        try:
            # Step 1: Context Gathering
            await self._execute_context_gathering(state_manager)
            
            # Step 2: Strategy Generation
            await self._execute_strategy_generation(state_manager)
            
            # Step 3: Regulatory Validation
            await self._execute_regulatory_validation(state_manager)
            
            # Step 4: Storage
            await self._execute_storage(state_manager)
            
        except Exception as error:
            self.logger.error(f"Workflow execution failed: {error}")
            state_manager.addError(f"Workflow execution failed: {str(error)}")
            
        finally:
            # Log performance metrics
            self._log_performance_metrics(state_manager)
            
        return state_manager.getState()
    
    async def _execute_context_gathering(
        self, 
        state_manager: StrategyWorkflowStateManager
    ) -> None:
        """Execute context gathering step with error handling."""
        step_start = time.time()
        
        try:
            self.logger.info("Starting context gathering...")
            
            context_result = await self.strategy_mcp.gather_context(
                plan_constraints=state_manager.getState().plan_constraints
            )
            
            state_manager.updateContextResult(context_result)
            self.logger.info(f"Context gathering completed: {len(context_result.web_search_results)} web results")
            
        except Exception as error:
            self.logger.error(f"Context gathering failed: {error}")
            state_manager.addError(f"Context gathering failed: {str(error)}")
            # Continue with empty context for graceful degradation
            
        finally:
            self.step_times['context_gathering'] = time.time() - step_start
    
    async def _execute_strategy_generation(
        self, 
        state_manager: StrategyWorkflowStateManager
    ) -> None:
        """Execute strategy generation step with error handling."""
        step_start = time.time()
        
        try:
            self.logger.info("Starting strategy generation...")
            
            state = state_manager.getState()
            if not state.context_result:
                raise ValueError("No context available for strategy generation")
            
            strategies = await self.strategy_creator.generate_strategies(
                context=state.context_result,
                plan_constraints=state.plan_constraints
            )
            
            if not strategies:
                raise ValueError("No strategies generated")
                
            state_manager.updateStrategies(strategies)
            self.logger.info(f"Strategy generation completed: {len(strategies)} strategies")
            
        except Exception as error:
            self.logger.error(f"Strategy generation failed: {error}")
            state_manager.addError(f"Strategy generation failed: {str(error)}")
            # Continue with empty strategies for graceful degradation
            
        finally:
            self.step_times['strategy_generation'] = time.time() - step_start
    
    async def _execute_regulatory_validation(
        self, 
        state_manager: StrategyWorkflowStateManager
    ) -> None:
        """Execute regulatory validation step with error handling."""
        step_start = time.time()
        
        try:
            self.logger.info("Starting regulatory validation...")
            
            state = state_manager.getState()
            if not state.strategies:
                raise ValueError("No strategies available for validation")
            
            validation_results = await self.regulatory_agent.validate_strategies(
                strategies=state.strategies
            )
            
            if not validation_results:
                raise ValueError("No validation results generated")
                
            state_manager.updateValidationResults(validation_results)
            self.logger.info(f"Regulatory validation completed: {len(validation_results)} validations")
            
        except Exception as error:
            self.logger.error(f"Regulatory validation failed: {error}")
            state_manager.addError(f"Regulatory validation failed: {str(error)}")
            # Continue with empty validations for graceful degradation
            
        finally:
            self.step_times['regulatory_validation'] = time.time() - step_start
    
    async def _execute_storage(
        self, 
        state_manager: StrategyWorkflowStateManager
    ) -> None:
        """Execute storage step with error handling."""
        step_start = time.time()
        
        try:
            self.logger.info("Starting strategy storage...")
            
            state = state_manager.getState()
            if not state.strategies or not state.validation_results:
                raise ValueError("No strategies or validation results available for storage")
            
            # Filter strategies that passed validation
            validated_strategies = [
                strategy for strategy in state.strategies
                if any(vr.strategy_id == strategy.id and vr.compliance_status == 'approved' 
                      for vr in state.validation_results)
            ]
            
            if not validated_strategies:
                self.logger.warning("No strategies passed validation")
                storage_result = StorageResult(
                    strategy_id="none",
                    storage_status="failed",
                    message="No strategies passed validation",
                    timestamp=datetime.now()
                )
            else:
                storage_results = await self.strategy_memory.store_strategies(
                    strategies=validated_strategies
                )
                storage_result = storage_results[0] if storage_results else StorageResult(
                    strategy_id="none",
                    storage_status="failed",
                    message="Storage operation failed",
                    timestamp=datetime.now()
                )
            
            state_manager.updateStorageConfirmation(storage_result)
            self.logger.info(f"Strategy storage completed: {storage_result.storage_status}")
            
        except Exception as error:
            self.logger.error(f"Strategy storage failed: {error}")
            state_manager.addError(f"Strategy storage failed: {str(error)}")
            
        finally:
            self.step_times['storage'] = time.time() - step_start
    
    def _log_performance_metrics(self, state_manager: StrategyWorkflowStateManager) -> None:
        """Log performance metrics for the workflow execution."""
        if not self.start_time:
            return
            
        total_time = time.time() - self.start_time
        
        self.logger.info("=== Workflow Performance Metrics ===")
        self.logger.info(f"Total execution time: {total_time:.2f}s")
        
        for step, step_time in self.step_times.items():
            self.logger.info(f"{step}: {step_time:.2f}s")
        
        # Check if we met the 30-second target
        if total_time > self.config.timeout_seconds:
            self.logger.warning(f"Workflow exceeded {self.config.timeout_seconds}s target: {total_time:.2f}s")
        else:
            self.logger.info(f"Workflow completed within {self.config.timeout_seconds}s target")
        
        # Log any errors
        if state_manager.hasErrors():
            self.logger.error(f"Workflow completed with {len(state_manager.getErrors())} errors")
            for error in state_manager.getErrors():
                self.logger.error(f"  - {error}")
        
        self.logger.info("=== End Performance Metrics ===")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for monitoring."""
        if not self.start_time:
            return {}
            
        total_time = time.time() - self.start_time
        
        return {
            "total_time": total_time,
            "step_times": self.step_times,
            "within_target": total_time <= self.config.timeout_seconds,
            "target_timeout": self.config.timeout_seconds
        } 