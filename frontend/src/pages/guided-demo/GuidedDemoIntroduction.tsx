import React from 'react';
import {
  AlertTriangle,
  ArrowRight,
  BrainCircuit,
  Clock,
  Eye,
  Flame,
  HeartPulse,
  Layers,
  Lock,
  MessageSquare,
  Microscope,
  Shield,
  Zap,
} from 'lucide-react';

/* ──────────────────────── Data ──────────────────────── */

const LIMITATIONS = [
  { icon: Microscope,    label: 'Missing microbiome integration',          gradient: 'from-rose-500 to-pink-600',   bg: 'bg-gradient-to-br from-rose-50 to-pink-50',   border: 'border-rose-200' },
  { icon: Layers,        label: 'Fragmented health data',                  gradient: 'from-amber-500 to-orange-600', bg: 'bg-gradient-to-br from-amber-50 to-orange-50', border: 'border-amber-200' },
  { icon: Lock,          label: 'Black-box predictions',                   gradient: 'from-slate-600 to-slate-700',  bg: 'bg-gradient-to-br from-slate-50 to-gray-50',   border: 'border-slate-200' },
  { icon: Shield,        label: 'Limited personalization',                 gradient: 'from-violet-500 to-purple-600', bg: 'bg-gradient-to-br from-violet-50 to-purple-50', border: 'border-violet-200' },
  { icon: MessageSquare, label: 'No Generative AI clinician summaries',    gradient: 'from-sky-500 to-blue-600',     bg: 'bg-gradient-to-br from-sky-50 to-blue-50',     border: 'border-sky-200' },
  { icon: Clock,         label: 'Limited continuous monitoring',           gradient: 'from-cyan-500 to-teal-600',    bg: 'bg-gradient-to-br from-cyan-50 to-teal-50',    border: 'border-cyan-200' },
] as const;

const MODALITIES = [
  {
    emoji: '🏥',
    title: 'Clinical Data',
    subtitle: 'Lab results, vitals, medical history',
    gradient: 'from-sky-500 to-blue-600',
    bg: 'from-sky-50 to-blue-50',
    ring: 'ring-sky-300',
  },
  {
    emoji: '⌚',
    title: 'Wearable / CGM Data',
    subtitle: 'Heart rate, glucose patterns, activity',
    gradient: 'from-cyan-500 to-teal-600',
    bg: 'from-cyan-50 to-teal-50',
    ring: 'ring-cyan-300',
  },
  {
    emoji: '🦠',
    title: 'Gut Microbiome Data',
    subtitle: 'Microbial composition & diversity',
    gradient: 'from-violet-500 to-purple-600',
    bg: 'from-violet-50 to-purple-50',
    ring: 'ring-violet-300',
  },
] as const;

const OUTCOMES = [
  { icon: HeartPulse,   title: 'More complete metabolic health assessment', gradient: 'from-sky-500 to-blue-600' },
  { icon: Eye,          title: 'Explainable disease-risk predictions',      gradient: 'from-violet-500 to-purple-600' },
  { icon: BrainCircuit, title: 'Personalized decision support',             gradient: 'from-emerald-500 to-teal-600' },
] as const;

interface GuidedDemoIntroductionProps {
  onContinue?: () => void;
}

