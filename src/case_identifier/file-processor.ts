/**
 * Unified File Processing Pipeline
 * Handles ANY file format through: Parse → Analyze → Classify → Extract
 */

import * as crypto from 'crypto';
import * as fs from 'fs';
import { ParsedElement, ContentAnalysis, SegmentType, ProcessingStatus } from './types';
import { ContentAnalyzer } from './content-analyzer';
import { SegmentClassifier } from './content-analyzer';
import { KeywordExtractor } from './keyword-extractor';

/**
 * Main pipeline orchestrator
 */
export class UnifiedFileProcessor {
  constructor(
    private formatParser: FormatParserFactory,
    private contentAnalyzer: ContentAnalyzer,
    private segmentClassifier: SegmentClassifier,
    private keywordExtractor: KeywordExtractor,
    private dbClient: SupabaseClient
  ) {}

  /**
   * Process a file through the complete pipeline
   */
  async processFile(filePath: string, filename: string): Promise<string> {
    const fileId = await this.registerFile(filePath, filename);
    
    try {
      // Update status: parsing
      await this.updateFileStatus(fileId, 'parsing');
      
      // Step 1: Parse file based on format
      const extension = filename.split('.').pop()?.toLowerCase() || '';
      const parser = this.formatParser.getParser(extension);
      const parsedElements = await parser.parse(filePath);
      
      // Update status: analyzing
      await this.updateFileStatus(fileId, 'analyzing');
      
      // Step 2: Analyze and classify each parsed element
      const classifiedSegments = await this.analyzeAndClassify(parsedElements, fileId);
      
      // Update status: extracting
      await this.updateFileStatus(fileId, 'extracting');
      
      // Step 3: Extract keywords from all segments
      await this.extractKeywordsFromSegments(classifiedSegments, fileId);
      
      // Update status: complete
      await this.updateFileStatus(fileId, 'complete');
      
      return fileId;
    } catch (error) {
      await this.updateFileStatus(fileId, 'failed', (error as Error).message);
      throw error;
    }
  }

  /**
   * Register file in database with content hash
   */
  private async registerFile(filePath: string, filename: string): Promise<string> {
    const contentHash = await this.calculateFileHash(filePath);
    const extension = filename.split('.').pop()?.toLowerCase() || '';
    const fs = await import('fs/promises');
    const stats = await fs.stat(filePath);
    
    // Check if file already exists (idempotent import)
    const { data: existing } = await this.dbClient
      .from('file_imports')
      .select('file_id')
      .eq('raw_content_hash', contentHash)
      .single();
    
    if (existing) {
      // Update existing record
      await this.dbClient
        .from('file_imports')
        .update({
          import_timestamp: new Date().toISOString(),
          processing_status: 'pending'
        })
        .eq('file_id', existing.file_id);
      
      return existing.file_id;
    }
    
    // Insert new file
    const { data, error } = await this.dbClient
      .from('file_imports')
      .insert({
        filename,
        extension,
        file_size_bytes: stats.size,
        raw_content_hash: contentHash,
        processing_status: 'pending'
      })
      .select('file_id')
      .single();
    
    if (error) throw error;
    return data.file_id;
  }

  /**
   * Calculate SHA-256 hash of file content
   */
  private async calculateFileHash(filePath: string): Promise<string> {
    return new Promise((resolve, reject) => {
      const hash = crypto.createHash('sha256');
      const stream = fs.createReadStream(filePath);
      
      stream.on('data', (data: string | Buffer) => hash.update(data));
      stream.on('end', () => resolve(hash.digest('hex')));
      stream.on('error', reject);
    });
  }

  /**
   * Update file processing status
   */
  private async updateFileStatus(
    fileId: string,
    status: ProcessingStatus,
    error?: string
  ): Promise<void> {
    await this.dbClient
      .from('file_imports')
      .update({
        processing_status: status,
        processing_error: error
      })
      .eq('file_id', fileId);
  }

