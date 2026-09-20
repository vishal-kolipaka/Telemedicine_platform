import React, { useState } from 'react';
import { AlignLeft, Copy, Check, Layers, ChevronDown, ChevronUp, FileText, ArrowRight } from 'lucide-react';
import type { DocumentPage } from '../types/reader';

interface Props {
  pages: DocumentPage[];
  isGuidedDemo?: boolean;
  onNextGuidedStep?: () => void;
}

export const ExtractedContentViewer: React.FC<Props> = ({
  pages,
  isGuidedDemo = false,
  onNextGuidedStep,
}) => {
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
    <div
      id="guided-extracted-content"
      className={`telemed-card p-5 space-y-4 transition-all duration-300 ${
        isGuidedDemo
          ? 'border-2 border-sky-400 ring-4 ring-sky-400/30 shadow-2xl shadow-sky-500/20 guided-blink-glow-card'
          : ''
      }`}
    >
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
            className={`flex items-center space-x-2 px-5 py-2.5 rounded-2xl transition-all shadow-md cursor-pointer ${
              isGuidedDemo
                ? 'bg-gradient-to-r from-orange-500 via-amber-500 to-sky-600 text-white font-black border-2 border-amber-300 ring-4 ring-orange-400/80 guided-blink-glow-orange scale-105'
                : 'bg-sky-50 hover:bg-sky-100 text-sky-700 text-xs font-bold border border-sky-200 shadow-2xs'
            }`}
          >
            <FileText className={`w-4 h-4 ${isGuidedDemo ? 'text-white' : 'text-sky-600'}`} />
            <span className={isGuidedDemo ? 'text-xs font-black tracking-wide' : ''}>
              {isExpanded ? 'Hide Raw Text' : 'View Raw Extracted Text'}
            </span>
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Guided Demo Step 3B Callout - High Visibility Vibrant Blue/Cyan Design */}
      {isGuidedDemo && (
        <div className="p-6 rounded-3xl bg-gradient-to-r from-sky-900 via-blue-900 to-indigo-950 text-white border-2 border-cyan-400 shadow-2xl shadow-blue-950/50 space-y-4 animate-fade-in guided-blink-glow-card">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center space-x-2.5">
              <span className="px-3 py-1 rounded-full bg-amber-400 text-slate-950 text-xs font-black tracking-wider uppercase shadow-md">
                🎯 GUIDED DEMO • STEP 03
              </span>
              <span className="text-sm font-black text-cyan-200 tracking-wide">
                Extracted Document Content
              </span>
            </div>
            <span className="text-xs font-extrabold text-white bg-white/20 backdrop-blur-md px-3 py-1 rounded-full border border-white/30">
              Pipeline Stage 1: Ingestion
            </span>
          </div>

          <p className="text-sm text-slate-100 leading-relaxed font-medium">
            The <strong className="text-cyan-300 font-extrabold underline underline-offset-4">Document Reader</strong> has extracted the raw text and structured information from the uploaded report. This is the information that is passed into the next stage of the pipeline for feature mapping.
          </p>

          {/* Pipeline flow visual */}
          <div className="flex flex-wrap items-center gap-2.5 py-3 px-4 bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 text-xs font-bold text-white shadow-inner">
            <span className="text-cyan-300">📄 Multimodal Report</span>
            <span className="text-amber-400 font-black text-base">→</span>
            <span className="px-3 py-1 bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-xl font-black shadow-md border border-cyan-300">
              ⚡ Document Reader (OCR &amp; Parser)
            </span>
            <span className="text-amber-400 font-black text-base">→</span>
            <span className="text-white font-extrabold">
              Structured Key-Values &amp; Raw Text
            </span>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-2 border-t border-white/15">
            <span className="text-xs text-cyan-200 font-semibold">
              Tip: Click the blinking <strong className="text-white">"View Raw Extracted Text"</strong> button above to inspect OCR output.
            </span>
            <button
              type="button"
              onClick={onNextGuidedStep}
              className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-amber-400 via-orange-500 to-amber-500 hover:from-amber-300 hover:to-orange-400 text-slate-950 font-black text-xs rounded-2xl shadow-xl shadow-amber-500/30 transition-all hover:scale-105 active:scale-95 cursor-pointer shrink-0 guided-blink-glow-orange"
            >
              <span>Next: Mapped Features Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

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
