-- Create strategies schema
CREATE SCHEMA IF NOT EXISTS strategies;

-- Core strategy metadata table with speed/cost/effort scoring
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

-- Vector embeddings table for semantic search
CREATE TABLE strategies.strategy_vectors (
  strategy_id UUID PRIMARY KEY REFERENCES strategies.strategies(id) ON DELETE CASCADE,
  embedding VECTOR(1536), -- OpenAI text-embedding-3-small
  model_version TEXT NOT NULL DEFAULT 'text-embedding-3-small',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Processing buffer table for reliability
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

-- Performance and reliability indexes
CREATE INDEX idx_strategies_constraints ON strategies.strategies USING gin(plan_constraints);
CREATE INDEX idx_strategies_llm_scores ON strategies.strategies (llm_score_speed, llm_score_cost, llm_score_effort);
CREATE INDEX idx_strategies_validation ON strategies.strategies (validation_status, created_at);
CREATE INDEX idx_strategy_vectors_embedding ON strategies.strategy_vectors USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_strategies_buffer_status ON strategies.strategies_buffer (status, expires_at);

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_strategies_updated_at BEFORE UPDATE
    ON strategies.strategies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS Policies (following existing patterns)
ALTER TABLE strategies.strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE strategies.strategy_vectors ENABLE ROW LEVEL SECURITY;
ALTER TABLE strategies.strategies_buffer ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (adjust based on existing auth patterns)
CREATE POLICY "Users can read their own strategies" ON strategies.strategies
    FOR SELECT USING (auth.uid() = author_id);

CREATE POLICY "Users can insert their own strategies" ON strategies.strategies
    FOR INSERT WITH CHECK (auth.uid() = author_id);

CREATE POLICY "Users can update their own strategies" ON strategies.strategies
    FOR UPDATE USING (auth.uid() = author_id);

-- Grant permissions
GRANT USAGE ON SCHEMA strategies TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA strategies TO postgres, service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA strategies TO authenticated; 