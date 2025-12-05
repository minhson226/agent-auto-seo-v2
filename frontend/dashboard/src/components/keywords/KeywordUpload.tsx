/**
 * Keyword upload component
 */
import { useState, useCallback } from 'react';
import { CloudArrowUpIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { useKeywords } from '../../hooks/useKeywords';
import { useWorkspaceStore } from '../../store/workspaceStore';

function isValidFile(file: File) {
  const validExtensions = ['.csv', '.txt'];
  const fileName = file.name.toLowerCase();
  return validExtensions.some((ext) => fileName.endsWith(ext));
}

export default function KeywordUpload() {
  const { currentWorkspaceId } = useWorkspaceStore();
  const { uploadKeywords } = useKeywords(currentWorkspaceId || undefined);
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && isValidFile(droppedFile)) {
      setFile(droppedFile);
      if (!name) {
        setName(droppedFile.name.replace(/\.[^/.]+$/, ''));
      }
    } else {
      setError('Please upload a CSV or TXT file');
    }
  }, [name]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && isValidFile(selectedFile)) {
      setFile(selectedFile);
      if (!name) {
        setName(selectedFile.name.replace(/\.[^/.]+$/, ''));
      }
      setError('');
    } else if (selectedFile) {
      setError('Please upload a CSV or TXT file');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!file) {
      setError('Please select a file');
      return;
    }

    if (!currentWorkspaceId) {
      setError('Please select a workspace first');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', name);
      formData.append('workspace_id', currentWorkspaceId);
      if (description) {
        formData.append('description', description);
      }

      await uploadKeywords.mutateAsync(formData);

      // Reset form
      setFile(null);
      setName('');
      setDescription('');
    } catch {
      setError('Failed to upload keywords');
    }
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <h3 className="mb-4 text-lg font-medium text-gray-900">
        Upload Keywords
      </h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="rounded-md bg-red-50 p-3">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
            isDragging
              ? 'border-indigo-500 bg-indigo-50'
              : file
                ? 'border-green-500 bg-green-50'
                : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          {file ? (
            <>
              <DocumentTextIcon className="h-12 w-12 text-green-500" />
              <p className="mt-2 text-sm font-medium text-gray-900">
                {file.name}
              </p>
              <p className="text-xs text-gray-500">
                {(file.size / 1024).toFixed(1)} KB
              </p>
              <button
                type="button"
                onClick={() => setFile(null)}
                className="mt-2 text-sm text-indigo-600 hover:text-indigo-500"
              >
                Change file
              </button>
            </>
          ) : (
            <>
              <CloudArrowUpIcon className="h-12 w-12 text-gray-400" />
              <p className="mt-2 text-sm text-gray-600">
                Drag and drop a file here, or{' '}
                <label className="cursor-pointer text-indigo-600 hover:text-indigo-500">
                  browse
                  <input
                    type="file"
                    accept=".csv,.txt"
                    onChange={handleFileChange}
                    className="sr-only"
                  />
                </label>
              </p>
              <p className="text-xs text-gray-500">CSV or TXT files only</p>
            </>
          )}
        </div>

        <div>
          <label
            htmlFor="name"
            className="block text-sm font-medium text-gray-700"
          >
            List Name
          </label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
          />
        </div>

        <div>
          <label
            htmlFor="description"
            className="block text-sm font-medium text-gray-700"
          >
            Description (optional)
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
          />
        </div>

        <button
          type="submit"
          disabled={!file || uploadKeywords.isPending}
          className="flex w-full justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {uploadKeywords.isPending ? 'Uploading...' : 'Upload Keywords'}
        </button>
      </form>
    </div>
  );
}