  /**
   * Analyze and classify all parsed elements
   */
  private async analyzeAndClassify(
    elements: ParsedElement[],
    fileId: string
  ): Promise<Array<{ segment: any; type: SegmentType }>> {
    const results: Array<{ segment: any; type: SegmentType }> = [];
    
    for (const element of elements) {
      const analysis = await this.contentAnalyzer.analyze(element);
      const segmentType = this.segmentClassifier.classify(analysis);
      
      const segment = await this.storeSegment(element, analysis, segmentType, fileId);
      results.push({ segment, type: segmentType });
    }
    
    return results;
  }

  /**
   * Store segment in appropriate table based on classification
   */
  private async storeSegment(
    element: ParsedElement,
    analysis: ContentAnalysis,
    type: SegmentType,
    fileId: string
  ): Promise<any> {
    const baseSegment = {
      file_id: fileId,
      position_in_file: element.position,
      extraction_timestamp: new Date().toISOString()
    };
    
    if (type === 'quantitative') {
      const { data, error } = await this.dbClient
        .from('quantitative_segments')
        .insert({
          ...baseSegment,
          data_structure: typeof element.content === 'object' ? element.content : { value: element.content },
          column_mappings: analysis.schema,
          numeric_density: analysis.numeric_density
        })
        .select()
        .single();
      
      if (error) throw error;
      return data;
    } else if (type === 'qualitative') {
      const textContent = typeof element.content === 'string'
        ? element.content
        : JSON.stringify(element.content);
      
      const { data, error } = await this.dbClient
        .from('qualitative_segments')
        .insert({
          ...baseSegment,
          text_content: textContent,
          segment_subtype: element.metadata.subtype,
          language_code: analysis.detected_language || 'en',
          word_count: this.countWords(textContent),
          sentence_count: this.countSentences(textContent)
        })
        .select()
        .single();
      
      if (error) throw error;
      return data;
    } else {
      // Mixed
      const { data, error } = await this.dbClient
        .from('mixed_segments')
        .insert({
          ...baseSegment,
          structure: element.content,
          text_elements: this.extractTextElements(element.content),
          numeric_elements: this.extractNumericElements(element.content),
          quantitative_ratio: analysis.numeric_density
        })
        .select()
        .single();
      
      if (error) throw error;
      return data;
    }
  }

  /**
   * Extract keywords from all classified segments
   */
  private async extractKeywordsFromSegments(
    segments: Array<{ segment: any; type: SegmentType }>,
    fileId: string
  ): Promise<void> {
    for (const { segment, type } of segments) {
      await this.keywordExtractor.extractAndStore(segment, type, fileId);
    }
  }

  // Utility methods
  private countWords(text: string): number {
    return text.trim().split(/\s+/).length;
  }

  private countSentences(text: string): number {
    return (text.match(/[.!?]+/g) || []).length;
  }

  private extractTextElements(content: any): Record<string, any> {
    // Extract text-based elements from mixed content
    if (typeof content === 'object') {
      const textElements: Record<string, any> = {};
      for (const [key, value] of Object.entries(content)) {
        if (typeof value === 'string' && value.length > 10) {
          textElements[key] = value;
        }
      }
      return textElements;
    }
    return {};
  }

  private extractNumericElements(content: any): Record<string, any> {
    // Extract numeric elements from mixed content
    if (typeof content === 'object') {
      const numericElements: Record<string, any> = {};
      for (const [key, value] of Object.entries(content)) {
        if (typeof value === 'number' || !isNaN(Number(value))) {
          numericElements[key] = value;
        }
      }
      return numericElements;
    }
    return {};
  }
}

/**
 * Format parser factory - returns appropriate parser for file type
 */
export class FormatParserFactory {
  private parsers: Map<string, FileParser>;

  constructor() {
    this.parsers = new Map();
    this.registerDefaultParsers();
  }

