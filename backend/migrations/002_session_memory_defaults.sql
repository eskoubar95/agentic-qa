-- Align session_memory defaults and indexing with spec (when 001 already applied)
ALTER TABLE session_memory ALTER COLUMN reliability_score SET DEFAULT 1.0;
ALTER TABLE session_memory ALTER COLUMN success_count SET DEFAULT 1;
CREATE INDEX IF NOT EXISTS idx_session_memory_reliability ON session_memory(reliability_score DESC);
