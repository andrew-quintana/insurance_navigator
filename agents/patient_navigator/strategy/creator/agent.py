import logging
import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from agents.base_agent import BaseAgent
from ..types import PlanConstraints, Strategy, StrategyScores, ContextRetrievalResult
from .models import StrategyCreatorInput, StrategyCreatorOutput

class StrategyCreatorAgent(BaseAgent):
    """
    StrategyCreator Agent - LLM-driven strategy generation
    
    Generates 4 strategies (speed, cost, effort, balanced) using prompt engineering
    with integrated LLM self-scoring mechanism (0.0-1.0 scale).
    """
    
    def __init__(self, use_mock: bool = False, **kwargs):
        """
        Initialize the Strategy Creator Agent.
        
        Args:
            use_mock: If True, use mock responses for testing
            **kwargs: Additional arguments passed to BaseAgent
        """
        super().__init__(
            name="strategy_creator",
            prompt="",  # Will be loaded from file
            output_schema=StrategyCreatorOutput,
            mock=use_mock,
            **kwargs
        )
        
        self.optimization_types = ['speed', 'cost', 'effort', 'balanced']

    async def generate_strategies(
        self,
        context: ContextRetrievalResult,
        plan_constraints: PlanConstraints
    ) -> List[Strategy]:
        """
        Generate 4 strategies with different optimization approaches
        """
        strategies = []

        for optimization_type in self.optimization_types:
            try:
                strategy = await self._generate_single_strategy(
                    context,
                    plan_constraints,
                    optimization_type
                )
                strategies.append(strategy)
            except Exception as error:
                self.logger.error(f"Failed to generate {optimization_type} strategy: {error}")
                # Continue with other strategies

        return strategies

    async def _generate_single_strategy(
        self,
        context: ContextRetrievalResult,
        plan_constraints: PlanConstraints,
        optimization_type: str
    ) -> Strategy:
        """
        Generate a single strategy for a specific optimization type
        """
        prompt = self._build_optimization_prompt(context, plan_constraints, optimization_type)
        
        response = await self._call_llm(prompt)
        parsed_response = self._parse_strategy_response(response, optimization_type)
        
        # Generate content hash for deduplication
        content_hash = self._generate_content_hash(parsed_response)
        
        return Strategy(
            id=self._generate_uuid(),
            title=parsed_response['title'],
            category=f"{optimization_type}-optimized",
            approach=parsed_response['approach'],
            rationale=parsed_response['rationale'],
            actionable_steps=parsed_response['actionable_steps'],
            plan_constraints=plan_constraints,
            llm_scores=parsed_response['llm_scores'],
            content_hash=content_hash,
            validation_status='pending',
            created_at=datetime.now()
        )

    def _build_optimization_prompt(
        self,
        context: ContextRetrievalResult,
        plan_constraints: PlanConstraints,
        optimization_type: str
    ) -> str:
        """
        Build optimization-specific prompt
        """
        context_summary = self._summarize_context(context)
        constraint_text = self._format_constraints(plan_constraints)
        
        optimization_prompts = {
            'speed': f"Generate the fastest possible strategy for accessing {plan_constraints.specialty_access} care. Focus on immediate availability, direct specialist access, and urgent care options.",
            'cost': f"Generate the most cost-effective strategy for accessing {plan_constraints.specialty_access} care. Focus on insurance coverage, in-network providers, and minimizing out-of-pocket costs.",
            'effort': f"Generate the strategy requiring minimal user effort for accessing {plan_constraints.specialty_access} care. Focus on streamlined processes, online booking, and simplified workflows.",
            'balanced': f"Generate a balanced strategy optimizing for speed, cost, and effort for accessing {plan_constraints.specialty_access} care. Consider all factors equally."
        }

        return f"""
You are a healthcare strategy expert. Generate a comprehensive strategy for accessing {plan_constraints.specialty_access} care.

{optimization_prompts[optimization_type]}

Plan Constraints:
{constraint_text}

Context Information:
{context_summary}

Generate a strategy with the following structure:
1. Title: Clear, descriptive title
2. Approach: Detailed strategy description
3. Rationale: Explanation of why this approach is optimal
4. Actionable Steps: 3-5 specific steps the user can take
5. Self-Scoring: Rate this strategy on speed (0.0-1.0), cost (0.0-1.0), and effort (0.0-1.0)

Format your response as JSON:
{{
  "title": "Strategy Title",
  "approach": "Detailed approach description",
  "rationale": "Explanation of strategy benefits",
  "actionableSteps": ["Step 1", "Step 2", "Step 3"],
  "llmScores": {{
    "speed": 0.8,
    "cost": 0.7,
    "effort": 0.6
  }}
}}
"""

    def _parse_strategy_response(self, response: str, optimization_type: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured strategy
        """
        try:
            # Try to parse as JSON first
            parsed = json.loads(response)
            
            # Validate required fields
            required_fields = ['title', 'approach', 'rationale', 'actionableSteps']
            if not all(field in parsed for field in required_fields):
                raise ValueError('Missing required fields in response')

            # Validate LLM scores
            scores = parsed.get('llmScores', {})
            validated_scores = StrategyScores(
                speed=self._validate_score(scores.get('speed'), 0.0, 1.0),
                cost=self._validate_score(scores.get('cost'), 0.0, 1.0),
                effort=self._validate_score(scores.get('effort'), 0.0, 1.0)
            )

            return {
                'title': parsed['title'],
                'approach': parsed['approach'],
                'rationale': parsed['rationale'],
                'actionable_steps': parsed['actionableSteps'] if isinstance(parsed['actionableSteps'], list) else [],
                'llm_scores': validated_scores
            }
        except Exception as error:
            self.logger.error('Failed to parse strategy response:', error)
            
            # Return fallback strategy
            return self._create_fallback_strategy(optimization_type)

    def _validate_score(self, score: Any, min_val: float, max_val: float) -> float:
        """
        Validate and normalize LLM score
        """
        try:
            num = float(score)
            if num < min_val or num > max_val:
                return (min_val + max_val) / 2  # Default to middle value
            return num
        except (ValueError, TypeError):
            return (min_val + max_val) / 2  # Default to middle value

    def _create_fallback_strategy(self, optimization_type: str) -> Dict[str, Any]:
        """
        Create fallback strategy when parsing fails
        """
        fallback_scores = {
            'speed': 0.9 if optimization_type == 'speed' else 0.5,
            'cost': 0.9 if optimization_type == 'cost' else 0.5,
            'effort': 0.9 if optimization_type == 'effort' else 0.5
        }

        return {
            'title': f"{optimization_type.title()}-Optimized Strategy",
            'approach': f"Standard {optimization_type}-optimized approach for healthcare access.",
            'rationale': f"This strategy prioritizes {optimization_type} optimization based on your constraints.",
            'actionable_steps': [
                'Contact your insurance provider for coverage details',
                'Search for in-network providers in your area',
                'Schedule an appointment with a qualified specialist'
            ],
            'llm_scores': StrategyScores(**fallback_scores)
        }

    def _summarize_context(self, context: ContextRetrievalResult) -> str:
        """
        Summarize context for prompt inclusion
        """
        parts = []

        if context.web_search_results:
            parts.append(f"Web search found {len(context.web_search_results)} relevant results")

        if context.relevant_strategies:
            parts.append(f"Found {len(context.relevant_strategies)} similar existing strategies")

        if context.regulatory_context:
            parts.append('Regulatory context available')

        return '. '.join(parts) if parts else 'Limited context available'

    def _format_constraints(self, plan_constraints: PlanConstraints) -> str:
        """
        Format plan constraints for prompt inclusion
        """
        parts = [
            f"Specialty: {plan_constraints.specialty_access}",
            f"Urgency: {plan_constraints.urgency_level}"
        ]

        if plan_constraints.budget_constraints and plan_constraints.budget_constraints.get('max_cost'):
            parts.append(f"Budget: ${plan_constraints.budget_constraints['max_cost']}")

        if plan_constraints.location_constraints and plan_constraints.location_constraints.get('max_distance'):
            parts.append(f"Max Distance: {plan_constraints.location_constraints['max_distance']} miles")

        if plan_constraints.time_constraints and plan_constraints.time_constraints.get('preferred_timeframe'):
            parts.append(f"Timeframe: {plan_constraints.time_constraints['preferred_timeframe']}")

        return '\n'.join(parts)

    def _generate_content_hash(self, strategy: Dict[str, Any]) -> str:
        """
        Generate content hash for deduplication
        """
        content = json.dumps({
            'title': strategy['title'],
            'approach': strategy['approach'],
            'rationale': strategy['rationale'],
            'actionable_steps': strategy['actionable_steps']
        }, sort_keys=True)
        
        return hashlib.sha256(content.encode()).hexdigest()

    async def _call_llm(self, prompt: str) -> str:
        """
        Call LLM with error handling
        """
        try:
            if self.mock:
                return self._generate_mock_response()
            
            # This would integrate with actual LLM client
            # For now, return mock response
            return self._generate_mock_response()
        except Exception as error:
            self.logger.error('LLM call failed:', error)
            raise error

    def _generate_mock_response(self) -> str:
        """
        Generate mock response for testing
        """
        return json.dumps({
            "title": "Mock Strategy",
            "approach": "This is a mock strategy for testing purposes.",
            "rationale": "Mock rationale explaining the approach.",
            "actionableSteps": [
                "Step 1: Contact provider",
                "Step 2: Schedule appointment",
                "Step 3: Follow up"
            ],
            "llmScores": {
                "speed": 0.8,
                "cost": 0.7,
                "effort": 0.6
            }
        })

    def _generate_uuid(self) -> str:
        """
        Generate UUID for strategy ID
        """
        import uuid
        return str(uuid.uuid4()) 