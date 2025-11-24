/**
 * MAPS - PYLIDC Integration Page
 * 
 * Query PYLIDC database, select multiple scans, and import to Supabase
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import { useDebounce } from '../hooks/useDebounce';

export default function PYLIDC() {
  const [selectedScans, setSelectedScans] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [importing, setImporting] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  
  // Filter states - Basic
  const [patientIdFilter, setPatientIdFilter] = useState('');
  const [minSlices, setMinSlices] = useState<number | undefined>();
  const [maxSlices, setMaxSlices] = useState<number | undefined>();
  const [minThickness, setMinThickness] = useState<number | undefined>();
  const [maxThickness, setMaxThickness] = useState<number | undefined>();

  // Filter states - Scan Quality
  const [minSpacing, setMinSpacing] = useState<number | undefined>();
  const [maxSpacing, setMaxSpacing] = useState<number | undefined>();
  const [contrastUsed, setContrastUsed] = useState<boolean | undefined>();
  const [hasNodules, setHasNodules] = useState<boolean | undefined>();
  const [minAnnotations, setMinAnnotations] = useState<number | undefined>();
  const [maxAnnotations, setMaxAnnotations] = useState<number | undefined>();

  // Debounce expensive filters to reduce API calls
  const debouncedPatientId = useDebounce(patientIdFilter, 500);
  const debouncedSearchQuery = useDebounce(searchQuery, 500);

  // Filter states - Morphological Features (1-5 scale)
  const [minSubtlety, setMinSubtlety] = useState<number | undefined>();
  const [maxSubtlety, setMaxSubtlety] = useState<number | undefined>();
  const [minSphericity, setMinSphericity] = useState<number | undefined>();
  const [maxSphericity, setMaxSphericity] = useState<number | undefined>();
  const [minMargin, setMinMargin] = useState<number | undefined>();
  const [maxMargin, setMaxMargin] = useState<number | undefined>();
  const [minLobulation, setMinLobulation] = useState<number | undefined>();
  const [maxLobulation, setMaxLobulation] = useState<number | undefined>();
  const [minSpiculation, setMinSpiculation] = useState<number | undefined>();
  const [maxSpiculation, setMaxSpiculation] = useState<number | undefined>();

  // Filter states - Clinical Assessment
  const [minMalignancy, setMinMalignancy] = useState<number | undefined>();
  const [maxMalignancy, setMaxMalignancy] = useState<number | undefined>();

  // Filter states - Internal Structure
  const [minTexture, setMinTexture] = useState<number | undefined>();
  const [maxTexture, setMaxTexture] = useState<number | undefined>();
  const [calcification, setCalcification] = useState<number | undefined>();

  // Filter states - Nodule Size
  const [minDiameter, setMinDiameter] = useState<number | undefined>();
  const [maxDiameter, setMaxDiameter] = useState<number | undefined>();

  // UI states
  const [sortBy, setSortBy] = useState<'scan_id' | 'patient_id' | 'slice_count' | 'slice_thickness'>('scan_id');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['basic']));
  
  const queryClient = useQueryClient();

  // Fetch PYLIDC scans with debounced filters
  const { data: scansData, isLoading, error, isFetching } = useQuery({
    queryKey: ['pylidc-scans', page, debouncedSearchQuery, debouncedPatientId, minSlices, maxSlices, minThickness, maxThickness,
      minSpacing, maxSpacing, contrastUsed, hasNodules, minAnnotations, maxAnnotations,
      minSubtlety, maxSubtlety, minSphericity, maxSphericity, minMargin, maxMargin,
      minLobulation, maxLobulation, minSpiculation, maxSpiculation, minMalignancy, maxMalignancy,
      minTexture, maxTexture, calcification, minDiameter, maxDiameter, sortBy, sortOrder],
    queryFn: () => apiClient.getPYLIDCScans({
      page,
      page_size: 30,
      patient_id: debouncedPatientId || undefined,
      min_slices: minSlices,
      max_slices: maxSlices,
      min_thickness: minThickness,
      max_thickness: maxThickness,
      min_spacing: minSpacing,
      max_spacing: maxSpacing,
      contrast_used: contrastUsed,
      has_nodules: hasNodules,
      min_annotations: minAnnotations,
      max_annotations: maxAnnotations,
      min_subtlety: minSubtlety,
      max_subtlety: maxSubtlety,
      min_sphericity: minSphericity,
      max_sphericity: maxSphericity,
      min_margin: minMargin,
      max_margin: maxMargin,
      min_lobulation: minLobulation,
      max_lobulation: maxLobulation,
      min_spiculation: minSpiculation,
      max_spiculation: maxSpiculation,
      min_malignancy: minMalignancy,
      max_malignancy: maxMalignancy,
      min_texture: minTexture,
      max_texture: maxTexture,
      calcification: calcification,
      min_diameter: minDiameter,
      max_diameter: maxDiameter,
    }),
    retry: false,
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
    cacheTime: 10 * 60 * 1000, // Keep in cache for 10 minutes
  });

  // Prefetch next page for instant navigation
  const queryClient = useQueryClient();
  
  useEffect(() => {
    if (page < (scansData?.total_pages || 1)) {
      queryClient.prefetchQuery({
        queryKey: ['pylidc-scans', page + 1, debouncedSearchQuery, debouncedPatientId, minSlices, maxSlices, minThickness, maxThickness,
          minSpacing, maxSpacing, contrastUsed, hasNodules, minAnnotations, maxAnnotations,
          minSubtlety, maxSubtlety, minSphericity, maxSphericity, minMargin, maxMargin,
          minLobulation, maxLobulation, minSpiculation, maxSpiculation, minMalignancy, maxMalignancy,
          minTexture, maxTexture, calcification, minDiameter, maxDiameter, sortBy, sortOrder],
        queryFn: () => apiClient.getPYLIDCScans({
          page: page + 1,
          page_size: 30,
          patient_id: debouncedPatientId || undefined,
          min_slices: minSlices,
          max_slices: maxSlices,
          min_thickness: minThickness,
          max_thickness: maxThickness,
          min_spacing: minSpacing,
          max_spacing: maxSpacing,
          contrast_used: contrastUsed,
          has_nodules: hasNodules,
          min_annotations: minAnnotations,
          max_annotations: maxAnnotations,
          min_subtlety: minSubtlety,
          max_subtlety: maxSubtlety,
          min_sphericity: minSphericity,
          max_sphericity: maxSphericity,
          min_margin: minMargin,
          max_margin: maxMargin,
          min_lobulation: minLobulation,
          max_lobulation: maxLobulation,
          min_spiculation: minSpiculation,
          max_spiculation: maxSpiculation,
          min_malignancy: minMalignancy,
          max_malignancy: maxMalignancy,
          min_texture: minTexture,
          max_texture: maxTexture,
          calcification: calcification,
          min_diameter: minDiameter,
          max_diameter: maxDiameter,
        }),
      });
    }
  }, [page, scansData?.total_pages, queryClient, debouncedSearchQuery, debouncedPatientId, minSlices, maxSlices, minThickness, maxThickness]);

  const scans: PYLIDCScan[] = scansData?.items || [];
  const totalPages = scansData?.total_pages || 1;

  // Loading skeleton component
  const LoadingSkeleton = () => (
    <div className="animate-pulse space-y-4">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="h-4 bg-gray-200 rounded w-20"></div>
          </div>
          <div className="grid grid-cols-4 gap-4">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded"></div>
          </div>
        </div>
      ))}
    </div>
  );

  // Import mutation
  const importMutation = useMutation({
    mutationFn: async (scanIds: string[]) => {
      const results = [];
      for (const scanId of scanIds) {
        try {
          const result = await apiClient.importPYLIDCScan(scanId);
          results.push({ scanId, success: true, result });
        } catch (error) {
          results.push({ scanId, success: false, error });
        }
      }
      return results;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pylidc-scans'] });
      setSelectedScans([]);
      setImporting(false);
    },
  });

  const handleSelectScan = (scanId: string) => {
    setSelectedScans(prev => 
      prev.includes(scanId) 
        ? prev.filter(id => id !== scanId)
        : [...prev, scanId]
    );
  };

  const handleSelectAll = () => {
    if (selectedScans.length === scans.length) {
      setSelectedScans([]);
    } else {
      setSelectedScans(scans.map(s => s.scan_id));
    }
  };

  const handleImport = async () => {
    if (selectedScans.length === 0) return;
    
    const confirmed = window.confirm(
      `Import ${selectedScans.length} scan(s) to database? This may take several minutes.`
    );
    
    if (confirmed) {
      setImporting(true);
      importMutation.mutate(selectedScans);
    }
  };

  // Client-side search filtering
  const filteredScans = searchQuery
    ? scans.filter(scan => 
        scan.scan_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        scan.patient_id.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : scans;

  // Client-side sorting
  const sortedScans = [...filteredScans].sort((a, b) => {
    let aVal: any = a[sortBy];
    let bVal: any = b[sortBy];
    
    if (typeof aVal === 'string') {
      return sortOrder === 'asc' 
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal);
    } else {
      return sortOrder === 'asc' 
        ? aVal - bVal
        : bVal - aVal;
    }
  });

  const clearFilters = () => {
    setSearchQuery('');
    setPatientIdFilter('');
    setMinSlices(undefined);
    setMaxSlices(undefined);
    setMinThickness(undefined);
    setMaxThickness(undefined);
    setMinSpacing(undefined);
    setMaxSpacing(undefined);
    setContrastUsed(undefined);
    setHasNodules(undefined);
    setMinAnnotations(undefined);
    setMaxAnnotations(undefined);
    setMinSubtlety(undefined);
    setMaxSubtlety(undefined);
    setMinSphericity(undefined);
    setMaxSphericity(undefined);
    setMinMargin(undefined);
    setMaxMargin(undefined);
    setMinLobulation(undefined);
    setMaxLobulation(undefined);
    setMinSpiculation(undefined);
    setMaxSpiculation(undefined);
    setMinMalignancy(undefined);
    setMaxMalignancy(undefined);
    setMinTexture(undefined);
    setMaxTexture(undefined);
    setCalcification(undefined);
    setMinDiameter(undefined);
    setMaxDiameter(undefined);
    setSortBy('scan_id');
    setSortOrder('asc');
  };

  // Helper to count active filters
  const getActiveFiltersCount = () => {
    let count = 0;
    if (patientIdFilter) count++;
    if (minSlices !== undefined || maxSlices !== undefined) count++;
    if (minThickness !== undefined || maxThickness !== undefined) count++;
    if (minSpacing !== undefined || maxSpacing !== undefined) count++;
    if (contrastUsed !== undefined) count++;
    if (hasNodules !== undefined) count++;
    if (minAnnotations !== undefined || maxAnnotations !== undefined) count++;
    if (minSubtlety !== undefined || maxSubtlety !== undefined) count++;
    if (minSphericity !== undefined || maxSphericity !== undefined) count++;
    if (minMargin !== undefined || maxMargin !== undefined) count++;
    if (minLobulation !== undefined || maxLobulation !== undefined) count++;
    if (minSpiculation !== undefined || maxSpiculation !== undefined) count++;
    if (minMalignancy !== undefined || maxMalignancy !== undefined) count++;
    if (minTexture !== undefined || maxTexture !== undefined) count++;
    if (calcification !== undefined) count++;
    if (minDiameter !== undefined || maxDiameter !== undefined) count++;
    return count;
  };

  // Helper to toggle section expansion
  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  };

  // Filter presets
  const applyPreset = (presetName: string) => {
    clearFilters();
    setShowFilters(true);

    switch (presetName) {
      case 'suspicious':
        // High malignancy with spiculation
        setMinMalignancy(4);
        setMinSpiculation(3);
        setHasNodules(true);
        break;
      case 'ground-glass':
        // Ground-glass opacities (low texture, low malignancy)
        setMaxTexture(2);
        setMaxMalignancy(2);
        setHasNodules(true);
        break;
      case 'high-quality':
        // High quality scans (thin slices with contrast)
        setMaxThickness(1.5);
        setContrastUsed(true);
        setMinSlices(100);
        break;
      case 'calcified':
        // Scans with calcified nodules
        setCalcification(1); // Start with popcorn, user can change
        setHasNodules(true);
        break;
      case 'large-nodules':
        // Large nodules (>10mm)
        setMinDiameter(10);
        setHasNodules(true);
        break;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">PYLIDC Integration</h1>
        <p className="text-gray-600 mt-2">
          Query PYLIDC database, select scans, and import to MAPS
        </p>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div className="flex-1 text-sm text-blue-800">
            <p className="font-medium mb-1">About PYLIDC Integration</p>
            <p>Import CT scans and annotations from the LIDC-IDRI dataset. Each scan includes multiple radiologist annotations with nodule characteristics.</p>
          </div>
        </div>
      </div>

      {/* Filter Presets */}
      <div className="bg-white p-4 rounded-lg shadow mb-4">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-gray-700">Quick Filters:</span>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => applyPreset('suspicious')}
              className="px-3 py-1 text-sm bg-red-50 text-red-700 border border-red-200 rounded-md hover:bg-red-100 transition-colors"
            >
              Suspicious Nodules
            </button>
            <button
              onClick={() => applyPreset('ground-glass')}
              className="px-3 py-1 text-sm bg-yellow-50 text-yellow-700 border border-yellow-200 rounded-md hover:bg-yellow-100 transition-colors"
            >
              Ground-Glass Opacities
            </button>
            <button
              onClick={() => applyPreset('high-quality')}
              className="px-3 py-1 text-sm bg-green-50 text-green-700 border border-green-200 rounded-md hover:bg-green-100 transition-colors"
            >
              High-Quality Scans
            </button>
            <button
              onClick={() => applyPreset('calcified')}
              className="px-3 py-1 text-sm bg-purple-50 text-purple-700 border border-purple-200 rounded-md hover:bg-purple-100 transition-colors"
            >
              Calcified Nodules
            </button>
            <button
              onClick={() => applyPreset('large-nodules')}
              className="px-3 py-1 text-sm bg-blue-50 text-blue-700 border border-blue-200 rounded-md hover:bg-blue-100 transition-colors"
            >
              Large Nodules (&gt;10mm)
            </button>
          </div>
        </div>
      </div>

      {/* Search and Actions */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <div className="flex flex-col gap-4">
          {/* Top Row: Search and Actions */}
          <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
            <div className="flex-1 w-full md:w-auto">
              <input
                type="text"
                placeholder="Search by Scan ID or Patient ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <div className="flex gap-2 w-full md:w-auto">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`flex-1 md:flex-none px-4 py-2 border rounded-lg transition-colors ${
                  showFilters ? 'bg-blue-50 border-blue-500 text-blue-700' : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                <span className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                  </svg>
                  Filters
                  {getActiveFiltersCount() > 0 && (
                    <span className="bg-blue-600 text-white text-xs font-bold rounded-full px-2 py-0.5">
                      {getActiveFiltersCount()}
                    </span>
                  )}
                </span>
              </button>
              <button
                onClick={handleSelectAll}
                className="flex-1 md:flex-none px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                {selectedScans.length === scans.length ? 'Deselect All' : 'Select All'}
              </button>
              <button
                onClick={handleImport}
                disabled={selectedScans.length === 0 || importing}
                className="flex-1 md:flex-none px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {importing ? 'Importing...' : `Import Selected (${selectedScans.length})`}
              </button>
            </div>
          </div>

          {/* Advanced Filters Panel */}
          {showFilters && (
            <div className="border-t pt-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Patient ID Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Patient ID</label>
                  <input
                    type="text"
                    placeholder="Filter by patient ID..."
                    value={patientIdFilter}
                    onChange={(e) => setPatientIdFilter(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  />
                </div>

                {/* Slice Count Range */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Slice Count Range</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      placeholder="Min"
                      value={minSlices || ''}
                      onChange={(e) => setMinSlices(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    />
                    <input
                      type="number"
                      placeholder="Max"
                      value={maxSlices || ''}
                      onChange={(e) => setMaxSlices(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    />
                  </div>
                </div>

                {/* Slice Thickness Range */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Slice Thickness (mm)</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      step="0.1"
                      placeholder="Min"
                      value={minThickness || ''}
                      onChange={(e) => setMinThickness(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    />
                    <input
                      type="number"
                      step="0.1"
                      placeholder="Max"
                      value={maxThickness || ''}
                      onChange={(e) => setMaxThickness(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    />
                  </div>
                </div>

                {/* Has Nodules Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Has Nodules</label>
                  <select
                    value={hasNodules === undefined ? '' : hasNodules ? 'yes' : 'no'}
                    onChange={(e) => setHasNodules(e.target.value === '' ? undefined : e.target.value === 'yes')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  >
                    <option value="">All</option>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                  </select>
                </div>

                {/* Slice Spacing Range */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Slice Spacing (mm)</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      step="0.1"
                      placeholder="Min"
                      value={minSpacing || ''}
                      onChange={(e) => setMinSpacing(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <input
                      type="number"
                      step="0.1"
                      placeholder="Max"
                      value={maxSpacing || ''}
                      onChange={(e) => setMaxSpacing(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                  </div>
                </div>

                {/* Contrast Used */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Contrast Used</label>
                  <select
                    value={contrastUsed === undefined ? '' : contrastUsed ? 'yes' : 'no'}
                    onChange={(e) => setContrastUsed(e.target.value === '' ? undefined : e.target.value === 'yes')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                  >
                    <option value="">All</option>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                  </select>
                </div>

                {/* Annotation Count */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Annotation Count</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      placeholder="Min"
                      value={minAnnotations || ''}
                      onChange={(e) => setMinAnnotations(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <input
                      type="number"
                      placeholder="Max"
                      value={maxAnnotations || ''}
                      onChange={(e) => setMaxAnnotations(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                  </div>
                </div>

                {/* Malignancy */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Malignancy (1-5)</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      min="1"
                      max="5"
                      placeholder="Min"
                      value={minMalignancy || ''}
                      onChange={(e) => setMinMalignancy(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <input
                      type="number"
                      min="1"
                      max="5"
                      placeholder="Max"
                      value={maxMalignancy || ''}
                      onChange={(e) => setMaxMalignancy(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                  </div>
                </div>

                {/* Subtlety */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Subtlety (1-5)</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      min="1"
                      max="5"
                      placeholder="Min"
                      value={minSubtlety || ''}
                      onChange={(e) => setMinSubtlety(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <input
                      type="number"
                      min="1"
                      max="5"
                      placeholder="Max"
                      value={maxSubtlety || ''}
                      onChange={(e) => setMaxSubtlety(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                  </div>
                </div>

                {/* Sphericity */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sphericity (1-5)</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      min="1"
                      max="5"
                      placeholder="Min"
                      value={minSphericity || ''}
                      onChange={(e) => setMinSphericity(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <input
                      type="number"
                      min="1"
                      max="5"
                      placeholder="Max"
                      value={maxSphericity || ''}
                      onChange={(e) => setMaxSphericity(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                  </div>
                </div>

                {/* Margin */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Margin (1-5)</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      min="1"
                      max="5"
                      placeholder="Min"
                      value={minMargin || ''}
                      onChange={(e) => setMinMargin(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <input
                      type="number"
                      min="1"
                      max="5"
                      placeholder="Max"
                      value={maxMargin || ''}
                      onChange={(e) => setMaxMargin(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                  </div>
                </div>

                {/* Lobulation */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Lobulation (1-5)</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      min="1"
                      max="5"
                      placeholder="Min"
                      value={minLobulation || ''}
                      onChange={(e) => setMinLobulation(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <input
                      type="number"
                      min="1"
                      max="5"
                      placeholder="Max"
                      value={maxLobulation || ''}
                      onChange={(e) => setMaxLobulation(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                  </div>
                </div>

                {/* Spiculation */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Spiculation (1-5)</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      min="1"
                      max="5"
                      placeholder="Min"
                      value={minSpiculation || ''}
                      onChange={(e) => setMinSpiculation(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <input
                      type="number"
                      min="1"
                      max="5"
                      placeholder="Max"
                      value={maxSpiculation || ''}
                      onChange={(e) => setMaxSpiculation(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                  </div>
                </div>

                {/* Texture */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Texture (1-5)</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      min="1"
                      max="5"
                      placeholder="Min"
                      value={minTexture || ''}
                      onChange={(e) => setMinTexture(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <input
                      type="number"
                      min="1"
                      max="5"
                      placeholder="Max"
                      value={maxTexture || ''}
                      onChange={(e) => setMaxTexture(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                  </div>
                </div>

                {/* Calcification */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Calcification Type</label>
                  <select
                    value={calcification || ''}
                    onChange={(e) => setCalcification(e.target.value ? Number(e.target.value) : undefined)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                  >
                    <option value="">All</option>
                    <option value="1">1 - Popcorn</option>
                    <option value="2">2 - Laminated</option>
                    <option value="3">3 - Solid</option>
                    <option value="4">4 - Non-central</option>
                    <option value="5">5 - Central</option>
                    <option value="6">6 - Absent</option>
                  </select>
                </div>

                {/* Diameter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nodule Diameter (mm)</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      step="0.1"
                      placeholder="Min"
                      value={minDiameter || ''}
                      onChange={(e) => setMinDiameter(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <input
                      type="number"
                      step="0.1"
                      placeholder="Max"
                      value={maxDiameter || ''}
                      onChange={(e) => setMaxDiameter(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                  </div>
                </div>

                {/* Sort By */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as any)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  >
                    <option value="scan_id">Scan ID</option>
                    <option value="patient_id">Patient ID</option>
                    <option value="slice_count">Slice Count</option>
                    <option value="slice_thickness">Slice Thickness</option>
                  </select>
                </div>

                {/* Sort Order */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sort Order</label>
                  <select
                    value={sortOrder}
                    onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  >
                    <option value="asc">Ascending</option>
                    <option value="desc">Descending</option>
                  </select>
                </div>
              </div>

              {/* Clear Filters Button */}
              <div className="mt-4 flex justify-end">
                <button
                  onClick={clearFilters}
                  className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 font-medium"
                >
                  Clear All Filters
                </button>
              </div>
            </div>
          )}
        </div>

        {selectedScans.length > 0 && !importing && (
          <div className="mt-3 flex items-center justify-between">
            <div className="text-sm text-gray-600">
              {selectedScans.length} scan(s) selected for import
            </div>
            <div className="flex gap-2">
              <button
                onClick={async () => {
                  try {
                    const selectedScanData = sortedScans.filter(s => selectedScans.includes(s.scan_id));
                    const data = JSON.stringify(selectedScanData, null, 2);
                    const blob = new Blob([data], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `pylidc_selected_${selectedScans.length}_scans.json`;
                    a.click();
                  } catch (error) {
                    alert(`Export failed: ${error}`);
                  }
                }}
                className="px-3 py-1 text-sm border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
              >
                Export JSON
              </button>
              <button
                onClick={async () => {
                  try {
                    const selectedScanData = sortedScans.filter(s => selectedScans.includes(s.scan_id));
                    const csv = [
                      ['Scan ID', 'Patient ID', 'Series UID', 'Slice Count', 'Slice Thickness', 'Contrast Used', 'Annotations', 'Has Nodules'],
                      ...selectedScanData.map(s => [
                        s.scan_id,
                        s.patient_id,
                        s.series_instance_uid,
                        s.slice_count.toString(),
                        s.slice_thickness.toFixed(2),
                        s.contrast_used ? 'Yes' : 'No',
                        s.annotation_count.toString(),
                        s.has_nodules ? 'Yes' : 'No'
                      ])
                    ].map(row => row.join(',')).join('\n');
                    
                    const blob = new Blob([csv], { type: 'text/csv' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `pylidc_selected_${selectedScans.length}_scans.csv`;
                    a.click();
                  } catch (error) {
                    alert(`Export failed: ${error}`);
                  }
                }}
                className="px-3 py-1 text-sm border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
              >
                Export CSV
              </button>
            </div>
          </div>
        )}

        {importing && (
          <div className="mt-3">
            <div className="flex items-center gap-2 text-sm text-blue-600">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              Importing scans... This may take several minutes.
            </div>
          </div>
        )}
      </div>

      {/* Import Progress/Results */}
      {importMutation.data && (
        <div className="bg-white rounded-lg shadow mb-6 p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Import Results</h3>
          <div className="space-y-2">
            {importMutation.data.map((result, idx) => (
              <div
                key={idx}
                className={`flex items-center justify-between p-3 rounded ${
                  result.success ? 'bg-green-50' : 'bg-red-50'
                }`}
              >
                <span className="font-mono text-sm">{result.scanId}</span>
                <span className={`text-sm font-medium ${
                  result.success ? 'text-green-700' : 'text-red-700'
                }`}>
                  {result.success ? '✓ Imported' : '✗ Failed'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Scans List */}
      {isLoading ? (
        <div className="bg-white rounded-lg shadow p-6">
          <LoadingSkeleton />
        </div>
      ) : isFetching && !isLoading ? (
        <div className="bg-white rounded-lg shadow p-6 relative">
          <div className="absolute top-4 right-4 flex items-center gap-2 text-sm text-blue-600">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            Updating...
          </div>
          <LoadingSkeleton />
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
          Error loading scans: {error instanceof Error ? error.message : 'Unknown error'}
        </div>
      ) : sortedScans.length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow text-center text-gray-600">
          {searchQuery || getActiveFiltersCount() > 0
            ? 'No scans found matching your filters.'
            : 'No scans available.'}
        </div>
      ) : (
        <>
          {/* Total Results Count */}
          {getActiveFiltersCount() > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-blue-800">
                <span className="font-semibold">{scansData?.total || 0} scan(s)</span> match your filter criteria
              </p>
            </div>
          )}

          {/* Stats Summary */}
          <div className="bg-white p-4 rounded-lg shadow mb-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{sortedScans.length}</div>
                <div className="text-sm text-gray-600">Total Scans</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{selectedScans.length}</div>
                <div className="text-sm text-gray-600">Selected</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {Math.round(sortedScans.reduce((sum, s) => sum + s.slice_count, 0) / sortedScans.length) || 0}
                </div>
                <div className="text-sm text-gray-600">Avg Slices</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {(sortedScans.reduce((sum, s) => sum + s.slice_thickness, 0) / sortedScans.length).toFixed(2) || 0}
                </div>
                <div className="text-sm text-gray-600">Avg Thickness</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left">
                      <input
                        type="checkbox"
                        checked={selectedScans.length === scans.length && scans.length > 0}
                        onChange={handleSelectAll}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                      />
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                        onClick={() => {
                          setSortBy('scan_id');
                          setSortOrder(sortBy === 'scan_id' && sortOrder === 'asc' ? 'desc' : 'asc');
                        }}>
                      Scan ID {sortBy === 'scan_id' && (sortOrder === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                        onClick={() => {
                          setSortBy('patient_id');
                          setSortOrder(sortBy === 'patient_id' && sortOrder === 'asc' ? 'desc' : 'asc');
                        }}>
                      Patient ID {sortBy === 'patient_id' && (sortOrder === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Series UID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                        onClick={() => {
                          setSortBy('slice_count');
                          setSortOrder(sortBy === 'slice_count' && sortOrder === 'asc' ? 'desc' : 'asc');
                        }}>
                      Slices {sortBy === 'slice_count' && (sortOrder === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                        onClick={() => {
                          setSortBy('slice_thickness');
                          setSortOrder(sortBy === 'slice_thickness' && sortOrder === 'asc' ? 'desc' : 'asc');
                        }}>
                      Thickness {sortBy === 'slice_thickness' && (sortOrder === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Contrast
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Annotations
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {sortedScans.map((scan) => (
                    <tr
                      key={scan.scan_id}
                      className={`hover:bg-gray-50 ${
                        selectedScans.includes(scan.scan_id) ? 'bg-blue-50' : ''
                      }`}
                    >
                      <td className="px-6 py-4">
                        <input
                          type="checkbox"
                          checked={selectedScans.includes(scan.scan_id)}
                          onChange={() => handleSelectScan(scan.scan_id)}
                          className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900 font-mono">
                          {scan.scan_id}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{scan.patient_id}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-500 truncate max-w-xs" title={scan.series_instance_uid}>
                          {scan.series_instance_uid}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{scan.slice_count}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {scan.slice_thickness.toFixed(2)}mm
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm">
                          {scan.contrast_used ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">Yes</span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">No</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {scan.annotation_count > 0 ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">{scan.annotation_count}</span>
                          ) : (
                            <span className="text-gray-400">0</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div className="flex gap-2">
                          <button
                            onClick={async () => {
                              try {
                                await apiClient.importPYLIDCScan(scan.scan_id);
                                queryClient.invalidateQueries({ queryKey: ['pylidc-scans'] });
                                alert(`Successfully imported ${scan.scan_id}`);
                              } catch (error) {
                                alert(`Failed to import: ${error}`);
                              }
                            }}
                            className="text-green-600 hover:text-green-800 font-medium"
                          >
                            Import
                          </button>
                          <span className="text-gray-300">|</span>
                          <button
                            onClick={() => {
                              // Navigate to detail view
                              window.location.href = `/pylidc/${scan.scan_id}`;
                            }}
                            className="text-blue-600 hover:text-blue-800 font-medium"
                          >
                            Details
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-between bg-white px-4 py-3 rounded-lg shadow">
              <div className="flex-1 flex justify-between sm:hidden">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    Page <span className="font-medium">{page}</span> of{' '}
                    <span className="font-medium">{totalPages}</span>
                  </p>
                </div>
                <div>
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                    <button
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <span className="sr-only">Previous</span>
                      ‹
                    </button>
                    
                    {/* Page numbers */}
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      let pageNum;
                      if (totalPages <= 5) {
                        pageNum = i + 1;
                      } else if (page <= 3) {
                        pageNum = i + 1;
                      } else if (page >= totalPages - 2) {
                        pageNum = totalPages - 4 + i;
                      } else {
                        pageNum = page - 2 + i;
                      }
                      
                      return (
                        <button
                          key={i}
                          onClick={() => setPage(pageNum)}
                          className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                            page === pageNum
                              ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                              : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                          }`}
                        >
                          {pageNum}
                        </button>
                      );
                    })}
                    
                    <button
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <span className="sr-only">Next</span>
                      ›
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
