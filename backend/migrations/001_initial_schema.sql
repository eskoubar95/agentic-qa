-- Agentic QA - Initial schema
-- Idempotent migration: uses IF NOT EXISTS where applicable

-- Schema migrations tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Tests: User-defined test definitions
CREATE TABLE IF NOT EXISTS tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    definition JSONB NOT NULL DEFAULT '{}',
    auto_handle_popups BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

COMMENT ON TABLE tests IS 'Test definitions with steps, URL, and popup handling config';

-- Test runs: Execution history for each test
CREATE TABLE IF NOT EXISTS test_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id UUID NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'queued',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    screenshots JSONB,
    logs JSONB,
    step_results JSONB,
    self_healed BOOLEAN DEFAULT false,
    llm_calls INTEGER DEFAULT 0,
    cost_usd DECIMAL(10, 6) DEFAULT 0,
    error TEXT,
    error_step INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

COMMENT ON TABLE test_runs IS 'Execution results; status: queued|running|passed|failed';

-- Session memory: Cached selectors/strategies for self-healing
CREATE TABLE IF NOT EXISTS session_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instruction_hash TEXT NOT NULL UNIQUE,
    page_url TEXT NOT NULL,
    instruction TEXT NOT NULL,
    action_data JSONB NOT NULL DEFAULT '{}',
    reliability_score REAL DEFAULT 1.0,
    success_count INTEGER DEFAULT 1,
    failure_count INTEGER DEFAULT 0,
    last_used TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

COMMENT ON TABLE session_memory IS 'Cached action strategies for self-healing; keyed by instruction hash';

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_test_runs_test_id ON test_runs(test_id);
CREATE INDEX IF NOT EXISTS idx_test_runs_status ON test_runs(status);
CREATE INDEX IF NOT EXISTS idx_test_runs_created_at ON test_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tests_user_id ON tests(user_id);
CREATE INDEX IF NOT EXISTS idx_tests_created_at ON tests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_session_memory_instruction_hash ON session_memory(instruction_hash);
CREATE INDEX IF NOT EXISTS idx_session_memory_last_used ON session_memory(last_used DESC);
CREATE INDEX IF NOT EXISTS idx_session_memory_reliability ON session_memory(reliability_score DESC);
