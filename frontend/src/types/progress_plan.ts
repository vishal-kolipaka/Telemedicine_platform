export interface ProgressPlanTask {
  id: string;
  title: string;
  category: string;
  priority_pillar: string;
  instruction: string;
  suggestion: string;
  why_selected: string;
  completion_required: boolean;
  recommendation_source: string;
  target?: string;
}

export interface ProgressPlanDay {
  day_number: number;
  week_number?: number;
  phase_number?: number;
  day_in_week?: number;
  title: string;
  focus_theme: string;
  tasks_count: number;
  tasks: ProgressPlanTask[];
  is_unlocked: boolean;
  is_completed: boolean;
}

export interface ProgressPlanWeek {
  week_number: number;
  title: string;
  subtitle?: string;
  days: ProgressPlanDay[];
}

export interface ProgressPlanPhase {
  phase_number: number;
  title: string;
  weeks_label?: string;
  subtitle?: string;
  weeks?: ProgressPlanWeek[];
  days?: ProgressPlanDay[];
}

export interface ProgressPlanData {
  plan_id: string;
  duration: '1_week' | '1_month' | '3_months';
  duration_label: string;
  total_days: number;
  total_weeks: number;
  total_tasks: number;
  patient_info: {
    patient_id?: string;
    name?: string;
    patient_name?: string;
    age?: number | string;
    gender?: string;
  };
  priority_pillars: string[];
  guideline_targets: Record<string, string>;
  phases?: ProgressPlanPhase[];
  weeks?: ProgressPlanWeek[];
  days: ProgressPlanDay[];
}

export interface ProgressPlanRecord {
  plan_id: string;
  patient_id: string;
  duration: '1_week' | '1_month' | '3_months';
  plan_data: ProgressPlanData;
  total_tasks: number;
  current_day: number;
  completed_tasks: string[];
  completed_days: number[];
  overall_progress: number;
  created_at: string;
  updated_at: string;
}
