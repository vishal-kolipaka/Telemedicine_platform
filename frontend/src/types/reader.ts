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
