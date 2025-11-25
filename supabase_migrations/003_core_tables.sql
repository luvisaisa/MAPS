-- =====================================================================
-- MAPS Supabase Migration 003: Core Tables
-- =====================================================================
-- Purpose: Create profiles, documents, and document_content tables
-- Date: November 25, 2025
-- =====================================================================

-- ---------------------------------------------------------------------
-- Table: schema_versions
-- ---------------------------------------------------------------------
CREATE TABLE schema_versions (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE schema_versions IS 'Tracks applied database migrations and schema versions';

-- Insert initial version
INSERT INTO schema_versions (version, description) VALUES (1, 'Initial schema setup with extensions and types');
INSERT INTO schema_versions (version, description) VALUES (2, 'Utility functions and trigger procedures');
INSERT INTO schema_versions (version, description) VALUES (3, 'Core tables: profiles, documents, document_content');

-- ---------------------------------------------------------------------
-- Table: profiles
-- ---------------------------------------------------------------------
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_name VARCHAR(255) NOT NULL UNIQUE,
    file_type file_type_enum NOT NULL,
    description TEXT,

    -- Profile configuration (JSONB for flexibility)
    mapping_definition JSONB NOT NULL DEFAULT '{}'::jsonb,
    validation_rules JSONB DEFAULT '{}'::jsonb,
    transformations JSONB DEFAULT '{}'::jsonb,
    entity_patterns JSONB DEFAULT '{}'::jsonb,

    -- Profile inheritance
    parent_profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    version VARCHAR(50) DEFAULT '1.0.0',

    -- Status flags
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ensure only one default profile per file type
CREATE UNIQUE INDEX idx_profiles_default_per_type
    ON profiles(file_type)
    WHERE is_default = TRUE;

-- Indexes
CREATE INDEX idx_profiles_file_type ON profiles(file_type);
CREATE INDEX idx_profiles_is_active ON profiles(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_profiles_parent ON profiles(parent_profile_id) WHERE parent_profile_id IS NOT NULL;

-- GIN indexes for JSONB fields
CREATE INDEX idx_profiles_mapping_definition ON profiles USING gin(mapping_definition);
CREATE INDEX idx_profiles_validation_rules ON profiles USING gin(validation_rules);

-- Trigger for auto-updating updated_at
CREATE TRIGGER profiles_update_timestamp
    BEFORE UPDATE ON profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE profiles IS 'Parsing profiles with mapping definitions for schema-agnostic ingestion';
COMMENT ON COLUMN profiles.mapping_definition IS 'JSONB mapping from source paths to canonical schema fields';
COMMENT ON COLUMN profiles.validation_rules IS 'JSONB validation constraints and business rules';
COMMENT ON COLUMN profiles.transformations IS 'JSONB data transformation rules (date formats, unit conversions, etc.)';
COMMENT ON COLUMN profiles.entity_patterns IS 'JSONB regex patterns for entity extraction';
COMMENT ON COLUMN profiles.parent_profile_id IS 'Enables profile inheritance for common configurations';

-- ---------------------------------------------------------------------
-- Table: documents
-- ---------------------------------------------------------------------
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- File metadata
    source_file_name VARCHAR(500) NOT NULL,
    source_file_path TEXT,
    file_type file_type_enum NOT NULL,
    file_size_bytes BIGINT,
    file_hash VARCHAR(64),  -- SHA-256 hash for deduplication

    -- Profile and batch tracking
    profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    batch_id UUID,

    -- Processing status
    status document_status_enum DEFAULT 'pending',
    error_message TEXT,
    processing_duration_ms INTEGER,

    -- Timestamps
    ingestion_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    uploaded_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Enhanced fields (from Migration 016)
    parse_case VARCHAR(255),
    detection_confidence DECIMAL(5, 4) CHECK (detection_confidence >= 0 AND detection_confidence <= 1),
    keywords_count INTEGER DEFAULT 0,
    parsed_at TIMESTAMP WITH TIME ZONE,
    parsed_content_preview TEXT,  -- First 500 chars
    document_title VARCHAR(500),
    document_date DATE,
    content_hash VARCHAR(64)  -- Hash of parsed content for change detection
);

-- Indexes for common queries
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_file_type ON documents(file_type);
CREATE INDEX idx_documents_profile_id ON documents(profile_id) WHERE profile_id IS NOT NULL;
CREATE INDEX idx_documents_batch_id ON documents(batch_id) WHERE batch_id IS NOT NULL;
CREATE INDEX idx_documents_file_hash ON documents(file_hash) WHERE file_hash IS NOT NULL;
CREATE INDEX idx_documents_parse_case ON documents(parse_case) WHERE parse_case IS NOT NULL;
CREATE INDEX idx_documents_detection_confidence ON documents(detection_confidence) WHERE detection_confidence IS NOT NULL;
CREATE INDEX idx_documents_keywords_count ON documents(keywords_count);
CREATE INDEX idx_documents_parsed_at ON documents(parsed_at DESC);
CREATE INDEX idx_documents_ingestion_timestamp ON documents(ingestion_timestamp DESC);
CREATE INDEX idx_documents_document_date ON documents(document_date DESC) WHERE document_date IS NOT NULL;
CREATE INDEX idx_documents_content_hash ON documents(content_hash) WHERE content_hash IS NOT NULL;

-- Composite index for filtering
CREATE INDEX idx_documents_status_parse_case ON documents(status, parse_case);

-- Triggers
CREATE TRIGGER documents_update_timestamp
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER documents_update_parsed_at
    BEFORE UPDATE OF status ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_parsed_at();

COMMENT ON TABLE documents IS 'Main document metadata and processing status tracking';
COMMENT ON COLUMN documents.file_hash IS 'SHA-256 hash of source file for deduplication';
COMMENT ON COLUMN documents.parse_case IS 'Detected or assigned parse case (e.g., LIDC_Single_Session, Complete_Attributes)';
COMMENT ON COLUMN documents.detection_confidence IS 'Confidence score from structure detector (0-1)';
COMMENT ON COLUMN documents.keywords_count IS 'Number of keywords extracted from document';
COMMENT ON COLUMN documents.parsed_at IS 'Timestamp when document was successfully parsed';
COMMENT ON COLUMN documents.content_hash IS 'SHA-256 hash of parsed content for detecting changes';

-- ---------------------------------------------------------------------
-- Table: document_content
-- ---------------------------------------------------------------------
CREATE TABLE document_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL UNIQUE REFERENCES documents(id) ON DELETE CASCADE,

    -- Canonical schema-agnostic storage
    canonical_data JSONB NOT NULL,
    searchable_text TEXT,  -- Auto-populated from canonical_data

    -- Extracted entities and metadata
    extracted_entities JSONB DEFAULT '{}'::jsonb,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- Quality metrics
    confidence_score DECIMAL(5, 4) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    validation_errors JSONB DEFAULT '[]'::jsonb,

    -- Schema tracking
    schema_version VARCHAR(50) DEFAULT '1.0.0',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_document_content_document_id ON document_content(document_id);
CREATE INDEX idx_document_content_tags ON document_content USING gin(tags);
CREATE INDEX idx_document_content_confidence_score ON document_content(confidence_score) WHERE confidence_score IS NOT NULL;

-- GIN indexes for JSONB and full-text search
CREATE INDEX idx_document_content_canonical_data ON document_content USING gin(canonical_data);
CREATE INDEX idx_document_content_canonical_data_path ON document_content USING gin(canonical_data jsonb_path_ops);
CREATE INDEX idx_document_content_extracted_entities ON document_content USING gin(extracted_entities);
CREATE INDEX idx_document_content_validation_errors ON document_content USING gin(validation_errors);

-- Full-text search index
CREATE INDEX idx_document_content_searchable_text ON document_content USING gin(to_tsvector('english', searchable_text));

-- Triggers
CREATE TRIGGER document_content_update_timestamp
    BEFORE UPDATE ON document_content
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER document_content_update_searchable
    BEFORE INSERT OR UPDATE OF canonical_data ON document_content
    FOR EACH ROW
    EXECUTE FUNCTION update_searchable_text();

COMMENT ON TABLE document_content IS 'Flexible JSONB storage for canonical document data with full-text search';
COMMENT ON COLUMN document_content.canonical_data IS 'Schema-agnostic JSONB storage for parsed document content';
COMMENT ON COLUMN document_content.searchable_text IS 'Auto-extracted text from canonical_data for full-text search';
COMMENT ON COLUMN document_content.extracted_entities IS 'Named entities (people, locations, measurements, etc.) extracted from content';
COMMENT ON COLUMN document_content.tags IS 'User-defined or auto-generated tags for categorization';
COMMENT ON COLUMN document_content.confidence_score IS 'Overall confidence in parsed data quality (0-1)';
COMMENT ON COLUMN document_content.validation_errors IS 'Array of validation errors or warnings';

-- =====================================================================
-- Verification Query
-- =====================================================================
-- Run this to verify tables are created:
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
-- AND table_name IN ('schema_versions', 'profiles', 'documents', 'document_content');
--
-- Check indexes:
-- SELECT indexname FROM pg_indexes WHERE tablename IN ('profiles', 'documents', 'document_content');
--
-- Check triggers:
-- SELECT tgname, tgrelid::regclass FROM pg_trigger WHERE tgname LIKE '%update%';

-- =====================================================================
-- END OF MIGRATION 003
-- =====================================================================
