/**
 * Stop Word Filtering and Keyword Relevance Scoring
 * Intelligently filters noise and scores keyword importance
 */

import { RelevanceFactors } from './types';

/**
 * Stop word filter with configurable categories
 */
export class StopWordFilter {
  private stopWords: Set<string> = new Set();
  private dbClient: SupabaseClient;

  constructor(dbClient: SupabaseClient) {
    this.dbClient = dbClient;
  }

  /**
   * Load stop words from database
   */
  async loadStopWords(): Promise<void> {
    const { data, error } = await this.dbClient
      .from('stop_words')
      .select('normalized_term')
      .eq('active', true);

    if (error) throw error;

    this.stopWords = new Set(data.map((row: any) => row.normalized_term));
  }

  /**
   * Check if a term should be filtered out
   */
  shouldFilter(term: string): boolean {
    const normalized = this.normalizeTerm(term);

    // Filter stop words
    if (this.stopWords.has(normalized)) return true;

    // Filter single characters (unless meaningful codes like "X" or "A")
    if (normalized.length === 1 && !/^[a-z]$/i.test(normalized)) return true;

    // Filter pure numbers (unless part of meaningful code like "365")
    if (/^\d+$/.test(normalized) && normalized.length < 3) return true;

    // Filter very short terms (< 2 chars)
    if (normalized.length < 2) return true;

    // Filter structural noise
    if (['null', 'undefined', 'n/a', 'na', 'nan'].includes(normalized)) return true;

    return false;
  }

  /**
   * Preserve technical terms that might otherwise be filtered
   */
  shouldPreserve(term: string): boolean {
    // Acronyms (all caps, 2-6 letters)
    if (/^[A-Z]{2,6}$/.test(term)) return true;

    // Technical codes (alphanumeric patterns)
    if (/^[A-Z]\d+[A-Z]?$/i.test(term)) return true; // e.g., B2B, P90, T1

    // Proper nouns (capitalized words in prose context)
    if (/^[A-Z][a-z]+$/.test(term) && term.length > 3) return true;

    // Domain-specific patterns (e.g., "24/7", "COVID-19")
    if (/\d+\/\d+/.test(term) || /[A-Z]+-\d+/.test(term)) return true;

    return false;
  }

  /**
   * Normalize term for comparison
   */
  normalizeTerm(term: string): string {
    return term.toLowerCase().trim().replace(/[^\w\s-]/g, '');
  }

  /**
   * Add custom stop words
   */
  async addStopWords(terms: string[], category: string = 'custom'): Promise<void> {
    const records = terms.map(term => ({
      term,
      normalized_term: this.normalizeTerm(term),
      category,
      active: true
    }));

    const { error } = await this.dbClient
      .from('stop_words')
      .upsert(records, { onConflict: 'term' });

    if (error) throw error;

    // Reload stop words
    await this.loadStopWords();
  }
}

/**
 * Keyword relevance scoring engine
 */
export class RelevanceScorer {
  private totalDocuments: number = 0;
  private dbClient: SupabaseClient;

  constructor(dbClient: SupabaseClient) {
    this.dbClient = dbClient;
  }

  /**
   * Calculate relevance score for a keyword
   * Score = TF * IDF * position_weight * cross_type_bonus * numeric_association_weight
   */
  async calculateRelevanceScore(
    keywordId: string,
    termFrequency: number,
    documentFrequency: number,
    occurrences: Array<{
      segment_type: string;
      position_weight: number;
      has_numeric_associations: boolean;
    }>
  ): Promise<number> {
    // Get total document count
    if (this.totalDocuments === 0) {
      await this.updateTotalDocuments();
    }

    // Calculate TF-IDF
    const tf = termFrequency;
    const idf = this.calculateIDF(documentFrequency);

    // Calculate position weight (average across occurrences)
    const avgPositionWeight = occurrences.reduce((sum, occ) => sum + occ.position_weight, 0) / occurrences.length;

    // Calculate cross-type bonus (appears in multiple segment types)
    const crossTypeBonus = this.calculateCrossTypeBonus(occurrences);

    // Calculate numeric association weight (frequently near significant numbers)
    const numericAssociationWeight = this.calculateNumericAssociationWeight(occurrences);

    // Combined relevance score
    const relevanceScore = tf * idf * avgPositionWeight * crossTypeBonus * numericAssociationWeight;

    return Math.min(relevanceScore, 1000); // Cap at 1000 to prevent outliers
  }

  /**
   * Calculate inverse document frequency
   */
  private calculateIDF(documentFrequency: number): number {
    if (documentFrequency === 0 || this.totalDocuments === 0) return 0;
    return Math.log(this.totalDocuments / documentFrequency);
  }

