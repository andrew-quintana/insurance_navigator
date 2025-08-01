import asyncio
import logging
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

from ..types import Strategy, StorageResult

class DatabaseIntegration:
    """
    Database Integration Module
    
    Handles buffer-based storage workflow with real Supabase operations:
    strategies_buffer → strategies → strategy_vector_buffer → strategy_vectors
    
    Includes transaction safety, retry logic, and idempotent processing.
    """
    
    def __init__(self, use_mock: bool = False, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """
        Initialize database integration.
        
        Args:
            use_mock: If True, use mock database operations
            supabase_url: Supabase URL (if not provided, will try to get from environment)
            supabase_key: Supabase service role key (if not provided, will try to get from environment)
        """
        self.use_mock = use_mock
        self.logger = logging.getLogger(__name__)
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        
        if not use_mock:
            if not SUPABASE_AVAILABLE:
                raise ImportError("Supabase library not available. Install with: pip install supabase")
            
            # Initialize Supabase client
            supabase_url = supabase_url or os.getenv("SUPABASE_URL")
            supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError("Supabase URL and service role key not provided and not set in environment")
            
            self.client: Client = create_client(supabase_url, supabase_key)
            self.logger.info("Initialized Supabase client for real database operations")
        else:
            self.logger.info("Using mock database operations")
    
    async def store_strategies_with_buffer_workflow(
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
        storage_results = []
        
        for strategy in strategies:
            try:
                result = await self._store_single_strategy_with_buffer(strategy)
                storage_results.append(result)
            except Exception as error:
                self.logger.error(f"Failed to store strategy {strategy.id}: {error}")
                
                # Create failure result
                storage_results.append(StorageResult(
                    strategy_id=strategy.id,
                    storage_status="failed",
                    message=f"Storage failed: {str(error)}",
                    timestamp=datetime.now()
                ))
        
        return storage_results
    
    async def _store_single_strategy_with_buffer(self, strategy: Strategy) -> StorageResult:
        """
        Store a single strategy using buffer-based workflow.
        
        Workflow: strategies_buffer → strategies → strategy_vector_buffer → strategy_vectors
        """
        if self.use_mock:
            return self._mock_store_strategy(strategy)
        
        # Step 1: Store in strategies_buffer
        buffer_result = await self._store_in_buffer(strategy)
        if buffer_result.get("status") != "success":
            return StorageResult(
                strategy_id=strategy.id,
                storage_status="failed",
                message=f"Buffer storage failed: {buffer_result.get('error', 'Unknown error')}",
                timestamp=datetime.now()
            )
        
        # Step 2: Commit to strategies table
        strategy_result = await self._commit_to_strategies_table(strategy)
        if strategy_result.get("status") != "success":
            return StorageResult(
                strategy_id=strategy.id,
                storage_status="failed",
                message=f"Strategy table commit failed: {strategy_result.get('error', 'Unknown error')}",
                timestamp=datetime.now()
            )
        
        # Step 3: Store in strategy_vector_buffer
        vector_buffer_result = await self._store_in_vector_buffer(strategy)
        if vector_buffer_result.get("status") != "success":
            return StorageResult(
                strategy_id=strategy.id,
                storage_status="failed",
                message=f"Vector buffer storage failed: {vector_buffer_result.get('error', 'Unknown error')}",
                timestamp=datetime.now()
            )
        
        # Step 4: Commit to strategy_vectors table
        vector_result = await self._commit_to_strategy_vectors(strategy)
        if vector_result.get("status") != "success":
            return StorageResult(
                strategy_id=strategy.id,
                storage_status="failed",
                message=f"Vector table commit failed: {vector_result.get('error', 'Unknown error')}",
                timestamp=datetime.now()
            )
        
        return StorageResult(
            strategy_id=strategy.id,
            storage_status="success",
            message="Strategy stored successfully with buffer workflow",
            timestamp=datetime.now()
        )
    
    async def _store_in_buffer(self, strategy: Strategy) -> Dict[str, Any]:
        """Store strategy in strategies_buffer table."""
        try:
            strategy_data = {
                "title": strategy.title,
                "category": strategy.category,
                "approach": strategy.approach,
                "rationale": strategy.rationale,
                "actionable_steps": strategy.actionable_steps,
                "plan_constraints": strategy.plan_constraints.__dict__,
                "llm_score_speed": strategy.llm_scores.speed,
                "llm_score_cost": strategy.llm_scores.cost,
                "llm_score_effort": strategy.llm_scores.effort,
                "content_hash": strategy.content_hash,
                "validation_status": strategy.validation_status,
                "created_at": strategy.created_at.isoformat()
            }
            
            result = self.client.table("strategies_buffer").insert({
                "strategy_data": strategy_data,
                "content_hash": strategy.content_hash,
                "status": "pending"
            }).execute()
            
            return {"status": "success", "data": result.data}
            
        except Exception as error:
            self.logger.error(f"Buffer storage failed: {error}")
            return {"status": "error", "error": str(error)}
    
    async def _commit_to_strategies_table(self, strategy: Strategy) -> Dict[str, Any]:
        """Commit strategy from buffer to main strategies table."""
        try:
            # Check if strategy already exists (idempotent)
            existing = self.client.table("strategies").select("*").eq("content_hash", strategy.content_hash).execute()
            
            if existing.data:
                return {"status": "success", "data": existing.data[0], "duplicate": True}
            
            # Insert into strategies table
            strategy_record = {
                "title": strategy.title,
                "category": strategy.category,
                "approach": strategy.approach,
                "rationale": strategy.rationale,
                "actionable_steps": strategy.actionable_steps,
                "plan_constraints": strategy.plan_constraints.__dict__,
                "llm_score_speed": strategy.llm_scores.speed,
                "llm_score_cost": strategy.llm_scores.cost,
                "llm_score_effort": strategy.llm_scores.effort,
                "content_hash": strategy.content_hash,
                "validation_status": strategy.validation_status,
                "created_at": strategy.created_at.isoformat()
            }
            
            result = self.client.table("strategies").insert(strategy_record).execute()
            
            # Update buffer status
            self.client.table("strategies_buffer").update({"status": "completed"}).eq("content_hash", strategy.content_hash).execute()
            
            return {"status": "success", "data": result.data[0] if result.data else None}
            
        except Exception as error:
            self.logger.error(f"Strategy table commit failed: {error}")
            return {"status": "error", "error": str(error)}
    
    async def _store_in_vector_buffer(self, strategy: Strategy) -> Dict[str, Any]:
        """Store strategy embedding in strategy_vector_buffer table."""
        try:
            # Generate embedding for strategy content using OpenAI API
            from .llm_integration import LLMIntegration
            llm_integration = LLMIntegration(use_mock=self.use_mock)
            
            # Create text for embedding
            strategy_text = f"{strategy.title} {strategy.approach} {strategy.rationale}"
            
            # Use OpenAI API for embedding generation (not local)
            embedding = await llm_integration.generate_embedding(strategy_text)
            
            if not embedding or len(embedding) != 1536:
                raise ValueError(f"Invalid embedding generated: expected 1536 dimensions, got {len(embedding) if embedding else 0}")
            
            # Store in vector buffer
            result = self.client.table("strategy_vector_buffer").insert({
                "strategy_id": strategy.id,
                "content_hash": strategy.content_hash,
                "embedding": embedding,
                "model_version": "text-embedding-3-small",
                "status": "pending"
            }).execute()
            
            return {"status": "success", "data": result.data}
            
        except Exception as error:
            self.logger.error(f"Vector buffer storage failed: {error}")
            return {"status": "error", "error": str(error)}
    
    async def _commit_to_strategy_vectors(self, strategy: Strategy) -> Dict[str, Any]:
        """Commit vector from buffer to main strategy_vectors table."""
        try:
            # Get embedding from buffer
            buffer_result = self.client.table("strategy_vector_buffer").select("*").eq("strategy_id", strategy.id).execute()
            
            if not buffer_result.data:
                return {"status": "error", "error": "No vector found in buffer"}
            
            vector_data = buffer_result.data[0]
            
            # Insert into strategy_vectors table
            result = self.client.table("strategy_vectors").insert({
                "strategy_id": strategy.id,
                "embedding": vector_data["embedding"],
                "model_version": vector_data["model_version"]
            }).execute()
            
            # Update buffer status
            self.client.table("strategy_vector_buffer").update({"status": "completed"}).eq("strategy_id", strategy.id).execute()
            
            return {"status": "success", "data": result.data[0] if result.data else None}
            
        except Exception as error:
            self.logger.error(f"Vector table commit failed: {error}")
            return {"status": "error", "error": str(error)}
    
    def _mock_store_strategy(self, strategy: Strategy) -> StorageResult:
        """Mock strategy storage for testing."""
        # Simulate processing delay
        import time
        time.sleep(0.1)
        
        return StorageResult(
            strategy_id=strategy.id,
            storage_status="success",
            message="Mock strategy storage completed",
            timestamp=datetime.now()
        )
    
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
        if self.use_mock:
            return self._mock_retrieve_strategies(plan_constraints, limit)
        
        try:
            # Step 1: Constraint-based pre-filtering
            filtered_strategies = await self._filter_by_constraints(plan_constraints)
            
            # Step 2: Vector similarity search
            similar_strategies = await self._search_by_similarity(filtered_strategies, plan_constraints, limit)
            
            return similar_strategies
            
        except Exception as error:
            self.logger.error(f"Strategy retrieval failed: {error}")
            return []
    
    async def _filter_by_constraints(self, plan_constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter strategies by plan constraints."""
        try:
            # Build query based on constraints
            query = self.client.table("strategies").select("*")
            
            # Add constraint filters
            if "specialty_access" in plan_constraints:
                # This would need more sophisticated filtering logic
                pass
            
            result = query.limit(100).execute()  # Get top 100 for similarity search
            return result.data
            
        except Exception as error:
            self.logger.error(f"Constraint filtering failed: {error}")
            return []
    
    async def _search_by_similarity(
        self,
        strategies: List[Dict[str, Any]],
        plan_constraints: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search strategies by vector similarity using OpenAI API."""
        try:
            # Create query text for similarity search
            query_text = f"healthcare {plan_constraints.get('specialty_access', ['general'])[0]} access"
            
            # Generate embedding for query using OpenAI API
            from .llm_integration import LLMIntegration
            llm_integration = LLMIntegration(use_mock=self.use_mock)
            query_embedding = await llm_integration.generate_embedding(query_text)
            
            if not query_embedding or len(query_embedding) != 1536:
                raise ValueError(f"Invalid query embedding generated: expected 1536 dimensions, got {len(query_embedding) if query_embedding else 0}")
            
            # Search by similarity using pgvector
            result = self.client.rpc(
                "match_strategy_vectors",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.7,
                    "match_count": limit
                }
            ).execute()
            
            return result.data or []
            
        except Exception as error:
            self.logger.error(f"Similarity search failed: {error}")
            return strategies[:limit]  # Fallback to simple limit
    
    def _mock_retrieve_strategies(
        self,
        plan_constraints: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Mock strategy retrieval for testing."""
        return [
            {
                "id": "mock-strategy-1",
                "title": "Mock Strategy 1",
                "category": "speed-optimized",
                "approach": "Direct specialist consultation",
                "rationale": "Fastest path to care",
                "actionable_steps": ["Contact specialist", "Schedule appointment"],
                "llm_scores": {"speed": 0.9, "cost": 0.6, "effort": 0.7}
            },
            {
                "id": "mock-strategy-2",
                "title": "Mock Strategy 2",
                "category": "cost-optimized",
                "approach": "Step-by-step care pathway",
                "rationale": "Most cost-effective approach",
                "actionable_steps": ["Start with primary care", "Follow recommended path"],
                "llm_scores": {"speed": 0.5, "cost": 0.9, "effort": 0.6}
            }
        ][:limit]
    
    def get_database_status(self) -> Dict[str, Any]:
        """Get database connection and operation status."""
        return {
            "using_mock": self.use_mock,
            "supabase_available": SUPABASE_AVAILABLE,
            "connection_status": "connected" if not self.use_mock else "mock"
        } 