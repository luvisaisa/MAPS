/**
 * Mock data for development when backend API is not available
 */

import type { 
  DashboardStats, 
  Profile, 
  ProcessingJob,
  PaginatedResponse,
  CanonicalDocument,
  Keyword,
  KeywordStats,
  ParseCaseDistribution,
  InterRaterReliability,
  DataCompleteness,
  PYLIDCScan
} from '../types/api';

export const mockDashboardStats: DashboardStats = {
  total_documents: 1247,
  total_jobs: 89,
  success_rate: 94.5,
  error_rate: 5.5,
  processing_trends: [
    { date: '2025-11-16', count: 45, success: 42, failed: 3 },
    { date: '2025-11-17', count: 52, success: 50, failed: 2 },
    { date: '2025-11-18', count: 38, success: 36, failed: 2 },
    { date: '2025-11-19', count: 61, success: 58, failed: 3 },
    { date: '2025-11-20', count: 47, success: 44, failed: 3 },
    { date: '2025-11-21', count: 55, success: 52, failed: 3 },
    { date: '2025-11-22', count: 43, success: 41, failed: 2 },
    { date: '2025-11-23', count: 28, success: 27, failed: 1 },
  ],
  parse_case_distribution: {
    'case_1_standard': 450,
    'case_2_multi_session': 320,
    'case_3_unblinded': 287,
    'case_4_variant': 190,
  },
  storage_usage: {
    total_size: 500000000,
    document_count: 1247,
    average_size: 400960,
  },
};

export const mockProfiles: Profile[] = [
  {
    profile_name: 'lidc_idri_standard',
    file_type: 'xml',
    description: 'Standard LIDC-IDRI CT annotation format',
    mappings: [],
    validation_rules: { required_fields: [] },
  },
  {
    profile_name: 'nyt_standard',
    file_type: 'xml',
    description: 'NYT XML format for radiology reports',
    mappings: [],
    validation_rules: { required_fields: [] },
  },
];

export const mockJobs: PaginatedResponse<ProcessingJob> = {
  items: [
    {
      id: 'job-001',
      status: 'completed',
      profile_name: 'lidc_idri_standard',
      file_count: 25,
      processed_count: 25,
      error_count: 0,
      created_at: '2025-11-23T10:30:00Z',
      updated_at: '2025-11-23T10:35:00Z',
      completed_at: '2025-11-23T10:35:00Z',
    },
    {
      id: 'job-002',
      status: 'processing',
      profile_name: 'lidc_idri_standard',
      file_count: 50,
      processed_count: 32,
      error_count: 1,
      created_at: '2025-11-23T10:40:00Z',
      updated_at: '2025-11-23T10:45:00Z',
    },
    {
      id: 'job-003',
      status: 'pending',
      profile_name: 'nyt_standard',
      file_count: 10,
      processed_count: 0,
      error_count: 0,
      created_at: '2025-11-23T10:45:00Z',
      updated_at: '2025-11-23T10:45:00Z',
    },
  ],
  total: 89,
  page: 1,
  page_size: 20,
  total_pages: 5,
};

export const mockDocuments: PaginatedResponse<CanonicalDocument> = {
  items: [
    {
      id: 'doc-001',
      metadata: {
        title: 'LIDC-IDRI-0001 CT Scan Annotation',
        date: '2025-11-20',
        source: 'LIDC-IDRI Dataset',
      },
      content: {},
      parse_case: 'case_1_standard',
      created_at: '2025-11-20T14:30:00Z',
    },
    {
      id: 'doc-002',
      metadata: {
        title: 'LIDC-IDRI-0002 CT Scan Annotation',
        date: '2025-11-20',
        source: 'LIDC-IDRI Dataset',
      },
      content: {},
      parse_case: 'case_2_multi_session',
      created_at: '2025-11-20T14:32:00Z',
    },
  ],
  total: 1247,
  page: 1,
  page_size: 20,
  total_pages: 63,
};

