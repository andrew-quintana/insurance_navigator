import { tavily } from '@tavily/core';
import { createClient } from '@supabase/supabase-js';
import { StrategyMCPConfig, WebSearchQuery, SemanticSearchResult, RegulatoryContextResult, PlanMetadata } from './types';
import { PlanConstraints, ContextRetrievalResult, SearchResult, QueryMetadata } from '../../../patient_navigator/strategy/types';

/**
 * StrategyMCP Tool - Context Gathering for Strategy Generation
 * 
 * Simplified context coordinator using Tavily-only web search and semantic similarity
 * for existing strategies. Follows the MCP tool pattern from existing architecture.
 */
export class StrategyMCPTool {
  private tavily: any;
  private supabase: any;
  private config: StrategyMCPConfig;

  constructor(config: StrategyMCPConfig) {
    this.config = config;
    this.tavily = tavily({ apiKey: config.tavilyApiKey });
    this.supabase = createClient(
      process.env.SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!
    );
  }

  /**
   * Main context gathering method
   */
  async gatherContext(planConstraints: PlanConstraints): Promise<ContextRetrievalResult> {
    const startTime = Date.now();
    
    try {
      // 1. Retrieve plan metadata for context
      const planMetadata = await this.getPlanMetadata(planConstraints);
      
      // 2. Generate web search queries with plan context
      const webSearchQueries = this.generateWebSearchQueries(planConstraints, planMetadata);
      
      // 3. Perform web searches
      const webSearchResults = await this.performWebSearches(webSearchQueries);
      
      // 4. Semantic search of existing strategies with plan context
      const relevantStrategies = await this.searchSimilarStrategies(planConstraints, planMetadata);
      
      // 5. Retrieve regulatory context
      const regulatoryContext = await this.getRegulatoryContext(planConstraints);
      
      const queryMetadata: QueryMetadata = {
        generatedQueries: webSearchQueries.map(q => q.query),
        searchDuration: Date.now() - startTime,
        resultCount: webSearchResults.length
      };

      return {
        webSearchResults,
        relevantStrategies,
        regulatoryContext: regulatoryContext.context,
        queryMetadata
      };
    } catch (error) {
      console.error('Error in context gathering:', error);
      throw error;
    }
  }

  /**
   * Mock plan metadata retrieval - will be replaced with actual plan metadata table
   */
  private async getPlanMetadata(planConstraints: PlanConstraints): Promise<PlanMetadata> {
    // Mock implementation based on typical HMO plan structures
    // In future this will query a plan metadata table
    const mockPlanMetadata: PlanMetadata = {
      planId: 'scan-classic-hmo-001',
      planName: 'SCAN Classic HMO',
      insuranceProvider: 'SCAN Health Plan',
      planType: 'HMO',
      networkType: 'in-network',
      copayStructure: {
        primaryCare: 0,        // HMO typically $0 copay for primary care
        specialist: 25,        // Specialist visits
        urgentCare: 50,        // Urgent care visits
        emergency: 100         // Emergency room visits
      },
      deductible: {
        individual: 0,         // HMO often has $0 deductible
        family: 0
      },
      outOfPocketMax: {
        individual: 4500,      // Annual out-of-pocket maximum
        family: 9000
      },
      coverageLimits: {
        annualVisits: 12,      // Primary care visits per year
        specialistVisits: 8,   // Specialist visits per year
        physicalTherapy: 20    // Physical therapy sessions
      },
      geographicScope: {
        states: ['CA'],
        counties: ['Los Angeles', 'Orange', 'San Diego', 'Riverside', 'San Bernardino'],
        zipCodes: ['90210', '90211', '90212', '92614', '92615', '92101', '92102']
      },
      preferredProviders: [
        'Kaiser Permanente',
        'Cedars-Sinai Medical Center',
        'UCLA Health',
        'USC Keck Medicine',
        'Hoag Memorial Hospital',
        'Scripps Health'
      ],
      excludedProviders: [
        'Some Excluded Provider Network',
        'Out-of-Network Specialists'
      ],
      priorAuthorizationRequired: [
        'MRI',
        'CT Scan',
        'Specialist Referral',
        'Physical Therapy',
        'Chiropractic Care',
        'Mental Health Services',
        'Durable Medical Equipment'
      ],
      stepTherapyRequired: [
        'Physical Therapy',
        'Chiropractic Care',
        'Mental Health Services',
        'Prescription Medications'
      ]
    };

    return mockPlanMetadata;
  }

