import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  Clock,
  XCircle,
  Activity,
  Heart,
  Dna,
  UserCheck,
  Sparkles,
  PlusCircle,
  X,
  ShieldCheck,
  Edit3,
  ChevronDown,
  ChevronUp,
  Table,
  ArrowRight,
} from 'lucide-react';

interface MappedFeatureValue {
  canonical_value: any;
  canonical_unit: string | null;
  original_value?: string;
  original_unit?: string | null;
  mapping_confidence?: number;
  mapping_method?: string;
  source?: string;
  is_derived?: boolean;
  is_user_added?: boolean;
}

interface ModelFeatureState {
  status?: string;
  values?: Record<string, MappedFeatureValue>;
  flagged_for_reconfirm?: any[];
  conflict_log?: any[];
}

export interface MapperOutputState {
  clinical?: ModelFeatureState;
  wearable?: ModelFeatureState;
  gut?: ModelFeatureState;
  _mapper_log?: any[];
}

interface MappedFeaturesDashboardProps {
  mapperOutput?: MapperOutputState | null;
  error?: string | null;
  userAddedValues?: Record<string, MappedFeatureValue>;
  onUserAddedValuesChange?: (values: Record<string, MappedFeatureValue>) => void;
  triggerCategoryQueue?: 'clinical' | 'wearable' | 'gut' | 'family' | null;
  onQueueDismissed?: () => void;
  isGuidedDemo?: boolean;
  guidedSubStep?: 'quality' | 'extraction' | 'modalities' | 'family_history' | 'features' | 'assessment';
  onSetGuidedSubStep?: (step: 'quality' | 'extraction' | 'modalities' | 'family_history' | 'features' | 'assessment') => void;
  onNextGuidedStep?: () => void;
}

interface FieldMeta {
  key: string;
  label: string;
  unit: string;
  type: 'float' | 'integer' | 'categorical' | 'boolean';
  valid_range?: [number, number];
  isDerivedField?: boolean;
  categories?: string[];
}

// Field Schema Definitions (Synchronized with feature_schema.json v2.0.0)
const CLINICAL_FIELDS: FieldMeta[] = [
  { key: 'Age', label: 'Age', unit: 'years', type: 'integer', valid_range: [18, 100] },
  { key: 'Gender', label: 'Gender', unit: '', type: 'categorical', categories: ['Male', 'Female'] },
  { key: 'Height', label: 'Height', unit: 'cm', type: 'float', valid_range: [100, 230] },
  { key: 'Weight', label: 'Weight', unit: 'kg', type: 'float', valid_range: [25, 250] },
  { key: 'BMI', label: 'BMI', unit: 'kg/m²', type: 'float', valid_range: [10, 70], isDerivedField: true },
  { key: 'Waist_Circumference', label: 'Waist Circumference', unit: 'cm', type: 'float', valid_range: [50, 180] },
  { key: 'Systolic_BP', label: 'Systolic Blood Pressure', unit: 'mmHg', type: 'float', valid_range: [70, 220] },
  { key: 'Diastolic_BP', label: 'Diastolic Blood Pressure', unit: 'mmHg', type: 'float', valid_range: [40, 140] },
  { key: 'Fasting_Blood_Glucose', label: 'Fasting Blood Glucose', unit: 'mg/dL', type: 'float', valid_range: [50, 400] },
  { key: 'HbA1c', label: 'HbA1c', unit: '%', type: 'float', valid_range: [3, 15] },
  { key: 'Triglycerides', label: 'Triglycerides', unit: 'mg/dL', type: 'float', valid_range: [30, 1000] },
  { key: 'HDL', label: 'HDL Cholesterol', unit: 'mg/dL', type: 'float', valid_range: [10, 120] },
  { key: 'LDL', label: 'LDL Cholesterol', unit: 'mg/dL', type: 'float', valid_range: [20, 300] },
  { key: 'ALT', label: 'ALT (SGPT)', unit: 'U/L', type: 'float', valid_range: [5, 300] },
  { key: 'AST', label: 'AST (SGOT)', unit: 'U/L', type: 'float', valid_range: [5, 300] },
];

const WEARABLE_FIELDS: FieldMeta[] = [
  { key: 'Age', label: 'Age', unit: 'years', type: 'integer', valid_range: [18, 100] },
  { key: 'Gender', label: 'Gender', unit: '', type: 'categorical', categories: ['Male', 'Female'] },
  { key: 'Average_Daily_Steps', label: 'Average Daily Steps', unit: 'steps/day', type: 'float', valid_range: [0, 40000] },
  { key: 'Active_Minutes', label: 'Active Minutes', unit: 'min/day', type: 'float', valid_range: [0, 300] },
  { key: 'Sedentary_Time_Minutes', label: 'Sedentary Time', unit: 'min/day', type: 'float', valid_range: [0, 1440] },
  { key: 'Resting_Heart_Rate', label: 'Resting Heart Rate', unit: 'bpm', type: 'float', valid_range: [35, 130] },
  { key: 'Heart_Rate_Variability_RMSSD', label: 'Heart Rate Variability (RMSSD)', unit: 'ms', type: 'float', valid_range: [0, 200] },
  { key: 'Sleep_Duration_Hours', label: 'Sleep Duration', unit: 'hours', type: 'float', valid_range: [0, 14] },
  { key: 'Sleep_Efficiency_Score', label: 'Sleep Efficiency Score', unit: 'score', type: 'float', valid_range: [0, 100] },
  { key: 'Autonomic_Stress_Score', label: 'Autonomic Stress Score', unit: 'score', type: 'float', valid_range: [0, 100] },
  { key: 'Activity_Energy_Expenditure', label: 'Activity Energy Expenditure', unit: 'kcal/day', type: 'float', valid_range: [800, 6000] },
  { key: 'Exercise_Frequency_Days', label: 'Exercise Frequency', unit: 'days/week', type: 'float', valid_range: [0, 7] },
  { key: 'CGM_Average_Glucose', label: 'CGM Average Glucose', unit: 'mg/dL', type: 'float', valid_range: [50, 400] },
  { key: 'CGM_Glucose_CV', label: 'CGM Glucose CV', unit: '% CV', type: 'float', valid_range: [0, 100] },
  { key: 'CGM_Time_In_Range', label: 'CGM Time In Range (TIR)', unit: '%', type: 'float', valid_range: [0, 100] },
  { key: 'CGM_Time_Above_Range', label: 'CGM Time Above Range (TAR)', unit: '%', type: 'float', valid_range: [0, 100] },
  { key: 'CGM_Time_Below_Range', label: 'CGM Time Below Range (TBR)', unit: '%', type: 'float', valid_range: [0, 100] },
];

