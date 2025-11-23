/**
 * MAPS - Keywords Page
 * 
 * Search, browse, and manage medical terminology keywords
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import type { Keyword, KeywordDirectory } from '../types/api';

export default function Keywords() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');

  // Fetch keyword directory
  const { data: directory, isLoading: directoryLoading } = useQuery({
    queryKey: ['keyword-directory'],
    queryFn: () => apiClient.getKeywordDirectory(),
  });

  // Search keywords
  const { data: searchResults, isLoading: searchLoading } = useQuery({
    queryKey: ['keyword-search', searchTerm],
    queryFn: () => apiClient.searchKeywords(searchTerm),
    enabled: searchTerm.length >= 2,
  });

  // Get keywords by category
  const { data: keywords, isLoading: keywordsLoading } = useQuery({
    queryKey: ['keywords', selectedCategory],
    queryFn: () => apiClient.getKeywords({ category: selectedCategory, limit: 100 }),
    enabled: !searchTerm && !!selectedCategory,
  });

  const categories = directory?.categories ? Object.keys(directory.categories) : [];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Medical Keywords</h1>
        <p className="text-gray-600 mt-2">
          Search and browse extracted medical terminology from processed documents
        </p>
      </div>

      {/* Stats Cards */}
      {directory && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-600">Total Keywords</div>
            <div className="text-2xl font-bold text-blue-600">{directory.total_keywords}</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-600">Categories</div>
            <div className="text-2xl font-bold text-green-600">{directory.total_categories}</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-600">Unique Terms</div>
            <div className="text-2xl font-bold text-purple-600">
              {Object.values(directory.categories).flat().length}
            </div>
          </div>
        </div>
      )}

      {/* Search Bar */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <div className="flex gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search keywords..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => {
              setSelectedCategory(e.target.value);
              setSearchTerm('');
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Results */}
      <div className="bg-white rounded-lg shadow">
        {searchLoading || keywordsLoading || directoryLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading keywords...</p>
          </div>
        ) : searchTerm && searchResults ? (
          <div className="divide-y divide-gray-200">
            <div className="p-4 bg-gray-50">
              <h2 className="font-semibold text-gray-900">
                Search Results ({searchResults.length})
              </h2>
            </div>
            {searchResults.map((result, idx) => (
              <div key={idx} className="p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{result.keyword.term}</h3>
                    {result.keyword.canonical_term !== result.keyword.term && (
                      <p className="text-sm text-gray-600">
                        → {result.keyword.canonical_term}
                      </p>
                    )}
                    {result.keyword.category && (
                      <span className="inline-block mt-1 px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                        {result.keyword.category}
                      </span>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-600">Frequency</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {result.keyword.frequency}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : keywords ? (
          <div className="divide-y divide-gray-200">
            <div className="p-4 bg-gray-50">
              <h2 className="font-semibold text-gray-900">
                {selectedCategory || 'All Keywords'} ({keywords.length})
              </h2>
            </div>
            {keywords.map((keyword) => (
              <KeywordItem key={keyword.id} keyword={keyword} />
            ))}
          </div>
        ) : directory ? (
          <div className="p-4">
            <h2 className="font-semibold text-gray-900 mb-4">Browse by Category</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className="p-4 border border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 text-left"
                >
                  <h3 className="font-medium text-gray-900">{cat}</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {directory.categories[cat]?.length || 0} keywords
                  </p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-8 text-center text-gray-600">
            No keywords found. Process some documents first.
          </div>
        )}
      </div>
    </div>
  );
}

function KeywordItem({ keyword }: { keyword: Keyword }) {
  return (
    <div className="p-4 hover:bg-gray-50">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="font-medium text-gray-900">{keyword.term}</h3>
          {keyword.canonical_term !== keyword.term && (
            <p className="text-sm text-gray-600">
              Canonical: {keyword.canonical_term}
            </p>
          )}
          {keyword.category && (
            <span className="inline-block mt-1 px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
              {keyword.category}
            </span>
          )}
          {keyword.source && (
            <p className="text-xs text-gray-500 mt-1">Source: {keyword.source}</p>
          )}
        </div>
        <div className="text-right ml-4">
          <div className="text-sm text-gray-600">Frequency</div>
          <div className="text-lg font-semibold text-gray-900">{keyword.frequency}</div>
          {keyword.confidence && (
            <div className="text-xs text-gray-500">
              Confidence: {(keyword.confidence * 100).toFixed(1)}%
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
