/**
 * Cross-Content Query Interface
 * Unified queries across all segment types and content forms
 */

/**
 * Query builder for cross-content searches
 */
export class CrossContentQueryBuilder {
  constructor(private dbClient: SupabaseClient) {}

  /**
   * Find keywords appearing in both quantitative and qualitative contexts
   * These are high-signal keywords that bridge data and narrative
   */
  async findCrossTypeKeywords(options: {
    minRelevanceScore?: number;
    minFileCount?: number;
    limit?: number;
  } = {}): Promise<any[]> {
    const {
      minRelevanceScore = 0,
      minFileCount = 1,
      limit = 100
    } = options;

    const { data, error } = await this.dbClient
      .from('cross_type_keywords')
      .select('*')
      .gte('relevance_score', minRelevanceScore)
      .gte('file_count', minFileCount)
      .order('relevance_score', { ascending: false })
      .limit(limit);

    if (error) throw error;
    return data;
  }

  /**
   * Get all contexts for a specific keyword across all segment types
   */
  async getKeywordContexts(keywordTerm: string): Promise<any[]> {
    const { data, error } = await this.dbClient
      .rpc('get_keyword_contexts', { keyword_term: keywordTerm });

    if (error) throw error;
    return data;
  }

  /**
   * Find all numeric values associated with a keyword
   */
  async getKeywordNumericAssociations(keywordTerm: string): Promise<any[]> {
    const normalized = keywordTerm.toLowerCase().trim();

    const { data, error } = await this.dbClient
      .from('keyword_numeric_associations')
      .select('*')
      .eq('term', keywordTerm);

    if (error) throw error;
    return data;
  }

  /**
   * Find files containing all specified keywords
   */
  async findFilesWithKeywords(keywordTerms: string[]): Promise<any[]> {
    const { data, error } = await this.dbClient
      .rpc('find_files_with_keywords', { keyword_terms: keywordTerms });

    if (error) throw error;
    return data;
  }

  /**
   * Compare keyword distributions across different file types or sources
   */
  async compareKeywordDistributions(options: {
    extension?: string;
    segmentType?: string;
    topN?: number;
  } = {}): Promise<any[]> {
    const { extension, segmentType, topN = 20 } = options;

    let query = this.dbClient
      .from('keyword_occurrences')
      .select(`
        keyword_id,
        extracted_keywords (term, normalized_term, relevance_score),
        segment_type,
        file_id,
        file_imports (filename, extension)
      `);

    if (extension) {
      query = query.eq('file_imports.extension', extension);
    }

    if (segmentType) {
      query = query.eq('segment_type', segmentType);
    }

    const { data, error } = await query;

    if (error) throw error;

    // Aggregate by keyword
    const distribution = new Map<string, {
      term: string;
      total_count: number;
      by_segment_type: Record<string, number>;
      by_extension: Record<string, number>;
      relevance_score: number;
    }>();

    for (const occurrence of data as any[]) {
      const keyword = occurrence.extracted_keywords;
      const key = keyword.normalized_term;

      if (!distribution.has(key)) {
        distribution.set(key, {
          term: keyword.term,
          total_count: 0,
          by_segment_type: {},
          by_extension: {},
          relevance_score: keyword.relevance_score || 0
        });
      }

      const entry = distribution.get(key)!;
      entry.total_count++;
      entry.by_segment_type[occurrence.segment_type] = (entry.by_segment_type[occurrence.segment_type] || 0) + 1;
      entry.by_extension[occurrence.file_imports.extension] = (entry.by_extension[occurrence.file_imports.extension] || 0) + 1;
    }

    // Convert to array and sort
    return Array.from(distribution.values())
      .sort((a, b) => b.total_count - a.total_count)
      .slice(0, topN);
  }

