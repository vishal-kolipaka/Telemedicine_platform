import React from 'react';
import { FileText, HardDrive, Layers, Calendar } from 'lucide-react';
import type { DocumentAnalysisResult } from '../types/reader';

interface Props {
  data: DocumentAnalysisResult;
}

export const DocumentInfoCard: React.FC<Props> = ({ data }) => {
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (isoString: string) => {
    try {
      return new Date(isoString).toLocaleString();
    } catch {
      return isoString;
    }
  };

  return (
    <div className="telemed-card p-6 space-y-4">
      <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
        <div className="w-8 h-8 rounded-lg bg-sky-100 text-sky-700 flex items-center justify-center font-bold">
          <FileText className="w-4 h-4" />
        </div>
        <h3 className="text-base font-bold text-slate-900">Document Information</h3>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm">
        
        <div className="space-y-1">
          <span className="text-xs text-slate-400 font-medium block">File Name</span>
          <div className="font-semibold text-slate-800 truncate" title={data.source_file}>
            {data.source_file}
          </div>
        </div>

        <div className="space-y-1">
          <span className="text-xs text-slate-400 font-medium block">File Type</span>
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-50 text-sky-700 uppercase border border-sky-200/60">
            {data.file_type}
          </div>
        </div>

        <div className="space-y-1">
          <span className="text-xs text-slate-400 font-medium block">MIME Type</span>
          <div className="font-mono text-xs text-slate-600 truncate" title={data.mime_type}>
            {data.mime_type}
          </div>
        </div>

        <div className="space-y-1">
          <span className="text-xs text-slate-400 font-medium block">File Size</span>
          <div className="font-medium text-slate-700 flex items-center space-x-1">
            <HardDrive className="w-3.5 h-3.5 text-slate-400" />
            <span>{formatBytes(data.file_size_bytes)}</span>
          </div>
        </div>

        <div className="space-y-1">
          <span className="text-xs text-slate-400 font-medium block">Total Pages</span>
          <div className="font-medium text-slate-700 flex items-center space-x-1">
            <Layers className="w-3.5 h-3.5 text-slate-400" />
            <span>{data.page_count} {data.page_count === 1 ? 'Page' : 'Pages'}</span>
          </div>
        </div>

        <div className="space-y-1">
          <span className="text-xs text-slate-400 font-medium block">Upload Time</span>
          <div className="font-medium text-slate-700 flex items-center space-x-1 text-xs">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            <span>{formatDate(data.upload_timestamp)}</span>
          </div>
        </div>

      </div>
    </div>
  );
};
