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
import type { CategoryGuidanceInfo } from '../components/NotEnoughDataGuidance';
import { analyzeDocuments, runHealthAssessment } from '../services/api';
import type { DocumentAnalysisResult, HealthAssessmentResponse } from '../types/reader';
import { RefreshCw, Sparkles, AlertCircle, Layers, FileText, CheckCircle2, Brain, ArrowRight } from 'lucide-react';

export const AnalyzePage: React.FC = () => {
  const [state, setState] = useState<'upload' | 'processing' | 'review' | 'analyzing' | 'assessment' | 'health-plan' | 'progress-plan'>('upload');
  const [progressPlanDuration, setProgressPlanDuration] = useState<'1_week' | '1_month' | '3_months'>('1_week');
  const [results, setResults] = useState<DocumentAnalysisResult[]>([]);
  const [activeDocIndex, setActiveDocIndex] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

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

  return (
    <div className="space-y-8 py-6">
      
      {/* Page Title & Subtitle */}
      {state !== 'assessment' && (
        <div className="text-center space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-100 text-sky-800 text-xs font-bold">
            <Sparkles className="w-3.5 h-3.5 text-sky-600" />
            <span>Intelligent Document Analysis & Clinical Fusion</span>
          </div>
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Analyze Medical Reports
          </h2>
          <p className="text-slate-500 text-sm max-w-lg mx-auto">
            Upload health records, lab reports, or wearable exports to extract features and generate a metabolic assessment.
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
        <div className="py-4">
          <FileUpload onFilesSelected={handleFilesSelected} />
        </div>
      )}

      {/* State 2: Processing Documents */}
      {state === 'processing' && <ProcessingLoader />}

      {/* State 3: Analyzing with ModelRouter & Fusion V2 */}
      {state === 'analyzing' && (
        <div className="py-12 flex flex-col items-center justify-center space-y-4">
          <div className="w-16 h-16 rounded-3xl bg-sky-100 text-sky-600 flex items-center justify-center shadow-lg shadow-sky-600/10">
            <Brain className="w-8 h-8 animate-pulse" />
          </div>
          <div className="text-center space-y-1">
            <h3 className="text-lg font-bold text-slate-900">Synthesizing Health Assessment</h3>
            <p className="text-xs text-slate-500 max-w-sm">
              Evaluating available biomarkers and clinical parameters...
            </p>
          </div>
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
            <ReportInfoCard data={activeResult} />
          </div>

          {/* Extracted Text Content Card */}
          <ExtractedContentViewer pages={activeResult.pages} />

          {/* Mapped Features Dashboard (Contract 2 Feature Mapper Results) */}
          <MappedFeaturesDashboard
            mapperOutput={activeResult.mapper_output}
            error={activeResult.mapper_output_error}
            userAddedValues={userAddedValues}
            onUserAddedValuesChange={(vals) => setUserAddedValues(vals)}
            triggerCategoryQueue={triggerCategoryQueue}
            onQueueDismissed={() => setTriggerCategoryQueue(null)}
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
            <div className="bg-white p-6 sm:p-8 rounded-3xl border border-sky-100 shadow-xl shadow-sky-500/5 space-y-6">
              <div className="space-y-2">
                <h3 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2">
                  <Sparkles className="w-5 h-5 text-sky-600" />
                  <span>Ready to analyze your health information?</span>
                </h3>
                <p className="text-slate-600 text-xs sm:text-sm leading-relaxed">
                  We'll generate an assessment using the information currently available. Some results may have limited data or may not be available if there isn't enough information.
                </p>
              </div>

              <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={handleReset}
                  className="w-full sm:w-auto px-5 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-2xl transition-colors cursor-pointer"
                >
                  Cancel & Upload Again
                </button>

                <button
                  type="button"
                  onClick={handleRunAssessment}
                  className="w-full sm:w-auto flex items-center justify-center space-x-2.5 px-8 py-3.5 bg-gradient-to-r from-sky-600 via-sky-500 to-cyan-600 hover:from-sky-700 hover:to-cyan-700 text-white font-bold text-sm rounded-2xl shadow-xl shadow-sky-600/25 transition-all transform hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
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
            window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
          }}
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
            window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
          }}
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
        />
      )}

    </div>
  );
};