  /**
   * Get all segments containing a keyword pattern
   */
  async getSegmentsWithKeywords(
    keywordTerms: string[],
    segmentType?: 'quantitative' | 'qualitative' | 'mixed'
  ): Promise<any[]> {
    // Get keyword IDs
    const { data: keywords, error: keywordError } = await this.dbClient
      .from('extracted_keywords')
      .select('keyword_id, normalized_term')
      .in('normalized_term', keywordTerms.map(t => t.toLowerCase().trim()));

    if (keywordError) throw keywordError;

    const keywordIds = keywords.map(k => k.keyword_id);

    // Get occurrences
    let query = this.dbClient
      .from('keyword_occurrences')
      .select('segment_id, segment_type, file_id, surrounding_context, associated_values')
      .in('keyword_id', keywordIds);

    if (segmentType) {
      query = query.eq('segment_type', segmentType);
    }

    const { data, error } = await query;

    if (error) throw error;

    // Group by segment
    const segmentMap = new Map<string, any>();

    for (const occurrence of data) {
      const key = `${occurrence.segment_type}:${occurrence.segment_id}`;

      if (!segmentMap.has(key)) {
        segmentMap.set(key, {
          segment_id: occurrence.segment_id,
          segment_type: occurrence.segment_type,
          file_id: occurrence.file_id,
          matched_keywords: [],
          contexts: [],
          associated_values: []
        });
      }

      const entry = segmentMap.get(key)!;
      entry.contexts.push(occurrence.surrounding_context);

      if (occurrence.associated_values) {
        entry.associated_values.push(occurrence.associated_values);
      }
    }

    return Array.from(segmentMap.values());
  }

  /**
   * Search across all content types using full-text search
   */
  async fullTextSearch(searchTerm: string, options: {
    segmentTypes?: string[];
    limit?: number;
  } = {}): Promise<any[]> {
    const { segmentTypes, limit = 50 } = options;
    const results: any[] = [];

    // Search qualitative segments (has full-text index)
    if (!segmentTypes || segmentTypes.includes('qualitative')) {
      const { data: qualData, error: qualError } = await this.dbClient
        .from('qualitative_segments')
        .select('segment_id, file_id, text_content, segment_subtype, position_in_file')
        .textSearch('text_vector', searchTerm)
        .limit(limit);

      if (qualError) throw qualError;

      results.push(...qualData.map((d: any) => ({
        ...d,
        segment_type: 'qualitative',
        content: d.text_content
      })));
    }

    // Search other segment types using ILIKE (less efficient but works)
    if (!segmentTypes || segmentTypes.includes('quantitative')) {
      const { data: quantData, error: quantError } = await this.dbClient
        .from('quantitative_segments')
        .select('segment_id, file_id, data_structure, position_in_file')
        .ilike('data_structure', `%${searchTerm}%`)
        .limit(limit);

      if (quantError) throw quantError;

      results.push(...quantData.map((d: any) => ({
        ...d,
        segment_type: 'quantitative',
        content: d.data_structure
      })));
    }

    if (!segmentTypes || segmentTypes.includes('mixed')) {
      const { data: mixedData, error: mixedError } = await this.dbClient
        .from('mixed_segments')
        .select('segment_id, file_id, structure, text_elements, position_in_file')
        .ilike('text_elements', `%${searchTerm}%`)
        .limit(limit);

      if (mixedError) throw mixedError;

      results.push(...mixedData.map((d: any) => ({
        ...d,
        segment_type: 'mixed',
        content: d.structure
      })));
    }

    return results.slice(0, limit);
  }

