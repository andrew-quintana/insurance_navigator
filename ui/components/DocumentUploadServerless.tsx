'use client'

import React, { useRef, useState, useCallback, useEffect } from 'react'
import { Upload, File, CheckCircle, AlertCircle, X, Clock } from 'lucide-react'
import { Card } from '@/components/ui/card'

interface UploadResponse {
  success: boolean
  document_id: string
  filename: string
  chunks_processed: number
  total_chunks: number
  text_length: number
  message: string
}

interface FileUploadStatus {
  file: File
  status: 'pending' | 'uploading' | 'complete' | 'error'
  progress: number
  documentId?: string
  error?: string
}

interface DocumentUploadProps {
  onUploadSuccess?: (result: UploadResponse) => void
  onUploadError?: (error: string) => void
  className?: string
}

export default function DocumentUploadServerless({ 
  onUploadSuccess, 
  onUploadError,
  className = ""
}: DocumentUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedFiles, setSelectedFiles] = useState<FileUploadStatus[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // File validation
  const validateFile = (file: File): string | null => {
    const maxSize = 50 * 1024 * 1024 // 50MB
    const allowedTypes = [
      'application/pdf',
      'text/plain',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword'
    ]

    if (file.size > maxSize) {
      return 'File size must be less than 50MB'
    }

    if (!allowedTypes.includes(file.type)) {
      return 'Only PDF, DOC, DOCX, and TXT files are supported'
    }

    return null
  }

  // Handle file selection for multiple files
  const handleFileSelect = useCallback((files: File[]) => {
    const newFiles = files.map(file => {
      const validation = validateFile(file)
      if (validation) {
        return {
          file,
          status: 'error' as const,
          progress: 0,
          error: validation
        }
      }
      return {
        file,
        status: 'pending' as const,
        progress: 0
      }
    })

    setSelectedFiles(prev => [...prev, ...newFiles])
    setError(null)
  }, [])

  // Handle drag events
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  // Update drop handler for multiple files
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileSelect(files)
    }
  }, [handleFileSelect])

  // Update file input change handler for multiple files
  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileSelect(Array.from(files))
    }
  }, [handleFileSelect])

  // Upload single file
  const uploadFile = async (fileStatus: FileUploadStatus): Promise<UploadResponse> => {
    const token = localStorage.getItem("token")
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
    
    const formData = new FormData()
    formData.append('file', fileStatus.file)
    formData.append('policy_id', fileStatus.file.name.replace(/\.[^/.]+$/, ""))
    
    const uploadResponse = await fetch(`${apiBaseUrl}/upload-document-backend`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    })

    if (!uploadResponse.ok) {
      const errorText = await uploadResponse.text()
      throw new Error(`Upload failed: ${uploadResponse.status} - ${errorText}`)
    }

    const result = await uploadResponse.json()
    return {
      success: true,
      document_id: result.document_id || result.id || 'unknown',
      filename: fileStatus.file.name,
      chunks_processed: result.chunks_processed || 1,
      total_chunks: result.total_chunks || 1,
      text_length: result.text_length || 0,
      message: result.message || 'Document processed successfully!'
    }
  }

  // Upload all files
  const handleUpload = async () => {
    if (selectedFiles.length === 0) return
    if (isUploading) return

    setIsUploading(true)
    setError(null)

    // Update all pending files to uploading status
    setSelectedFiles(prev => prev.map(file => 
      file.status === 'pending' ? { ...file, status: 'uploading', progress: 0 } : file
    ))

    try {
      // Upload files sequentially to avoid overwhelming the server
      for (const fileStatus of selectedFiles) {
        if (fileStatus.status !== 'uploading') continue

        try {
          const result = await uploadFile(fileStatus)
          
          // Update file status to complete
          setSelectedFiles(prev => prev.map(f => 
            f.file === fileStatus.file 
              ? { ...f, status: 'complete', progress: 100, documentId: result.document_id }
              : f
          ))

          // Call success handler for each file
          if (onUploadSuccess) {
            onUploadSuccess(result)
          }
        } catch (err) {
          console.error('File upload failed:', err)
          const error = err instanceof Error ? err.message : 'Unknown error occurred'
          
          // Update file status to error
          setSelectedFiles(prev => prev.map(f => 
            f.file === fileStatus.file 
              ? { ...f, status: 'error', progress: 0, error }
              : f
          ))

          // Call error handler
          if (onUploadError) {
            onUploadError(`Failed to upload ${fileStatus.file.name}: ${error}`)
          }
        }
      }
    } finally {
      setIsUploading(false)
    }
  }

  const removeFile = (file: File) => {
    setSelectedFiles(prev => prev.filter(f => f.file !== file))
  }

  const resetUpload = () => {
    setSelectedFiles([])
    setError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <Card className={`p-6 ${className}`}>
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center ${
          isDragOver ? 'border-teal-500 bg-teal-50' : 'border-gray-300'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileInputChange}
          className="hidden"
          multiple
          accept=".pdf,.doc,.docx,.txt"
        />

        <Upload className="mx-auto h-12 w-12 text-gray-400" />
        
        <h3 className="mt-4 text-lg font-semibold text-gray-900">
          Upload Your Documents
        </h3>
        
        <p className="mt-2 text-sm text-gray-600">
          Drag and drop your files here, or{' '}
          <button
            type="button"
            className="text-teal-600 hover:text-teal-500 font-medium"
            onClick={() => fileInputRef.current?.click()}
          >
            browse
          </button>
        </p>
        
        <p className="mt-1 text-xs text-gray-500">
          PDF, DOC, DOCX or TXT up to 50MB
        </p>
      </div>

      {/* File List */}
      {selectedFiles.length > 0 && (
        <div className="mt-4 space-y-3">
          {selectedFiles.map((fileStatus) => (
            <div
              key={fileStatus.file.name}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center space-x-3">
                <File className="h-5 w-5 text-gray-400" />
                <div>
                  <p className="text-sm font-medium text-gray-900">{fileStatus.file.name}</p>
                  <p className="text-xs text-gray-500">
                    {(fileStatus.file.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                {fileStatus.status === 'pending' && (
                  <button
                    onClick={() => removeFile(fileStatus.file)}
                    className="text-gray-400 hover:text-gray-500"
                  >
                    <X className="h-5 w-5" />
                  </button>
                )}
                
                {fileStatus.status === 'uploading' && (
                  <Clock className="h-5 w-5 text-teal-500 animate-spin" />
                )}
                
                {fileStatus.status === 'complete' && (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                )}
                
                {fileStatus.status === 'error' && (
                  <div className="flex items-center space-x-1 text-red-500">
                    <AlertCircle className="h-5 w-5" />
                    <span className="text-xs">{fileStatus.error}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-lg flex items-center">
          <AlertCircle className="h-5 w-5 mr-2" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {/* Upload Button */}
      {selectedFiles.length > 0 && (
        <div className="mt-4 flex justify-end space-x-3">
          <button
            onClick={resetUpload}
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-800"
            disabled={isUploading}
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={isUploading || selectedFiles.every(f => f.status === 'complete')}
            className={`px-4 py-2 rounded-md text-sm font-medium text-white ${
              isUploading
                ? 'bg-teal-400 cursor-not-allowed'
                : 'bg-teal-600 hover:bg-teal-700'
            }`}
          >
            {isUploading ? 'Uploading...' : 'Upload Files'}
          </button>
        </div>
      )}
    </Card>
  )
} 