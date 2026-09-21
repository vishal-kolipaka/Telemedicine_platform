import React, { useEffect } from 'react';
import type { HealthAssessmentResponse } from '../types/reader';
import { GuidedCalloutCard } from './guided-demo/GuidedCalloutCard';
import type { Stage5SubStep } from '../pages/AnalyzePage';
import {
  Sparkles,
  ArrowLeft,
  Printer,
  RefreshCw,
  TrendingUp,
  Target,
  CheckCircle2,
  Activity,
  Apple,
  Scale,
  Clock,
  ShieldCheck,
  Info,
  Calendar,
  User,
  HeartPulse,
} from 'lucide-react';

interface Props {
  assessment: HealthAssessmentResponse;
  onBack: () => void;
  onReset: () => void;
  onCreateProgressPlan: (duration: '1_week' | '1_month' | '3_months') => void;
  isGuidedDemo?: boolean;
  guidedSubStep?: Stage5SubStep;
  onNextGuidedStep?: (target?: Stage5SubStep) => void;
}

// Known reference ranges for visual indicator calculations
const KNOWN_RANGES: Record<string, { min: number; max: number; unit: string; display: string }> = {
  Fasting_Blood_Glucose: { min: 70, max: 99, unit: 'mg/dL', display: '70–99 mg/dL' },
  HbA1c: { min: 4.0, max: 5.6, unit: '%', display: '< 5.7%' },
  BMI: { min: 18.5, max: 24.9, unit: 'kg/m²', display: '18.5–24.9 kg/m²' },
  Waist_Circumference: { min: 50, max: 94, unit: 'cm', display: '< 94 cm' },
  Systolic_BP: { min: 90, max: 120, unit: 'mmHg', display: '< 120 mmHg' },
  Diastolic_BP: { min: 60, max: 80, unit: 'mmHg', display: '< 80 mmHg' },
  Triglycerides: { min: 50, max: 149, unit: 'mg/dL', display: '< 150 mg/dL' },
  HDL: { min: 40, max: 80, unit: 'mg/dL', display: '> 40 mg/dL' },
  LDL: { min: 50, max: 99, unit: 'mg/dL', display: '< 100 mg/dL' },
  ALT: { min: 7, max: 56, unit: 'U/L', display: '7–56 U/L' },
  AST: { min: 10, max: 40, unit: 'U/L', display: '10–40 U/L' },
  Average_Daily_Steps: { min: 7500, max: 15000, unit: 'steps/day', display: '>= 7,500 steps/day' },
  Daily_Steps: { min: 7500, max: 15000, unit: 'steps/day', display: '>= 7,500 steps/day' },
  Sedentary_Time_Minutes: { min: 0, max: 480, unit: 'min/day', display: '< 480 min/day' },
  Sedentary_Minutes: { min: 0, max: 480, unit: 'min/day', display: '< 480 min/day' },
  Sleep_Duration_Hours: { min: 7.0, max: 9.0, unit: 'hours/night', display: '7–9 hours/night' },
  Sleep_Duration: { min: 7.0, max: 9.0, unit: 'hours/night', display: '7–9 hours/night' },
};

