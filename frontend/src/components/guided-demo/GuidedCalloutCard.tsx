import React from 'react';
import { ArrowRight, Sparkles } from 'lucide-react';

interface Props {
  badge?: string;
  title: string;
  description: string | React.ReactNode;
  actionInstruction?: string;
  nextLabel?: string;
  onNext?: () => void;
  pointerDirection?: 'up' | 'down' | 'left' | 'right' | 'none';
  className?: string;
}

export const GuidedCalloutCard: React.FC<Props> = ({
  badge = '🎯 GUIDED DEMO',
  title,
  description,
  actionInstruction,
  nextLabel,
  onNext,
  pointerDirection = 'none',
  className = '',
}) => {
  return (
    <div
      className={`relative z-20 p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-blue-950 via-sky-900 to-indigo-950 text-white border-2 border-cyan-400 shadow-2xl shadow-blue-950/50 space-y-3 animate-fade-in guided-blink-glow-card max-w-xl ${className}`}
    >
      {/* Pointer Arrow Indicator if specified */}
      {pointerDirection === 'down' && (
        <div className="absolute -bottom-2.5 left-8 w-5 h-5 bg-gradient-to-r from-sky-900 to-indigo-950 border-r-2 border-b-2 border-cyan-400 rotate-45" />
      )}
      {pointerDirection === 'up' && (
        <div className="absolute -top-2.5 left-8 w-5 h-5 bg-gradient-to-r from-blue-950 to-sky-900 border-l-2 border-t-2 border-cyan-400 rotate-45" />
      )}

      {/* Header Row: Badge & Title */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center space-x-2">
          <span className="px-2.5 py-0.5 rounded-full bg-amber-400 text-slate-950 text-[10px] font-black tracking-wider uppercase shadow-xs">
            {badge}
          </span>
          <span className="text-xs font-black text-cyan-200 tracking-wide flex items-center space-x-1">
            <Sparkles className="w-3 h-3 text-cyan-300 inline" />
            <span>{title}</span>
          </span>
        </div>
      </div>

      {/* Body / Description */}
      <div className="text-xs text-slate-100 leading-relaxed font-medium">
        {description}
      </div>

      {/* Action Footer: Either Instruction or Next Button */}
      {(actionInstruction || (nextLabel && onNext)) && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pt-2 border-t border-white/20">
          {actionInstruction && (
            <span className="text-xs font-extrabold text-amber-300">
              {actionInstruction}
            </span>
          )}

          {nextLabel && onNext && (
            <button
              type="button"
              onClick={onNext}
              className="flex items-center space-x-1.5 px-4 py-2 bg-gradient-to-r from-amber-400 via-orange-500 to-amber-500 hover:from-amber-300 hover:to-orange-400 text-slate-950 font-black text-xs rounded-xl shadow-lg shadow-amber-500/30 transition-all hover:scale-105 active:scale-95 cursor-pointer shrink-0 ml-auto guided-blink-glow-orange"
            >
              <span>{nextLabel}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      )}
    </div>
  );
};
