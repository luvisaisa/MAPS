/**
 * Usage Examples for Schema-Agnostic Case Identifier System
 * Demonstrates end-to-end workflows and common query patterns
 */

// Note: Install @supabase/supabase-js and @types/node before using
// npm install @supabase/supabase-js
// npm install --save-dev @types/node

import { getSupabaseClient } from './supabase-client';
import {
  UnifiedFileProcessor,
  FormatParserFactory
} from './file-processor';
import { ContentAnalyzer, SegmentClassifier } from './content-analyzer';
import { KeywordExtractor } from './keyword-extractor';
import { KeywordProcessor } from './keyword-relevance';
import { CrossContentQueryBuilder } from './query-interface';
import { CasePatternDetector } from './case-detector';

// Initialize secure Supabase client (reads from environment, never hardcoded)
const supabase = getSupabaseClient();

// =============================================================================
// Example 1: Process a Single File
// =============================================================================

async function example1_processSingleFile() {
  console.log('=== Example 1: Process Single File ===\n');

  // Initialize components
  const formatParser = new FormatParserFactory();
  const contentAnalyzer = new ContentAnalyzer();
  const segmentClassifier = new SegmentClassifier();
  const keywordProcessor = new KeywordProcessor(supabase);
  await keywordProcessor.initialize();
  const keywordExtractor = new KeywordExtractor(supabase, keywordProcessor);

  // Create processor
  const processor = new UnifiedFileProcessor(
    formatParser,
    contentAnalyzer,
    segmentClassifier,
    keywordExtractor,
    supabase
  );

  // Process file (works for ANY format: CSV, JSON, XML, PDF, etc.)
  const fileId = await processor.processFile(
    '/path/to/data.csv',
    'data.csv'
  );

  console.log(`File processed successfully! File ID: ${fileId}`);
}

// =============================================================================
// Example 2: Process Multiple Files of Different Types
// =============================================================================

async function example2_processMultipleFiles() {
  console.log('=== Example 2: Process Multiple Files ===\n');

  const formatParser = new FormatParserFactory();
  const contentAnalyzer = new ContentAnalyzer();
  const segmentClassifier = new SegmentClassifier();
  const keywordProcessor = new KeywordProcessor(supabase);
  await keywordProcessor.initialize();
  const keywordExtractor = new KeywordExtractor(supabase, keywordProcessor);

  const processor = new UnifiedFileProcessor(
    formatParser,
    contentAnalyzer,
    segmentClassifier,
    keywordExtractor,
    supabase
  );

  // Process different file types through same pipeline
  const files = [
    { path: '/data/study_results.csv', name: 'study_results.csv' },
    { path: '/data/methodology.pdf', name: 'methodology.pdf' },
    { path: '/data/annotations.xml', name: 'annotations.xml' },
    { path: '/data/measurements.xlsx', name: 'measurements.xlsx' }
  ];

  for (const file of files) {
    const fileId = await processor.processFile(file.path, file.name);
    console.log(`Processed ${file.name} → ${fileId}`);
  }

  console.log('\nAll files processed through unified pipeline!');
}

// =============================================================================
// Example 3: Find Keywords Spanning Quantitative and Qualitative Content
// =============================================================================

async function example3_crossTypeKeywords() {
  console.log('=== Example 3: Cross-Type Keywords ===\n');

  const queryBuilder = new CrossContentQueryBuilder(supabase);

  // Find keywords appearing in BOTH quantitative and qualitative segments
  const crossTypeKeywords = await queryBuilder.findCrossTypeKeywords({
    minRelevanceScore: 10,
    minFileCount: 2,
    limit: 20
  });

  console.log('High-signal keywords bridging data and narrative:\n');
  for (const keyword of crossTypeKeywords) {
    console.log(`${keyword.term}`);
    console.log(`  Relevance: ${keyword.relevance_score.toFixed(2)}`);
    console.log(`  Quantitative occurrences: ${keyword.quantitative_occurrences}`);
    console.log(`  Qualitative occurrences: ${keyword.qualitative_occurrences}`);
    console.log(`  Files: ${keyword.file_count}`);
    console.log('');
  }
}

