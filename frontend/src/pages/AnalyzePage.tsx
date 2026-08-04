import React, { useState } from 'react';
import { FileUpload } from '../components/FileUpload';
import { ProcessingLoader } from '../components/ProcessingLoader';
import { DocumentInfoCard } from '../components/DocumentInfoCard';
import { ReportInfoCard } from '../components/ReportInfoCard';
import { ExtractedContentViewer } from '../components/ExtractedContentViewer';
import { MappedFeaturesDashboard } from '../components/MappedFeaturesDashboard';
import { TechnicalDetails } from '../components/TechnicalDetails';
import { analyzeDocuments } from '../services/api';
import type { DocumentAnalysisResult } from '../types/reader';
import { RefreshCw, Sparkles, AlertCircle, Layers, FileText, CheckCircle2 } from 'lucide-react';

export const AnalyzePage: React.FC = () => {
  const [state, setState] = useState<'upload' | 'processing' | 'results'>('upload');
  const [results, setResults] = useState<DocumentAnalysisResult[]>([]);
  const [activeDocIndex, setActiveDocIndex] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleFilesSelected = async (files: File[]) => {
    setState('processing');
    setErrorMsg(null);

    try {
      // Call backend REST API endpoint with all selected files for this session
      const resList = await analyzeDocuments(files);
      setResults(resList);
      setActiveDocIndex(0);
      setState('results');
    } catch (err: any) {
      console.error('Extraction error:', err);
      setErrorMsg(err.message || 'Failed to process document(s). Make sure backend server is running.');
      setState('upload');
    }
  };

  const handleReset = () => {
    setState('upload');
    setResults([]);
    setActiveDocIndex(0);
    setErrorMsg(null);
  };

  const activeResult = results[activeDocIndex] || results[0];

  return (
    <div className="space-y-8 py-6">
      
      {/* Page Title & Subtitle */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-100 text-sky-800 text-xs font-bold">
          <Sparkles className="w-3.5 h-3.5 text-sky-600" />
          <span>Intelligent Document Analysis</span>
        </div>
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Analyze Medical Reports
        </h2>
        <p className="text-slate-500 text-sm max-w-lg mx-auto">
          Upload 1 or multiple health records, lab reports, or datasets to extract structured clinical data.
        </p>
      </div>

      {/* Error Alert */}
      {errorMsg && (
        <div className="max-w-2xl mx-auto p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-3 text-rose-800 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-bold block">Processing Failure</span>
            <span>{errorMsg}</span>
          </div>
        </div>
      )}

      {/* State 1: Upload */}
      {state === 'upload' && (
        <div className="py-4">
          <FileUpload onFilesSelected={handleFilesSelected} />
        </div>
      )}

      {/* State 2: Processing */}
      {state === 'processing' && <ProcessingLoader />}

      {/* State 3: Results Presentation */}
      {state === 'results' && results.length > 0 && activeResult && (
        <div className="space-y-8 max-w-5xl mx-auto animate-fade-in">
          
          {/* Batch Summary Header */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center font-bold">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-base font-bold text-slate-900">
                    Session Results ({results.length} {results.length === 1 ? 'Document' : 'Documents'})
                  </span>
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold flex items-center space-x-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    <span>Processed</span>
                  </span>
                </div>
                <span className="text-xs text-slate-500">
                  Select document tab below to inspect extracted clinical content
                </span>
              </div>
            </div>

            <button
              onClick={handleReset}
              className="flex items-center space-x-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Analyze Another Batch</span>
            </button>
          </div>

          {/* Document Tab Switcher (if >1 document) */}
          {results.length > 1 && (
            <div className="flex items-center space-x-2 overflow-x-auto p-1.5 bg-slate-200/60 rounded-2xl border border-slate-200">
              {results.map((res, idx) => (
                <button
                  key={res.document_id || idx}
                  onClick={() => setActiveDocIndex(idx)}
                  className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                    activeDocIndex === idx
                      ? 'bg-white text-sky-700 shadow-sm border border-slate-200/80'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                  }`}
                >
                  <FileText className={`w-4 h-4 ${activeDocIndex === idx ? 'text-sky-600' : 'text-slate-400'}`} />
                  <span className="truncate max-w-xs">{res.source_file}</span>
                  {res.status === 'EXACT_DUPLICATE' && (
                    <span className="px-1.5 py-0.5 text-[10px] bg-amber-100 text-amber-800 rounded-md uppercase font-semibold">
                      Duplicate
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}

          {/* Active Document Duplicate Banner */}
          {activeResult.status === 'EXACT_DUPLICATE' && (
            <div className="p-4 bg-amber-50 border-2 border-amber-300 rounded-2xl flex items-start space-x-3 text-amber-900 shadow-xs">
              <Sparkles className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-bold text-base block">Duplicate Document Identified in Batch</span>
                <p className="text-xs text-amber-800 leading-relaxed">
                  This file is identical to another document within this batch (Match ID: <span className="font-mono font-bold">{activeResult.matched_document_id}</span>). Deduplication saved processing compute.
                </p>
              </div>
            </div>
          )}

          {/* Cards Grid: Document Info & Report Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <DocumentInfoCard data={activeResult} />
            <ReportInfoCard data={activeResult} />
          </div>

          {/* Extracted Text Content Card */}
          <ExtractedContentViewer pages={activeResult.pages} />

          {/* Mapped Features Dashboard (Contract 2 Feature Mapper Results) */}
          <MappedFeaturesDashboard
            mapperOutput={activeResult.mapper_output}
            error={activeResult.mapper_output_error}
          />

          {/* Expandable Technical Details (Extraction Log & Raw JSON) */}
          <TechnicalDetails data={activeResult} />

        </div>
      )}

    </div>
  );
};
