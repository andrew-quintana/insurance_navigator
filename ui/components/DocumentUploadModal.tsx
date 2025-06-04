'use client'

import React from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import DocumentUpload from './DocumentUpload'

interface UploadResponse {
  success: boolean
  document_id: string
  filename: string
  chunks_processed: number
  total_chunks: number
  text_length: number
  message: string
}

interface DocumentUploadModalProps {
  isOpen: boolean
  onClose: () => void
  onUploadSuccess?: (result: UploadResponse) => void
  onUploadError?: (error: string) => void
}

export default function DocumentUploadModal({
  isOpen,
  onClose,
  onUploadSuccess,
  onUploadError
}: DocumentUploadModalProps) {
  const handleUploadSuccess = (result: UploadResponse) => {
    onUploadSuccess?.(result)
    // Auto-close modal after 2 seconds on successful upload
    setTimeout(() => {
      onClose()
    }, 2000)
  }

  const handleUploadError = (error: string) => {
    onUploadError?.(error)
    // Keep modal open on error so user can retry
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-teal-800">
            Upload Your Insurance Documents
          </DialogTitle>
        </DialogHeader>
        
        <DocumentUpload
          onUploadSuccess={handleUploadSuccess}
          onUploadError={handleUploadError}
          className="border-0 shadow-none"
        />
      </DialogContent>
    </Dialog>
  )
} 