// =============================================================================
// Example 4: Retrieve All Numeric Associations for a Keyword
// =============================================================================

async function example4_numericAssociations() {
  console.log('=== Example 4: Numeric Associations ===\n');

  const queryBuilder = new CrossContentQueryBuilder(supabase);

  // Get all numbers associated with the keyword "dosage"
  const associations = await queryBuilder.getKeywordNumericAssociations('dosage');

  console.log('All numeric values associated with "dosage":\n');
  for (const assoc of associations) {
    console.log(`File: ${assoc.filename}`);
    console.log(`Context: ${assoc.surrounding_context?.substring(0, 100)}...`);
    console.log(`Numbers: ${JSON.stringify(assoc.associated_values)}`);
    console.log('---');
  }
}

// =============================================================================
// Example 5: Find Files Containing Specific Keyword Pattern
// =============================================================================

async function example5_findFilesWithKeywords() {
  console.log('=== Example 5: Find Files with Keywords ===\n');

  const queryBuilder = new CrossContentQueryBuilder(supabase);

  // Find files containing ALL of these keywords
  const files = await queryBuilder.findFilesWithKeywords([
    'patient',
    'treatment',
    'outcome'
  ]);

  console.log('Files containing patient + treatment + outcome:\n');
  for (const file of files) {
    console.log(`${file.filename}`);
    console.log(`  Matched keywords: ${file.match_count}`);
    console.log(`  Keywords: ${JSON.stringify(file.matched_keywords)}`);
    console.log('');
  }
}

// =============================================================================
// Example 6: Detect Case Patterns
// =============================================================================

async function example6_detectCasePatterns() {
  console.log('=== Example 6: Detect Case Patterns ===\n');

  const detector = new CasePatternDetector(supabase);

  // Detect patterns with cross-type validation
  const patterns = await detector.detectPatterns({
    minKeywordCount: 3,
    minCoOccurrenceThreshold: 2,
    minConfidenceScore: 0.6,
    requireCrossTypeValidation: true
  });

  console.log(`Detected ${patterns.length} high-confidence case patterns:\n`);
  for (const pattern of patterns) {
    console.log(`Pattern ID: ${pattern.pattern_signature.substring(0, 16)}...`);
    console.log(`  Confidence: ${(pattern.confidence_score * 100).toFixed(1)}%`);
    console.log(`  Cross-type validated: ${pattern.cross_type_validated}`);
    console.log(`  Keywords (${pattern.keyword_count}):`);
    for (const kw of pattern.keywords.slice(0, 5)) {
      console.log(`    - ${kw.term} (freq: ${kw.frequency})`);
    }
    console.log(`  Appears in ${pattern.file_count} files, ${pattern.segment_count} segments`);
    console.log('');
  }
}

// =============================================================================
// Example 7: Full-Text Search Across All Content Types
// =============================================================================

async function example7_fullTextSearch() {
  console.log('=== Example 7: Full-Text Search ===\n');

  const queryBuilder = new CrossContentQueryBuilder(supabase);

  // Search for "adverse event" across ALL segment types
  const results = await queryBuilder.fullTextSearch('adverse event', {
    limit: 10
  });

  console.log('Search results for "adverse event":\n');
  for (const result of results) {
    console.log(`Type: ${result.segment_type}`);
    console.log(`File ID: ${result.file_id}`);
    console.log(`Content preview: ${JSON.stringify(result.content).substring(0, 100)}...`);
    console.log('---');
  }
}

// =============================================================================
// Example 8: Compare Keyword Distributions
// =============================================================================

async function example8_compareDistributions() {
  console.log('=== Example 8: Keyword Distributions ===\n');

  const queryBuilder = new CrossContentQueryBuilder(supabase);

  // Compare keywords in CSV files vs PDF files
  const csvDistribution = await queryBuilder.compareKeywordDistributions({
    extension: 'csv',
    topN: 10
  });

  const pdfDistribution = await queryBuilder.compareKeywordDistributions({
    extension: 'pdf',
    topN: 10
  });

  console.log('Top keywords in CSV files:\n');
  for (const entry of csvDistribution) {
    console.log(`  ${entry.term}: ${entry.total_count} occurrences`);
  }

  console.log('\nTop keywords in PDF files:\n');
  for (const entry of pdfDistribution) {
    console.log(`  ${entry.term}: ${entry.total_count} occurrences`);
  }
}

