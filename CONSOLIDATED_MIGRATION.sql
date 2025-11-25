-- =====================================================================
-- MAPS CONSOLIDATED MIGRATION - SINGLE FILE DEPLOYMENT
-- =====================================================================
-- Purpose: Deploy complete MAPS database schema in one execution
-- Date: November 25, 2025
-- Version: 1.0
--
-- This file consolidates migrations from:
--   - 001_initial_schema.sql
--   - 002_add_keyword_enhancements.sql
--   - 015_detection_details_table.sql
--   - 016_documents_enhancements.sql
--   - Performance indexes
--
-- INSTRUCTIONS:
-- 1. Copy this entire file
-- 2. Paste into Supabase SQL Editor
-- 3. Click "Run"
-- 4. Wait for completion (~30 seconds)
-- 5. Run verification queries at the end
-- =====================================================================

-- =====================================================================
-- CLEANUP (Optional - only if starting fresh)
-- =====================================================================
-- Uncomment the following if you want to drop existing tables first:
-- DROP TABLE IF EXISTS case_patterns CASCADE;
-- DROP SCHEMA IF EXISTS public CASCADE;
-- CREATE SCHEMA public;
-- GRANT ALL ON SCHEMA public TO postgres;
-- GRANT ALL ON SCHEMA public TO public;

-- =====================================================================
-- SECTION 1: EXTENSIONS
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================================
-- SECTION 2: CORE TABLES
-- =====================================================================

-- documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_file_name VARCHAR(500) NOT NULL,
    source_file_path TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL CHECK (file_type IN ('XML', 'JSON', 'CSV', 'PDF', 'DOCX', 'OTHER')),
    file_size_bytes BIGINT,
    file_hash VARCHAR(64),
    profile_id UUID,

    -- Ingestion tracking
    ingestion_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    uploaded_by VARCHAR(255),

    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'archived')),
    error_message TEXT,
    processing_duration_ms INTEGER,

    -- Metadata
    original_format_version VARCHAR(50),
    source_system VARCHAR(255),
    batch_id UUID,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE documents IS 'Metadata for all ingested documents regardless of source format';

-- document_content table
CREATE TABLE IF NOT EXISTS document_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL UNIQUE REFERENCES documents(id) ON DELETE CASCADE,

    canonical_data JSONB NOT NULL,
    searchable_text TEXT,
    extracted_entities JSONB DEFAULT '{}'::jsonb,
    tags TEXT[],
    schema_version INTEGER DEFAULT 1,
    confidence_score DECIMAL(5, 4),
    validation_errors JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE document_content IS 'Normalized canonical data extracted from source documents';

-- profiles table
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_name VARCHAR(255) NOT NULL UNIQUE,
    file_type VARCHAR(50) NOT NULL CHECK (file_type IN ('XML', 'JSON', 'CSV', 'PDF', 'DOCX', 'OTHER')),

    description TEXT,
    source_format_description TEXT,
    canonical_schema_version INTEGER DEFAULT 1,

    mapping_definition JSONB NOT NULL,
    validation_rules JSONB DEFAULT '{}'::jsonb,
    transformations JSONB DEFAULT '[]'::jsonb,
    entity_patterns JSONB DEFAULT '{}'::jsonb,

    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,

    version VARCHAR(50) DEFAULT '1.0.0',
    parent_profile_id UUID REFERENCES profiles(id),

    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE profiles IS 'Profile definitions for mapping source formats to canonical schema';

-- Add foreign key from documents to profiles
ALTER TABLE documents ADD CONSTRAINT fk_documents_profile
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE SET NULL;

-- ingestion_logs table
CREATE TABLE IF NOT EXISTS ingestion_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    batch_id UUID,

    log_level VARCHAR(20) NOT NULL CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT NOT NULL,
    details JSONB,

    operation VARCHAR(100),
    duration_ms INTEGER,

    file_location TEXT,
    line_number INTEGER,

    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE ingestion_logs IS 'Comprehensive audit trail for all ingestion and processing operations';

