-- Generic Agent Tracer database schema for PostgreSQL

-- Traces table (generic)
CREATE TABLE IF NOT EXISTS agent_tracer_traces (
    trace_id UUID PRIMARY KEY,
    trace_type VARCHAR(100) NOT NULL DEFAULT 'agent_execution',
    status VARCHAR(50) NOT NULL,

    -- Generic trigger info
    trigger_type VARCHAR(100) NOT NULL,
    trigger_source VARCHAR(100),
    triggered_by VARCHAR(255),
    triggered_at TIMESTAMP NOT NULL,

    -- Timing
    created_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_ms INTEGER,

    -- All agent-specific metadata stored as JSONB
    metadata JSONB NOT NULL DEFAULT '{}',

    -- Summary metrics
    total_spans INTEGER,
    failed_spans INTEGER,
    summary_metrics JSONB DEFAULT '{}',  -- Custom metrics per agent system

    -- Reference to full trace
    trace_document_url TEXT
);

-- Generic indexes
CREATE INDEX IF NOT EXISTS idx_traces_created_at ON agent_tracer_traces(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_traces_trigger ON agent_tracer_traces(triggered_by, trigger_type);
CREATE INDEX IF NOT EXISTS idx_traces_status ON agent_tracer_traces(status);

-- JSONB indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_traces_metadata ON agent_tracer_traces USING GIN(metadata);

-- Spans table (generic)
CREATE TABLE IF NOT EXISTS agent_tracer_spans (
    span_id VARCHAR(255) PRIMARY KEY,
    trace_id UUID NOT NULL REFERENCES agent_tracer_traces(trace_id) ON DELETE CASCADE,
    parent_span_id VARCHAR(255),

    name VARCHAR(255) NOT NULL,
    span_type VARCHAR(100),
    status VARCHAR(50),

    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_ms INTEGER,

    -- Agent metadata as JSONB
    agent_metadata JSONB DEFAULT '{}',

    span_document_url TEXT
);

-- Generic span indexes
CREATE INDEX IF NOT EXISTS idx_spans_trace ON agent_tracer_spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_spans_type ON agent_tracer_spans(span_type);
CREATE INDEX IF NOT EXISTS idx_spans_status ON agent_tracer_spans(status);
CREATE INDEX IF NOT EXISTS idx_spans_agent_metadata ON agent_tracer_spans USING GIN(agent_metadata);

-- Example queries:
-- SELECT * FROM agent_tracer_traces WHERE metadata->>'job_id' = 'auth-service';
-- SELECT * FROM agent_tracer_traces WHERE metadata->>'alert_name' = 'HighCPUUsage';
