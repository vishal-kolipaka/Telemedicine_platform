import React from 'react';
import { Activity, ShieldCheck, Target, HeartHandshake, Award } from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-12 py-8">
      
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-100 text-sky-800 text-xs font-bold">
          <Activity className="w-3.5 h-3.5 text-sky-600" />
          <span>About TeleMed Platform</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          Empowering Healthcare with Intelligent Document Intelligence
        </h2>
        <p className="text-slate-600 text-base max-w-2xl mx-auto leading-relaxed">
          TeleMed is built to assist medical practitioners, clinicians, and researchers by turning unstructured health reports into standardized, model-ready clinical data.
        </p>
      </div>

      {/* Vision Card */}
      <div className="telemed-card p-8 md:p-10 space-y-6 bg-gradient-to-br from-white via-sky-50/30 to-white">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-sky-600 text-white flex items-center justify-center font-bold shadow-md shadow-sky-600/20">
            <Target className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-slate-900">Our Mission</h3>
        </div>

        <p className="text-slate-700 text-sm leading-relaxed">
          Healthcare data exists in disparate formats — laboratory PDFs, clinical notes, scanned reports, and device logs. TeleMed bridges these data sources into a unified, high-integrity decision support platform.
        </p>

        <p className="text-slate-700 text-sm leading-relaxed">
          By combining advanced document reading with automated quality verification, TeleMed ensures that patient information is accurately parsed and prepared for clinical decision support.
        </p>
      </div>

      {/* Core Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        <div className="telemed-card p-6 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center">
            <Award className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-slate-900 text-base">Clinical Accuracy</h4>
          <p className="text-xs text-slate-500 leading-relaxed">
            Every document undergoes strict character plausibility, non-empty, and date confidence validation to ensure data integrity.
          </p>
        </div>

        <div className="telemed-card p-6 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-slate-900 text-base">Privacy & Trust</h4>
          <p className="text-xs text-slate-500 leading-relaxed">
            Built around strict stateless processing and security best practices to protect sensitive patient information.
          </p>
        </div>

        <div className="telemed-card p-6 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-100 text-cyan-700 flex items-center justify-center">
            <HeartHandshake className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-slate-900 text-base">Clinician-Centric</h4>
          <p className="text-xs text-slate-500 leading-relaxed">
            Designed for simplicity and speed, giving medical professionals clear, structured insights at a glance.
          </p>
        </div>

      </div>

    </div>
  );
};
