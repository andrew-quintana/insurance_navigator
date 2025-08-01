from pydantic import BaseModel
from typing import List, Dict, Any
from ..types import PlanConstraints, ContextRetrievalResult, StrategyScores

class StrategyCreatorInput(BaseModel):
    context: ContextRetrievalResult
    plan_constraints: PlanConstraints
    optimization_type: str

class StrategyCreatorOutput(BaseModel):
    title: str
    category: str
    approach: str
    rationale: str
    actionable_steps: List[str]
    llm_scores: StrategyScores 