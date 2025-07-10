-- Add new status values to the enum one at a time
ALTER TYPE "documents"."document_processing_status" ADD VALUE IF NOT EXISTS 'parsing';
ALTER TYPE "documents"."document_processing_status" ADD VALUE IF NOT EXISTS 'parsing-failed';
ALTER TYPE "documents"."document_processing_status" ADD VALUE IF NOT EXISTS 'chunking';
ALTER TYPE "documents"."document_processing_status" ADD VALUE IF NOT EXISTS 'chunking-failed';
ALTER TYPE "documents"."document_processing_status" ADD VALUE IF NOT EXISTS 'embedding';
ALTER TYPE "documents"."document_processing_status" ADD VALUE IF NOT EXISTS 'embedding-failed';