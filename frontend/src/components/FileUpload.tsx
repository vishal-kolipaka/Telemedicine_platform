import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, Sparkles, FileSpreadsheet, FileCode, Image, X, Plus, AlertCircle, Clipboard } from 'lucide-react';

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onFilesSelected }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [pasteNotice, setPasteNotice] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const ALLOWED_EXTENSIONS = ['.txt', '.pdf', '.png', '.jpg', '.jpeg', '.csv', '.xlsx'];

  // Global Clipboard Paste (Ctrl + V) Handler
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      if (!e.clipboardData) return;

      const items = e.clipboardData.items;
      const newFiles: File[] = [];

      // 1. Check for image or file items in clipboard (e.g. Snipping Tool screenshots)
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.type.indexOf('image') !== -1) {
          const blob = item.getAsFile();
          if (blob) {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
            const screenshotFile = new File([blob], `pasted_screenshot_${timestamp}.png`, {
              type: 'image/png',
            });
            newFiles.push(screenshotFile);
          }
        } else if (item.kind === 'file') {
          const file = item.getAsFile();
          if (file) newFiles.push(file);
        }
      }

      // 2. If no files, check if raw report text was pasted
      if (newFiles.length === 0) {
        const pastedText = e.clipboardData.getData('text');
        if (pastedText && pastedText.trim().length > 10) {
          const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
          const textFile = new File([pastedText], `pasted_report_${timestamp}.txt`, {
            type: 'text/plain',
          });
          newFiles.push(textFile);
        }
      }

      if (newFiles.length > 0) {
        e.preventDefault();
        validateAndAddFiles(newFiles);
        setPasteNotice(`Pasted ${newFiles.length} item(s) from clipboard!`);
        setTimeout(() => setPasteNotice(null), 3000);
      }
    };

    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, [selectedFiles]);

  const validateAndAddFiles = (fileList: FileList | File[]) => {
    const valid: File[] = [];
    let invalidCount = 0;

    Array.from(fileList).forEach((file) => {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (ALLOWED_EXTENSIONS.includes(ext)) {
        // Prevent duplicate addition in staged list
        if (!selectedFiles.some((f) => f.name === file.name && f.size === file.size)) {
          valid.push(file);
        }
      } else {
        invalidCount++;
      }
    });

    if (invalidCount > 0) {
      setErrorMsg(`Skipped ${invalidCount} unsupported file(s). Allowed: TXT, PDF, PNG, JPG, JPEG, CSV, XLSX.`);
    } else {
      setErrorMsg(null);
    }

    if (valid.length > 0) {
      setSelectedFiles((prev) => [...prev, ...valid]);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndAddFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files.length > 0) {
      validateAndAddFiles(e.target.files);
    }
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleStartAnalysis = () => {
    if (selectedFiles.length > 0) {
      onFilesSelected(selectedFiles);
    }
  };

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    if (['csv', 'xlsx'].includes(ext || '')) return <FileSpreadsheet className="w-5 h-5 text-emerald-600" />;
    if (['png', 'jpg', 'jpeg'].includes(ext || '')) return <Image className="w-5 h-5 text-cyan-600" />;
    if (ext === 'txt') return <FileCode className="w-5 h-5 text-slate-600" />;
    return <FileText className="w-5 h-5 text-sky-600" />;
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="w-full max-w-3xl mx-auto space-y-6">
      
      {/* Drag & Drop Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => selectedFiles.length === 0 && inputRef.current?.click()}
        className={`relative telemed-card p-8 md:p-12 text-center border-2 border-dashed transition-all duration-200 ${
          selectedFiles.length === 0 ? 'cursor-pointer' : ''
        } ${
          dragActive
            ? 'border-sky-500 bg-sky-50/80 scale-[1.01]'
            : selectedFiles.length > 0
            ? 'border-sky-300 bg-sky-50/10'
            : 'border-slate-300 hover:border-sky-400 hover:bg-sky-50/30'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".txt,.pdf,.png,.jpg,.jpeg,.csv,.xlsx"
          onChange={handleChange}
          className="hidden"
        />

        {selectedFiles.length === 0 ? (
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-sky-100/80 text-sky-600 flex items-center justify-center shadow-xs">
              <Upload className="w-8 h-8" />
            </div>
            
            <div className="space-y-1">
              <h3 className="text-lg font-bold text-slate-900">
                Drag and drop your medical reports here
              </h3>
              <p className="text-sm text-slate-500">
                Upload 1 or multiple reports simultaneously (Clinical, Gut Microbiome, Wearables)
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-3">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  inputRef.current?.click();
                }}
                className="px-5 py-2.5 bg-sky-600 hover:bg-sky-700 text-white text-sm font-semibold rounded-xl shadow-md shadow-sky-600/20 transition-all duration-150"
              >
                Browse Files
              </button>

              <span className="text-xs font-semibold text-slate-400">OR</span>

              <div className="flex items-center space-x-1.5 px-3.5 py-2 bg-slate-100/90 text-slate-700 text-xs font-semibold rounded-xl border border-slate-200 shadow-2xs">
                <Clipboard className="w-4 h-4 text-sky-600" />
                <span>Press <kbd className="px-1.5 py-0.5 bg-white border border-slate-300 rounded-md font-mono text-[11px] shadow-2xs">Ctrl + V</kbd> to paste screenshot</span>
              </div>
            </div>

            {/* Supported Formats Badges */}
            <div className="pt-4 border-t border-slate-200/60 w-full max-w-md">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Supported Formats
              </span>
              <div className="flex flex-wrap items-center justify-center gap-1.5">
                {ALLOWED_EXTENSIONS.map((ext) => (
                  <span
                    key={ext}
                    className="px-2.5 py-1 bg-slate-100 text-slate-700 text-xs font-medium rounded-md uppercase border border-slate-200/80"
                  >
                    {ext.replace('.', '')}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Staged Files List State */
          <div className="space-y-6 text-left" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between border-b border-slate-200/80 pb-3">
              <div>
                <h4 className="font-bold text-slate-900 text-base">
                  Staged Documents ({selectedFiles.length})
                </h4>
                <span className="text-xs text-slate-500">
                  Ready for intelligent structure analysis
                </span>
              </div>

              <button
                type="button"
                onClick={() => inputRef.current?.click()}
                className="flex items-center space-x-1.5 px-3 py-1.5 bg-sky-50 hover:bg-sky-100 text-sky-700 text-xs font-semibold rounded-lg border border-sky-200 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add More Files</span>
              </button>
            </div>

            {/* File Items Grid */}
            <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
              {selectedFiles.map((file, idx) => (
                <div
                  key={`${file.name}_${idx}`}
                  className="flex items-center justify-between p-3 bg-white border border-slate-200 rounded-xl shadow-2xs hover:border-sky-300 transition-all"
                >
                  <div className="flex items-center space-x-3 truncate">
                    <div className="p-2 bg-slate-50 rounded-lg shrink-0">
                      {getFileIcon(file.name)}
                    </div>
                    <div className="truncate">
                      <span className="font-bold text-slate-800 text-sm block truncate">
                        {file.name}
                      </span>
                      <span className="text-xs text-slate-400 font-mono">
                        {formatBytes(file.size)} • {file.type || 'Document'}
                      </span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleRemoveFile(idx)}
                    className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors ml-2 shrink-0"
                    title="Remove file"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>

            {/* Action Bar */}
            <div className="flex items-center justify-between pt-3 border-t border-slate-200/80">
              <button
                type="button"
                onClick={() => setSelectedFiles([])}
                className="text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
              >
                Clear All
              </button>

              <button
                type="button"
                onClick={handleStartAnalysis}
                className="flex items-center space-x-2 px-6 py-2.5 bg-gradient-to-r from-sky-600 to-cyan-600 hover:from-sky-700 hover:to-cyan-700 text-white font-semibold text-sm rounded-xl shadow-lg shadow-sky-600/30 transition-all transform hover:scale-[1.02]"
              >
                <Sparkles className="w-4 h-4" />
                <span>
                  Process {selectedFiles.length} {selectedFiles.length === 1 ? 'Document' : 'Documents'}
                </span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Clipboard Paste Notice Toast */}
      {pasteNotice && (
        <div className="p-4 bg-emerald-50 border border-emerald-300 rounded-xl flex items-center space-x-3 text-emerald-800 text-sm animate-fade-in shadow-xs">
          <Clipboard className="w-5 h-5 text-emerald-600 shrink-0" />
          <span className="font-semibold">{pasteNotice}</span>
        </div>
      )}

      {/* Error Alert */}
      {errorMsg && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-3 text-rose-700 text-sm animate-fade-in">
          <AlertCircle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

    </div>
  );
};
