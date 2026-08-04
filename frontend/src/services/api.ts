import type { DocumentAnalysisResult } from '../types/reader';

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
