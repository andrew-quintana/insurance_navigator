import { StrategyWorkflowState, PlanConstraints, ContextRetrievalResult, Strategy, ValidationResult, StorageResult } from '../types';

/**
 * Workflow State Management for Strategy Generation
 * 
 * Manages the state transitions in the LangGraph workflow:
 * 1. Context Gathering → 2. Strategy Generation → 3. Regulatory Validation → 4. Storage
 */

export class StrategyWorkflowStateManager {
  private state: StrategyWorkflowState;

  constructor(initialConstraints: PlanConstraints) {
    this.state = {
      planConstraints: initialConstraints,
      errors: []
    };
  }

  /**
   * Update context gathering results
   */
  updateContextResult(contextResult: ContextRetrievalResult): void {
    this.state.contextResult = contextResult;
  }

  /**
   * Update generated strategies
   */
  updateStrategies(strategies: Strategy[]): void {
    this.state.strategies = strategies;
  }

  /**
   * Update validation results
   */
  updateValidationResults(validationResults: ValidationResult[]): void {
    this.state.validationResults = validationResults;
  }

  /**
   * Update storage confirmation
   */
  updateStorageConfirmation(storageConfirmation: StorageResult): void {
    this.state.storageConfirmation = storageConfirmation;
  }

  /**
   * Add error to state
   */
  addError(error: string): void {
    if (!this.state.errors) {
      this.state.errors = [];
    }
    this.state.errors.push(error);
  }

  /**
   * Get current state
   */
  getState(): StrategyWorkflowState {
    return { ...this.state };
  }

  /**
   * Check if workflow has errors
   */
  hasErrors(): boolean {
    return !!(this.state.errors && this.state.errors.length > 0);
  }

  /**
   * Get all errors
   */
  getErrors(): string[] {
    return this.state.errors || [];
  }

  /**
   * Validate state completeness
   */
  validateState(): boolean {
    return !!(this.state.planConstraints) &&
           !!(this.state.contextResult) &&
           !!(this.state.strategies) &&
           !!(this.state.validationResults) &&
           !!(this.state.storageConfirmation);
  }
} 