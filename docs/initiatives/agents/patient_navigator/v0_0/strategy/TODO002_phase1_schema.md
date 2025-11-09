# Phase 1 Database Schema Decisions - Strategy System MVP

## Schema Overview

The MVP database schema implements a simplified 2-table design optimized for healthcare strategy generation with speed/cost/effort optimization.

### Core Tables

#### 1. `strategies.strategies` - Main Strategy Metadata
```sql
CREATE TABLE strategies.strategies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  category TEXT NOT NULL,
  approach TEXT NOT NULL,
  rationale TEXT NOT NULL,
  actionable_steps JSONB NOT NULL,
  plan_constraints JSONB NOT NULL,
  
  -- Speed/Cost/Effort scoring (replacing quality per REFACTOR001.md)
  llm_score_speed NUMERIC(3,2) CHECK (llm_score_speed >= 0.0 AND llm_score_speed <= 1.0),
  llm_score_cost NUMERIC(3,2) CHECK (llm_score_cost >= 0.0 AND llm_score_cost <= 1.0),
  llm_score_effort NUMERIC(3,2) CHECK (llm_score_effort >= 0.0 AND llm_score_effort <= 1.0),
  
  -- Human effectiveness scoring (1.0-5.0)
  human_score_effectiveness NUMERIC(3,2) CHECK (human_score_effectiveness >= 1.0 AND human_score_effectiveness <= 5.0),
  num_ratings INTEGER DEFAULT 0,
  
  -- Reliability and validation fields
  content_hash TEXT UNIQUE, -- For deduplication
  validation_status TEXT DEFAULT 'pending' CHECK (validation_status IN ('pending', 'approved', 'flagged', 'rejected')),
  
  author_id UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### 2. `strategies.strategy_vectors` - Vector Embeddings
```sql
CREATE TABLE strategies.strategy_vectors (
  strategy_id UUID PRIMARY KEY REFERENCES strategies.strategies(id) ON DELETE CASCADE,
  embedding VECTOR(1536), -- OpenAI text-embedding-3-small
  model_version TEXT NOT NULL DEFAULT 'text-embedding-3-small',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### 3. `strategies.strategies_buffer` - Processing Reliability
```sql
CREATE TABLE strategies.strategies_buffer (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  strategy_data JSONB NOT NULL,
  content_hash TEXT NOT NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'abandoned')),
  retry_count INTEGER DEFAULT 0,
  expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '24 hours'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## Design Decisions

### 1. MVP 2-Table Approach vs Complex Multi-Table

**Decision**: Simplified `strategies.strategies` + `strategies.strategy_vectors` approach

**Rationale**:
- **Performance**: JOIN operations faster than complex nested queries
- **Maintainability**: Clear separation of metadata vs. vector operations
- **Scalability**: Follows existing pgvector patterns from documents schema
- **Development Speed**: Reduced migration complexity

**Alternatives Considered**:
- Single table with embedded vectors (rejected: query performance issues)
- Multi-table normalized design (rejected: over-engineering for MVP)

### 2. Speed/Cost/Effort vs Speed/Cost/Quality Optimization

**Decision**: Replace quality metrics with effort measurement

**Rationale**:
- **User Value**: Effort measurement more actionable for healthcare consumers
- **Measurability**: Effort easier to quantify than subjective quality
- **Differentiation**: Creates distinct optimization strategies
- **Practical Focus**: Aligns with real-world healthcare decision factors

**Database Migration**:
```sql
ALTER TABLE strategies.strategies 
  RENAME COLUMN llm_score_quality TO llm_score_effort;
```

### 3. Dual Scoring System

**Decision**: LLM scores (0.0-1.0) + human effectiveness scores (1.0-5.0)

**Rationale**:
- **LLM Scores**: Generated during strategy creation for immediate optimization
- **Human Scores**: Updated via user feedback for long-term improvement
- **Different Scales**: Prevents confusion between automated and human ratings
- **Embedded Storage**: Avoids complex joins while supporting future enhancements

### 4. Content Hash Deduplication

**Decision**: Use content_hash as unique constraint for deduplication

**Rationale**:
- **Idempotency**: Prevents duplicate strategies from multiple processing attempts
- **Performance**: Fast lookup for existing strategies
- **Reliability**: Handles processing failures gracefully
- **Storage Efficiency**: Reduces database bloat from duplicates

### 5. Processing Buffer Table

**Decision**: Separate buffer table for reliability

**Rationale**:
- **Failure Handling**: Captures failed processing attempts
- **Retry Logic**: Supports automatic retry with exponential backoff
- **Cleanup**: TTL-based expiration prevents unbounded growth
- **Monitoring**: Clear status tracking for operational visibility

## Performance Optimizations

### Indexing Strategy

#### 1. Constraint-Based Filtering
```sql
CREATE INDEX idx_strategies_constraints ON strategies.strategies USING gin(plan_constraints);
```
- **Purpose**: Fast filtering by plan constraints (specialty, urgency, budget, etc.)
- **Type**: GIN index for JSONB operations
- **Performance**: Sub-100ms constraint-based queries

#### 2. LLM Score Optimization
```sql
CREATE INDEX idx_strategies_llm_scores ON strategies.strategies (llm_score_speed, llm_score_cost, llm_score_effort);
```
- **Purpose**: Fast sorting and filtering by optimization scores
- **Type**: Composite index for multi-dimensional scoring
- **Performance**: Efficient strategy ranking and retrieval

#### 3. Vector Similarity Search
```sql
CREATE INDEX idx_strategy_vectors_embedding ON strategies.strategy_vectors USING ivfflat (embedding vector_cosine_ops);
```
- **Purpose**: Fast semantic similarity search
- **Type**: ivfflat index for pgvector operations
- **Performance**: Sub-100ms vector similarity queries

#### 4. Validation Status Filtering
```sql
CREATE INDEX idx_strategies_validation ON strategies.strategies (validation_status, created_at);
```
- **Purpose**: Fast filtering by validation status and recency
- **Type**: Composite index for status-based queries
- **Performance**: Efficient validation workflow management

#### 5. Buffer Status Management
```sql
CREATE INDEX idx_strategies_buffer_status ON strategies.strategies_buffer (status, expires_at);
```
- **Purpose**: Fast cleanup of expired buffer entries
- **Type**: Composite index for status and TTL management
- **Performance**: Efficient buffer maintenance

### Query Optimization Patterns

#### 1. Constraint-Based Pre-Filtering
```sql
-- Example: Find strategies for cardiology with high urgency
SELECT * FROM strategies.strategies 
WHERE plan_constraints @> '{"specialtyAccess": "cardiology", "urgencyLevel": "high"}'
ORDER BY llm_score_speed DESC;
```

#### 2. Vector Similarity with Metadata Filtering
```sql
-- Example: Semantic search with constraint filtering
SELECT s.*, sv.embedding 
FROM strategies.strategies s
JOIN strategies.strategy_vectors sv ON s.id = sv.strategy_id
WHERE s.validation_status = 'approved'
  AND s.plan_constraints @> '{"specialtyAccess": "cardiology"}'
ORDER BY sv.embedding <=> $1::vector;
```

#### 3. Dual Scoring Queries
```sql
-- Example: Strategies with high LLM scores and human ratings
SELECT * FROM strategies.strategies 
WHERE llm_score_speed > 0.8 
  AND human_score_effectiveness > 4.0
  AND num_ratings >= 5;
```

## Security & Access Control

### Row Level Security (RLS)

#### 1. User-Based Access Control
```sql
CREATE POLICY "Users can read their own strategies" ON strategies.strategies
    FOR SELECT USING (auth.uid() = author_id);

CREATE POLICY "Users can insert their own strategies" ON strategies.strategies
    FOR INSERT WITH CHECK (auth.uid() = author_id);

CREATE POLICY "Users can update their own strategies" ON strategies.strategies
    FOR UPDATE USING (auth.uid() = author_id);
```

**Rationale**:
- **Data Isolation**: Users can only access their own strategies
- **Privacy Protection**: Prevents cross-user data leakage
- **Compliance**: Supports healthcare privacy requirements
- **Scalability**: Efficient for multi-tenant deployments

#### 2. Service Role Access
```sql
GRANT ALL ON ALL TABLES IN SCHEMA strategies TO postgres, service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA strategies TO authenticated;
```

**Rationale**:
- **System Operations**: Service role for automated processing
- **User Access**: Authenticated users can read shared strategies
- **Admin Access**: Postgres role for maintenance operations

### Data Protection Features

#### 1. Content Hash Deduplication
- **Purpose**: Prevents duplicate strategy storage
- **Implementation**: UNIQUE constraint on content_hash
- **Benefits**: Storage efficiency and data integrity

#### 2. Audit Trail
- **Purpose**: Complete strategy lifecycle tracking
- **Implementation**: created_at, updated_at timestamps
- **Benefits**: Compliance and debugging support

#### 3. Validation Status Tracking
- **Purpose**: Regulatory compliance workflow
- **Implementation**: Status enum with audit trail
- **Benefits**: Quality assurance and compliance

## Scalability Considerations

### Horizontal Scaling Readiness

#### 1. Stateless Design
- **Strategy Generation**: No session state required
- **Vector Operations**: Distributed across read replicas
- **Caching Strategy**: Redis/memory caching for hot data

#### 2. Database Partitioning
- **Future Consideration**: Partition by author_id for large deployments
- **Current Design**: Single table with efficient indexing
- **Migration Path**: Easy to add partitioning later

#### 3. Vector Search Scaling
- **Current**: Single pgvector instance
- **Future**: Horizontal read replicas for vector operations
- **Performance**: Sub-100ms queries with proper indexing

### Storage Efficiency

#### 1. Embedded Scoring
- **Approach**: Store scores directly in strategy table
- **Benefits**: No complex joins for common queries
- **Trade-offs**: Slightly larger row size vs. query performance

#### 2. JSONB Constraints
- **Approach**: Flexible constraint storage with GIN indexing
- **Benefits**: Schema flexibility and query performance
- **Trade-offs**: Less structured than normalized approach

#### 3. Vector Storage
- **Approach**: Separate table for embeddings
- **Benefits**: Isolated vector operations and storage
- **Trade-offs**: Additional JOIN for similarity queries

## Migration Strategy

### Phase 1 Implementation
1. **Schema Creation**: All tables and indexes created
2. **RLS Policies**: Basic user-based access control
3. **Triggers**: Updated timestamp management
4. **Permissions**: Service role and user access granted

### Future Migrations
1. **Quality → Effort**: Rename column when needed
2. **Partitioning**: Add table partitioning for scale
3. **Additional Indexes**: Performance optimization based on usage
4. **Enhanced RLS**: More granular access control

## Monitoring & Maintenance

### Performance Monitoring
- **Query Performance**: Track execution times for common queries
- **Index Usage**: Monitor index effectiveness
- **Storage Growth**: Track table and index sizes
- **Vector Operations**: Monitor similarity search performance

### Maintenance Tasks
- **Regular VACUUM**: Clean up deleted rows and update statistics
- **Index Maintenance**: Rebuild indexes as needed
- **Buffer Cleanup**: Remove expired buffer entries
- **Statistics Updates**: Keep query planner statistics current

## Conclusion

The MVP database schema provides a solid foundation for the Strategy Evaluation & Validation System with:

1. **Performance**: Optimized for sub-100ms queries
2. **Scalability**: Ready for horizontal scaling
3. **Security**: Comprehensive access control
4. **Reliability**: Buffer table for failure handling
5. **Maintainability**: Clean separation of concerns

This design supports the 4-component workflow (StrategyMCP → StrategyCreator → RegulatoryAgent → StrategyMemoryLite) while maintaining the flexibility to evolve with future requirements. 