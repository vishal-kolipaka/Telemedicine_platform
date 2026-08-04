import React, { useState } from 'react';
import { AlignLeft, Copy, Check, Layers, ChevronDown, ChevronUp, FileText } from 'lucide-react';
import type { DocumentPage } from '../types/reader';

interface Props {
  pages: DocumentPage[];
}

export const ExtractedContentViewer: React.FC<Props> = ({ pages }) => {
  const [selectedPageIndex, setSelectedPageIndex] = useState(0);
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  if (!pages || pages.length === 0) {
    return (
      <div className="telemed-card p-8 text-center text-slate-400">
        No text content extracted from document.
      </div>
    );
  }

  const currentPage = pages[selectedPageIndex] || pages[0];
  const textLines = (currentPage.raw_text || '').split('\n');

  const handleCopy = () => {
    navigator.clipboard.writeText(currentPage.raw_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="telemed-card p-5 space-y-4">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
          <div className="w-9 h-9 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center font-bold">
            <AlignLeft className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-base font-extrabold text-slate-900">Extracted Document Content</h3>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold border border-slate-200">
                {textLines.length} lines • {currentPage.raw_text.length} chars
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium mt-0.5">
              Raw OCR & parsed text output from Document Reader
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          {/* Multi-page selector if >1 page */}
          {pages.length > 1 && isExpanded && (
            <div className="flex items-center space-x-1.5 bg-slate-100 p-1 rounded-xl text-xs font-medium text-slate-700">
              <Layers className="w-3.5 h-3.5 ml-1 text-slate-500" />
              {pages.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedPageIndex(idx)}
                  className={`px-2.5 py-1 rounded-lg transition-all ${
                    selectedPageIndex === idx
                      ? 'bg-white text-sky-700 font-bold shadow-xs'
                      : 'hover:text-slate-900'
                  }`}
                >
                  Page {idx + 1}
                </button>
              ))}
            </div>
          )}

          {/* Copy Button (only when expanded) */}
          {isExpanded && (
            <button
              onClick={handleCopy}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="text-emerald-700">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-slate-500" />
                  <span>Copy Text</span>
                </>
              )}
            </button>
          )}

          {/* Expand / Collapse Toggle Button */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center space-x-1.5 px-4 py-2 bg-sky-50 hover:bg-sky-100 text-sky-700 text-xs font-bold rounded-xl border border-sky-200 transition-all shadow-2xs"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>{isExpanded ? 'Hide Raw Text' : 'View Raw Extracted Text'}</span>
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Formatted Scrollable Text Viewer (Rendered ONLY when expanded) */}
      {isExpanded && (
        <div className="bg-slate-900 text-slate-100 rounded-2xl p-4 font-mono text-xs overflow-x-auto max-h-96 leading-relaxed shadow-inner border border-slate-800 animate-fade-in pt-3 mt-3 border-t border-slate-100">
          {textLines.map((line, idx) => (
            <div key={idx} className="flex hover:bg-slate-800/60 rounded-xs px-1 py-0.5">
              <span className="w-10 select-none text-slate-600 text-right pr-4 shrink-0 font-sans">
                {idx + 1}
              </span>
              <span className="whitespace-pre-wrap break-words flex-1 text-slate-200">
                {line || ' '}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
