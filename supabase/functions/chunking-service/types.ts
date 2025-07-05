export interface ChunkMetadata {
  document_id: string;
  section_title: string;
  section_level: number;
  chunk_index: number;
  total_chunks: number;
  start_char: number;
  end_char: number;
} 