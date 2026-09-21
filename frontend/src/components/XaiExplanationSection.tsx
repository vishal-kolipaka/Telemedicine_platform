import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  TrendingUp,
  TrendingDown,
  Watch,
  Layers,
  AlertCircle,
  ShieldCheck,
  Microscope,
  Stethoscope,
} from 'lucide-react';
import type {
  XaiResponse,
  DiseaseExplanation,
  FeatureContribution,
} from '../types/reader';
import { formatRiskPercentage } from '../utils/formatters';

import type { Stage4SubStep } from '../pages/AnalyzePage';
import { GuidedCalloutCard } from './guided-demo/GuidedCalloutCard';

interface Props {
  xai: XaiResponse;
  activeDiseaseKey: string;
  onSelectDisease: (diseaseKey: string) => void;
  isGuidedDemo?: boolean;
  guidedSubStep?: Stage4SubStep;
  onNextGuidedStep?: (target?: Stage4SubStep) => void;
}

const DISEASE_KEYS = [
  'Type2_Diabetes',
  'Prediabetes',
  'High_Adiposity_Risk',
  'Metabolic_Syndrome',
  'NAFLD',
];

const DISEASE_LABELS: Record<string, string> = {
  Type2_Diabetes: 'Type 2 Diabetes',
  Prediabetes: 'Prediabetes',
  High_Adiposity_Risk: 'High Adiposity Risk',
  Metabolic_Syndrome: 'Metabolic Syndrome',
  NAFLD: 'NAFLD',
};

type ModalitySourceKey = 'all' | 'clinical' | 'wearable' | 'gut';