  private registerDefaultParsers(): void {
    this.parsers.set('csv', new CSVParser());
    this.parsers.set('tsv', new TSVParser());
    this.parsers.set('json', new JSONParser());
    this.parsers.set('xml', new XMLParser());
    this.parsers.set('pdf', new PDFParser());
    this.parsers.set('txt', new TextParser());
    this.parsers.set('docx', new DOCXParser());
    this.parsers.set('xlsx', new XLSXParser());
  }

  getParser(extension: string): FileParser {
    const parser = this.parsers.get(extension);
    if (!parser) {
      throw new Error(`No parser registered for extension: ${extension}`);
    }
    return parser;
  }

  registerParser(extension: string, parser: FileParser): void {
    this.parsers.set(extension, parser);
  }
}

/**
 * Base interface for file parsers
 */
export interface FileParser {
  parse(filePath: string): Promise<ParsedElement[]>;
}

/**
 * CSV Parser
 */
export class CSVParser implements FileParser {
  async parse(filePath: string): Promise<ParsedElement[]> {
    const fsPromises = await import('fs/promises');
    const content = await fsPromises.readFile(filePath, 'utf-8');
    const lines = content.split('\n').filter((line: string) => line.trim());
    
    if (lines.length === 0) return [];
    
    const headers = this.parseCSVLine(lines[0]);
    const rows: ParsedElement[] = [];
    
    for (let i = 1; i < lines.length; i++) {
      const values = this.parseCSVLine(lines[i]);
      const rowData: Record<string, string> = {};
      
      headers.forEach((header, index) => {
        rowData[header] = values[index] || '';
      });
      
      rows.push({
        content: rowData,
        type: 'table',
        position: { line_start: i + 1, line_end: i + 1 },
        metadata: { row_index: i, headers }
      });
    }
    
    return rows;
  }

  private parseCSVLine(line: string): string[] {
    const result: string[] = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        result.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    
    result.push(current.trim());
    return result;
  }
}

/**
 * TSV Parser (similar to CSV but tab-delimited)
 */
export class TSVParser implements FileParser {
  async parse(filePath: string): Promise<ParsedElement[]> {
    const fsPromises = await import('fs/promises');
    const content = await fsPromises.readFile(filePath, 'utf-8');
    const lines = content.split('\n').filter((line: string) => line.trim());
    
    if (lines.length === 0) return [];
    
    const headers = lines[0].split('\t');
    const rows: ParsedElement[] = [];
    
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split('\t');
      const rowData: Record<string, string> = {};
      
      headers.forEach((header, index) => {
        rowData[header] = values[index] || '';
      });
      
      rows.push({
        content: rowData,
        type: 'table',
        position: { line_start: i + 1, line_end: i + 1 },
        metadata: { row_index: i, headers }
      });
    }
    
    return rows;
  }
}

/**
 * JSON Parser
 */
export class JSONParser implements FileParser {
  async parse(filePath: string): Promise<ParsedElement[]> {
    const fsPromises = await import('fs/promises');
    const content = await fsPromises.readFile(filePath, 'utf-8');
    const json = JSON.parse(content);
    
    return this.parseJSONStructure(json, []);
  }

  private parseJSONStructure(
    obj: any,
    path: string[]
  ): ParsedElement[] {
    const elements: ParsedElement[] = [];
    
    if (Array.isArray(obj)) {
      obj.forEach((item, index) => {
        elements.push(...this.parseJSONStructure(item, [...path, `[${index}]`]));
      });
    } else if (typeof obj === 'object' && obj !== null) {
      elements.push({
        content: obj,
        type: 'tree',
        position: { xpath: path.join('.') },
        metadata: { keys: Object.keys(obj), depth: path.length }
      });
      
      for (const [key, value] of Object.entries(obj)) {
        if (typeof value === 'object') {
          elements.push(...this.parseJSONStructure(value, [...path, key]));
        }
      }
    }
    
    return elements;
  }
}

