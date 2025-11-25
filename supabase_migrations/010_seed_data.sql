-- =====================================================================
-- MAPS Supabase Migration 010: Seed Data
-- =====================================================================
-- Purpose: Initial data for stop words, default profiles, and sample parse cases
-- Date: November 25, 2025
-- =====================================================================

-- ---------------------------------------------------------------------
-- Seed: Stop Words (Common English)
-- ---------------------------------------------------------------------
INSERT INTO stop_words (term, category, is_active) VALUES
    -- Articles
    ('a', 'common_english', TRUE),
    ('an', 'common_english', TRUE),
    ('the', 'common_english', TRUE),

    -- Conjunctions
    ('and', 'common_english', TRUE),
    ('or', 'common_english', TRUE),
    ('but', 'common_english', TRUE),
    ('yet', 'common_english', TRUE),
    ('so', 'common_english', TRUE),
    ('nor', 'common_english', TRUE),

    -- Prepositions
    ('in', 'common_english', TRUE),
    ('on', 'common_english', TRUE),
    ('at', 'common_english', TRUE),
    ('to', 'common_english', TRUE),
    ('for', 'common_english', TRUE),
    ('of', 'common_english', TRUE),
    ('with', 'common_english', TRUE),
    ('from', 'common_english', TRUE),
    ('by', 'common_english', TRUE),
    ('about', 'common_english', TRUE),
    ('into', 'common_english', TRUE),
    ('through', 'common_english', TRUE),
    ('during', 'common_english', TRUE),
    ('before', 'common_english', TRUE),
    ('after', 'common_english', TRUE),
    ('above', 'common_english', TRUE),
    ('below', 'common_english', TRUE),
    ('between', 'common_english', TRUE),
    ('under', 'common_english', TRUE),
    ('over', 'common_english', TRUE),

    -- Pronouns
    ('i', 'common_english', TRUE),
    ('you', 'common_english', TRUE),
    ('he', 'common_english', TRUE),
    ('she', 'common_english', TRUE),
    ('it', 'common_english', TRUE),
    ('we', 'common_english', TRUE),
    ('they', 'common_english', TRUE),
    ('me', 'common_english', TRUE),
    ('him', 'common_english', TRUE),
    ('her', 'common_english', TRUE),
    ('us', 'common_english', TRUE),
    ('them', 'common_english', TRUE),
    ('my', 'common_english', TRUE),
    ('your', 'common_english', TRUE),
    ('his', 'common_english', TRUE),
    ('its', 'common_english', TRUE),
    ('our', 'common_english', TRUE),
    ('their', 'common_english', TRUE),
    ('this', 'common_english', TRUE),
    ('that', 'common_english', TRUE),
    ('these', 'common_english', TRUE),
    ('those', 'common_english', TRUE),

    -- Verbs
    ('is', 'common_english', TRUE),
    ('are', 'common_english', TRUE),
    ('was', 'common_english', TRUE),
    ('were', 'common_english', TRUE),
    ('been', 'common_english', TRUE),
    ('be', 'common_english', TRUE),
    ('have', 'common_english', TRUE),
    ('has', 'common_english', TRUE),
    ('had', 'common_english', TRUE),
    ('do', 'common_english', TRUE),
    ('does', 'common_english', TRUE),
    ('did', 'common_english', TRUE),
    ('will', 'common_english', TRUE),
    ('would', 'common_english', TRUE),
    ('should', 'common_english', TRUE),
    ('could', 'common_english', TRUE),
    ('may', 'common_english', TRUE),
    ('might', 'common_english', TRUE),
    ('must', 'common_english', TRUE),
    ('can', 'common_english', TRUE),

    -- Other common words
    ('not', 'common_english', TRUE),
    ('no', 'common_english', TRUE),
    ('yes', 'common_english', TRUE),
    ('all', 'common_english', TRUE),
    ('some', 'common_english', TRUE),
    ('any', 'common_english', TRUE),
    ('each', 'common_english', TRUE),
    ('every', 'common_english', TRUE),
    ('both', 'common_english', TRUE),
    ('few', 'common_english', TRUE),
    ('many', 'common_english', TRUE),
    ('more', 'common_english', TRUE),
    ('most', 'common_english', TRUE),
    ('other', 'common_english', TRUE),
    ('such', 'common_english', TRUE),
    ('only', 'common_english', TRUE),
    ('own', 'common_english', TRUE),
    ('same', 'common_english', TRUE),
    ('than', 'common_english', TRUE),
    ('then', 'common_english', TRUE),
    ('very', 'common_english', TRUE),
    ('when', 'common_english', TRUE),
    ('where', 'common_english', TRUE),
    ('who', 'common_english', TRUE),
    ('which', 'common_english', TRUE),
    ('what', 'common_english', TRUE),
    ('how', 'common_english', TRUE),
    ('why', 'common_english', TRUE)
