/**
 * Case Identification Logic
 * Detects emerging patterns and clusters keywords into "cases"
 */

import * as crypto from 'crypto';

/**
 * Case pattern detector
 */
export class CasePatternDetector {
  constructor(private dbClient: SupabaseClient) {}

  /**
   * Detect case patterns across all files
   */
  async detectPatterns(options: {
    minKeywordCount?: number;
    minCoOccurrenceThreshold?: number;
    minConfidenceScore?: number;
    requireCrossTypeValidation?: boolean;
  } = {}): Promise<any[]> {
    const {
      minKeywordCount = 3,
      minCoOccurrenceThreshold = 2,
      minConfidenceScore = 0.5,
      requireCrossTypeValidation = false
    } = options;

    // Step 1: Find keyword clusters (keywords that frequently co-occur)
    const clusters = await this.findKeywordClusters(minCoOccurrenceThreshold);

    // Step 2: Filter clusters by size
    const validClusters = clusters.filter(c => c.keywords.length >= minKeywordCount);

    // Step 3: Calculate confidence scores and validate
    const patterns: any[] = [];

    for (const cluster of validClusters) {
      const pattern = await this.createCasePattern(cluster, requireCrossTypeValidation);

      if (pattern && pattern.confidence_score >= minConfidenceScore) {
        patterns.push(pattern);
      }
    }

    // Step 4: Store patterns in database
    for (const pattern of patterns) {
      await this.storeCasePattern(pattern);
    }

    return patterns;
  }

  /**
   * Find clusters of keywords that frequently co-occur
   */
  private async findKeywordClusters(minCoOccurrence: number): Promise<any[]> {
    // Get all keyword occurrences grouped by segment
    const { data: occurrences, error } = await this.dbClient
      .from('keyword_occurrences')
      .select(`
        segment_id,
        segment_type,
        file_id,
        keyword_id,
        extracted_keywords (term, normalized_term, relevance_score)
      `);

    if (error) throw error;

    // Group by segment
    const segmentMap = new Map<string, {
      segment_id: string;
      segment_type: string;
      file_id: string;
      keywords: Array<{ keyword_id: string; term: string; normalized_term: string; relevance_score: number }>;
    }>();

    for (const occ of occurrences) {
      const key = `${occ.segment_type}:${occ.segment_id}`;

      if (!segmentMap.has(key)) {
        segmentMap.set(key, {
          segment_id: occ.segment_id,
          segment_type: occ.segment_type,
          file_id: occ.file_id,
          keywords: []
        });
      }

      segmentMap.get(key)!.keywords.push({
        keyword_id: occ.keyword_id,
        term: occ.extracted_keywords.term,
        normalized_term: occ.extracted_keywords.normalized_term,
        relevance_score: occ.extracted_keywords.relevance_score || 0
      });
    }

    // Build co-occurrence matrix
    const coOccurrenceMatrix = new Map<string, Map<string, number>>();

    for (const segment of segmentMap.values()) {
      const keywords = segment.keywords;

      // For each pair of keywords in this segment
      for (let i = 0; i < keywords.length; i++) {
        for (let j = i + 1; j < keywords.length; j++) {
          const kw1 = keywords[i].keyword_id;
          const kw2 = keywords[j].keyword_id;

          // Ensure consistent ordering
          const [key1, key2] = kw1 < kw2 ? [kw1, kw2] : [kw2, kw1];

          if (!coOccurrenceMatrix.has(key1)) {
            coOccurrenceMatrix.set(key1, new Map());
          }

          const innerMap = coOccurrenceMatrix.get(key1)!;
          innerMap.set(key2, (innerMap.get(key2) || 0) + 1);
        }
      }
    }

    // Extract clusters using simple connected components
    const clusters = this.extractClusters(coOccurrenceMatrix, minCoOccurrence, occurrences);

    return clusters;
  }

