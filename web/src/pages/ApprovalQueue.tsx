import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import type { QueueItem, QueueStats, ApprovalRequest } from '../types/api';

export function ApprovalQueue() {
  const [statusFilter, setStatusFilter] = useState<'pending' | 'approved' | 'rejected' | 'all'>('pending');
  const [minConfidence, setMinConfidence] = useState<number>(0);
  const [maxConfidence, setMaxConfidence] = useState<number>(1);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [reviewingItem, setReviewingItem] = useState<QueueItem | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [overrideParseCase, setOverrideParseCase] = useState('');
  const queryClient = useQueryClient();

  // Fetch queue statistics
  const { data: stats } = useQuery({
    queryKey: ['queue-stats'],
    queryFn: () => apiClient.getQueueStats(),
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Fetch queue items
  const { data: items = [], isLoading, error } = useQuery({
    queryKey: ['queue-items', statusFilter, minConfidence, maxConfidence],
    queryFn: () => apiClient.getQueueItems({
      status: statusFilter === 'all' ? undefined : statusFilter,
      min_confidence: minConfidence,
      max_confidence: maxConfidence,
      limit: 1000,
    }),
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  // Review mutation
  const reviewMutation = useMutation({
    mutationFn: ({ itemId, request }: { itemId: string; request: ApprovalRequest }) =>
      apiClient.reviewQueueItem(itemId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queue-items'] });
      queryClient.invalidateQueries({ queryKey: ['queue-stats'] });
      setReviewingItem(null);
      setReviewNotes('');
      setOverrideParseCase('');
    },
  });

  // Batch review mutation
  const batchReviewMutation = useMutation({
    mutationFn: ({ itemIds, action }: { itemIds: string[]; action: 'approve' | 'reject' }) =>
      apiClient.batchReviewQueueItems(itemIds, action, 'user'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queue-items'] });
      queryClient.invalidateQueries({ queryKey: ['queue-stats'] });
      setSelectedItems(new Set());
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (itemId: string) => apiClient.deleteQueueItem(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queue-items'] });
      queryClient.invalidateQueries({ queryKey: ['queue-stats'] });
    },
  });

  const handleReview = (action: 'approve' | 'reject') => {
    if (!reviewingItem) return;

    const request: ApprovalRequest = {
      action,
      notes: reviewNotes || undefined,
      parse_case: overrideParseCase || undefined,
      reviewed_by: 'user',
    };

    reviewMutation.mutate({ itemId: reviewingItem.id, request });
  };

  const handleBatchReview = (action: 'approve' | 'reject') => {
    if (selectedItems.size === 0) return;
    if (!window.confirm(`Are you sure you want to ${action} ${selectedItems.size} items?`)) return;

    batchReviewMutation.mutate({ itemIds: Array.from(selectedItems), action });
  };

  const toggleSelectItem = (itemId: string) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(itemId)) {
      newSelected.delete(itemId);
    } else {
      newSelected.add(itemId);
    }
    setSelectedItems(newSelected);
  };

  const selectAll = () => {
    const pendingItems = items.filter(item => item.status === 'pending');
    setSelectedItems(new Set(pendingItems.map(item => item.id)));
  };

  const clearSelection = () => {
    setSelectedItems(new Set());
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.75) return 'text-green-700 bg-green-100';
    if (confidence >= 0.5) return 'text-yellow-700 bg-yellow-100';
    return 'text-red-700 bg-red-100';
  };

  const getConfidenceBadge = (confidence: number) => {
    const percentage = (confidence * 100).toFixed(1);
    const colorClass = getConfidenceColor(confidence);
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
        {percentage}%
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
    };
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800'}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-semibold mb-2">Error Loading Approval Queue</h3>
          <p className="text-red-600">{(error as Error).message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Approval Queue</h1>
        <p className="text-gray-600">Review and approve files with low confidence scores</p>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600 mb-1">Pending</div>
            <div className="text-3xl font-bold text-yellow-600">{stats.total_pending}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600 mb-1">Approved</div>
            <div className="text-3xl font-bold text-green-600">{stats.total_approved}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600 mb-1">Rejected</div>
            <div className="text-3xl font-bold text-red-600">{stats.total_rejected}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600 mb-1">Avg Confidence</div>
            <div className="text-3xl font-bold text-blue-600">{(stats.avg_confidence * 100).toFixed(1)}%</div>
          </div>
        </div>
      )}

      {/* Confidence Distribution */}
      {stats && stats.total_pending > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm font-medium text-blue-900">Low confidence (&lt;50%): </span>
              <span className="text-sm font-semibold text-blue-800">{stats.low_confidence_count} items</span>
            </div>
            <div>
              <span className="text-sm font-medium text-blue-900">Medium confidence (50-75%): </span>
              <span className="text-sm font-semibold text-blue-800">{stats.medium_confidence_count} items</span>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Min Confidence: {(minConfidence * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={minConfidence}
              onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Confidence: {(maxConfidence * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={maxConfidence}
              onChange={(e) => setMaxConfidence(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>
        </div>
      </div>

      {/* Batch Actions */}
      {selectedItems.size > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-blue-900">
                {selectedItems.size} item(s) selected
              </span>
              <button
                onClick={clearSelection}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Clear selection
              </button>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleBatchReview('approve')}
                disabled={batchReviewMutation.isPending}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                Approve Selected
              </button>
              <button
                onClick={() => handleBatchReview('reject')}
                disabled={batchReviewMutation.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                Reject Selected
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Items List */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="text-gray-500">Loading queue items...</div>
        </div>
      ) : items.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="text-gray-500">No items found</div>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm text-gray-600">{items.length} item(s)</div>
            {statusFilter === 'pending' && items.length > 0 && (
              <button
                onClick={selectAll}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Select all pending
              </button>
            )}
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Select
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    File
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Parse Case
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Confidence
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Uploaded
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedItems.has(item.id)}
                        onChange={() => toggleSelectItem(item.id)}
                        disabled={item.status !== 'pending'}
                        className="rounded"
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">{item.filename}</div>
                      <div className="text-xs text-gray-500">
                        {item.file_type} • {formatFileSize(item.file_size)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{item.detected_parse_case}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getConfidenceBadge(item.confidence)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(item.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(item.uploaded_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex gap-2">
                        {item.status === 'pending' && (
                          <button
                            onClick={() => setReviewingItem(item)}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            Review
                          </button>
                        )}
                        <button
                          onClick={() => {
                            if (window.confirm('Delete this item?')) {
                              deleteMutation.mutate(item.id);
                            }
                          }}
                          className="text-red-600 hover:text-red-800"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Review Modal */}
      {reviewingItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Review Item</h2>
                <p className="text-sm text-gray-600 mt-1">{reviewingItem.filename}</p>
              </div>
              <button
                onClick={() => {
                  setReviewingItem(null);
                  setReviewNotes('');
                  setOverrideParseCase('');
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4 mb-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm font-medium text-gray-700">Detected Parse Case</div>
                  <div className="text-sm text-gray-900 mt-1">{reviewingItem.detected_parse_case}</div>
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-700">Confidence</div>
                  <div className="mt-1">{getConfidenceBadge(reviewingItem.confidence)}</div>
                </div>
              </div>

              {/* Detection Details */}
              {reviewingItem.detection_details && (
                <div className="mt-4 border-t border-gray-200 pt-4">
                  <ParseCaseDetails detectionDetails={reviewingItem.detection_details} showFieldAnalysis={true} />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Override Parse Case (optional)
                </label>
                <input
                  type="text"
                  value={overrideParseCase}
                  onChange={(e) => setOverrideParseCase(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Leave empty to use detected parse case"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Review Notes (optional)
                </label>
                <textarea
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Add notes about your decision..."
                />
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setReviewingItem(null);
                  setReviewNotes('');
                  setOverrideParseCase('');
                }}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => handleReview('reject')}
                disabled={reviewMutation.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                Reject
              </button>
              <button
                onClick={() => handleReview('approve')}
                disabled={reviewMutation.isPending}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                Approve
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
