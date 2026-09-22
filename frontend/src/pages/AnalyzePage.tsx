import React, { useState } from 'react';
import { FileUpload } from '../components/FileUpload';
import { ProcessingLoader } from '../components/ProcessingLoader';
import { DocumentInfoCard } from '../components/DocumentInfoCard';
import { ReportInfoCard } from '../components/ReportInfoCard';
import { ExtractedContentViewer } from '../components/ExtractedContentViewer';
import { MappedFeaturesDashboard } from '../components/MappedFeaturesDashboard';
import { TechnicalDetails } from '../components/TechnicalDetails';
import { HealthAssessmentResults } from '../components/HealthAssessmentResults';
import { PersonalizedHealthPlanPage } from '../components/PersonalizedHealthPlanPage';
import { PersonalizedProgressPlanPage } from '../components/PersonalizedProgressPlanPage';
import { NotEnoughDataGuidance } from '../components/NotEnoughDataGuidance';
import { DeploymentWaitNotice } from '../components/DeploymentWaitNotice';
import type { CategoryGuidanceInfo } from '../components/NotEnoughDataGuidance';
import { analyzeDocuments, runHealthAssessment } from '../services/api';
import type { DocumentAnalysisResult, HealthAssessmentResponse } from '../types/reader';
import { RefreshCw, Sparkles, AlertCircle, Layers, FileText, CheckCircle2, Brain, ArrowRight, ArrowLeft } from 'lucide-react';

export type Stage3SubStep = 'quality' | 'extraction' | 'modalities' | 'family_history' | 'features' | 'assessment';
export type Stage4SubStep =
  | 'prediction'
  | 'why_result'
  | 'disease_tabs'
  | 'multimodal_signals'
  | 'contributing_features'
  | 'evidence_sources'
  | 'review_assessment'
  | 'plan_button';
export type Stage5SubStep =
  | 'plan_summary'
  | 'recommendations'
  | 'progress_plan'
  | 'select_plan';
export type ProgressPlanSubStep =
  | 'plan_header'
  | 'duration'
  | 'overall_progress'
  | 'daily_checklist'
  | 'daily_tasks'
  | 'download_pdf'
  | 'workflow_summary'
  | 'completion_screen';

interface AnalyzePageProps {
  isGuidedDemo?: boolean;
  guidedDemoStep?: number;
  onExitGuidedDemo?: () => void;
  onGuidedDemoAdvance?: () => void;
}

