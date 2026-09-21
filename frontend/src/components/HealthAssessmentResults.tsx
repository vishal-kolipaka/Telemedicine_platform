import React, { useState, useEffect } from 'react';
import {
  Activity,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  RefreshCw,
  Printer,
  ShieldCheck,
  Info,
  Calendar,
  User,
  ArrowUp,
  ArrowDown,
  ArrowUpDown,
} from 'lucide-react';
import type { HealthAssessmentResponse, AssessmentDiseaseResult } from '../types/reader';
import { XaiExplanationSection } from './XaiExplanationSection';
import { formatRiskPercentage } from '../utils/formatters';
import type { Stage4SubStep } from '../pages/AnalyzePage';
import { GuidedCalloutCard } from './guided-demo/GuidedCalloutCard';

interface Props {
  assessment: HealthAssessmentResponse;
  onReset: () => void;
  onViewHealthPlan?: () => void;
  isGuidedDemo?: boolean;
  guidedSubStep?: Stage4SubStep;
  onNextGuidedStep?: (target?: Stage4SubStep) => void;
}

export const HealthAssessmentResults: React.FC<Props> = ({
  assessment,
  onReset,
  onViewHealthPlan,
  isGuidedDemo = false,
  guidedSubStep,
  onNextGuidedStep,
}) => {
  // Always scroll to top when the results page mounts
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }, []);
  const {
    patient_id,
    patient_name,
    patient_age,
    patient_gender,
    assessment_timestamp,
    has_any_usable_data,
    summary_message,
    diseases,
    xai,
  } = assessment;

  // Dynamically sort disease cards: unsuppressed by risk score descending, then suppressed conditions
  const sortedDiseases = [...diseases].sort((a, b) => {
    if (a.is_suppressed && !b.is_suppressed) return 1;
    if (!a.is_suppressed && b.is_suppressed) return -1;
    const scoreA = a.risk_percentage !== null ? a.risk_percentage : -1;
    const scoreB = b.risk_percentage !== null ? b.risk_percentage : -1;
    return scoreB - scoreA;
  });

  // State to track which disease is actively focused in the XAI section
  const [activeXaiDiseaseKey, setActiveXaiDiseaseKey] = useState<string>(() => {
    if (xai?.default_disease) {
      return xai.default_disease;
    }
    const highestNonSuppressed = sortedDiseases.find(
      (d) => d.risk_percentage !== null && !d.is_suppressed && d.status_label !== 'Not Enough Information'
    );
    return highestNonSuppressed?.key || sortedDiseases[0]?.key || 'Type2_Diabetes';
  });

  const handleWhyThisResult = (diseaseKey: string) => {
    setActiveXaiDiseaseKey(diseaseKey);
    const element = document.getElementById('xai-explanation-section');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    if (isGuidedDemo && guidedSubStep === 'why_result') {
      onNextGuidedStep?.('disease_tabs');
    }
  };

  const formattedDate = new Date(assessment_timestamp).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  const getStatusBadge = (disease: AssessmentDiseaseResult) => {
    // Priority 1: Suppressed state takes precedence over all other badges
    if (disease.is_suppressed) {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[11px] font-bold border border-slate-300 shrink-0">
          <ShieldCheck className="w-3 h-3 text-slate-500" />
          <span>Superseded</span>
        </span>
      );
    }

    // Priority 2: Standard status mapping
    switch (disease.status_label) {
      case 'Assessment Available':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 text-[11px] font-bold border border-emerald-200 shrink-0">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            <span>Assessment Available</span>
          </span>
        );
      case 'Limited Data Assessment':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-900 text-[11px] font-bold border border-amber-300 shrink-0">
            <AlertTriangle className="w-3 h-3 text-amber-700" />
            <span>Limited Data</span>
          </span>
        );
      case 'Not Enough Information':
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[11px] font-bold border border-slate-300 shrink-0">
            <HelpCircle className="w-3 h-3 text-slate-500" />
            <span>Not Enough Info</span>
          </span>
        );
    }
  };

  const getDecisionBadge = (disease: AssessmentDiseaseResult) => {
    // Priority 1: Suppressed state
    if (disease.is_suppressed) {
      return (
        <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-lg bg-slate-100 text-slate-700 text-[11px] font-bold border border-slate-200">
          <span>Superseded by Type 2 Diabetes</span>
        </span>
      );
    }

    // Priority 2: Genuinely missing or unavailable score
    if (disease.status_label === 'Not Enough Information' || disease.decision === null || disease.risk_percentage === null) {
      return (
        <span className="px-2.5 py-0.5 rounded-lg bg-slate-100 text-slate-600 text-[11px] font-semibold">
          No Score Available
        </span>
      );
    }

    // Priority 3: Positive prediction
    if (disease.decision === true) {
      return (
        <span className="inline-flex items-center space-x-1.5 px-3 py-0.5 rounded-full bg-rose-50 text-rose-800 border border-rose-200 text-[11px] font-bold">
          <span className="w-2 h-2 rounded-full bg-rose-600 inline-block" />
          <span>Elevated Risk</span>
        </span>
      );
    }

    // Priority 4: Negative prediction (amber if moderate 20-49%, emerald if low <20%)
    if (disease.risk_percentage !== null && disease.risk_percentage >= 20) {
      return (
        <span className="inline-flex items-center space-x-1.5 px-3 py-0.5 rounded-full bg-amber-50 text-amber-900 border border-amber-300 text-[11px] font-bold">
          <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />
          <span>Moderate Risk</span>
        </span>
      );
    }

    return (
      <span className="inline-flex items-center space-x-1.5 px-3 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px] font-bold">
        <span className="w-2 h-2 rounded-full bg-emerald-600 inline-block" />
        <span>Low Risk</span>
      </span>
    );
  };

  const getPriorityInfo = (index: number) => {
    switch (index) {
      case 0:
        return {
          label: 'Priority: Highest',
          icon: <ArrowUp className="w-3.5 h-3.5 text-rose-600" />,
          colorClass: 'text-rose-800 bg-rose-50/60 border-rose-100',
          accentBorder: 'border-t-4 border-t-rose-500',
          progressBarColor: 'bg-rose-500',
        };
      case 1:
        return {
          label: 'Priority: High',
          icon: <ArrowUp className="w-3.5 h-3.5 text-amber-600" />,
          colorClass: 'text-amber-800 bg-amber-50/60 border-amber-100',
          accentBorder: 'border-t-4 border-t-amber-500',
          progressBarColor: 'bg-amber-500',
        };
      case 2:
        return {
          label: 'Priority: Moderate',
          icon: <Info className="w-3.5 h-3.5 text-amber-600" />,
          colorClass: 'text-amber-800 bg-amber-50/40 border-amber-100',
          accentBorder: 'border-t-4 border-t-amber-400',
          progressBarColor: 'bg-amber-400',
        };
      case 3:
        return {
          label: 'Priority: Low',
          icon: <ArrowDown className="w-3.5 h-3.5 text-emerald-600" />,
          colorClass: 'text-emerald-800 bg-emerald-50/60 border-emerald-100',
          accentBorder: 'border-t-4 border-t-emerald-500',
          progressBarColor: 'bg-emerald-500',
        };
      case 4:
      default:
        return {
          label: 'Priority: Lowest',
          icon: <ArrowDown className="w-3.5 h-3.5 text-emerald-600" />,
          colorClass: 'text-emerald-800 bg-emerald-50/40 border-emerald-100',
          accentBorder: 'border-t-4 border-t-emerald-400',
          progressBarColor: 'bg-emerald-400',
        };
    }
  };

  return (
    <div className="space-y-8 animate-fade-in w-full py-2">
      {/* Header Card */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xl shadow-sky-500/5 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-6">
          <div className="space-y-2">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-100 text-sky-800 text-xs font-bold">
              <Sparkles className="w-3.5 h-3.5 text-sky-600" />
              <span>Personalized Assessment Report</span>
            </div>
            <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
              Metabolic Health Assessment
            </h2>
            <p className="text-xs text-slate-500 flex flex-wrap items-center gap-3">
              <span className="flex items-center space-x-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>{formattedDate}</span>
              </span>
              <span>•</span>
              <span className="flex items-center space-x-1">
                <User className="w-3.5 h-3.5 text-slate-400" />
                <span>Patient ID: <strong className="font-mono text-slate-700">{patient_id}</strong></span>
              </span>
              {patient_name && (
                <>
                  <span>•</span>
                  <span>Name: <strong className="text-slate-800">{patient_name}</strong></span>
                </>
              )}
              {patient_age && (
                <>
                  <span>•</span>
                  <span>Age: <strong className="text-slate-800">{patient_age} yrs</strong></span>
                </>
              )}
              {patient_gender && (
                <>
                  <span>•</span>
                  <span>Gender: <strong className="text-slate-800">{patient_gender}</strong></span>
                </>
              )}
            </p>
          </div>

          {/* Top Actions */}
          <div className="flex items-center space-x-3 shrink-0 relative">
            {assessment.health_plan && onViewHealthPlan && (
              <div className="relative">
                {isGuidedDemo && guidedSubStep === 'plan_button' && (
                  <div className="absolute right-0 top-full mt-3 z-30 w-80 sm:w-96">
                    <GuidedCalloutCard
                      badge="🎯 GUIDED DEMO • PERSONALIZED GUIDANCE"
                      title="Next: Personalized Health Plan"
                      description="After reviewing the metabolic health assessment and supporting evidence, click Personalized Plan to see how the platform turns these findings into personalized preventive guidance."
                      actionInstruction="👉 Click 'Personalized Plan' to continue."
                      pointerDirection="up"
                    />
                  </div>
                )}
                <button
                  id="guided-personalized-plan-btn"
                  type="button"
                  onClick={onViewHealthPlan}
                  className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-bold rounded-2xl transition-all cursor-pointer ${
                    isGuidedDemo && guidedSubStep === 'plan_button'
                      ? 'bg-gradient-to-r from-orange-500 via-amber-500 to-sky-600 hover:from-orange-600 hover:to-sky-700 text-white border-2 border-amber-300 ring-4 ring-orange-400/80 guided-blink-glow-orange scale-110 shadow-2xl shadow-orange-500/40 font-black'
                      : 'bg-gradient-to-r from-sky-600 via-sky-500 to-cyan-600 hover:from-sky-700 hover:to-cyan-700 text-white shadow-md shadow-sky-600/20'
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5 text-sky-200" />
                  <span>✨ Personalized Plan</span>
                </button>
              </div>
            )}
            <button
              type="button"
              onClick={() => window.print()}
              className="flex items-center space-x-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-2xl transition-colors cursor-pointer"
            >
              <Printer className="w-4 h-4" />
              <span>Print</span>
            </button>
            <button
              type="button"
              onClick={onReset}
              className="flex items-center space-x-2 px-5 py-2.5 bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold rounded-2xl shadow-lg shadow-sky-600/25 transition-all cursor-pointer"
            >
              <RefreshCw className="w-4 h-4" />
              <span>New Analysis</span>
            </button>
          </div>
        </div>

        {/* Summary Banner */}
        <div
          className={`p-4 rounded-2xl border flex items-start space-x-3 text-xs leading-relaxed ${
            has_any_usable_data
              ? 'bg-sky-50/70 border-sky-200 text-sky-950'
              : 'bg-amber-50 border-amber-200 text-amber-950'
          }`}
        >
          <Info className="w-4 h-4 text-sky-600 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-bold block text-sm">Assessment Overview</span>
            <p className="text-slate-600">{summary_message}</p>
          </div>
        </div>
      </div>

      {/* Disease Cards Section */}
      <div className="space-y-4">
        {/* Header with Title and Sorting Indicator */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-1">
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-sky-600" />
            <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">
              Health Risk Indicators
            </h3>
          </div>
          <div className="flex items-center space-x-1.5 text-xs text-slate-500 font-medium">
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
            <span>Sorted by Risk Score (High → Low)</span>
          </div>
        </div>

        {/* Guided Demo Step 4A Callout: Disease Prediction Card */}
        {isGuidedDemo && guidedSubStep === 'prediction' && (
          <div className="pb-2">
            <GuidedCalloutCard
              badge="🎯 GUIDED DEMO • METABOLIC RISK"
              title={`Primary Assessment: ${sortedDiseases[0]?.display_name || 'Metabolic Condition'}`}
              description={
                <span>
                  This card shows the metabolic disease risk predicted by <strong>!Health Prism</strong> from the available health evidence. Calculated risk for <strong>{sortedDiseases[0]?.display_name}</strong> is <strong className="text-amber-300">{formatRiskPercentage(sortedDiseases[0]?.risk_percentage)}</strong> ({sortedDiseases[0]?.decision ? 'Elevated Risk' : 'Moderate/Low Risk'}). The calculated risk represents the model's estimated risk for this condition based on the analyzed health features.
                </span>
              }
              nextLabel="Next: 'Why this result?'"
              onNext={() => onNextGuidedStep?.('why_result')}
              pointerDirection="down"
            />
          </div>
        )}

        {/* Dynamic 5 Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {sortedDiseases.map((disease, idx) => {
            const hasScore = disease.risk_percentage !== null;
            const priority = getPriorityInfo(idx);
            const isSelected = activeXaiDiseaseKey === disease.key;
            const isPrimaryTarget = idx === 0;

            return (
              <div
                key={disease.key}
                id={isPrimaryTarget ? 'guided-prediction-card' : undefined}
                className={`bg-white rounded-3xl p-5 border transition-all duration-200 flex flex-col justify-between space-y-4 shadow-sm hover:shadow-md ${
                  isSelected ? 'border-sky-500 ring-2 ring-sky-500/20' : 'border-slate-200'
                } ${priority.accentBorder} ${
                  isGuidedDemo && guidedSubStep === 'prediction' && isPrimaryTarget
                    ? 'ring-4 ring-orange-400 ring-offset-4 ring-offset-slate-50 border-2 border-orange-400 guided-blink-glow-card shadow-2xl shadow-orange-500/30'
                    : ''
                }`}
              >
                {/* Top Row: Disease Title & Modality/Data Status Badge */}
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-1.5 min-h-[44px]">
                    <h4 className="font-extrabold text-slate-900 text-sm leading-tight">
                      {disease.display_name}
                    </h4>
                    {getStatusBadge(disease)}
                  </div>

                  {/* Decision Tag */}
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] font-bold text-slate-600 uppercase tracking-wider">
                      Result
                    </span>
                    {getDecisionBadge(disease)}
                  </div>
                </div>

                {/* Center Risk Score / Superseded State */}
                <div className="bg-slate-50 rounded-2xl p-3 text-center space-y-1 border border-slate-100">
                  <span className="text-[11px] text-slate-500 font-medium block">
                    Calculated Risk
                  </span>
                  <div className="h-9 flex items-center justify-center">
                    {disease.is_suppressed ? (
                      <span className="text-xs font-bold text-slate-500">
                        — (Superseded)
                      </span>
                    ) : hasScore ? (
                      <span className="text-2xl font-black text-slate-900 tracking-tight">
                        {formatRiskPercentage(disease.risk_percentage)}
                      </span>
                    ) : (
                      <span className="text-xs font-bold text-slate-400">
                        Not Available
                      </span>
                    )}
                  </div>

                  {/* Progress Bar */}
                  {disease.is_suppressed ? (
                    <div className="w-full bg-slate-200/50 rounded-full h-1.5" />
                  ) : hasScore ? (
                    <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                      <div
                        className={`h-1.5 rounded-full transition-all duration-500 ${priority.progressBarColor}`}
                        style={{ width: `${Math.min(100, Math.max(4, disease.risk_percentage || 0))}%` }}
                      />
                    </div>
                  ) : (
                    <div className="w-full bg-slate-200/60 rounded-full h-1.5" />
                  )}
                </div>

                {/* Explanation / Clinical Note */}
                <p className="text-[11px] text-slate-500 leading-relaxed min-h-[32px]">
                  {disease.explanation}
                </p>

                {/* Guided Demo Step 4B Callout */}
                {isGuidedDemo && guidedSubStep === 'why_result' && isPrimaryTarget && (
                  <div className="pt-2">
                    <GuidedCalloutCard
                      badge="🎯 'Why this result?'"
                      title="Evidence Entry Point"
                      description="This option lets you inspect the multimodal evidence, laboratory biomarkers, sensor features, and explainable AI reasoning behind the prediction."
                      actionInstruction="👉 Click 'Why this result?' below to view the evidence."
                      pointerDirection="down"
                    />
                  </div>
                )}

                {/* Action: Why this result? */}
                <button
                  id={isPrimaryTarget ? 'guided-why-this-result-btn' : undefined}
                  type="button"
                  onClick={() => handleWhyThisResult(disease.key)}
                  className={`w-full flex items-center justify-center space-x-1.5 py-2 px-3 rounded-2xl text-xs font-bold transition-all cursor-pointer ${
                    isGuidedDemo && guidedSubStep === 'why_result' && isPrimaryTarget
                      ? 'bg-gradient-to-r from-orange-500 via-amber-500 to-sky-600 text-white font-black ring-4 ring-orange-400/80 guided-blink-glow-orange scale-105 shadow-xl shadow-orange-500/30'
                      : isSelected
                      ? 'bg-sky-600 text-white shadow-xs'
                      : 'bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-200'
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Why this result?</span>
                </button>

                {/* Bottom Priority Indicator */}
                <div
                  className={`pt-2.5 border-t border-slate-100 flex items-center justify-center space-x-1.5 text-xs font-bold ${priority.colorClass}`}
                >
                  {priority.icon}
                  <span>{priority.label}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Embedded Explainable AI (XAI) Section */}
      {xai && xai.has_usable_explanations && (
        <XaiExplanationSection
          xai={xai}
          activeDiseaseKey={activeXaiDiseaseKey}
          onSelectDisease={setActiveXaiDiseaseKey}
          isGuidedDemo={isGuidedDemo}
          guidedSubStep={guidedSubStep}
          onNextGuidedStep={onNextGuidedStep}
        />
      )}

      {/* Medical Advisory Banner */}
      <div className="p-4 rounded-2xl bg-sky-50/50 border border-sky-200 text-xs text-slate-600 flex items-start space-x-2.5 leading-relaxed">
        <ShieldCheck className="w-4 h-4 text-sky-600 shrink-0 mt-0.5" />
        <p>
          <strong className="text-slate-800">Medical Advisory:</strong> This assessment is AI-generated and for informational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Please consult a qualified healthcare provider for medical decisions.
        </p>
      </div>
    </div>
  );
};
