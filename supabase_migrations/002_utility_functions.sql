-- =====================================================================
-- MAPS Supabase Migration 002: Utility Functions and Triggers
-- =====================================================================
-- Purpose: Create reusable trigger functions and utility procedures
-- Date: November 25, 2025
-- =====================================================================

-- ---------------------------------------------------------------------
-- Trigger Function: Auto-update updated_at timestamp
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_updated_at_column() IS 'Automatically updates the updated_at column to current timestamp on row modification';

-- ---------------------------------------------------------------------
-- Trigger Function: Auto-set parsed_at when status becomes completed
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_parsed_at()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status AND NEW.status = 'completed' THEN
        NEW.parsed_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_parsed_at() IS 'Sets parsed_at timestamp when document status changes to completed';

-- ---------------------------------------------------------------------
-- Trigger Function: Log status changes to ingestion_logs
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION log_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO ingestion_logs (document_id, log_level, message, operation, details)
        VALUES (
            NEW.id,
            'INFO',
            FORMAT('Document status changed from %s to %s', OLD.status, NEW.status),
            'status_change',
            jsonb_build_object(
                'old_status', OLD.status,
                'new_status', NEW.status,
                'changed_at', NOW()
            )
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION log_status_change() IS 'Automatically logs document status changes to ingestion_logs table';

-- ---------------------------------------------------------------------
-- Trigger Function: Auto-populate searchable_text from canonical_data
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_searchable_text()
RETURNS TRIGGER AS $$
BEGIN
    -- Extract all text values from JSONB and concatenate
    -- This creates a searchable index of all content
    NEW.searchable_text = (
        SELECT string_agg(value::text, ' ')
        FROM jsonb_each_text(NEW.canonical_data)
        WHERE value IS NOT NULL AND value::text != ''
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_searchable_text() IS 'Extracts and concatenates all text values from canonical_data JSONB for full-text search';

-- ---------------------------------------------------------------------
-- Utility Function: Generate content hash for deduplication
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION generate_content_hash(content_text TEXT)
RETURNS VARCHAR(64) AS $$
BEGIN
    RETURN encode(digest(content_text, 'sha256'), 'hex');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION generate_content_hash(TEXT) IS 'Generates SHA-256 hash of content for deduplication detection';

-- ---------------------------------------------------------------------
-- Utility Function: Extract numeric values from JSONB
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION extract_numeric_from_jsonb(data JSONB)
RETURNS JSONB AS $$
DECLARE
    result JSONB := '{}'::jsonb;
    key TEXT;
    value JSONB;
BEGIN
    FOR key, value IN SELECT * FROM jsonb_each(data)
    LOOP
        IF jsonb_typeof(value) = 'number' THEN
            result := result || jsonb_build_object(key, value);
        ELSIF jsonb_typeof(value) = 'object' THEN
            result := result || jsonb_build_object(key, extract_numeric_from_jsonb(value));
        ELSIF jsonb_typeof(value) = 'array' THEN
            -- Skip arrays for now (can be enhanced if needed)
            NULL;
        END IF;
    END LOOP;
    RETURN result;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION extract_numeric_from_jsonb(JSONB) IS 'Recursively extracts numeric values from JSONB object';

-- ---------------------------------------------------------------------
-- Utility Function: Calculate string similarity score
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION calculate_similarity(text1 TEXT, text2 TEXT)
RETURNS REAL AS $$
BEGIN
    RETURN similarity(LOWER(text1), LOWER(text2));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_similarity(TEXT, TEXT) IS 'Calculates trigram similarity score (0.0-1.0) between two strings';

-- ---------------------------------------------------------------------
-- Utility Function: Validate UUID format
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION is_valid_uuid(uuid_text TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    PERFORM uuid_text::UUID;
    RETURN TRUE;
EXCEPTION
    WHEN others THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION is_valid_uuid(TEXT) IS 'Validates if text string is a valid UUID format';

-- =====================================================================
-- Verification Query
-- =====================================================================
-- Run this to verify functions are created:
-- SELECT proname, prosrc FROM pg_proc WHERE proname IN (
--     'update_updated_at_column', 'update_parsed_at', 'log_status_change',
--     'update_searchable_text', 'generate_content_hash', 'extract_numeric_from_jsonb',
--     'calculate_similarity', 'is_valid_uuid'
-- );

-- =====================================================================
-- END OF MIGRATION 002
-- =====================================================================
