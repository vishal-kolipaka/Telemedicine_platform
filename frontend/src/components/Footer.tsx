import React from 'react';
import { Activity, ShieldCheck, Lock, Heart } from 'lucide-react';

interface FooterProps {
  setActiveTab: (tab: 'dashboard' | 'analyze' | 'about' | 'contact' | 'guided-demo') => void;
}

export const Footer: React.FC<FooterProps> = ({ setActiveTab }) => {
  return (
    <footer className="bg-slate-900 text-slate-300 border-t border-slate-800 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          
          {/* Brand Column */}
          <div className="space-y-4 md:col-span-2">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-lg bg-sky-600 flex items-center justify-center text-white">
                <Activity className="w-5 h-5" />
              </div>
              <div>
                <span className="text-xl font-black text-white tracking-tight block">!Health Prism</span>
                <span className="text-xs text-sky-400 font-semibold tracking-wide">Not Just One View of Health.</span>
              </div>
            </div>
            <p className="text-slate-400 text-sm max-w-md leading-relaxed">
              A multimodal metabolic health decision support platform bringing together Clinical, Wearable, and Gut Microbiome signals for explainable risk assessment and personalized care routines.
            </p>
            <div className="flex items-center space-x-4 text-xs text-slate-400 pt-2">
              <div className="flex items-center space-x-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Clinical Grade</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <Lock className="w-4 h-4 text-sky-400" />
                <span>Data Privacy Guard</span>
              </div>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Platform</h4>
            <ul className="space-y-2.5 text-sm">
              <li>
                <button onClick={() => setActiveTab('dashboard')} className="hover:text-sky-400 transition-colors">
                  Dashboard
                </button>
              </li>
              <li>
                <button onClick={() => setActiveTab('analyze')} className="hover:text-sky-400 transition-colors">
                  Analyze Medical Reports
                </button>
              </li>
              <li>
                <button onClick={() => setActiveTab('about')} className="hover:text-sky-400 transition-colors">
                  About !Health Prism
                </button>
              </li>
              <li>
                <button onClick={() => setActiveTab('contact')} className="hover:text-sky-400 transition-colors">
                  Contact Support
                </button>
              </li>
            </ul>
          </div>

          {/* Legal / Info */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Support & Trust</h4>
            <p className="text-slate-400 text-xs leading-relaxed mb-4">
              !Health Prism provides multimodal metabolic health decision support tools designed for explainable risk assessment and personalized clinical routines.
            </p>
            <span className="inline-block px-3 py-1 bg-slate-800 text-slate-300 text-xs rounded-full border border-slate-700">
              Phase 1 Release v1.0
            </span>
          </div>

        </div>

        <div className="pt-8 border-t border-slate-800 text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© {new Date().getFullYear()} !Health Prism. All rights reserved.</p>
          <div className="flex items-center space-x-1">
            <span>Engineered with care for clinical excellence</span>
            <Heart className="w-3.5 h-3.5 text-rose-500 fill-rose-500" />
          </div>
        </div>
      </div>
    </footer>
  );
};