export const XaiExplanationSection: React.FC<Props> = ({
  xai,
  activeDiseaseKey,
  onSelectDisease,
  isGuidedDemo = false,
  guidedSubStep,
  onNextGuidedStep,
}) => {
  const [activeFilterTab, setActiveFilterTab] = useState<ModalitySourceKey>('all');

  const explanation: DiseaseExplanation | undefined = xai.explanations?.[activeDiseaseKey];

  // Determine available modalities for the currently active disease
  const availableSources: ('clinical' | 'wearable' | 'gut')[] = React.useMemo(() => {
    if (!explanation) return [];
    if (explanation.available_sources && explanation.available_sources.length > 0) {
      return explanation.available_sources;
    }
    if (explanation.modalities) {
      return Object.keys(explanation.modalities) as ('clinical' | 'wearable' | 'gut')[];
    }
    return [];
  }, [explanation]);

  // If the active filter is no longer available when switching diseases, reset to 'all'
  useEffect(() => {
    if (activeFilterTab !== 'all' && !availableSources.includes(activeFilterTab as any)) {
      setActiveFilterTab('all');
    }
  }, [activeDiseaseKey, availableSources, activeFilterTab]);

  if (!explanation) {
    return null;
  }

  const isHighestRisk = xai.default_disease === activeDiseaseKey;

  // Modality signals for the Provenance card (right-aligned pills)
  const clinSignal =
    explanation.modalities?.clinical?.risk_percentage ??
    explanation.provenance?.modality_scores?.clinical_risk_percentage ??
    null;

  const gutSignal =
    explanation.modalities?.gut?.risk_percentage ??
    explanation.provenance?.modality_scores?.gut_risk_percentage ??
    null;

  const wearSignal =
    explanation.modalities?.wearable?.risk_percentage ??
    explanation.provenance?.modality_scores?.wearable_risk_percentage ??
    null;

  // Compute active feature lists based on selected Signal Source Filter
  const activeRiskDrivers: FeatureContribution[] = React.useMemo(() => {
    if (activeFilterTab === 'all') {
      return explanation.risk_drivers || [];
    }
    if (explanation.modalities?.[activeFilterTab]?.risk_drivers) {
      return explanation.modalities[activeFilterTab]!.risk_drivers;
    }
    return (explanation.risk_drivers || []).filter((f) => f.source_modality === activeFilterTab);
  }, [explanation, activeFilterTab]);

  const activeProtectiveFactors: FeatureContribution[] = React.useMemo(() => {
    if (activeFilterTab === 'all') {
      return explanation.protective_factors || [];
    }
    if (explanation.modalities?.[activeFilterTab]?.protective_factors) {
      return explanation.modalities[activeFilterTab]!.protective_factors;
    }
    return (explanation.protective_factors || []).filter((f) => f.source_modality === activeFilterTab);
  }, [explanation, activeFilterTab]);

  const renderFeatureRow = (feature: FeatureContribution, type: 'risk' | 'protective', isFirst: boolean = false) => {
    const isRisk = type === 'risk';
    const barBg = isRisk ? 'bg-rose-500' : 'bg-emerald-500';
    const textColor = isRisk ? 'text-rose-700' : 'text-emerald-700';
    const isTarget = isFirst && isRisk && isGuidedDemo && guidedSubStep === 'contributing_features';

    // Modality-specific badge
    const getModalityBadge = () => {
      if (!feature.source_modality) return null;
      if (feature.source_modality === 'clinical') {
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-sky-50 text-sky-700 text-[10px] font-bold border border-sky-200">
            <Stethoscope className="w-3 h-3 text-sky-600" />
            <span>Clinical Model</span>
          </span>
        );
      }
      if (feature.source_modality === 'gut') {
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-teal-50 text-teal-700 text-[10px] font-bold border border-teal-200">
            <Microscope className="w-3 h-3 text-teal-600" />
            <span>Gut Model</span>
          </span>
        );
      }
      if (feature.source_modality === 'wearable') {
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 text-[10px] font-bold border border-purple-200">
            <Watch className="w-3 h-3 text-purple-600" />
            <span>Wearable Model</span>
          </span>
        );
      }
      return null;
    };

    return (
      <React.Fragment key={`${feature.source_modality || 'src'}-${feature.feature_key}`}>
        {isTarget && (
          <div className="pb-2">
            <GuidedCalloutCard
              badge="🎯 Contributing Health Signals"
              title={`Feature Signal: ${feature.display_name}`}
              description={
                <span>
                  This individual signal contributed to the model's assessment for <strong>{explanation.display_name}</strong>. Measured value: <strong className="text-amber-300 font-mono">{feature.formatted_value}</strong>{feature.normal_range ? ` (Ref: ${feature.normal_range})` : ''} with a relative influence of <strong className="text-amber-300 font-mono">{feature.relative_impact_percentage}%</strong>. <em>Note: features are associated with the model's prediction without making unsupported causal claims.</em>
                </span>
              }
              nextLabel="Next: Evidence by Source"
              onNext={() => onNextGuidedStep?.('evidence_sources')}
              pointerDirection="down"
            />
          </div>
        )}

        <div
          id={isTarget ? 'guided-contributing-feature-card' : undefined}
          className={`p-4 rounded-2xl bg-white border transition-all space-y-3 ${
            isTarget
              ? 'border-2 border-orange-400 ring-4 ring-orange-400/80 shadow-2xl shadow-orange-500/30 guided-blink-glow-card scale-[1.01]'
              : 'border-slate-200/80 shadow-xs hover:shadow-md'
          }`}
        >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-bold text-slate-900">
                {feature.display_name}
              </span>
              {feature.scientific_name && feature.scientific_name !== feature.display_name && (
                <span className="text-xs italic text-slate-500 hidden md:inline">
                  ({feature.scientific_name})
                </span>
              )}
              {getModalityBadge()}
            </div>
            {feature.role_description && (
              <p className="text-xs text-slate-500 leading-relaxed max-w-xl">
                {feature.role_description}
              </p>
            )}
          </div>

          {/* Value and Normal Range */}
          <div className="flex items-center space-x-2 self-start sm:self-auto shrink-0">
            <span className="font-mono text-sm font-extrabold text-slate-900 px-2.5 py-1 bg-slate-100 rounded-xl">
              {feature.formatted_value}
            </span>
            {feature.normal_range && (
              <span className="text-[11px] text-slate-500 border border-slate-200 px-2 py-1 rounded-xl">
                Ref: {feature.normal_range}
              </span>
            )}
          </div>
        </div>

        {/* Proportional Influence Bar */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-[11px]">
            <span className={`font-semibold ${textColor} flex items-center space-x-1`}>
              {isRisk ? (
                <>
                  <TrendingUp className="w-3 h-3 text-rose-500" />
                  <span>Pushed model risk higher</span>
                </>
              ) : (
                <>
                  <TrendingDown className="w-3 h-3 text-emerald-500" />
                  <span>Associated with lower model risk</span>
                </>
              )}
            </span>
            <span className="text-slate-400 font-mono text-[10px]">
              Relative influence: {feature.relative_impact_percentage}%
            </span>
          </div>

          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all duration-500 ${barBg}`}
              style={{ width: `${Math.min(100, Math.max(8, feature.relative_impact_percentage))}%` }}
            />
          </div>
        </div>
        </div>
      </React.Fragment>
    );
  };

  return (
    <div id="xai-explanation-section" className="space-y-6 animate-fade-in w-full pt-4">
      {/* Top Section Header & Disease Switching Navigation */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xl shadow-sky-500/5 space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-100 pb-5">
          <div className="space-y-1.5">
            <div className="flex items-center space-x-2">
              <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-sky-100 text-sky-900 text-xs font-bold">
                <Sparkles className="w-3.5 h-3.5 text-sky-600" />
                <span>Explainable AI (XAI) Transparency Layer</span>
              </div>
              {isHighestRisk && (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800 text-[11px] font-bold border border-rose-200">
                  <span>Highest Risk Focus</span>
                </span>
              )}
            </div>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Why is {explanation.display_name} showing this result?
            </h3>
            <p className="text-xs text-slate-500">
              Understanding the key laboratory markers, microbiome features, sensor metrics, and AI model reasoning behind your assessment.
            </p>
          </div>

          {/* Disease Selector Navigation Tabs */}
          <div className="relative">
            {isGuidedDemo && guidedSubStep === 'disease_tabs' && (
              <div className="mb-3">
                <GuidedCalloutCard
                  badge="🎯 Multiple Metabolic Outcomes"
                  title="Cross-Condition Assessment"
                  description={
                    <span>
                      <strong>!Health Prism</strong> evaluates multiple metabolic disease and risk outcomes ({DISEASE_KEYS.map((k) => DISEASE_LABELS[k]).join(', ')}) using the available health evidence across modalities.
                    </span>
                  }
                  nextLabel="Next: Multimodal Evidence"
                  onNext={() => onNextGuidedStep?.('multimodal_signals')}
                  pointerDirection="down"
                />
              </div>
            )}
            <div
              id="guided-disease-category-tabs"
              className={`flex flex-wrap items-center gap-1.5 p-1.5 rounded-2xl shrink-0 transition-all ${
                isGuidedDemo && guidedSubStep === 'disease_tabs'
                  ? 'bg-amber-50 border-2 border-orange-400 ring-4 ring-orange-400/70 guided-blink-glow-card shadow-lg shadow-orange-500/20'
                  : 'bg-slate-100/80'
              }`}
            >
              {DISEASE_KEYS.map((key) => {
                const isSelected = key === activeDiseaseKey;
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => {
                      onSelectDisease(key);
                      setActiveFilterTab('all');
                    }}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-white text-sky-800 shadow-xs border border-slate-200/80 font-extrabold'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
                    }`}
                  >
                    {DISEASE_LABELS[key]}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Guided Demo Step 4D Callout: Multimodal Signal Summary */}
        {isGuidedDemo && guidedSubStep === 'multimodal_signals' && (
          <GuidedCalloutCard
            badge="🎯 Multimodal Evidence"
            title="Evidence by Data Modality"
            description={
              <span>
                These indicators summarize the model's evidence and risk contribution associated with the available health-data sources ({clinSignal !== null ? `Clinical Lab: ${formatRiskPercentage(clinSignal)}` : ''}{gutSignal !== null ? ` • Gut Microbiome: ${formatRiskPercentage(gutSignal)}` : ''}{wearSignal !== null ? ` • Wearable/CGM: ${formatRiskPercentage(wearSignal)}` : ''}) for <strong>{explanation.display_name}</strong>.
              </span>
            }
            nextLabel="Next: Contributing Signals"
            onNext={() => onNextGuidedStep?.('contributing_features')}
            pointerDirection="down"
          />
        )}

        {/* Assessment Provenance & Signal Cards */}
        <div className="p-5 rounded-2xl bg-gradient-to-r from-sky-50/80 via-slate-50 to-indigo-50/40 border border-sky-200/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start space-x-3 text-xs">
            <Layers className="w-5 h-5 text-sky-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-slate-900 text-sm">Assessment Provenance</span>
              </div>
              <p className="text-slate-600 leading-relaxed max-w-2xl text-xs">
                {explanation.provenance.description ||
                  'This assessment combines your diagnostic health markers, physiological data, and intelligent predictive models.'}
              </p>
            </div>
          </div>

          {/* Modality Signal Pills on the Right */}
          <div id="guided-multimodal-signals" className="flex flex-wrap items-center gap-2 shrink-0 self-start md:self-auto">
            {clinSignal !== null && clinSignal !== undefined && (
              <div className={`px-3.5 py-1.5 rounded-xl border text-center shadow-xs transition-all ${
                isGuidedDemo && guidedSubStep === 'multimodal_signals'
                  ? 'bg-amber-50 border-2 border-orange-500 ring-4 ring-orange-400/80 guided-blink-glow-box scale-105'
                  : 'bg-white border-sky-200'
              }`}>
                <span className="block text-[10px] uppercase font-bold text-slate-400">Clinical Signal</span>
                <span className="text-xs font-mono font-extrabold text-slate-800">
                  {formatRiskPercentage(clinSignal)}
                </span>
              </div>
            )}
            {gutSignal !== null && gutSignal !== undefined && (
              <div className={`px-3.5 py-1.5 rounded-xl border text-center shadow-xs transition-all ${
                isGuidedDemo && guidedSubStep === 'multimodal_signals'
                  ? 'bg-amber-50 border-2 border-orange-500 ring-4 ring-orange-400/80 guided-blink-glow-box scale-105'
                  : 'bg-white border-teal-200'
              }`}>
                <span className="block text-[10px] uppercase font-bold text-slate-400">Gut Signal</span>
                <span className="text-xs font-mono font-extrabold text-slate-800">
                  {formatRiskPercentage(gutSignal)}
                </span>
              </div>
            )}
            {wearSignal !== null && wearSignal !== undefined && (
              <div className={`px-3.5 py-1.5 rounded-xl border text-center shadow-xs transition-all ${
                isGuidedDemo && guidedSubStep === 'multimodal_signals'
                  ? 'bg-amber-50 border-2 border-orange-500 ring-4 ring-orange-400/80 guided-blink-glow-box scale-105'
                  : 'bg-white border-purple-200'
              }`}>
                <span className="block text-[10px] uppercase font-bold text-slate-400">Wearable Signal</span>
                <span className="text-xs font-mono font-extrabold text-slate-800">
                  {formatRiskPercentage(wearSignal)}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Suppressed Condition Notice */}
        {explanation.is_suppressed && (
          <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-900 flex items-start space-x-3">
            <ShieldCheck className="w-5 h-5 text-slate-500 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold text-sm block">Secondary Indicator Superseded</span>
              <p className="text-slate-600">
                {explanation.provenance.description || 'Type 2 Diabetes criteria met; secondary prediabetes indicator suppressed.'}
              </p>
            </div>
          </div>
        )}

        {/* Insufficient Evidence Notice */}
        {!explanation.available && !explanation.is_suppressed && (
          <div className="p-6 rounded-2xl bg-amber-50/80 border border-amber-200 text-xs text-amber-950 flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold text-sm block">Detailed Explanation Not Available</span>
              <p className="text-slate-600">
                {explanation.provenance.description}
              </p>
            </div>
          </div>
        )}

        {/* Available Explanation Breakdown */}
        {explanation.available && (
          <div className="space-y-8">
            {/* Guided Demo Step 4F Callout: Evidence by Source */}
            {isGuidedDemo && guidedSubStep === 'evidence_sources' && (
              <GuidedCalloutCard
                badge="🎯 Evidence by Source"
                title="Filter Signals by Modality"
                description="The evidence can be filtered and inspected across the available health-data sources, including clinical laboratory markers, continuous wearable/CGM metrics, and gut microbiome taxa. Explore the filters or continue to review the assessment."
                nextLabel="Next: Review Assessment"
                onNext={() => onNextGuidedStep?.('review_assessment')}
                pointerDirection="down"
              />
            )}

            {/* Dynamic Signal Source Filter Bar */}
            <div
              id="guided-signal-source-filter"
              className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3 rounded-2xl p-2 transition-all ${
                isGuidedDemo && guidedSubStep === 'evidence_sources'
                  ? 'bg-amber-50/70 border-2 border-orange-400 ring-4 ring-orange-400/70 guided-blink-glow-card shadow-lg shadow-orange-500/20'
                  : ''
              }`}
            >
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Signal Source Filter
              </span>
              <div className="inline-flex flex-wrap rounded-xl bg-slate-100 p-1 text-xs gap-1">
                <button
                  type="button"
                  onClick={() => setActiveFilterTab('all')}
                  className={`px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
                    activeFilterTab === 'all'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  All Signals
                </button>

                {availableSources.includes('clinical') && (
                  <button
                    type="button"
                    onClick={() => setActiveFilterTab('clinical')}
                    className={`px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
                      activeFilterTab === 'clinical'
                        ? 'bg-white text-slate-900 shadow-xs'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    Clinical Lab Markers
                  </button>
                )}

                {availableSources.includes('wearable') && (
                  <button
                    type="button"
                    onClick={() => setActiveFilterTab('wearable')}
                    className={`px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
                      activeFilterTab === 'wearable'
                        ? 'bg-white text-slate-900 shadow-xs'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    Wearable & CGM Signals
                  </button>
                )}

                {availableSources.includes('gut') && (
                  <button
                    type="button"
                    onClick={() => setActiveFilterTab('gut')}
                    className={`px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
                      activeFilterTab === 'gut'
                        ? 'bg-white text-slate-900 shadow-xs'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    Gut Microbiome Taxa
                  </button>
                )}
              </div>
            </div>

            {/* Factors Increasing Risk */}
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-rose-600" />
                <h4 className="text-lg font-extrabold text-slate-900 tracking-tight">
                  Factors That Pushed Model Risk Higher
                </h4>
                <span className="text-xs text-slate-400 font-medium">
                  ({activeRiskDrivers.length} key driver{activeRiskDrivers.length === 1 ? '' : 's'})
                </span>
              </div>

              {activeRiskDrivers.length > 0 ? (
                <div className="grid grid-cols-1 gap-3">
                  {activeRiskDrivers.map((feat, idx) => renderFeatureRow(feat, 'risk', idx === 0))}
                </div>
              ) : (
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-500 italic">
                  No significant elevated risk factors detected for this model.
                </div>
              )}
            </div>

            {/* Factors Helping Reduce Risk / Protective Factors */}
            <div className="space-y-4 pt-2">
              <div className="flex items-center space-x-2">
                <TrendingDown className="w-5 h-5 text-emerald-600" />
                <h4 className="text-lg font-extrabold text-slate-900 tracking-tight">
                  Factors Helping Lower or Balance Risk
                </h4>
                <span className="text-xs text-slate-400 font-medium">
                  ({activeProtectiveFactors.length} protective factor{activeProtectiveFactors.length === 1 ? '' : 's'})
                </span>
              </div>

              {activeProtectiveFactors.length > 0 ? (
                <div className="grid grid-cols-1 gap-3">
                  {activeProtectiveFactors.map((feat) => renderFeatureRow(feat, 'protective', false))}
                </div>
              ) : (
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-500 italic">
                  No prominent protective factors were identified within this patient data vector.
                </div>
              )}
            </div>

            {/* Guided Demo Step 4G Callout: Review the Full Assessment */}
            {isGuidedDemo && guidedSubStep === 'review_assessment' && (
              <div className="pt-4">
                <GuidedCalloutCard
                  badge="🎯 Review the Assessment"
                  title="Consolidated Multimodal Assessment"
                  description="Review the risk indicators, multimodal signal contributions, and supporting evidence above. This is the consolidated view produced from your integrated clinical, wearable, gut microbiome, and user-reported information."
                  nextLabel="Continue to Personalized Plan"
                  onNext={() => onNextGuidedStep?.('plan_button')}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
