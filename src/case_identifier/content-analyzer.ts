/**
 * Content Analyzer and Segment Classifier
 * Determines whether content is quantitative, qualitative, or mixed
 */

import { ParsedElement, ContentAnalysis, SegmentType } from './types';

/**
 * Analyzes content to determine its nature (quantitative vs qualitative)
 */
export class ContentAnalyzer {
  /**
   * Analyze a parsed element to determine its content characteristics
   */
  async analyze(element: ParsedElement): Promise<ContentAnalysis> {
    const numericDensity = this.calculateNumericDensity(element.content);
    const textDensity = this.calculateTextDensity(element.content);
    const hasProse = this.detectProse(element.content);
    const hasStructure = this.detectStructure(element.content);
    const detectedLanguage = this.detectLanguage(element.content);
    const schema = this.inferSchema(element.content);
    
    // Classify based on densities
    let classification: SegmentType;
    if (numericDensity >= 0.70) {
      classification = 'quantitative';
    } else if (numericDensity <= 0.30) {
      classification = 'qualitative';
    } else {
      classification = 'mixed';
    }
    
    return {
      numeric_density: numericDensity,
      text_density: textDensity,
      has_prose: hasProse,
      has_structure: hasStructure,
      detected_language: detectedLanguage,
      schema,
      classification
    };
  }

  /**
   * Calculate the ratio of numeric content to total content
   */
  private calculateNumericDensity(content: any): number {
    if (typeof content === 'string') {
      return this.calculateStringNumericDensity(content);
    } else if (typeof content === 'object') {
      return this.calculateObjectNumericDensity(content);
    }
    return 0;
  }

  private calculateStringNumericDensity(text: string): number {
    // Extract all words/tokens
    const tokens = text.split(/\s+/).filter(t => t.length > 0);
    if (tokens.length === 0) return 0;
    
    // Count numeric tokens (numbers, dates, currencies, measurements)
    const numericTokens = tokens.filter(token => 
      this.isNumericToken(token)
    ).length;
    
    return numericTokens / tokens.length;
  }

  private calculateObjectNumericDensity(obj: any): number {
    const values = this.getAllValues(obj);
    if (values.length === 0) return 0;
    
    const numericValues = values.filter(v => 
      typeof v === 'number' || this.isNumericToken(String(v))
    ).length;
    
    return numericValues / values.length;
  }

  /**
   * Check if a token represents a numeric value
   */
  private isNumericToken(token: string): boolean {
    // Pure numbers
    if (!isNaN(Number(token))) return true;
    
    // Currencies: $100, €50, £75
    if (/^[£$€¥][\d,]+\.?\d*$/.test(token)) return true;
    
    // Percentages: 45%, 12.5%
    if (/^\d+\.?\d*%$/.test(token)) return true;
    
    // Dates: 2023-01-15, 01/15/2023
    if (/^\d{2,4}[-/]\d{1,2}[-/]\d{1,4}$/.test(token)) return true;
    
    // Measurements with units: 10kg, 5.5m, 100ml
    if (/^\d+\.?\d*[a-zA-Z]{1,3}$/.test(token)) return true;
    
    // Boolean-like: true, false, yes, no, 0, 1
    if (/^(true|false|yes|no|0|1)$/i.test(token)) return true;
    
    return false;
  }

  /**
   * Calculate text density (prose-like content)
   */
  private calculateTextDensity(content: any): number {
    if (typeof content === 'string') {
      // Long strings with punctuation are likely text
      const hasMultipleSentences = (content.match(/[.!?]/g) || []).length > 1;
      const avgWordLength = content.split(/\s+/)
        .filter(w => w.length > 0)
        .reduce((sum, w) => sum + w.length, 0) / content.split(/\s+/).length;
      
      // English prose averages 4-5 chars per word
      if (hasMultipleSentences && avgWordLength >= 3 && avgWordLength <= 7) {
        return 0.9;
      }
      
      return 1 - this.calculateNumericDensity(content);
    } else if (typeof content === 'object') {
      const textValues = this.getAllValues(content).filter(v => 
        typeof v === 'string' && v.length > 20 && /[.!?]/.test(v)
      ).length;
      
      const totalValues = this.getAllValues(content).length;
      return totalValues > 0 ? textValues / totalValues : 0;
    }
    
    return 0;
  }