  /**
   * Extract connected components as clusters
   */
  private extractClusters(
    coOccurrenceMatrix: Map<string, Map<string, number>>,
    minCoOccurrence: number,
    allOccurrences: any[]
  ): any[] {
    // Build adjacency list of keywords that co-occur >= minCoOccurrence times
    const adjacency = new Map<string, Set<string>>();

    for (const [kw1, innerMap] of coOccurrenceMatrix.entries()) {
      for (const [kw2, count] of innerMap.entries()) {
        if (count >= minCoOccurrence) {
          if (!adjacency.has(kw1)) adjacency.set(kw1, new Set());
          if (!adjacency.has(kw2)) adjacency.set(kw2, new Set());

          adjacency.get(kw1)!.add(kw2);
          adjacency.get(kw2)!.add(kw1);
        }
      }
    }

    // Find connected components (clusters)
    const visited = new Set<string>();
    const clusters: any[] = [];

    for (const keywordId of adjacency.keys()) {
      if (visited.has(keywordId)) continue;

      // BFS to find connected component
      const cluster: string[] = [];
      const queue: string[] = [keywordId];
      visited.add(keywordId);

      while (queue.length > 0) {
        const current = queue.shift()!;
        cluster.push(current);

        const neighbors = adjacency.get(current) || new Set();
        for (const neighbor of neighbors) {
          if (!visited.has(neighbor)) {
            visited.add(neighbor);
            queue.push(neighbor);
          }
        }
      }

      // Get keyword details for this cluster
      const keywordDetails = allOccurrences
        .filter(occ => cluster.includes(occ.keyword_id))
        .map(occ => ({
          keyword_id: occ.keyword_id,
          term: occ.extracted_keywords.term,
          normalized_term: occ.extracted_keywords.normalized_term,
          relevance_score: occ.extracted_keywords.relevance_score || 0
        }));

      // Remove duplicates
      const uniqueKeywords = Array.from(
        new Map(keywordDetails.map(k => [k.keyword_id, k])).values()
      );

      clusters.push({
        keywords: uniqueKeywords,
        size: uniqueKeywords.length
      });
    }

    return clusters;
  }

  /**
   * Create a case pattern from a keyword cluster
   */
  private async createCasePattern(
    cluster: any,
    requireCrossTypeValidation: boolean
  ): Promise<any | null> {
    const keywordIds = cluster.keywords.map((k: any) => k.keyword_id);

    // Get all segments containing these keywords
    const { data: occurrences, error } = await this.dbClient
      .from('keyword_occurrences')
      .select('segment_id, segment_type, file_id')
      .in('keyword_id', keywordIds);

    if (error) throw error;

    // Group by segment
    const segmentCounts = new Map<string, number>();
    const segmentDetails: Array<{ segment_id: string; segment_type: string; file_id: string }> = [];

    for (const occ of occurrences) {
      const key = `${occ.segment_type}:${occ.segment_id}`;
      segmentCounts.set(key, (segmentCounts.get(key) || 0) + 1);

      if (!segmentDetails.find(s => s.segment_id === occ.segment_id)) {
        segmentDetails.push({
          segment_id: occ.segment_id,
          segment_type: occ.segment_type,
          file_id: occ.file_id
        });
      }
    }

    // Check if pattern appears in multiple segment types
    const segmentTypes = new Set(segmentDetails.map(s => s.segment_type));
    const crossTypeValidated = segmentTypes.has('quantitative') && segmentTypes.has('qualitative');

    if (requireCrossTypeValidation && !crossTypeValidated) {
      return null;
    }

    // Calculate confidence score
    const confidenceScore = this.calculateConfidenceScore(cluster, segmentDetails, crossTypeValidated);

    // Generate pattern signature (for deduplication)
    const sortedKeywordIds = keywordIds.sort();
    const signature = crypto.createHash('sha256').update(sortedKeywordIds.join(',')).digest('hex');

    // Get unique files
    const uniqueFiles = new Set(segmentDetails.map(s => s.file_id));

    return {
      pattern_signature: signature,
      keywords: cluster.keywords.map((k: any) => ({
        keyword_id: k.keyword_id,
        term: k.term,
        frequency: occurrences.filter((o: any) => o.keyword_id === k.keyword_id).length
      })),
      source_segments: segmentDetails,
      confidence_score: confidenceScore,
      cross_type_validated: crossTypeValidated,
      keyword_count: cluster.keywords.length,
      segment_count: segmentDetails.length,
      file_count: uniqueFiles.size
    };
  }

  /**
   * Calculate confidence score for a case pattern
   */
  private calculateConfidenceScore(
    cluster: any,
    segmentDetails: any[],
    crossTypeValidated: boolean
  ): number {
    let score = 0;

    // Factor 1: Number of keywords in cluster (more = higher confidence)
    const keywordFactor = Math.min(cluster.keywords.length / 10, 1.0) * 0.3;
    score += keywordFactor;

    // Factor 2: Number of segments (more occurrences = higher confidence)
    const segmentFactor = Math.min(segmentDetails.length / 20, 1.0) * 0.2;
    score += segmentFactor;

    // Factor 3: Cross-type validation (big boost if validated)
    const crossTypeFactor = crossTypeValidated ? 0.3 : 0.0;
    score += crossTypeFactor;

    // Factor 4: Average relevance score of keywords
    const avgRelevance = cluster.keywords.reduce((sum: number, k: any) => sum + (k.relevance_score || 0), 0) / cluster.keywords.length;
    const relevanceFactor = Math.min(avgRelevance / 100, 1.0) * 0.2;
    score += relevanceFactor;

    return Math.min(score, 1.0);
  }

