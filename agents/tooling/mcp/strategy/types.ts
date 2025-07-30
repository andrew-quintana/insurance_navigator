import { PlanConstraints, ContextRetrievalResult, SearchResult, QueryMetadata } from '../../../patient_navigator/strategy/types';

export interface StrategyMCPConfig {
  tavilyApiKey: string;
  maxSearchResults: number;
  searchTimeout: number;
  similarityThreshold: number;
}

export interface WebSearchQuery {
  query: string;
  optimizationType: 'speed' | 'cost' | 'effort';
  maxResults: number;
}

export interface SemanticSearchResult {
  strategyId: string;
  similarity: number;
  content: string;
}

export interface RegulatoryContextResult {
  context: string;
  sources: string[];
  relevance: number;
}

// Plan metadata interface for context integration
export interface PlanMetadata {
  planId: string;
  planName: string;
  insuranceProvider: string;
  planType: 'HMO' | 'PPO' | 'EPO' | 'POS' | 'HDHP';
  networkType: 'in-network' | 'out-of-network' | 'both';
  copayStructure: {
    primaryCare: number;
    specialist: number;
    urgentCare: number;
    emergency: number;
  };
  deductible: {
    individual: number;
    family: number;
  };
  outOfPocketMax: {
    individual: number;
    family: number;
  };
  coverageLimits: {
    annualVisits?: number;
    specialistVisits?: number;
    physicalTherapy?: number;
  };
  geographicScope: {
    states: string[];
    counties?: string[];
    zipCodes?: string[];
  };
  preferredProviders?: string[];
  excludedProviders?: string[];
  priorAuthorizationRequired: string[];
  stepTherapyRequired: string[];
} 