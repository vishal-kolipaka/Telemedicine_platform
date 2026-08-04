import React from 'react';
import { CalendarCheck, AlertTriangle, CheckCircle2, XCircle, Award } from 'lucide-react';
import type { DocumentAnalysisResult } from '../types/reader';

interface Props {
  data: DocumentAnalysisResult;
}

export const ReportInfoCard: React.FC<Props> = ({ data }) => {
  const qualityPassed = data?.quality_check?.passed ?? true;

  return (
    <div className="telemed-card p-6 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
            <CalendarCheck className="w-4 h-4" />
          </div>
          <h3 className="text-base font-bold text-slate-900">Report & Quality Assessment</h3>
        </div>
        
        {/* Quality Status Pill */}
        <div
          className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold ${
            qualityPassed
              ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
              : 'bg-rose-100 text-rose-800 border border-rose-300'
          }`}
        >
          {qualityPassed ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
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
