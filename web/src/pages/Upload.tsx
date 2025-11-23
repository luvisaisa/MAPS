import { useState } from 'react';
import { FileUploader } from '../components/FileUploader/FileUploader';
import { ProfileSelector } from '../components/ProfileSelector/ProfileSelector';
import { BatchProcessor } from '../components/BatchProcessor/BatchProcessor';
import { ProgressTracker } from '../components/ProgressTracker/ProgressTracker';

export function Upload() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingJobs, setProcessingJobs] = useState<string[]>([]);

  const handleFilesSelected = (files: File[]) => {
    setSelectedFiles(files);
  };

  const handleProfileSelected = (profileName: string) => {
    setSelectedProfile(profileName);
  };

  const handleStartProcessing = () => {
    if (selectedFiles.length > 0 && selectedProfile) {
      setIsProcessing(true);
    }
  };

  const handleProcessingComplete = (jobIds: string[]) => {
    setProcessingJobs(jobIds);
    setIsProcessing(false);
    setSelectedFiles([]);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Upload & Process Files</h1>

      <div className="space-y-8">
        {/* File Upload Section */}
        <section className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Files</h2>
          <FileUploader
            onFilesSelected={handleFilesSelected}
            selectedFiles={selectedFiles}
          />
        </section>

        {/* Profile Selection */}
        {selectedFiles.length > 0 && (
          <section className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Profile</h2>
            <ProfileSelector
              onProfileSelected={handleProfileSelected}
              selectedProfile={selectedProfile}
            />
          </section>
        )}

        {/* Process Button */}
        {selectedFiles.length > 0 && selectedProfile && !isProcessing && (
          <div className="flex justify-end">
            <button
              onClick={handleStartProcessing}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Start Processing ({selectedFiles.length} {selectedFiles.length === 1 ? 'file' : 'files'})
            </button>
          </div>
        )}

        {/* Batch Processing */}
        {isProcessing && (
          <section className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Processing</h2>
            <BatchProcessor
              files={selectedFiles}
              profileName={selectedProfile}
              onComplete={handleProcessingComplete}
            />
          </section>
        )}

        {/* Progress Tracking */}
        {processingJobs.length > 0 && (
          <section className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Jobs</h2>
            <ProgressTracker jobIds={processingJobs} />
          </section>
        )}
      </div>
    </div>
  );
}