ON CONFLICT (term) DO NOTHING;

-- Medical domain stop words (optional)
INSERT INTO stop_words (term, category, is_active) VALUES
    ('patient', 'domain', TRUE),
    ('study', 'domain', TRUE),
    ('image', 'domain', TRUE),
    ('report', 'domain', TRUE),
    ('findings', 'domain', TRUE),
    ('impression', 'domain', TRUE),
    ('technique', 'domain', TRUE),
    ('indication', 'domain', TRUE)
ON CONFLICT (term) DO NOTHING;

-- ---------------------------------------------------------------------
-- Seed: Default Profiles
-- ---------------------------------------------------------------------

-- LIDC-IDRI Standard Profile
INSERT INTO profiles (
    profile_name,
    file_type,
    description,
    mapping_definition,
    validation_rules,
    is_active,
    is_default
) VALUES (
    'lidc_idri_standard',
    'XML',
    'Standard LIDC-IDRI XML format with ResponseHeader and unblindedReadNodule structure',
    jsonb_build_object(
        'header_path', '/ResponseHeader',
        'study_uid_path', '/ResponseHeader/StudyInstanceUID',
        'series_uid_path', '/ResponseHeader/SeriesInstanceUID',
        'modality_path', '/ResponseHeader/Modality',
        'nodule_path', '/ResponseHeader/readingSession/unblindedReadNodule',
        'characteristics_path', 'characteristics',
        'roi_path', 'roi'
    ),
    jsonb_build_object(
        'required_fields', jsonb_build_array('StudyInstanceUID', 'SeriesInstanceUID'),
        'required_elements', jsonb_build_array('ResponseHeader', 'readingSession')
    ),
    TRUE,
    TRUE
);

-- Generic XML Profile
INSERT INTO profiles (
    profile_name,
    file_type,
    description,
    mapping_definition,
    validation_rules,
    is_active,
    is_default
) VALUES (
    'generic_xml',
    'XML',
    'Generic XML parser for unstructured medical imaging data',
    jsonb_build_object(
        'flexible_parsing', TRUE,
        'extract_all_attributes', TRUE
    ),
    jsonb_build_object(
        'required_fields', jsonb_build_array()
    ),
    TRUE,
    FALSE
);

-- CSV Profile
INSERT INTO profiles (
    profile_name,
    file_type,
    description,
    mapping_definition,
    validation_rules,
    is_active,
    is_default
) VALUES (
    'generic_csv',
    'CSV',
    'Generic CSV parser with automatic column detection',
    jsonb_build_object(
        'header_detection', 'auto',
        'delimiter', ',',
        'encoding', 'utf-8'
    ),
    jsonb_build_object(
        'min_columns', 1
    ),
    TRUE,
    TRUE
);

-- JSON Profile
INSERT INTO profiles (
    profile_name,
    file_type,
    description,
    mapping_definition,
    validation_rules,
    is_active,
    is_default
) VALUES (
    'generic_json',
    'JSON',
    'Generic JSON parser for flexible document structures',
    jsonb_build_object(
        'flexible_parsing', TRUE,
        'extract_nested', TRUE
    ),
    jsonb_build_object(
        'valid_json_required', TRUE
    ),
    TRUE,
    TRUE
);

-- ---------------------------------------------------------------------
-- Seed: Parse Cases
-- ---------------------------------------------------------------------