const GUT_FIELDS: FieldMeta[] = [
  { key: 'Age', label: 'Age', unit: 'years', type: 'integer', valid_range: [18, 100] },
  { key: 'Gender', label: 'Gender', unit: '', type: 'categorical', categories: ['Male', 'Female'] },
  { key: 'Akkermansia', label: 'Akkermansia muciniphila', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Faecalibacterium', label: 'Faecalibacterium prausnitzii', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Roseburia', label: 'Roseburia', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Bifidobacterium', label: 'Bifidobacterium', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Bacteroides', label: 'Bacteroides', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Prevotella', label: 'Prevotella', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Ruminococcus', label: 'Ruminococcus', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Blautia', label: 'Blautia', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Collinsella', label: 'Collinsella', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Escherichia_Shigella', label: 'Escherichia / Shigella', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Coprococcus', label: 'Coprococcus', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Alistipes', label: 'Alistipes', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Subdoligranulum', label: 'Subdoligranulum', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Enterococcus', label: 'Enterococcus', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Eubacterium', label: 'Eubacterium', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Parabacteroides', label: 'Parabacteroides', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Lactobacillus', label: 'Lactobacillus', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Klebsiella', label: 'Klebsiella', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Streptococcus', label: 'Streptococcus', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Eggerthella', label: 'Eggerthella', unit: '%', type: 'float', valid_range: [0, 30] },
  { key: 'Other_Taxa', label: 'Other Taxa', unit: '%', type: 'float', valid_range: [0, 30] },
];

const FAMILY_HISTORY_FIELDS: FieldMeta[] = [
  { key: 'Family_History_Diabetes', label: 'Family History of Diabetes', unit: '', type: 'boolean' },
  { key: 'Family_History_Hypertension', label: 'Family History of High Blood Pressure', unit: '', type: 'boolean' },
  { key: 'Family_History_CVD', label: 'Family History of Cardiovascular Disease (CVD)', unit: '', type: 'boolean' },
];

export const MappedFeaturesDashboard: React.FC<MappedFeaturesDashboardProps> = ({
  mapperOutput,
  error,
  userAddedValues: externalUserAddedValues,
  onUserAddedValuesChange,
  triggerCategoryQueue,
  onQueueDismissed,
  isGuidedDemo = false,
  guidedSubStep = 'modalities',
  onSetGuidedSubStep,
  onNextGuidedStep,
}) => {
  // Local state to store user-entered values live
  const [internalUserAddedValues, setInternalUserAddedValues] = useState<Record<string, MappedFeatureValue>>({});
  const userAddedValues = externalUserAddedValues || internalUserAddedValues;

  // Feature Tables Collapsible Visibility State (Default: False)
  const [showTables, setShowTables] = useState<boolean>(false);

  // Missing Field Questionnaire Wizard Queue State
  const [queue, setQueue] = useState<{ model: 'clinical' | 'wearable' | 'gut' | 'family'; meta: FieldMeta }[]>([]);
  const [queueIndex, setQueueIndex] = useState<number>(0);

  // Form input and error state
  const [inputValue, setInputValue] = useState<string>('');
  const [validationError, setValidationError] = useState<string | null>(null);

  // Unit selector state for Height and Weight
  const [heightUnit, setHeightUnit] = useState<'cm' | 'ft_in' | 'inches'>('cm');
  const [weightUnit, setWeightUnit] = useState<'kg' | 'lbs'>('kg');
  const [feetValue, setFeetValue] = useState<string>('');
  const [inchesValue, setInchesValue] = useState<string>('');

  if (error) {
    return (
      <div className="p-6 bg-rose-50 border-2 border-rose-200 rounded-2xl space-y-3">
        <div className="flex items-center space-x-2 text-rose-800 font-bold text-base">
          <XCircle className="w-5 h-5 text-rose-600" />
          <span>Feature Mapper Error</span>
        </div>
        <p className="text-xs text-rose-700 leading-relaxed">{error}</p>
      </div>
    );
  }

  if (!mapperOutput) {
    return null;
  }

  const clinicalState = mapperOutput.clinical || {};
  const wearableState = mapperOutput.wearable || {};
  const gutState = mapperOutput.gut || {};

  // Merge server extracted values with user added values
  const clinValues = { ...(clinicalState.values || {}), ...userAddedValues };

  // Inherit shared features (Age & Gender) across all models if present in clinical/shared state
  const sharedFromClin: Record<string, MappedFeatureValue> = {};
  if (clinValues['Age']) sharedFromClin['Age'] = clinValues['Age'];
  if (clinValues['Gender']) sharedFromClin['Gender'] = clinValues['Gender'];

  const wearValues = { ...sharedFromClin, ...(wearableState.values || {}), ...userAddedValues };
  const gutValues = { ...sharedFromClin, ...(gutState.values || {}), ...userAddedValues };

  const familyValues = { ...(clinicalState.values || {}), ...userAddedValues };

  // Calculate dynamic stats
  const clinFoundCount = CLINICAL_FIELDS.filter((f) => clinValues[f.key] !== undefined).length;
  const clinMissingCount = CLINICAL_FIELDS.length - clinFoundCount;

  const wearFoundCount = WEARABLE_FIELDS.filter((f) => wearValues[f.key] !== undefined).length;
  const wearMissingCount = WEARABLE_FIELDS.length - wearFoundCount;

  const gutFoundCount = GUT_FIELDS.filter((f) => gutValues[f.key] !== undefined).length;
  const gutMissingCount = GUT_FIELDS.length - gutFoundCount;

  const familyFoundCount = FAMILY_HISTORY_FIELDS.filter((f) => familyValues[f.key] !== undefined).length;
  const familyMissingCount = FAMILY_HISTORY_FIELDS.length - familyFoundCount;

  // Open Queue Wizard Handler (for Summary Cards or Table Badges)
  const handleStartQueue = (model: 'clinical' | 'wearable' | 'gut' | 'family', singleMeta?: FieldMeta) => {
    let missingList: FieldMeta[] = [];

    if (singleMeta) {
      missingList = [singleMeta];
    } else {
      if (model === 'clinical') {
        missingList = CLINICAL_FIELDS.filter((f) => clinValues[f.key] === undefined);
      } else if (model === 'wearable') {
        missingList = WEARABLE_FIELDS.filter((f) => wearValues[f.key] === undefined);
      } else if (model === 'gut') {
        missingList = GUT_FIELDS.filter((f) => gutValues[f.key] === undefined);
      } else if (model === 'family') {
        missingList = FAMILY_HISTORY_FIELDS.filter((f) => familyValues[f.key] === undefined);
      }
    }

    if (missingList.length > 0) {
      setQueue(missingList.map((meta) => ({ model, meta })));
      setQueueIndex(0);
      setInputValue('');
      setValidationError(null);
      setHeightUnit('cm');
      setWeightUnit('kg');
      setFeetValue('');
      setInchesValue('');
    }
  };

  // Trigger wizard queue externally if requested
  React.useEffect(() => {
    if (triggerCategoryQueue) {
      handleStartQueue(triggerCategoryQueue);
    }
  }, [triggerCategoryQueue]);

  // Close Wizard Queue Modal
  const handleCloseModal = () => {
    setQueue([]);
    setQueueIndex(0);
    setInputValue('');
    setValidationError(null);
    if (onQueueDismissed) {
      onQueueDismissed();
    }
  };

  // Current active question item in queue
  const currentItem = queue[queueIndex];

  // Submit and validate user entry against schema
  // Convert height from user-selected unit to cm
  const convertHeightToCm = (): number | null => {
    if (heightUnit === 'cm') {
      const val = parseFloat(inputValue);
      return isNaN(val) ? null : val;
    } else if (heightUnit === 'ft_in') {
      const ft = parseFloat(feetValue);
      const inches = parseFloat(inchesValue || '0');
      if (isNaN(ft)) return null;
      if (isNaN(inches)) return null;
      return Math.round(((ft * 12) + inches) * 2.54 * 100) / 100;
    } else if (heightUnit === 'inches') {
      const val = parseFloat(inputValue);
      return isNaN(val) ? null : Math.round(val * 2.54 * 100) / 100;
    }
    return null;
  };

  // Convert weight from user-selected unit to kg
  const convertWeightToKg = (): number | null => {
    if (weightUnit === 'kg') {
      const val = parseFloat(inputValue);
      return isNaN(val) ? null : val;
    } else if (weightUnit === 'lbs') {
      const val = parseFloat(inputValue);
      return isNaN(val) ? null : Math.round(val * 0.453592 * 100) / 100;
    }
    return null;
  };

  const handleSaveValue = (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentItem) return;

    const { meta } = currentItem;
    let parsedVal: any = typeof inputValue === 'string' ? inputValue.trim() : inputValue;

    if (meta.type === 'boolean') {
      if (parsedVal !== 'Yes' && parsedVal !== 'No' && parsedVal !== true && parsedVal !== false) {
        setValidationError('⚠️ Please select either Yes or No.');
        return;
      }
    } else if (meta.type === 'categorical') {
      if (!meta.categories?.includes(parsedVal)) {
        setValidationError(`⚠️ Please select a valid option (${meta.categories?.join(', ')}).`);
        return;
      }
    } else if (meta.key === 'Height_cm') {
      // Special height conversion
      const cmVal = convertHeightToCm();
      if (cmVal === null) {
        if (heightUnit === 'ft_in') {
          setValidationError('⚠️ Please enter valid feet and inches values.');
        } else {
          setValidationError('⚠️ Invalid Numerical Value: Please enter a valid number.');
        }
        return;
      }
      if (meta.valid_range) {
        const [min, max] = meta.valid_range;
        if (cmVal < min || cmVal > max) {
          setValidationError(
            `⚠️ Out of Range: Converted value ${cmVal} cm is outside valid range [${min}, ${max}] cm. Please check your input.`
          );
          return;
        }
      }
      parsedVal = cmVal;
    } else if (meta.key === 'Weight_kg') {
      // Special weight conversion
      const kgVal = convertWeightToKg();
      if (kgVal === null) {
        setValidationError('⚠️ Invalid Numerical Value: Please enter a valid number.');
        return;
      }
      if (meta.valid_range) {
        const [min, max] = meta.valid_range;
        if (kgVal < min || kgVal > max) {
          setValidationError(
            `⚠️ Out of Range: Converted value ${kgVal} kg is outside valid range [${min}, ${max}] kg. Please check your input.`
          );
          return;
        }
      }
      parsedVal = kgVal;
    } else {
      const num = parseFloat(parsedVal);
      if (isNaN(num)) {
        setValidationError('⚠️ Invalid Numerical Value: Please enter a valid number.');
        return;
      }
      if (meta.valid_range) {
        const [min, max] = meta.valid_range;
        if (num < min || num > max) {
          setValidationError(
            `⚠️ Out of Plausibility Range: Value ${num} is outside valid schema range [${min}, ${max}] ${meta.unit}. Please enter a realistic medical value.`
          );
          return;
        }
      }
      parsedVal = meta.type === 'integer' ? Math.round(num) : num;
    }

    // Validation passed — store feature in userAddedValues live
    const updated = {
      ...userAddedValues,
      [meta.key]: {
        canonical_value: parsedVal,
        canonical_unit: meta.unit || null,
        mapping_confidence: 1.0,
        mapping_method: 'user_entry',
        is_user_added: true,
      },
    };
    setInternalUserAddedValues(updated);
    if (onUserAddedValuesChange) {
      onUserAddedValuesChange(updated);
    }

    // Check if there are remaining missing questions in the queue sequence!
    if (queueIndex < queue.length - 1) {
      setQueueIndex((prev) => prev + 1);
      setInputValue('');
      setValidationError(null);
    } else {
      // Sequence complete — close modal
      handleCloseModal();
      if (isGuidedDemo && guidedSubStep === 'family_history') {
        onSetGuidedSubStep?.('features');
      }
    }
  };

  return (
    <div id="guided-mapped-dashboard" className="space-y-8 mt-8 border-t border-slate-200 pt-8">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-100 text-indigo-800 text-xs font-bold mb-2">
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span>Structured Data Mapping</span>
          </div>
          <h3 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Mapped Features Dashboard
          </h3>
          <p className="text-slate-500 text-xs mt-1">
            Canonicalized features normalized against standard clinical schemas (Contract 2).
          </p>
        </div>
      </div>

      {/* Guided Demo Step 3C / 3D Callout: Modalities Explanation - High Visibility Vibrant Blue/Indigo Design */}
      {isGuidedDemo && guidedSubStep === 'modalities' && (
        <div className="p-6 rounded-3xl bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white border-2 border-cyan-400 shadow-2xl shadow-blue-950/50 space-y-4 animate-fade-in guided-blink-glow-card">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center space-x-2.5">
              <span className="px-3 py-1 rounded-full bg-amber-400 text-slate-950 text-xs font-black tracking-wider uppercase shadow-md">
                🎯 GUIDED DEMO • STEP 03
              </span>
              <span className="text-sm font-black text-cyan-200 tracking-wide">
                Standardized Multimodal Modalities
              </span>
            </div>
            <span className="text-xs font-extrabold text-white bg-white/20 backdrop-blur-md px-3 py-1 rounded-full border border-white/30">
              Contract 2 Schemas
            </span>
          </div>

          <p className="text-sm text-slate-100 leading-relaxed font-medium">
            The Document Reader and Feature Mapper mapped the report into standardized schemas required by each AI model:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
            <div className="p-4 rounded-2xl bg-white/10 backdrop-blur-md border border-cyan-300/30 space-y-1.5 shadow-inner">
              <div className="flex items-center justify-between">
                <span className="text-sm font-black text-cyan-300">Clinical Features</span>
                <span className="text-xs font-black text-amber-300 bg-amber-400/20 px-2 py-0.5 rounded-md font-mono">{clinFoundCount} / {CLINICAL_FIELDS.length}</span>
              </div>
              <p className="text-xs text-slate-200 leading-relaxed">
                These are the clinical features extracted and mapped from the uploaded report into the standardized clinical schema used by the prediction pipeline.
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-white/10 backdrop-blur-md border border-rose-300/30 space-y-1.5 shadow-inner">
              <div className="flex items-center justify-between">
                <span className="text-sm font-black text-rose-300">Wearable / CGM Features</span>
                <span className="text-xs font-black text-amber-300 bg-amber-400/20 px-2 py-0.5 rounded-md font-mono">{wearFoundCount} / {WEARABLE_FIELDS.length}</span>
              </div>
              <p className="text-xs text-slate-200 leading-relaxed">
                These are physiological and glucose-related measurements extracted from the report and mapped to the wearable model's expected feature schema.
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-white/10 backdrop-blur-md border border-teal-300/30 space-y-1.5 shadow-inner">
              <div className="flex items-center justify-between">
                <span className="text-sm font-black text-teal-300">Gut Microbiome Features</span>
                <span className="text-xs font-black text-amber-300 bg-amber-400/20 px-2 py-0.5 rounded-md font-mono">{gutFoundCount} / {GUT_FIELDS.length}</span>
              </div>
              <p className="text-xs text-slate-200 leading-relaxed">
                These are microbiome taxa measurements extracted from the report and mapped into the format required by the gut microbiome model.
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-2 border-t border-white/15">
            <span className="text-xs text-cyan-200 font-semibold">
              All displayed feature counts reflect actual pipeline mapping results.
            </span>
            <button
              type="button"
              onClick={onNextGuidedStep}
              className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-amber-400 via-orange-500 to-amber-500 hover:from-amber-300 hover:to-orange-400 text-slate-950 font-black text-xs rounded-2xl shadow-xl shadow-amber-500/30 transition-all hover:scale-105 active:scale-95 cursor-pointer shrink-0 guided-blink-glow-orange"
            >
              <span>Next: Family History Questionnaire</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Guided Demo Step 3E / 3F Callout: Family History Input Required - High Visibility Orange Theme */}
      {isGuidedDemo && guidedSubStep === 'family_history' && (
        <div className="p-6 rounded-3xl bg-gradient-to-r from-orange-600 via-amber-600 to-rose-600 text-white border-2 border-amber-300 shadow-2xl shadow-orange-600/30 space-y-3 animate-fade-in guided-blink-glow-card">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center space-x-2.5">
              <span className="px-3 py-1 rounded-full bg-slate-950 text-amber-300 text-xs font-black tracking-wider uppercase shadow-md border border-amber-400">
                🎯 GUIDED DEMO • STEP 03
              </span>
              <span className="text-sm font-black text-white">One more input is required</span>
            </div>
            <span className="text-xs font-black text-orange-950 bg-amber-200 px-3 py-1 rounded-full shadow-xs">
              {familyFoundCount} / {FAMILY_HISTORY_FIELDS.length} Completed
            </span>
          </div>

          <p className="text-sm text-amber-50 leading-relaxed font-medium">
            The report provides the available clinical, wearable, and gut microbiome information. The remaining family-history information is collected directly from the user.
          </p>

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-2 border-t border-white/20">
            <span className="text-xs font-black text-amber-100">
              👉 For demonstration purposes, select <strong className="text-white underline underline-offset-4">YES</strong> for each of the three family-history questions.
            </span>
            {familyMissingCount > 0 ? (
              <button
                type="button"
                onClick={() => handleStartQueue('family')}
                className="flex items-center space-x-2 px-6 py-3 bg-white hover:bg-amber-50 text-orange-700 font-black text-xs rounded-2xl shadow-xl shadow-black/25 transition-all hover:scale-105 active:scale-95 cursor-pointer shrink-0 guided-blink-glow-orange"
              >
                <span>Open Questionnaire Now</span>
                <ArrowRight className="w-4 h-4 text-orange-600" />
              </button>
            ) : (
              <button
                type="button"
                onClick={onNextGuidedStep}
                className="flex items-center space-x-2 px-6 py-3 bg-emerald-400 hover:bg-emerald-300 text-slate-950 font-black text-xs rounded-2xl shadow-xl shadow-emerald-500/30 transition-all hover:scale-105 active:scale-95 cursor-pointer shrink-0 guided-blink-glow-orange"
              >
                <span>Next: View Detailed Feature Tables</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* 4 Summary Cards Grid (ALWAYS VISIBLE - Pic 3) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Clinical */}
        <div className={`bg-white p-5 rounded-2xl border transition-all flex flex-col justify-between space-y-4 ${
          isGuidedDemo && guidedSubStep === 'modalities'
            ? 'border-sky-400 ring-2 ring-sky-400/80 shadow-md shadow-sky-500/10'
            : 'border-slate-200 shadow-xs'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Clinical Model</span>
            <Activity className="w-5 h-5 text-sky-600" />
          </div>
          <div>
            <div className="text-2xl font-extrabold text-slate-900">
              {clinFoundCount} <span className="text-slate-400 font-medium text-base">/ {CLINICAL_FIELDS.length}</span>
            </div>
            <span className="text-xs text-slate-500 font-medium">Extracted Features</span>
          </div>
          <div>
            {clinMissingCount === 0 ? (
              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>🟢 Complete</span>
              </span>
            ) : (
              <button
                onClick={() => handleStartQueue('clinical')}
                className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-100 text-amber-900 border border-amber-300 text-xs font-bold animate-pulse hover:scale-105 transition-all shadow-2xs cursor-pointer"
              >
                <span className="w-2 h-2 rounded-full bg-amber-600 animate-ping inline-block" />
                <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                <span>🟡 {clinMissingCount} Missing (Click to Fill)</span>
              </button>
            )}
          </div>
        </div>

        {/* Card 2: Wearable */}
        <div className={`bg-white p-5 rounded-2xl border transition-all flex flex-col justify-between space-y-4 ${
          isGuidedDemo && guidedSubStep === 'modalities'
            ? 'border-rose-400 ring-2 ring-rose-400/80 shadow-md shadow-rose-500/10'
            : 'border-slate-200 shadow-xs'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Wearable Model</span>
            <Heart className="w-5 h-5 text-rose-600" />
          </div>
          <div>
            <div className="text-2xl font-extrabold text-slate-900">
              {wearFoundCount} <span className="text-slate-400 font-medium text-base">/ {WEARABLE_FIELDS.length}</span>
            </div>
            <span className="text-xs text-slate-500 font-medium">Device & CGM Metrics</span>
          </div>
          <div>
            {wearMissingCount === 0 ? (
              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>🟢 Complete</span>
              </span>
            ) : (
              <button
                onClick={() => handleStartQueue('wearable')}
                className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-100 text-amber-900 border border-amber-300 text-xs font-bold animate-pulse hover:scale-105 transition-all shadow-2xs cursor-pointer"
              >
                <span className="w-2 h-2 rounded-full bg-amber-600 animate-ping inline-block" />
                <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                <span>🟡 {wearMissingCount} Missing (Click to Fill)</span>
              </button>
            )}
          </div>
        </div>

        {/* Card 3: Gut Microbiome */}
        <div className={`bg-white p-5 rounded-2xl border transition-all flex flex-col justify-between space-y-4 ${
          isGuidedDemo && guidedSubStep === 'modalities'
            ? 'border-teal-400 ring-2 ring-teal-400/80 shadow-md shadow-teal-500/10'
            : 'border-slate-200 shadow-xs'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Gut Microbiome</span>
            <Dna className="w-5 h-5 text-teal-600" />
          </div>
          <div>
            <div className="text-2xl font-extrabold text-slate-900">
              {gutFoundCount} <span className="text-slate-400 font-medium text-base">/ {GUT_FIELDS.length}</span>
            </div>
            <span className="text-xs text-slate-500 font-medium">Taxa Abundance</span>
          </div>
          <div>
            {gutMissingCount === 0 ? (
              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>🟢 Complete</span>
              </span>
            ) : (
              <button
                onClick={() => handleStartQueue('gut')}
                className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-100 text-amber-900 border border-amber-300 text-xs font-bold animate-pulse hover:scale-105 transition-all shadow-2xs cursor-pointer"
              >
                <span className="w-2 h-2 rounded-full bg-amber-600 animate-ping inline-block" />
                <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                <span>🟡 {gutMissingCount} Missing (Click to Fill)</span>
              </button>
            )}
          </div>
        </div>

        {/* Card 4: Family History */}
        <div
          id="guided-family-history"
          className={`bg-white p-5 rounded-2xl border transition-all flex flex-col justify-between space-y-4 ${
            isGuidedDemo && guidedSubStep === 'family_history'
              ? 'border-orange-400 ring-4 ring-orange-400/80 ring-offset-2 animate-pulse shadow-xl shadow-orange-500/20'
              : 'border-slate-200 shadow-xs'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Family History</span>
            <UserCheck className="w-5 h-5 text-orange-600" />
          </div>
          <div>
            <div className="text-2xl font-extrabold text-slate-900">
              {familyFoundCount} <span className="text-slate-400 font-medium text-base">/ {FAMILY_HISTORY_FIELDS.length}</span>
            </div>
            <span className="text-xs text-slate-500 font-medium">User Questionnaire</span>
          </div>
          <div>
            {familyMissingCount === 0 ? (
              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>🟢 Complete</span>
              </span>
            ) : (
              <button
                onClick={() => handleStartQueue('family')}
                className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-orange-100 text-orange-900 border border-orange-300 text-xs font-bold transition-all shadow-2xs cursor-pointer ${
                  isGuidedDemo && guidedSubStep === 'family_history'
                    ? 'ring-2 ring-orange-500 scale-105 shadow-md shadow-orange-500/30'
                    : 'animate-pulse hover:scale-105'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-orange-500 animate-ping inline-block" />
                <Clock className="w-3.5 h-3.5 text-orange-700" />
                <span>🟠 Awaiting User Input</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Guided Demo Step 3G Callout (when tables are not yet opened) - High Visibility Vibrant Electric Blue Theme */}
      {isGuidedDemo && guidedSubStep === 'features' && !showTables && (
        <div className="p-6 rounded-3xl bg-gradient-to-r from-blue-950 via-sky-900 to-indigo-950 text-white border-2 border-cyan-400 shadow-2xl shadow-cyan-500/20 space-y-4 animate-fade-in guided-blink-glow-card">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center space-x-2.5">
              <span className="px-3 py-1 rounded-full bg-amber-400 text-slate-950 text-xs font-black tracking-wider uppercase shadow-md">
                🎯 GUIDED DEMO • STEP 03
              </span>
              <span className="text-sm font-black text-cyan-200">View Detailed Feature Tables</span>
            </div>
            <span className="text-xs font-extrabold text-white bg-white/20 backdrop-blur-md px-3 py-1 rounded-full border border-white/30">
              Detailed Inspection
            </span>
          </div>

          <p className="text-sm text-slate-100 leading-relaxed font-medium">
            Open the detailed feature tables to see the values extracted and prepared for the prediction models.
          </p>

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-2 border-t border-white/20">
            <span className="text-xs font-black text-amber-200">
              👉 Click <strong>"View Detailed Feature Tables"</strong> below to view extracted and derived parameters.
            </span>
            <button
              type="button"
              onClick={() => setShowTables(true)}
              className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-amber-400 via-orange-500 to-amber-500 hover:from-amber-300 hover:to-orange-400 text-slate-950 font-black text-xs rounded-2xl shadow-xl shadow-amber-500/40 transition-all hover:scale-105 active:scale-95 cursor-pointer shrink-0 guided-blink-glow-orange"
            >
              <span>Open Tables Now</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Master Toggle Dropdown Button for Detailed Feature Tables (Collapsible) */}
      <div
        id="guided-feature-tables"
        className={`flex items-center justify-between bg-slate-50 p-4 rounded-2xl border transition-all ${
          isGuidedDemo && guidedSubStep === 'features'
            ? 'border-2 border-sky-400 ring-4 ring-sky-400/30 bg-sky-50/50 shadow-xl shadow-sky-500/10 guided-blink-glow-card'
            : 'border-slate-200'
        }`}
      >
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold">
            <Table className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-extrabold text-slate-900">Detailed Feature Schema Tables</h4>
            <span className="text-xs text-slate-500">
              Inspect raw canonical values, units, and extraction confidence breakdowns across all models
            </span>
          </div>
        </div>

        <button
          onClick={() => setShowTables(!showTables)}
          className={`flex items-center space-x-2 px-6 py-3 rounded-2xl transition-all cursor-pointer ${
            isGuidedDemo && guidedSubStep === 'features' && !showTables
              ? 'bg-gradient-to-r from-orange-500 via-amber-500 to-sky-600 text-white font-black border-2 border-amber-300 ring-4 ring-orange-400/80 guided-blink-glow-orange shadow-xl shadow-orange-500/40 scale-105'
              : 'bg-white hover:bg-slate-100 text-slate-800 text-xs font-extrabold border border-slate-300 shadow-2xs'
          }`}
        >
          <span>{showTables ? 'Hide Feature Tables' : 'View Detailed Feature Tables'}</span>
          {showTables ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* 4 Feature Tables (Rendered ONLY when showTables === true) */}
      {showTables && (
        <div className="space-y-8 animate-fade-in">
          
          {/* Guided Demo Step 3H Callout: Extracted vs Derived Values - High Visibility Dark Glass Theme */}
          {isGuidedDemo && guidedSubStep === 'features' && (
            <div className="p-6 rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white border-2 border-cyan-400 shadow-2xl shadow-indigo-950/50 space-y-4 animate-fade-in guided-blink-glow-card">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center space-x-2.5">
                  <span className="px-3 py-1 rounded-full bg-amber-400 text-slate-950 text-xs font-black tracking-wider uppercase shadow-md">
                    🎯 GUIDED DEMO • STEP 03
                  </span>
                  <span className="text-sm font-black text-cyan-200">Extracted &amp; Derived Features</span>
                </div>
                <span className="text-xs font-extrabold text-white bg-white/20 backdrop-blur-md px-3 py-1 rounded-full border border-white/30">
                  Standardized Verification
                </span>
              </div>

              <p className="text-sm text-slate-100 leading-relaxed font-medium">
                Some values are directly extracted from the uploaded report. Other values are derived or transformed from related information in the report according to the system's feature-mapping and preprocessing rules.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                <div className="p-4 rounded-2xl bg-emerald-950/70 border-2 border-emerald-400 space-y-1.5 shadow-inner">
                  <div className="flex items-center space-x-2">
                    <span className="px-2.5 py-1 rounded-full bg-emerald-400 text-emerald-950 font-black text-xs">
                      ✅ Extracted Successfully
                    </span>
                  </div>
                  <p className="text-xs text-emerald-100 leading-relaxed font-medium">
                    Value directly identified from the source report (e.g. Fasting Blood Glucose, Blood Pressure, Heart Rate).
                  </p>
                </div>

                <div className="p-4 rounded-2xl bg-amber-950/70 border-2 border-amber-400 space-y-1.5 shadow-inner">
                  <div className="flex items-center space-x-2">
                    <span className="px-2.5 py-1 rounded-full bg-amber-400 text-amber-950 font-black text-xs">
                      🟡 Derived Value
                    </span>
                  </div>
                  <p className="text-xs text-amber-100 leading-relaxed font-medium">
                    Value calculated or transformed using relevant information from the report (such as BMI, calculated from Height and Weight according to schema rules).
                  </p>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-2 border-t border-white/20">
                <span className="text-xs text-cyan-200 font-semibold">
                  Notice the highlighted status badges in the tables below.
                </span>
                <button
                  type="button"
                  onClick={onNextGuidedStep}
                  className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-amber-400 via-orange-500 to-amber-500 hover:from-amber-300 hover:to-orange-400 text-slate-950 font-black text-xs rounded-2xl shadow-xl shadow-amber-500/30 transition-all hover:scale-105 active:scale-95 cursor-pointer shrink-0 guided-blink-glow-orange"
                >
                  <span>Next: Ready for Health Assessment</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Feature Group 1: Clinical Features */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="px-6 py-4 bg-slate-50/80 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-lg bg-sky-100 text-sky-700 flex items-center justify-center font-bold">
                  <Activity className="w-4 h-4" />
                </div>
                <h4 className="text-base font-extrabold text-slate-900">Clinical Features</h4>
              </div>
              <span className="text-xs font-semibold px-3 py-1 bg-white border border-slate-200 rounded-full text-slate-600">
                {clinFoundCount} of {CLINICAL_FIELDS.length} Extracted
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-slate-100/60 text-slate-500 uppercase text-[11px] font-bold border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-3">Feature Name</th>
                    <th className="px-6 py-3">Extracted Value</th>
                    <th className="px-6 py-3">Unit</th>
                    <th className="px-6 py-3">Confidence / Source</th>
                    <th className="px-6 py-3">Mapping Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {CLINICAL_FIELDS.map((field) => {
                    const item = clinValues[field.key];
                    const isFound = item !== undefined;
                    const isDerived = item?.source === 'derived' || item?.mapping_method === 'derived';
                    const isUserAdded = item?.is_user_added;

                    return (
                      <tr key={field.key} className="hover:bg-slate-50/60 transition-colors">
                        <td className="px-6 py-3.5 font-bold text-slate-900">{field.label}</td>
                        <td className="px-6 py-3.5 font-mono text-sm">
                          {isFound ? (
                            <span className="font-bold text-slate-900">{String(item.canonical_value)}</span>
                          ) : (
                            <span className="text-slate-400 italic">—</span>
                          )}
                        </td>
                        <td className="px-6 py-3.5 text-slate-500 font-medium">
                          {isFound ? item.canonical_unit || field.unit || '—' : field.unit || '—'}
                        </td>
                        <td className="px-6 py-3.5 text-slate-500">
                          {isFound ? (
                            <span className="inline-flex items-center space-x-1.5">
                              <span className="font-semibold text-slate-700">
                                {item.mapping_confidence ? `${Math.round(item.mapping_confidence * 100)}%` : '100%'}
                              </span>
                              <span className="text-[10px] text-slate-400">
                                ({item.mapping_method || (isUserAdded ? 'user_entry' : 'rule_match')})
                              </span>
                            </span>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>
                        <td className="px-6 py-3.5">
                          {isUserAdded ? (
                            <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 text-[11px] font-bold">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                              <span>✅ User Provided</span>
                            </span>
                          ) : isDerived && isFound ? (
                            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200 text-[11px] font-bold">
                              <span>🟡 Derived Value</span>
                            </span>
                          ) : isFound ? (
                            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px] font-bold">
                              <span>✅ Extracted Successfully</span>
                            </span>
                          ) : (
                            <button
                              onClick={() => handleStartQueue('clinical', field)}
                              className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-orange-100 text-orange-900 border border-orange-300 text-[11px] font-bold animate-pulse hover:scale-105 transition-all shadow-2xs cursor-pointer"
                            >
                              <span className="w-2 h-2 rounded-full bg-orange-500 animate-ping inline-block" />
                              <PlusCircle className="w-3.5 h-3.5 text-orange-700" />
                              <span>❌ Missing (Click to Enter)</span>
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Feature Group 2: Wearable Features */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="px-6 py-4 bg-slate-50/80 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center font-bold">
                  <Heart className="w-4 h-4" />
                </div>
                <h4 className="text-base font-extrabold text-slate-900">Wearable Device & CGM Features</h4>
              </div>
              <span className="text-xs font-semibold px-3 py-1 bg-white border border-slate-200 rounded-full text-slate-600">
                {wearFoundCount} of {WEARABLE_FIELDS.length} Extracted
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-slate-100/60 text-slate-500 uppercase text-[11px] font-bold border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-3">Feature Name</th>
                    <th className="px-6 py-3">Extracted Value</th>
                    <th className="px-6 py-3">Unit</th>
                    <th className="px-6 py-3">Confidence / Source</th>
                    <th className="px-6 py-3">Mapping Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {WEARABLE_FIELDS.map((field) => {
                    const item = wearValues[field.key];
                    const isFound = item !== undefined;
                    const isUserAdded = item?.is_user_added;

                    return (
                      <tr key={field.key} className="hover:bg-slate-50/60 transition-colors">
                        <td className="px-6 py-3.5 font-bold text-slate-900">{field.label}</td>
                        <td className="px-6 py-3.5 font-mono text-sm">
                          {isFound ? (
                            <span className="font-bold text-slate-900">{String(item.canonical_value)}</span>
                          ) : (
                            <span className="text-slate-400 italic">—</span>
                          )}
                        </td>
                        <td className="px-6 py-3.5 text-slate-500 font-medium">
                          {isFound ? item.canonical_unit || field.unit || '—' : field.unit || '—'}
                        </td>
                        <td className="px-6 py-3.5 text-slate-500">
                          {isFound ? (
                            <span className="inline-flex items-center space-x-1.5">
                              <span className="font-semibold text-slate-700">
                                {item.mapping_confidence ? `${Math.round(item.mapping_confidence * 100)}%` : '100%'}
                              </span>
                              <span className="text-[10px] text-slate-400">
                                ({item.mapping_method || (isUserAdded ? 'user_entry' : 'rule_match')})
                              </span>
                            </span>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>
                        <td className="px-6 py-3.5">
                          {isUserAdded ? (
                            <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 text-[11px] font-bold">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                              <span>✅ User Provided</span>
                            </span>
                          ) : isFound ? (
                            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px] font-bold">
                              <span>✅ Extracted Successfully</span>
                            </span>
                          ) : (
                            <button
                              onClick={() => handleStartQueue('wearable', field)}
                              className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-orange-100 text-orange-900 border border-orange-300 text-[11px] font-bold animate-pulse hover:scale-105 transition-all shadow-2xs cursor-pointer"
                            >
                              <span className="w-2 h-2 rounded-full bg-orange-500 animate-ping inline-block" />
                              <PlusCircle className="w-3.5 h-3.5 text-orange-700" />
                              <span>❌ Missing (Click to Enter)</span>
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Feature Group 3: Gut Microbiome Features */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="px-6 py-4 bg-slate-50/80 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center font-bold">
                  <Dna className="w-4 h-4" />
                </div>
                <h4 className="text-base font-extrabold text-slate-900">Gut Microbiome Taxonomy Features</h4>
              </div>
              <span className="text-xs font-semibold px-3 py-1 bg-white border border-slate-200 rounded-full text-slate-600">
                {gutFoundCount} of {GUT_FIELDS.length} Extracted
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-slate-100/60 text-slate-500 uppercase text-[11px] font-bold border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-3">Taxon / Index Name</th>
                    <th className="px-6 py-3">Extracted Value</th>
                    <th className="px-6 py-3">Unit</th>
                    <th className="px-6 py-3">Confidence / Source</th>
                    <th className="px-6 py-3">Mapping Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {GUT_FIELDS.map((field) => {
                    const item = gutValues[field.key];
                    const isFound = item !== undefined;
                    const isUserAdded = item?.is_user_added;

                    return (
                      <tr key={field.key} className="hover:bg-slate-50/60 transition-colors">
                        <td className="px-6 py-3.5 font-bold text-slate-900 italic">{field.label}</td>
                        <td className="px-6 py-3.5 font-mono text-sm">
                          {isFound ? (
                            <span className="font-bold text-slate-900">{String(item.canonical_value)}</span>
                          ) : (
                            <span className="text-slate-400 italic">—</span>
                          )}
                        </td>
                        <td className="px-6 py-3.5 text-slate-500 font-medium">
                          {isFound ? item.canonical_unit || field.unit || '—' : field.unit || '—'}
                        </td>
                        <td className="px-6 py-3.5 text-slate-500">
                          {isFound ? (
                            <span className="inline-flex items-center space-x-1.5">
                              <span className="font-semibold text-slate-700">
                                {item.mapping_confidence ? `${Math.round(item.mapping_confidence * 100)}%` : '100%'}
                              </span>
                              <span className="text-[10px] text-slate-400">
                                ({item.mapping_method || (isUserAdded ? 'user_entry' : 'rule_match')})
                              </span>
                            </span>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>
                        <td className="px-6 py-3.5">
                          {isUserAdded ? (
                            <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 text-[11px] font-bold">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                              <span>✅ User Provided</span>
                            </span>
                          ) : isFound ? (
                            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px] font-bold">
                              <span>✅ Extracted Successfully</span>
                            </span>
                          ) : (
                            <button
                              onClick={() => handleStartQueue('gut', field)}
                              className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-orange-100 text-orange-900 border border-orange-300 text-[11px] font-bold animate-pulse hover:scale-105 transition-all shadow-2xs cursor-pointer"
                            >
                              <span className="w-2 h-2 rounded-full bg-orange-500 animate-ping inline-block" />
                              <PlusCircle className="w-3.5 h-3.5 text-orange-700" />
                              <span>❌ Missing (Click to Enter)</span>
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Feature Group 4: Family History (User Questionnaire) */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="px-6 py-4 bg-slate-50/80 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-lg bg-orange-100 text-orange-700 flex items-center justify-center font-bold">
                  <UserCheck className="w-4 h-4" />
                </div>
                <h4 className="text-base font-extrabold text-slate-900">Family History (User Form Questions)</h4>
              </div>
              <span className="text-xs font-semibold px-3 py-1 bg-white border border-slate-200 rounded-full text-slate-600">
                {familyFoundCount} of {FAMILY_HISTORY_FIELDS.length} Answered
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-slate-100/60 text-slate-500 uppercase text-[11px] font-bold border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-3">Question / Field</th>
                    <th className="px-6 py-3">Status Value</th>
                    <th className="px-6 py-3">Source</th>
                    <th className="px-6 py-3">Mapping Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {FAMILY_HISTORY_FIELDS.map((field) => {
                    const item = familyValues[field.key];
                    const isFound = item !== undefined;

                    return (
                      <tr key={field.key} className="hover:bg-slate-50/60 transition-colors">
                        <td className="px-6 py-3.5 font-bold text-slate-900">{field.label}</td>
                        <td className="px-6 py-3.5 font-mono text-sm">
                          {isFound ? (
                            <span className="font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-md">
                              {String(item.canonical_value)}
                            </span>
                          ) : (
                            <span className="text-slate-400 italic">Waiting for User Input</span>
                          )}
                        </td>
                        <td className="px-6 py-3.5 text-slate-500 font-medium">user_form</td>
                        <td className="px-6 py-3.5">
                          {isFound ? (
                            <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 text-[11px] font-bold">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                              <span>✅ Answered</span>
                            </span>
                          ) : (
                            <button
                              onClick={() => handleStartQueue('family', field)}
                              className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-orange-100 text-orange-900 border border-orange-300 text-[11px] font-bold animate-pulse hover:scale-105 transition-all shadow-2xs cursor-pointer"
                            >
                              <span className="w-2 h-2 rounded-full bg-orange-500 animate-ping inline-block" />
                              <Clock className="w-3.5 h-3.5 text-orange-700" />
                              <span>⏳ Awaiting Input (Click to Enter)</span>
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Interactive Guided Modal Questionnaire Wizard for Missing Value Entry */}
      {currentItem && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-6 relative">
            {/* Modal Header Bar with Queue Progress */}
            <div className="flex items-start justify-between border-b border-slate-100 pb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-2xl bg-sky-100 text-sky-700 flex items-center justify-center font-bold">
                  <Edit3 className="w-5 h-5 text-sky-600" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h4 className="text-lg font-extrabold text-slate-900">
                      Enter Missing Feature Value
                    </h4>
                    {queue.length > 1 && (
                      <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 font-bold border border-amber-300">
                        Step {queueIndex + 1} of {queue.length}
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-sky-700 font-bold">
                    Schema Validation Engine (Contract 2)
                  </span>
                </div>
              </div>
              <button
                onClick={handleCloseModal}
                className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 flex items-center justify-center transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Guided Demo Instruction Banner in Questionnaire Modal */}
            {isGuidedDemo && (
              <div className="p-3.5 rounded-2xl bg-gradient-to-r from-orange-500/10 via-amber-500/10 to-orange-500/5 border-2 border-orange-400/80 shadow-sm flex items-start space-x-3 animate-fade-in">
                <div className="w-7 h-7 rounded-lg bg-orange-500 text-white flex items-center justify-center font-bold shrink-0 text-xs shadow-xs">
                  🎯
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] uppercase font-extrabold tracking-wider px-2 py-0.5 rounded-full bg-orange-100 text-orange-900 border border-orange-200">
                      GUIDED DEMO INSTRUCTION
                    </span>
                    <span className="text-xs font-bold text-slate-800">User Questionnaire</span>
                  </div>
                  <p className="text-xs text-slate-700 mt-1 leading-relaxed font-medium">
                    For demonstration purposes, select <strong>"YES"</strong> for each of the three family-history questions, then click <strong>"{queueIndex < queue.length - 1 ? 'Validate & Next Question' : 'Validate & Save All'}"</strong>.
                  </p>
                </div>
              </div>
            )}

            {/* Target Feature Metadata Card */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-500 uppercase">TARGET FEATURE</span>
                <span className="font-mono font-bold text-sky-800 bg-sky-100 px-2 py-0.5 rounded-md">
                  {currentItem.meta.key}
                </span>
              </div>
              <div className="text-base font-extrabold text-slate-900">
                {currentItem.meta.label}
              </div>
              <div className="flex items-center space-x-4 text-xs text-slate-600 pt-1 border-t border-slate-200/60">
                {currentItem.meta.unit && (
                  <span>
                    Unit: <strong className="text-slate-800">{currentItem.meta.unit}</strong>
                  </span>
                )}
                {currentItem.meta.valid_range && (
                  <span>
                    Plausibility Range:{' '}
                    <strong className="text-emerald-700 font-mono">
                      [{currentItem.meta.valid_range[0]}, {currentItem.meta.valid_range[1]}]
                    </strong>
                  </span>
                )}
              </div>
            </div>

            {/* Validation Error Alert Box */}
            {validationError && (
              <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-start space-x-3 text-rose-800 text-xs animate-shake">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <div className="font-semibold leading-relaxed">{validationError}</div>
              </div>
            )}

            {/* Input Form */}
            <form onSubmit={handleSaveValue} className="space-y-5">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  ENTER {currentItem.meta.label.toUpperCase()} VALUE
                </label>

                {currentItem.meta.type === 'boolean' ? (
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setInputValue('Yes')}
                      className={`py-3.5 px-4 rounded-2xl font-bold text-sm border transition-all cursor-pointer ${
                        inputValue === 'Yes'
                          ? 'bg-emerald-600 text-white border-emerald-600 shadow-md ring-2 ring-emerald-400'
                          : isGuidedDemo
                          ? 'bg-emerald-50 hover:bg-emerald-100 text-emerald-950 border-emerald-300 ring-2 ring-emerald-400/80 animate-pulse font-extrabold'
                          : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-200'
                      }`}
                    >
                      Yes {isGuidedDemo && <span className="text-xs ml-1 font-semibold text-emerald-700">(Select)</span>}
                    </button>
                    <button
                      type="button"
                      onClick={() => setInputValue('No')}
                      className={`py-3.5 px-4 rounded-2xl font-bold text-sm border transition-all cursor-pointer ${
                        inputValue === 'No'
                          ? 'bg-rose-600 text-white border-rose-600 shadow-md ring-2 ring-rose-400'
                          : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-200'
                      }`}
                    >
                      No
                    </button>
                  </div>
                ) : currentItem.meta.type === 'categorical' ? (
                  <div className="grid grid-cols-2 gap-3">
                    {currentItem.meta.categories?.map((cat) => (
                      <button
                        type="button"
                        key={cat}
                        onClick={() => setInputValue(cat)}
                        className={`py-3.5 px-4 rounded-2xl font-bold text-sm border transition-all cursor-pointer ${
                          inputValue === cat
                            ? 'bg-sky-600 text-white border-sky-600 shadow-md ring-2 ring-sky-400'
                            : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-200'
                        }`}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                ) : currentItem.meta.key === 'Height_cm' ? (
                  /* ── Height Input with Unit Selector ── */
                  <div className="space-y-3">
                    {/* Unit Selector Buttons */}
                    <div className="flex gap-2">
                      {[
                        { value: 'cm' as const, label: 'Centimeters (cm)' },
                        { value: 'ft_in' as const, label: 'Feet & Inches' },
                        { value: 'inches' as const, label: 'Inches' },
                      ].map((unit) => (
                        <button
                          type="button"
                          key={unit.value}
                          onClick={() => {
                            setHeightUnit(unit.value);
                            setInputValue('');
                            setFeetValue('');
                            setInchesValue('');
                            setValidationError(null);
                          }}
                          className={`flex-1 py-2.5 px-3 rounded-xl text-xs font-bold border-2 transition-all cursor-pointer ${
                            heightUnit === unit.value
                              ? 'bg-sky-600 text-white border-sky-600 shadow-md ring-2 ring-sky-300'
                              : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
                          }`}
                        >
                          {unit.label}
                        </button>
                      ))}
                    </div>

                    {/* Dynamic Input Based on Selected Unit */}
                    {heightUnit === 'ft_in' ? (
                      <div className="flex gap-3">
                        <div className="relative flex-1">
                          <input
                            type="text"
                            value={feetValue}
                            onChange={(e) => setFeetValue(e.target.value)}
                            placeholder="Feet"
                            className="w-full px-4 py-3.5 pr-12 bg-slate-50 border-2 border-slate-200 focus:border-sky-500 rounded-2xl text-slate-900 font-mono text-base outline-none transition-all"
                            autoFocus
                          />
                          <span className="absolute right-3 top-3.5 px-2 py-0.5 bg-slate-200 text-slate-700 text-xs font-bold rounded-lg pointer-events-none">
                            ft
                          </span>
                        </div>
                        <div className="relative flex-1">
                          <input
                            type="text"
                            value={inchesValue}
                            onChange={(e) => setInchesValue(e.target.value)}
                            placeholder="Inches"
                            className="w-full px-4 py-3.5 pr-12 bg-slate-50 border-2 border-slate-200 focus:border-sky-500 rounded-2xl text-slate-900 font-mono text-base outline-none transition-all"
                          />
                          <span className="absolute right-3 top-3.5 px-2 py-0.5 bg-slate-200 text-slate-700 text-xs font-bold rounded-lg pointer-events-none">
                            in
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="relative">
                        <input
                          type="text"
                          value={inputValue}
                          onChange={(e) => setInputValue(e.target.value)}
                          placeholder={`Enter height in ${heightUnit === 'cm' ? 'centimeters' : 'inches'}`}
                          className="w-full px-4 py-3.5 pr-20 bg-slate-50 border-2 border-slate-200 focus:border-sky-500 rounded-2xl text-slate-900 font-mono text-base outline-none transition-all"
                          autoFocus
                        />
                        <span className="absolute right-3 top-3.5 px-2.5 py-1 bg-slate-200 text-slate-700 text-xs font-bold rounded-xl pointer-events-none">
                          {heightUnit === 'cm' ? 'cm' : 'in'}
                        </span>
                      </div>
                    )}

                    {/* Live Conversion Preview */}
                    {heightUnit !== 'cm' && (
                      (() => {
                        let previewCm: number | null = null;
                        if (heightUnit === 'ft_in') {
                          const ft = parseFloat(feetValue);
                          const inches = parseFloat(inchesValue || '0');
                          if (!isNaN(ft) && !isNaN(inches)) {
                            previewCm = Math.round(((ft * 12) + inches) * 2.54 * 100) / 100;
                          }
                        } else if (heightUnit === 'inches') {
                          const val = parseFloat(inputValue);
                          if (!isNaN(val)) previewCm = Math.round(val * 2.54 * 100) / 100;
                        }
                        return previewCm !== null ? (
                          <div className="flex items-center space-x-2 px-3 py-2 bg-emerald-50 border border-emerald-200 rounded-xl">
                            <span className="text-xs font-bold text-emerald-800">→ Converts to:</span>
                            <span className="text-sm font-mono font-extrabold text-emerald-700">{previewCm} cm</span>
                          </div>
                        ) : null;
                      })()
                    )}
                  </div>
                ) : currentItem.meta.key === 'Weight_kg' ? (
                  /* ── Weight Input with Unit Selector ── */
                  <div className="space-y-3">
                    {/* Unit Selector Buttons */}
                    <div className="flex gap-2">
                      {[
                        { value: 'kg' as const, label: 'Kilograms (kg)' },
                        { value: 'lbs' as const, label: 'Pounds (lbs)' },
                      ].map((unit) => (
                        <button
                          type="button"
                          key={unit.value}
                          onClick={() => {
                            setWeightUnit(unit.value);
                            setInputValue('');
                            setValidationError(null);
                          }}
                          className={`flex-1 py-2.5 px-3 rounded-xl text-xs font-bold border-2 transition-all cursor-pointer ${
                            weightUnit === unit.value
                              ? 'bg-sky-600 text-white border-sky-600 shadow-md ring-2 ring-sky-300'
                              : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
                          }`}
                        >
                          {unit.label}
                        </button>
                      ))}
                    </div>

                    {/* Weight Input */}
                    <div className="relative">
                      <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder={`Enter weight in ${weightUnit === 'kg' ? 'kilograms' : 'pounds'}`}
                        className="w-full px-4 py-3.5 pr-20 bg-slate-50 border-2 border-slate-200 focus:border-sky-500 rounded-2xl text-slate-900 font-mono text-base outline-none transition-all"
                        autoFocus
                      />
                      <span className="absolute right-3 top-3.5 px-2.5 py-1 bg-slate-200 text-slate-700 text-xs font-bold rounded-xl pointer-events-none">
                        {weightUnit}
                      </span>
                    </div>

                    {/* Live Conversion Preview */}
                    {weightUnit === 'lbs' && (
                      (() => {
                        const val = parseFloat(inputValue);
                        const previewKg = !isNaN(val) ? Math.round(val * 0.453592 * 100) / 100 : null;
                        return previewKg !== null ? (
                          <div className="flex items-center space-x-2 px-3 py-2 bg-emerald-50 border border-emerald-200 rounded-xl">
                            <span className="text-xs font-bold text-emerald-800">→ Converts to:</span>
                            <span className="text-sm font-mono font-extrabold text-emerald-700">{previewKg} kg</span>
                          </div>
                        ) : null;
                      })()
                    )}
                  </div>
                ) : (
                  <div className="relative">
                    <input
                      type="text"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      placeholder={`Enter ${currentItem.meta.label.toLowerCase()} (${
                        currentItem.meta.unit || 'value'
                      })`}
                      className="w-full px-4 py-3.5 pr-20 bg-slate-50 border-2 border-slate-200 focus:border-sky-500 rounded-2xl text-slate-900 font-mono text-base outline-none transition-all"
                      autoFocus
                    />
                    {currentItem.meta.unit && (
                      <span className="absolute right-3 top-3.5 px-2.5 py-1 bg-slate-200 text-slate-700 text-xs font-bold rounded-xl pointer-events-none">
                        {currentItem.meta.unit}
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Modal Action Buttons */}
              <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="px-5 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-2xl transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex items-center space-x-2 px-6 py-3 bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold rounded-2xl shadow-lg shadow-sky-600/25 transition-all cursor-pointer"
                >
                  <ShieldCheck className="w-4 h-4" />
                  <span>
                    {queueIndex < queue.length - 1 ? 'Validate & Next Question' : 'Validate & Save All'}
                  </span>
                  {queueIndex < queue.length - 1 && <ArrowRight className="w-4 h-4" />}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
