import React from 'react';
import { CalendarCheck, AlertTriangle, CheckCircle2, XCircle, Award, ArrowRight } from 'lucide-react';
import type { DocumentAnalysisResult } from '../types/reader';

interface Props {
  data: DocumentAnalysisResult;
  isGuidedDemo?: boolean;
  onNextGuidedStep?: () => void;
}

export const ReportInfoCard: React.FC<Props> = ({ data, isGuidedDemo = false, onNextGuidedStep }) => {
  const qualityPassed = data?.quality_check?.passed ?? true;

  return (
    <div id="guided-report-quality" className={`telemed-card p-6 space-y-4 transition-all duration-300 ${
      isGuidedDemo ? 'ring-2 ring-amber-400/80 shadow-xl shadow-amber-500/10' : ''
    }`}>
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
            <CalendarCheck className="w-4 h-4" />
          </div>
          <h3 className="text-base font-bold text-slate-900">Report & Quality Assessment</h3>
        </div>
        
        {/* Quality Status Pill */}
        <div
          className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-full text-xs font-black transition-all ${
            qualityPassed
              ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
              : 'bg-rose-100 text-rose-800 border border-rose-300'
          } ${isGuidedDemo ? 'ring-4 ring-orange-400 ring-offset-2 guided-blink-glow-orange bg-emerald-500 text-white font-black shadow-lg shadow-emerald-500/40' : ''}`}
        >
          {qualityPassed ? (
            <>
              <CheckCircle2 className={`w-4 h-4 ${isGuidedDemo ? 'text-white' : 'text-emerald-600'}`} />
              <span>QUALITY PASSED</span>
            </>
          ) : (
            <>
              <XCircle className="w-3.5 h-3.5 text-rose-600" />
              <span>QUALITY CHECK FAILED</span>
            </>
          )}
        </div>
      </div>

      {/* Guided Demo Step 3A Callout - Eye-Catching Orange & Amber Gradient */}
      {isGuidedDemo && (
        <div className="p-6 rounded-3xl bg-gradient-to-r from-amber-600 via-orange-600 to-rose-600 text-white border-2 border-amber-300 shadow-2xl shadow-orange-600/30 space-y-3 animate-fade-in guided-blink-glow-card">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <span className="px-3 py-1 rounded-full bg-slate-950 text-amber-300 text-xs font-black tracking-wider uppercase shadow-md border border-amber-400">
                🎯 GUIDED DEMO • STEP 03
              </span>
              <span className="text-sm font-black text-white">Extraction Quality</span>
            </div>
            <span className="text-xs font-black text-emerald-950 bg-emerald-300 px-3 py-1 rounded-full shadow-xs">
              ✓ Verified Passed
            </span>
          </div>

          <p className="text-sm text-amber-50 leading-relaxed font-medium">
            The document has been successfully processed and passed the system's extraction quality checks. This indicates that the report was read and structured with sufficient confidence for the next stage.
          </p>

          <div className="flex items-center justify-end pt-2 border-t border-white/20">
            <button
              type="button"
              onClick={onNextGuidedStep}
              className="flex items-center space-x-2 px-6 py-3 bg-white hover:bg-amber-50 text-orange-700 text-xs font-black rounded-2xl shadow-xl shadow-black/25 transition-all hover:scale-105 active:scale-95 cursor-pointer guided-blink-glow-orange"
            >
              <span>Next: Extracted Document Content</span>
              <ArrowRight className="w-4 h-4 text-orange-600" />
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 text-sm">
        
        {/* Report Date */}
        <div className="space-y-1">
          <span className="text-xs text-slate-400 font-medium block">Report Date</span>
          <div className="font-bold text-slate-800 text-base">
            {data.report_date ? data.report_date : 'Not Detected'}
          </div>
        </div>

        {/* Date Confidence */}
        <div className="space-y-1">
          <span className="text-xs text-slate-400 font-medium block">Date Confidence</span>
          {data.report_date_confidence ? (
            <span
              className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                data.report_date_confidence === 'HIGH'
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-amber-50 text-amber-700 border border-amber-200'
              }`}
            >
              {data.report_date_confidence}
            </span>
          ) : (
            <span className="text-xs text-slate-400">N/A</span>
          )}
        </div>

        {/* Extraction Confidence */}
        <div className="space-y-1 col-span-2 pt-2 border-t border-slate-100">
          <span className="text-xs text-slate-400 font-medium block">Overall Extraction Confidence</span>
          <div className="flex items-center space-x-2">
            <Award
              className={`w-4 h-4 ${
                data.extraction_confidence === 'high'
                  ? 'text-emerald-600'
                  : data.extraction_confidence === 'medium'
                  ? 'text-amber-500'
                  : 'text-rose-500'
              }`}
            />
            <span className="font-semibold capitalize text-slate-800">
              {data.extraction_confidence} Confidence Processing
            </span>
          </div>
        </div>

        {/* Quality Failure Reason if applicable */}
        {!qualityPassed && data.quality_check.reason && (
          <div className="col-span-2 p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-2 text-rose-800 text-xs">
            <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block">Issue Detected:</span>
              <span>{data.quality_check.reason}</span>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
