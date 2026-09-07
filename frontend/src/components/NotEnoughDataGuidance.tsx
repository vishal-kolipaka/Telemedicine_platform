import React, { useState } from 'react';
import {
  Sparkles,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Activity,
  Heart,
  Dna,
  PlusCircle,
} from 'lucide-react';

export const FRIENDLY_FIELD_NAMES: Record<string, string> = {
  // Clinical
  Age: 'Age',
  Gender: 'Gender',
  Height: 'Height',
  Weight: 'Weight',
  BMI: 'Body Mass Index (BMI)',
  Waist_Circumference: 'Waist Circumference',
  Systolic_BP: 'Systolic Blood Pressure',
  Diastolic_BP: 'Diastolic Blood Pressure',
  Fasting_Blood_Glucose: 'Fasting Blood Glucose',
  HbA1c: 'HbA1c (Glycated Hemoglobin)',
  Triglycerides: 'Triglycerides',
  HDL: 'HDL Cholesterol',
  LDL: 'LDL Cholesterol',
  ALT: 'ALT Liver Enzyme (SGPT)',
  AST: 'AST Liver Enzyme (SGOT)',
  Family_History_Diabetes: 'Family History of Diabetes',
  Family_History_Hypertension: 'Family History of High Blood Pressure',
  Family_History_CVD: 'Family History of Cardiovascular Disease / Stroke',

  // Wearable
  Average_Daily_Steps: 'Average Daily Steps',
  Active_Minutes: 'Active Minutes',
  Sedentary_Time_Minutes: 'Sedentary Time',
  Resting_Heart_Rate: 'Resting Heart Rate',
  Heart_Rate_Variability_RMSSD: 'Heart Rate Variability (HRV)',
  Sleep_Duration_Hours: 'Sleep Duration',
  Sleep_Efficiency_Score: 'Sleep Efficiency Score',
  Autonomic_Stress_Score: 'Autonomic Stress Score',
  Activity_Energy_Expenditure: 'Activity Energy Expenditure',
  Exercise_Frequency_Days: 'Exercise Frequency',
  CGM_Average_Glucose: 'Average Glucose (CGM)',
  CGM_Glucose_CV: 'Glucose Variability CV (CGM)',
  CGM_Time_In_Range: 'Time In Range TIR (CGM)',
  CGM_Time_Above_Range: 'Time Above Range TAR (CGM)',
  CGM_Time_Below_Range: 'Time Below Range TBR (CGM)',

  // Gut Microbiome
  Akkermansia: 'Akkermansia muciniphila',
  Faecalibacterium: 'Faecalibacterium prausnitzii',
  Roseburia: 'Roseburia',
  Bifidobacterium: 'Bifidobacterium',
  Bacteroides: 'Bacteroides',
  Prevotella: 'Prevotella',
  Ruminococcus: 'Ruminococcus',
  Blautia: 'Blautia',
  Collinsella: 'Collinsella',
  Escherichia_Shigella: 'Escherichia / Shigella',
  Coprococcus: 'Coprococcus',
  Alistipes: 'Alistipes',
  Subdoligranulum: 'Subdoligranulum',
  Enterococcus: 'Enterococcus',
  Eubacterium: 'Eubacterium',
  Parabacteroides: 'Parabacteroides',
  Lactobacillus: 'Lactobacillus',
  Klebsiella: 'Klebsiella',
  Streptococcus: 'Streptococcus',
  Eggerthella: 'Eggerthella',
  Other_Taxa: 'Other Gut Microbiome Taxa',
};

export interface CategoryGuidanceInfo {
  id: 'clinical' | 'wearable' | 'gut';
  title: string;
  iconType: 'clinical' | 'wearable' | 'gut';
  totalRequired: number;
  foundCount: number;
  missingCount: number;
  missingFields: string[];
  isClosest: boolean;
}

interface Props {
  categories: CategoryGuidanceInfo[];
  closestCategory: CategoryGuidanceInfo | null;
  onProvideMissing: (categoryId: 'clinical' | 'wearable' | 'gut') => void;
  onProceedAnyway: () => void;
}

