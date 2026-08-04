import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Terminal, Code2, Clock } from 'lucide-react';
import type { DocumentAnalysisResult } from '../types/reader';

interface Props {
  data: DocumentAnalysisResult;
}

export const TechnicalDetails: React.FC<Props> = ({ data }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'log' | 'json'>('log');

  return (
    <div className="telemed-card border-slate-200 overflow-hidden">
      
      {/* Accordion Toggle Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-4 flex items-center justify-between bg-slate-50/70 hover:bg-slate-100/80 transition-colors text-left"
      >
        <div className="flex items-center space-x-2.5">
          <Terminal className="w-4 h-4 text-slate-500" />
          <span className="text-sm font-bold text-slate-800">
            Show Technical Details & Diagnostic Logs
          </span>
          <span className="text-xs text-slate-400 font-normal">
            ({data.extraction_log?.length || 0} log events)
          </span>
        </div>

        <div className="flex items-center space-x-2 text-xs font-semibold text-sky-700">
          <span>{isOpen ? 'Hide Details' : 'Expand Details'}</span>
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Expanded Content */}
      {isOpen && (
        <div className="p-6 border-t border-slate-200/80 space-y-4 animate-fade-in bg-white">
          
          {/* Internal Tab Switcher */}
          <div className="flex items-center space-x-2 border-b border-slate-200 pb-2">
            <button
              onClick={() => setActiveTab('log')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'log'
                  ? 'bg-slate-900 text-white'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              <span>Extraction Log</span>
            </button>

            <button
              onClick={() => setActiveTab('json')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'json'
                  ? 'bg-slate-900 text-white'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>Raw Output JSON</span>
            </button>
          </div>

          {/* Tab 1: Extraction Log */}
          {activeTab === 'log' && (
            <div className="bg-slate-900 text-slate-100 rounded-xl p-4 font-mono text-xs max-h-80 overflow-y-auto space-y-2 border border-slate-800">
              {data.extraction_log && data.extraction_log.length > 0 ? (
                data.extraction_log.map((log, idx) => (
                  <div key={idx} className="flex items-start space-x-2 text-slate-300">
                    <span className="text-slate-500 shrink-0">[{log.timestamp}]</span>
                    <span
                      className={`font-semibold shrink-0 uppercase px-1 rounded-xs text-[10px] ${
                        log.level === 'ERROR'
                          ? 'bg-rose-900/80 text-rose-300'
                          : log.level === 'WARNING'
                          ? 'bg-amber-900/80 text-amber-300'
                          : 'bg-sky-900/80 text-sky-300'
                      }`}
                    >
                      {log.level}
                    </span>
                    <span className="text-slate-400 shrink-0">[{log.module}]:</span>
                    <span className="text-slate-200 flex-1">{log.message}</span>
                  </div>
                ))
              ) : (
                <div className="text-slate-500 italic">No log entries recorded.</div>
              )}
            </div>
          )}

          {/* Tab 2: Raw JSON */}
          {activeTab === 'json' && (
            <div className="bg-slate-900 text-emerald-400 rounded-xl p-4 font-mono text-xs max-h-96 overflow-y-auto border border-slate-800 leading-relaxed">
              <pre>{JSON.stringify(data, null, 2)}</pre>
            </div>
          )}

        </div>
      )}

    </div>
  );
};
