-- =====================================================================
-- MAPS Supabase Migration 008: Database Views
-- =====================================================================
-- Purpose: Create views for common UI query patterns and analytics
-- Date: November 25, 2025
-- =====================================================================

-- ---------------------------------------------------------------------
-- View: v_document_list (For Documents page UI)
-- ---------------------------------------------------------------------
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

    -- Content preview
    COALESCE(d.parsed_content_preview, LEFT(c.searchable_text, 500)) AS content_preview,

    -- Tags from document_content
    c.tags,

    -- Profile info
    p.profile_name,

    -- Detection details (if available)
    dd.match_percentage,
    dd.total_expected,
    dd.total_detected,

    -- Calculated fields
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

COMMENT ON VIEW v_document_list IS 'Comprehensive document listing view for UI with all relevant metadata';

-- ---------------------------------------------------------------------
-- View: v_document_detail (For Document Detail Modal)
-- ---------------------------------------------------------------------
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

    -- Profile info
    p.profile_name,
    p.description AS profile_description,

    -- Full content
    c.canonical_data,
    c.searchable_text,
    c.extracted_entities,
    c.tags,
    c.confidence_score AS content_confidence,
    c.schema_version,

    -- Detection details
    dd.expected_attributes,
    dd.detected_attributes,
    dd.missing_attributes,
    dd.match_percentage,
    dd.field_analysis,
    dd.detector_type,
    dd.detected_at,

    -- Statistics
    (SELECT COUNT(*) FROM ingestion_logs WHERE document_id = d.id) AS log_count,
    (SELECT COUNT(*) FROM ingestion_logs WHERE document_id = d.id AND log_level = 'ERROR') AS error_count

FROM documents d
LEFT JOIN document_content c ON d.id = c.document_id
LEFT JOIN profiles p ON d.profile_id = p.id
LEFT JOIN detection_details dd ON d.id = dd.document_id;

COMMENT ON VIEW v_document_detail IS 'Complete document details including content, detection analysis, and statistics';

-- ---------------------------------------------------------------------
-- View: v_documents_by_parse_case (Statistics for UI)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_documents_by_parse_case AS
SELECT
    parse_case,
    COUNT(*) AS total_documents,
    AVG(detection_confidence) AS avg_confidence,
    MIN(detection_confidence) AS min_confidence,
    MAX(detection_confidence) AS max_confidence,
    SUM(keywords_count) AS total_keywords,
    AVG(keywords_count) AS avg_keywords_per_doc,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_count,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
    MAX(parsed_at) AS last_parsed_at
FROM documents
WHERE parse_case IS NOT NULL
GROUP BY parse_case
ORDER BY total_documents DESC;

COMMENT ON VIEW v_documents_by_parse_case IS 'Statistics grouped by parse case for analytics dashboard';

-- ---------------------------------------------------------------------
-- View: v_detection_summary (Detection Analysis for UI)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_detection_summary AS
SELECT
    dd.id,
    dd.parse_case,
    dd.confidence,
    dd.match_percentage,
    dd.total_expected,
    dd.total_detected,
    dd.detector_type,
    dd.detection_method,
    dd.detected_at,

    -- Extract attribute names from JSONB arrays
    (SELECT jsonb_agg(attr->>'name')
     FROM jsonb_array_elements(dd.expected_attributes) attr) AS expected_attr_names,

    (SELECT jsonb_agg(attr->>'name')
     FROM jsonb_array_elements(dd.detected_attributes) attr) AS detected_attr_names,

    (SELECT jsonb_agg(attr->>'name')
     FROM jsonb_array_elements(dd.missing_attributes) attr) AS missing_attr_names,

    -- Document info
    d.source_file_name,
    d.status AS document_status,
    d.file_type

FROM detection_details dd
LEFT JOIN documents d ON dd.document_id = d.id
ORDER BY dd.detected_at DESC;

COMMENT ON VIEW v_detection_summary IS 'Detection analysis summary with extracted attribute names for UI display';

-- ---------------------------------------------------------------------
-- View: v_keyword_consolidated (All keyword data)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_keyword_consolidated AS
SELECT
    k.keyword_id,
    k.keyword_text,
    k.normalized_form,
    k.category,
    k.is_standard,
    k.vocabulary_source,
    k.definition,

    -- Statistics
    ks.total_frequency,
    ks.document_count,
    ks.idf_score,
    ks.avg_tf_idf,
    ks.last_calculated,

    -- Synonym count
    (SELECT COUNT(*) FROM keyword_synonyms WHERE canonical_keyword_id = k.keyword_id) AS synonym_count,

    -- Occurrence count
    (SELECT COUNT(*) FROM keyword_occurrences WHERE keyword_id = k.keyword_id) AS occurrence_count

FROM keywords k
LEFT JOIN keyword_statistics ks ON k.keyword_id = ks.keyword_id
ORDER BY ks.total_frequency DESC NULLS LAST;

COMMENT ON VIEW v_keyword_consolidated IS 'All keyword data with statistics and counts for UI';