export const mockKeywords: Keyword[] = [
  {
    id: 'kw-001',
    term: 'pulmonary nodule',
    canonical_term: 'pulmonary_nodule',
    category: 'pathology',
    frequency: 342,
  },
  {
    id: 'kw-002',
    term: 'ground glass opacity',
    canonical_term: 'ground_glass_opacity',
    category: 'imaging_characteristic',
    frequency: 198,
  },
  {
    id: 'kw-003',
    term: 'spiculation',
    canonical_term: 'spiculation',
    category: 'morphology',
    frequency: 156,
  },
];

export const mockKeywordStats: KeywordStats = {
  total_keywords: 2845,
  unique_terms: 487,
  categories: {
    anatomy: 89,
    pathology: 142,
    imaging_characteristic: 95,
    morphology: 76,
    measurement: 85,
  },
  top_keywords: [
    { term: 'pulmonary nodule', count: 342 },
    { term: 'ground glass opacity', count: 198 },
    { term: 'spiculation', count: 156 },
    { term: 'calcification', count: 134 },
    { term: 'lobulation', count: 112 },
  ],
};

export const mockParseCaseDistribution: ParseCaseDistribution[] = [
  { parse_case: 'case_1_standard', count: 450, percentage: 36.1 },
  { parse_case: 'case_2_multi_session', count: 320, percentage: 25.7 },
  { parse_case: 'case_3_unblinded', count: 287, percentage: 23.0 },
  { parse_case: 'case_4_variant', count: 190, percentage: 15.2 },
];

export const mockInterRaterReliability: InterRaterReliability = {
  fleiss_kappa: 0.82,
  cohens_kappa: 0.79,
  agreement_percentage: 85.3,
  disagreement_details: {
    subtlety: 12,
    internal_structure: 8,
    calcification: 5,
    sphericity: 15,
    margin: 10,
    lobulation: 14,
    spiculation: 7,
    texture: 11,
    malignancy: 9,
  },
};

export const mockDataCompleteness: DataCompleteness = {
  total_records: 1247,
  complete_records: 1189,
  completeness_percentage: 95.3,
  missing_fields: {
    'nodule.subtlety': 12,
    'nodule.calcification': 8,
    'nodule.sphericity': 15,
    'nodule.margin': 6,
    'nodule.texture': 11,
    'session.service_date': 4,
    'reading.reader_id': 2,
  },
};

export const mockPYLIDCScans: PaginatedResponse<PYLIDCScan> = {
  items: [
    {
      scan_id: 'LIDC-IDRI-0001',
      patient_id: 'LIDC-IDRI-0001',
      study_instance_uid: '1.3.6.1.4.1.14519.5.2.1.6279.6001.298806137288633453246975630100',
      series_instance_uid: '1.3.6.1.4.1.14519.5.2.1.6279.6001.298806137288633453246975630178',
      slice_count: 133,
      slice_thickness: 2.5,
      slice_spacing: 2.5,
      pixel_spacing: [0.703125, 0.703125],
      contrast_used: false,
      annotation_count: 4,
      has_nodules: true,
    },
    {
      scan_id: 'LIDC-IDRI-0002',
      patient_id: 'LIDC-IDRI-0002',
      study_instance_uid: '1.3.6.1.4.1.14519.5.2.1.6279.6001.179049373636438705059720603100',
      series_instance_uid: '1.3.6.1.4.1.14519.5.2.1.6279.6001.179049373636438705059720603192',
      slice_count: 128,
      slice_thickness: 2.5,
      slice_spacing: 2.5,
      pixel_spacing: [0.683594, 0.683594],
      contrast_used: true,
      annotation_count: 3,
      has_nodules: true,
    },
    {
      scan_id: 'LIDC-IDRI-0003',
      patient_id: 'LIDC-IDRI-0003',
      study_instance_uid: '1.3.6.1.4.1.14519.5.2.1.6279.6001.101370605276577556143013894800',
      series_instance_uid: '1.3.6.1.4.1.14519.5.2.1.6279.6001.101370605276577556143013894866',
      slice_count: 116,
      slice_thickness: 2.5,
      slice_spacing: null,
      pixel_spacing: [0.664063, 0.664063],
      contrast_used: false,
      annotation_count: 2,
      has_nodules: true,
    },
  ],
  total: 1018,
  page: 1,
  page_size: 20,
  total_pages: 51,
};
