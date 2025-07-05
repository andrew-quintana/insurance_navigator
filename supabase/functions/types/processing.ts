export interface ProcessingMetadata {
  document_type?: string;
  filename?: string;
  timestamp: string;
  memory_usage: number;
  size?: number;
  content_type?: string;
  chunk_count?: number;
  avg_chunk_size?: number;
  chunks_stored?: number;
  vectors_generated?: number;
  total_chunks?: number;
  total_vectors?: number;
  processing_time?: string;
  error_type?: string;
}

export interface ProcessingLog {
  id: string;
  document_id: string;
  stage: string;
  status: string;
  error_message?: string;
  metadata: ProcessingMetadata;
  created_at: string;
  updated_at: string;
} 