  /**
   * Generate web search queries with plan context for each optimization type
   */
  private generateWebSearchQueries(planConstraints: PlanConstraints, planMetadata: PlanMetadata): WebSearchQuery[] {
    const { specialtyAccess, urgencyLevel } = planConstraints;
    const { planType, networkType, copayStructure, deductible, geographicScope } = planMetadata;
    
    // Create context-rich queries that include plan details
    const planContext = `${planType} plan ${networkType} network $${copayStructure.specialist} specialist copay $${deductible.individual} deductible`;
    const locationContext = geographicScope.states.length > 0 ? `in ${geographicScope.states.join(', ')}` : '';
    
    return [
      {
        query: `fastest healthcare ${specialtyAccess} access ${urgencyLevel} urgency ${planContext} ${locationContext} immediate appointment SCAN Health Plan`,
        optimizationType: 'speed',
        maxResults: 3
      },
      {
        query: `cheapest healthcare ${specialtyAccess} options cost-effective ${planContext} ${locationContext} low cost providers SCAN HMO network`,
        optimizationType: 'cost',
        maxResults: 3
      },
      {
        query: `easiest healthcare ${specialtyAccess} process minimal effort ${planContext} ${locationContext} streamlined access SCAN Classic HMO`,
        optimizationType: 'effort',
        maxResults: 3
      }
    ];
  }

  /**
   * Perform web searches using Tavily
   */
  private async performWebSearches(queries: WebSearchQuery[]): Promise<SearchResult[]> {
    const results: SearchResult[] = [];
    
    for (const query of queries) {
      try {
        const searchResult = await this.tavily.search(query.query);
        
        // Transform Tavily results to our format
        const transformedResults: SearchResult[] = searchResult.results.map((result: any) => ({
          title: result.title,
          url: result.url,
          content: result.content,
          relevance: 0.8 // Default relevance score
        }));

        results.push(...transformedResults);
      } catch (error) {
        console.error(`Error searching for query "${query.query}":`, error);
        // Continue with other queries
      }
    }

    return results;
  }

  /**
   * Search for similar existing strategies using vector similarity with plan context
   */
  private async searchSimilarStrategies(planConstraints: PlanConstraints, planMetadata: PlanMetadata): Promise<any[]> {
    try {
      // Create embedding for plan constraints with plan metadata context
      const constraintText = this.createConstraintTextWithPlanContext(planConstraints, planMetadata);
      
      // TODO: Implement vector similarity search with plan context
      // This would require embedding generation and pgvector query with plan metadata
      // For MVP, return empty array
      return [];
    } catch (error) {
      console.error('Error in semantic strategy search:', error);
      return [];
    }
  }

  /**
   * Get regulatory context from documents schema
   */
  private async getRegulatoryContext(planConstraints: PlanConstraints): Promise<RegulatoryContextResult> {
    try {
      // TODO: Implement regulatory context retrieval from documents schema
      // For MVP, return basic context
      return {
        context: `Healthcare regulations for ${planConstraints.specialtyAccess} services`,
        sources: ['regulatory_documents'],
        relevance: 0.7
      };
    } catch (error) {
      console.error('Error getting regulatory context:', error);
      return {
        context: 'Basic healthcare compliance guidelines',
        sources: [],
        relevance: 0.5
      };
    }
  }

  /**
   * Create text representation of plan constraints with plan metadata for embedding
   */
  private createConstraintTextWithPlanContext(planConstraints: PlanConstraints, planMetadata: PlanMetadata): string {
    const { specialtyAccess, urgencyLevel, budgetConstraints, locationConstraints, timeConstraints } = planConstraints;
    const { planType, networkType, copayStructure, deductible, geographicScope, preferredProviders } = planMetadata;
    
    const parts = [
      `Specialty: ${specialtyAccess}`,
      `Urgency: ${urgencyLevel}`,
      `Plan Type: ${planType}`,
      `Network: ${networkType}`,
      `Specialist Copay: $${copayStructure.specialist}`,
      `Deductible: $${deductible.individual}`,
      budgetConstraints ? `Budget: ${JSON.stringify(budgetConstraints)}` : '',
      locationConstraints ? `Location: ${JSON.stringify(locationConstraints)}` : '',
      timeConstraints ? `Time: ${JSON.stringify(timeConstraints)}` : '',
      geographicScope.states.length > 0 ? `States: ${geographicScope.states.join(', ')}` : '',
      preferredProviders && preferredProviders.length > 0 ? `Preferred Providers: ${preferredProviders.join(', ')}` : ''
    ];
    
    return parts.filter(part => part).join(' ');
  }

  /**
   * Create text representation of plan constraints for embedding (legacy method)
   */
  private createConstraintText(planConstraints: PlanConstraints): string {
    const parts = [
      `Specialty: ${planConstraints.specialtyAccess}`,
      `Urgency: ${planConstraints.urgencyLevel}`,
      planConstraints.budgetConstraints ? `Budget: ${JSON.stringify(planConstraints.budgetConstraints)}` : '',
      planConstraints.locationConstraints ? `Location: ${JSON.stringify(planConstraints.locationConstraints)}` : '',
      planConstraints.timeConstraints ? `Time: ${JSON.stringify(planConstraints.timeConstraints)}` : ''
    ];
    
    return parts.filter(part => part).join(' ');
  }
} 