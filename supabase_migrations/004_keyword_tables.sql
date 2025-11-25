-- =====================================================================
-- MAPS Supabase Migration 004: Keyword System Tables
-- =====================================================================
-- Purpose: Create comprehensive keyword tracking and analysis system
-- Date: November 25, 2025
-- =====================================================================

-- ---------------------------------------------------------------------
-- Table: keywords
-- ---------------------------------------------------------------------
CREATE TABLE keywords (
    keyword_id SERIAL PRIMARY KEY,
    keyword_text VARCHAR(255) NOT NULL,
    normalized_form VARCHAR(255),
    category VARCHAR(100),

    -- Standardized vocabulary support
    is_standard BOOLEAN DEFAULT FALSE,
    vocabulary_source VARCHAR(100),  -- RadLex, LOINC, Lung-RADS, SNOMED, etc.
    source_refs TEXT,  -- External ID or reference code
    definition TEXT,
    description TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Unique constraint on keyword text (case-insensitive)
CREATE UNIQUE INDEX idx_keywords_text_lower ON keywords(LOWER(keyword_text));

-- Indexes
CREATE INDEX idx_keywords_normalized_form ON keywords(normalized_form) WHERE normalized_form IS NOT NULL;
CREATE INDEX idx_keywords_category ON keywords(category) WHERE category IS NOT NULL;
CREATE INDEX idx_keywords_vocabulary_source ON keywords(vocabulary_source) WHERE vocabulary_source IS NOT NULL;
CREATE INDEX idx_keywords_is_standard ON keywords(is_standard) WHERE is_standard = TRUE;

-- Full-text search on keyword_text
CREATE INDEX idx_keywords_text_search ON keywords USING gin(to_tsvector('english', keyword_text));

-- Trigger
CREATE TRIGGER keywords_update_timestamp
    BEFORE UPDATE ON keywords
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE keywords IS 'Master keyword vocabulary with support for standardized medical terminologies';
COMMENT ON COLUMN keywords.vocabulary_source IS 'Source of standardized term (RadLex, LOINC, Lung-RADS, SNOMED CT, etc.)';
COMMENT ON COLUMN keywords.source_refs IS 'External reference ID or code from vocabulary source';

-- ---------------------------------------------------------------------
-- Table: keyword_statistics
-- ---------------------------------------------------------------------
CREATE TABLE keyword_statistics (
    stats_id SERIAL PRIMARY KEY,
    keyword_id INTEGER NOT NULL UNIQUE REFERENCES keywords(keyword_id) ON DELETE CASCADE,

    -- Usage statistics
    total_frequency INTEGER DEFAULT 0,
    document_count INTEGER DEFAULT 0,

    -- TF-IDF metrics
    idf_score DECIMAL(10, 6),
    avg_tf_idf DECIMAL(10, 6),

    -- Timestamps
    last_calculated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_keyword_statistics_keyword_id ON keyword_statistics(keyword_id);
CREATE INDEX idx_keyword_statistics_document_count ON keyword_statistics(document_count DESC);
CREATE INDEX idx_keyword_statistics_total_frequency ON keyword_statistics(total_frequency DESC);
CREATE INDEX idx_keyword_statistics_idf_score ON keyword_statistics(idf_score DESC) WHERE idf_score IS NOT NULL;

-- Trigger
CREATE TRIGGER keyword_statistics_update_timestamp
    BEFORE UPDATE ON keyword_statistics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE keyword_statistics IS 'Statistical metrics for keyword usage and relevance (TF-IDF, frequency)';

-- ---------------------------------------------------------------------
-- Table: keyword_synonyms
-- ---------------------------------------------------------------------
CREATE TABLE keyword_synonyms (
    synonym_id SERIAL PRIMARY KEY,
    canonical_keyword_id INTEGER NOT NULL REFERENCES keywords(keyword_id) ON DELETE CASCADE,
    synonym_text VARCHAR(255) NOT NULL,
    synonym_type VARCHAR(50) DEFAULT 'alternate',  -- alternate, abbreviation, misspelling, etc.
    confidence DECIMAL(3, 2) CHECK (confidence >= 0 AND confidence <= 1),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Unique constraint: one synonym maps to one canonical keyword
CREATE UNIQUE INDEX idx_keyword_synonyms_unique ON keyword_synonyms(canonical_keyword_id, LOWER(synonym_text));

-- Indexes
CREATE INDEX idx_keyword_synonyms_canonical_id ON keyword_synonyms(canonical_keyword_id);
CREATE INDEX idx_keyword_synonyms_text_lower ON keyword_synonyms(LOWER(synonym_text));
CREATE INDEX idx_keyword_synonyms_type ON keyword_synonyms(synonym_type);

-- Trigger
CREATE TRIGGER keyword_synonyms_update_timestamp
    BEFORE UPDATE ON keyword_synonyms
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE keyword_synonyms IS 'Synonym mappings to canonical keywords for normalization';
COMMENT ON COLUMN keyword_synonyms.confidence IS 'Confidence score for fuzzy matches (0-1)';

-- ---------------------------------------------------------------------
-- Table: keyword_sources
-- ---------------------------------------------------------------------
CREATE TABLE keyword_sources (
    source_id SERIAL PRIMARY KEY,
    keyword_id INTEGER NOT NULL REFERENCES keywords(keyword_id) ON DELETE CASCADE,

    -- Source metadata
    source_type VARCHAR(50) NOT NULL,  -- xml, pdf, research_paper, manual_entry, etc.
    source_file VARCHAR(500),
    sector VARCHAR(100),  -- lidc, luna16, custom, etc.
    frequency INTEGER DEFAULT 1,

    -- Timestamps
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Unique constraint: one keyword per source file
CREATE UNIQUE INDEX idx_keyword_sources_unique ON keyword_sources(keyword_id, source_file);

-- Indexes
CREATE INDEX idx_keyword_sources_keyword_id ON keyword_sources(keyword_id);
CREATE INDEX idx_keyword_sources_source_type ON keyword_sources(source_type);
CREATE INDEX idx_keyword_sources_sector ON keyword_sources(sector) WHERE sector IS NOT NULL;
CREATE INDEX idx_keyword_sources_frequency ON keyword_sources(frequency DESC);

-- Trigger
CREATE TRIGGER keyword_sources_update_timestamp
    BEFORE UPDATE ON keyword_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE keyword_sources IS 'Track which files and sources contributed each keyword';

-- ---------------------------------------------------------------------
-- Table: keyword_search_history
-- ---------------------------------------------------------------------
CREATE TABLE keyword_search_history (
    search_id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    result_count INTEGER DEFAULT 0,
    execution_time_ms DECIMAL(10, 2),
    user_sector VARCHAR(100),

    -- Timestamps
    search_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_keyword_search_history_timestamp ON keyword_search_history(search_timestamp DESC);
CREATE INDEX idx_keyword_search_history_query_text ON keyword_search_history USING gin(to_tsvector('english', query_text));
CREATE INDEX idx_keyword_search_history_user_sector ON keyword_search_history(user_sector) WHERE user_sector IS NOT NULL;

COMMENT ON TABLE keyword_search_history IS 'Analytics for keyword search queries and performance';

-- ---------------------------------------------------------------------
-- Table: keyword_reference_sources
-- ---------------------------------------------------------------------
CREATE TABLE keyword_reference_sources (
    source_id SERIAL PRIMARY KEY,
    citation TEXT NOT NULL,
    title TEXT,
    authors TEXT,
    journal VARCHAR(255),
    year INTEGER,
    doi VARCHAR(100),
    url TEXT,
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_keyword_reference_sources_year ON keyword_reference_sources(year DESC) WHERE year IS NOT NULL;
CREATE INDEX idx_keyword_reference_sources_doi ON keyword_reference_sources(doi) WHERE doi IS NOT NULL;
CREATE INDEX idx_keyword_reference_sources_journal ON keyword_reference_sources(journal) WHERE journal IS NOT NULL;

-- Trigger
CREATE TRIGGER keyword_reference_sources_update_timestamp
    BEFORE UPDATE ON keyword_reference_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE keyword_reference_sources IS 'Research papers and sources for keyword definitions';

-- ---------------------------------------------------------------------
-- Table: stop_words
-- ---------------------------------------------------------------------
CREATE TABLE stop_words (
    term VARCHAR(100) PRIMARY KEY,
    category VARCHAR(50) DEFAULT 'common_english',  -- common_english, domain, custom
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_stop_words_category ON stop_words(category);
CREATE INDEX idx_stop_words_is_active ON stop_words(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE stop_words IS 'Stop words to filter out during keyword extraction';

-- =====================================================================
-- Update schema version
-- =====================================================================
INSERT INTO schema_versions (version, description)
VALUES (4, 'Keyword system tables with statistics, synonyms, and sources');

-- =====================================================================
-- Verification Query
-- =====================================================================
-- Run this to verify tables are created:
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
-- AND table_name LIKE 'keyword%' OR table_name = 'stop_words'
-- ORDER BY table_name;
--
-- Check indexes:
-- SELECT indexname FROM pg_indexes WHERE tablename LIKE 'keyword%' OR tablename = 'stop_words';

-- =====================================================================
-- END OF MIGRATION 004
-- =====================================================================
