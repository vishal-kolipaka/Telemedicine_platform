import React from 'react';
import { Sparkles, ArrowRight, ShieldCheck, Zap, Database, Brain, CheckCircle2, Stethoscope, FileSearch, Compass, Layers, Eye } from 'lucide-react';

interface Props {
  onStartAnalysis: () => void;
  onStartGuidedDemo: () => void;
}

export const DashboardPage: React.FC<Props> = ({ onStartAnalysis, onStartGuidedDemo }) => {
  return (
    <div className="space-y-16 py-8">

      {/* ───── Guided Demo Entry Card — FIRST, so judges see it immediately ───── */}
      <section className="guided-fade-in-up">
        <div className="guided-demo-card relative overflow-hidden p-6 sm:p-8">

          {/* Ambient glow orbs */}
          <div className="absolute -top-16 -right-16 w-56 h-56 bg-orange-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-16 -left-16 w-56 h-56 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">

            {/* Left: Info */}
            <div className="flex items-start space-x-4 max-w-2xl">
              <div className="flex-shrink-0 w-12 h-12 rounded-2xl bg-gradient-to-br from-orange-500 to-amber-500 text-white flex items-center justify-center shadow-lg shadow-orange-500/30">
                <Compass className="w-6 h-6" />
              </div>
              <div className="space-y-2">
                <div className="flex items-center space-x-3">
                  <h3 className="text-xl font-extrabold text-white">🎯 Guided Demo</h3>
                  <span className="px-2.5 py-0.5 text-[10px] font-black uppercase tracking-wider bg-orange-500 text-white rounded-full animate-pulse">
                    New
                  </span>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed">
                  Follow the recommended workflow to understand <strong className="text-white">!Health Prism</strong>. 
                  Explore how we integrate <strong className="text-sky-400">Clinical</strong>, <strong className="text-cyan-400">Wearable</strong>, 
                  and <strong className="text-violet-400">Gut Microbiome</strong> data to provide explainable metabolic health insights.
                </p>
                <div className="flex items-center space-x-4 text-xs text-slate-400 pt-0.5">
                  <span className="flex items-center space-x-1"><Layers className="w-3.5 h-3.5" /><span>Multimodal Data</span></span>
                  <span className="flex items-center space-x-1"><Eye className="w-3.5 h-3.5" /><span>Explainable AI</span></span>
                  <span className="flex items-center space-x-1"><Compass className="w-3.5 h-3.5" /><span>Step-by-Step</span></span>
                </div>
              </div>
            </div>

            {/* Right: Blinking CTA */}
            <button
              onClick={onStartGuidedDemo}
              className="guided-blink-btn group flex-shrink-0 flex items-center space-x-3 px-8 py-4 bg-gradient-to-r from-orange-500 via-orange-600 to-amber-600 hover:from-orange-600 hover:to-amber-700 text-white font-extrabold text-sm rounded-2xl transition-all transform hover:scale-[1.03] active:scale-[0.97]"
            >
              <span>Start Guided Demo</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>

          </div>
        </div>
      </section>
      
      {/* Large Hero Section */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-sky-50/80 via-white to-sky-50/30 border border-sky-100 p-8 md:p-16 shadow-xl shadow-sky-500/5">
        
        {/* Background Ambient Glowing Orbs */}
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-sky-200/50 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-cyan-200/40 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Left Text Column */}
          <div className="lg:col-span-7 space-y-6 text-left">
            
            {/* Platform Badge */}
            <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-sky-100/90 text-sky-800 text-xs font-bold border border-sky-200 shadow-2xs">
              <Sparkles className="w-4 h-4 text-sky-600" />
              <span>Next-Gen Telemedicine Support</span>
            </div>

            {/* Title */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight leading-[1.15]">
              AI-Powered Healthcare <br className="hidden sm:inline" />
              <span className="bg-gradient-to-r from-sky-600 via-sky-500 to-cyan-500 bg-clip-text text-transparent">
                Analysis Platform
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-lg sm:text-xl text-slate-600 max-w-2xl font-normal leading-relaxed">
              Upload medical reports and receive structured analysis through our intelligent processing platform.
            </p>

            {/* CTA Button */}
            <div className="pt-4 flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
              <button
                onClick={onStartAnalysis}
                className="group flex items-center justify-center space-x-3 px-8 py-4 bg-gradient-to-r from-sky-600 via-sky-500 to-cyan-600 hover:from-sky-700 hover:to-cyan-700 text-white font-bold text-lg rounded-2xl shadow-xl shadow-sky-600/25 transition-all transform hover:scale-[1.02] active:scale-[0.98]"
              >
                <span>Start Analysis</span>
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>

              <div className="flex items-center space-x-2 text-xs text-slate-500 px-3 py-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span>Instant multi-format document processing</span>
              </div>
            </div>

          </div>

          {/* Right Healthcare AI Graphic Card */}
          <div className="lg:col-span-5 relative">
            <div className="telemed-card p-6 md:p-8 bg-white/90 backdrop-blur-md border-sky-100 shadow-2xl space-y-6">
              
              {/* Graphic Header */}
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-sky-600 text-white flex items-center justify-center font-bold shadow-md shadow-sky-600/20">
                    <Brain className="w-6 h-6 animate-pulse" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 text-sm">TeleMed Engine</h4>
                    <span className="text-xs text-emerald-600 font-semibold flex items-center space-x-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping inline-block" />
                      <span>Processing Active</span>
                    </span>
                  </div>
                </div>
                <span className="text-xs font-mono font-semibold bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md">
                  Phase 1 Ready
                </span>
              </div>

              {/* Graphic Metrics Simulation */}
              <div className="space-y-3">
                
                <div className="p-3 bg-sky-50/70 border border-sky-100 rounded-xl flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2 text-sky-900 font-medium">
                    <FileSearch className="w-4 h-4 text-sky-600" />
                    <span>Multi-Format Ingestion</span>
                  </div>
                  <span className="font-bold text-sky-700">PDF • TXT • CSV • Images</span>
                </div>

                <div className="p-3 bg-emerald-50/70 border border-emerald-100 rounded-xl flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2 text-emerald-900 font-medium">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>Quality Verification</span>
                  </div>
                  <span className="font-bold text-emerald-700">100% Validated</span>
                </div>

                <div className="p-3 bg-cyan-50/70 border border-cyan-100 rounded-xl flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2 text-cyan-900 font-medium">
                    <Stethoscope className="w-4 h-4 text-cyan-600" />
                    <span>Clinical Standardization</span>
                  </div>
                  <span className="font-bold text-cyan-700">Structured Output</span>
                </div>

              </div>

            </div>
          </div>

        </div>
      </section>

      {/* Feature Highlights Grid */}
      <section className="space-y-8 text-center">
        <div className="space-y-2">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
            Engineered for Modern Telemedicine
          </h2>
          <p className="text-slate-500 text-sm max-w-xl mx-auto">
            Combining state-of-the-art document processing with seamless medical data organization.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          <div className="telemed-card p-6 text-left space-y-3 border-t-4 border-t-sky-500">
            <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center font-bold">
              <Database className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-base">Heterogeneous File Parsing</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Handles lab test PDFs, scanned reports, CSV datasets, and plain text notes without manual rekeying.
            </p>
          </div>

          <div className="telemed-card p-6 text-left space-y-3 border-t-4 border-t-cyan-500">
            <div className="w-10 h-10 rounded-xl bg-cyan-100 text-cyan-700 flex items-center justify-center font-bold">
              <Zap className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-base">Automated Validation</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Verifies extraction quality, alphanumeric consistency, and report date detection with confidence tags.
            </p>
          </div>

          <div className="telemed-card p-6 text-left space-y-3 border-t-4 border-t-emerald-500">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-base">Trusted Clinical Foundation</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Designed to serve as the reliable data foundation for AI clinical decision support systems.
            </p>
          </div>

        </div>
      </section>

    </div>
  );
};


