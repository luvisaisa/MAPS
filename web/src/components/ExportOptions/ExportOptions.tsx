import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../services/api';
import type { ExportFormat } from '../../types/api';

interface ExportOptionsProps {
  jobId: string;
}

export function ExportOptions({ jobId }: ExportOptionsProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('excel');

  const exportMutation = useMutation({
    mutationFn: async (format: ExportFormat) => {
      return apiClient.exportJob(jobId, { format });
    },
    onSuccess: (data) => {
      window.open(data.download_url, '_blank');
      setIsOpen(false);
    },
  });

  const handleExport = () => {
    exportMutation.mutate(selectedFormat);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
      >
        Export
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-20">
            <div className="p-3">
              <h4 className="text-sm font-semibold text-gray-900 mb-2">Export Format</h4>
              <div className="space-y-2">
                {(['excel', 'json', 'csv'] as ExportFormat[]).map((format) => (
                  <label
                    key={format}
                    className="flex items-center gap-2 cursor-pointer"
                  >
                    <input
                      type="radio"
                      name="export-format"
                      value={format}
                      checked={selectedFormat === format}
                      onChange={(e) => setSelectedFormat(e.target.value as ExportFormat)}
                      className="w-4 h-4 text-blue-600"
                    />
                    <span className="text-sm text-gray-700 uppercase">{format}</span>
                  </label>
                ))}
              </div>
              <button
                onClick={handleExport}
                disabled={exportMutation.isPending}
                className="w-full mt-3 px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {exportMutation.isPending ? 'Exporting...' : 'Download'}
              </button>
              {exportMutation.isError && (
                <p className="text-xs text-red-600 mt-2">
                  {(exportMutation.error as Error).message}
                </p>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
