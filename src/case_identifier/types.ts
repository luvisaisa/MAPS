/**
 * Type definitions for the unified schema-agnostic case identifier system
 */

export type SegmentType = 'quantitative' | 'qualitative' | 'mixed';
export type ProcessingStatus = 'pending' | 'parsing' | 'analyzing' | 'extracting' | 'complete' | 'failed';
export type StopWordCategory = 'common_english' | 'academic' | 'structural' | 'domain_specific' | 'custom';

export interface FileImport {
  file_id: string;
  filename: string;
  extension: string;
  file_size_bytes: number;
  import_timestamp: Date;
  raw_content_hash: string;
  processing_status: ProcessingStatus;
  processing_error?: string;
  metadata: Record<string, any>;
}

export interface QuantitativeSegment {
  segment_id: string;
  file_id: string;
  data_structure: Record<string, any>;
  column_mappings?: Record<string, string>;
  row_count?: number;
  detected_schema?: Record<string, any>;
  numeric_density?: number;
  position_in_file: Record<string, any>;
  extraction_timestamp: Date;
}

export interface QualitativeSegment {
  segment_id: string;
  file_id: string;
  text_content: string;
  segment_subtype?: string;
  language_code: string;
  word_count?: number;
  sentence_count?: number;
  position_in_file: Record<string, any>;
  extraction_timestamp: Date;
}

export interface MixedSegment {
  segment_id: string;
  file_id: string;
  structure: Record<string, any>;
  text_elements?: Record<string, any>;
  numeric_elements?: Record<string, any>;
  quantitative_ratio: number;
  position_in_file: Record<string, any>;
  extraction_timestamp: Date;
}

export interface ExtractedKeyword {
  keyword_id: string;
  term: string;
  normalized_term: string;
  is_phrase: boolean;
  total_frequency: number;
  document_frequency: number;
  relevance_score: number;
  first_seen_timestamp: Date;
  last_seen_timestamp: Date;
}

export interface KeywordOccurrence {
  occurrence_id: string;
  keyword_id: string;
  segment_id: string;
  segment_type: SegmentType;
  file_id: string;
  surrounding_context?: string;
  associated_values?: Record<string, any>;
  position_metadata?: Record<string, any>;
  position_weight: number;
  occurrence_timestamp: Date;
}

export interface CasePattern {
  case_id: string;
  pattern_signature: string;
  keywords: Array<{ keyword_id: string; term: string; frequency: number }>;
  source_segments: Array<{ segment_id: string; segment_type: SegmentType; file_id: string }>;
  confidence_score: number;
  cross_type_validated: boolean;
  keyword_count: number;
  segment_count: number;
  file_count: number;
  detected_timestamp: Date;
  last_updated_timestamp: Date;
}

/**
 * Parsed element from any file format
 */
export interface ParsedElement {
  content: string | Record<string, any> | Array<any>;
  type: 'text' | 'table' | 'tree' | 'structured';
  position: {
    line_start?: number;
    line_end?: number;
    page?: number;
    sheet_name?: string;
    xpath?: string;
    paragraph_index?: number;
    [key: string]: any;
  };
  metadata: Record<string, any>;
}

/**
 * Content analysis result
 */
export interface ContentAnalysis {
  numeric_density: number; // 0.0 to 1.0
  text_density: number; // 0.0 to 1.0
  has_prose: boolean;
  has_structure: boolean;
  detected_language?: string;
  schema?: Record<string, string>;
  classification: SegmentType;
}

/**
 * Extracted keyword with context
 */
export interface ExtractedKeywordWithContext {
  term: string;
  normalized_term: string;
  is_phrase: boolean;
  frequency: number;
  contexts: Array<{
    surrounding_text: string;
    position: Record<string, any>;
    associated_numbers: number[];
    position_weight: number;
  }>;
}

/**
 * Relevance scoring factors
 */
export interface RelevanceFactors {
  tf: number; // Term frequency
  idf: number; // Inverse document frequency
  position_weight: number; // Higher for headers, titles
  cross_type_bonus: number; // Appears in both quan and qual
  numeric_association_weight: number; // Frequently near significant numbers
}