  /**
   * Get keyword co-occurrence patterns (keywords that appear together)
   */
  async getKeywordCoOccurrences(
    keywordTerm: string,
    minCoOccurrenceCount: number = 2
  ): Promise<any[]> {
    const normalized = keywordTerm.toLowerCase().trim();

    // Get all segment IDs where this keyword appears
    const { data: targetOccurrences, error: targetError } = await this.dbClient
      .from('keyword_occurrences')
      .select('segment_id, segment_type')
      .eq('extracted_keywords.normalized_term', normalized)
      .select('*, extracted_keywords!inner(normalized_term)');

    if (targetError) throw targetError;

    const segmentIds = targetOccurrences.map(o => o.segment_id);

    // Find other keywords in those same segments
    const { data: coOccurrences, error: coError } = await this.dbClient
      .from('keyword_occurrences')
      .select(`
        keyword_id,
        segment_id,
        extracted_keywords (term, normalized_term, relevance_score)
      `)
      .in('segment_id', segmentIds);

    if (coError) throw coError;

    // Count co-occurrences
    const coOccurrenceMap = new Map<string, {
      term: string;
      normalized_term: string;
      count: number;
      relevance_score: number;
    }>();

    for (const occ of coOccurrences as any[]) {
      const keyword = occ.extracted_keywords;
      if (keyword.normalized_term === normalized) continue; // Skip the target keyword itself

      if (!coOccurrenceMap.has(keyword.normalized_term)) {
        coOccurrenceMap.set(keyword.normalized_term, {
          term: keyword.term,
          normalized_term: keyword.normalized_term,
          count: 0,
          relevance_score: keyword.relevance_score || 0
        });
      }

      coOccurrenceMap.get(keyword.normalized_term)!.count++;
    }

    // Filter by minimum count and sort
    return Array.from(coOccurrenceMap.values())
      .filter(entry => entry.count >= minCoOccurrenceCount)
      .sort((a, b) => b.count - a.count);
  }

  /**
   * Get statistics for a specific file's content
   */
  async getFileContentStats(fileId: string): Promise<any> {
    // Get segment counts by type
    const { data: quantSegs, error: quantError } = await this.dbClient
      .from('quantitative_segments')
      .select('segment_id', { count: 'exact', head: true })
      .eq('file_id', fileId);

    const { data: qualSegs, error: qualError } = await this.dbClient
      .from('qualitative_segments')
      .select('segment_id', { count: 'exact', head: true })
      .eq('file_id', fileId);

    const { data: mixedSegs, error: mixedError } = await this.dbClient
      .from('mixed_segments')
      .select('segment_id', { count: 'exact', head: true })
      .eq('file_id', fileId);

    // Get keyword count
    const { data: keywords, error: keywordError } = await this.dbClient
      .from('keyword_occurrences')
      .select('keyword_id', { count: 'exact', head: true })
      .eq('file_id', fileId);

    // Get file info
    const { data: fileInfo, error: fileError } = await this.dbClient
      .from('file_imports')
      .select('*')
      .eq('file_id', fileId)
      .single();

    if (fileError) throw fileError;

    return {
      file_info: fileInfo,
      segment_counts: {
        quantitative: quantSegs,
        qualitative: qualSegs,
        mixed: mixedSegs,
        total: (quantSegs || 0) + (qualSegs || 0) + (mixedSegs || 0)
      },
      unique_keyword_count: keywords || 0
    };
  }

  /**
   * Get top keywords by relevance across all files
   */
  async getTopKeywords(options: {
    limit?: number;
    minDocumentFrequency?: number;
    segmentType?: string;
  } = {}): Promise<any[]> {
    const { limit = 50, minDocumentFrequency = 1, segmentType } = options;

    let query = this.dbClient
      .from('extracted_keywords')
      .select('*')
      .gte('document_frequency', minDocumentFrequency)
      .order('relevance_score', { ascending: false })
      .limit(limit);

    const { data, error } = await query;

    if (error) throw error;

    // If filtering by segment type, need to check occurrences
    if (segmentType) {
      const filteredKeywords: any[] = [];

      for (const keyword of data) {
        const { data: occurrences, error: occError } = await this.dbClient
          .from('keyword_occurrences')
          .select('occurrence_id')
          .eq('keyword_id', keyword.keyword_id)
          .eq('segment_type', segmentType)
          .limit(1);

        if (occError) throw occError;

        if (occurrences.length > 0) {
          filteredKeywords.push(keyword);
        }
      }

      return filteredKeywords;
    }

    return data;
  }
}

// Type placeholder
interface SupabaseClient {
  from(table: string): any;
  rpc(functionName: string, params: any): any;
}
