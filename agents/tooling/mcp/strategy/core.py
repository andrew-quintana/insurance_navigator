import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import json

from supabase import create_client, Client
from tavily import TavilyClient

from .types import StrategyMCPConfig, WebSearchQuery, SemanticSearchResult, RegulatoryContextResult, PlanMetadata
from ...patient_navigator.strategy.types import PlanConstraints, ContextRetrievalResult, SearchResult, QueryMetadata

class StrategyMCPTool:
    """
    StrategyMCP Tool - Context Gathering for Strategy Generation
    
    Simplified context coordinator using Tavily-only web search and semantic similarity
    for existing strategies. Follows the MCP tool pattern from existing architecture.
    """
    
    def __init__(self, config: StrategyMCPConfig):
        self.config = config
        self.tavily = TavilyClient(api_key=config.tavily_api_key)
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.CACHE_TTL = 5 * 60  # 5 minutes
        self.WEB_SEARCH_TIMEOUT = 5  # 5 seconds
        self.logger = logging.getLogger(__name__)

    async def gather_context(self, plan_constraints: PlanConstraints) -> ContextRetrievalResult:
        """
        Main context gathering method
        """
        start_time = datetime.now()
        
        try:
            # 1. Retrieve plan metadata for context
            plan_metadata = await self._get_plan_metadata(plan_constraints)
            
            # 2. Generate web search queries with plan context
            web_search_queries = self._generate_web_search_queries(plan_constraints, plan_metadata)
            
            # 3. Perform web searches with timeout and fallback
            web_search_results = await self._perform_web_searches(web_search_queries)
            
            # 4. Semantic search of existing strategies with plan context
            relevant_strategies = await self._search_similar_strategies(plan_constraints, plan_metadata)
            
            # 5. Retrieve regulatory context
            regulatory_context = await self._get_regulatory_context(plan_constraints)
            
            query_metadata = QueryMetadata(
                generated_queries=[q.query for q in web_search_queries],
                search_duration=(datetime.now() - start_time).total_seconds(),
                result_count=len(web_search_results)
            )

            return ContextRetrievalResult(
                web_search_results=web_search_results,
                relevant_strategies=relevant_strategies,
                regulatory_context=regulatory_context.context,
                query_metadata=query_metadata
            )
        except Exception as error:
            self.logger.error('Error in context gathering:', error)
            # Return fallback result with semantic search only
            return await self._get_fallback_context(plan_constraints)

    async def _get_plan_metadata(self, plan_constraints: PlanConstraints) -> PlanMetadata:
        """
        Mock plan metadata retrieval - will be replaced with actual plan metadata table
        """
        # Mock implementation based on typical HMO plan structures
        # In future this will query a plan metadata table
        mock_plan_metadata = PlanMetadata(
            plan_id='scan-classic-hmo-001',
            plan_name='SCAN Classic HMO',
            insurance_provider='SCAN Health Plan',
            plan_type='HMO',
            network_type='in-network',
            copay_structure={
                'primary_care': 0,        # HMO typically $0 copay for primary care
                'specialist': 25,         # Specialist visits
                'urgent_care': 50,        # Urgent care visits
                'emergency': 100          # Emergency room visits
            },
            deductible={
                'individual': 0,          # HMO often has $0 deductible
                'family': 0
            },
            out_of_pocket_max={
                'individual': 4500,       # Annual out-of-pocket maximum
                'family': 9000
            },
            coverage_limits={
                'annual_visits': 12,      # Primary care visits per year
                'specialist_visits': 8,   # Specialist visits per year
                'physical_therapy': 20    # Physical therapy sessions
            },
            geographic_scope={
                'states': ['CA'],
                'counties': ['Los Angeles', 'Orange', 'San Diego', 'Riverside', 'San Bernardino'],
                'zip_codes': ['90210', '90211', '90212', '92614', '92615', '92101', '92102']
            },
            preferred_providers=[
                'Kaiser Permanente',
                'UCLA Health',
                'Cedars-Sinai',
                'Hoag Memorial Hospital'
            ],
            excluded_providers=[],
            prior_authorization_required=[
                'MRI',
                'CT Scan',
                'Specialist referrals',
                'Physical therapy'
            ],
            step_therapy_required=[
                'Prescription medications',
                'Physical therapy'
            ]
        )

        return mock_plan_metadata

    def _generate_web_search_queries(self, plan_constraints: PlanConstraints, plan_metadata: PlanMetadata) -> List[WebSearchQuery]:
        """
        Generate web search queries for each optimization type
        """
        constraint_text = self._create_constraint_text_with_plan_context(plan_constraints, plan_metadata)
        
        queries = [
            # Speed-optimized query
            WebSearchQuery(
                query=f"speed optimized care corresponding to {constraint_text}",
                optimization_type='speed',
                max_results=3
            ),
            
            # Cost-optimized query
            WebSearchQuery(
                query=f"cost optimized care corresponding to {constraint_text}",
                optimization_type='cost',
                max_results=3
            ),
            
            # Effort-optimized query
            WebSearchQuery(
                query=f"patient effort optimized care corresponding to {constraint_text}",
                optimization_type='effort',
                max_results=3
            )
        ]

        return queries

    async def _perform_web_searches(self, queries: List[WebSearchQuery]) -> List[SearchResult]:
        """
        Perform web searches with timeout and caching
        """
        results = []
        
        for query in queries:
            try:
                # Check cache first
                cache_key = f"web_search_{query.query}"
                cached = self.cache.get(cache_key)
                if cached and (datetime.now() - cached['timestamp']).total_seconds() < self.CACHE_TTL:
                    results.extend(cached['data'])
                    continue

                # Perform search with timeout
                search_result = await self._search_with_timeout(query.query, query.max_results)
                
                # Transform results
                transformed_results = []
                for i, result in enumerate(search_result.get('results', [])):
                    transformed_results.append(SearchResult(
                        title=result.get('title', ''),
                        url=result.get('url', ''),
                        content=result.get('content', ''),
                        relevance=1.0 - (i * 0.1)  # Simple relevance scoring
                    ))

                # Cache results
                self.cache[cache_key] = {
                    'data': transformed_results,
                    'timestamp': datetime.now()
                }

                results.extend(transformed_results)
            except Exception as error:
                self.logger.warning(f"Web search failed for query: {query.query}", error)
                # Continue with other queries

        return results

    async def _search_with_timeout(self, query: str, max_results: int) -> Dict[str, Any]:
        """
        Perform search with timeout
        """
        import asyncio
        
        try:
            # Create search task
            search_task = asyncio.create_task(
                self.tavily.search(query, max_results=max_results, search_depth='basic')
            )
            
            # Wait with timeout
            result = await asyncio.wait_for(search_task, timeout=self.WEB_SEARCH_TIMEOUT)
            return result
        except asyncio.TimeoutError:
            raise Exception("Search timeout")

    async def _search_similar_strategies(self, plan_constraints: PlanConstraints, plan_metadata: PlanMetadata) -> List[Any]:
        """
        Search similar strategies using vector similarity
        """
        try:
            # Create embedding for constraint text
            constraint_text = self._create_constraint_text_with_plan_context(plan_constraints, plan_metadata)
            
            # For now, return mock results since embedding generation requires OpenAI API
            # In production, this would use OpenAI embeddings and pgvector similarity search
            mock_strategies = [
                {
                    'id': 'mock-strategy-1',
                    'title': 'Fast Cardiology Access Strategy',
                    'category': 'speed-optimized',
                    'approach': 'Direct specialist appointment booking',
                    'rationale': 'Bypass primary care referral for urgent cardiology needs',
                    'actionable_steps': [
                        'Contact cardiology department directly',
                        'Request urgent appointment slot',
                        'Provide insurance information upfront'
                    ],
                    'plan_constraints': plan_constraints,
                    'llm_scores': {'speed': 0.9, 'cost': 0.7, 'effort': 0.6},
                    'content_hash': 'mock-hash-1',
                    'validation_status': 'approved',
                    'created_at': datetime.now()
                }
            ]

            return mock_strategies
        except Exception as error:
            self.logger.warning('Semantic search failed:', error)
            return []

    async def _get_regulatory_context(self, plan_constraints: PlanConstraints) -> RegulatoryContextResult:
        """
        Retrieve regulatory context from documents schema
        """
        try:
            # Query documents schema for regulatory information
            response = self.supabase.table('documents').select('content, metadata').eq('category', 'regulatory').ilike('content', f'%{plan_constraints.specialty_access}%').limit(3).execute()
            
            regulatory_docs = response.data if response.data else []

            if not regulatory_docs:
                return RegulatoryContextResult(
                    context='Standard healthcare regulations apply. Consult with your insurance provider for specific coverage details.',
                    sources=[]
                )

            context = '\n\n'.join([doc['content'] for doc in regulatory_docs])
            
            sources = [
                {
                    'type': 'document',
                    'title': doc.get('metadata', {}).get('title', 'Regulatory Document'),
                    'content': doc['content'],
                    'relevance': 0.8
                }
                for doc in regulatory_docs
            ]

            return RegulatoryContextResult(context=context, sources=sources)
        except Exception as error:
            self.logger.warning('Regulatory context retrieval failed:', error)
            return RegulatoryContextResult(
                context='Standard healthcare regulations apply. Consult with your insurance provider for specific coverage details.',
                sources=[]
            )

    def _create_constraint_text_with_plan_context(self, plan_constraints: PlanConstraints, plan_metadata: PlanMetadata) -> str:
        """
        Create constraint text with plan context for enhanced queries
        """
        base_constraints = self._create_constraint_text(plan_constraints)
        
        plan_context = [
            plan_metadata.plan_type,
            plan_metadata.network_type,
            f"${plan_metadata.copay_structure['specialist']} specialist copay",
            f"${plan_metadata.deductible['individual']} deductible",
            ' '.join(plan_metadata.geographic_scope['states']),
            plan_metadata.insurance_provider
        ]

        return f"{base_constraints} {' '.join(plan_context)}"

    def _create_constraint_text(self, plan_constraints: PlanConstraints) -> str:
        """
        Create basic constraint text for search queries
        """
        parts = [
            plan_constraints.specialty_access,
            plan_constraints.urgency_level,
            f"budget ${plan_constraints.budget_constraints['max_cost']}" if plan_constraints.budget_constraints and plan_constraints.budget_constraints.get('max_cost') else '',
            f"within {plan_constraints.location_constraints['max_distance']} miles" if plan_constraints.location_constraints and plan_constraints.location_constraints.get('max_distance') else '',
            plan_constraints.time_constraints.get('preferred_timeframe', '') if plan_constraints.time_constraints else ''
        ]

        return ' '.join([part for part in parts if part])

    async def _get_fallback_context(self, plan_constraints: PlanConstraints) -> ContextRetrievalResult:
        """
        Fallback context when web search fails
        """
        self.logger.info('Using fallback context due to web search failure')
        
        return ContextRetrievalResult(
            web_search_results=[],
            relevant_strategies=[],
            regulatory_context='Standard healthcare regulations apply. Consult with your insurance provider for specific coverage details.',
            query_metadata=QueryMetadata(
                generated_queries=[],
                search_duration=0,
                result_count=0
            )
        )

    def _clear_expired_cache(self) -> None:
        """
        Clear expired cache entries
        """
        now = datetime.now()
        expired_keys = [
            key for key, value in self.cache.items()
            if (now - value['timestamp']).total_seconds() > self.CACHE_TTL
        ]
        for key in expired_keys:
            del self.cache[key] 