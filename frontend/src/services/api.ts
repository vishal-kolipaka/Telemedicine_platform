import type { DocumentAnalysisResult, HealthAssessmentResponse, RunAssessmentRequest } from '../types/reader';
import type { ProgressPlanRecord } from '../types/progress_plan';

export async function analyzeDocuments(files: File[]): Promise<DocumentAnalysisResult[]> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await fetch('/api/analyze', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to process document(s)' }));
    throw new Error(errorData.detail || `Server error (${response.status})`);
  }

  return await response.json();
}

export async function runHealthAssessment(request: RunAssessmentRequest): Promise<HealthAssessmentResponse> {
  const response = await fetch('/api/run-assessment', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to execute health assessment' }));
    throw new Error(errorData.detail || `Server error (${response.status})`);
  }

  return await response.json();
}

// ── PROGRESS PLAN API SERVICES ───────────────────────────────────────────────

export async function generateProgressPlan(payload: {
  patient_id: string;
  patient_name?: string;
  patient_age?: any;
  patient_gender?: string;
  duration: '1_week' | '1_month' | '3_months';
  health_plan: any;
}): Promise<ProgressPlanRecord> {
  const response = await fetch('/api/progress-plan/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to generate progress plan' }));
    throw new Error(errorData.detail || `Server error (${response.status})`);
  }

  return await response.json();
}

export async function getProgressPlan(planId: string): Promise<ProgressPlanRecord> {
  const response = await fetch(`/api/progress-plan/${planId}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to load progress plan' }));
    throw new Error(errorData.detail || `Server error (${response.status})`);
  }
  return await response.json();
}

export async function toggleProgressPlanTask(
  planId: string,
  taskId: string,
  completed?: boolean
): Promise<ProgressPlanRecord> {
  const response = await fetch(`/api/progress-plan/${planId}/toggle-task`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task_id: taskId, completed }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to update task progress' }));
    throw new Error(errorData.detail || `Server error (${response.status})`);
  }

  return await response.json();
}

export async function resetProgressPlan(planId: string): Promise<ProgressPlanRecord> {
  const response = await fetch(`/api/progress-plan/${planId}/reset`, {
    method: 'POST',
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to reset progress plan' }));
    throw new Error(errorData.detail || `Server error (${response.status})`);
  }

  return await response.json();
}

export async function downloadProgressPlanPdf(planId: string, filename: string = 'progress_plan.pdf'): Promise<void> {
  const response = await fetch(`/api/progress-plan/${planId}/pdf`);
  if (!response.ok) {
    throw new Error('Failed to download PDF');
  }
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
