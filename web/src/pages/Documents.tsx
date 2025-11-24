/**
 * Documents Page - MAPS Document Management
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../services/api';
import type { DocumentSummary } from '../types/api';
import { CompactMatchIndicator } from '../components/AttributeMatchIndicator';

export default function Documents() {
  const [filters, setFilters] = useState({
    status: '',
    parse_case: '',
    search: '',
    limit: 50,
  });

  const { data: documents = [], isLoading } = useQuery({
    queryKey: ['documents', filters],
    queryFn: () => apiClient.getDocuments(filters),
  });

  const { data: stats } = useQuery({
    queryKey: ['documents-stats'],
    queryFn: () => apiClient.getDocumentsStats(),
  });

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      completed: 'bg-green-100 text-green-800',
      processing: 'bg-blue-100 text-blue-800',
      pending: 'bg-yellow-100 text-yellow-800',
      failed: 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Documents</h1>
          <p className="text-gray-600 mt-1">MAPS Document Management</p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Total Documents</div>
              <div className="text-2xl font-bold text-gray-900">{stats.total_documents}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Completed</div>
              <div className="text-2xl font-bold text-green-600">{stats.by_status?.completed || 0}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Processing</div>
              <div className="text-2xl font-bold text-blue-600">{stats.by_status?.processing || 0}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Failed</div>
              <div className="text-2xl font-bold text-red-600">{stats.by_status?.failed || 0}</div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input
              type="text"
              placeholder="Search documents..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Status</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
            <select
              value={filters.parse_case}
              onChange={(e) => setFilters({ ...filters, parse_case: e.target.value })}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Parse Cases</option>
              <option value="Complete_Attributes">Complete Attributes</option>
              <option value="LIDC_Single_Session">LIDC Single Session</option>
              <option value="LIDC_Multi_Session_2">LIDC Multi Session 2</option>
            </select>
          </div>
        </div>

        {/* Documents Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {isLoading ? (
            <div className="p-8 text-center text-gray-500">Loading documents...</div>
          ) : documents.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No documents found</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Filename</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Parse Case</th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Match</th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Keywords</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Uploaded</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {documents.map((doc: DocumentSummary) => (
                    <tr key={doc.id} className="hover:bg-gray-50 cursor-pointer transition-colors">
                      <td className="px-6 py-4 text-sm text-gray-900">
                        <div className="font-medium">{doc.filename}</div>
                        {doc.document_title && (
                          <div className="text-xs text-gray-500 mt-1">{doc.document_title}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                          {doc.parse_case || 'Unknown'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        {doc.confidence !== undefined && doc.confidence !== null && (
                          <CompactMatchIndicator matchPercentage={doc.confidence * 100} size={32} />
                        )}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(doc.status)}`}>
                          {doc.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center text-sm text-gray-900">
                        {doc.keywords_count}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {new Date(doc.uploaded_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