export const NotEnoughDataGuidance: React.FC<Props> = ({
  categories,
  closestCategory,
  onProvideMissing,
  onProceedAnyway,
}) => {
  const [expandedCategoryId, setExpandedCategoryId] = useState<string | null>(
    closestCategory?.id || null
  );

  const getCategoryIcon = (type: 'clinical' | 'wearable' | 'gut') => {
    switch (type) {
      case 'clinical':
        return <Activity className="w-5 h-5 text-sky-600" />;
      case 'wearable':
        return <Heart className="w-5 h-5 text-rose-600" />;
      case 'gut':
        return <Dna className="w-5 h-5 text-indigo-600" />;
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedCategoryId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="bg-white p-6 sm:p-8 rounded-3xl border-2 border-amber-200/90 shadow-xl shadow-amber-500/5 space-y-6 animate-fade-in">
      {/* Header Banner */}
      <div className="space-y-3">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-amber-100 text-amber-900 text-xs font-bold border border-amber-300">
          <Sparkles className="w-4 h-4 text-amber-700" />
          <span>Almost Ready for Assessment</span>
        </div>

        <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          We're almost there!
        </h3>

        <p className="text-slate-600 text-sm sm:text-base leading-relaxed max-w-3xl">
          We don't quite have enough information yet to generate a full health assessment, but you're very close.
          Completing <strong>even ONE category</strong> is enough to generate your assessment results—you do not need to fill out everything.
        </p>
      </div>

      {/* Recommended Closest Path Highlight Box */}
      {closestCategory && (
        <div className="p-5 rounded-2xl bg-gradient-to-r from-sky-50 via-cyan-50/50 to-white border-2 border-sky-300 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xs">
          <div className="flex items-start space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-sky-600 text-white flex items-center justify-center font-bold shrink-0 shadow-md shadow-sky-600/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="space-y-0.5">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold text-sky-800 uppercase tracking-wider">
                  Recommended Quickest Path
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-sky-200/80 text-sky-900 font-extrabold">
                  Easiest
                </span>
              </div>
              <h4 className="text-base font-extrabold text-slate-900">
                Complete {closestCategory.title} ({closestCategory.missingCount} more {closestCategory.missingCount === 1 ? 'value' : 'values'} needed)
              </h4>
              <p className="text-xs text-slate-600">
                You only need to provide {closestCategory.missingCount} additional {closestCategory.missingCount === 1 ? 'piece' : 'pieces'} of information to unlock your health assessment.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => onProvideMissing(closestCategory.id)}
            className="w-full sm:w-auto flex items-center justify-center space-x-2 px-6 py-3 bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold rounded-2xl shadow-lg shadow-sky-600/25 transition-all transform hover:scale-[1.02] cursor-pointer shrink-0"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Provide {closestCategory.title} Info</span>
          </button>
        </div>
      )}

      {/* Category Overview Cards */}
      <div className="space-y-3 pt-2">
        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          Assessment Categories Status
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {categories.map((cat) => {
            const isExpanded = expandedCategoryId === cat.id;

            return (
              <div
                key={cat.id}
                className={`p-4 rounded-2xl border transition-all ${
                  cat.isClosest
                    ? 'bg-white border-sky-400 shadow-md ring-2 ring-sky-100'
                    : 'bg-slate-50 border-slate-200'
                }`}
              >
                {/* Header */}
                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                  <div className="flex items-center space-x-2">
                    {getCategoryIcon(cat.iconType)}
                    <span className="text-sm font-bold text-slate-900">{cat.title}</span>
                  </div>
                  {cat.isClosest && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-sky-100 text-sky-800 font-extrabold">
                      Closest
                    </span>
                  )}
                </div>

                {/* Progress Stats */}
                <div className="py-3 space-y-1.5">
                  <div className="flex items-baseline justify-between text-xs">
                    <span className="text-slate-500 font-medium">Data Available</span>
                    <span className="font-mono font-bold text-slate-800">
                      {cat.foundCount} / {cat.totalRequired}
                    </span>
                  </div>

                  <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-1.5 rounded-full ${
                        cat.foundCount > 0 ? 'bg-sky-500' : 'bg-slate-300'
                      }`}
                      style={{
                        width: `${Math.min(100, Math.max(0, (cat.foundCount / cat.totalRequired) * 100))}%`,
                      }}
                    />
                  </div>

                  <div className="text-xs text-amber-800 font-semibold pt-1">
                    🟡 {cat.missingCount} {cat.missingCount === 1 ? 'value' : 'values'} needed
                  </div>
                </div>

                {/* Action & Toggle Details */}
                <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
                  <button
                    type="button"
                    onClick={() => toggleExpand(cat.id)}
                    className="flex items-center space-x-1 text-xs text-slate-500 hover:text-slate-800 font-medium transition-colors cursor-pointer"
                  >
                    <span>{isExpanded ? 'Hide Details' : 'View Missing'}</span>
                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>

                  <button
                    type="button"
                    onClick={() => onProvideMissing(cat.id)}
                    className="text-xs font-bold text-sky-700 hover:text-sky-900 transition-colors cursor-pointer"
                  >
                    Fill Now →
                  </button>
                </div>

                {/* Expandable Missing Items List */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-slate-200/80 space-y-1.5 animate-fade-in max-h-40 overflow-y-auto pr-1">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                      Missing Information:
                    </span>
                    {cat.missingFields.slice(0, 10).map((fieldKey) => (
                      <div
                        key={fieldKey}
                        className="text-xs text-slate-700 bg-white px-2.5 py-1 rounded-lg border border-slate-100 font-medium truncate"
                        title={FRIENDLY_FIELD_NAMES[fieldKey] || fieldKey}
                      >
                        • {FRIENDLY_FIELD_NAMES[fieldKey] || fieldKey}
                      </div>
                    ))}
                    {cat.missingFields.length > 10 && (
                      <span className="text-[11px] text-slate-400 italic block pl-1">
                        + {cat.missingFields.length - 10} additional taxa / biomarkers
                      </span>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Dual Option Footer Actions */}
      <div className="pt-4 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
        <button
          type="button"
          onClick={() => {
            if (closestCategory) {
              onProvideMissing(closestCategory.id);
            }
          }}
          className="w-full sm:w-auto flex items-center justify-center space-x-2 px-8 py-3.5 bg-gradient-to-r from-sky-600 via-sky-500 to-cyan-600 hover:from-sky-700 hover:to-cyan-700 text-white font-bold text-sm rounded-2xl shadow-xl shadow-sky-600/25 transition-all transform hover:scale-[1.02] cursor-pointer"
        >
          <PlusCircle className="w-5 h-5" />
          <span>Provide Missing Information</span>
        </button>

        <button
          type="button"
          onClick={onProceedAnyway}
          className="w-full sm:w-auto flex items-center justify-center space-x-2 px-6 py-3.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-2xl transition-colors cursor-pointer"
        >
          <span>Proceed with Available Information Anyway</span>
          <ArrowRight className="w-4 h-4 text-slate-500" />
        </button>
      </div>
    </div>
  );
};
