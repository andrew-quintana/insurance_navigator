import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..types import Strategy, StorageResult
from ..workflow.database_integration import DatabaseIntegration

class StrategyMemoryLiteWorkflow:
    """
    StrategyMemoryLite Workflow - Buffer-based strategy storage and retrieval
    
    Implements agent-orchestrated flow with buffer → commit pattern:
    1. Strategy Generator produces 4 strategy variants
    2. Regulatory Agent evaluates each strategy for feasibility
    3. Validated strategies are emitted as markdown with metadata
    4. Strategy ingestion service logs markdown into strategies_buffer
    5. Valid entries are committed to strategies table
    6. Markdown content is passed to embedding pipeline
    7. Embeddings are stored via strategy_vector_buffer → strategy_vectors
    """
    
    def __init__(self, use_mock: bool = False):
        """
        Initialize the Strategy Memory Lite Workflow.
        
        Args:
            use_mock: If True, use mock database operations
        """
        self.use_mock = use_mock
        self.logger = logging.getLogger(__name__)
        
        # Initialize database integration
        self.database_integration = DatabaseIntegration(use_mock=use_mock)
        
        # Performance tracking
        self.storage_times: List[float] = []
        self.retrieval_times: List[float] = []
    
    async def store_strategies(
        self,
        strategies: List[Strategy]
    ) -> List[StorageResult]:
        """
        Store strategies using buffer-based workflow.
        
        Args:
            strategies: List of strategies to store
            
        Returns:
            List of storage results for each strategy
        """
        if not strategies:
            self.logger.warning("No strategies provided for storage")
            return []
        
        self.logger.info(f"Starting storage of {len(strategies)} strategies")
        start_time = datetime.now()
        
        try:
            # Use database integration for buffer-based storage
            storage_results = await self.database_integration.store_strategies_with_buffer_workflow(strategies)
            
            # Track performance
            duration = (datetime.now() - start_time).total_seconds()
            self.storage_times.append(duration)
            
            # Log results
            successful_storage = sum(1 for result in storage_results if result.storage_status == "success")
            self.logger.info(f"Storage completed: {successful_storage}/{len(strategies)} strategies stored successfully in {duration:.2f}s")
            
            return storage_results
            
        except Exception as error:
            self.logger.error(f"Strategy storage failed: {error}")
            
            # Return failure results for all strategies
            return [
                StorageResult(
                    strategy_id=strategy.id,
                    storage_status="failed",
                    message=f"Storage failed: {str(error)}",
                    timestamp=datetime.now()
                )
                for strategy in strategies
            ]

    async def retrieve_strategies(
        self,
        plan_constraints: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve strategies using constraint-based filtering and vector similarity.
        
        Args:
            plan_constraints: Plan constraints for filtering
            limit: Maximum number of strategies to retrieve
            
        Returns:
            List of retrieved strategies
        """
        self.logger.info(f"Starting strategy retrieval with limit {limit}")
        start_time = datetime.now()
        
        try:
            # Use database integration for retrieval
            strategies = await self.database_integration.retrieve_strategies(plan_constraints, limit)
            
            # Track performance
            duration = (datetime.now() - start_time).total_seconds()
            self.retrieval_times.append(duration)
            
            self.logger.info(f"Retrieval completed: {len(strategies)} strategies retrieved in {duration:.2f}s")
            
            return strategies
            
        except Exception as error:
            self.logger.error(f"Strategy retrieval failed: {error}")
            return []

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for storage and retrieval operations."""
        return {
            "storage_operations": len(self.storage_times),
            "retrieval_operations": len(self.retrieval_times),
            "avg_storage_time": sum(self.storage_times) / len(self.storage_times) if self.storage_times else 0,
            "avg_retrieval_time": sum(self.retrieval_times) / len(self.retrieval_times) if self.retrieval_times else 0,
            "using_mock": self.use_mock
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of the memory workflow."""
        return {
            "using_mock": self.use_mock,
            "database_status": self.database_integration.get_database_status(),
            "performance_metrics": self.get_performance_metrics()
        } 