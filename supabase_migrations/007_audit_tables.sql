-- =====================================================================
-- MAPS Supabase Migration 007: Audit and Tracking Tables
-- =====================================================================
-- Purpose: Comprehensive logging, batch tracking, and query analytics
-- Date: November 25, 2025
-- =====================================================================

-- ---------------------------------------------------------------------
-- Table: ingestion_logs
-- ---------------------------------------------------------------------
CREATE TABLE ingestion_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    batch_id UUID,  -- Can reference batch_metadata

    -- Log details
    log_level log_level_enum NOT NULL,
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,

    -- Operation metadata
    operation VARCHAR(100),  -- parse, validate, extract_keywords, etc.
    duration_ms INTEGER,
    file_location VARCHAR(500),  -- Source code file
    line_number INTEGER,  -- Source code line

    -- Timestamps
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_ingestion_logs_document_id ON ingestion_logs(document_id) WHERE document_id IS NOT NULL;
CREATE INDEX idx_ingestion_logs_batch_id ON ingestion_logs(batch_id) WHERE batch_id IS NOT NULL;
CREATE INDEX idx_ingestion_logs_log_level ON ingestion_logs(log_level);
CREATE INDEX idx_ingestion_logs_operation ON ingestion_logs(operation) WHERE operation IS NOT NULL;
CREATE INDEX idx_ingestion_logs_timestamp ON ingestion_logs(timestamp DESC);

-- Composite index for error queries
CREATE INDEX idx_ingestion_logs_level_timestamp ON ingestion_logs(log_level, timestamp DESC) WHERE log_level IN ('ERROR', 'CRITICAL');

-- GIN index for details JSONB
CREATE INDEX idx_ingestion_logs_details ON ingestion_logs USING gin(details);

-- Partitioning consideration: For large-scale deployments, consider partitioning by timestamp (monthly)
-- Example (uncomment if needed):
-- CREATE TABLE ingestion_logs_2025_11 PARTITION OF ingestion_logs
--     FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

COMMENT ON TABLE ingestion_logs IS 'Comprehensive operation logs with severity levels and performance metrics';
COMMENT ON COLUMN ingestion_logs.details IS 'JSONB for additional context (stack traces, field values, etc.)';
COMMENT ON COLUMN ingestion_logs.duration_ms IS 'Operation duration in milliseconds for performance tracking';

-- ---------------------------------------------------------------------
-- Table: batch_metadata
-- ---------------------------------------------------------------------
CREATE TABLE batch_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_name VARCHAR(255),
    profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    uploaded_by VARCHAR(255),

    -- Statistics
    total_files INTEGER DEFAULT 0,
    successful INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    skipped INTEGER DEFAULT 0,

    -- Performance metrics
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    total_duration_ms BIGINT,

    -- Status
    status batch_status_enum DEFAULT 'pending',
    error_summary TEXT,

    -- Additional metadata
    configuration JSONB DEFAULT '{}'::jsonb,
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_batch_metadata_profile_id ON batch_metadata(profile_id) WHERE profile_id IS NOT NULL;
CREATE INDEX idx_batch_metadata_status ON batch_metadata(status);
CREATE INDEX idx_batch_metadata_uploaded_by ON batch_metadata(uploaded_by) WHERE uploaded_by IS NOT NULL;
CREATE INDEX idx_batch_metadata_started_at ON batch_metadata(started_at DESC);
CREATE INDEX idx_batch_metadata_completed_at ON batch_metadata(completed_at DESC) WHERE completed_at IS NOT NULL;

-- GIN index for configuration
CREATE INDEX idx_batch_metadata_configuration ON batch_metadata USING gin(configuration);

-- Trigger
CREATE TRIGGER batch_metadata_update_timestamp
    BEFORE UPDATE ON batch_metadata
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE batch_metadata IS 'Batch processing tracking with statistics and performance metrics';
COMMENT ON COLUMN batch_metadata.configuration IS 'JSONB batch configuration (filters, options, parameters)';

-- ---------------------------------------------------------------------
-- Table: user_queries
-- ---------------------------------------------------------------------
CREATE TABLE user_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_text TEXT NOT NULL,
    filters JSONB DEFAULT '{}'::jsonb,
    results_count INTEGER DEFAULT 0,

    -- User tracking
    executed_by VARCHAR(255),

    -- Performance
    execution_time_ms DECIMAL(10, 2),

    -- Query metadata
    query_type VARCHAR(100),  -- search, filter, export, etc.
    api_endpoint VARCHAR(255),

    -- Timestamps
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_user_queries_executed_by ON user_queries(executed_by) WHERE executed_by IS NOT NULL;
CREATE INDEX idx_user_queries_query_type ON user_queries(query_type) WHERE query_type IS NOT NULL;
CREATE INDEX idx_user_queries_timestamp ON user_queries(timestamp DESC);
CREATE INDEX idx_user_queries_execution_time ON user_queries(execution_time_ms DESC) WHERE execution_time_ms IS NOT NULL;