// =============================================================================
// Example 9: Update Relevance Scores
// =============================================================================

async function example9_updateRelevanceScores() {
  console.log('=== Example 9: Update Relevance Scores ===\n');

  const keywordProcessor = new KeywordProcessor(supabase);
  await keywordProcessor.initialize();

  console.log('Recalculating relevance scores for all keywords...');
  await keywordProcessor.updateRelevanceScores();
  console.log('Relevance scores updated!');
}

// =============================================================================
// Example 10: Edge Case - Empty File
// =============================================================================

async function example10_edgeCaseEmptyFile() {
  console.log('=== Example 10: Edge Case - Empty File ===\n');

  const formatParser = new FormatParserFactory();
  const contentAnalyzer = new ContentAnalyzer();
  const segmentClassifier = new SegmentClassifier();
  const keywordProcessor = new KeywordProcessor(supabase);
  await keywordProcessor.initialize();
  const keywordExtractor = new KeywordExtractor(supabase, keywordProcessor);

  const processor = new UnifiedFileProcessor(
    formatParser,
    contentAnalyzer,
    segmentClassifier,
    keywordExtractor,
    supabase
  );

  try {
    const fileId = await processor.processFile('/path/to/empty.csv', 'empty.csv');
    console.log('Empty file processed (no segments created)');
  } catch (error) {
    console.error('Error processing empty file:', error);
  }
}

// =============================================================================
// Example 11: Query Pattern - Get All Contexts for a Keyword
// =============================================================================

async function example11_keywordContexts() {
  console.log('=== Example 11: Keyword Contexts ===\n');

  const queryBuilder = new CrossContentQueryBuilder(supabase);

  // Get every occurrence of "efficacy" with full context
  const contexts = await queryBuilder.getKeywordContexts('efficacy');

  console.log('All contexts for "efficacy":\n');
  for (const ctx of contexts.slice(0, 5)) {
    console.log(`Segment type: ${ctx.segment_type}`);
    console.log(`File: ${ctx.file_name}`);
    console.log(`Context: ${ctx.context?.substring(0, 150)}...`);
    if (ctx.numeric_values) {
      console.log(`Associated numbers: ${JSON.stringify(ctx.numeric_values)}`);
    }
    console.log('---');
  }
}

// =============================================================================
// Example 12: Add Custom Stop Words
// =============================================================================

async function example12_customStopWords() {
  console.log('=== Example 12: Custom Stop Words ===\n');

  const keywordProcessor = new KeywordProcessor(supabase);
  await keywordProcessor.initialize();

  // Add domain-specific stop words
  await keywordProcessor.getFilter().addStopWords(
    ['lorem', 'ipsum', 'placeholder'],
    'custom'
  );

  console.log('Custom stop words added!');
}

// =============================================================================
// Run Examples
// =============================================================================

async function runExamples() {
  try {
    // await example1_processSingleFile();
    // await example2_processMultipleFiles();
    await example3_crossTypeKeywords();
    await example4_numericAssociations();
    await example5_findFilesWithKeywords();
    await example6_detectCasePatterns();
    await example7_fullTextSearch();
    await example8_compareDistributions();
    // await example9_updateRelevanceScores();
    // await example10_edgeCaseEmptyFile();
    await example11_keywordContexts();
    // await example12_customStopWords();
  } catch (error) {
    console.error('Error running examples:', error);
  }
}

// Uncomment to run:
// runExamples();

export {
  example1_processSingleFile,
  example2_processMultipleFiles,
  example3_crossTypeKeywords,
  example4_numericAssociations,
  example5_findFilesWithKeywords,
  example6_detectCasePatterns,
  example7_fullTextSearch,
  example8_compareDistributions,
  example9_updateRelevanceScores,
  example10_edgeCaseEmptyFile,
  example11_keywordContexts,
  example12_customStopWords
};
