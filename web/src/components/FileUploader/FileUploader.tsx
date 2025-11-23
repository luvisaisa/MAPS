import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';

interface FileUploaderProps {
  onFilesSelected: (files: File[]) => void;
  selectedFiles: File[];
  acceptedFileTypes?: string[];
  maxFiles?: number;
  maxSize?: number;
}

export function FileUploader({
  onFilesSelected,
  selectedFiles,
  acceptedFileTypes = ['.xml', '.json', '.pdf', '.zip'],
  maxFiles = 1000,
  maxSize = 100 * 1024 * 1024, // 100MB per file (for ZIPs)
}: FileUploaderProps) {
  const [errors, setErrors] = useState<string[]>([]);
  const [isExtracting, setIsExtracting] = useState(false);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      setErrors([]);
      const newFiles = [...selectedFiles, ...acceptedFiles];
      
      if (newFiles.length > maxFiles) {
        setErrors([`Maximum ${maxFiles} files allowed. Only first ${maxFiles} files will be selected.`]);
        onFilesSelected(newFiles.slice(0, maxFiles));
      } else {
        onFilesSelected(newFiles);
      }
    },
    [selectedFiles, onFilesSelected, maxFiles]
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: {
      'application/xml': ['.xml'],
      'application/json': ['.json'],
      'text/xml': ['.xml'],
      'application/pdf': ['.pdf'],
      'application/zip': ['.zip'],
      'application/x-zip-compressed': ['.zip'],
    },
    maxSize,
    multiple: true,
    // Allow directory selection
    // @ts-ignore - webkitdirectory is not in TS types but works in browsers
    webkitdirectory: false,
  });

  const removeFile = (index: number) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index);
    onFilesSelected(newFiles);
  };

  const clearAll = () => {
    onFilesSelected([]);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i)) + ' ' + sizes[i];
  };

  const handleFolderUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrors([]);
    const files = Array.from(e.target.files || []);
    const supportedFiles = files.filter(f => 
      f.name.endsWith('.xml') || 
      f.name.endsWith('.json') || 
      f.name.endsWith('.pdf') ||
      f.name.endsWith('.zip')
    );
    
    if (supportedFiles.length === 0) {
      setErrors(['No supported files found in the selected folder(s)']);
      return;
    }

    const newFiles = [...selectedFiles, ...supportedFiles];
    
    if (newFiles.length > maxFiles) {
      setErrors([`Maximum ${maxFiles} files allowed. Only first ${maxFiles} files will be selected.`]);
      onFilesSelected(newFiles.slice(0, maxFiles));
    } else {
      onFilesSelected(newFiles);
    }
  };

  return (
    <div className="space-y-4">
      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div className="flex-1 text-sm text-blue-800">
            <p className="font-medium mb-1">Upload multiple files or entire folders</p>
            <p>Maximum {maxFiles} files per upload. Accepted formats: XML, JSON, PDF, ZIP</p>
            <p className="text-xs mt-1 text-blue-700">ZIP files will be automatically extracted on the server</p>
          </div>
        </div>
      </div>

      {/* Upload Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Dropzone for Files */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400 bg-white'
          }`}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-2">
            <svg
              className="w-10 h-10 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            {isDragActive ? (
              <p className="text-blue-600 font-medium">Drop files here</p>
            ) : (
              <>
                <p className="text-gray-700 font-medium">Select Multiple Files</p>
                <p className="text-xs text-gray-500">
                  Drag & drop or click to browse
                </p>
                <p className="text-xs text-gray-400">
                  Max {formatFileSize(maxSize)} per file
                </p>
              </>
            )}
          </div>
        </div>

        {/* Folder Upload Button */}
        <div className="border-2 border-dashed border-gray-300 hover:border-gray-400 rounded-lg p-6 text-center bg-white transition-colors">
          <label className="cursor-pointer flex flex-col items-center gap-2">
            <input
              type="file"
              // @ts-ignore
              webkitdirectory=""
              directory=""
              multiple
              onChange={handleFolderUpload}
              className="hidden"
            />
            <svg
              className="w-10 h-10 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
              />
            </svg>
            <p className="text-gray-700 font-medium">Select Folder(s)</p>
            <p className="text-xs text-gray-500">
              Upload entire directories
            </p>
            <p className="text-xs text-gray-400">
              XML & JSON files only
            </p>
          </label>
        </div>
      </div>

      {/* Errors */}
      {errors.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h4 className="text-yellow-800 font-semibold mb-2">Notice:</h4>
          <ul className="list-disc list-inside text-sm text-yellow-700">
            {errors.map((error, idx) => (
              <li key={idx}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* File Rejections */}
      {fileRejections.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h4 className="text-red-800 font-semibold mb-2">Some files were rejected:</h4>
          <ul className="list-disc list-inside text-sm text-red-600">
            {fileRejections.map(({ file, errors }) => (
              <li key={file.name}>
                {file.name}: {errors.map(e => e.message).join(', ')}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ZIP Extraction Progress */}
      {isExtracting && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <span className="text-sm text-blue-800 font-medium">Extracting ZIP files...</span>
          </div>
        </div>
      )}

      {/* Selected Files List */}
      {selectedFiles.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900">
              Selected Files ({selectedFiles.length} / {maxFiles})
            </h3>
            <button
              onClick={clearAll}
              className="text-sm text-red-600 hover:text-red-700 font-medium"
            >
              Clear All
            </button>
          </div>
          <div className="divide-y divide-gray-200 max-h-64 overflow-y-auto">
            {selectedFiles.map((file, index) => (
              <div key={index} className="flex items-center justify-between p-3 hover:bg-gray-50">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                    {file.name.endsWith('.zip') && (
                      <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded font-medium">
                        ZIP
                      </span>
                    )}
                    {file.name.endsWith('.pdf') && (
                      <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded font-medium">
                        PDF
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="ml-4 text-red-600 hover:text-red-700"
                  title="Remove file"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
