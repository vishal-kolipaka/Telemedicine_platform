export interface ExtractionLogEntry {
  operation_id?: string;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR';
  module: string;
  message: string;
}

export interface DocumentPage {
  page_index: number;
  extractor_used: string;
  raw_text: string;
  tables: string[][][]; // Array of tables, each table is rows x cells
  average_page_confidence: number | null;
}

export interface QualityCheck {
  passed: boolean;
  reason: string | null;
}

export interface DocumentAnalysisResult {
  document_id: string;
  source_file: string;
  file_type: 'pdf' | 'image' | 'csv' | 'xlsx' | 'text' | string;
  mime_type: string;
  file_size_bytes: number;
  page_count: number;
  report_date: string | null;
  report_date_confidence: 'HIGH' | 'LOW' | null;
  upload_timestamp: string;
  file_hash: string;
  pages: DocumentPage[];
  extraction_log: ExtractionLogEntry[];
  quality_check: QualityCheck;
  extraction_confidence: 'high' | 'medium' | 'low';
  status?: 'EXACT_DUPLICATE';
  matched_document_id?: string;
  mapper_output?: any;
  mapper_output_error?: string;
}

export type AssessmentStatusLabel =
  | 'Assessment Available'
  | 'Limited Data Assessment'
  | 'Not Enough Information';

export interface AssessmentDiseaseResult {
  key: string;
  display_name: string;
  risk_score: number | null;
  risk_percentage: number | null;
  decision: boolean | null;
  decision_text: 'Positive' | 'Negative' | 'N/A';
  status_label: AssessmentStatusLabel;
  is_suppressed: boolean;
  explanation: string;
}

export interface FeatureContribution {
  feature_key: string;
  display_name: string;
  scientific_name?: string | null;
  role_description?: string;
  raw_value: any;
  formatted_value: string;
  shap_value: number;
  abs_shap_value: number;
  direction: 'increases_risk' | 'reduces_risk' | 'neutral';
  normal_range?: string;
  relative_impact_percentage: number;
  source_modality?: 'clinical' | 'wearable' | 'gut';
  source_role?: 'primary_contributor' | 'independent_signal';
  source_label?: string;
}

export interface AvailableModelSignal {
  modality: 'clinical' | 'wearable' | 'gut';
  name: string;
  role: 'PRIMARY' | 'INDEPENDENT';
  role_label: 'PRIMARY' | 'INDEPENDENT';
  role_description?: string;
  risk_percentage: number | null;
  decision?: boolean | null;
}

export interface ModalityDetail {
  available: boolean;
  predicted: boolean;
  risk_score: number | null;
  risk_percentage: number | null;
  decision: boolean | null;
  role: 'primary_contributor' | 'independent_signal';
  role_label: 'PRIMARY' | 'INDEPENDENT';
  role_description: string;
  risk_drivers: FeatureContribution[];
  protective_factors: FeatureContribution[];
}

export interface ModalityProvenance {
  type: 'clinical_passthrough' | 'multi_modality_stacker' | 'gut_passthrough' | 'wearable_passthrough' | 'single_modality' | 'suppressed_secondary' | 'insufficient' | 'fallback';
  badge: string;
  primary_modalities: string[];
  headline: string;
  description: string;
  modality_scores?: {
    clinical_risk_percentage?: number | null;
    gut_risk_percentage?: number | null;
    wearable_risk_percentage?: number | null;
  };
  available_signals?: AvailableModelSignal[];
}

export interface SupportingWearableEvidence {
  available: boolean;
  is_mathematical_contributor?: boolean;
  raw_wearable_risk_percentage?: number | null;
  headline?: string;
  notice?: string;
  top_signals?: FeatureContribution[];
}

export interface ModalityBreakdown {
  clinical?: {
    risk_drivers: FeatureContribution[];
    protective_factors: FeatureContribution[];
  };
  wearable?: {
    risk_drivers: FeatureContribution[];
    protective_factors: FeatureContribution[];
  };
  gut?: {
    risk_drivers: FeatureContribution[];
    protective_factors: FeatureContribution[];
  };
}

export interface DiseaseExplanation {
  disease_key: string;
  display_name: string;
  available: boolean;
  risk_percentage: number | null;
  decision: boolean | null;
  is_suppressed: boolean;
  provenance: ModalityProvenance;
  modalities?: {
    clinical?: ModalityDetail;
    wearable?: ModalityDetail;
    gut?: ModalityDetail;
  };
  available_sources?: ('clinical' | 'wearable' | 'gut')[];
  risk_drivers: FeatureContribution[];
  protective_factors: FeatureContribution[];
  supporting_wearable_evidence?: SupportingWearableEvidence;
  modality_breakdown?: ModalityBreakdown | null;
}

export interface XaiResponse {
  default_disease: string | null;
  has_usable_explanations: boolean;
  explanations: Record<string, DiseaseExplanation>;
  error?: string;
}

export interface HealthPlanContributingItem {
  parameter: string;
  friendly_name: string;
  patient_value: any;
  unit: string;
  status: 'above_expected_range' | 'below_expected_range' | 'within_expected_range' | 'interpretation_unavailable';
  explanation_sentence: string;
}

export interface HealthPlanPriority {
  rank: number;
  title: string;
  explanation: string;
}

export interface HealthPlanRecommendationItem {
  title: string;
  priority_rank: number;
  recommendation_text: string;
  numerical_target?: string | null;
}

export interface HealthPlanWhyItem {
  title: string;
  reason: string;
  evidence_source: string;
}

export interface HealthPlanSections {
  section_a_your_results?: {
    title: string;
    body: string;
    evaluated_conditions: Array<{
      disease: string;
      risk_level: string;
      probability_percentage: string;
    }>;
  };
  section_b_what_is_contributing?: {
    title: string;
    body: string;
    contributing_items: HealthPlanContributingItem[];
  };
  section_c_what_to_focus_on_first?: {
    title: string;
    intro: string;
    priorities: HealthPlanPriority[];
  };
  section_d_personalized_recommendations?: {
    title: string;
    intro: string;
    recommendations: HealthPlanRecommendationItem[];
  };
  section_e_why_suggested?: {
    title: string;
    items: HealthPlanWhyItem[];
  };
}

export interface HealthPlanResponse {
  summary_title: string;
  primary_disease_evaluated?: string;
  status?: string;
  message?: string;
  sections?: HealthPlanSections | null;
  total_validated_recommendations?: number;
}

export interface HealthAssessmentResponse {
  patient_id: string;
  patient_name?: string | null;
  patient_age?: number | null;
  patient_gender?: string | null;
  assessment_timestamp: string;
  has_any_usable_data: boolean;
  summary_message: string;
  diseases: AssessmentDiseaseResult[];
  xai?: XaiResponse;
  health_plan?: HealthPlanResponse | null;
}

export interface RunAssessmentRequest {
  contract2: Record<string, any>;
  user_answers?: Record<string, any>;
  patient_id?: string;
}