-- LIDC Single Session
INSERT INTO parse_cases (
    name,
    description,
    format_type,
    detection_criteria,
    field_mappings,
    detection_priority,
    requires_header,
    requires_modality,
    is_active
) VALUES (
    'LIDC_Single_Session',
    'LIDC-IDRI format with single reading session',
    'XML',
    jsonb_build_object(
        'required_elements', jsonb_build_array('ResponseHeader', 'readingSession', 'unblindedReadNodule'),
        'max_reading_sessions', 1
    ),
    jsonb_build_object(
        'study_uid', '/ResponseHeader/StudyInstanceUID',
        'series_uid', '/ResponseHeader/SeriesInstanceUID',
        'nodule_id', '/ResponseHeader/readingSession/noduleID'
    ),
    90,
    TRUE,
    TRUE,
    TRUE
);

-- LIDC Multi Session 4
INSERT INTO parse_cases (
    name,
    description,
    format_type,
    detection_criteria,
    field_mappings,
    detection_priority,
    requires_header,
    requires_modality,
    is_active
) VALUES (
    'LIDC_Multi_Session_4',
    'LIDC-IDRI format with 4 radiologist reading sessions',
    'XML',
    jsonb_build_object(
        'required_elements', jsonb_build_array('ResponseHeader', 'readingSession', 'unblindedReadNodule'),
        'reading_session_count', 4
    ),
    jsonb_build_object(
        'study_uid', '/ResponseHeader/StudyInstanceUID',
        'series_uid', '/ResponseHeader/SeriesInstanceUID'
    ),
    95,
    TRUE,
    TRUE,
    TRUE
);

-- Complete Attributes
INSERT INTO parse_cases (
    name,
    description,
    format_type,
    detection_criteria,
    field_mappings,
    detection_priority,
    requires_header,
    requires_modality,
    is_active
) VALUES (
    'Complete_Attributes',
    'Full radiologist annotations with all characteristics',
    'XML',
    jsonb_build_object(
        'required_characteristics', jsonb_build_array('subtlety', 'internalStructure', 'calcification', 'sphericity', 'margin', 'lobulation', 'spiculation', 'texture', 'malignancy')
    ),
    jsonb_build_object(
        'study_uid', '/ResponseHeader/StudyInstanceUID',
        'characteristics', '/ResponseHeader/readingSession/unblindedReadNodule/characteristics'
    ),
    85,
    TRUE,
    TRUE,
    TRUE
);

-- Core Attributes Only
INSERT INTO parse_cases (
    name,
    description,
    format_type,
    detection_criteria,
    field_mappings,
    detection_priority,
    requires_header,
    requires_modality,
    is_active
) VALUES (
    'Core_Attributes_Only',
    'Minimal annotations with only essential characteristics',
    'XML',
    jsonb_build_object(
        'required_characteristics', jsonb_build_array('subtlety', 'malignancy'),
        'max_characteristics', 3
    ),
    jsonb_build_object(
        'study_uid', '/ResponseHeader/StudyInstanceUID'
    ),
    70,
    TRUE,
    FALSE,
    TRUE
);

-- Generic CSV Case
INSERT INTO parse_cases (
    name,
    description,
    format_type,
    detection_criteria,
    field_mappings,
    detection_priority,
    requires_header,
    requires_modality,
    is_active
) VALUES (
    'Generic_CSV_Tabular',
    'Generic CSV file with tabular data',
    'CSV',
    jsonb_build_object(
        'min_columns', 2,
        'min_rows', 1
    ),
    jsonb_build_object(
        'flexible_mapping', TRUE
    ),
    50,
    FALSE,
    FALSE,
    TRUE
);