  /**
   * Calculate cross-type bonus
   * Higher score if keyword appears in multiple content types
   */
  private calculateCrossTypeBonus(occurrences: Array<{ segment_type: string }>): number {
    const types = new Set(occurrences.map(o => o.segment_type));

    if (types.size === 3) {
      // Appears in all three types (quan, qual, mixed)
      return 2.0;
    } else if (types.size === 2) {
      // Appears in two types
      if (types.has('quantitative') && types.has('qualitative')) {
        // High signal: bridges quan and qual
        return 1.8;
      }
      return 1.5;
    } else {
      // Single type only
      return 1.0;
    }
  }

  /**
   * Calculate numeric association weight
   * Higher if keyword frequently appears near significant numbers
   */
  private calculateNumericAssociationWeight(
    occurrences: Array<{ has_numeric_associations: boolean }>
  ): number {
    const withNumericAssociations = occurrences.filter(o => o.has_numeric_associations).length;
    const ratio = withNumericAssociations / occurrences.length;

    // Scale from 1.0 (no associations) to 1.5 (all have associations)
    return 1.0 + (ratio * 0.5);
  }

  /**
   * Update total document count from database
   */
  private async updateTotalDocuments(): Promise<void> {
    const { count, error } = await this.dbClient
      .from('file_imports')
      .select('*', { count: 'exact', head: true })
      .eq('processing_status', 'complete');

    if (error) throw error;
    this.totalDocuments = count || 0;
  }

  /**
   * Calculate position weight based on location in document
   * Higher weight for keywords in headers, titles, first paragraphs
   */
  calculatePositionWeight(positionMetadata: Record<string, any>): number {
    let weight = 1.0;

    // Headers and titles
    if (positionMetadata.in_header || positionMetadata.in_title) {
      weight *= 2.0;
    }

    // First paragraph or section
    if (positionMetadata.paragraph_index === 0 || positionMetadata.section_index === 0) {
      weight *= 1.5;
    }

    // First page
    if (positionMetadata.page === 1) {
      weight *= 1.3;
    }

    // Abstract or summary sections
    if (positionMetadata.segment_subtype === 'abstract' || positionMetadata.segment_subtype === 'summary') {
      weight *= 1.8;
    }

    // Column headers in tables
    if (positionMetadata.is_column_header) {
      weight *= 1.7;
    }

    // XML/JSON attribute names or keys (structural keywords)
    if (positionMetadata.is_key || positionMetadata.is_attribute) {
      weight *= 1.6;
    }

    return Math.min(weight, 3.0); // Cap at 3.0
  }

  /**
   * Batch update relevance scores for all keywords
   */
  async updateAllRelevanceScores(): Promise<void> {
    // Get all keywords with their occurrences
    const { data: keywords, error: keywordError } = await this.dbClient
      .from('extracted_keywords')
      .select('keyword_id, total_frequency, document_frequency');

    if (keywordError) throw keywordError;

    for (const keyword of keywords) {
      // Get occurrences for this keyword
      const { data: occurrences, error: occError } = await this.dbClient
        .from('keyword_occurrences')
        .select('segment_type, position_weight, associated_values')
        .eq('keyword_id', keyword.keyword_id);

      if (occError) throw occError;

      const occurrenceData = occurrences.map((occ: any) => ({
        segment_type: occ.segment_type,
        position_weight: occ.position_weight || 1.0,
        has_numeric_associations: occ.associated_values !== null && Object.keys(occ.associated_values).length > 0
      }));

      // Calculate relevance score
      const score = await this.calculateRelevanceScore(
        keyword.keyword_id,
        keyword.total_frequency,
        keyword.document_frequency,
        occurrenceData
      );

      // Update keyword with new relevance score
      await this.dbClient
        .from('extracted_keywords')
        .update({ relevance_score: score })
        .eq('keyword_id', keyword.keyword_id);
    }
  }
}

/**
 * Combined filter and scorer for keyword extraction pipeline
 */
export class KeywordProcessor {
  private filter: StopWordFilter;
  private scorer: RelevanceScorer;

  constructor(dbClient: SupabaseClient) {
    this.filter = new StopWordFilter(dbClient);
    this.scorer = new RelevanceScorer(dbClient);
  }

  async initialize(): Promise<void> {
    await this.filter.loadStopWords();
  }

  /**
   * Process and validate a keyword candidate
   */
  shouldKeep(term: string): boolean {
    // Preserve important terms even if they might be filtered
    if (this.filter.shouldPreserve(term)) return true;

    // Filter stop words and noise
    if (this.filter.shouldFilter(term)) return false;

    return true;
  }

  /**
   * Calculate position weight for an occurrence
   */
  calculatePositionWeight(positionMetadata: Record<string, any>): number {
    return this.scorer.calculatePositionWeight(positionMetadata);
  }

  /**
   * Update relevance scores for all keywords
   */
  async updateRelevanceScores(): Promise<void> {
    await this.scorer.updateAllRelevanceScores();
  }

  /**
   * Get filter for direct access
   */
  getFilter(): StopWordFilter {
    return this.filter;
  }

  /**
   * Get scorer for direct access
   */
  getScorer(): RelevanceScorer {
    return this.scorer;
  }
}

// Type placeholder
interface SupabaseClient {
  from(table: string): any;
}