-- ---------------------------------------------------------------------
-- View: v_cross_type_keywords (Keywords in both quan/qual - HIGH SIGNAL)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_cross_type_keywords AS
SELECT
    k.keyword_id,
    k.keyword_text,
    k.category,

    -- Occurrence counts by segment type
    SUM(CASE WHEN ko.segment_type = 'quantitative' THEN 1 ELSE 0 END) AS quantitative_count,
    SUM(CASE WHEN ko.segment_type = 'qualitative' THEN 1 ELSE 0 END) AS qualitative_count,
    SUM(CASE WHEN ko.segment_type = 'mixed' THEN 1 ELSE 0 END) AS mixed_count,

    COUNT(DISTINCT ko.segment_id) AS total_segments,
    COUNT(*) AS total_occurrences,

    -- Files where this keyword appears
    COUNT(DISTINCT
        CASE WHEN ko.segment_type = 'quantitative'
        THEN (SELECT file_id FROM quantitative_segments WHERE segment_id = ko.segment_id)
        WHEN ko.segment_type = 'qualitative'
        THEN (SELECT file_id FROM qualitative_segments WHERE segment_id = ko.segment_id)
        WHEN ko.segment_type = 'mixed'
        THEN (SELECT file_id FROM mixed_segments WHERE segment_id = ko.segment_id)
        END
    ) AS file_count

FROM keywords k
INNER JOIN keyword_occurrences ko ON k.keyword_id = ko.keyword_id
GROUP BY k.keyword_id, k.keyword_text, k.category
HAVING
    -- Must appear in at least 2 different segment types
    COUNT(DISTINCT ko.segment_type) >= 2
ORDER BY total_occurrences DESC;

COMMENT ON VIEW v_cross_type_keywords IS 'Keywords appearing in multiple segment types - high confidence signals for case detection';

-- ---------------------------------------------------------------------
-- View: v_ingestion_health (Daily metrics for last 30 days)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_ingestion_health AS
SELECT
    ingestion_timestamp::DATE AS date,
    COUNT(*) AS total_documents,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS successful,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
    SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) AS processing,
    AVG(processing_duration_ms)::NUMERIC(10,2) AS avg_processing_time_ms,
    AVG(keywords_count)::NUMERIC(10,2) AS avg_keywords_per_doc
FROM documents
WHERE ingestion_timestamp >= NOW() - INTERVAL '30 days'
GROUP BY ingestion_timestamp::DATE
ORDER BY ingestion_timestamp::DATE DESC;

COMMENT ON VIEW v_ingestion_health IS 'Daily ingestion health metrics for last 30 days';

-- ---------------------------------------------------------------------
-- View: v_pending_queue_summary (Approval queue overview)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_pending_queue_summary AS
SELECT
    pca.pending_id,
    pca.file_id,
    d.source_file_name,
    d.file_type,

    -- Detection info
    pca.confidence_score,
    pca.detection_method,
    pca.review_status,
    pc.name AS suggested_case_name,
    pc.description AS suggested_case_description,

    -- Evidence
    pca.keyword_signature,
    array_length(pca.keyword_ids, 1) AS keyword_count,

    -- Review tracking
    pca.reviewed_by,
    pca.reviewed_at,
    pca.created_at,

    -- Age in hours
    EXTRACT(EPOCH FROM (NOW() - pca.created_at)) / 3600 AS age_hours

FROM pending_case_assignment pca
LEFT JOIN documents d ON pca.file_id = d.id
LEFT JOIN parse_cases pc ON pca.suggested_case_id = pc.id
WHERE pca.review_status = 'pending'
ORDER BY pca.confidence_score DESC, pca.created_at ASC;

COMMENT ON VIEW v_pending_queue_summary IS 'Approval queue overview for manual review UI';

-- ---------------------------------------------------------------------
-- View: v_batch_processing_status (Batch progress tracking)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_batch_processing_status AS
SELECT
    bm.id AS batch_id,
    bm.batch_name,
    bm.status,
    bm.total_files,
    bm.successful,
    bm.failed,
    bm.skipped,

    -- Progress percentage
    CASE
        WHEN bm.total_files > 0
        THEN ROUND((bm.successful + bm.failed + bm.skipped)::NUMERIC / bm.total_files * 100, 2)
        ELSE 0
    END AS progress_percentage,

    -- Performance metrics
    bm.started_at,
    bm.completed_at,
    CASE
        WHEN bm.completed_at IS NOT NULL
        THEN EXTRACT(EPOCH FROM (bm.completed_at - bm.started_at))
        ELSE EXTRACT(EPOCH FROM (NOW() - bm.started_at))
    END AS duration_seconds,

    -- Error rate
    CASE
        WHEN bm.total_files > 0
        THEN ROUND(bm.failed::NUMERIC / bm.total_files * 100, 2)
        ELSE 0
    END AS error_rate_percentage,

    p.profile_name,
    bm.uploaded_by

FROM batch_metadata bm
LEFT JOIN profiles p ON bm.profile_id = p.id
ORDER BY bm.started_at DESC;

COMMENT ON VIEW v_batch_processing_status IS 'Real-time batch processing status with progress and performance metrics';

-- =====================================================================
-- Update schema version
-- =====================================================================
INSERT INTO schema_versions (version, description)
VALUES (8, 'Database views for common UI query patterns and analytics');

-- =====================================================================
-- Verification Query
-- =====================================================================
-- Run this to verify views are created:
-- SELECT table_name FROM information_schema.views
-- WHERE table_schema = 'public'
-- AND table_name LIKE 'v_%'
-- ORDER BY table_name;
--
-- Test a view:
-- SELECT * FROM v_document_list LIMIT 5;

-- =====================================================================
-- END OF MIGRATION 008
-- =====================================================================
