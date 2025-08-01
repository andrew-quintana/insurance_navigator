from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel

from ...patient_navigator.strategy.types import PlanConstraints, ContextRetrievalResult, SearchResult, QueryMetadata

@dataclass
class StrategyMCPConfig:
    tavily_api_key: str
    max_search_results: int
    search_timeout: int
    similarity_threshold: float

@dataclass
class WebSearchQuery:
    query: str
    optimization_type: Literal['speed', 'cost', 'effort']
    max_results: int

@dataclass
class SemanticSearchResult:
    strategy_id: str
    similarity: float
    content: str

@dataclass
class RegulatoryContextResult:
    context: str
    sources: List[Dict[str, Any]]

@dataclass
class PlanMetadata:
    plan_id: str
    plan_name: str
    insurance_provider: str
    plan_type: Literal['HMO', 'PPO', 'EPO', 'POS', 'HDHP']
    network_type: Literal['in-network', 'out-of-network', 'both']
    copay_structure: Dict[str, int]
    deductible: Dict[str, int]
    out_of_pocket_max: Dict[str, int]
    coverage_limits: Dict[str, Optional[int]]
    geographic_scope: Dict[str, List[str]]
    preferred_providers: Optional[List[str]] = None
    excluded_providers: Optional[List[str]] = None
    prior_authorization_required: List[str] = None
    step_therapy_required: List[str] = None

    def __post_init__(self):
        if self.prior_authorization_required is None:
            self.prior_authorization_required = []
        if self.step_therapy_required is None:
            self.step_therapy_required = [] 