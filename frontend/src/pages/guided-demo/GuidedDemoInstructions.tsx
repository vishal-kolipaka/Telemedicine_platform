import React from 'react';
import { ArrowRight, Sparkles, Stethoscope, Layers, BrainCircuit, Target, HeartPulse } from 'lucide-react';

interface Props {
  onContinue: () => void;
}

const STEPS = [
  { number: '01', title: 'Why !Health Prism?', description: 'The problem and the idea.', icon: HeartPulse, gradient: 'from-rose-500 to-pink-600', bg: 'bg-gradient-to-br from-rose-50 to-pink-50', ring: 'ring-rose-200', numColor: 'text-rose-400' },
  { number: '02', title: 'Multimodal Health Data', description: 'Clinical, Wearable, & Gut Microbiome.', icon: Layers, gradient: 'from-sky-500 to-blue-600', bg: 'bg-gradient-to-br from-sky-50 to-blue-50', ring: 'ring-sky-200', numColor: 'text-sky-400' },
  { number: '03', title: 'Fusion & Prediction', description: 'Modality processing & disease prediction.', icon: Stethoscope, gradient: 'from-violet-500 to-purple-600', bg: 'bg-gradient-to-br from-violet-50 to-purple-50', ring: 'ring-violet-200', numColor: 'text-violet-400' },
  { number: '04', title: 'Explainability', description: 'TreeSHAP model explanations.', icon: BrainCircuit, gradient: 'from-amber-500 to-orange-600', bg: 'bg-gradient-to-br from-amber-50 to-orange-50', ring: 'ring-amber-200', numColor: 'text-amber-400' },
  { number: '05', title: 'Personalized Insights', description: 'Decision support & recommendations.', icon: Target, gradient: 'from-emerald-500 to-teal-600', bg: 'bg-gradient-to-br from-emerald-50 to-teal-50', ring: 'ring-emerald-200', numColor: 'text-emerald-400' },
] as const;

export const GuidedDemoInstructions: React.FC<Props> = ({ onContinue }) => {
  return (
    <div className="max-w-3xl mx-auto py-2 px-4 flex flex-col" style={{ minHeight: 'calc(100vh - 180px)' }}>

      {/* Header — vibrant */}
      <div className="text-center space-y-3 mb-5 guided-fade-in-up">
        <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-gradient-to-r from-orange-500 to-amber-500 text-white text-xs font-black shadow-md shadow-orange-500/25 uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Guided Experience</span>
        </div>

        <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight leading-tight">
          Welcome to the{' '}
          <span className="prism-gradient-text">!</span>
          <span className="bg-gradient-to-r from-sky-600 via-sky-500 to-cyan-500 bg-clip-text text-transparent">
            Health Prism
          </span>{' '}
          Guided Demo
        </h1>

        <p className="text-slate-500 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
          Follow the recommended workflow to understand how !Health Prism brings together
          multiple dimensions of health data to generate <strong className="text-slate-700">explainable metabolic health insights</strong>.
        </p>
      </div>

      {/* "What you'll see" + Timeline */}
      <div className="flex-1">
        <div className="mb-3 guided-fade-in-up guided-stagger-1">
          <h2 className="text-sm font-black text-slate-800 uppercase tracking-wider">What you'll see</h2>
          <div className="w-12 h-0.5 bg-gradient-to-r from-sky-500 to-cyan-500 rounded-full mt-1" />
        </div>

        {/* Compact colorful timeline */}
        <div className="relative">
          {/* Vertical connector — rainbow gradient */}
          <div className="absolute left-5 top-5 bottom-5 w-0.5 bg-gradient-to-b from-rose-400 via-violet-400 to-emerald-400 rounded-full" />

          <div className="space-y-0">
            {STEPS.map((step, index) => {
              const Icon = step.icon;
              return (
                <div
                  key={step.number}
                  className={`relative flex items-center space-x-4 py-2.5 px-2 rounded-xl transition-all hover:bg-slate-50 hover:scale-[1.01] guided-fade-in-up guided-stagger-${index + 1}`}
                >
                  {/* Step icon — gradient background */}
                  <div
                    className={`relative z-10 flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br ${step.gradient} flex items-center justify-center shadow-md`}
                  >
                    <Icon className="w-4.5 h-4.5 text-white" />
                  </div>

                  {/* Text */}
                  <div className="flex items-center space-x-2 min-w-0">
                    <span className={`text-[10px] font-mono font-black ${step.numColor}`}>{step.number}</span>
                    <h3 className="text-sm font-bold text-slate-900">{step.title}</h3>
                    <span className="hidden sm:inline text-xs text-slate-400 font-medium">— {step.description}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Continue Button — vibrant, always visible */}
      <div className="flex flex-col items-center space-y-3 pt-4 pb-2 guided-fade-in-up guided-stagger-6">
        <button
          onClick={onContinue}
          className="group flex items-center space-x-3 px-10 py-4 bg-gradient-to-r from-sky-600 via-sky-500 to-cyan-600 hover:from-sky-700 hover:to-cyan-700 text-white font-extrabold text-base rounded-2xl shadow-xl shadow-sky-600/30 transition-all transform hover:scale-[1.03] active:scale-[0.97]"
        >
          <span>Continue</span>
          <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
        </button>

        <span className="text-xs font-semibold text-slate-400 tracking-wide">
          Guided Demo&nbsp;&nbsp;•&nbsp;&nbsp;Introduction
        </span>
      </div>
    </div>
  );
};