export const AnalyzePage: React.FC<AnalyzePageProps> = ({
  isGuidedDemo = false,
  guidedDemoStep = 2,
  onExitGuidedDemo,
  onGuidedDemoAdvance,
}) => {
  const [state, setState] = useState<'upload' | 'processing' | 'review' | 'analyzing' | 'assessment' | 'health-plan' | 'progress-plan'>('upload');
  const [progressPlanDuration, setProgressPlanDuration] = useState<'1_week' | '1_month' | '3_months'>('1_week');
  const [results, setResults] = useState<DocumentAnalysisResult[]>([]);
  const [activeDocIndex, setActiveDocIndex] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Guided Demo Stage 3 Sub-step tracking
  const [stage3SubStep, setStage3SubStep] = useState<Stage3SubStep>('quality');
  // Guided Demo Stage 4 Sub-step tracking
  const [stage4SubStep, setStage4SubStep] = useState<Stage4SubStep>('prediction');
  // Guided Demo Stage 5 Sub-step tracking
  const [stage5SubStep, setStage5SubStep] = useState<Stage5SubStep>('plan_summary');
  // Guided Demo Progress Plan Sub-step tracking
  const [progressPlanSubStep, setProgressPlanSubStep] = useState<ProgressPlanSubStep>('plan_header');

  // Notify guided demo when documents reach review state
  React.useEffect(() => {
    if (isGuidedDemo && state === 'review') {
      onGuidedDemoAdvance?.();
    }
  }, [isGuidedDemo, state, onGuidedDemoAdvance]);

  const handleStage3Advance = (nextStep?: Stage3SubStep) => {
    let target: Stage3SubStep = 'quality';
    if (nextStep) {
      target = nextStep;
    } else {
      if (stage3SubStep === 'quality') target = 'extraction';
      else if (stage3SubStep === 'extraction') target = 'modalities';
      else if (stage3SubStep === 'modalities') target = 'family_history';
      else if (stage3SubStep === 'family_history') target = 'features';
      else if (stage3SubStep === 'features') target = 'assessment';
      else target = 'assessment';
    }
    setStage3SubStep(target);

    // Smooth scroll to target
    setTimeout(() => {
      let targetId = '';
      if (target === 'quality') targetId = 'guided-report-quality';
      else if (target === 'extraction') targetId = 'guided-extracted-content';
      else if (target === 'modalities') targetId = 'guided-mapped-dashboard';
      else if (target === 'family_history') targetId = 'guided-family-history';
      else if (target === 'features') targetId = 'guided-feature-tables';
      else if (target === 'assessment') targetId = 'guided-assessment-cta';

      if (targetId) {
        const el = document.getElementById(targetId);
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    }, 120);
  };

  const handleStage4Advance = (nextStep?: Stage4SubStep) => {
    const order: Stage4SubStep[] = [
      'prediction',
      'why_result',
      'disease_tabs',
      'multimodal_signals',
      'contributing_features',
      'evidence_sources',
      'review_assessment',
      'plan_button',
    ];
    let target: Stage4SubStep = 'prediction';
    if (nextStep) {
      target = nextStep;
    } else {
      const idx = order.indexOf(stage4SubStep);
      target = idx < order.length - 1 ? order[idx + 1] : 'plan_button';
    }
    setStage4SubStep(target);

    // Smooth scroll to target
    setTimeout(() => {
      let targetId = '';
      if (target === 'prediction') targetId = 'guided-prediction-card';
      else if (target === 'why_result') targetId = 'guided-why-this-result-btn';
      else if (target === 'disease_tabs') targetId = 'guided-disease-category-tabs';
      else if (target === 'multimodal_signals') targetId = 'guided-multimodal-signals';
      else if (target === 'contributing_features') targetId = 'guided-contributing-feature-card';
      else if (target === 'evidence_sources') targetId = 'guided-signal-source-filter';
      else if (target === 'review_assessment') targetId = 'xai-explanation-section';
      else if (target === 'plan_button') targetId = 'guided-personalized-plan-btn';

      if (targetId) {
        const el = document.getElementById(targetId);
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    }, 120);
  };

  const handleStage5Advance = (nextStep?: Stage5SubStep) => {
    const order: Stage5SubStep[] = [
      'plan_summary',
      'recommendations',
      'progress_plan',
      'select_plan',
    ];
    let target: Stage5SubStep = 'plan_summary';
    if (nextStep) {
      target = nextStep;
    } else {
      const idx = order.indexOf(stage5SubStep);
      target = idx < order.length - 1 ? order[idx + 1] : 'select_plan';
    }
    setStage5SubStep(target);

    // Smooth scroll to target
    setTimeout(() => {
      let targetId = '';
      if (target === 'plan_summary') targetId = 'guided-plan-header';
      else if (target === 'recommendations') targetId = 'guided-actionable-recommendations';
      else if (target === 'progress_plan') targetId = 'guided-progress-plan-section';
      else if (target === 'select_plan') targetId = 'guided-progress-plan-buttons';

      if (targetId) {
        const el = document.getElementById(targetId);
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    }, 120);
  };

  const handleProgressPlanAdvance = (nextStep?: ProgressPlanSubStep) => {
    const order: ProgressPlanSubStep[] = [
      'plan_header',
      'duration',
      'overall_progress',
      'daily_checklist',
      'daily_tasks',
      'download_pdf',
      'workflow_summary',
      'completion_screen',
    ];
    let target: ProgressPlanSubStep = 'plan_header';
    if (nextStep) {
      target = nextStep;
    } else {
      const idx = order.indexOf(progressPlanSubStep);
      target = idx < order.length - 1 ? order[idx + 1] : 'completion_screen';
    }
    setProgressPlanSubStep(target);

    // Smooth scroll to target
    setTimeout(() => {
      let targetId = '';
      if (target === 'plan_header') targetId = 'guided-progress-header';
      else if (target === 'duration') targetId = 'guided-duration-selector';
      else if (target === 'overall_progress') targetId = 'guided-overall-progress';
      else if (target === 'daily_checklist') targetId = 'guided-day-selector-strip';
      else if (target === 'daily_tasks') targetId = 'guided-task-checklist';
      else if (target === 'download_pdf') targetId = 'guided-download-pdf-btn';
      else if (target === 'workflow_summary') targetId = 'guided-progress-header';
      else if (target === 'completion_screen') {
        window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
        return;
      }

      if (targetId) {
        const el = document.getElementById(targetId);
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    }, 120);
  };

  // User answered values from questionnaire wizard
  const [userAddedValues, setUserAddedValues] = useState<Record<string, any>>({});

  // Assessment results from Fusion V2
  const [assessmentResult, setAssessmentResult] = useState<HealthAssessmentResponse | null>(null);

  // Track queue trigger for MappedFeaturesDashboard
  const [triggerCategoryQueue, setTriggerCategoryQueue] = useState<'clinical' | 'wearable' | 'gut' | 'family' | null>(null);

  const handleFilesSelected = async (files: File[]) => {
    setState('processing');
    setErrorMsg(null);
    setUserAddedValues({});
    setAssessmentResult(null);

    try {
      // Call backend REST API endpoint with all selected files for this session
      const resList = await analyzeDocuments(files);
      setResults(resList);
      setActiveDocIndex(0);
      setState('review');
    } catch (err: any) {
      console.error('Extraction error:', err);
      setErrorMsg(err.message || 'Failed to process document(s). Make sure backend server is running.');
      setState('upload');
    }
  };

  const handleRunAssessment = async () => {
    const activeResult = results[activeDocIndex] || results[0];
    if (!activeResult || !activeResult.mapper_output) {
      setErrorMsg('No structured clinical data available for assessment.');
      return;
    }

    setState('analyzing');
    setErrorMsg(null);

    try {
      const patientId =
        activeResult.mapper_output?.patient_info?.patient_id ||
        activeResult.document_id ||
        'P001001';

      const assessment = await runHealthAssessment({
        contract2: activeResult.mapper_output,
        user_answers: userAddedValues,
        patient_id: patientId,
      });

      setAssessmentResult(assessment);
      setState('assessment');
      window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
    } catch (err: any) {
      console.error('Assessment error:', err);
      setErrorMsg(err.message || 'Failed to generate health assessment. Please try again.');
      setState('review');
    }
  };

  const handleReset = () => {
    setState('upload');
    setResults([]);
    setActiveDocIndex(0);
    setUserAddedValues({});
    setAssessmentResult(null);
    setTriggerCategoryQueue(null);
    setErrorMsg(null);
  };

  const activeResult = results[activeDocIndex] || results[0];
  const mapperOutput = activeResult?.mapper_output;

  // Schema-synchronized required fields
  const clinicalRequiredFields = [
    'Age', 'Gender', 'Height', 'Weight', 'BMI', 'Waist_Circumference',
    'Systolic_BP', 'Diastolic_BP', 'Fasting_Blood_Glucose', 'HbA1c',
    'Triglycerides', 'HDL', 'LDL', 'ALT', 'AST',
    'Family_History_Diabetes', 'Family_History_Hypertension', 'Family_History_CVD'
  ];

  const wearableRequiredFields = [
    'Average_Daily_Steps', 'Active_Minutes', 'Sedentary_Time_Minutes',
    'Resting_Heart_Rate', 'Heart_Rate_Variability_RMSSD', 'Sleep_Duration_Hours',
    'Sleep_Efficiency_Score', 'Autonomic_Stress_Score', 'Activity_Energy_Expenditure',
    'Exercise_Frequency_Days', 'CGM_Average_Glucose', 'CGM_Glucose_CV',
    'CGM_Time_In_Range', 'CGM_Time_Above_Range', 'CGM_Time_Below_Range'
  ];

  const gutRequiredFields = [
    'Akkermansia', 'Faecalibacterium', 'Roseburia', 'Bifidobacterium',
    'Bacteroides', 'Prevotella', 'Ruminococcus', 'Blautia',
    'Collinsella', 'Escherichia_Shigella', 'Coprococcus', 'Alistipes',
    'Subdoligranulum', 'Enterococcus', 'Eubacterium', 'Parabacteroides',
    'Lactobacillus', 'Klebsiella', 'Streptococcus', 'Eggerthella', 'Other_Taxa'
  ];

  // Derive real field counts dynamically from schema and Contract 2 state
  const computeDomainInfo = (
    domainKey: 'clinical' | 'wearable' | 'gut',
    title: string,
    allFields: string[]
  ): CategoryGuidanceInfo => {
    const domainData = mapperOutput?.[domainKey];
    let missingList: string[] = [];

    if (!domainData || domainData.status === 'not_available') {
      missingList = allFields.filter((f) => userAddedValues[f] === undefined);
    } else {
      const rawMissing: string[] = domainData.missing_fields || [];
      missingList = rawMissing.filter((f) => userAddedValues[f] === undefined);
    }

    const missingCount = missingList.length;
    const totalRequired = allFields.length;
    const foundCount = Math.max(0, totalRequired - missingCount);

    return {
      id: domainKey,
      title,
      iconType: domainKey,
      totalRequired,
      foundCount,
      missingCount,
      missingFields: missingList,
      isClosest: false,
    };
  };

  const clinicalInfo = computeDomainInfo('clinical', 'Clinical Health', clinicalRequiredFields);
  const wearableInfo = computeDomainInfo('wearable', 'Wearable & Device Data', wearableRequiredFields);
  const gutInfo = computeDomainInfo('gut', 'Gut Microbiome', gutRequiredFields);

  const categories = [clinicalInfo, wearableInfo, gutInfo];

  // Check if at least ONE category is complete (0 missing fields)
  const isAnyCategoryComplete = categories.some((c) => c.missingCount === 0);

  // Identify closest category when nothing is complete
  let closestCategory: CategoryGuidanceInfo | null = null;
  if (!isAnyCategoryComplete) {
    const sorted = [...categories].sort((a, b) => a.missingCount - b.missingCount);
    closestCategory = sorted[0];
    categories.forEach((c) => {
      c.isClosest = c.id === closestCategory?.id;
    });
  }

  const handleProvideMissing = (categoryId: 'clinical' | 'wearable' | 'gut') => {
    if (categoryId === 'clinical') {
      const missing = clinicalInfo.missingFields;
      const isOnlyFamily = missing.length > 0 && missing.every((f) => f.startsWith('Family_History_'));
      setTriggerCategoryQueue(isOnlyFamily ? 'family' : 'clinical');
    } else {
      setTriggerCategoryQueue(categoryId);
    }
  };

  // Scroll to top on mount / demo change
  React.useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }, [isGuidedDemo]);

  return (
    <div className="space-y-4 py-2">
      
      {/* ── Guided Demo Top Bar (Shown ONLY in Guided Demo mode) ── */}
      {isGuidedDemo && progressPlanSubStep !== 'completion_screen' && (
        <div className="space-y-2 py-1 px-1 guided-fade-in border-b border-slate-200/80 pb-2.5">
          <div className="flex items-center justify-between">
            {/* Left: Exit */}
            <button
              type="button"
              onClick={onExitGuidedDemo}
              className="group flex items-center space-x-2 text-sm text-slate-500 hover:text-orange-600 transition-colors font-semibold cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
              <span>Exit Demo</span>
            </button>

            {/* Center: Colorful progress pill */}
            <div className="flex items-center space-x-2 px-4 py-1.5 rounded-full bg-gradient-to-r from-sky-600 to-cyan-600 text-white text-xs font-bold shadow-md shadow-sky-600/20">
              <Sparkles className="w-3.5 h-3.5" />
              <span>
                {state === 'progress-plan'
                  ? 'Guided Demo • Final Stage: Personalized Progress Plan'
                  : state === 'health-plan'
                  ? 'Guided Demo • Step 05 of 5: Personalized Health Plan & Actions'
                  : state === 'assessment'
                  ? 'Guided Demo • Step 04 of 5: Predictions & Multimodal Evidence'
                  : state === 'review' || guidedDemoStep >= 3
                  ? 'Guided Demo • Step 03 of 5: Feature Mapping & Verification'
                  : 'Guided Demo • Step 02: Load & Process Report'}
              </span>
            </div>

            {/* Right: Step badge */}
            <span className="text-xs font-bold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full border border-slate-200">
              {state === 'progress-plan'
                ? 'Final Stage'
                : state === 'health-plan'
                ? 'Step 5 of 5'
                : state === 'assessment'
                ? 'Step 4 of 5'
                : state === 'review' || guidedDemoStep >= 3
                ? 'Step 3 of 5'
                : 'Step 2 of 5'}
            </span>
          </div>

          {/* Sub-stepper pills for Stage 3 */}
          {state === 'review' && (
            <div className="flex items-center justify-center space-x-1.5 overflow-x-auto py-1 text-[11px] font-bold">
              {[
                { id: 'quality', label: 'Quality' },
                { id: 'extraction', label: 'Extraction' },
                { id: 'modalities', label: 'Modalities' },
                { id: 'family_history', label: 'Family History' },
                { id: 'features', label: 'Features' },
                { id: 'assessment', label: 'Assessment' },
              ].map((sub, idx, arr) => {
                const subStepOrder: Stage3SubStep[] = ['quality', 'extraction', 'modalities', 'family_history', 'features', 'assessment'];
                const isCurrent = stage3SubStep === sub.id;
                const isPast = subStepOrder.indexOf(stage3SubStep) > idx;

                return (
                  <React.Fragment key={sub.id}>
                    <button
                      type="button"
                      onClick={() => handleStage3Advance(sub.id as Stage3SubStep)}
                      className={`flex items-center space-x-1 px-2.5 py-0.5 rounded-lg transition-all cursor-pointer ${
                        isCurrent
                          ? 'bg-amber-500 text-white font-extrabold shadow-sm ring-2 ring-amber-300'
                          : isPast
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'text-slate-400 hover:text-slate-700 bg-slate-100'
                      }`}
                    >
                      <span>{sub.label}</span>
                    </button>
                    {idx < arr.length - 1 && (
                      <span className="text-slate-300 font-normal">→</span>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          )}

          {/* Sub-stepper pills for Stage 4 */}
          {state === 'assessment' && (
            <div className="flex items-center justify-center space-x-1.5 overflow-x-auto py-1 text-[11px] font-bold">
              {[
                { id: 'prediction', label: 'Prediction' },
                { id: 'why_result', label: 'Why Result' },
                { id: 'disease_tabs', label: 'Categories' },
                { id: 'multimodal_signals', label: 'Modality Signals' },
                { id: 'contributing_features', label: 'Features' },
                { id: 'evidence_sources', label: 'Sources' },
                { id: 'review_assessment', label: 'Review' },
                { id: 'plan_button', label: 'Plan' },
              ].map((sub, idx, arr) => {
                const subStepOrder: Stage4SubStep[] = [
                  'prediction',
                  'why_result',
                  'disease_tabs',
                  'multimodal_signals',
                  'contributing_features',
                  'evidence_sources',
                  'review_assessment',
                  'plan_button',
                ];
                const isCurrent = stage4SubStep === sub.id;
                const isPast = subStepOrder.indexOf(stage4SubStep) > idx;

                return (
                  <React.Fragment key={sub.id}>
                    <button
                      type="button"
                      onClick={() => handleStage4Advance(sub.id as Stage4SubStep)}
                      className={`flex items-center space-x-1 px-2.5 py-0.5 rounded-lg transition-all cursor-pointer ${
                        isCurrent
                          ? 'bg-amber-500 text-white font-extrabold shadow-sm ring-2 ring-amber-300'
                          : isPast
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'text-slate-400 hover:text-slate-700 bg-slate-100'
                      }`}
                    >
                      <span>{sub.label}</span>
                    </button>
                    {idx < arr.length - 1 && (
                      <span className="text-slate-300 font-normal">→</span>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          )}

          {/* Sub-stepper pills for Stage 5 */}
          {state === 'health-plan' && (
            <div className="flex items-center justify-center space-x-1.5 overflow-x-auto py-1 text-[11px] font-bold">
              {[
                { id: 'plan_summary', label: 'Plan Summary' },
                { id: 'recommendations', label: 'Recommendations' },
                { id: 'progress_plan', label: 'Progress Plan' },
                { id: 'select_plan', label: 'Choose Duration' },
              ].map((sub, idx, arr) => {
                const subStepOrder: Stage5SubStep[] = [
                  'plan_summary',
                  'recommendations',
                  'progress_plan',
                  'select_plan',
                ];
                const isCurrent = stage5SubStep === sub.id;
                const isPast = subStepOrder.indexOf(stage5SubStep) > idx;

                return (
                  <React.Fragment key={sub.id}>
                    <button
                      type="button"
                      onClick={() => handleStage5Advance(sub.id as Stage5SubStep)}
                      className={`flex items-center space-x-1 px-2.5 py-0.5 rounded-lg transition-all cursor-pointer ${
                        isCurrent
                          ? 'bg-amber-500 text-white font-extrabold shadow-sm ring-2 ring-amber-300'
                          : isPast
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'text-slate-400 hover:text-slate-700 bg-slate-100'
                      }`}
                    >
                      <span>{sub.label}</span>
                    </button>
                    {idx < arr.length - 1 && (
                      <span className="text-slate-300 font-normal">→</span>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          )}

          {/* Sub-stepper pills for Progress Plan */}
          {state === 'progress-plan' && (
            <div className="flex items-center justify-center space-x-1.5 overflow-x-auto py-1 text-[11px] font-bold">
              {[
                { id: 'plan_header', label: 'Plan Overview' },
                { id: 'duration', label: 'Duration' },
                { id: 'overall_progress', label: 'Progress' },
                { id: 'daily_checklist', label: 'Daily Routine' },
                { id: 'daily_tasks', label: 'Actions' },
                { id: 'download_pdf', label: 'Plan PDF' },
                { id: 'workflow_summary', label: 'Summary' },
              ].map((sub, idx, arr) => {
                const subStepOrder: ProgressPlanSubStep[] = [
                  'plan_header',
                  'duration',
                  'overall_progress',
                  'daily_checklist',
                  'daily_tasks',
                  'download_pdf',
                  'workflow_summary',
                  'completion_screen',
                ];
                const isCurrent = progressPlanSubStep === sub.id;
                const isPast = subStepOrder.indexOf(progressPlanSubStep) > idx;

                return (
                  <React.Fragment key={sub.id}>
                    <button
                      type="button"
                      onClick={() => handleProgressPlanAdvance(sub.id as ProgressPlanSubStep)}
                      className={`flex items-center space-x-1 px-2.5 py-0.5 rounded-lg transition-all cursor-pointer ${
                        isCurrent
                          ? 'bg-amber-500 text-white font-extrabold shadow-sm ring-2 ring-amber-300'
                          : isPast
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'text-slate-400 hover:text-slate-700 bg-slate-100'
                      }`}
                    >
                      <span>{sub.label}</span>
                    </button>
                    {idx < arr.length - 1 && (
                      <span className="text-slate-300 font-normal">→</span>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ── Page Header Row (Compact & Wide) ── */}
      {state !== 'assessment' && state !== 'health-plan' && state !== 'progress-plan' && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200/80 pb-2.5">
          <div>
            <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-sky-100 text-sky-800 text-[11px] font-bold mb-1">
              <Sparkles className="w-3 h-3 text-sky-600" />
              <span>Intelligent Document Analysis &amp; Clinical Fusion</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Analyze Medical Reports
            </h2>
          </div>
          <p className="text-xs text-slate-500 max-w-md sm:text-right">
            Upload multimodal records or load the demo report to evaluate metabolic health.
          </p>
        </div>
      )}

      {/* Error Alert */}
      {errorMsg && (
        <div className="max-w-2xl mx-auto p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-3 text-rose-800 text-sm animate-fade-in">
          <AlertCircle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-bold block">Processing Failure</span>
            <span>{errorMsg}</span>
          </div>
        </div>
      )}

      {/* State 1: Upload */}
      {state === 'upload' && (
        <div className="py-2">
          <FileUpload
            onFilesSelected={handleFilesSelected}
            isGuidedDemo={isGuidedDemo}
          />
        </div>
      )}

      {/* State 2: Processing Documents */}
      {state === 'processing' && <ProcessingLoader />}

      {/* State 3: Analyzing with ModelRouter & Fusion V2 */}
      {state === 'analyzing' && (
        <div className="py-12 flex flex-col items-center justify-center space-y-5 animate-fade-in text-center max-w-xl mx-auto">
          <div className="w-16 h-16 rounded-3xl bg-sky-100 text-sky-600 flex items-center justify-center shadow-lg shadow-sky-600/10">
            <Brain className="w-8 h-8 animate-pulse" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-slate-900">Synthesizing Health Assessment</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Evaluating available biomarkers and clinical parameters...
            </p>
          </div>

          {/* Deployment / Cold-Start Informational Notice */}
          <DeploymentWaitNotice
            title="Assessment may take a little longer on the first run"
            message="Because !Health Prism is running on a free-tier deployment, the analysis service may need a moment to wake up. Please wait while we complete your health assessment."
            subtext="Thank you for your patience."
          />
        </div>
      )}

      {/* State 4: Review Extracted Information */}
      {state === 'review' && results.length > 0 && activeResult && (
        <div className="space-y-8 w-full max-w-[1500px] mx-auto animate-fade-in">
          
          {/* Batch Summary Header */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center font-bold">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-base font-bold text-slate-900">
                    Session Results ({results.length} {results.length === 1 ? 'Document' : 'Documents'})
                  </span>
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold flex items-center space-x-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    <span>Processed</span>
                  </span>
                </div>
                <span className="text-xs text-slate-500">
                  Review extracted information below. You can provide missing data if known, or proceed directly.
                </span>
              </div>
            </div>

            <button
              onClick={handleReset}
              className="flex items-center space-x-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Analyze Another Batch</span>
            </button>
          </div>

          {/* Document Tab Switcher (if >1 document) */}
          {results.length > 1 && (
            <div className="flex items-center space-x-2 overflow-x-auto p-1.5 bg-slate-200/60 rounded-2xl border border-slate-200">
              {results.map((res, idx) => (
                <button
                  key={res.document_id || idx}
                  onClick={() => setActiveDocIndex(idx)}
                  className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                    activeDocIndex === idx
                      ? 'bg-white text-sky-700 shadow-sm border border-slate-200/80'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                  }`}
                >
                  <FileText className={`w-4 h-4 ${activeDocIndex === idx ? 'text-sky-600' : 'text-slate-400'}`} />
                  <span className="truncate max-w-xs">{res.source_file}</span>
                  {res.status === 'EXACT_DUPLICATE' && (
                    <span className="px-1.5 py-0.5 text-[10px] bg-amber-100 text-amber-800 rounded-md uppercase font-semibold">
                      Duplicate
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}

          {/* Cards Grid: Document Info & Report Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <DocumentInfoCard data={activeResult} />
            <ReportInfoCard
              data={activeResult}
              isGuidedDemo={isGuidedDemo && state === 'review' && stage3SubStep === 'quality'}
              onNextGuidedStep={() => handleStage3Advance('extraction')}
            />
          </div>

          {/* Extracted Text Content Card */}
          <ExtractedContentViewer
            pages={activeResult.pages}
            isGuidedDemo={isGuidedDemo && state === 'review' && stage3SubStep === 'extraction'}
            onNextGuidedStep={() => handleStage3Advance('modalities')}
          />

          {/* Mapped Features Dashboard (Contract 2 Feature Mapper Results) */}
          <MappedFeaturesDashboard
            mapperOutput={activeResult.mapper_output}
            error={activeResult.mapper_output_error}
            userAddedValues={userAddedValues}
            onUserAddedValuesChange={(vals) => setUserAddedValues(vals)}
            triggerCategoryQueue={triggerCategoryQueue}
            onQueueDismissed={() => setTriggerCategoryQueue(null)}
            isGuidedDemo={isGuidedDemo && state === 'review'}
            guidedSubStep={stage3SubStep}
            onSetGuidedSubStep={(st) => handleStage3Advance(st)}
            onNextGuidedStep={() => handleStage3Advance()}
          />

          {/* Guidance or Confirmation Step based on completeness */}
          {!isAnyCategoryComplete ? (
            <NotEnoughDataGuidance
              categories={categories}
              closestCategory={closestCategory}
              onProvideMissing={handleProvideMissing}
              onProceedAnyway={handleRunAssessment}
            />
          ) : (
            /* Standard CTA Confirmation Bar when at least 1 category is complete */
            <div className={`p-6 sm:p-8 rounded-3xl transition-all duration-300 space-y-6 ${
              isGuidedDemo && state === 'review'
                ? 'bg-white border-2 border-sky-300 ring-4 ring-sky-400/20 shadow-2xl shadow-sky-500/10'
                : 'bg-white border border-sky-100 shadow-xl shadow-sky-500/5'
            }`}>
              <div className="space-y-2">
                <h3 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2">
                  <Sparkles className="w-5 h-5 text-sky-600" />
                  <span>Ready to analyze your health information?</span>
                </h3>
                <p className="text-slate-600 text-xs sm:text-sm leading-relaxed">
                  We'll generate an assessment using the information currently available. Some results may have limited data or may not be available if there isn't enough information.
                </p>
              </div>

              {/* Guided Demo Final Action Callout - Eye-Catching Orange & Sky Blue Theme */}
              {isGuidedDemo && (
                <div className="p-6 rounded-3xl bg-gradient-to-r from-orange-600 via-amber-600 to-sky-700 text-white border-2 border-amber-300 shadow-2xl shadow-orange-600/30 space-y-3 animate-fade-in guided-blink-glow-card">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center space-x-2.5">
                      <span className="px-3 py-1 rounded-full bg-slate-950 text-amber-300 text-xs font-black tracking-wider uppercase shadow-md border border-amber-400">
                        🎯 GUIDED DEMO • STAGE 03
                      </span>
                      <span className="text-sm font-black text-white">
                        {stage3SubStep === 'assessment' ? 'Ready for Health Assessment' : 'Multi-Modal Features Prepared'}
                      </span>
                    </div>
                    <span className="text-xs font-black text-sky-950 bg-cyan-300 px-3 py-1 rounded-full shadow-xs">
                      ⚡ Ready to Execute
                    </span>
                  </div>

                  <p className="text-sm text-amber-50 leading-relaxed font-medium">
                    {stage3SubStep === 'assessment'
                      ? 'Your clinical, wearable, gut microbiome, and family history information have now been verified and prepared for the metabolic health assessment.'
                      : 'All extracted clinical, wearable, and microbiome features are verified. You can follow the guided steps above or click the blinking button below at any time to run the assessment.'}
                  </p>

                  <div className="pt-2 border-t border-white/20 flex items-center justify-between">
                    <span className="text-xs font-black text-amber-200">
                      👉 Click <strong className="text-white underline underline-offset-4">"Analyze My Health Data"</strong> below to generate predictions.
                    </span>
                  </div>
                </div>
              )}

              <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={handleReset}
                  className="w-full sm:w-auto px-5 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-2xl transition-colors cursor-pointer"
                >
                  Cancel & Upload Again
                </button>

                <button
                  id="guided-assessment-cta"
                  type="button"
                  onClick={handleRunAssessment}
                  className={`w-full sm:w-auto flex items-center justify-center space-x-2.5 px-8 py-3.5 font-black text-sm rounded-2xl shadow-xl transition-all transform cursor-pointer ${
                    isGuidedDemo && state === 'review'
                      ? 'bg-gradient-to-r from-orange-500 via-amber-500 to-sky-600 hover:from-orange-600 hover:to-sky-700 text-white border-2 border-amber-300 ring-4 ring-orange-400/80 guided-blink-glow-orange scale-105 hover:scale-110 active:scale-95'
                      : 'bg-gradient-to-r from-sky-600 via-sky-500 to-cyan-600 hover:from-sky-700 hover:to-cyan-700 text-white shadow-sky-600/25 hover:scale-[1.02] active:scale-[0.98]'
                  }`}
                >
                  <Brain className="w-5 h-5" />
                  <span>Analyze My Health Data</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Expandable Technical Details (Extraction Log & Raw JSON) */}
          <TechnicalDetails data={activeResult} />

        </div>
      )}

      {/* State 5: Final Assessment Results Page */}
      {state === 'assessment' && assessmentResult && (
        <HealthAssessmentResults
          assessment={assessmentResult}
          onReset={handleReset}
          onViewHealthPlan={() => {
            setState('health-plan');
            setStage5SubStep('plan_summary');
            window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
          }}
          isGuidedDemo={isGuidedDemo}
          guidedSubStep={stage4SubStep}
          onNextGuidedStep={handleStage4Advance}
        />
      )}

      {/* State 6: Dedicated Personalized Health Plan Page */}
      {state === 'health-plan' && assessmentResult && (
        <PersonalizedHealthPlanPage
          assessment={assessmentResult}
          onBack={() => {
            setState('assessment');
            window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
          }}
          onReset={handleReset}
          onCreateProgressPlan={(dur) => {
            setProgressPlanDuration(dur);
            setState('progress-plan');
            setProgressPlanSubStep('plan_header');
            window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
          }}
          isGuidedDemo={isGuidedDemo}
          guidedSubStep={stage5SubStep}
          onNextGuidedStep={handleStage5Advance}
        />
      )}

      {/* State 7: Dedicated Personalized Progress Plan Page */}
      {state === 'progress-plan' && assessmentResult && (
        <PersonalizedProgressPlanPage
          assessment={assessmentResult}
          initialDuration={progressPlanDuration}
          onBack={() => {
            setState('health-plan');
            window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
          }}
          onReset={handleReset}
          isGuidedDemo={isGuidedDemo}
          guidedSubStep={progressPlanSubStep}
          onNextGuidedStep={handleProgressPlanAdvance}
          onExitGuidedDemo={onExitGuidedDemo}
        />
      )}

    </div>
  );
};
