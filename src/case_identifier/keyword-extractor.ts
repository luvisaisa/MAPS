/**
 * Keyword Extraction Engine
 * Extracts keywords from all segment types with context preservation
 */

import { SegmentType, ExtractedKeywordWithContext } from './types';
import { KeywordProcessor } from './keyword-relevance';

/**
 * Main keyword extraction engine
 */
export class KeywordExtractor {
  private processor: KeywordProcessor;
  private dbClient: SupabaseClient;

  constructor(dbClient: SupabaseClient, processor: KeywordProcessor) {
    this.dbClient = dbClient;
    this.processor = processor;
  }

  /**
   * Extract and store keywords from a segment
   */
  async extractAndStore(
    segment: any,
    segmentType: SegmentType,
    fileId: string
  ): Promise<void> {
    // Extract keywords based on segment type
    let keywords: ExtractedKeywordWithContext[];

    if (segmentType === 'quantitative') {
      keywords = await this.extractFromQuantitative(segment);
    } else if (segmentType === 'qualitative') {
      keywords = await this.extractFromQualitative(segment);
    } else {
      keywords = await this.extractFromMixed(segment);
    }

    // Store each keyword and its occurrences
    for (const keyword of keywords) {
      await this.storeKeywordWithOccurrences(keyword, segment.segment_id, segmentType, fileId);
    }
  }

  /**
   * Extract keywords from quantitative segments
   */
  private async extractFromQuantitative(segment: any): Promise<ExtractedKeywordWithContext[]> {
    const keywords: ExtractedKeywordWithContext[] = [];

    // Extract column headers / field names
    if (segment.column_mappings) {
      for (const columnName of Object.keys(segment.column_mappings)) {
        if (this.processor.shouldKeep(columnName)) {
          keywords.push({
            term: columnName,
            normalized_term: this.normalizeTerm(columnName),
            is_phrase: columnName.includes(' '),
            frequency: 1,
            contexts: [{
            surrounding_text: `Column: ${columnName}`,
            position: { ...segment.position_in_file, is_column_header: true },
            associated_numbers: this.extractNumbersFromColumn(segment.data_structure, columnName),
            position_weight: this.processor.calculatePositionWeight({ is_column_header: true })
            }]
          });
        }
      }
    }

    // Extract repeated categorical values (if text)
    const categoricalValues = this.findCategoricalValues(segment.data_structure);
    for (const [value, count] of Object.entries(categoricalValues)) {
      if (this.processor.shouldKeep(value)) {
        keywords.push({
          term: value,
          normalized_term: this.normalizeTerm(value),
          is_phrase: value.includes(' '),
          frequency: count,
          contexts: [{
            surrounding_text: `Categorical value in quantitative data`,
            position: segment.position_in_file,
            associated_numbers: [],
            position_weight: 1.0
          }]
        });
      }
    }

    // Extract enum-like patterns
    const enumPatterns = this.findEnumPatterns(segment.data_structure);
    for (const pattern of enumPatterns) {
      if (this.processor.shouldKeep(pattern)) {
        keywords.push({
          term: pattern,
          normalized_term: this.normalizeTerm(pattern),
          is_phrase: false,
          frequency: 1,
          contexts: [{
            surrounding_text: `Enum pattern in structured data`,
            position: segment.position_in_file,
            associated_numbers: [],
            position_weight: 1.2
          }]
        });
      }
    }

    return keywords;
  }

  /**
   * Extract keywords from qualitative segments
   */
  private async extractFromQualitative(segment: any): Promise<ExtractedKeywordWithContext[]> {
    const keywords: ExtractedKeywordWithContext[] = [];
    const text = segment.text_content;

    // N-gram extraction (1-3 words)
    const ngrams = this.extractNGrams(text, 1, 3);

    for (const [ngram, positions] of ngrams.entries()) {
      if (this.processor.shouldKeep(ngram)) {
        // Get surrounding context for first occurrence
        const contextWindow = this.getContextWindow(text, positions[0], 50);

        // Check if in special position (header, title, first paragraph, etc.)
        const positionWeight = this.processor.calculatePositionWeight({
          ...segment.position_in_file,
          segment_subtype: segment.segment_subtype
        });

        keywords.push({
          term: ngram,
          normalized_term: this.normalizeTerm(ngram),
          is_phrase: ngram.split(/\s+/).length > 1,
          frequency: positions.length,
          contexts: positions.map(pos => ({
            surrounding_text: this.getContextWindow(text, pos, 50),
            position: { ...segment.position_in_file, char_offset: pos },
            associated_numbers: this.extractNumbersFromContext(text, pos),
            position_weight: positionWeight
          }))
        });
      }
    }

    // Named entity recognition (simple: capitalized phrases, quoted terms)
    const namedEntities = this.extractNamedEntities(text);
    for (const entity of namedEntities) {
      if (this.processor.shouldKeep(entity.term) && !ngrams.has(entity.term)) {
        keywords.push({
          term: entity.term,
          normalized_term: this.normalizeTerm(entity.term),
          is_phrase: entity.term.split(/\s+/).length > 1,
          frequency: entity.frequency,
          contexts: [{
            surrounding_text: entity.context,
            position: { ...segment.position_in_file, entity_type: entity.type },
            associated_numbers: [],
            position_weight: 1.3 // Higher weight for named entities
          }]
        });
      }
    }

    return keywords;
  }