-- ---------------------------------------------------------------------
-- Seed: Sample Keywords (Medical Imaging)
-- ---------------------------------------------------------------------
INSERT INTO keywords (keyword_text, normalized_form, category, is_standard, vocabulary_source, definition) VALUES
    ('nodule', 'nodule', 'finding', TRUE, 'RadLex', 'A small rounded mass of distinct cells or tissue'),
    ('opacity', 'opacity', 'finding', TRUE, 'RadLex', 'Area of increased density on radiographic image'),
    ('ground glass opacity', 'ground_glass_opacity', 'finding', TRUE, 'RadLex', 'Hazy increased opacity with preserved bronchial and vascular markings'),
    ('malignancy', 'malignancy', 'diagnosis', TRUE, 'SNOMED CT', 'Cancerous growth or tumor'),
    ('benign', 'benign', 'diagnosis', TRUE, 'SNOMED CT', 'Non-cancerous growth'),
    ('lung', 'lung', 'anatomy', TRUE, 'RadLex', 'Primary respiratory organ'),
    ('pleura', 'pleura', 'anatomy', TRUE, 'RadLex', 'Membrane surrounding the lungs'),
    ('calcification', 'calcification', 'finding', TRUE, 'RadLex', 'Deposition of calcium salts in tissue'),
    ('spiculation', 'spiculation', 'finding', TRUE, 'RadLex', 'Spiky or star-shaped margin pattern'),
    ('lobulation', 'lobulation', 'finding', TRUE, 'RadLex', 'Rounded, undulating margin pattern'),
    ('subtlety', 'subtlety', 'characteristic', FALSE, 'LIDC', 'Difficulty of detection (1-5 scale)'),
    ('malignancy', 'malignancy_score', 'characteristic', FALSE, 'LIDC', 'Likelihood of malignancy (1-5 scale)'),
    ('texture', 'texture', 'characteristic', TRUE, 'RadLex', 'Surface characteristic of lesion'),
    ('margin', 'margin', 'characteristic', TRUE, 'RadLex', 'Border definition of lesion'),
    ('sphericity', 'sphericity', 'characteristic', FALSE, 'LIDC', 'Three-dimensional shape roundness'),
    ('roi', 'roi', 'technical', TRUE, 'DICOM', 'Region of interest'),
    ('dicom', 'dicom', 'technical', TRUE, 'DICOM', 'Digital Imaging and Communications in Medicine standard'),
    ('ct', 'ct', 'modality', TRUE, 'RadLex', 'Computed Tomography'),
    ('mri', 'mri', 'modality', TRUE, 'RadLex', 'Magnetic Resonance Imaging'),
    ('pet', 'pet', 'modality', TRUE, 'RadLex', 'Positron Emission Tomography')
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------
-- Seed: Sample Keyword Synonyms
-- ---------------------------------------------------------------------
INSERT INTO keyword_synonyms (canonical_keyword_id, synonym_text, synonym_type, confidence) VALUES
    ((SELECT keyword_id FROM keywords WHERE keyword_text = 'nodule'), 'lesion', 'alternate', 0.85),
    ((SELECT keyword_id FROM keywords WHERE keyword_text = 'nodule'), 'mass', 'alternate', 0.75),
    ((SELECT keyword_id FROM keywords WHERE keyword_text = 'opacity'), 'density', 'alternate', 0.90),
    ((SELECT keyword_id FROM keywords WHERE keyword_text = 'malignancy'), 'cancer', 'alternate', 0.95),
    ((SELECT keyword_id FROM keywords WHERE keyword_text = 'benign'), 'non-cancerous', 'alternate', 1.00),
    ((SELECT keyword_id FROM keywords WHERE keyword_text = 'lung'), 'pulmonary', 'alternate', 0.95),
    ((SELECT keyword_id FROM keywords WHERE keyword_text = 'ct'), 'computed tomography', 'expansion', 1.00),
    ((SELECT keyword_id FROM keywords WHERE keyword_text = 'mri'), 'magnetic resonance imaging', 'expansion', 1.00),
    ((SELECT keyword_id FROM keywords WHERE keyword_text = 'pet'), 'positron emission tomography', 'expansion', 1.00),
    ((SELECT keyword_id FROM keywords WHERE keyword_text = 'roi'), 'region of interest', 'expansion', 1.00)
ON CONFLICT DO NOTHING;

-- =====================================================================
-- Update schema version
-- =====================================================================
INSERT INTO schema_versions (version, description)
VALUES (10, 'Seed data: stop words, default profiles, parse cases, and sample keywords');

-- =====================================================================
-- Verification Query
-- =====================================================================
-- Run this to verify seed data is loaded:
-- SELECT COUNT(*) FROM stop_words;
-- SELECT COUNT(*) FROM profiles;
-- SELECT COUNT(*) FROM parse_cases;
-- SELECT COUNT(*) FROM keywords;
-- SELECT COUNT(*) FROM keyword_synonyms;

-- =====================================================================
-- END OF MIGRATION 010
-- =====================================================================
