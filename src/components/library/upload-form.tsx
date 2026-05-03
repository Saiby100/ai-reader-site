'use client';

import { useState, useRef } from 'react';
import { useDocumentUpload } from '@/hooks/use-reader-document';
import { getSupportedAcceptString } from '@/lib/file-parsers';

type UploadFormProps = {
  /** Called after a document is successfully uploaded */
  onUploadComplete: () => void;
};

const UploadForm = ({ onUploadComplete }: UploadFormProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { uploadDocument } = useDocumentUpload();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      await uploadDocument(file);
      onUploadComplete();
      setIsOpen(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } finally {
      setIsUploading(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="rounded border border-gray-300 px-4 py-2 hover:border-gray-500 dark:border-gray-700 dark:hover:border-gray-500"
      >
        Upload Document
      </button>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded border border-gray-200 p-4 dark:border-gray-700">
      <div>
        <label className="block text-sm mb-1">File</label>
        <input
          ref={fileInputRef}
          type="file"
          accept={getSupportedAcceptString()}
          required
          className="text-sm"
        />
      </div>

      <div>
        <label className="block text-sm mb-1 text-gray-400">Tags (coming soon)</label>
        <input
          type="text"
          disabled
          placeholder="Tags will be assignable here"
          className="w-full rounded border border-gray-200 px-2 py-1 text-sm disabled:opacity-50 dark:border-gray-700"
        />
      </div>

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={isUploading}
          className="rounded bg-gray-900 px-4 py-1 text-sm text-white hover:bg-gray-700 disabled:opacity-50 dark:bg-white dark:text-gray-900 dark:hover:bg-gray-200"
        >
          {isUploading ? 'Uploading...' : 'Upload'}
        </button>
        <button
          type="button"
          onClick={() => setIsOpen(false)}
          className="rounded border border-gray-300 px-4 py-1 text-sm hover:border-gray-500 dark:border-gray-700"
        >
          Cancel
        </button>
      </div>
    </form>
  );
};

export { UploadForm };
