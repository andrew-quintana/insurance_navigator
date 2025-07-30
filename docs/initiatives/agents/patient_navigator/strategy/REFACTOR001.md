Refactor Prescription: Strategy System MVP Simplification

  Overview

  This document prescribes refactoring the Strategy Evaluation & Validation System (001) to be a high-level MVP implementation focusing on prompt engineering and LLM-driven logic rather than granular programmatic analysis.

  Core Changes Required

  1. Optimization Goals Update: Speed → Cost → Effort

  Current State: Speed, Cost, Quality scoring system
  Target State: Speed, Cost, Effort scoring system

  Database Schema Updates

  -- Update strategies.strategies table
  ALTER TABLE strategies.strategies
    RENAME COLUMN llm_score_quality TO llm_score_effort;

  -- Update constraints  
  ALTER TABLE strategies.strategies
    DROP CONSTRAINT strategies_llm_score_quality_check,
    ADD CONSTRAINT strategies_llm_score_effort_check
      CHECK (llm_score_effort >= 0.0 AND llm_score_effort <= 1.0);

  -- Update indexes
  DROP INDEX idx_strategies_llm_scores;
  CREATE INDEX idx_strategies_llm_scores ON strategies.strategies
    (llm_score_speed, llm_score_cost, llm_score_effort);

  Strategy Generation Logic

  New Approach: Generate 4 strategies total
  1. Speed-Optimized: Fastest path to resolution
  2. Cost-Optimized: Most cost-effective approach
  3. Effort-Optimized: Minimal user effort required
  4. Balanced: Best combination of all three factors

  2. StrategyCreator Agent Simplification

  Current Problem: Too granular with complex optimization algorithms
  Solution: High-level prompt-driven approach

  Simplified Implementation

  class StrategyCreatorAgent(BaseAgent):
      """High-level strategy generation using prompt engineering"""

      async def generate_strategies(self, context: ContextRetrievalResult) -> StrategyResponse:
          """Generate 4 strategies: speed, cost, effort, balanced"""

          strategies = []
          for optimization_type in ['speed', 'cost', 'effort', 'balanced']:
              strategy = await self._generate_single_strategy(context, optimization_type)
              strategies.append(strategy)

          return StrategyResponse(strategies=strategies)

      async def _generate_single_strategy(self, context, optimization_type):
          """Single strategy generation via LLM prompt"""
          prompt = self._build_optimization_prompt(context, optimization_type)
          response = await self.llm_client.generate(prompt)
          return self._parse_strategy_response(response, optimization_type)

  Prompt Engineering Focus

  - Speed Prompt: "Generate the fastest possible strategy..."
  - Cost Prompt: "Generate the most cost-effective strategy..."
  - Effort Prompt: "Generate the strategy requiring minimal user effort..."
  - Balanced Prompt: "Generate a balanced strategy optimizing for speed, cost, and effort..."

  3. StrategyMCP Tool Simplification

  Current Problem: Complex multi-provider web search with detailed analysis
  Solution: Simple Tavily integration + semantic search

  Simplified Implementation

  from tavily import TavilyClient

  class StrategyMCPTool:
      """Simplified context gathering using Tavily + semantic search"""

      def __init__(self):
          self.tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

      async def gather_context(self, plan_constraints: PlanConstraints) -> ContextRetrievalResult:
          """High-level context gathering"""

          # 1. Semantic search of existing strategies
          similar_strategies = await self._search_similar_strategies(plan_constraints)

          # 2. Simple web search for each optimization type
          web_context = await self._search_web_context(plan_constraints)

          # 3. Regulatory context from documents schema
          regulatory_context = await self._get_regulatory_context(plan_constraints)

          return ContextRetrievalResult(
              similar_strategies=similar_strategies,
              web_context=web_context,
              regulatory_context=regulatory_context
          )

      async def _search_web_context(self, constraints):
          """Simple Tavily search for optimization contexts"""
          searches = [
              f"fastest healthcare {constraints.specialtyAccess} access",
              f"cheapest healthcare {constraints.specialtyAccess} options",
              f"easiest healthcare {constraints.specialtyAccess} process"
          ]

          results = []
          for query in searches:
              result = await self.tavily.search(query, max_results=3)
              results.extend(result)

          return results

  4. Remove Granular Analysis Components

  Components to Remove/Simplify

  - ❌ Exact text matching: Replace with semantic similarity
  - ❌ Detailed strategy analysis: Use LLM reasoning instead
  - ❌ Complex multi-provider fallback: Use Tavily only
  - ❌ Granular regulatory parsing: Use semantic search + LLM interpretation
  - ❌ Complex optimization algorithms: Use prompt engineering

  Replace With

  - ✅ SentenceBERT: For any text similarity needs
  - ✅ Tavily: Single web search provider
  - ✅ LLM-driven analysis: Context interpretation via prompts
  - ✅ Semantic search: Vector similarity for strategy/regulatory content

  5. RegulatoryAgent Simplification

  Current Problem: Complex ReAct pattern with detailed validation
  Solution: Simple LLM-based compliance check

  class RegulatoryAgent(BaseAgent):
      """Simplified regulatory validation via LLM"""

      async def validate_strategies(self, strategies: List[Strategy]) -> List[ValidationResult]:
          """High-level compliance validation"""

          results = []
          for strategy in strategies:
              # Simple regulatory context + LLM validation
              regulatory_context = await self._get_regulatory_context(strategy)
              validation = await self._llm_validate(strategy, regulatory_context)
              results.append(validation)

          return results

      async def _llm_validate(self, strategy, regulatory_context):
          """Single LLM call for compliance validation"""
          prompt = f"""
          Validate this healthcare strategy for compliance:
          Strategy: {strategy.approach}
          Regulatory Context: {regulatory_context}
          
          Provide: compliance_status (approved/flagged/rejected), reasons, confidence_score
          """

          response = await self.llm_client.generate(prompt)
          return self._parse_validation_response(response)

  6. Phase Documentation Removal

  Remove Closeout Sections

  Remove the following completion tracking sections from all documents:
  - Phase completion checklists
  - Detailed progress tracking
  - Granular task breakdowns
  - Complex handoff documentation

  Keep Essential Elements

  - Core implementation requirements
  - Database schema specifications
  - Interface definitions
  - Success criteria

  Updated Architecture Principles

  1. LLM-First Approach

  - Context Engineering: Provide rich context to LLMs
  - Prompt Engineering: Use well-crafted prompts for logic
  - Minimal Programming Logic: Avoid complex algorithms
  - Semantic Understanding: Leverage LLM reasoning over rule-based logic

  2. Simplified Tool Chain

  - Tavily: Single web search provider
  - SentenceBERT: Text similarity when needed
  - Supabase: Direct database access
  - LangGraph: Simple 4-node workflow orchestration

  3. MVP Focus

  - 4 Strategy Types: Speed, Cost, Effort, Balanced
  - High-Level Logic: Avoid granular analysis
  - Prompt-Driven: Use LLM capabilities over programming
  - Simple Validation: Basic compliance checking

  Implementation Priority

  Phase 1: Database Schema Update

  1. Update scoring fields from quality → effort
  2. Update constraints and indexes
  3. Update similarity search function

  Phase 2: Component Simplification

  1. Simplify StrategyMCP with Tavily integration
  2. Refactor StrategyCreator to 4-strategy prompt approach
  3. Simplify RegulatoryAgent to LLM-based validation
  4. Update StrategyMemoryLite for new scoring system

  Phase 3: Documentation Cleanup

  1. Remove granular phase tracking
  2. Update interface specifications
  3. Simplify success criteria
  4. Focus on MVP delivery

  Benefits of Simplified Approach

  Development Velocity

  - Faster Implementation: Less complex code to write
  - Easier Maintenance: Simpler logic to understand
  - Rapid Iteration: Prompt tuning vs algorithm development
  - Reduced Testing: Fewer edge cases and complex scenarios

  MVP Viability

  - Core Functionality: 4 strategy types with optimization
  - Usable Output: High-quality strategies via LLM reasoning
  - Scalable Foundation: Can add complexity later if needed
  - User Value: Immediate healthcare strategy assistance

  Technical Advantages

  - LLM Strengths: Leverage reasoning and language understanding
  - Context Rich: Provide comprehensive context for better decisions
  - Flexible: Easy to adjust via prompt modifications
  - Maintainable: Clear separation of concerns

  This refactor transforms the system from a complex analytical engine to a focused MVP that leverages LLM capabilities for healthcare strategy generation with speed/cost/effort optimization.