  /**
   * Extract keywords from mixed segments
   */
  private async extractFromMixed(segment: any): Promise<ExtractedKeywordWithContext[]> {
    const keywords: ExtractedKeywordWithContext[] = [];

    // Extract from text elements
    if (segment.text_elements) {
      for (const [key, textValue] of Object.entries(segment.text_elements)) {
        if (typeof textValue === 'string') {
          const textKeywords = await this.extractFromText(textValue, segment.position_in_file);
          keywords.push(...textKeywords);

          // Key itself might be a keyword
          if (this.processor.shouldKeep(key)) {
            keywords.push({
              term: key,
              normalized_term: this.normalizeTerm(key),
              is_phrase: key.includes(' '),
              frequency: 1,
              contexts: [{
                surrounding_text: `${key}: ${textValue.substring(0, 50)}...`,
                position: { ...segment.position_in_file, is_key: true },
                associated_numbers: this.extractNumbers(String(segment.numeric_elements?.[key] || '')),
                position_weight: 1.5
              }]
            });
          }
        }
      }
    }

    // Extract from numeric elements (field names)
    if (segment.numeric_elements) {
      for (const key of Object.keys(segment.numeric_elements)) {
        if (this.processor.shouldKeep(key)) {
          keywords.push({
            term: key,
            normalized_term: this.normalizeTerm(key),
            is_phrase: key.includes(' '),
            frequency: 1,
            contexts: [{
              surrounding_text: `${key}: ${segment.numeric_elements[key]}`,
              position: { ...segment.position_in_file, is_key: true },
              associated_numbers: [Number(segment.numeric_elements[key])].filter(n => !isNaN(n)),
              position_weight: 1.6 // Higher weight when associated with numbers
            }]
          });
        }
      }
    }

    return keywords;
  }

  /**
   * Helper: Extract keywords from plain text
   */
  private async extractFromText(
    text: string,
    basePosition: Record<string, any>
  ): Promise<ExtractedKeywordWithContext[]> {
    const keywords: ExtractedKeywordWithContext[] = [];
    const ngrams = this.extractNGrams(text, 1, 2);

    for (const [ngram, positions] of ngrams.entries()) {
      if (this.processor.shouldKeep(ngram)) {
        keywords.push({
          term: ngram,
          normalized_term: this.normalizeTerm(ngram),
          is_phrase: ngram.split(/\s+/).length > 1,
          frequency: positions.length,
          contexts: positions.map(pos => ({
            surrounding_text: this.getContextWindow(text, pos, 40),
            position: { ...basePosition, char_offset: pos },
            associated_numbers: this.extractNumbersFromContext(text, pos),
            position_weight: 1.0
          }))
        });
      }
    }

    return keywords;
  }

  /**
   * Extract N-grams from text
   */
  private extractNGrams(text: string, minN: number, maxN: number): Map<string, number[]> {
    const ngrams = new Map<string, number[]>();
    const words = text.split(/\s+/).filter(w => w.length > 0);

    for (let n = minN; n <= maxN; n++) {
      for (let i = 0; i <= words.length - n; i++) {
        const ngram = words.slice(i, i + n).join(' ');
        const position = text.indexOf(ngram);

        if (!ngrams.has(ngram)) {
          ngrams.set(ngram, []);
        }
        ngrams.get(ngram)!.push(position);
      }
    }

    return ngrams;
  }

  /**
   * Extract named entities (simple approach)
   */
  private extractNamedEntities(text: string): Array<{ term: string; type: string; frequency: number; context: string }> {
    const entities: Array<{ term: string; type: string; frequency: number; context: string }> = [];

    // Capitalized phrases (potential proper nouns)
    const capitalizedPhrases = text.match(/\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b/g) || [];
    for (const phrase of capitalizedPhrases) {
      const context = this.getContextWindow(text, text.indexOf(phrase), 50);
      entities.push({ term: phrase, type: 'proper_noun', frequency: 1, context });
    }

    // Quoted terms (important concepts)
    const quotedTerms = text.match(/"([^"]+)"/g) || [];
    for (const quoted of quotedTerms) {
      const term = quoted.replace(/"/g, '');
      const context = this.getContextWindow(text, text.indexOf(quoted), 50);
      entities.push({ term, type: 'quoted', frequency: 1, context });
    }

    return entities;
  }

  /**
   * Get text window around a position
   */
  private getContextWindow(text: string, position: number, windowSize: number): string {
    const start = Math.max(0, position - windowSize);
    const end = Math.min(text.length, position + windowSize);
    return text.substring(start, end);
  }

