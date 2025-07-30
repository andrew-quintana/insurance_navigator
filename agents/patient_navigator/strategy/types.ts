// Core plan constraints interface
export interface PlanConstraints {
  specialtyAccess: string;
  urgencyLevel: 'low' | 'medium' | 'high' | 'emergency';
  budgetConstraints?: {
    maxCost?: number;
    insuranceCoverage?: string;
  };
  locationConstraints?: {
    maxDistance?: number;
    preferredLocations?: string[];
  };
  timeConstraints?: {
    preferredTimeframe?: string;
    availabilityWindows?: string[];
  };
  additionalFactors?: Record<string, any>;
}

// Strategy scoring interface (speed/cost/effort)
export interface StrategyScores {
  speed: number;    // 0.0-1.0
  cost: number;     // 0.0-1.0  
  effort: number;   // 0.0-1.0
}

// Core strategy interface
export interface Strategy {
  id: string;
  title: string;
  category: string;
  approach: string;
  rationale: string;
  actionableSteps: any[];
  planConstraints: PlanConstraints;
  llmScores: StrategyScores;
  contentHash: string;
  validationStatus: 'pending' | 'approved' | 'flagged' | 'rejected';
  createdAt: Date;
}

// Context retrieval result interface
export interface ContextRetrievalResult {
  webSearchResults: SearchResult[];
  relevantStrategies: Strategy[];
  regulatoryContext: string;
  queryMetadata: QueryMetadata;
}

// Search result interface
export interface SearchResult {
  title: string;
  url: string;
  content: string;
  relevance: number;
}

// Query metadata interface
export interface QueryMetadata {
  generatedQueries: string[];
  searchDuration: number;
  resultCount: number;
}

// Validation result interface
export interface ValidationResult {
  strategyId: string;
  complianceStatus: 'approved' | 'flagged' | 'rejected';
  validationReasons: ValidationReason[];
  confidenceScore: number;
  sourceReferences: SourceReference[];
}

// Validation reason interface
export interface ValidationReason {
  category: 'legal' | 'feasibility' | 'ethical';
  description: string;
  severity: 'info' | 'warning' | 'critical';
}

// Source reference interface
export interface SourceReference {
  type: 'web' | 'regulatory' | 'document';
  url?: string;
  title: string;
  content: string;
  relevance: number;
}

// Storage result interface
export interface StorageResult {
  strategyId: string;
  storageStatus: 'success' | 'failed';
  vectorEmbeddingCreated: boolean;
  metadataStored: boolean;
  errorMessage?: string;
}

// Workflow state interface
export interface StrategyWorkflowState {
  planConstraints: PlanConstraints;
  contextResult?: ContextRetrievalResult;
  strategies?: Strategy[];
  validationResults?: ValidationResult[];
  storageConfirmation?: StorageResult;
  errors?: string[];
} 