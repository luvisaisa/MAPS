-- =====================================================================
-- MAPS Supabase Migration 006: Case Detection System
-- =====================================================================
-- Purpose: Parse case definitions, detection details, and approval queue
-- Date: November 25, 2025
-- =====================================================================

-- ---------------------------------------------------------------------
-- Table: parse_cases
-- ---------------------------------------------------------------------
CREATE TABLE parse_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    version VARCHAR(50) DEFAULT '1.0.0',
    format_type file_type_enum,

    -- Detection configuration
    detection_criteria JSONB NOT NULL DEFAULT '{}'::jsonb,
    field_mappings JSONB NOT NULL DEFAULT '{}'::jsonb,
    detection_priority INTEGER DEFAULT 50 CHECK (detection_priority >= 0 AND detection_priority <= 100),

    -- Requirements flags
    requires_header BOOLEAN DEFAULT FALSE,
    requires_modality BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_parse_cases_is_active ON parse_cases(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_parse_cases_format_type ON parse_cases(format_type) WHERE format_type IS NOT NULL;
CREATE INDEX idx_parse_cases_detection_priority ON parse_cases(detection_priority DESC);

-- GIN indexes for JSONB
CREATE INDEX idx_parse_cases_detection_criteria ON parse_cases USING gin(detection_criteria);
CREATE INDEX idx_parse_cases_field_mappings ON parse_cases USING gin(field_mappings);

-- Trigger
CREATE TRIGGER parse_cases_update_timestamp
    BEFORE UPDATE ON parse_cases
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE parse_cases IS 'Parse case definitions with detection rules and field mappings';
COMMENT ON COLUMN parse_cases.detection_criteria IS 'JSONB rules for identifying this case (required fields, patterns, etc.)';
COMMENT ON COLUMN parse_cases.field_mappings IS 'JSONB mappings from case-specific fields to canonical schema';
COMMENT ON COLUMN parse_cases.detection_priority IS 'Evaluation order (0-100, higher = earlier evaluation)';

-- ---------------------------------------------------------------------
-- Table: detection_details
-- ---------------------------------------------------------------------
CREATE TABLE detection_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    queue_item_id VARCHAR(50),  -- Reference to pending_case_assignment if applicable
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,

    -- Detection results
    parse_case VARCHAR(255) NOT NULL,
    confidence DECIMAL(5, 4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),

    -- Attribute analysis (JSONB arrays)
    expected_attributes JSONB NOT NULL DEFAULT '[]'::jsonb,
    detected_attributes JSONB NOT NULL DEFAULT '[]'::jsonb,
    missing_attributes JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Metrics
    match_percentage DECIMAL(5, 2) NOT NULL,  -- 0.00 to 100.00
    total_expected INTEGER NOT NULL DEFAULT 0,
    total_detected INTEGER NOT NULL DEFAULT 0,

    -- Field-by-field analysis
    field_analysis JSONB DEFAULT '[]'::jsonb,

    -- Detection metadata
    detector_type VARCHAR(100) DEFAULT 'XMLStructureDetector',
    detector_version VARCHAR(50) DEFAULT '1.0.0',
    detection_method detection_method_enum,
    confidence_breakdown JSONB,  -- Detailed scoring breakdown

    -- Timestamps
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_detection_details_document_id ON detection_details(document_id);
CREATE INDEX idx_detection_details_parse_case ON detection_details(parse_case);
CREATE INDEX idx_detection_details_confidence ON detection_details(confidence DESC);
CREATE INDEX idx_detection_details_match_percentage ON detection_details(match_percentage DESC);
CREATE INDEX idx_detection_details_queue_item_id ON detection_details(queue_item_id) WHERE queue_item_id IS NOT NULL;

-- GIN indexes for JSONB arrays
CREATE INDEX idx_detection_details_expected_attributes ON detection_details USING gin(expected_attributes);
CREATE INDEX idx_detection_details_detected_attributes ON detection_details USING gin(detected_attributes);
CREATE INDEX idx_detection_details_missing_attributes ON detection_details USING gin(missing_attributes);
CREATE INDEX idx_detection_details_field_analysis ON detection_details USING gin(field_analysis);
CREATE INDEX idx_detection_details_confidence_breakdown ON detection_details USING gin(confidence_breakdown);

-- Trigger
CREATE TRIGGER detection_details_update_timestamp
    BEFORE UPDATE ON detection_details
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE detection_details IS 'Detailed parse case detection analysis with attribute matching';
COMMENT ON COLUMN detection_details.confidence IS 'Overall detection confidence (0.0-1.0)';
COMMENT ON COLUMN detection_details.match_percentage IS 'Percentage of expected attributes found (0-100)';
COMMENT ON COLUMN detection_details.field_analysis IS 'Array of per-field analysis results with detection status';

-- ---------------------------------------------------------------------
-- Table: pending_case_assignment (Approval Queue)
-- ---------------------------------------------------------------------
CREATE TABLE pending_case_assignment (
    pending_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    -- Segment reference (if content-based detection)
    segment_id UUID,
    segment_type segment_type_enum,

    -- Detection metadata
    suggested_case_id UUID REFERENCES parse_cases(id) ON DELETE SET NULL,
    detection_method detection_method_enum NOT NULL,
    confidence_score DECIMAL(5, 4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),

    -- Evidence for suggestion
    keyword_signature TEXT,
    keyword_ids INTEGER[],  -- Array of keyword_id references
    pattern_match_details JSONB,

    -- Review tracking
    review_status review_status_enum DEFAULT 'pending',
    assigned_case_id UUID REFERENCES parse_cases(id) ON DELETE SET NULL,
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_pending_case_assignment_file_id ON pending_case_assignment(file_id);
CREATE INDEX idx_pending_case_assignment_review_status ON pending_case_assignment(review_status);
CREATE INDEX idx_pending_case_assignment_confidence_score ON pending_case_assignment(confidence_score DESC);
CREATE INDEX idx_pending_case_assignment_suggested_case ON pending_case_assignment(suggested_case_id) WHERE suggested_case_id IS NOT NULL;
CREATE INDEX idx_pending_case_assignment_segment ON pending_case_assignment(segment_id, segment_type) WHERE segment_id IS NOT NULL;

-- Composite index for pending queue queries
CREATE INDEX idx_pending_case_assignment_status_confidence ON pending_case_assignment(review_status, confidence_score DESC);

-- GIN indexes
CREATE INDEX idx_pending_case_assignment_keyword_ids ON pending_case_assignment USING gin(keyword_ids);
CREATE INDEX idx_pending_case_assignment_pattern_match ON pending_case_assignment USING gin(pattern_match_details);

-- Trigger
CREATE TRIGGER pending_case_assignment_update_timestamp
    BEFORE UPDATE ON pending_case_assignment
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE pending_case_assignment IS 'Approval queue for low-confidence case detections requiring manual review';
COMMENT ON COLUMN pending_case_assignment.confidence_score IS 'Detection confidence (typically <0.8 for items in queue)';
COMMENT ON COLUMN pending_case_assignment.keyword_signature IS 'Comma-separated keyword IDs that matched';
COMMENT ON COLUMN pending_case_assignment.pattern_match_details IS 'JSONB details of pattern matching results';

-- ---------------------------------------------------------------------
-- Table: case_patterns
-- ---------------------------------------------------------------------
CREATE TABLE case_patterns (
    case_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_signature VARCHAR(64) UNIQUE NOT NULL,  -- Hash of keyword+segment combination
    case_label VARCHAR(255),

    -- Detection metadata
    detection_method detection_method_enum,
    keywords JSONB,  -- Keyword IDs and frequencies
    source_segments JSONB,  -- Segment IDs grouped by type

    -- Confidence metrics
    confidence_score DECIMAL(5, 4) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    cross_type_validated BOOLEAN DEFAULT FALSE,  -- Found in both quan/qual

    -- Statistics
    keyword_count INTEGER DEFAULT 0,
    segment_count INTEGER DEFAULT 0,
    file_count INTEGER DEFAULT 0,

    -- Versioning
    version_history JSONB DEFAULT '[]'::jsonb,

    -- Timestamps
    detected_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_case_patterns_case_label ON case_patterns(case_label) WHERE case_label IS NOT NULL;
CREATE INDEX idx_case_patterns_confidence_score ON case_patterns(confidence_score DESC);
CREATE INDEX idx_case_patterns_cross_type_validated ON case_patterns(cross_type_validated) WHERE cross_type_validated = TRUE;
CREATE INDEX idx_case_patterns_keyword_count ON case_patterns(keyword_count DESC);
CREATE INDEX idx_case_patterns_file_count ON case_patterns(file_count DESC);

-- GIN indexes
CREATE INDEX idx_case_patterns_keywords ON case_patterns USING gin(keywords);
CREATE INDEX idx_case_patterns_source_segments ON case_patterns USING gin(source_segments);
CREATE INDEX idx_case_patterns_version_history ON case_patterns USING gin(version_history);

-- Trigger
CREATE TRIGGER case_patterns_update_timestamp
    BEFORE UPDATE ON case_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE case_patterns IS 'Detected keyword-based case patterns with cross-type validation';
COMMENT ON COLUMN case_patterns.pattern_signature IS 'SHA-256 hash of keyword+segment combination for uniqueness';
COMMENT ON COLUMN case_patterns.cross_type_validated IS 'TRUE if keywords found in both quantitative and qualitative segments (high confidence signal)';

-- =====================================================================
-- Update schema version
-- =====================================================================
INSERT INTO schema_versions (version, description)
VALUES (6, 'Case detection system with parse cases, detection details, approval queue, and pattern recognition');

-- =====================================================================
-- Verification Query
-- =====================================================================
-- Run this to verify tables are created:
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
-- AND table_name IN ('parse_cases', 'detection_details', 'pending_case_assignment', 'case_patterns')
-- ORDER BY table_name;
--
-- Check indexes:
-- SELECT tablename, indexname FROM pg_indexes
-- WHERE tablename IN ('parse_cases', 'detection_details', 'pending_case_assignment', 'case_patterns');

-- =====================================================================
-- END OF MIGRATION 006
-- =====================================================================