  /**
   * Extract numbers from context around position
   */
  private extractNumbersFromContext(text: string, position: number, windowSize: number = 100): number[] {
    const context = this.getContextWindow(text, position, windowSize);
    return this.extractNumbers(context);
  }

  /**
   * Extract numbers from text
   */
  private extractNumbers(text: string): number[] {
    const numbers: number[] = [];
    const matches = text.match(/\b\d+\.?\d*\b/g) || [];

    for (const match of matches) {
      const num = parseFloat(match);
      if (!isNaN(num)) {
        numbers.push(num);
      }
    }

    return numbers;
  }

  /**
   * Extract numbers from a specific column in structured data
   */
  private extractNumbersFromColumn(dataStructure: any, columnName: string): number[] {
    const numbers: number[] = [];

    if (Array.isArray(dataStructure)) {
      for (const row of dataStructure) {
        if (row[columnName] !== undefined) {
          const value = row[columnName];
          if (typeof value === 'number') {
            numbers.push(value);
          } else if (typeof value === 'string') {
            const num = parseFloat(value);
            if (!isNaN(num)) numbers.push(num);
          }
        }
      }
    } else if (typeof dataStructure === 'object' && dataStructure[columnName] !== undefined) {
      const value = dataStructure[columnName];
      if (typeof value === 'number') {
        numbers.push(value);
      }
    }

    return numbers.slice(0, 10); // Limit to first 10 for storage
  }

  /**
   * Find categorical values (repeated text values in structured data)
   */
  private findCategoricalValues(dataStructure: any): Record<string, number> {
    const valueCounts: Record<string, number> = {};

    const collectValues = (obj: any) => {
      if (typeof obj === 'string' && obj.length < 50 && !/^\d+$/.test(obj)) {
        valueCounts[obj] = (valueCounts[obj] || 0) + 1;
      } else if (Array.isArray(obj)) {
        obj.forEach(collectValues);
      } else if (typeof obj === 'object' && obj !== null) {
        Object.values(obj).forEach(collectValues);
      }
    };

    collectValues(dataStructure);

    // Only return values that appear multiple times
    return Object.fromEntries(
      Object.entries(valueCounts).filter(([_, count]) => count > 1)
    );
  }

  /**
   * Find enum-like patterns (consistent categorical values)
   */
  private findEnumPatterns(dataStructure: any): string[] {
    const categoricalValues = this.findCategoricalValues(dataStructure);

    // Enum pattern: multiple occurrences, short values, consistent format
    return Object.entries(categoricalValues)
      .filter(([value, count]) => count >= 2 && value.length <= 20)
      .map(([value]) => value);
  }

  /**
   * Normalize term for storage
   */
  private normalizeTerm(term: string): string {
    return term.toLowerCase().trim().replace(/[^\w\s-]/g, '');
  }

  /**
   * Store keyword and its occurrences
   */
  private async storeKeywordWithOccurrences(
    keyword: ExtractedKeywordWithContext,
    segmentId: string,
    segmentType: SegmentType,
    fileId: string
  ): Promise<void> {
    // Upsert keyword
    const { data: keywordData, error: keywordError } = await this.dbClient
      .from('extracted_keywords')
      .upsert({
        term: keyword.term,
        normalized_term: keyword.normalized_term,
        is_phrase: keyword.is_phrase,
        total_frequency: keyword.frequency,
        document_frequency: 1
      }, {
        onConflict: 'normalized_term',
        ignoreDuplicates: false
      })
      .select('keyword_id')
      .single();

    if (keywordError) throw keywordError;

    const keywordId = keywordData.keyword_id;

    // Insert occurrences
    for (const context of keyword.contexts) {
      await this.dbClient
        .from('keyword_occurrences')
        .insert({
          keyword_id: keywordId,
          segment_id: segmentId,
          segment_type: segmentType,
          file_id: fileId,
          surrounding_context: context.surrounding_text,
          associated_values: context.associated_numbers.length > 0
            ? { numbers: context.associated_numbers }
            : null,
          position_metadata: context.position,
          position_weight: context.position_weight
        });
    }

    // Update keyword statistics
    await this.updateKeywordStats(keywordId);
  }

  /**
   * Update keyword statistics
   */
  private async updateKeywordStats(keywordId: string): Promise<void> {
    // Get total frequency across all occurrences
    const { data: occurrences, error: occError } = await this.dbClient
      .from('keyword_occurrences')
      .select('file_id')
      .eq('keyword_id', keywordId);

    if (occError) throw occError;

    const totalFrequency = occurrences.length;
    const uniqueFiles = new Set(occurrences.map(o => o.file_id));
    const documentFrequency = uniqueFiles.size;

    await this.dbClient
      .from('extracted_keywords')
      .update({
        total_frequency: totalFrequency,
        document_frequency: documentFrequency,
        last_seen_timestamp: new Date().toISOString()
      })
      .eq('keyword_id', keywordId);
  }
}

// Type placeholder
interface SupabaseClient {
  from(table: string): any;
}
