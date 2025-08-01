import logging
import hashlib
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from supabase import create_client, Client
import os

from ..types import Strategy, PlanConstraints, StorageResult

@dataclass
class StrategyBufferEntry:
    """Buffer entry for strategy processing"""
    id: str
    strategy_data: Dict[str, Any]
    content_hash: str
    status: str  # 'pending', 'processing', 'completed', 'failed', 'abandoned'
    retry_count: int = 0
    expires_at: datetime = None
    created_at: datetime = None
    updated_at: datetime = None

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
    
    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
        self.logger = logging.getLogger(__name__)

    async def store_strategies(self, strategies: List[Strategy]) -> List[StorageResult]:
        """
        Store strategies using buffer-based workflow with idempotent operations
        """
        storage_results = []

        for strategy in strategies:
            try:
                # Early exit check for existing strategy using content_hash
                if await self._strategy_exists_by_content_hash(strategy.content_hash):
                    self.logger.info(f"Strategy with content_hash {strategy.content_hash} already exists, skipping")
                    storage_results.append(StorageResult(
                        strategy_id=strategy.id,
                        storage_status='skipped',
                        vector_embedding_created=False,
                        metadata_stored=True,
                        error_message='Strategy already exists'
                    ))
                    continue

                # Step 1: Create buffer entry (idempotent)
                buffer_entry = await self._create_buffer_entry_idempotent(strategy)
                
                # Step 2: Process strategy (validate and prepare for storage)
                processed_strategy = await self._process_strategy(strategy)
                
                # Step 3: Commit to main table with retry logic
                storage_result = await self._commit_strategy_with_retry(processed_strategy)
                
                # Step 4: Generate and store embeddings with retry logic
                embedding_result = await self._store_embeddings_with_retry(strategy)
                
                # Step 5: Update buffer status
                await self._update_buffer_status(buffer_entry.id, 'completed')
                
                storage_results.append(storage_result)
                
            except Exception as error:
                self.logger.error(f"Failed to store strategy {strategy.id}: {error}")
                storage_results.append(self._create_fallback_storage_result(strategy.id))

        return storage_results

    async def _strategy_exists_by_content_hash(self, content_hash: str) -> bool:
        """
        Check if strategy exists by content_hash across all tables
        """
        try:
            # Check main strategies table
            response = self.supabase.table('strategies').select('id').eq('content_hash', content_hash).limit(1).execute()
            if response.data:
                return True

            # Check strategies_buffer table
            response = self.supabase.table('strategies_buffer').select('id').eq('content_hash', content_hash).eq('status', 'completed').limit(1).execute()
            if response.data:
                return True

            return False
        except Exception as error:
            self.logger.error(f"Error checking strategy existence: {error}")
            return False

    async def _create_buffer_entry_idempotent(self, strategy: Strategy) -> StrategyBufferEntry:
        """
        Create buffer entry with idempotent insert using content_hash
        """
        content_hash = self._generate_content_hash(strategy)
        
        # Check if buffer entry already exists
        existing_response = self.supabase.table('strategies_buffer').select('*').eq('content_hash', content_hash).limit(1).execute()
        if existing_response.data:
            self.logger.info(f"Buffer entry for content_hash {content_hash} already exists")
            existing_data = existing_response.data[0]
            return StrategyBufferEntry(
                id=existing_data['id'],
                strategy_data=existing_data['strategy_data'],
                content_hash=existing_data['content_hash'],
                status=existing_data['status'],
                retry_count=existing_data['retry_count'],
                expires_at=datetime.fromisoformat(existing_data['expires_at']),
                created_at=datetime.fromisoformat(existing_data['created_at']),
                updated_at=datetime.fromisoformat(existing_data['updated_at'])
            )

        buffer_data = {
            'strategy_data': {
                'id': strategy.id,
                'title': strategy.title,
                'category': strategy.category,
                'approach': strategy.approach,
                'rationale': strategy.rationale,
                'actionable_steps': strategy.actionable_steps,
                'plan_constraints': strategy.plan_constraints,
                'llm_score_speed': strategy.llm_scores.speed,
                'llm_score_cost': strategy.llm_scores.cost,
                'llm_score_effort': strategy.llm_scores.effort,
                'content_hash': content_hash,
                'validation_status': strategy.validation_status,
                'author_id': None  # Will be set by RLS policies
            },
            'content_hash': content_hash,
            'status': 'pending',
            'retry_count': 0,
            'expires_at': datetime.now() + timedelta(hours=24)
        }

        response = self.supabase.table('strategies_buffer').insert(buffer_data).execute()
        
        if response.data:
            buffer_entry = response.data[0]
            return StrategyBufferEntry(
                id=buffer_entry['id'],
                strategy_data=buffer_entry['strategy_data'],
                content_hash=buffer_entry['content_hash'],
                status=buffer_entry['status'],
                retry_count=buffer_entry['retry_count'],
                expires_at=datetime.fromisoformat(buffer_entry['expires_at']),
                created_at=datetime.fromisoformat(buffer_entry['created_at']),
                updated_at=datetime.fromisoformat(buffer_entry['updated_at'])
            )
        else:
            raise Exception("Failed to create buffer entry")

    async def _process_strategy(self, strategy: Strategy) -> Dict[str, Any]:
        """
        Process strategy for storage (validation, formatting, etc.)
        """
        # Check if strategy already exists
        existing = await self._check_strategy_exists(strategy.content_hash)
        if existing:
            self.logger.info(f"Strategy with content_hash {strategy.content_hash} already exists")
            return existing

        # Format strategy for storage
        processed_strategy = {
            'id': strategy.id,
            'title': strategy.title,
            'category': strategy.category,
            'approach': strategy.approach,
            'rationale': strategy.rationale,
            'actionable_steps': strategy.actionable_steps,
            'plan_constraints': strategy.plan_constraints,
            'llm_score_speed': strategy.llm_scores.speed,
            'llm_score_cost': strategy.llm_scores.cost,
            'llm_score_effort': strategy.llm_scores.effort,
            'content_hash': strategy.content_hash,
            'validation_status': strategy.validation_status,
            'author_id': None
        }

        return processed_strategy

    async def _commit_strategy_with_retry(self, processed_strategy: Dict[str, Any]) -> StorageResult:
        """
        Commit strategy to main strategies table with retry logic and exponential backoff
        """
        return await self._retry_with_exponential_backoff(
            lambda: self._commit_strategy(processed_strategy),
            max_retries=3,
            operation_name="commit_strategy"
        )

    async def _commit_strategy(self, processed_strategy: Dict[str, Any]) -> StorageResult:
        """
        Commit strategy to main strategies table
        """
        try:
            # Use upsert to handle potential duplicates
            response = self.supabase.table('strategies').upsert(
                processed_strategy,
                on_conflict='content_hash'
            ).execute()
            
            if response.data:
                return StorageResult(
                    strategy_id=processed_strategy['id'],
                    storage_status='success',
                    vector_embedding_created=False,  # Will be handled separately
                    metadata_stored=True
                )
            else:
                raise Exception("Failed to insert strategy")
                
        except Exception as error:
            self.logger.error(f"Failed to commit strategy {processed_strategy['id']}: {error}")
            raise error

    async def _store_embeddings_with_retry(self, strategy: Strategy) -> bool:
        """
        Store embeddings with retry logic and exponential backoff
        """
        return await self._retry_with_exponential_backoff(
            lambda: self._store_embeddings(strategy),
            max_retries=3,
            operation_name="store_embeddings"
        )

    async def _store_embeddings(self, strategy: Strategy) -> bool:
        """
        Store embeddings via buffer → commit pattern
        """
        try:
            # Step 1: Create vector buffer entry (idempotent)
            vector_buffer_entry = await self._create_vector_buffer_entry_idempotent(strategy)
            
            # Step 2: Generate embedding (placeholder for OpenAI integration)
            embedding = await self._generate_embedding(strategy)
            
            # Step 3: Store in vector buffer
            await self._store_vector_buffer(vector_buffer_entry['id'], embedding)
            
            # Step 4: Commit to main vector table
            await self._commit_vector_embedding(strategy.id, embedding)
            
            return True
            
        except Exception as error:
            self.logger.error(f"Failed to store embeddings for strategy {strategy.id}: {error}")
            return False

    async def _create_vector_buffer_entry_idempotent(self, strategy: Strategy) -> Dict[str, Any]:
        """
        Create vector buffer entry with idempotent insert
        """
        # Check if vector buffer entry already exists
        existing_response = self.supabase.table('strategy_vector_buffer').select('*').eq('content_hash', strategy.content_hash).limit(1).execute()
        if existing_response.data:
            self.logger.info(f"Vector buffer entry for content_hash {strategy.content_hash} already exists")
            return existing_response.data[0]

        buffer_data = {
            'strategy_id': strategy.id,
            'content_hash': strategy.content_hash,
            'status': 'pending',
            'retry_count': 0,
            'expires_at': datetime.now() + timedelta(hours=24)
        }

        response = self.supabase.table('strategy_vector_buffer').insert(buffer_data).execute()
        
        if response.data:
            return response.data[0]
        else:
            raise Exception("Failed to create vector buffer entry")

    async def _generate_embedding(self, strategy: Strategy) -> List[float]:
        """
        Generate embedding for strategy content (placeholder for OpenAI integration)
        """
        # For now, return mock embedding
        # In production, this would call OpenAI embeddings API
        content = f"{strategy.title} {strategy.approach} {strategy.rationale}"
        return [0.1] * 1536  # Mock embedding vector

    async def _store_vector_buffer(self, buffer_id: str, embedding: List[float]) -> None:
        """
        Store embedding in vector buffer
        """
        buffer_data = {
            'embedding': embedding,
            'model_version': 'text-embedding-3-small',
            'status': 'processing'
        }

        self.supabase.table('strategy_vector_buffer').update(buffer_data).eq('id', buffer_id).execute()

    async def _commit_vector_embedding(self, strategy_id: str, embedding: List[float]) -> None:
        """
        Commit embedding to main vector table
        """
        vector_data = {
            'strategy_id': strategy_id,
            'embedding': embedding,
            'model_version': 'text-embedding-3-small'
        }

        # Use upsert to handle potential duplicates
        self.supabase.table('strategy_vectors').upsert(
            vector_data,
            on_conflict='strategy_id'
        ).execute()

    async def _retry_with_exponential_backoff(self, operation, max_retries: int = 3, operation_name: str = "operation") -> Any:
        """
        Retry helper with exponential backoff
        """
        for attempt in range(max_retries + 1):
            try:
                return await operation()
            except Exception as error:
                if attempt == max_retries:
                    self.logger.error(f"{operation_name} failed after {max_retries} retries: {error}")
                    raise error
                
                # Calculate backoff delay: 2^attempt * 1000ms (1s, 2s, 4s)
                delay = (2 ** attempt) * 1000
                self.logger.warning(f"{operation_name} failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay}ms: {error}")
                await asyncio.sleep(delay / 1000)  # Convert to seconds

    async def retrieve_strategies(
        self,
        plan_constraints: PlanConstraints,
        limit: int = 10
    ) -> List[Strategy]:
        """
        Retrieve strategies using constraint-based filtering and vector similarity
        """
        try:
            # Step 1: Constraint-based pre-filtering
            filtered_strategies = await self._filter_by_constraints(plan_constraints)
            
            # Step 2: Vector similarity search on filtered results
            similar_strategies = await self._search_by_similarity(
                plan_constraints,
                filtered_strategies,
                limit
            )

            return similar_strategies
        except Exception as error:
            self.logger.error('Strategy retrieval failed:', error)
            return []

    async def _filter_by_constraints(self, plan_constraints: PlanConstraints) -> List[Dict[str, Any]]:
        """
        Filter strategies by plan constraints
        """
        response = self.supabase.table('strategies').select('*').eq('validation_status', 'approved').contains('plan_constraints', {
            'specialty_access': plan_constraints.specialty_access,
            'urgency_level': plan_constraints.urgency_level
        }).limit(50).execute()

        return response.data if response.data else []

    async def _search_by_similarity(
        self,
        plan_constraints: PlanConstraints,
        filtered_strategies: List[Dict[str, Any]],
        limit: int
    ) -> List[Strategy]:
        """
        Search by vector similarity on pre-filtered results
        """
        if not filtered_strategies:
            return []

        # Create embedding for constraint text
        constraint_text = self._create_constraint_text(plan_constraints)
        
        # For now, return mock results since embedding generation requires OpenAI API
        # In production, this would use OpenAI embeddings and pgvector similarity search
        mock_strategies = []
        
        for strategy_data in filtered_strategies[:limit]:
            strategy = Strategy(
                id=strategy_data['id'],
                title=strategy_data['title'],
                category=strategy_data['category'],
                approach=strategy_data['approach'],
                rationale=strategy_data['rationale'],
                actionable_steps=strategy_data.get('actionable_steps', []),
                plan_constraints=strategy_data['plan_constraints'],
                llm_scores={
                    'speed': strategy_data.get('llm_score_speed', 0.5),
                    'cost': strategy_data.get('llm_score_cost', 0.5),
                    'effort': strategy_data.get('llm_score_effort', 0.5)
                },
                content_hash=strategy_data['content_hash'],
                validation_status=strategy_data['validation_status'],
                created_at=datetime.fromisoformat(strategy_data['created_at'])
            )
            mock_strategies.append(strategy)

        return mock_strategies

    async def update_human_scores(
        self,
        strategy_id: str,
        effectiveness_score: float,
        followability_score: Optional[float] = None
    ) -> bool:
        """
        Update human effectiveness scores from user feedback
        """
        try:
            update_data = {
                'human_score_effectiveness': effectiveness_score,
                'human_followability_avg': followability_score or effectiveness_score,
                'num_ratings': self.supabase.sql('num_ratings + 1'),
                'updated_at': datetime.now().isoformat()
            }

            response = self.supabase.table('strategies').update(update_data).eq('id', strategy_id).execute()

            return bool(response.data)
        except Exception as error:
            self.logger.error(f"Failed to update human scores for strategy {strategy_id}: {error}")
            return False

    async def _check_strategy_exists(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """
        Check if strategy exists by content hash
        """
        response = self.supabase.table('strategies').select('*').eq('content_hash', content_hash).single().execute()
        return response.data if response.data else None

    async def _update_buffer_status(self, buffer_id: str, status: str) -> None:
        """
        Update buffer entry status
        """
        update_data = {
            'status': status,
            'updated_at': datetime.now().isoformat()
        }

        self.supabase.table('strategies_buffer').update(update_data).eq('id', buffer_id).execute()

    def _generate_content_hash(self, strategy: Strategy) -> str:
        """
        Generate content hash for deduplication
        """
        content = json.dumps({
            'title': strategy.title,
            'approach': strategy.approach,
            'rationale': strategy.rationale,
            'actionable_steps': strategy.actionable_steps
        }, sort_keys=True)
        
        return hashlib.sha256(content.encode()).hexdigest()

    def _create_constraint_text(self, plan_constraints: PlanConstraints) -> str:
        """
        Create constraint text for similarity search
        """
        parts = [
            plan_constraints.specialty_access,
            plan_constraints.urgency_level,
            f"budget ${plan_constraints.budget_constraints['max_cost']}" if plan_constraints.budget_constraints and plan_constraints.budget_constraints.get('max_cost') else '',
            f"within {plan_constraints.location_constraints['max_distance']} miles" if plan_constraints.location_constraints and plan_constraints.location_constraints.get('max_distance') else '',
            plan_constraints.time_constraints.get('preferred_timeframe', '') if plan_constraints.time_constraints else ''
        ]

        return ' '.join([part for part in parts if part])

    def _create_fallback_storage_result(self, strategy_id: str) -> StorageResult:
        """
        Create fallback storage result when storage fails
        """
        return StorageResult(
            strategy_id=strategy_id,
            storage_status='failed',
            vector_embedding_created=False,
            metadata_stored=False,
            error_message='Storage operation failed'
        )

    async def clear_expired_buffer(self) -> int:
        """
        Clear expired buffer entries
        """
        try:
            response = self.supabase.table('strategies_buffer').delete().lt('expires_at', datetime.now().isoformat()).execute()
            return len(response.data) if response.data else 0
        except Exception as error:
            self.logger.error('Buffer cleanup failed:', error)
            return 0

    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics
        """
        try:
            strategies_response = self.supabase.table('strategies').select('id', count='exact').execute()
            vectors_response = self.supabase.table('strategy_vectors').select('strategy_id', count='exact').execute()
            buffer_response = self.supabase.table('strategies_buffer').select('id', count='exact').execute()

            return {
                'strategies_count': strategies_response.count if hasattr(strategies_response, 'count') else 0,
                'vectors_count': vectors_response.count if hasattr(vectors_response, 'count') else 0,
                'buffer_count': buffer_response.count if hasattr(buffer_response, 'count') else 0,
                'errors': []
            }
        except Exception as error:
            self.logger.error('Failed to get storage stats:', error)
            return {
                'strategies_count': 0,
                'vectors_count': 0,
                'buffer_count': 0,
                'errors': [str(error)]
            } 