import React, { useEffect } from 'react';
import { ArrowLeft, Sparkles } from 'lucide-react';
import { GuidedDemoInstructions } from './guided-demo/GuidedDemoInstructions';
import { GuidedDemoIntroduction } from './guided-demo/GuidedDemoIntroduction';

interface Props {
  step: number;
  setStep: (step: number) => void;
  onExit: () => void;
  onContinueToAnalyze: () => void;
}

export const GuidedDemoPage: React.FC<Props> = ({ step, setStep, onExit, onContinueToAnalyze }) => {
  /* Scroll to top whenever the step changes */
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [step]);

  return (
    <div className="guided-fade-in">

      {/* ── Demo Top Bar ── */}
      <div className="flex items-center justify-between mb-4 px-1">

        {/* Left: Exit */}
        <button
          onClick={onExit}
          className="group flex items-center space-x-2 text-sm text-slate-500 hover:text-orange-600 transition-colors font-semibold"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
          <span>Exit Demo</span>
        </button>

        {/* Center: Colorful progress pill */}
        <div className="flex items-center space-x-2 px-4 py-1.5 rounded-full bg-gradient-to-r from-sky-600 to-cyan-600 text-white text-xs font-bold shadow-md shadow-sky-600/20">
          <Sparkles className="w-3.5 h-3.5" />
          <span>{step === 0 ? 'Guided Demo • Introduction' : `Guided Demo • Step ${String(step).padStart(2, '0')}`}</span>
        </div>

        {/* Right: Spacer for alignment */}
        <div className="w-24" />
      </div>

      {/* ── Step Content ── */}
      {step === 0 && (
        <GuidedDemoInstructions onContinue={() => setStep(1)} />
      )}

      {step === 1 && (
        <GuidedDemoIntroduction onContinue={onContinueToAnalyze} />
      )}
    </div>
  );
};