export const PersonalizedHealthPlanPage: React.FC<Props> = ({
  assessment,
  onBack,
  onReset,
  onCreateProgressPlan,
  isGuidedDemo = false,
  guidedSubStep,
  onNextGuidedStep,
}) => {
  // Always scroll to top when page opens
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }, []);

  const healthPlan = assessment.health_plan;
  const {
    patient_id,
    patient_name,
    patient_age,
    patient_gender,
    assessment_timestamp,
  } = assessment;

  const formattedDate = new Date(assessment_timestamp).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  // Pillar icon helper
  const getPillarIcon = (title: string) => {
    const t = title.toLowerCase();
    if (t.includes('physical') || t.includes('activity') || t.includes('movement') || t.includes('walk') || t.includes('move')) {
      return <Activity className="w-6 h-6 text-emerald-600" />;
    }
    if (t.includes('diet') || t.includes('fiber') || t.includes('nutrition') || t.includes('food')) {
      return <Apple className="w-6 h-6 text-sky-600" />;
    }
    if (t.includes('weight') || t.includes('caloric') || t.includes('bmi')) {
      return <Scale className="w-6 h-6 text-indigo-600" />;
    }
    if (t.includes('sedentary') || t.includes('sitting') || t.includes('sleep')) {
      return <Clock className="w-6 h-6 text-amber-600" />;
    }
    return <Target className="w-6 h-6 text-teal-600" />;
  };

  // If no plan is available
  if (!healthPlan || !healthPlan.sections) {
    return (
      <div className="space-y-6 max-w-5xl mx-auto py-6 animate-fade-in">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-white hover:bg-slate-100 text-slate-800 text-sm font-bold rounded-2xl border border-slate-200 shadow-xs transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Assessment</span>
        </button>

        <div className="bg-white rounded-3xl p-8 sm:p-12 border border-slate-200 shadow-xl space-y-4 text-center">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-sky-50 text-sky-700 flex items-center justify-center">
            <Info className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900">Personalized Plan Currently Unavailable</h2>
          <p className="text-sm text-slate-600 max-w-lg mx-auto leading-relaxed">
            {healthPlan?.message ||
              "We don't have enough verified guideline evidence to generate personalized lifestyle recommendations for this specific assessment. Please consult your physician for tailored advice."}
          </p>
          <div className="pt-4">
            <button
              type="button"
              onClick={onBack}
              className="px-6 py-3 bg-sky-600 text-white text-sm font-bold rounded-2xl hover:bg-sky-700 shadow-lg shadow-sky-600/20 cursor-pointer"
            >
              Return to Assessment Overview
            </button>
          </div>
        </div>
      </div>
    );
  }

  const {
    section_a_your_results,
    section_b_what_is_contributing,
    section_c_what_to_focus_on_first,
    section_d_personalized_recommendations,
    section_e_why_suggested,
  } = healthPlan.sections;

  return (
    <div className="space-y-8 max-w-6xl mx-auto py-4 animate-fade-in">
      {/* ── TOP NAVIGATION & HEADER BAR ────────────────────────────────────── */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xl shadow-sky-500/5 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-6">
          <button
            type="button"
            onClick={onBack}
            className="inline-flex items-center space-x-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold rounded-2xl transition-all cursor-pointer self-start sm:self-auto"
          >
            <ArrowLeft className="w-4 h-4 text-slate-600" />
            <span>Back to Assessment</span>
          </button>

          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={() => window.print()}
              className="flex items-center space-x-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold rounded-2xl transition-colors cursor-pointer"
            >
              <Printer className="w-4 h-4 text-slate-600" />
              <span>Print Plan</span>
            </button>
            <button
              type="button"
              onClick={onReset}
              className="flex items-center space-x-2 px-5 py-2.5 bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold rounded-2xl shadow-md shadow-sky-600/25 transition-all cursor-pointer"
            >
              <RefreshCw className="w-4 h-4" />
              <span>New Analysis</span>
            </button>
          </div>
        </div>

        {/* Hero Banner Header */}
        <div
          id="guided-plan-header"
          className={`space-y-3 relative transition-all duration-300 ${
            isGuidedDemo && guidedSubStep === 'plan_summary'
              ? 'p-6 sm:p-7 rounded-3xl bg-gradient-to-r from-sky-50/70 via-white to-sky-50/40 border-2 border-orange-400 ring-4 ring-orange-400 ring-offset-4 ring-offset-slate-50 guided-blink-glow-card shadow-2xl shadow-orange-500/20 z-20'
              : ''
          } ${
            isGuidedDemo && guidedSubStep && guidedSubStep !== 'plan_summary'
              ? 'opacity-60'
              : ''
          }`}
        >
          {/* Floating Guided Demo Callout for Sub-Step 1 */}
          {isGuidedDemo && guidedSubStep === 'plan_summary' && (
            <div className="absolute top-2 right-2 sm:right-6 z-30 w-[92vw] sm:w-[420px] max-w-full">
              <GuidedCalloutCard
                badge="🎯 GUIDED DEMO"
                title="Your Personalized Health Plan"
                description="This section turns the assessment findings into personalized health guidance based on the available health evidence."
                nextLabel="Next →"
                onNext={() => onNextGuidedStep?.('recommendations')}
                pointerDirection="none"
              />
            </div>
          )}

          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-100 text-sky-800 text-xs font-bold">
            <Sparkles className="w-3.5 h-3.5 text-sky-600" />
            <span>Personalized Health Guide</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            ✨ Your Personalized Health Plan
          </h1>
          <p className="text-sm sm:text-base text-slate-700 max-w-3xl leading-relaxed font-medium">
            Based on your health results, here are the areas that may be most important for you to focus on.
          </p>

          <div className="pt-2 text-xs text-slate-500 flex flex-wrap items-center gap-3">
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
          </div>
        </div>

        {/* ── 📅 YOUR PROGRESS PLAN CREATION COMPONENT ──────────────────────── */}
        <div
          id="guided-progress-plan-section"
          className={`mt-6 p-6 sm:p-7 rounded-3xl bg-gradient-to-br from-sky-50 via-indigo-50/50 to-teal-50/40 transition-all duration-300 relative flex flex-col lg:flex-row lg:items-center justify-between gap-6 ${
            isGuidedDemo && (guidedSubStep === 'progress_plan' || guidedSubStep === 'select_plan')
              ? 'border-2 border-orange-400 ring-4 ring-orange-400 ring-offset-4 ring-offset-slate-50 guided-blink-glow-card shadow-2xl shadow-orange-500/20 z-20'
              : 'border-2 border-sky-200 shadow-sm'
          } ${
            isGuidedDemo && (guidedSubStep === 'plan_summary' || guidedSubStep === 'recommendations')
              ? 'opacity-60'
              : ''
          }`}
        >
          {/* Floating Guided Demo Callout for Sub-Step 3 */}
          {isGuidedDemo && guidedSubStep === 'progress_plan' && (
            <div className="absolute top-full mt-3 left-4 sm:left-6 z-30 w-[92vw] sm:w-[440px] max-w-full">
              <GuidedCalloutCard
                badge="🎯 GUIDED DEMO"
                title="Turn Recommendations Into a Routine"
                description="This section lets you convert the personalized recommendations into a structured routine and track your progress over time."
                nextLabel="Next →"
                onNext={() => onNextGuidedStep?.('select_plan')}
                pointerDirection="up"
              />
            </div>
          )}

          <div className="space-y-1.5 max-w-xl">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-100 text-sky-900 text-xs font-black border border-sky-200">
              <Calendar className="w-3.5 h-3.5 text-sky-700" />
              <span>📅 YOUR PROGRESS PLAN</span>
            </div>
            <h3 className="text-lg sm:text-xl font-black text-slate-950 tracking-tight">
              Turn these recommendations into a guided routine
            </h3>
            <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-normal">
              Track your daily habit progress with an interactive step-by-step checklist and download a printable plan.
            </p>
          </div>

          <div
            id="guided-progress-plan-buttons"
            className={`flex flex-wrap sm:flex-nowrap items-center gap-3 shrink-0 relative transition-all duration-300 ${
              isGuidedDemo && guidedSubStep === 'select_plan'
                ? 'p-2.5 rounded-3xl bg-amber-50/90 border-2 border-amber-400 ring-4 ring-orange-400/80 shadow-2xl shadow-orange-500/30'
                : ''
            }`}
          >
            {/* Floating Guided Demo Callout for Sub-Step 4 */}
            {isGuidedDemo && guidedSubStep === 'select_plan' && (
              <div className="absolute top-full mt-4 right-0 sm:right-2 z-30 w-[92vw] sm:w-[420px] max-w-full">
                <GuidedCalloutCard
                  badge="🎯 GUIDED DEMO"
                  title="Choose Your Plan"
                  description="Select a duration to turn your personalized recommendations into a structured routine."
                  actionInstruction="👉 Choose any plan to continue."
                  pointerDirection="up"
                />
              </div>
            )}

            <button
              type="button"
              onClick={() => onCreateProgressPlan('1_week')}
              className={`flex-1 sm:flex-none flex items-center justify-center space-x-2 px-4 py-3 bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs sm:text-sm rounded-2xl shadow-md shadow-sky-600/20 transition-all cursor-pointer ${
                isGuidedDemo && guidedSubStep === 'select_plan'
                  ? 'ring-4 ring-orange-400/90 guided-blink-glow-orange scale-105 font-black border border-white shadow-xl'
                  : 'transform hover:scale-[1.02] active:scale-[0.98]'
              }`}
            >
              <span>Create 1 Week Plan →</span>
            </button>
            <button
              type="button"
              onClick={() => onCreateProgressPlan('1_month')}
              className={`flex-1 sm:flex-none flex items-center justify-center space-x-2 px-4 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs sm:text-sm rounded-2xl shadow-md shadow-emerald-600/20 transition-all cursor-pointer ${
                isGuidedDemo && guidedSubStep === 'select_plan'
                  ? 'ring-4 ring-emerald-400/90 guided-blink-glow-orange scale-105 font-black border border-white shadow-xl'
                  : 'transform hover:scale-[1.02] active:scale-[0.98]'
              }`}
            >
              <span>Create 1 Month Plan →</span>
            </button>
            <button
              type="button"
              onClick={() => onCreateProgressPlan('3_months')}
              className={`flex-1 sm:flex-none flex items-center justify-center space-x-2 px-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs sm:text-sm rounded-2xl shadow-md shadow-indigo-600/20 transition-all cursor-pointer ${
                isGuidedDemo && guidedSubStep === 'select_plan'
                  ? 'ring-4 ring-indigo-400/90 guided-blink-glow-orange scale-105 font-black border border-white shadow-xl'
                  : 'transform hover:scale-[1.02] active:scale-[0.98]'
              }`}
            >
              <span>Create 3 Months Plan →</span>
            </button>
          </div>
        </div>
      </div>

      {/* ── 1. 🩺 A. YOUR ASSESSMENT SUMMARY ─────────────────────────────────── */}
      {section_a_your_results && (
        <div className={`bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xl shadow-sky-500/5 space-y-4 transition-opacity duration-300 ${
          isGuidedDemo ? 'opacity-60' : ''
        }`}>
          <div className="flex items-center space-x-3 pb-3 border-b border-slate-100">
            <div className="p-2.5 rounded-2xl bg-sky-50 text-sky-700 border border-sky-200">
              <TrendingUp className="w-6 h-6 text-sky-600" />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
                🩺 A. Your Assessment Summary
              </h2>
              <p className="text-xs text-slate-500">Overview of what your health assessment showed</p>
            </div>
          </div>

          <p className="text-sm sm:text-base text-slate-800 leading-relaxed font-normal pt-1">
            {section_a_your_results.body}
          </p>

          {/* Condition Pills */}
          {section_a_your_results.evaluated_conditions && section_a_your_results.evaluated_conditions.length > 0 && (
            <div className="pt-3 flex flex-wrap gap-2.5">
              {section_a_your_results.evaluated_conditions.map((cond, idx) => {
                const isElevated = cond.risk_level.toLowerCase().includes('high') || cond.risk_level.toLowerCase().includes('moderate');
                return (
                  <div
                    key={idx}
                    className={`px-3.5 py-2 rounded-2xl text-xs flex items-center space-x-2 font-bold border ${
                      isElevated
                        ? 'bg-rose-50/80 text-rose-900 border-rose-200'
                        : 'bg-slate-50 text-slate-800 border-slate-200'
                    }`}
                  >
                    <span>{cond.disease.replace(/_/g, ' ')}:</span>
                    <span className={isElevated ? 'text-rose-700' : 'text-slate-600'}>{cond.risk_level}</span>
                    <span className="text-slate-400 font-mono text-[11px]">({cond.probability_percentage})</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ── 2. 🔍 B. KEY FACTORS CONTRIBUTING TO YOUR RESULTS ────────────────── */}
      {section_b_what_is_contributing && (
        <div className={`bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xl shadow-sky-500/5 space-y-6 transition-opacity duration-300 ${
          isGuidedDemo ? 'opacity-60' : ''
        }`}>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-100">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-2xl bg-amber-50 text-amber-700 border border-amber-200">
                <HeartPulse className="w-6 h-6 text-amber-600" />
              </div>
              <div>
                <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
                  🔍 B. Key Factors Contributing to Your Results
                </h2>
                <p className="text-xs sm:text-sm text-slate-600">
                  Your key health measurements and how they compare to standard target ranges
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-1">
            {section_b_what_is_contributing.contributing_items.map((item, idx) => {
              const isAbove = item.status === 'above_expected_range';
              const isBelow = item.status === 'below_expected_range';
              const isNormal = item.status === 'within_expected_range';
              const isUnavailable = item.status === 'interpretation_unavailable';

              const knownRange = KNOWN_RANGES[item.parameter];
              const numericVal = typeof item.patient_value === 'number' ? item.patient_value : parseFloat(item.patient_value);
              const hasNumericRange = !isNaN(numericVal) && knownRange !== undefined;

              // Calculate range bar percentage marker (clamped between 5% and 95%)
              let markerPercent = 50;
              let targetLeftPercent = 25;
              let targetWidthPercent = 50;

              if (hasNumericRange) {
                const rangeSpan = knownRange.max - knownRange.min;
                const visualMin = Math.max(0, knownRange.min - rangeSpan * 0.8);
                const visualMax = knownRange.max + rangeSpan * 0.8;
                const totalSpan = visualMax - visualMin;

                targetLeftPercent = Math.max(5, Math.min(80, ((knownRange.min - visualMin) / totalSpan) * 100));
                const targetRightPercent = Math.max(20, Math.min(95, ((knownRange.max - visualMin) / totalSpan) * 100));
                targetWidthPercent = Math.max(15, targetRightPercent - targetLeftPercent);

                markerPercent = Math.max(6, Math.min(94, ((numericVal - visualMin) / totalSpan) * 100));
              }

              return (
                <div
                  key={idx}
                  className="p-5 sm:p-6 rounded-3xl bg-slate-50/70 border-2 border-slate-200 hover:border-sky-300 transition-all flex flex-col justify-between space-y-4"
                >
                  <div className="space-y-3">
                    {/* Top Row: Friendly Name + Status Badge */}
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="text-base font-extrabold text-slate-900 leading-snug">
                        {item.friendly_name}
                      </h3>

                      {isAbove && (
                        <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full bg-rose-100 text-rose-900 border border-rose-300 text-xs font-black shrink-0">
                          <span>↑ Above Target</span>
                        </span>
                      )}
                      {isBelow && (
                        <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full bg-amber-100 text-amber-900 border border-amber-300 text-xs font-black shrink-0">
                          <span>↓ Below Target</span>
                        </span>
                      )}
                      {isNormal && (
                        <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300 text-xs font-black shrink-0">
                          <span>✓ Within Target</span>
                        </span>
                      )}
                      {isUnavailable && (
                        <span className="inline-flex items-center px-3 py-1 rounded-full bg-slate-200 text-slate-700 text-xs font-bold shrink-0">
                          <span>Recorded</span>
                        </span>
                      )}
                    </div>

                    {/* Main Patient Value & Target Callout */}
                    <div className="grid grid-cols-2 gap-3 p-3.5 bg-white rounded-2xl border border-slate-200/80">
                      <div>
                        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                          YOUR VALUE
                        </div>
                        <div className="text-2xl sm:text-3xl font-black text-slate-950 mt-0.5">
                          {item.patient_value} <span className="text-xs font-bold text-slate-600">{item.unit}</span>
                        </div>
                      </div>

                      <div className="border-l border-slate-100 pl-3">
                        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                          STANDARD TARGET
                        </div>
                        <div className="text-sm sm:text-base font-extrabold text-slate-800 mt-1">
                          {knownRange ? knownRange.display : 'Not standard'}
                        </div>
                      </div>
                    </div>

                    {/* Visual Range Indicator Bar (Safety rule: only shown when reference range is available) */}
                    {hasNumericRange && !isUnavailable ? (
                      <div className="space-y-1.5 pt-1">
                        <div className="relative h-4 bg-slate-200 rounded-full overflow-hidden">
                          {/* Standard Target Green Zone */}
                          <div
                            className="absolute top-0 bottom-0 bg-emerald-300/80 border-x border-emerald-500"
                            style={{ left: `${targetLeftPercent}%`, width: `${targetWidthPercent}%` }}
                          />
                          {/* Patient Value Marker */}
                          <div
                            className={`absolute top-0 bottom-0 w-2.5 rounded-full shadow-md transform -translate-x-1/2 ${
                              isAbove ? 'bg-rose-600' : isBelow ? 'bg-amber-600' : 'bg-emerald-700'
                            }`}
                            style={{ left: `${markerPercent}%` }}
                          />
                        </div>

                        <div className="flex justify-between text-[10px] font-bold text-slate-500 px-1">
                          <span>Lower</span>
                          <span className="text-emerald-800 font-extrabold">Healthy Target Range ({knownRange.display})</span>
                          <span>Higher</span>
                        </div>
                      </div>
                    ) : (
                      <div className="text-[11px] text-slate-500 italic bg-white p-2.5 rounded-xl border border-slate-100">
                        This value is shown as recorded. A standard reference range is not available for this parameter.
                      </div>
                    )}
                  </div>

                  {/* Simple Conversational Explanation */}
                  <p className="text-xs sm:text-sm text-slate-800 leading-relaxed border-t border-slate-200/80 pt-3 font-normal">
                    {item.explanation_sentence}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── 3. 🎯 C. WHAT SHOULD YOU FOCUS ON FIRST? ─────────────────────────── */}
      {section_c_what_to_focus_on_first && (
        <div className={`bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xl shadow-sky-500/5 space-y-6 transition-opacity duration-300 ${
          isGuidedDemo ? 'opacity-60' : ''
        }`}>
          <div className="flex items-center space-x-3 pb-3 border-b border-slate-100">
            <div className="p-2.5 rounded-2xl bg-indigo-50 text-indigo-700 border border-indigo-200">
              <Target className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
                🎯 C. What Should You Focus On First?
              </h2>
              <p className="text-xs sm:text-sm text-slate-600">
                Ranked in order of greatest positive impact for your specific health results
              </p>
            </div>
          </div>

          <div className="space-y-4 pt-1">
            {section_c_what_to_focus_on_first.priorities.map((p, idx) => {
              const rankColor =
                p.rank === 1
                  ? 'bg-sky-600 text-white'
                  : p.rank === 2
                  ? 'bg-emerald-600 text-white'
                  : 'bg-indigo-600 text-white';

              return (
                <div
                  key={idx}
                  className="p-5 sm:p-6 rounded-3xl bg-slate-50 border-2 border-slate-200 hover:border-slate-300 transition-all flex flex-col sm:flex-row sm:items-start gap-4"
                >
                  <div className={`w-10 h-10 rounded-2xl ${rankColor} flex items-center justify-center font-black text-base shrink-0 shadow-sm`}>
                    #{p.rank}
                  </div>
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-black uppercase tracking-wider text-slate-500">
                        PRIORITY {p.rank}
                      </span>
                    </div>
                    <h3 className="text-lg sm:text-xl font-extrabold text-slate-950">
                      {p.title}
                    </h3>
                    <p className="text-sm text-slate-800 leading-relaxed font-normal">
                      {p.explanation}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── 4. ✅ D. YOUR ACTIONABLE RECOMMENDATIONS ────────────────────────── */}
      {section_d_personalized_recommendations && (
        <div
          id="guided-actionable-recommendations"
          className={`bg-white p-6 sm:p-8 rounded-3xl border transition-all duration-300 relative space-y-6 ${
            isGuidedDemo && guidedSubStep === 'recommendations'
              ? 'border-2 border-orange-400 ring-4 ring-orange-400 ring-offset-4 ring-offset-slate-50 guided-blink-glow-card shadow-2xl shadow-orange-500/20 z-20'
              : 'border-slate-200 shadow-xl shadow-sky-500/5'
          } ${
            isGuidedDemo && guidedSubStep && guidedSubStep !== 'recommendations'
              ? 'opacity-60'
              : ''
          }`}
        >
          {/* Floating Guided Demo Callout for Sub-Step 2 */}
          {isGuidedDemo && guidedSubStep === 'recommendations' && (
            <div className="absolute top-4 right-4 sm:right-8 z-30 w-[92vw] sm:w-[440px] max-w-full">
              <GuidedCalloutCard
                badge="🎯 GUIDED DEMO"
                title="Actionable Recommendations"
                description="These recommendations translate the assessment findings into practical actions that can be incorporated into everyday life."
                nextLabel="Next →"
                onNext={() => onNextGuidedStep?.('progress_plan')}
                pointerDirection="none"
              />
            </div>
          )}

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-2xl bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-6 h-6 text-emerald-600" />
              </div>
              <div>
                <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
                  ✅ D. Your Actionable Recommendations
                </h2>
                <p className="text-xs sm:text-sm text-slate-600">
                  Practical, everyday steps backed by verified clinical guidelines
                </p>
              </div>
            </div>
            <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold self-start sm:self-auto">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>{section_d_personalized_recommendations.recommendations.length} Action Pillars</span>
            </span>
          </div>

          <div className={`grid grid-cols-1 md:grid-cols-2 gap-5 pt-1 transition-opacity duration-300 ${
            isGuidedDemo && guidedSubStep === 'recommendations' ? 'opacity-75' : ''
          }`}>
            {section_d_personalized_recommendations.recommendations.map((rec, idx) => (
              <div
                key={idx}
                className="p-6 rounded-3xl bg-white border-2 border-slate-200 shadow-md hover:shadow-lg hover:border-sky-300 transition-all flex flex-col justify-between space-y-5"
              >
                <div className="space-y-3.5">
                  <div className="flex items-center justify-between">
                    <div className="p-3 rounded-2xl bg-slate-100 border border-slate-200">
                      {getPillarIcon(rec.title)}
                    </div>
                    <span className="text-xs font-black text-slate-700 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
                      Action #{rec.priority_rank}
                    </span>
                  </div>

                  <h3 className="text-lg sm:text-xl font-extrabold text-slate-950 leading-tight">
                    {rec.title}
                  </h3>

                  <p className="text-sm text-slate-800 leading-relaxed font-normal">
                    {rec.recommendation_text}
                  </p>
                </div>

                {/* Target Highlight Box */}
                {rec.numerical_target && (
                  <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-start space-x-3">
                    <Target className="w-5 h-5 text-emerald-700 shrink-0 mt-0.5" />
                    <div>
                      <div className="text-[11px] font-black text-emerald-900 uppercase tracking-wider">
                        🎯 YOUR TARGET
                      </div>
                      <div className="text-sm sm:text-base font-black text-emerald-950 mt-0.5">
                        {rec.numerical_target}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── 5. 💡 E. WHY THESE ACTIONS WERE CHOSEN FOR YOU ─────────────────── */}
      {section_e_why_suggested && section_e_why_suggested.items.length > 0 && (
        <div className={`bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xl shadow-sky-500/5 space-y-4 transition-opacity duration-300 ${
          isGuidedDemo ? 'opacity-60' : ''
        }`}>
          <div className="flex items-center space-x-3 pb-3 border-b border-slate-100">
            <div className="p-2.5 rounded-2xl bg-teal-50 text-teal-700 border border-teal-200">
              <ShieldCheck className="w-6 h-6 text-teal-600" />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
                💡 E. Why These Actions Were Chosen for You
              </h2>
              <p className="text-xs text-slate-500">Verified evidence sources backing your personalized recommendations</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
            {section_e_why_suggested.items.map((item, idx) => (
              <div
                key={idx}
                className="p-4 sm:p-5 rounded-2xl bg-slate-50 border border-slate-200 text-xs sm:text-sm text-slate-700 space-y-2"
              >
                <div className="font-extrabold text-slate-900 text-sm">
                  {item.title}
                </div>
                <p className="leading-relaxed text-slate-700">
                  {item.reason}
                </p>
                <div className="pt-2 border-t border-slate-200/60 text-[11px] font-bold text-slate-500 flex items-center space-x-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Source: {item.evidence_source}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── BOTTOM MEDICAL ADVISORY & ACTIONS ──────────────────────────────── */}
      <div className={`p-5 rounded-2xl bg-sky-50/70 border border-sky-200 text-xs sm:text-sm text-slate-700 flex items-start space-x-3 leading-relaxed transition-opacity duration-300 ${
        isGuidedDemo ? 'opacity-60' : ''
      }`}>
        <ShieldCheck className="w-5 h-5 text-sky-700 shrink-0 mt-0.5" />
        <p>
          <strong className="text-slate-900 font-bold">Medical Advisory:</strong> This personalized health plan is generated using verified clinical practice guidelines for informational and lifestyle support. It is not a substitute for professional clinical medical advice, diagnosis, or treatment. Always discuss major lifestyle changes with your healthcare provider.
        </p>
      </div>

      <div className="flex justify-center pt-2">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center space-x-2 px-8 py-3.5 bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm rounded-2xl shadow-xl shadow-slate-900/20 transition-all transform hover:scale-[1.02] cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Assessment Results</span>
        </button>
      </div>
    </div>
  );
};