export const GuidedDemoIntroduction: React.FC<GuidedDemoIntroductionProps> = ({ onContinue }) => {
  return (
    <div className="max-w-4xl mx-auto py-6 px-4">

      {/* Page Title — large, bold, no duplicate badge */}
      <div className="text-center mb-2 guided-fade-in-up">
        <h1 className="text-5xl sm:text-6xl font-black text-slate-900 tracking-tight leading-none">
          <span className="prism-gradient-text text-6xl sm:text-7xl">!</span>{' '}
          <span className="bg-gradient-to-r from-sky-700 via-sky-600 to-cyan-600 bg-clip-text text-transparent">
            Health Prism
          </span>
        </h1>
        <p className="text-xl sm:text-2xl text-slate-500 font-semibold mt-3 italic tracking-tight">
          "Not Just One View of Health."
        </p>
        <div className="w-32 h-1 prism-spectrum mx-auto mt-4 rounded-full" />
      </div>

      {/* ───── SECTION A — THE PROBLEM ───── */}
      <section className="guided-section guided-fade-in-up guided-stagger-1">
        <div className="flex items-center space-x-3 mb-5">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-rose-500 to-pink-600 flex items-center justify-center shadow-lg shadow-rose-500/25">
            <AlertTriangle className="w-5 h-5 text-white" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">The Problem</h2>
        </div>

        <p className="text-slate-600 leading-relaxed max-w-3xl mb-6 text-base">
          Metabolic diseases are among the leading global health challenges.
          Gut microbiome composition plays a significant role, yet existing telemedicine platforms
          <strong className="text-rose-600"> largely ignore microbiome information</strong>.
        </p>

        <h3 className="text-xs font-black uppercase tracking-[0.15em] text-slate-400 mb-4">Current Limitations</h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {LIMITATIONS.map((item, i) => {
            const Icon = item.icon;
            return (
              <div
                key={i}
                className={`flex items-center space-x-3 p-3.5 rounded-xl border ${item.border} ${item.bg} hover:scale-[1.01] transition-transform guided-fade-in-up guided-stagger-${i + 1}`}
              >
                <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${item.gradient} flex items-center justify-center flex-shrink-0 shadow-md`}>
                  <Icon className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-bold text-slate-700">{item.label}</span>
              </div>
            );
          })}
        </div>

        <div className="mt-6 p-4 rounded-xl bg-gradient-to-r from-slate-50 to-sky-50/50 border border-slate-200">
          <p className="text-slate-600 leading-relaxed text-sm">
            There is a need for an <strong className="text-sky-700">intelligent, explainable, AI-driven platform</strong> that
            integrates gut microbiome profiles, wearable sensor data, and clinical information.
          </p>
        </div>
      </section>

      {/* ───── SECTION B — THE THOUGHT ───── */}
      <section className="guided-section guided-fade-in-up guided-stagger-2">
        <div className="relative text-center py-10 px-6 rounded-3xl bg-gradient-to-b from-slate-900 via-slate-800 to-sky-900 overflow-hidden">

          {/* Ambient glows */}
          <div className="absolute -top-12 -right-12 w-40 h-40 bg-sky-500/15 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-12 -left-12 w-40 h-40 bg-violet-500/15 rounded-full blur-3xl pointer-events-none" />

          <p className="relative text-xs uppercase tracking-[0.2em] font-black text-sky-400 mb-5">The Thought</p>

          <p className="relative text-slate-300 text-base sm:text-lg max-w-2xl mx-auto leading-relaxed mb-8">
            A person's metabolic health may look different when viewed through different sources of health information.
          </p>

          {/* Three perspectives */}
          <div className="relative flex flex-col sm:flex-row items-center justify-center gap-3 mb-8">
            <span className="px-4 py-2 rounded-xl bg-sky-500/20 border border-sky-400/30 text-sky-300 font-bold text-sm backdrop-blur-sm">
              Clinical Data
            </span>
            <span className="text-slate-500 font-bold text-lg hidden sm:inline">+</span>
            <span className="px-4 py-2 rounded-xl bg-cyan-500/20 border border-cyan-400/30 text-cyan-300 font-bold text-sm backdrop-blur-sm">
              Wearable Data
            </span>
            <span className="text-slate-500 font-bold text-lg hidden sm:inline">+</span>
            <span className="px-4 py-2 rounded-xl bg-violet-500/20 border border-violet-400/30 text-violet-300 font-bold text-sm backdrop-blur-sm">
              Gut Microbiome
            </span>
          </div>

          <p className="relative text-xl sm:text-2xl font-black text-white italic max-w-xl mx-auto mb-8 leading-snug">
            "What if we could see health from multiple perspectives?"
          </p>

          {/* Arrow down */}
          <div className="relative flex justify-center mb-5">
            <div className="w-px h-8 bg-gradient-to-b from-slate-500 to-sky-400" />
          </div>

          <p className="relative text-xs uppercase tracking-[0.2em] font-bold text-slate-400 mb-3">This led to</p>

          <h2 className="relative text-4xl sm:text-5xl font-black tracking-tight leading-none">
            <span className="prism-gradient-text text-5xl sm:text-6xl">!</span>{' '}
            <span className="bg-gradient-to-r from-sky-400 via-cyan-400 to-sky-300 bg-clip-text text-transparent">
              Health Prism
            </span>
          </h2>
        </div>
      </section>

      {/* ───── SECTION C — OUR SOLUTION ───── */}
      <section className="guided-section guided-fade-in-up guided-stagger-3">
        <div className="flex items-center space-x-3 mb-5">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/25">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">Our Solution</h2>
        </div>

        <p className="text-slate-600 leading-relaxed max-w-3xl mb-6 text-base">
          <strong className="text-slate-800">!Health Prism</strong> is a multimodal preventive-health decision-support platform that integrates:
        </p>

        {/* Modality cards — rich gradient borders */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          {MODALITIES.map((mod, i) => (
            <div
              key={i}
              className={`p-5 rounded-2xl bg-gradient-to-br ${mod.bg} ring-2 ${mod.ring} text-center space-y-2 hover:scale-[1.02] transition-transform guided-fade-in-up guided-stagger-${i + 1}`}
            >
              <span className="text-4xl block">{mod.emoji}</span>
              <h4 className="font-black text-base text-slate-800">{mod.title}</h4>
              <p className="text-xs text-slate-500 font-medium">{mod.subtitle}</p>
            </div>
          ))}
        </div>

        {/* Data-flow diagram — dark version */}
        <div className="relative p-6 sm:p-8 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-700 mb-8 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-sky-500/5 via-transparent to-violet-500/5 pointer-events-none" />

          <div className="relative flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">

            {/* Source nodes */}
            <div className="flex flex-col gap-2 text-center sm:text-right">
              <span className="text-sm font-bold text-sky-300 bg-sky-500/15 border border-sky-500/30 px-3 py-1.5 rounded-lg">🏥 Clinical</span>
              <span className="text-sm font-bold text-cyan-300 bg-cyan-500/15 border border-cyan-500/30 px-3 py-1.5 rounded-lg">⌚ Wearable</span>
              <span className="text-sm font-bold text-violet-300 bg-violet-500/15 border border-violet-500/30 px-3 py-1.5 rounded-lg">🦠 Gut Microbiome</span>
            </div>

            {/* Arrow */}
            <div className="text-slate-500 text-lg font-bold">──▶</div>

            {/* Center: !Health Prism */}
            <div className="relative px-6 py-4 rounded-2xl bg-gradient-to-br from-sky-600 via-sky-500 to-cyan-600 text-white text-center shadow-xl shadow-sky-600/30">
              <div className="absolute inset-0 rounded-2xl guided-shimmer pointer-events-none" />
              <p className="text-xs uppercase tracking-[0.15em] font-black opacity-80 mb-1">Platform</p>
              <p className="text-xl font-black tracking-tight">
                <span className="text-cyan-200">!</span> Health Prism
              </p>
            </div>

            {/* Arrow */}
            <div className="text-slate-500 text-lg font-bold">──▶</div>

            {/* Output */}
            <div className="px-5 py-3.5 rounded-2xl bg-gradient-to-br from-emerald-500/15 to-teal-500/15 border border-emerald-400/30 text-center">
              <p className="text-xs uppercase tracking-wider font-black text-emerald-400 mb-0.5">Output</p>
              <p className="text-sm font-bold text-emerald-300">Metabolic Health<br />Assessment</p>
            </div>
          </div>
        </div>

        {/* Outcomes */}
        <p className="text-slate-500 text-sm font-semibold mb-4">…and uses these complementary sources to provide:</p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {OUTCOMES.map((item, i) => {
            const Icon = item.icon;
            return (
              <div
                key={i}
                className={`telemed-card p-4 flex items-center space-x-3 hover:scale-[1.01] transition-transform guided-fade-in-up guided-stagger-${i + 1}`}
              >
                <div className={`w-9 h-9 rounded-lg bg-gradient-to-br ${item.gradient} flex items-center justify-center flex-shrink-0 shadow-md`}>
                  <Icon className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-bold text-slate-800 leading-snug">{item.title}</span>
              </div>
            );
          })}
        </div>
      </section>

      {/* ───── SECTION D — WHY THE "!" ───── */}
      <section className="guided-section guided-fade-in-up guided-stagger-4">
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/25">
            <Flame className="w-5 h-5 text-white" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            Why the "<span className="prism-gradient-text">!</span>" in !Health Prism?
          </h2>
        </div>

        {/* Traditional vs !Prism — side by side */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-8">
          {/* Traditional Prism */}
          <div className="p-6 rounded-2xl bg-gradient-to-b from-slate-50 to-gray-100 border border-slate-200 space-y-4 text-center">
            <p className="text-xs font-black uppercase tracking-[0.15em] text-slate-400">Traditional Prism</p>
            <p className="text-sm text-slate-500 font-medium">One source → separated into many</p>

            <div className="flex flex-col items-center gap-3 py-3">
              <div className="w-32 h-2.5 rounded-full bg-slate-300" />
              <span className="text-xs font-black text-slate-400 uppercase tracking-wider">▼ Prism ▼</span>
              <div className="w-48 h-3 prism-spectrum" />
              <p className="text-xs text-slate-400 font-bold mt-1">ONE → MANY</p>
            </div>
          </div>

          {/* !Health Prism — bold dark style */}
          <div className="p-6 rounded-2xl bg-gradient-to-b from-slate-900 to-sky-900 border border-sky-500/30 space-y-4 text-center overflow-hidden relative">
            <div className="absolute -top-8 -right-8 w-24 h-24 bg-sky-500/10 rounded-full blur-2xl pointer-events-none" />
            <p className="relative text-xs font-black uppercase tracking-[0.15em] text-sky-400">!Health Prism</p>
            <p className="relative text-sm text-slate-300 font-medium">Multiple sources → unified assessment</p>

            <div className="relative flex flex-col items-center gap-3 py-3">
              <div className="flex gap-2">
                <span className="w-16 h-2.5 rounded-full bg-gradient-to-r from-sky-400 to-sky-500" />
                <span className="w-16 h-2.5 rounded-full bg-gradient-to-r from-cyan-400 to-cyan-500" />
                <span className="w-16 h-2.5 rounded-full bg-gradient-to-r from-violet-400 to-violet-500" />
              </div>
              <span className="text-xs font-black text-sky-400 uppercase tracking-wider">▼ !Prism ▼</span>
              <div className="w-32 h-3 rounded-full bg-gradient-to-r from-sky-500 via-cyan-400 to-sky-500 shadow-lg shadow-sky-500/30" />
              <p className="text-xs text-sky-300 font-black mt-1">MANY → ONE</p>
            </div>
          </div>
        </div>

        {/* The ! explanation — with gradient accent */}
        <div className="p-6 sm:p-8 rounded-2xl bg-gradient-to-r from-slate-50 via-white to-violet-50/30 border border-slate-200 space-y-3 mb-8">
          <div className="flex items-start space-x-5">
            <span className="prism-gradient-text text-6xl sm:text-7xl font-black leading-none select-none">!</span>
            <div className="space-y-2 pt-2">
              <p className="text-slate-700 leading-relaxed font-medium">
                In programming, <code className="px-2 py-0.5 bg-slate-100 rounded-md text-sm font-mono font-black text-violet-700">!</code> represents
                logical <strong className="text-slate-900">NOT</strong> — a <strong className="text-slate-900">negation</strong>.
              </p>
              <p className="text-slate-600 leading-relaxed text-sm">
                A <strong>Prism</strong> traditionally separates one source into many outputs.<br />
                An <strong className="text-sky-700">!Prism</strong> represents the conceptual opposite: bringing
                multiple health-data perspectives together toward <strong className="text-slate-800">one integrated assessment</strong>.
              </p>
            </div>
          </div>
        </div>

        {/* Grand reveal — dark premium card */}
        <div className="text-center py-10 px-6 rounded-3xl bg-gradient-to-b from-slate-900 via-slate-800 to-sky-900 overflow-hidden relative space-y-5">
          <div className="absolute -top-16 left-1/2 -translate-x-1/2 w-64 h-32 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-16 left-1/2 -translate-x-1/2 w-64 h-32 bg-violet-500/10 rounded-full blur-3xl pointer-events-none" />

          <p className="relative text-xs uppercase tracking-[0.25em] font-black text-slate-400">This is why our platform is called</p>

          <h2 className="relative text-6xl sm:text-7xl lg:text-8xl font-black tracking-tight leading-none">
            <span className="prism-gradient-text">!</span>{' '}
            <span className="bg-gradient-to-r from-sky-400 via-cyan-300 to-sky-400 bg-clip-text text-transparent">
              Health Prism
            </span>
          </h2>

          <div className="relative w-48 h-2 prism-spectrum mx-auto rounded-full" />

          <p className="relative text-xl sm:text-2xl font-black text-slate-300 italic tracking-tight">
            "Not Just One View of Health."
          </p>
        </div>
      </section>

      {/* ───── SECTION E — CONTINUE TO REAL ANALYZE ───── */}
      <section className="guided-section guided-fade-in-up guided-stagger-5">
        <div className="flex flex-col items-center space-y-4">

          <button
            type="button"
            onClick={() => {
              window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
              onContinue?.();
            }}
            className="group flex items-center space-x-3 px-10 py-4.5 bg-gradient-to-r from-orange-500 via-amber-500 to-emerald-500 hover:from-orange-600 hover:to-emerald-600 text-white font-extrabold text-base sm:text-lg rounded-2xl shadow-xl shadow-orange-500/25 transform hover:scale-[1.03] active:scale-[0.98] transition-all cursor-pointer"
          >
            <span>Continue to Guided Analysis</span>
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1.5 transition-transform" />
          </button>

          {/* Progress indicator */}
          <span className="text-xs font-semibold text-slate-500 tracking-wide">
            Guided Demo&nbsp;&nbsp;—&nbsp;&nbsp;Step 01 Complete • Next: Multimodal Analysis
          </span>
        </div>
      </section>

    </div>
  );
};
