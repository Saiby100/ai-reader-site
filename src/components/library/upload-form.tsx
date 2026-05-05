'use client';

import { useState, useRef } from 'react';
import { useDocumentUpload } from '@/hooks/use-reader-document';
import { getSupportedAcceptString, getFileExtension } from '@/lib/file-parsers';
import { UploadIcon, CheckIcon, CloseIcon } from '@/components/icons';

type UploadFormProps = {
  /** Called after a document is successfully uploaded */
  onUploadComplete: () => void;
};

const UploadForm = ({ onUploadComplete }: UploadFormProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [tagsInput, setTagsInput] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { uploadDocument } = useDocumentUpload();

  const resetForm = () => {
    setTitle('');
    setAuthor('');
    setTagsInput('');
    setSelectedFileName(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFileName(file.name);
      if (!title) {
        const ext = getFileExtension(file.name);
        setTitle(file.name.replace(new RegExp(`\\${ext}$`, 'i'), ''));
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      const dt = new DataTransfer();
      dt.items.add(file);
      if (fileInputRef.current) {
        fileInputRef.current.files = dt.files;
      }
      setSelectedFileName(file.name);
      if (!title) {
        const ext = getFileExtension(file.name);
        setTitle(file.name.replace(new RegExp(`\\${ext}$`, 'i'), ''));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;

    const tags = tagsInput
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

    setIsUploading(true);
    try {
      await uploadDocument(file, { title, author, tags });
      onUploadComplete();
      setIsOpen(false);
      resetForm();
    } finally {
      setIsUploading(false);
    }
  };

  const handleClose = () => {
    if (isUploading) return;
    setIsOpen(false);
    resetForm();
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="h-[38px] px-[18px] rounded-[var(--radius)] bg-accent border-none text-white text-[13px] font-medium cursor-pointer flex items-center gap-[7px] font-sans transition-all hover:opacity-90"
      >
        <UploadIcon size={15} /> Add document
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" />

          <div className="relative bg-white rounded-[var(--radius-lg)] shadow-xl w-full max-w-[520px] mx-4 p-6 animate-[fade-in_0.15s_ease-out]">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-[15px] font-semibold text-ink">Add a document</h3>
              <button
                onClick={handleClose}
                className="h-8 w-8 rounded-[var(--radius)] bg-sand-2 border border-border text-ink flex items-center justify-center cursor-pointer transition-all hover:bg-sand-3"
              >
                <CloseIcon size={14} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-[var(--radius-lg)] p-9 flex flex-col items-center gap-3 cursor-pointer transition-all ${
                  dragging
                    ? 'border-accent bg-accent-light'
                    : 'border-border bg-sand-1'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={getSupportedAcceptString()}
                  className="hidden"
                  onChange={handleFileChange}
                />
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
                    dragging ? 'bg-accent' : 'bg-sand-2'
                  }`}
                >
                  <UploadIcon size={22} className={dragging ? 'text-white' : 'text-ink-3'} />
                </div>
                {selectedFileName ? (
                  <div className="text-[13px] text-green font-medium flex items-center gap-1.5">
                    <CheckIcon size={14} /> {selectedFileName}
                  </div>
                ) : (
                  <>
                    <div className="text-[13.5px] font-medium text-ink text-center">
                      Drop a document here, or <span className="text-accent">click to browse</span>
                    </div>
                    <div className="text-[11.5px] text-ink-3">PDF, DOCX, TXT, Markdown</div>
                  </>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-medium text-ink-3 uppercase tracking-wider mb-1">Title</label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                    placeholder="Document title"
                    className="w-full rounded-[var(--radius)] border border-border px-3 py-2 text-[13px] font-sans bg-white text-ink outline-none placeholder:text-ink-3"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-ink-3 uppercase tracking-wider mb-1">Author</label>
                  <input
                    type="text"
                    value={author}
                    onChange={(e) => setAuthor(e.target.value)}
                    placeholder="Author name"
                    className="w-full rounded-[var(--radius)] border border-border px-3 py-2 text-[13px] font-sans bg-white text-ink outline-none placeholder:text-ink-3"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-ink-3 uppercase tracking-wider mb-1">Tags</label>
                <input
                  type="text"
                  value={tagsInput}
                  onChange={(e) => setTagsInput(e.target.value)}
                  placeholder="Comma-separated tags"
                  className="w-full rounded-[var(--radius)] border border-border px-3 py-2 text-[13px] font-sans bg-white text-ink outline-none placeholder:text-ink-3"
                />
              </div>

              <div className="flex items-center gap-3 pt-1">
                <button
                  type="submit"
                  disabled={isUploading || !selectedFileName}
                  className="h-[38px] px-[18px] rounded-[var(--radius)] bg-accent border-none text-white text-[13px] font-medium cursor-pointer flex items-center justify-center gap-[7px] font-sans transition-all hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isUploading ? 'Uploading…' : 'Upload'}
                </button>
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={isUploading}
                  className="h-[38px] px-[18px] rounded-[var(--radius)] bg-sand-2 border border-border text-ink text-[13px] font-medium cursor-pointer flex items-center gap-[7px] font-sans transition-all hover:bg-sand-3 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

export { UploadForm };
