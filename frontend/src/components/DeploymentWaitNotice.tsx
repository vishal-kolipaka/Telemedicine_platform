import React from 'react';
import { Info, Sparkles } from 'lucide-react';

interface Props {
  title?: string;
  message?: string;
  subtext?: string;
  className?: string;
}

export const DeploymentWaitNotice: React.FC<Props> = ({
  title = 'First analysis may take a little longer',
  message = 'Because !Health Prism is running on a free-tier deployment, the backend service may need a moment to wake up before processing begins. Please wait while we complete the analysis.',
  subtext = 'Thank you for your patience.',
  className = '',
}) => {
  return (
    <div
      className={`mx-auto max-w-md w-full p-3.5 sm:p-4 rounded-2xl bg-sky-50/80 border border-sky-200/80 shadow-xs text-left text-xs transition-all animate-fade-in ${className}`}
    >
      <div className="flex items-start space-x-3">
        <div className="p-1.5 rounded-xl bg-sky-100 text-sky-600 shrink-0 mt-0.5 shadow-2xs">
          <Info className="w-4 h-4" />
        </div>
        <div className="space-y-1 flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h4 className="font-bold text-sky-950 text-xs sm:text-[13px] tracking-tight truncate">
              {title}
            </h4>
            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-sky-100/90 text-sky-700 text-[10px] font-semibold shrink-0">
              <Sparkles className="w-2.5 h-2.5 text-sky-600" />
              <span>Service Warmup</span>
            </span>
          </div>
          <p className="text-slate-600 leading-relaxed font-normal text-[11px] sm:text-xs">
            {message}
          </p>
          {subtext && (
            <p className="text-[10px] sm:text-[11px] font-medium text-sky-700/80 pt-0.5">
              {subtext}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
