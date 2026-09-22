import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle2, FileSearch, Cpu, Sparkles, Database } from 'lucide-react';
import { DeploymentWaitNotice } from './DeploymentWaitNotice';

export const ProcessingLoader: React.FC = () => {
  const steps = [
    { label: 'Reading document...', icon: FileSearch },
    { label: 'Extracting content...', icon: Cpu },
    { label: 'Analyzing structure...', icon: Database },
    { label: 'Preparing results...', icon: Sparkles },
  ];

  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStepIndex((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
    }, 700);

    return () => clearInterval(timer);
  }, [steps.length]);

  return (
    <div className="telemed-card p-12 max-w-xl mx-auto text-center space-y-8 animate-fade-in my-8">
      
      {/* Pulse Rings Graphic */}
      <div className="relative w-24 h-24 mx-auto flex items-center justify-center">
        <div className="absolute inset-0 rounded-full bg-sky-400/20 animate-ping" />
        <div className="absolute inset-2 rounded-full bg-sky-500/30 animate-pulse" />
        <div className="relative w-16 h-16 rounded-full bg-gradient-to-tr from-sky-600 to-cyan-500 flex items-center justify-center text-white shadow-lg shadow-sky-500/30">
          <Loader2 className="w-8 h-8 animate-spin" />
        </div>
      </div>

      {/* Progress Heading */}
      <div className="space-y-2">
        <h3 className="text-xl font-bold text-slate-900">Processing Medical Document</h3>
        <p className="text-sm text-slate-500">
          Our intelligent platform is parsing and structuring your file content.
        </p>
      </div>

      {/* Steps List */}
      <div className="space-y-3 max-w-sm mx-auto text-left border border-slate-200/80 bg-slate-50/50 p-4 rounded-xl">
        {steps.map((step, idx) => {
          const StepIcon = step.icon;
          const isDone = idx < currentStepIndex;
          const isCurrent = idx === currentStepIndex;

          return (
            <div
              key={step.label}
              className={`flex items-center space-x-3 text-sm p-2 rounded-lg transition-all duration-300 ${
                isCurrent
                  ? 'bg-white shadow-xs text-sky-700 font-semibold'
                  : isDone
                  ? 'text-slate-600 font-medium'
                  : 'text-slate-400'
              }`}
            >
              {isDone ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
              ) : isCurrent ? (
                <Loader2 className="w-5 h-5 text-sky-600 animate-spin shrink-0" />
              ) : (
                <StepIcon className="w-5 h-5 text-slate-300 shrink-0" />
              )}
              <span>{step.label}</span>
            </div>
          );
        })}
      </div>

      {/* Deployment / Cold-Start Informational Notice */}
      <DeploymentWaitNotice
        title="First analysis may take a little longer"
        message="Because !Health Prism is running on a free-tier deployment, the backend service may need a moment to wake up before processing begins. Please wait while we complete the analysis."
        subtext="Thank you for your patience."
      />

      <div className="text-xs text-slate-400 font-medium">
        Please wait while we complete the structural analysis...
      </div>

    </div>
  );
};
