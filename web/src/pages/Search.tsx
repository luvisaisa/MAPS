/**
 * MAPS - Advanced Search Page
 * 
 * Full-text search across processed documents with filters
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import type { SearchFilters } from '../types/api';

export default function Search() {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>({});
  const [submitted, setSubmitted] = useState(false);

  const { data: results, isLoading, error } = useQuery({
    queryKey: ['search', query, filters],
    queryFn: () => apiClient.advancedSearch(query, filters),
    enabled: submitted && query.length >= 2,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  const handleFilterChange = (key: keyof SearchFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Advanced Search</h1>
        <p className="text-gray-600 mt-2">
          Search across all processed documents with advanced filters
        </p>
      </div>

      {/* Search Form */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <form onSubmit={handleSearch}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search Query
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter search terms..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Filters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Date From
              </label>
              <input
                type="date"
                value={filters.date_from || ''}
                onChange={(e) => handleFilterChange('date_from', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Date To
              </label>
              <input
                type="date"
                value={filters.date_to || ''}
                onChange={(e) => handleFilterChange('date_to', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Has Keywords
              </label>
              <select
                value={filters.has_keywords ? 'yes' : 'no'}
                onChange={(e) => handleFilterChange('has_keywords', e.target.value === 'yes')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Any</option>
                <option value="yes">Yes</option>
                <option value="no">No</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={query.length < 2}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            Search
          </button>
        </form>
      </div>

      {/* Results */}
      {isLoading && (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Searching...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
          Error: {error instanceof Error ? error.message : 'Search failed'}
        </div>
      )}

      {results && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 bg-gray-50 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h2 className="font-semibold text-gray-900">
                {results.total} results found
              </h2>
              <span className="text-sm text-gray-600">
                {results.took_ms}ms
              </span>
            </div>
          </div>

          <div className="divide-y divide-gray-200">
            {results.results.length === 0 ? (
              <div className="p-8 text-center text-gray-600">
                No results found. Try different search terms or filters.
              </div>
            ) : (
              results.results.map((result) => (
                <div key={result.document_id} className="p-4 hover:bg-gray-50">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-medium text-gray-900 text-lg">
                      {result.title}
                    </h3>
                    <span className="text-sm text-gray-500 ml-4">
                      Score: {result.score.toFixed(2)}
                    </span>
                  </div>
                  <p className="text-gray-700 mb-2">{result.snippet}</p>
                  {result.highlights.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {result.highlights.map((highlight, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-yellow-100 text-yellow-800 text-sm rounded"
                          dangerouslySetInnerHTML={{ __html: highlight }}
                        />
                      ))}
                    </div>
                  )}
                  <div className="mt-2 text-sm text-gray-600">
                    ID: {result.document_id}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
