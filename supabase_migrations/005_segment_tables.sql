-- =====================================================================
-- MAPS Supabase Migration 005: Content Segment Tables
-- =====================================================================
-- Purpose: Schema-agnostic content classification (quantitative/qualitative/mixed)
-- Date: November 25, 2025
-- =====================================================================

-- ---------------------------------------------------------------------
-- Table: quantitative_segments
-- ---------------------------------------------------------------------
CREATE TABLE quantitative_segments (
    segment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    -- Numeric/tabular data storage
    data_structure JSONB NOT NULL,  -- Actual numeric data
    column_mappings JSONB,  -- Detected column schema
    detected_schema VARCHAR(255),
    row_count INTEGER,

    -- Position tracking
    segment_order INTEGER,  -- Order within file
    start_position JSONB,  -- File-specific positioning metadata
    end_position JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_quantitative_segments_file_id ON quantitative_segments(file_id);
CREATE INDEX idx_quantitative_segments_row_count ON quantitative_segments(row_count) WHERE row_count IS NOT NULL;
CREATE INDEX idx_quantitative_segments_segment_order ON quantitative_segments(file_id, segment_order);

-- GIN indexes for JSONB
CREATE INDEX idx_quantitative_segments_data_structure ON quantitative_segments USING gin(data_structure);
CREATE INDEX idx_quantitative_segments_data_structure_path ON quantitative_segments USING gin(data_structure jsonb_path_ops);
CREATE INDEX idx_quantitative_segments_column_mappings ON quantitative_segments USING gin(column_mappings);

-- Trigger
CREATE TRIGGER quantitative_segments_update_timestamp
    BEFORE UPDATE ON quantitative_segments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE quantitative_segments IS 'Numeric/tabular data segments with flexible JSONB storage';
COMMENT ON COLUMN quantitative_segments.data_structure IS 'Actual numeric data in flexible JSONB format';
COMMENT ON COLUMN quantitative_segments.column_mappings IS 'Detected schema with column names and data types';

-- ---------------------------------------------------------------------
-- Table: qualitative_segments
-- ---------------------------------------------------------------------
CREATE TABLE qualitative_segments (
    segment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    -- Text content
    text_content TEXT NOT NULL,
    segment_type qualitative_segment_subtype_enum DEFAULT 'body',

    -- Position tracking
    segment_order INTEGER,
    position_in_file JSONB,  -- Start/end markers, page numbers, etc.

    -- Metadata
    word_count INTEGER,
    character_count INTEGER,
    language VARCHAR(10) DEFAULT 'en',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_qualitative_segments_file_id ON qualitative_segments(file_id);
CREATE INDEX idx_qualitative_segments_segment_type ON qualitative_segments(segment_type);
CREATE INDEX idx_qualitative_segments_segment_order ON qualitative_segments(file_id, segment_order);
CREATE INDEX idx_qualitative_segments_word_count ON qualitative_segments(word_count) WHERE word_count IS NOT NULL;

-- GIN index for JSONB
CREATE INDEX idx_qualitative_segments_position ON qualitative_segments USING gin(position_in_file);

-- Full-text search index
CREATE INDEX idx_qualitative_segments_text_search ON qualitative_segments USING gin(to_tsvector('english', text_content));

-- Trigger
CREATE TRIGGER qualitative_segments_update_timestamp
    BEFORE UPDATE ON qualitative_segments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE qualitative_segments IS 'Text-based content segments with full-text search';
COMMENT ON COLUMN qualitative_segments.segment_type IS 'Type of text segment (abstract, body, caption, etc.)';
COMMENT ON COLUMN qualitative_segments.position_in_file IS 'Position markers for locating segment in source file';

-- ---------------------------------------------------------------------
-- Table: mixed_segments
-- ---------------------------------------------------------------------
CREATE TABLE mixed_segments (
    segment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    -- Mixed content storage
    structure JSONB NOT NULL,  -- Overall structure with both types
    text_elements TEXT[],  -- Array of text chunks
    numeric_elements JSONB,  -- Numeric data interspersed with text

    -- Position tracking
    segment_order INTEGER,
    position_in_file JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_mixed_segments_file_id ON mixed_segments(file_id);
CREATE INDEX idx_mixed_segments_segment_order ON mixed_segments(file_id, segment_order);

-- GIN indexes
CREATE INDEX idx_mixed_segments_structure ON mixed_segments USING gin(structure);
CREATE INDEX idx_mixed_segments_structure_path ON mixed_segments USING gin(structure jsonb_path_ops);
CREATE INDEX idx_mixed_segments_numeric_elements ON mixed_segments USING gin(numeric_elements);
CREATE INDEX idx_mixed_segments_text_elements ON mixed_segments USING gin(text_elements);

-- Trigger
CREATE TRIGGER mixed_segments_update_timestamp
    BEFORE UPDATE ON mixed_segments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE mixed_segments IS 'Segments containing interleaved text and numeric data';
COMMENT ON COLUMN mixed_segments.structure IS 'Overall structure showing text/numeric interleaving';
COMMENT ON COLUMN mixed_segments.text_elements IS 'Ordered array of text chunks';
COMMENT ON COLUMN mixed_segments.numeric_elements IS 'Numeric data elements with context';

-- ---------------------------------------------------------------------
-- Table: keyword_occurrences (Polymorphic linking table)
-- ---------------------------------------------------------------------
CREATE TABLE keyword_occurrences (
    occurrence_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword_id INTEGER NOT NULL REFERENCES keywords(keyword_id) ON DELETE CASCADE,

    -- Polymorphic segment reference
    segment_id UUID NOT NULL,
    segment_type segment_type_enum NOT NULL,

    -- Context and associations
    surrounding_context TEXT,  -- Text around keyword occurrence
    associated_values JSONB,  -- Numeric values near keyword
    position INTEGER,  -- Position within segment

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_keyword_occurrences_keyword_id ON keyword_occurrences(keyword_id);
CREATE INDEX idx_keyword_occurrences_segment ON keyword_occurrences(segment_id, segment_type);
CREATE INDEX idx_keyword_occurrences_segment_type ON keyword_occurrences(segment_type);

-- GIN index for associated_values
CREATE INDEX idx_keyword_occurrences_associated_values ON keyword_occurrences USING gin(associated_values);

-- Composite index for cross-type keyword detection
CREATE INDEX idx_keyword_occurrences_keyword_type ON keyword_occurrences(keyword_id, segment_type);

COMMENT ON TABLE keyword_occurrences IS 'Polymorphic keyword occurrences linking to any segment type';
COMMENT ON COLUMN keyword_occurrences.segment_type IS 'Type of segment (quantitative/qualitative/mixed) for polymorphic lookup';
COMMENT ON COLUMN keyword_occurrences.associated_values IS 'Numeric values found near keyword (e.g., measurements, coordinates)';

-- =====================================================================
-- Update schema version
-- =====================================================================
INSERT INTO schema_versions (version, description)
VALUES (5, 'Content segment tables (quantitative, qualitative, mixed) with polymorphic keyword occurrences');

-- =====================================================================
-- Verification Query
-- =====================================================================
-- Run this to verify tables are created:
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
-- AND table_name LIKE '%segment%' OR table_name = 'keyword_occurrences'
-- ORDER BY table_name;
--
-- Check indexes:
-- SELECT indexname, indexdef FROM pg_indexes
-- WHERE tablename LIKE '%segment%' OR tablename = 'keyword_occurrences';

-- =====================================================================
-- END OF MIGRATION 005
-- =====================================================================