/**
 * XML Parser
 */
export class XMLParser implements FileParser {
  async parse(filePath: string): Promise<ParsedElement[]> {
    const fsPromises = await import('fs/promises');
    const xml2js = await import('xml2js');
    const content = await fsPromises.readFile(filePath, 'utf-8');
    const parser = new xml2js.Parser();
    const result = await parser.parseStringPromise(content);
    
    return this.parseXMLNode(result, []);
  }

  private parseXMLNode(node: any, path: string[]): ParsedElement[] {
    const elements: ParsedElement[] = [];
    
    if (typeof node === 'object' && node !== null) {
      for (const [tagName, value] of Object.entries(node)) {
        const currentPath = [...path, tagName];
        
        elements.push({
          content: value as any,
          type: 'tree',
          position: { xpath: '/' + currentPath.join('/') },
          metadata: { tag_name: tagName, depth: currentPath.length }
        });
        
        if (Array.isArray(value)) {
          value.forEach((item, index) => {
            elements.push(...this.parseXMLNode(item, [...currentPath, `[${index}]`]));
          });
        } else if (typeof value === 'object') {
          elements.push(...this.parseXMLNode(value, currentPath));
        }
      }
    }
    
    return elements;
  }
}

/**
 * PDF Parser (requires pdf-parse library)
 */
export class PDFParser implements FileParser {
  async parse(filePath: string): Promise<ParsedElement[]> {
    const fsPromises = await import('fs/promises');
    const pdfParse = await import('pdf-parse');
    const dataBuffer = await fsPromises.readFile(filePath);
    const data = await pdfParse.default(dataBuffer);
    
    // Split text into paragraphs
    const paragraphs = data.text.split('\n\n').filter((p: string) => p.trim());
    
    return paragraphs.map((text: string, index: number) => ({
      content: text,
      type: 'text',
      position: { paragraph_index: index, page: Math.floor(index / 10) + 1 },
      metadata: { total_pages: data.numpages }
    }));
  }
}

/**
 * Plain text parser
 */
export class TextParser implements FileParser {
  async parse(filePath: string): Promise<ParsedElement[]> {
    const fsPromises = await import('fs/promises');
    const content = await fsPromises.readFile(filePath, 'utf-8');
    const paragraphs = content.split('\n\n').filter((p: string) => p.trim());
    
    return paragraphs.map((text: string, index: number) => ({
      content: text,
      type: 'text',
      position: { paragraph_index: index },
      metadata: {}
    }));
  }
}

/**
 * DOCX Parser (requires mammoth library)
 */
export class DOCXParser implements FileParser {
  async parse(filePath: string): Promise<ParsedElement[]> {
    const mammoth = await import('mammoth');
    const result = await mammoth.extractRawText({ path: filePath });
    const paragraphs = result.value.split('\n\n').filter((p: string) => p.trim());
    
    return paragraphs.map((text: string, index: number) => ({
      content: text,
      type: 'text',
      position: { paragraph_index: index },
      metadata: { source_type: 'docx' }
    }));
  }
}

/**
 * XLSX Parser (requires xlsx library)
 */
export class XLSXParser implements FileParser {
  async parse(filePath: string): Promise<ParsedElement[]> {
    const XLSX = await import('xlsx');
    const workbook = XLSX.readFile(filePath);
    const elements: ParsedElement[] = [];
    
    for (const sheetName of workbook.SheetNames) {
      const worksheet = workbook.Sheets[sheetName];
      const data = XLSX.utils.sheet_to_json(worksheet);
      
      data.forEach((row: any, index: number) => {
        elements.push({
          content: row,
          type: 'table',
          position: { sheet_name: sheetName, row_index: index },
          metadata: { sheet_name: sheetName, total_sheets: workbook.SheetNames.length }
        });
      });
    }
    
    return elements;
  }
}

// Type placeholder for Supabase client
interface SupabaseClient {
  from(table: string): any;
}
