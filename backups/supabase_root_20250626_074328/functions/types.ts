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