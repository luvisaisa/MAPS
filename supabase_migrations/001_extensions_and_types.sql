-- =====================================================================
-- MAPS Supabase Migration 001: Extensions and Custom Types
-- =====================================================================
-- Purpose: Create foundational database extensions and ENUM types
-- Date: November 25, 2025
-- =====================================================================

-- ---------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------

-- UUID generation (required for all tables)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Trigram text matching for fuzzy search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Vector embeddings (optional - requires Pro tier or higher)
-- Uncomment if you have Pro/Team tier and want embedding support
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Full-text search language support
-- Already included in PostgreSQL, just confirming availability
-- CREATE EXTENSION IF NOT EXISTS unaccent;

-- ---------------------------------------------------------------------
-- Custom ENUM Types
-- ---------------------------------------------------------------------

-- File types supported by MAPS
CREATE TYPE file_type_enum AS ENUM (
    'XML',
    'JSON',
    'CSV',
    'PDF',
    'DOCX',
    'XLSX',
    'TXT',
    'OTHER'
);

-- Document processing status
CREATE TYPE document_status_enum AS ENUM (
    'pending',
    'processing',
    'completed',
    'failed',
    'archived'
);

-- Logging severity levels
CREATE TYPE log_level_enum AS ENUM (
    'DEBUG',
    'INFO',
    'WARNING',
    'ERROR',
    'CRITICAL'
);

-- Case assignment review status
CREATE TYPE review_status_enum AS ENUM (
    'pending',
    'assigned',
    'rejected',
    'merged'
);

-- Content segment types (schema-agnostic classification)
CREATE TYPE segment_type_enum AS ENUM (
    'quantitative',
    'qualitative',
    'mixed'
);

-- Case detection methods
CREATE TYPE detection_method_enum AS ENUM (
    'filename_regex',
    'keyword_signature',
    'content_analysis',
    'hybrid',
    'manual'
);

-- Qualitative text segment subtypes
CREATE TYPE qualitative_segment_subtype_enum AS ENUM (
    'abstract',
    'body',
    'caption',
    'annotation',
    'metadata',
    'header',
    'footer',
    'comment',
    'other'
);

-- Batch processing status
CREATE TYPE batch_status_enum AS ENUM (
    'pending',
    'in_progress',
    'completed',
    'failed',
    'cancelled'
);

-- =====================================================================
-- Verification Query
-- =====================================================================
-- Run this to verify extensions and types are created:
-- SELECT * FROM pg_extension WHERE extname IN ('uuid-ossp', 'pg_trgm');
-- SELECT typname FROM pg_type WHERE typtype = 'e' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');

-- =====================================================================
-- END OF MIGRATION 001
-- =====================================================================