-- batch_metadata table
CREATE TABLE IF NOT EXISTS batch_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_name VARCHAR(255),
    profile_id UUID REFERENCES profiles(id),

    total_files INTEGER DEFAULT 0,
    successful INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    skipped INTEGER DEFAULT 0,

    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    total_duration_ms INTEGER,

    uploaded_by VARCHAR(255),

    status VARCHAR(50) DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'failed', 'cancelled'))
);

-- user_queries table
CREATE TABLE IF NOT EXISTS user_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_text TEXT,
    filters JSONB,
    results_count INTEGER,
    executed_by VARCHAR(255),
    execution_time_ms INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- schema_versions table
CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================
-- SECTION 3: KEYWORD TABLES
-- =====================================================================

CREATE TABLE IF NOT EXISTS keywords (
    keyword_id SERIAL PRIMARY KEY,
    keyword_text VARCHAR(255) NOT NULL UNIQUE,
    normalized_form VARCHAR(255),
    category VARCHAR(100),
    definition TEXT,
    description TEXT,
    source_refs TEXT,

    -- Standardization
    is_standard BOOLEAN DEFAULT FALSE,
    vocabulary_source VARCHAR(100),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE keywords IS 'Master keyword dictionary with standardized medical terminology';

CREATE TABLE IF NOT EXISTS keyword_statistics (
    stats_id SERIAL PRIMARY KEY,
    keyword_id INTEGER REFERENCES keywords(keyword_id) ON DELETE CASCADE,
    total_frequency INTEGER DEFAULT 0,
    document_count INTEGER DEFAULT 0,
    idf_score DECIMAL(10, 6),
    avg_tf_idf DECIMAL(10, 6),
    last_calculated TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS keyword_synonyms (
    synonym_id SERIAL PRIMARY KEY,
    canonical_keyword_id INTEGER REFERENCES keywords(keyword_id) ON DELETE CASCADE,
    synonym_text VARCHAR(255) NOT NULL,
    synonym_type VARCHAR(50),
    confidence DECIMAL(5, 4),
    UNIQUE(canonical_keyword_id, synonym_text)
);

CREATE TABLE IF NOT EXISTS keyword_sources (
    source_id SERIAL PRIMARY KEY,
    keyword_id INTEGER REFERENCES keywords(keyword_id) ON DELETE CASCADE,
    source_type VARCHAR(50),
    source_file VARCHAR(500),
    sector VARCHAR(100),
    frequency INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS stop_words (
    term VARCHAR(100) PRIMARY KEY,
    category VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE
);

-- =====================================================================
-- SECTION 4: PARSE CASE DETECTION TABLES
-- =====================================================================

CREATE TABLE IF NOT EXISTS parse_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    version VARCHAR(20) NOT NULL DEFAULT '1.0',

    detection_criteria JSONB NOT NULL,
    field_mappings JSONB DEFAULT '[]'::jsonb,

    format_type VARCHAR(50),
    detection_priority INTEGER DEFAULT 50,
    requires_header BOOLEAN DEFAULT FALSE,
    requires_modality BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE parse_cases IS 'Parse case definitions with detection criteria';

CREATE TABLE IF NOT EXISTS detection_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    queue_item_id VARCHAR(50),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,

    parse_case VARCHAR(255) NOT NULL,
    confidence DECIMAL(5, 4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),

    expected_attributes JSONB NOT NULL DEFAULT '[]'::jsonb,
    detected_attributes JSONB NOT NULL DEFAULT '[]'::jsonb,
    missing_attributes JSONB NOT NULL DEFAULT '[]'::jsonb,

    match_percentage DECIMAL(5, 2) NOT NULL,
    total_expected INTEGER NOT NULL DEFAULT 0,
    total_detected INTEGER NOT NULL DEFAULT 0,

    field_analysis JSONB DEFAULT '[]'::jsonb,

    detector_type VARCHAR(100) DEFAULT 'XMLStructureDetector',
    detector_version VARCHAR(50) DEFAULT '1.0.0',
    detection_method VARCHAR(255),
    confidence_breakdown JSONB DEFAULT '{}'::jsonb,

    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE detection_details IS 'Detailed parse case detection analysis';

CREATE TABLE IF NOT EXISTS pending_case_assignment (
    pending_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID REFERENCES documents(id) ON DELETE CASCADE,

    suggested_case_id UUID REFERENCES parse_cases(id),
    detection_method VARCHAR(100),
    confidence_score DECIMAL(5, 4),

    keyword_signature TEXT,
    keyword_ids INTEGER[],
    pattern_match_details JSONB,

    review_status VARCHAR(50) DEFAULT 'pending' CHECK (review_status IN ('pending', 'assigned', 'rejected')),
    assigned_case_id UUID REFERENCES parse_cases(id),
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE pending_case_assignment IS 'Approval queue for low-confidence parse case detections';

CREATE TABLE IF NOT EXISTS case_patterns (
    case_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_signature VARCHAR(500) UNIQUE,
    case_label VARCHAR(255),
    detection_method VARCHAR(100),

    keywords JSONB,
    source_segments JSONB,

    confidence_score DECIMAL(5, 4),
    cross_type_validated BOOLEAN DEFAULT FALSE,

    keyword_count INTEGER DEFAULT 0,
    segment_count INTEGER DEFAULT 0,
    file_count INTEGER DEFAULT 0,

    version_history JSONB,

    detected_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE case_patterns IS 'Detected keyword patterns across documents';

-- =====================================================================
-- SECTION 5: DOCUMENT ENHANCEMENTS (from migration 016)
-- =====================================================================

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS parse_case VARCHAR(255),
    ADD COLUMN IF NOT EXISTS detection_confidence DECIMAL(5, 4) CHECK (detection_confidence >= 0 AND detection_confidence <= 1),
    ADD COLUMN IF NOT EXISTS keywords_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS parsed_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS parsed_content_preview TEXT,
    ADD COLUMN IF NOT EXISTS document_title VARCHAR(500),
    ADD COLUMN IF NOT EXISTS document_date DATE,
    ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64);

COMMENT ON COLUMN documents.parse_case IS 'Detected or assigned parse case';
COMMENT ON COLUMN documents.detection_confidence IS 'Confidence score from structure detector (0-1)';
COMMENT ON COLUMN documents.keywords_count IS 'Number of keywords extracted from document';

-- =====================================================================
-- SECTION 6: INDEXES
-- =====================================================================

-- Documents indexes
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_profile_id ON documents(profile_id);
CREATE INDEX IF NOT EXISTS idx_documents_ingestion_timestamp ON documents(ingestion_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_documents_batch_id ON documents(batch_id);
CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_documents_parse_case ON documents(parse_case);
CREATE INDEX IF NOT EXISTS idx_documents_detection_confidence ON documents(detection_confidence);
CREATE INDEX IF NOT EXISTS idx_documents_keywords_count ON documents(keywords_count);
CREATE INDEX IF NOT EXISTS idx_documents_parsed_at ON documents(parsed_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_unique_path ON documents(source_file_path) WHERE status != 'archived';

-- Document content indexes
CREATE INDEX IF NOT EXISTS idx_content_document_id ON document_content(document_id);
CREATE INDEX IF NOT EXISTS idx_content_canonical_data_gin ON document_content USING GIN (canonical_data);
CREATE INDEX IF NOT EXISTS idx_content_entities_gin ON document_content USING GIN (extracted_entities);
CREATE INDEX IF NOT EXISTS idx_content_tags_gin ON document_content USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_content_searchable_text_gin ON document_content USING GIN (to_tsvector('english', searchable_text));

-- Profiles indexes
CREATE INDEX IF NOT EXISTS idx_profiles_file_type ON profiles(file_type);
CREATE INDEX IF NOT EXISTS idx_profiles_is_active ON profiles(is_active);
CREATE INDEX IF NOT EXISTS idx_profiles_is_default ON profiles(is_default, file_type);
CREATE INDEX IF NOT EXISTS idx_profiles_mapping_gin ON profiles USING GIN (mapping_definition);
CREATE UNIQUE INDEX IF NOT EXISTS idx_profiles_unique_default ON profiles(file_type, is_default) WHERE is_default = TRUE;

-- Logs indexes
CREATE INDEX IF NOT EXISTS idx_logs_document_id ON ingestion_logs(document_id);
CREATE INDEX IF NOT EXISTS idx_logs_batch_id ON ingestion_logs(batch_id);
CREATE INDEX IF NOT EXISTS idx_logs_level ON ingestion_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON ingestion_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_operation ON ingestion_logs(operation);

-- Batch metadata indexes
CREATE INDEX IF NOT EXISTS idx_batch_started_at ON batch_metadata(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_batch_status ON batch_metadata(status);

-- User queries indexes
CREATE INDEX IF NOT EXISTS idx_user_queries_timestamp ON user_queries(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_user_queries_executed_by ON user_queries(executed_by);

-- Keyword indexes
CREATE INDEX IF NOT EXISTS idx_keywords_normalized ON keywords(normalized_form);
CREATE INDEX IF NOT EXISTS idx_keywords_category ON keywords(category);
CREATE INDEX IF NOT EXISTS idx_keywords_vocab_source ON keywords(vocabulary_source);

-- Parse cases indexes
CREATE INDEX IF NOT EXISTS idx_parse_cases_name ON parse_cases(name);
CREATE INDEX IF NOT EXISTS idx_parse_cases_active ON parse_cases(is_active);

-- Detection details indexes
CREATE INDEX IF NOT EXISTS idx_detection_document ON detection_details(document_id);
CREATE INDEX IF NOT EXISTS idx_detection_parse_case ON detection_details(parse_case);
CREATE INDEX IF NOT EXISTS idx_detection_confidence ON detection_details(confidence);
CREATE INDEX IF NOT EXISTS idx_detection_expected_attrs_gin ON detection_details USING GIN (expected_attributes);
CREATE INDEX IF NOT EXISTS idx_detection_detected_attrs_gin ON detection_details USING GIN (detected_attributes);

-- =====================================================================
-- SECTION 7: FUNCTIONS AND TRIGGERS
-- =====================================================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables
CREATE TRIGGER documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER document_content_updated_at BEFORE UPDATE ON document_content
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER keywords_updated_at BEFORE UPDATE ON keywords
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER detection_details_updated_at BEFORE UPDATE ON detection_details
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Update searchable_text from canonical_data
CREATE OR REPLACE FUNCTION update_searchable_text()
RETURNS TRIGGER AS $$
BEGIN
    NEW.searchable_text = (
        SELECT STRING_AGG(value::text, ' ')
        FROM jsonb_each_text(NEW.canonical_data)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER document_content_searchable_text
    BEFORE INSERT OR UPDATE OF canonical_data ON document_content
    FOR EACH ROW EXECUTE FUNCTION update_searchable_text();

-- Log status changes
CREATE OR REPLACE FUNCTION log_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO ingestion_logs (document_id, log_level, message, details, operation)
        VALUES (
            NEW.id,
            CASE
                WHEN NEW.status = 'failed' THEN 'ERROR'
                WHEN NEW.status = 'completed' THEN 'INFO'
                ELSE 'WARNING'
            END,
            'Status changed from ' || COALESCE(OLD.status, 'NULL') || ' to ' || NEW.status,
            jsonb_build_object(
                'old_status', OLD.status,
                'new_status', NEW.status,
                'error_message', NEW.error_message
            ),
            'status_change'
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER documents_status_change AFTER UPDATE OF status ON documents
    FOR EACH ROW EXECUTE FUNCTION log_status_change();

-- Update parsed_at when document completes
CREATE OR REPLACE FUNCTION update_parsed_at()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status AND NEW.status = 'completed' THEN
        NEW.parsed_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER documents_update_parsed_at BEFORE UPDATE OF status ON documents
    FOR EACH ROW EXECUTE FUNCTION update_parsed_at();

-- =====================================================================
-- SECTION 8: VIEWS
-- =====================================================================

CREATE OR REPLACE VIEW v_document_summary AS
SELECT
    d.id,
    d.source_file_name,
    d.file_type,
    d.status,
    d.ingestion_timestamp,
    p.profile_name,
    c.tags,
    c.schema_version,
    c.confidence_score,
    c.canonical_data->>'document_type' AS document_type,
    c.canonical_data->'document_metadata'->>'title' AS title,
    c.canonical_data->'document_metadata'->>'date' AS document_date,
    LEFT(c.searchable_text, 200) AS text_preview,
    d.file_size_bytes,
    d.uploaded_by
FROM documents d
LEFT JOIN document_content c ON d.id = c.document_id
LEFT JOIN profiles p ON d.profile_id = p.id
WHERE d.status != 'archived';

CREATE OR REPLACE VIEW v_document_list AS
SELECT
    d.id,
    d.source_file_name AS filename,
    d.document_title,
    d.parse_case,
    d.detection_confidence AS confidence,
    d.file_type,
    d.file_size_bytes,
    d.keywords_count,
    d.status,
    d.ingestion_timestamp AS uploaded_at,
    d.parsed_at,
    d.document_date,
    d.uploaded_by,
    d.error_message,
    COALESCE(d.parsed_content_preview, LEFT(c.searchable_text, 500)) AS content_preview,
    c.tags,
    p.profile_name,
    dd.match_percentage,
    dd.total_expected,
    dd.total_detected,
    CASE
        WHEN d.status = 'completed' THEN 'success'
        WHEN d.status = 'failed' THEN 'error'
        WHEN d.status = 'processing' THEN 'processing'
        ELSE 'pending'
    END AS status_category
FROM documents d
LEFT JOIN document_content c ON d.id = c.document_id
LEFT JOIN profiles p ON d.profile_id = p.id
LEFT JOIN detection_details dd ON d.id = dd.document_id
WHERE d.status != 'archived'
ORDER BY d.ingestion_timestamp DESC;

CREATE OR REPLACE VIEW v_document_detail AS
SELECT
    d.id,
    d.source_file_name,
    d.source_file_path,
    d.document_title,
    d.file_type,
    d.file_size_bytes,
    d.file_hash,
    d.parse_case,
    d.detection_confidence,
    d.keywords_count,
    d.status,
    d.error_message,
    d.processing_duration_ms,
    d.ingestion_timestamp,
    d.parsed_at,
    d.document_date,
    d.uploaded_by,
    d.created_at,
    d.updated_at,
    p.profile_name,
    p.description AS profile_description,
    c.canonical_data,
    c.searchable_text,
    c.extracted_entities,
    c.tags,
    c.confidence_score AS content_confidence,
    c.schema_version,
    dd.expected_attributes,
    dd.detected_attributes,
    dd.missing_attributes,
    dd.match_percentage,
    dd.field_analysis,
    dd.detector_type,
    dd.detected_at,
    (SELECT COUNT(*) FROM ingestion_logs WHERE document_id = d.id) AS log_count,
    (SELECT COUNT(*) FROM ingestion_logs WHERE document_id = d.id AND log_level = 'ERROR') AS error_count
FROM documents d
LEFT JOIN document_content c ON d.id = c.document_id
LEFT JOIN profiles p ON d.profile_id = p.id
LEFT JOIN detection_details dd ON d.id = dd.document_id;

CREATE OR REPLACE VIEW v_ingestion_health AS
SELECT
    DATE(ingestion_timestamp) AS date,
    file_type,
    COUNT(*) AS total_documents,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS successful,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
    AVG(processing_duration_ms) AS avg_duration_ms,
    AVG(file_size_bytes) AS avg_file_size_bytes
FROM documents
WHERE ingestion_timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(ingestion_timestamp), file_type
ORDER BY date DESC, file_type;

CREATE OR REPLACE VIEW v_detection_summary AS
SELECT
    dd.id,
    dd.queue_item_id,
    dd.document_id,
    dd.parse_case,
    dd.confidence,
    dd.match_percentage,
    dd.total_expected,
    dd.total_detected,
    dd.total_expected - dd.total_detected AS total_missing,
    dd.detector_type,
    dd.detected_at,
    (SELECT JSONB_AGG(attr->>'name') FROM JSONB_ARRAY_ELEMENTS(dd.expected_attributes) attr) AS expected_attr_names,
    (SELECT JSONB_AGG(attr->>'name') FROM JSONB_ARRAY_ELEMENTS(dd.detected_attributes) attr) AS detected_attr_names,
    (SELECT JSONB_AGG(attr->>'name') FROM JSONB_ARRAY_ELEMENTS(dd.missing_attributes) attr) AS missing_attr_names,
    d.source_file_name,
    d.file_type,
    d.status AS document_status
FROM detection_details dd
LEFT JOIN documents d ON dd.document_id = d.id;

-- =====================================================================
-- SECTION 9: SEED DATA
-- =====================================================================

-- Default profile
INSERT INTO profiles (profile_name, file_type, description, mapping_definition, is_active, is_default)
VALUES (
    'generic_xml_passthrough',
    'XML',
    'Generic XML profile that extracts all elements without specific mapping',
    '{"mode": "passthrough", "extract_all_elements": true, "preserve_structure": true}'::jsonb,
    true,
    false
) ON CONFLICT (profile_name) DO NOTHING;

-- Common stop words
INSERT INTO stop_words (term, category) VALUES
('the', 'common_english'), ('a', 'common_english'), ('an', 'common_english'),
('and', 'common_english'), ('or', 'common_english'), ('but', 'common_english'),
('in', 'common_english'), ('on', 'common_english'), ('at', 'common_english'),
('to', 'common_english'), ('for', 'common_english'), ('of', 'common_english'),
('with', 'common_english'), ('by', 'common_english'), ('from', 'common_english'),
('is', 'common_english'), ('are', 'common_english'), ('was', 'common_english'),
('were', 'common_english'), ('be', 'common_english'), ('been', 'common_english'),
('this', 'common_english'), ('that', 'common_english'), ('these', 'common_english'),
('those', 'common_english'), ('it', 'common_english'), ('its', 'common_english')
ON CONFLICT (term) DO NOTHING;

-- Sample keywords
INSERT INTO keywords (keyword_text, normalized_form, category, is_standard, vocabulary_source) VALUES
('nodule', 'nodule', 'medical', true, 'RadLex'),
('lesion', 'lesion', 'medical', true, 'RadLex'),
('opacity', 'opacity', 'medical', true, 'RadLex'),
('calcification', 'calcification', 'medical', true, 'RadLex'),
('spiculation', 'spiculation', 'medical', true, 'RadLex')
ON CONFLICT (keyword_text) DO NOTHING;

-- =====================================================================
-- SECTION 10: SCHEMA VERSION
-- =====================================================================

INSERT INTO schema_versions (version, description) VALUES
(1, 'Initial schema for schema-agnostic data ingestion system'),
(2, 'Add keyword enhancements and standardization'),
(15, 'Add detection_details table for parse case identification'),
(16, 'Enhance documents table with parse case tracking and metadata')
ON CONFLICT (version) DO NOTHING;

-- =====================================================================
-- VERIFICATION QUERIES
-- =====================================================================
-- Run these after the migration to verify everything was created:

-- Check tables created
SELECT
    'Tables Created' AS check_type,
    COUNT(*) AS count,
    '15+ expected' AS expected
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE';

-- Check views created
SELECT
    'Views Created' AS check_type,
    COUNT(*) AS count,
    '5+ expected' AS expected
FROM information_schema.views
WHERE table_schema = 'public';

-- Check schema version
SELECT
    'Schema Version' AS check_type,
    MAX(version)::TEXT AS count,
    '16 expected' AS expected
FROM schema_versions;

-- List all tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Check seed data
SELECT
    'Stop Words' AS data_type,
    COUNT(*)::TEXT AS count,
    '25+ expected' AS expected
FROM stop_words

UNION ALL

SELECT
    'Profiles' AS data_type,
    COUNT(*)::TEXT AS count,
    '1+ expected' AS expected
FROM profiles

UNION ALL

SELECT
    'Keywords' AS data_type,
    COUNT(*)::TEXT AS count,
    '5+ expected' AS expected
FROM keywords;

-- =====================================================================
-- END OF CONSOLIDATED MIGRATION
-- =====================================================================
--
-- If all verification queries pass, schema is ready!
-- Next steps:
-- 1. Test backend connection: python3 scripts/verify_supabase_schema.py
-- 2. Continue to Phase 2: Parse service implementation
-- =====================================================================
