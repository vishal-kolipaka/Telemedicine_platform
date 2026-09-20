import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, Sparkles, FileSpreadsheet, FileCode, Image, X, Plus, AlertCircle, Clipboard, CheckCircle2 } from 'lucide-react';

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  isGuidedDemo?: boolean;
  onStagedCountChange?: (count: number) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFilesSelected,
  isGuidedDemo = false,
  onStagedCountChange,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [pasteNotice, setPasteNotice] = useState<string | null>(null);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const ALLOWED_EXTENSIONS = ['.txt', '.pdf', '.png', '.jpg', '.jpeg', '.csv', '.xlsx'];

  // Notify parent of staged count changes
  useEffect(() => {
    onStagedCountChange?.(selectedFiles.length);
  }, [selectedFiles, onStagedCountChange]);

  const handleLoadDemoReport = async () => {
    try {
      setLoadingDemo(true);
      setErrorMsg(null);
      const response = await fetch('/HealthPrism_Demo_Multimodal_Report.pdf');
      if (!response.ok) {
        throw new Error(`Failed to load demo report (${response.status})`);
      }
      const blob = await response.blob();
      const demoFile = new File([blob], 'HealthPrism_Demo_Multimodal_Report.pdf', {
        type: 'application/pdf',
      });
      validateAndAddFiles([demoFile]);
    } catch (err: any) {
      console.error('Failed to load demo report:', err);
      setErrorMsg('Unable to load demo report. Please try browsing for the file.');
    } finally {
      setLoadingDemo(false);
    }
  };

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
    <div className="w-full max-w-7xl mx-auto space-y-4">
      
      {/* 2-Column Responsive Grid on Desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">

        {/* ── LEFT COLUMN: Guided Instructions & Demo Report ── */}
        <div className="lg:col-span-5 space-y-4">

          {/* Guided Demo Hero Card (Shown during Guided Demo) */}
          {isGuidedDemo && (
            <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-sky-950 text-white shadow-xl border border-sky-500/30 relative overflow-hidden guided-fade-in">
              <div className="absolute -top-10 -right-10 w-36 h-36 bg-sky-500/15 rounded-full blur-2xl pointer-events-none" />
              <div className="absolute -bottom-10 -left-10 w-36 h-48 bg-orange-500/15 rounded-full blur-2xl pointer-events-none" />

              <div className="relative space-y-3">
                <div className="flex items-center justify-between">
                  <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-black uppercase tracking-wider border ${
                    selectedFiles.length === 0
                      ? 'bg-orange-500/20 text-orange-300 border-orange-400/30'
                      : 'bg-emerald-500/20 text-emerald-300 border-emerald-400/30'
                  }`}>
                    {selectedFiles.length === 0 ? 'Step 02: Load Demo Report' : 'Next Action: Process Document'}
                  </span>
                  <span className="text-xs font-bold text-slate-400">Step 2 of 5</span>
                </div>

                <div className="flex items-start space-x-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-md ${
                    selectedFiles.length === 0
                      ? 'bg-gradient-to-br from-orange-500 to-amber-500 text-white shadow-orange-500/30'
                      : 'bg-gradient-to-br from-emerald-500 to-teal-500 text-white shadow-emerald-500/30'
                  }`}>
                    {selectedFiles.length === 0 ? (
                      <Sparkles className="w-5 h-5" />
                    ) : (
                      <CheckCircle2 className="w-5 h-5" />
                    )}
                  </div>
                  <div>
                    <h3 className="text-base sm:text-lg font-black text-white tracking-tight leading-snug">
                      {selectedFiles.length === 0
                        ? 'Load the Provided Test Report'
                        : 'Report Staged & Ready'}
                    </h3>
                    <p className="text-xs text-slate-300 leading-relaxed mt-1">
                      {selectedFiles.length === 0
                        ? 'For this demonstration, use the prepared synthetic report with Clinical, Wearable/CGM and Gut data. Click "Load Demo Report" below.'
                        : 'Your synthetic multimodal report is staged. Now click "Process 1 Document" on the right to start analysis.'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Demo / Test Report Card */}
          <div
            id="demo-test-report-card"
            className={`telemed-card p-5 sm:p-6 rounded-2xl border transition-all duration-300 ${
              isGuidedDemo && selectedFiles.length === 0
                ? 'bg-gradient-to-br from-orange-50/95 via-amber-50/50 to-orange-50/90 border-2 border-orange-500 ring-4 ring-orange-400/40 shadow-xl shadow-orange-500/20 guided-spotlight-active'
                : 'bg-white border-slate-200/90 shadow-xs hover:border-slate-300'
            }`}
          >
            {/* Guided Demo Spotlight Callout Badge (visible ONLY during Guided Demo when 0 files staged) */}
            {isGuidedDemo && selectedFiles.length === 0 && (
              <div className="mb-3">
                <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-gradient-to-r from-orange-500 to-amber-500 text-white text-xs font-black shadow-md shadow-orange-500/25 guided-bounce-attention">
                  <span className="w-2 h-2 rounded-full bg-white animate-ping" />
                  <span>👇 CLICK HERE TO LOAD DEMO REPORT</span>
                </span>
              </div>
            )}

            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                  isGuidedDemo && selectedFiles.length === 0
                    ? 'bg-gradient-to-br from-orange-500 to-amber-600 text-white shadow-md shadow-orange-500/30'
                    : 'bg-sky-100 text-sky-700'
                }`}>
                  <FileText className="w-4 h-4" />
                </div>
                <span className={`text-xs uppercase tracking-wider font-extrabold px-2.5 py-0.5 rounded-md border ${
                  isGuidedDemo && selectedFiles.length === 0
                    ? 'bg-orange-100 text-orange-800 border-orange-200'
                    : 'bg-sky-50 text-sky-800 border-sky-200'
                }`}>
                  Demo / Test Report
                </span>
              </div>

              <div>
                <h4 className="text-sm sm:text-base font-bold text-slate-900 leading-snug">
                  Want to explore !Health Prism without preparing your own health data?
                </h4>
                <p className="text-xs text-slate-500 leading-relaxed mt-1">
                  Use our prepared synthetic multimodal report containing verified <strong className="text-slate-700">Clinical</strong> (15 biomarkers), <strong className="text-slate-700">Wearable / CGM</strong>, and <strong className="text-slate-700">Gut Microbiome</strong> parameters.
                </p>
              </div>

              <div className="pt-2">
                <button
                  type="button"
                  id="load-demo-report-btn"
                  onClick={handleLoadDemoReport}
                  disabled={loadingDemo}
                  className={`w-full py-3 px-4 text-xs sm:text-sm font-extrabold rounded-xl transition-all flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50 ${
                    isGuidedDemo && selectedFiles.length === 0
                      ? 'bg-gradient-to-r from-orange-500 via-amber-500 to-emerald-500 hover:from-orange-600 hover:to-emerald-600 text-white shadow-lg shadow-orange-500/30 transform hover:scale-[1.02] active:scale-[0.98]'
                      : 'bg-slate-900 hover:bg-slate-800 text-white shadow-sm hover:shadow'
                  }`}
                >
                  <Sparkles className={`w-4 h-4 ${isGuidedDemo && selectedFiles.length === 0 ? 'text-white' : 'text-amber-400'}`} />
                  <span>{loadingDemo ? 'Loading Report...' : 'Load Demo Report'}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Clipboard Paste Notice Toast */}
          {pasteNotice && (
            <div className="p-3.5 bg-emerald-50 border border-emerald-300 rounded-xl flex items-center space-x-2.5 text-emerald-800 text-xs animate-fade-in shadow-xs">
              <Clipboard className="w-4 h-4 text-emerald-600 shrink-0" />
              <span className="font-semibold">{pasteNotice}</span>
            </div>
          )}

          {/* Error Alert */}
          {errorMsg && (
            <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-2.5 text-rose-700 text-xs animate-fade-in">
              <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

        </div>

        {/* ── RIGHT COLUMN: Medical Reports Upload Area / Staged Documents ── */}
        <div className="lg:col-span-7">
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => selectedFiles.length === 0 && inputRef.current?.click()}
            className={`relative telemed-card p-6 sm:p-8 text-center border-2 border-dashed transition-all duration-200 min-h-[340px] flex flex-col justify-center ${
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
              <div className="flex flex-col items-center justify-center space-y-4 my-auto">
                <div className="w-14 h-14 rounded-2xl bg-sky-100/80 text-sky-600 flex items-center justify-center shadow-xs">
                  <Upload className="w-7 h-7" />
                </div>
                
                <div className="space-y-1">
                  <h3 className="text-base sm:text-lg font-bold text-slate-900">
                    Drag and drop your medical reports here
                  </h3>
                  <p className="text-xs text-slate-500 max-w-md mx-auto">
                    Upload 1 or multiple reports simultaneously (Clinical, Gut Microbiome, Wearables)
                  </p>
                </div>

                <div className="flex flex-col sm:flex-row items-center gap-2.5 pt-1">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      inputRef.current?.click();
                    }}
                    className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold rounded-xl shadow-md shadow-sky-600/20 transition-all duration-150 cursor-pointer"
                  >
                    Browse Files
                  </button>

                  <span className="text-[11px] font-semibold text-slate-400">OR</span>

                  <div className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-100/90 text-slate-700 text-xs font-semibold rounded-xl border border-slate-200 shadow-2xs">
                    <Clipboard className="w-3.5 h-3.5 text-sky-600" />
                    <span>Press <kbd className="px-1.5 py-0.5 bg-white border border-slate-300 rounded-md font-mono text-[11px] shadow-2xs">Ctrl + V</kbd> to paste</span>
                  </div>
                </div>

                {/* Supported Formats Badges */}
                <div className="pt-3 border-t border-slate-200/60 w-full max-w-sm mx-auto">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">
                    Supported Formats
                  </span>
                  <div className="flex flex-wrap items-center justify-center gap-1">
                    {ALLOWED_EXTENSIONS.map((ext) => (
                      <span
                        key={ext}
                        className="px-2 py-0.5 bg-slate-100 text-slate-600 text-[11px] font-medium rounded-md uppercase border border-slate-200/80"
                      >
                        {ext.replace('.', '')}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              /* Staged Files List State */
              <div className="space-y-4 text-left w-full my-auto" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center justify-between border-b border-slate-200/80 pb-2.5">
                  <div>
                    <h4 className="font-bold text-slate-900 text-sm sm:text-base">
                      Staged Documents ({selectedFiles.length})
                    </h4>
                    <span className="text-xs text-slate-500">
                      Ready for intelligent structure analysis
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={() => inputRef.current?.click()}
                    className="flex items-center space-x-1.5 px-3 py-1.5 bg-sky-50 hover:bg-sky-100 text-sky-700 text-xs font-semibold rounded-lg border border-sky-200 transition-colors cursor-pointer"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add More Files</span>
                  </button>
                </div>

                {/* File Items Grid */}
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
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
                        className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors ml-2 shrink-0 cursor-pointer"
                        title="Remove file"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>

                {/* Action Bar */}
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-3 border-t border-slate-200/80">
                  <button
                    type="button"
                    onClick={() => setSelectedFiles([])}
                    className="text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors py-1 cursor-pointer"
                  >
                    Clear All
                  </button>

                  <div className="flex flex-col items-end gap-1.5">
                    {/* Guided Demo attention pointer above Process button */}
                    {isGuidedDemo && (
                      <div className="guided-bounce-attention">
                        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-gradient-to-r from-orange-500 via-amber-500 to-emerald-500 text-white text-xs font-black shadow-md shadow-orange-500/30">
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>👇 CLICK HERE TO PROCESS DOCUMENT</span>
                        </span>
                      </div>
                    )}

                    <button
                      type="button"
                      id="process-staged-documents-btn"
                      onClick={handleStartAnalysis}
                      className={`flex items-center justify-center space-x-2 px-6 py-2.5 text-white font-semibold text-sm rounded-xl transition-all transform hover:scale-[1.02] cursor-pointer ${
                        isGuidedDemo
                          ? 'bg-gradient-to-r from-orange-500 via-amber-500 to-emerald-500 hover:from-orange-600 hover:to-emerald-600 font-extrabold shadow-xl shadow-orange-500/35 ring-4 ring-orange-400/50 guided-process-pulse'
                          : 'bg-gradient-to-r from-sky-600 to-cyan-600 hover:from-sky-700 hover:to-cyan-700 shadow-lg shadow-sky-600/30'
                      }`}
                    >
                      <Sparkles className="w-4 h-4" />
                      <span>
                        Process {selectedFiles.length} {selectedFiles.length === 1 ? 'Document' : 'Documents'}
                      </span>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

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
