'use client';

import { useState, useRef } from 'react';
import { useDocumentUpload } from '@/hooks/use-reader-document';
import { getSupportedAcceptString, getFileExtension } from '@/lib/file-parsers';

type UploadMode = 'file' | 'text';

type UploadFormProps = {
  /** Called after a document is successfully uploaded */
  onUploadComplete: () => void;
};

const UploadForm = ({ onUploadComplete }: UploadFormProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [mode, setMode] = useState<UploadMode>('file');
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [tagsInput, setTagsInput] = useState('');
  const [pastedText, setPastedText] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { uploadDocument, uploadFromText } = useDocumentUpload();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && !title) {
      const ext = getFileExtension(file.name);
      setTitle(file.name.replace(new RegExp(`\\${ext}$`, 'i'), ''));
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const tags = tagsInput
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

    setIsUploading(true);
    try {
      if (mode === 'file') {
        const file = fileInputRef.current?.files?.[0];
        if (!file) return;
        await uploadDocument(file, { title, author, tags });
      } else {
        if (!pastedText.trim()) return;
        await uploadFromText(pastedText, { title, author, tags });
      }

      onUploadComplete();
      setIsOpen(false);
      setTitle('');
      setAuthor('');
      setTagsInput('');
      setPastedText('');
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
      <div className="flex gap-2 text-sm">
        <button
          type="button"
          onClick={() => setMode('file')}
          className={`rounded px-3 py-1 ${mode === 'file' ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900' : 'border border-gray-300 dark:border-gray-700'}`}
        >
          File
        </button>
        <button
          type="button"
          onClick={() => setMode('text')}
          className={`rounded px-3 py-1 ${mode === 'text' ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900' : 'border border-gray-300 dark:border-gray-700'}`}
        >
          Paste Text
        </button>
      </div>

      {mode === 'file' ? (
        <div>
          <label className="block text-sm mb-1">File</label>
          <input
            ref={fileInputRef}
            type="file"
            accept={getSupportedAcceptString()}
            required
            onChange={handleFileChange}
            className="text-sm"
          />
        </div>
      ) : (
        <div>
          <label className="block text-sm mb-1">Content</label>
          <textarea
            value={pastedText}
            onChange={(e) => setPastedText(e.target.value)}
            required
            placeholder="Paste your text here..."
            rows={6}
            className="w-full rounded border border-gray-200 px-2 py-1 text-sm dark:border-gray-700 dark:bg-transparent"
          />
        </div>
      )}

      <div>
        <label className="block text-sm mb-1">Title</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          placeholder="Document title"
          className="w-full rounded border border-gray-200 px-2 py-1 text-sm dark:border-gray-700 dark:bg-transparent"
        />
      </div>

      <div>
        <label className="block text-sm mb-1">Author</label>
        <input
          type="text"
          value={author}
          onChange={(e) => setAuthor(e.target.value)}
          placeholder="Author name"
          className="w-full rounded border border-gray-200 px-2 py-1 text-sm dark:border-gray-700 dark:bg-transparent"
        />
      </div>

      <div>
        <label className="block text-sm mb-1">Tags</label>
        <input
          type="text"
          value={tagsInput}
          onChange={(e) => setTagsInput(e.target.value)}
          placeholder="Comma-separated tags"
          className="w-full rounded border border-gray-200 px-2 py-1 text-sm dark:border-gray-700 dark:bg-transparent"
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