-- GIN indexes
CREATE INDEX idx_user_queries_filters ON user_queries USING gin(filters);
CREATE INDEX idx_user_queries_text_search ON user_queries USING gin(to_tsvector('english', query_text));

COMMENT ON TABLE user_queries IS 'Search and query analytics for performance monitoring and usage patterns';
COMMENT ON COLUMN user_queries.filters IS 'JSONB filters applied to query (date ranges, categories, etc.)';

-- ---------------------------------------------------------------------
-- Table: system_metrics (Optional - for monitoring)
-- ---------------------------------------------------------------------
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15, 6) NOT NULL,
    metric_unit VARCHAR(50),  -- count, milliseconds, bytes, percentage, etc.

    -- Context
    metric_category VARCHAR(100),  -- performance, storage, usage, errors
    tags JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_system_metrics_metric_name ON system_metrics(metric_name);
CREATE INDEX idx_system_metrics_category ON system_metrics(metric_category) WHERE metric_category IS NOT NULL;
CREATE INDEX idx_system_metrics_recorded_at ON system_metrics(recorded_at DESC);

-- Composite index for time-series queries
CREATE INDEX idx_system_metrics_name_time ON system_metrics(metric_name, recorded_at DESC);

-- GIN index for tags
CREATE INDEX idx_system_metrics_tags ON system_metrics USING gin(tags);

COMMENT ON TABLE system_metrics IS 'System-wide performance and usage metrics for monitoring dashboards';
COMMENT ON COLUMN system_metrics.tags IS 'JSONB tags for metric dimensions (environment, component, etc.)';

-- =====================================================================
-- Helper Function: Get ingestion health for last N days
-- =====================================================================
CREATE OR REPLACE FUNCTION get_ingestion_health(days INTEGER DEFAULT 30)
RETURNS TABLE (
    date DATE,
    total_documents INTEGER,
    successful INTEGER,
    failed INTEGER,
    avg_processing_time_ms NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.ingestion_timestamp::DATE AS date,
        COUNT(*)::INTEGER AS total_documents,
        SUM(CASE WHEN d.status = 'completed' THEN 1 ELSE 0 END)::INTEGER AS successful,
        SUM(CASE WHEN d.status = 'failed' THEN 1 ELSE 0 END)::INTEGER AS failed,
        AVG(d.processing_duration_ms)::NUMERIC AS avg_processing_time_ms
    FROM documents d
    WHERE d.ingestion_timestamp >= NOW() - (days || ' days')::INTERVAL
    GROUP BY d.ingestion_timestamp::DATE
    ORDER BY d.ingestion_timestamp::DATE DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_ingestion_health(INTEGER) IS 'Returns daily ingestion statistics for last N days';

-- =====================================================================
-- Helper Function: Get batch processing summary
-- =====================================================================
CREATE OR REPLACE FUNCTION get_batch_summary(batch_uuid UUID)
RETURNS TABLE (
    batch_id UUID,
    batch_name VARCHAR,
    total_files INTEGER,
    successful INTEGER,
    failed INTEGER,
    duration_seconds NUMERIC,
    avg_file_time_ms NUMERIC,
    error_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        bm.id AS batch_id,
        bm.batch_name,
        bm.total_files,
        bm.successful,
        bm.failed,
        (EXTRACT(EPOCH FROM (bm.completed_at - bm.started_at)))::NUMERIC AS duration_seconds,
        (bm.total_duration_ms::NUMERIC / NULLIF(bm.total_files, 0))::NUMERIC AS avg_file_time_ms,
        (bm.failed::NUMERIC / NULLIF(bm.total_files, 0) * 100)::NUMERIC AS error_rate
    FROM batch_metadata bm
    WHERE bm.id = batch_uuid;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_batch_summary(UUID) IS 'Returns comprehensive summary for a specific batch';

-- =====================================================================
-- Update schema version
-- =====================================================================
INSERT INTO schema_versions (version, description)
VALUES (7, 'Audit and tracking tables (ingestion_logs, batch_metadata, user_queries, system_metrics)');

-- =====================================================================
-- Verification Query
-- =====================================================================
-- Run this to verify tables are created:
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
-- AND table_name IN ('ingestion_logs', 'batch_metadata', 'user_queries', 'system_metrics')
-- ORDER BY table_name;
--
-- Check functions:
-- SELECT proname FROM pg_proc WHERE proname IN ('get_ingestion_health', 'get_batch_summary');

-- =====================================================================
-- END OF MIGRATION 007
-- =====================================================================