  /**
   * Detect if content contains prose (natural language sentences)
   */
  private detectProse(content: any): boolean {
    const text = typeof content === 'string' ? content : JSON.stringify(content);
    
    // Look for sentence patterns
    const sentences = text.match(/[A-Z][^.!?]*[.!?]/g) || [];
    if (sentences.length < 2) return false;
    
    // Check for common prose indicators
    const proseIndicators = [
      /\b(the|a|an|is|are|was|were|been|have|has|had)\b/i, // Articles and verbs
      /[,;:()]/, // Punctuation typical in prose
      /\b\w{4,}\b.*\b\w{4,}\b/ // Multiple longer words
    ];
    
    return proseIndicators.some(pattern => pattern.test(text));
  }

  /**
   * Detect if content has structured data patterns
   */
  private detectStructure(content: any): boolean {
    if (typeof content === 'object' && content !== null) {
      // Arrays and objects are inherently structured
      return true;
    }
    
    if (typeof content === 'string') {
      // Look for key-value patterns: "key: value"
      if (/\w+:\s*\w+/.test(content)) return true;
      
      // Look for tabular patterns (consistent delimiters)
      const lines = content.split('\n');
      if (lines.length > 2) {
        const firstLineDelimiters = (lines[0].match(/[,\t|]/g) || []).length;
        const consistentDelimiters = lines.slice(1, 5).every(line =>
          (line.match(/[,\t|]/g) || []).length === firstLineDelimiters
        );
        
        if (consistentDelimiters && firstLineDelimiters > 0) return true;
      }
    }
    
    return false;
  }

  /**
   * Simple language detection (English vs other)
   */
  private detectLanguage(content: any): string | undefined {
    const text = typeof content === 'string' ? content : JSON.stringify(content);
    
    // Simple heuristic: check for common English words
    const commonEnglishWords = ['the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was', 'were'];
    const words = text.toLowerCase().split(/\s+/);
    const englishWordCount = words.filter(w => commonEnglishWords.includes(w)).length;
    
    if (englishWordCount > words.length * 0.02) {
      return 'en';
    }
    
    return undefined;
  }

  /**
   * Infer schema from structured content
   */
  private inferSchema(content: any): Record<string, string> | undefined {
    if (typeof content === 'object' && content !== null && !Array.isArray(content)) {
      const schema: Record<string, string> = {};
      
      for (const [key, value] of Object.entries(content)) {
        if (typeof value === 'number') {
          schema[key] = 'number';
        } else if (typeof value === 'boolean') {
          schema[key] = 'boolean';
        } else if (typeof value === 'string') {
          if (this.isNumericToken(value)) {
            schema[key] = 'numeric_string';
          } else if (value.length > 50) {
            schema[key] = 'text';
          } else {
            schema[key] = 'string';
          }
        } else if (Array.isArray(value)) {
          schema[key] = 'array';
        } else if (typeof value === 'object') {
          schema[key] = 'object';
        } else {
          schema[key] = 'unknown';
        }
      }
      
      return Object.keys(schema).length > 0 ? schema : undefined;
    }
    
    return undefined;
  }

  /**
   * Extract all values from nested object structure
   */
  private getAllValues(obj: any, values: any[] = []): any[] {
    if (typeof obj === 'object' && obj !== null) {
      if (Array.isArray(obj)) {
        obj.forEach(item => this.getAllValues(item, values));
      } else {
        Object.values(obj).forEach(value => {
          values.push(value);
          if (typeof value === 'object') {
            this.getAllValues(value, values);
          }
        });
      }
    } else {
      values.push(obj);
    }
    
    return values;
  }
}

/**
 * Classifies content into quantitative, qualitative, or mixed segments
 */
export class SegmentClassifier {
  /**
   * Classify content based on analysis results
   */
  classify(analysis: ContentAnalysis): SegmentType {
    // Already determined in analyzer, but this allows for override logic
    return analysis.classification;
  }

  /**
   * Additional classification with custom thresholds
   */
  classifyWithThresholds(
    analysis: ContentAnalysis,
    quantThreshold: number = 0.70,
    mixedLowerBound: number = 0.30
  ): SegmentType {
    if (analysis.numeric_density >= quantThreshold) {
      return 'quantitative';
    } else if (analysis.numeric_density <= mixedLowerBound) {
      return 'qualitative';
    } else {
      return 'mixed';
    }
  }

  /**
   * Get confidence score for classification
   */
  getConfidence(analysis: ContentAnalysis): number {
    const { numeric_density } = analysis;
    
    // Higher confidence when clearly in one category
    if (numeric_density >= 0.90 || numeric_density <= 0.10) {
      return 0.95;
    } else if (numeric_density >= 0.80 || numeric_density <= 0.20) {
      return 0.85;
    } else if (numeric_density >= 0.70 || numeric_density <= 0.30) {
      return 0.75;
    } else {
      // Mixed category has inherently lower confidence
      return 0.60;
    }
  }
}
