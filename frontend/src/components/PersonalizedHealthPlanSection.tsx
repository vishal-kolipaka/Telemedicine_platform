import React from 'react';
import type { HealthPlanResponse } from '../types/reader';
import {
  Sparkles,
  Target,
  ArrowRight,
  TrendingUp,
  Activity,
  Heart,
  Scale,
  Apple,
  Clock,
  ShieldCheck,
  CheckCircle2,
  Info,
  ChevronRight
} from 'lucide-react';

interface Props {
  healthPlan?: HealthPlanResponse | null;
}

export const PersonalizedHealthPlanSection: React.FC<Props> = ({ healthPlan }) => {
  // If health plan is null or unavailable, show a clean, friendly fallback
  if (!healthPlan || !healthPlan.sections) {
    return (
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex items-center space-x-3 text-slate-800">
          <div className="p-2.5 rounded-2xl bg-sky-50 text-sky-700 border border-sky-200">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base sm:text-lg font-bold text-slate-900">Your Personalized Health Plan</h3>
            <p className="text-xs text-slate-500">Tailored lifestyle guidance based on clinical guidelines</p>
          </div>
        </div>
        <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 text-xs sm:text-sm text-slate-600 flex items-start space-x-3">
          <Info className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            {healthPlan?.message ||
              "We don't currently have enough verified guideline information to create a personalized recommendation for this result. Please speak with a qualified healthcare professional for further guidance."}
          </p>
        </div>
      </div>
    );
  }

  const {
    section_a_your_results,
    section_b_what_is_contributing,
    section_c_what_to_focus_on_first,
    section_d_personalized_recommendations,
    section_e_why_suggested
  } = healthPlan.sections;

  // Icon selector for recommendation cards
  const getPillarIcon = (title: string) => {
    const t = title.toLowerCase();
    if (t.includes('physical') || t.includes('activity') || t.includes('movement') || t.includes('walk')) {
      return <Activity className="w-5 h-5 text-emerald-600" />;
    }
    if (t.includes('diet') || t.includes('fiber') || t.includes('nutrition') || t.includes('food')) {
      return <Apple className="w-5 h-5 text-sky-600" />;
    }
    if (t.includes('weight') || t.includes('caloric') || t.includes('bmi')) {
      return <Scale className="w-5 h-5 text-indigo-600" />;
    }
    if (t.includes('sedentary') || t.includes('sitting') || t.includes('sleep')) {
      return <Clock className="w-5 h-5 text-amber-600" />;
    }
    return <Target className="w-5 h-5 text-teal-600" />;
  };

  return (
    <div className="bg-gradient-to-b from-white to-slate-50/50 rounded-3xl p-6 sm:p-8 lg:p-10 border border-slate-200 shadow-xs space-y-8 sm:space-y-10">
      {/* ── HEADER ──────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 rounded-2xl bg-sky-600 text-white shadow-xs">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-sky-700 bg-sky-50 px-2.5 py-0.5 rounded-full border border-sky-200 inline-block mb-1">
              Personalized Plan
            </span>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              {healthPlan.summary_title || 'Your Personalized Health Plan'}
            </h2>
          </div>
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-500 bg-slate-50 px-3 py-1.5 rounded-full border border-slate-200 shrink-0">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Evidence-Based & Validated</span>
        </div>
      </div>

      {/* ── SECTION A: YOUR RESULTS ──────────────────────────────────────── */}
      {section_a_your_results && (
        <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-2xs space-y-4">
          <div className="flex items-center space-x-2 text-slate-900">
            <TrendingUp className="w-5 h-5 text-sky-600" />
            <h3 className="text-base sm:text-lg font-bold">
              {section_a_your_results.title || 'A. What Your Results Mean'}
            </h3>
          </div>
          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
            {section_a_your_results.body}
          </p>

          {/* Evaluated Conditions Quick Pill Strip */}
          {section_a_your_results.evaluated_conditions && section_a_your_results.evaluated_conditions.length > 0 && (
            <div className="pt-2 flex flex-wrap gap-2.5">
              {section_a_your_results.evaluated_conditions.map((cond, idx) => (
                <div
                  key={idx}
                  className="px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-xs flex items-center space-x-2"
                >
                  <span className="font-semibold text-slate-800">{cond.disease.replace(/_/g, ' ')}:</span>
                  <span className="font-bold text-slate-600">{cond.risk_level}</span>
                  <span className="text-slate-400 font-mono text-[11px]">({cond.probability_percentage})</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── SECTION B: WHAT'S CONTRIBUTING TO YOUR RISK ───────────────────── */}
      {section_b_what_is_contributing && (
        <div className="space-y-4">
          <div className="flex items-center space-x-2 text-slate-900">
            <Heart className="w-5 h-5 text-rose-500" />
            <h3 className="text-base sm:text-lg font-bold">
              {section_b_what_is_contributing.title || 'B. Key Factors Contributing to Your Results'}
            </h3>
          </div>
          <p className="text-xs sm:text-sm text-slate-500">
            {section_b_what_is_contributing.body}
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5 pt-1">
            {section_b_what_is_contributing.contributing_items.map((item, idx) => {
              const isAbove = item.status === 'above_expected_range';
              const isBelow = item.status === 'below_expected_range';
              const isNormal = item.status === 'within_expected_range';

              const badgeColor = isAbove
                ? 'bg-amber-50 text-amber-800 border-amber-200'
                : isBelow
                ? 'bg-rose-50 text-rose-800 border-rose-200'
                : isNormal
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-slate-50 text-slate-700 border-slate-200';

              return (
                <div
                  key={idx}
                  className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-2xs space-y-2.5 flex flex-col justify-between"
                >
                  <div className="space-y-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-bold text-slate-800 line-clamp-1">{item.friendly_name}</span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${badgeColor} shrink-0`}>
                        {isAbove ? 'Above Target' : isBelow ? 'Below Target' : isNormal ? 'Normal' : 'Measured'}
                      </span>
                    </div>
                    <div className="text-base font-extrabold text-slate-900">
                      {item.patient_value} <span className="text-xs font-medium text-slate-500">{item.unit}</span>
                    </div>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed border-t border-slate-100 pt-2">
                    {item.explanation_sentence}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── SECTION C: WHAT TO FOCUS ON FIRST (PRIORITIES) ─────────────────── */}
      {section_c_what_to_focus_on_first && (
        <div className="space-y-4">
          <div className="flex items-center space-x-2 text-slate-900">
            <Target className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base sm:text-lg font-bold">
              {section_c_what_to_focus_on_first.title || 'C. What Should You Focus On First?'}
            </h3>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 leading-relaxed">
            {section_c_what_to_focus_on_first.intro}
          </p>

          <div className="space-y-3 pt-1">
            {section_c_what_to_focus_on_first.priorities.map((p, idx) => (
              <div
                key={idx}
                className="p-4 sm:p-5 rounded-2xl bg-white border border-slate-200/90 shadow-2xs flex items-start space-x-4"
              >
                <div className="w-8 h-8 rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center justify-center font-extrabold text-sm shrink-0 mt-0.5">
                  {p.rank}
                </div>
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-slate-900">{p.title}</h4>
                  <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">{p.explanation}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── SECTION D: YOUR ACTION PLAN (MAIN RECOMMENDATIONS) ─────────────── */}
      {section_d_personalized_recommendations && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-slate-900">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              <h3 className="text-base sm:text-lg font-bold">
                {section_d_personalized_recommendations.title || 'D. Your Actionable Recommendations'}
              </h3>
            </div>
            <span className="text-xs font-bold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
              {section_d_personalized_recommendations.recommendations.length} Action Pillars
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-500">
            {section_d_personalized_recommendations.intro}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-1">
            {section_d_personalized_recommendations.recommendations.map((rec, idx) => (
              <div
                key={idx}
                className="p-5 rounded-2xl bg-white border-2 border-slate-200/90 shadow-xs hover:border-sky-300 transition-all flex flex-col justify-between space-y-4"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                      {getPillarIcon(rec.title)}
                    </div>
                    <span className="text-[11px] font-extrabold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                      Pillar {rec.priority_rank}
                    </span>
                  </div>

                  <h4 className="text-base font-bold text-slate-900 leading-tight">
                    {rec.title}
                  </h4>

                  {rec.numerical_target && (
                    <div className="p-2.5 rounded-xl bg-sky-50/70 border border-sky-200 text-xs">
                      <span className="font-bold text-sky-900 block mb-0.5">Evidence Target</span>
                      <span className="text-sky-800 font-semibold">{rec.numerical_target}</span>
                    </div>
                  )}

                  <p className="text-xs sm:text-sm text-slate-700 leading-relaxed">
                    {rec.recommendation_text}
                  </p>
                </div>

                <div className="pt-2 border-t border-slate-100 flex items-center text-[11px] font-bold text-sky-700">
                  <span>Guideline Grounded</span>
                  <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── SECTION E: WHY THESE WERE SUGGESTED ───────────────────────────── */}
      {section_e_why_suggested && (
        <div className="p-5 sm:p-6 rounded-2xl bg-slate-50/80 border border-slate-200 space-y-3.5">
          <div className="flex items-center space-x-2 text-slate-900">
            <Info className="w-4 h-4 text-sky-600" />
            <h4 className="text-sm sm:text-base font-bold">
              {section_e_why_suggested.title || 'E. Why These Actions Were Chosen for You'}
            </h4>
          </div>

          <div className="space-y-2.5 text-xs sm:text-sm text-slate-600">
            {section_e_why_suggested.items.map((item, idx) => (
              <div key={idx} className="flex items-start space-x-2.5">
                <ArrowRight className="w-3.5 h-3.5 text-sky-600 shrink-0 mt-1" />
                <p className="leading-relaxed">
                  <strong className="text-slate-800">{item.title}:</strong> {item.reason}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