  /**
   * Store case pattern in database
   */
  private async storeCasePattern(pattern: any): Promise<void> {
    // Check if pattern already exists
    const { data: existing, error: existError } = await this.dbClient
      .from('case_patterns')
      .select('case_id')
      .eq('pattern_signature', pattern.pattern_signature)
      .single();

    if (existError && existError.code !== 'PGRST116') {
      // PGRST116 = no rows returned
      throw existError;
    }

    if (existing) {
      // Update existing pattern
      await this.dbClient
        .from('case_patterns')
        .update({
          keywords: pattern.keywords,
          source_segments: pattern.source_segments,
          confidence_score: pattern.confidence_score,
          cross_type_validated: pattern.cross_type_validated,
          keyword_count: pattern.keyword_count,
          segment_count: pattern.segment_count,
          file_count: pattern.file_count,
          last_updated_timestamp: new Date().toISOString()
        })
        .eq('case_id', existing.case_id);
    } else {
      // Insert new pattern
      await this.dbClient
        .from('case_patterns')
        .insert({
          pattern_signature: pattern.pattern_signature,
          keywords: pattern.keywords,
          source_segments: pattern.source_segments,
          confidence_score: pattern.confidence_score,
          cross_type_validated: pattern.cross_type_validated,
          keyword_count: pattern.keyword_count,
          segment_count: pattern.segment_count,
          file_count: pattern.file_count
        });
    }
  }

  /**
   * Get all detected case patterns
   */
  async getCasePatterns(options: {
    minConfidenceScore?: number;
    crossTypeValidatedOnly?: boolean;
    limit?: number;
  } = {}): Promise<any[]> {
    const {
      minConfidenceScore = 0,
      crossTypeValidatedOnly = false,
      limit = 100
    } = options;

    let query = this.dbClient
      .from('case_patterns')
      .select('*')
      .gte('confidence_score', minConfidenceScore)
      .order('confidence_score', { ascending: false })
      .limit(limit);

    if (crossTypeValidatedOnly) {
      query = query.eq('cross_type_validated', true);
    }

    const { data, error } = await query;

    if (error) throw error;
    return data;
  }

  /**
   * Get case pattern details by ID
   */
  async getCasePatternDetails(caseId: string): Promise<any> {
    const { data, error } = await this.dbClient
      .from('case_patterns')
      .select('*')
      .eq('case_id', caseId)
      .single();

    if (error) throw error;

    // Get additional details for each keyword
    const keywordIds = data.keywords.map((k: any) => k.keyword_id);

    const { data: keywordDetails, error: keywordError } = await this.dbClient
      .from('extracted_keywords')
      .select('*')
      .in('keyword_id', keywordIds);

    if (keywordError) throw keywordError;

    // Enrich pattern data
    return {
      ...data,
      keyword_details: keywordDetails
    };
  }

  /**
   * Find similar case patterns based on keyword overlap
   */
  async findSimilarPatterns(caseId: string, minOverlapRatio: number = 0.5): Promise<any[]> {
    // Get target pattern
    const { data: targetPattern, error: targetError } = await this.dbClient
      .from('case_patterns')
      .select('*')
      .eq('case_id', caseId)
      .single();

    if (targetError) throw targetError;

    const targetKeywordIds = new Set(targetPattern.keywords.map((k: any) => k.keyword_id));

    // Get all other patterns
    const { data: allPatterns, error: allError } = await this.dbClient
      .from('case_patterns')
      .select('*')
      .neq('case_id', caseId);

    if (allError) throw allError;

    // Calculate overlap and filter
    const similarPatterns = allPatterns
      .map((pattern: any) => {
        const patternKeywordIds = new Set(pattern.keywords.map((k: any) => k.keyword_id));
        const intersection = new Set([...targetKeywordIds].filter(x => patternKeywordIds.has(x)));
        const union = new Set([...targetKeywordIds, ...patternKeywordIds]);

        const overlapRatio = intersection.size / union.size;

        return {
          ...pattern,
          overlap_ratio: overlapRatio,
          shared_keywords: Array.from(intersection)
        };
      })
      .filter((p: any) => p.overlap_ratio >= minOverlapRatio)
      .sort((a: any, b: any) => b.overlap_ratio - a.overlap_ratio);

    return similarPatterns;
  }
}

// Type placeholder
interface SupabaseClient {
  from(table: string): any;
}
