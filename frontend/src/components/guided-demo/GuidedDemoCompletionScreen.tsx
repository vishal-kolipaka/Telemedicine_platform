import React from 'react';
import {
  ArrowRight,
  Brain,
  Calendar,
  ShieldCheck,
  Award,
  Layers,
} from 'lucide-react';

interface Props {
  onReturnToDashboard: () => void;
}

export const GuidedDemoCompletionScreen: React.FC<Props> = ({ onReturnToDashboard }) => {
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center py-8 px-4 sm:px-6 animate-fade-in text-slate-100">
      
      {/* Central Hero Completion Card */}
      <div className="w-full max-w-4xl bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950 border-2 border-cyan-400/80 rounded-3xl p-6 sm:p-10 shadow-2xl shadow-blue-950/80 space-y-8 relative overflow-hidden guided-blink-glow-card">
        
        {/* Subtle background glow accents */}
        <div className="absolute -top-24 -right-24 w-72 h-72 bg-sky-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-72 h-72 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />

        {/* Top Header Badge & Title */}
        <div className="text-center space-y-3 relative z-10">
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-gradient-to-r from-amber-400 via-orange-500 to-amber-500 text-slate-950 text-xs font-black uppercase tracking-wider shadow-lg shadow-amber-500/20">
            <Award className="w-4 h-4 text-slate-950" />
            <span>🎯 GUIDED DEMO COMPLETE</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight pt-1">
            Guided Demo Complete
          </h1>

          <p className="text-base sm:text-lg text-cyan-200 font-semibold max-w-2xl mx-auto">
            Thank you for exploring <span className="text-white font-extrabold">!Health Prism</span>.
          </p>

          <p className="text-xs sm:text-sm text-slate-300 max-w-2xl mx-auto leading-relaxed pt-1">
            You've seen how <strong className="text-white">!Health Prism</strong> brings together Clinical, Wearable, and Gut Microbiome data to create an explainable metabolic health assessment, personalized recommendations, and a structured progress plan.
          </p>
        </div>

        {/* Visual Journey Flow Summary */}
        <div className="space-y-3 relative z-10">
          <div className="text-[11px] font-black uppercase tracking-wider text-slate-400 text-center">
            THE !HEALTH PRISM END-TO-END WORKFLOW
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Step 1: Multimodal Data */}
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 hover:border-cyan-400/50 transition-all space-y-2 text-center sm:text-left">
              <div className="w-8 h-8 rounded-xl bg-sky-500/20 border border-sky-400/30 text-sky-300 flex items-center justify-center mx-auto sm:mx-0">
                <Layers className="w-4 h-4" />
              </div>
              <div className="text-xs font-black text-cyan-200">1. Multimodal Input</div>
              <p className="text-[11px] text-slate-300 leading-snug">
                Clinical labs, wearable metrics, gut microbiome & family history extracted & verified.
              </p>
            </div>

            {/* Step 2: Explainable Assessment */}
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 hover:border-cyan-400/50 transition-all space-y-2 text-center sm:text-left">
              <div className="w-8 h-8 rounded-xl bg-indigo-500/20 border border-indigo-400/30 text-indigo-300 flex items-center justify-center mx-auto sm:mx-0">
                <Brain className="w-4 h-4" />
              </div>
              <div className="text-xs font-black text-indigo-200">2. Metabolic Risk & Evidence</div>
              <p className="text-[11px] text-slate-300 leading-snug">
                Five metabolic conditions evaluated with transparent SHAP explanations & signal sources.
              </p>
            </div>

            {/* Step 3: Personalized Guidance */}
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 hover:border-cyan-400/50 transition-all space-y-2 text-center sm:text-left">
              <div className="w-8 h-8 rounded-xl bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 flex items-center justify-center mx-auto sm:mx-0">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div className="text-xs font-black text-emerald-200">3. Actionable Guidance</div>
              <p className="text-[11px] text-slate-300 leading-snug">
                Personalized nutrition, activity & lifestyle pillars backed by clinical guidelines.
              </p>
            </div>

            {/* Step 4: Trackable Routine */}
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 hover:border-cyan-400/50 transition-all space-y-2 text-center sm:text-left">
              <div className="w-8 h-8 rounded-xl bg-amber-500/20 border border-amber-400/30 text-amber-300 flex items-center justify-center mx-auto sm:mx-0">
                <Calendar className="w-4 h-4" />
              </div>
              <div className="text-xs font-black text-amber-200">4. Trackable Progress Routine</div>
              <p className="text-[11px] text-slate-300 leading-snug">
                Step-by-step daily habit checklists with unlockable days & downloadable plan PDF.
              </p>
            </div>
          </div>
        </div>

        {/* Polished Core Philosophy Callout */}
        <div className="p-5 rounded-2xl bg-gradient-to-r from-blue-900/60 via-indigo-900/60 to-purple-900/60 border border-cyan-400/30 text-center space-y-1.5 relative z-10">
          <div className="text-base sm:text-lg font-black text-white tracking-wide">
            "From multiple health signals to one clearer view of metabolic health."
          </div>
          <div className="text-xs font-semibold text-cyan-300">
            Not just one view of health.
          </div>
        </div>

        {/* Primary Final CTA Button */}
        <div className="text-center pt-2 relative z-10">
          <button
            type="button"
            onClick={onReturnToDashboard}
            className="inline-flex items-center space-x-2.5 px-8 py-4 bg-gradient-to-r from-amber-400 via-orange-500 to-amber-500 hover:from-amber-300 hover:to-orange-400 text-slate-950 font-black text-sm sm:text-base rounded-2xl shadow-2xl shadow-orange-500/40 transition-all hover:scale-105 active:scale-95 cursor-pointer guided-blink-glow-orange border border-white/30"
          >
            <span>Return to Dashboard</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>

      </div>

    </div>
  );
};
