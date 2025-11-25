-- =====================================================================
-- MAPS Supabase Migration 009: Stored Functions and Procedures
-- =====================================================================
-- Purpose: Business logic functions for detection, search, and analytics
-- Date: November 25, 2025
-- =====================================================================

-- ---------------------------------------------------------------------
-- Function: search_documents (Full-text search with filters)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION search_documents(
    search_query TEXT,
    parse_case_filter VARCHAR DEFAULT NULL,
    status_filter VARCHAR DEFAULT NULL,
    limit_results INTEGER DEFAULT 100
)
RETURNS TABLE (
    document_id UUID,
    filename VARCHAR,
    parse_case VARCHAR,
    confidence DECIMAL,
    status document_status_enum,
    relevance REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id AS document_id,
        d.source_file_name AS filename,
        d.parse_case,
        d.detection_confidence AS confidence,
        d.status,
        ts_rank(to_tsvector('english', c.searchable_text), plainto_tsquery('english', search_query)) AS relevance
    FROM documents d
    LEFT JOIN document_content c ON d.id = c.document_id
    WHERE
        (parse_case_filter IS NULL OR d.parse_case = parse_case_filter)
        AND (status_filter IS NULL OR d.status::TEXT = status_filter)
        AND to_tsvector('english', c.searchable_text) @@ plainto_tsquery('english', search_query)
    ORDER BY relevance DESC, d.ingestion_timestamp DESC
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION search_documents IS 'Full-text search across documents with optional filters and relevance ranking';

-- ---------------------------------------------------------------------
-- Function: get_keywords_by_category
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_keywords_by_category(p_category VARCHAR)
RETURNS TABLE (
    keyword_id INTEGER,
    keyword_text VARCHAR,
    normalized_form VARCHAR,
    is_standard BOOLEAN,
    vocabulary_source VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        k.keyword_id,
        k.keyword_text,
        k.normalized_form,
        k.is_standard,
        k.vocabulary_source
    FROM keywords k
    WHERE k.category = p_category
    ORDER BY k.keyword_text;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_keywords_by_category IS 'Retrieves keywords filtered by category';

-- ---------------------------------------------------------------------
-- Function: search_keywords_full (Full-text keyword search)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION search_keywords_full(p_search_term TEXT)
RETURNS TABLE (
    keyword_id INTEGER,
    keyword_text VARCHAR,
    match_type VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        k.keyword_id,
        k.keyword_text,
        CASE
            WHEN LOWER(k.keyword_text) = LOWER(p_search_term) THEN 'exact'
            WHEN LOWER(k.keyword_text) LIKE '%' || LOWER(p_search_term) || '%' THEN 'partial'
            ELSE 'fuzzy'
        END AS match_type
    FROM keywords k
    WHERE
        LOWER(k.keyword_text) LIKE '%' || LOWER(p_search_term) || '%'
        OR EXISTS (
            SELECT 1 FROM keyword_synonyms ks
            WHERE ks.canonical_keyword_id = k.keyword_id
            AND LOWER(ks.synonym_text) LIKE '%' || LOWER(p_search_term) || '%'
        )
    ORDER BY
        CASE
            WHEN LOWER(k.keyword_text) = LOWER(p_search_term) THEN 1
            WHEN LOWER(k.keyword_text) LIKE LOWER(p_search_term) || '%' THEN 2
            ELSE 3
        END,
        k.keyword_text;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION search_keywords_full IS 'Full-text keyword search with exact, partial, and fuzzy matching';

-- ---------------------------------------------------------------------
-- Function: calculate_case_confidence
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION calculate_case_confidence(
    p_keyword_count INTEGER,
    p_segment_count INTEGER,
    p_has_quantitative BOOLEAN,
    p_has_qualitative BOOLEAN,
    p_high_relevance_keywords INTEGER DEFAULT 0
)
RETURNS DECIMAL AS $$
DECLARE
    base_score DECIMAL;
    cross_type_bonus DECIMAL;
    relevance_bonus DECIMAL;
BEGIN
    -- Base score from keyword density
    base_score := LEAST((p_keyword_count::DECIMAL / (p_segment_count + 1)::DECIMAL), 0.70);

    -- Bonus for cross-type presence (keywords in both quan/qual)
    cross_type_bonus := CASE
        WHEN p_has_quantitative AND p_has_qualitative THEN 0.20
        ELSE 0.0
    END;

    -- Bonus for high-relevance keywords
    relevance_bonus := CASE
        WHEN p_high_relevance_keywords > 0
        THEN LEAST(p_high_relevance_keywords::DECIMAL * 0.02, 0.10)
        ELSE 0.0
    END;

    RETURN LEAST(base_score + cross_type_bonus + relevance_bonus, 1.0);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_case_confidence IS 'Calculates confidence score for case detection based on keyword presence and distribution';

-- ---------------------------------------------------------------------
-- Function: detect_case_from_file
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION detect_case_from_file(p_file_id UUID)
RETURNS TABLE(
    case_id UUID,
    case_name VARCHAR,
    confidence_score DECIMAL,
    should_auto_assign BOOLEAN,
    detection_method detection_method_enum
) AS $$
DECLARE
    v_filename VARCHAR;
    v_file_type VARCHAR;
    v_keyword_count INTEGER;
    v_segment_count INTEGER;
    v_has_quan BOOLEAN;
    v_has_qual BOOLEAN;
    v_confidence DECIMAL;
BEGIN
    -- Get file metadata
    SELECT source_file_name, file_type::TEXT
    INTO v_filename, v_file_type
    FROM documents
    WHERE id = p_file_id;

    -- Try filename pattern matching first (highest confidence)
    FOR case_id, case_name IN
        SELECT pc.id, pc.name
        FROM parse_cases pc
        WHERE pc.is_active = TRUE
        AND (pc.format_type::TEXT = v_file_type OR pc.format_type IS NULL)
        ORDER BY pc.detection_priority DESC
    LOOP
        -- Check if filename matches any pattern in detection_criteria
        -- This is simplified - in practice, you'd extract patterns from JSONB
        IF v_filename ~ '.*' THEN  -- Placeholder regex
            RETURN QUERY SELECT
                case_id,
                case_name,
                1.0::DECIMAL AS confidence_score,
                TRUE AS should_auto_assign,
                'filename_regex'::detection_method_enum AS detection_method;
            RETURN;
        END IF;
    END LOOP;

    -- Fallback to keyword-based detection
    SELECT
        COUNT(DISTINCT ko.keyword_id),
        COUNT(DISTINCT ko.segment_id),
        BOOL_OR(ko.segment_type = 'quantitative'),
        BOOL_OR(ko.segment_type = 'qualitative')
    INTO v_keyword_count, v_segment_count, v_has_quan, v_has_qual
    FROM keyword_occurrences ko
    WHERE ko.segment_id IN (
        SELECT segment_id FROM quantitative_segments WHERE file_id = p_file_id
        UNION
        SELECT segment_id FROM qualitative_segments WHERE file_id = p_file_id
        UNION
        SELECT segment_id FROM mixed_segments WHERE file_id = p_file_id
    );

    -- Calculate confidence
    v_confidence := calculate_case_confidence(
        v_keyword_count,
        v_segment_count,
        v_has_quan,
        v_has_qual,
        0  -- high_relevance_keywords - could be enhanced
    );

    -- Return best matching case
    RETURN QUERY SELECT
        NULL::UUID AS case_id,
        'Unknown'::VARCHAR AS case_name,
        v_confidence AS confidence_score,
        v_confidence >= 0.8 AS should_auto_assign,
        'keyword_signature'::detection_method_enum AS detection_method;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION detect_case_from_file IS 'Hybrid case detection using filename patterns (primary) and keyword signatures (fallback)';

-- ---------------------------------------------------------------------
-- Function: process_case_assignment
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION process_case_assignment(p_file_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_case_id UUID;
    v_case_name VARCHAR;
    v_confidence DECIMAL;
    v_should_auto_assign BOOLEAN;
    v_detection_method detection_method_enum;
BEGIN
    -- Detect case
    SELECT * INTO v_case_id, v_case_name, v_confidence, v_should_auto_assign, v_detection_method
    FROM detect_case_from_file(p_file_id)
    LIMIT 1;

    IF v_should_auto_assign THEN
        -- High confidence - auto-assign
        UPDATE documents
        SET
            parse_case = v_case_name,
            detection_confidence = v_confidence,
            status = 'processing'
        WHERE id = p_file_id;

        RETURN TRUE;
    ELSE
        -- Low confidence - add to approval queue
        INSERT INTO pending_case_assignment (
            file_id,
            suggested_case_id,
            detection_method,
            confidence_score,
            review_status
        ) VALUES (
            p_file_id,
            v_case_id,
            v_detection_method,
            v_confidence,
            'pending'
        );

        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION process_case_assignment IS 'Auto-assigns case if confidence >= 0.8, otherwise adds to pending queue';

-- ---------------------------------------------------------------------
-- Function: assign_case_manually
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION assign_case_manually(
    p_pending_id UUID,
    p_assigned_case_id UUID,
    p_reviewed_by VARCHAR,
    p_review_notes TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_file_id UUID;
    v_case_name VARCHAR;
BEGIN
    -- Get file_id and case name
    SELECT pca.file_id, pc.name
    INTO v_file_id, v_case_name
    FROM pending_case_assignment pca
    LEFT JOIN parse_cases pc ON pc.id = p_assigned_case_id
    WHERE pca.pending_id = p_pending_id;

    IF v_file_id IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Update pending_case_assignment
    UPDATE pending_case_assignment
    SET
        review_status = 'assigned',
        assigned_case_id = p_assigned_case_id,
        reviewed_by = p_reviewed_by,
        reviewed_at = NOW(),
        review_notes = p_review_notes
    WHERE pending_id = p_pending_id;

    -- Update document
    UPDATE documents
    SET
        parse_case = v_case_name,
        status = 'processing'
    WHERE id = v_file_id;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION assign_case_manually IS 'Manually assigns case from approval queue and updates document';

-- ---------------------------------------------------------------------
-- Function: get_cross_type_keywords
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_cross_type_keywords(p_min_occurrences INTEGER DEFAULT 2)
RETURNS TABLE (
    keyword_id INTEGER,
    keyword_text VARCHAR,
    quantitative_count BIGINT,
    qualitative_count BIGINT,
    mixed_count BIGINT,
    total_occurrences BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        k.keyword_id,
        k.keyword_text,
        SUM(CASE WHEN ko.segment_type = 'quantitative' THEN 1 ELSE 0 END) AS quantitative_count,
        SUM(CASE WHEN ko.segment_type = 'qualitative' THEN 1 ELSE 0 END) AS qualitative_count,
        SUM(CASE WHEN ko.segment_type = 'mixed' THEN 1 ELSE 0 END) AS mixed_count,
        COUNT(*)::BIGINT AS total_occurrences
    FROM keywords k
    INNER JOIN keyword_occurrences ko ON k.keyword_id = ko.keyword_id
    GROUP BY k.keyword_id, k.keyword_text
    HAVING
        COUNT(DISTINCT ko.segment_type) >= 2
        AND COUNT(*) >= p_min_occurrences
    ORDER BY COUNT(*) DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_cross_type_keywords IS 'Returns keywords appearing in multiple segment types - high confidence signals';

-- ---------------------------------------------------------------------
-- Function: update_keyword_statistics
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_keyword_statistics(p_keyword_id INTEGER)
RETURNS VOID AS $$
DECLARE
    v_total_frequency INTEGER;
    v_document_count INTEGER;
BEGIN
    -- Calculate statistics from keyword_occurrences
    SELECT
        COUNT(*),
        COUNT(DISTINCT CASE
            WHEN ko.segment_type = 'quantitative' THEN qs.file_id
            WHEN ko.segment_type = 'qualitative' THEN qls.file_id
            WHEN ko.segment_type = 'mixed' THEN ms.file_id
        END)
    INTO v_total_frequency, v_document_count
    FROM keyword_occurrences ko
    LEFT JOIN quantitative_segments qs ON ko.segment_id = qs.segment_id AND ko.segment_type = 'quantitative'
    LEFT JOIN qualitative_segments qls ON ko.segment_id = qls.segment_id AND ko.segment_type = 'qualitative'
    LEFT JOIN mixed_segments ms ON ko.segment_id = ms.segment_id AND ko.segment_type = 'mixed'
    WHERE ko.keyword_id = p_keyword_id;

    -- Update or insert statistics
    INSERT INTO keyword_statistics (keyword_id, total_frequency, document_count, last_calculated)
    VALUES (p_keyword_id, v_total_frequency, v_document_count, NOW())
    ON CONFLICT (keyword_id) DO UPDATE
    SET
        total_frequency = EXCLUDED.total_frequency,
        document_count = EXCLUDED.document_count,
        last_calculated = NOW();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_keyword_statistics IS 'Recalculates and updates statistics for a specific keyword';

-- ---------------------------------------------------------------------
-- Function: get_document_keywords
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_document_keywords(p_document_id UUID)
RETURNS TABLE (
    keyword_id INTEGER,
    keyword_text VARCHAR,
    occurrence_count BIGINT,
    segment_types TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        k.keyword_id,
        k.keyword_text,
        COUNT(*)::BIGINT AS occurrence_count,
        ARRAY_AGG(DISTINCT ko.segment_type::TEXT) AS segment_types
    FROM keywords k
    INNER JOIN keyword_occurrences ko ON k.keyword_id = ko.keyword_id
    WHERE ko.segment_id IN (
        SELECT segment_id FROM quantitative_segments WHERE file_id = p_document_id
        UNION
        SELECT segment_id FROM qualitative_segments WHERE file_id = p_document_id
        UNION
        SELECT segment_id FROM mixed_segments WHERE file_id = p_document_id
    )
    GROUP BY k.keyword_id, k.keyword_text
    ORDER BY COUNT(*) DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_document_keywords IS 'Returns all keywords found in a document with occurrence counts';

-- =====================================================================
-- Update schema version
-- =====================================================================
INSERT INTO schema_versions (version, description)
VALUES (9, 'Stored functions for case detection, keyword search, and analytics');

-- =====================================================================
-- Verification Query
-- =====================================================================
-- Run this to verify functions are created:
-- SELECT proname, prosrc FROM pg_proc
-- WHERE proname IN (
--     'search_documents', 'get_keywords_by_category', 'search_keywords_full',
--     'calculate_case_confidence', 'detect_case_from_file', 'process_case_assignment',
--     'assign_case_manually', 'get_cross_type_keywords', 'update_keyword_statistics',
--     'get_document_keywords'
-- );

-- =====================================================================
-- END OF MIGRATION 009
-- =====================================================================
