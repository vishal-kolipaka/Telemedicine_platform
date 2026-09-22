import React from 'react';
import { Clock, Zap } from 'lucide-react';

interface Props {
  title?: string;
  message?: string;
  subtext?: string;
  className?: string;
}

export const DeploymentWaitNotice: React.FC<Props> = ({
  title = 'First analysis may take a little longer',
  message = 'Because !Health Prism is running on a free-tier deployment, the backend service may need a moment to wake up before processing begins. Please wait while we complete the analysis.',
  subtext = 'Thank you for your patience while models initialize.',
  className = '',
}) => {
  return (
    <div
      className={`mx-auto max-w-lg w-full p-4 sm:p-5 rounded-2xl bg-gradient-to-br from-white via-sky-50/90 to-cyan-50/70 border-2 border-sky-400 service-warmup-card text-left transition-all animate-fade-in ${className}`}
    >
      {/* Eye-Catching Header Badges */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600 text-white text-[11px] font-black shadow-xs tracking-wider uppercase">
          <Zap className="w-3.5 h-3.5 fill-white text-white" />
          <span>Cloud Server Wake-Up (~1–2 Mins)</span>
        </span>
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold border border-emerald-300">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span>Engine Active</span>
        </span>
      </div>

      {/* Main Content Area */}
      <div className="flex items-start space-x-3.5">
        <div className="p-2 rounded-xl bg-gradient-to-br from-sky-500 to-cyan-600 text-white shadow-md shadow-sky-500/25 shrink-0 mt-0.5">
          <Clock className="w-4 h-4" />
        </div>
        <div className="space-y-2 flex-1 min-w-0">
          <h4 className="font-black text-slate-900 text-sm sm:text-base tracking-tight leading-snug">
            {title}
          </h4>
          <p className="text-slate-700 leading-relaxed font-normal text-xs sm:text-[13px]">
            {message}
          </p>
          
          {/* Action / Reassurance Strip */}
          <div className="p-2.5 rounded-xl bg-sky-100/90 border border-sky-300/80 flex items-center space-x-2 text-[11px] sm:text-xs text-sky-950 font-semibold shadow-2xs">
            <span className="text-sky-600 font-bold shrink-0">ℹ️</span>
            <span>Live analysis is actively running in the cloud — please keep this page open.</span>
          </div>

          {/* Animated Shimmer Progress Bar */}
          <div className="w-full bg-sky-200/80 rounded-full h-1.5 overflow-hidden relative mt-2.5">
            <div className="w-full h-full bg-gradient-to-r from-sky-400 via-cyan-300 to-indigo-500 rounded-full notice-shimmer-bar" />
          </div>

          {subtext && (
            <div className="flex items-center justify-between pt-1 text-[11px] text-sky-800 font-medium">
              <span>{subtext}</span>
              <span className="text-[10px] font-mono text-slate-400">Processing...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
