export enum DocumentStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export enum DocumentType {
  USER_UPLOADED = 'user_uploaded',
  REGULATORY = 'regulatory',
  POLICY = 'policy',
  MEDICAL_RECORD = 'medical_record',
  CLAIM = 'claim'
}

export interface Document {
  id: string
  user_id: string
  original_filename: string
  file_size: number
  content_type: string
  file_hash: string
  storage_path: string
  document_type: DocumentType
  status: DocumentStatus
  error_message?: string
  structured_contents?: any
  metadata: Record<string, any>
  jurisdiction?: string
  program?: string[]
  effective_date?: string
  expiration_date?: string
  source_url?: string
  tags?: string[]
  created_at: string
  updated_at: string
}

export interface DocumentVector {
  id: string
  document_record_id: string
  user_id: string
  chunk_index: number
  content_embedding: number[]
  encrypted_chunk_text: string
  encrypted_chunk_metadata: string
  encryption_key_id?: string
  created_at: string
  is_active: boolean
} 

export interface ProcessDocumentRequest {
  file: {
    name: string;
    type: string;
    size: number;
    data: string; // base64 encoded file data
  };
  metadata?: {
    documentType?: string;
    tags?: string[];
    [key: string]: unknown;
  };
}

export interface Job {
  id: string;
  document_id: string;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  error_message?: string;
  error_details?: unknown;
  metadata: Record<string, unknown>;
}

export type JobStatus = 
  | 'STARTED'
  | 'UPLOAD_FAILED'
  | 'PARSE_FAILED'
  | 'VECTORIZE_FAILED'
  | 'COMPLETED';

export interface ErrorResponse {
  error: string;
  details?: unknown;
}

export interface SuccessResponse {
  success: true;
  jobId: string;
  documentId: string;
  status: JobStatus;
} 

export interface ProcessDocumentRequest {
  file: {
    name: string;
    type: string;
    size: number;
    data: string; // base64 encoded file data
  };
  metadata?: {
    documentType?: string;
    tags?: string[];
    [key: string]: unknown;
  };
}

export interface Job {
  id: string;
  document_id: string;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  error_message?: string;
  error_details?: unknown;
  metadata: Record<string, unknown>;
}

export type JobStatus = 
  | 'STARTED'
  | 'UPLOAD_FAILED'
  | 'PARSE_FAILED'
  | 'VECTORIZE_FAILED'
  | 'COMPLETED';

export interface ErrorResponse {
  error: string;
  details?: unknown;
}

export interface SuccessResponse {
  success: true;
  jobId: string;
  documentId: string;
  status: JobStatus;
} 