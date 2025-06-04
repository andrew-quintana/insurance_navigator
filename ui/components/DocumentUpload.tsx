'use client'

import React, { useState, useRef, useCallback } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Upload, File, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'

interface UploadResponse {
  success: boolean
  document_id: string
  filename: string
  chunks_processed: number
  total_chunks: number
  text_length: number
  message: string
}

interface DocumentUploadProps {
  onUploadSuccess?: (result: UploadResponse) => void
  onUploadError?: (error: string) => void
  className?: string
}

export default function DocumentUpload({ 
  onUploadSuccess, 
  onUploadError,
  className = ""
}: DocumentUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  // File validation
  const validateFile = (file: File): string | null => {
    const maxSize = 10 * 1024 * 1024 // 10MB
    const allowedTypes = [
      'application/pdf',
      'text/plain',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword'
    ]

    if (file.size > maxSize) {
      return 'File size must be less than 10MB'
    }

    if (!allowedTypes.includes(file.type)) {
      return 'Only PDF, DOC, DOCX, and TXT files are supported'
    }

    return null
  }

  // Handle file selection
  const handleFileSelect = useCallback((file: File) => {
    const validation = validateFile(file)
    if (validation) {
      setError(validation)
      return
    }

    setSelectedFile(file)
    setError(null)
    setUploadResult(null)
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

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }, [handleFileSelect])

  // Handle file input change
  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileSelect(files[0])
    }
  }, [handleFileSelect])

  // Upload file to backend
  const uploadFile = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    setUploadProgress(0)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      // Get API URL from environment
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      const uploadUrl = `${apiBaseUrl}/upload-policy`

      // Get auth token
      const token = localStorage.getItem('token')
      if (!token) {
        throw new Error('Authentication required')
      }

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90))
      }, 200)

      const response = await fetch(uploadUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      })

      clearInterval(progressInterval)
      setUploadProgress(100)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Upload failed with status ${response.status}`)
      }

      const result: UploadResponse = await response.json()
      setUploadResult(result)
      onUploadSuccess?.(result)

      // Reset form after successful upload
      setTimeout(() => {
        setSelectedFile(null)
        setUploadProgress(0)
        setUploadResult(null)
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
      }, 3000)

    } catch (error) {
      console.error('Upload error:', error)
      const errorMessage = error instanceof Error ? error.message : 'Upload failed'
      setError(errorMessage)
      onUploadError?.(errorMessage)
    } finally {
      setIsUploading(false)
    }
  }

  // Reset form
  const resetForm = () => {
    setSelectedFile(null)
    setError(null)
    setUploadResult(null)
    setUploadProgress(0)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <Card className={`p-6 ${className}`}>
      <div className="space-y-4">
        <div className="text-center">
          <h3 className="text-lg font-semibold text-teal-800 mb-2">
            Upload Insurance Document
          </h3>
          <p className="text-sm text-gray-600">
            Upload your Medicare, insurance policy, or related documents for personalized assistance
          </p>
        </div>

        {/* Drag and Drop Area */}
        <div
          className={`
            border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer
            ${isDragOver 
              ? 'border-teal-500 bg-teal-50' 
              : 'border-gray-300 hover:border-teal-400 hover:bg-teal-50'
            }
            ${selectedFile ? 'border-teal-500 bg-teal-50' : ''}
          `}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.doc,.docx,.txt"
            onChange={handleFileInputChange}
            className="hidden"
          />

          {selectedFile ? (
            <div className="space-y-2">
              <File className="h-12 w-12 text-teal-600 mx-auto" />
              <div>
                <p className="font-medium text-teal-800">{selectedFile.name}</p>
                <p className="text-sm text-gray-600">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              <Upload className="h-12 w-12 text-gray-400 mx-auto" />
              <div>
                <p className="text-gray-600">
                  Drag and drop your document here, or <span className="text-teal-600 font-medium">browse</span>
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Supports PDF, DOC, DOCX, TXT (max 10MB)
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Upload Progress */}
        {isUploading && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Uploading and processing...</span>
              <span className="text-teal-600">{uploadProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-teal-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Success Message */}
        {uploadResult && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
              <div className="flex-1">
                <p className="font-medium text-green-800">Upload Successful!</p>
                <p className="text-sm text-green-700 mt-1">
                  {uploadResult.message}
                </p>
                <div className="text-xs text-green-600 mt-2 space-y-1">
                  <p>• Processed {uploadResult.chunks_processed} text chunks</p>
                  <p>• Document ID: {uploadResult.document_id}</p>
                  <p>• Text length: {uploadResult.text_length.toLocaleString()} characters</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
              <div className="flex-1">
                <p className="font-medium text-red-800">Upload Failed</p>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-3">
          {selectedFile && !isUploading && !uploadResult && (
            <>
              <Button
                onClick={uploadFile}
                className="flex-1 bg-teal-700 hover:bg-teal-800 text-white"
                disabled={isUploading}
              >
                {isUploading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4 mr-2" />
                    Upload Document
                  </>
                )}
              </Button>
              <Button
                onClick={resetForm}
                variant="outline"
                className="text-gray-600 border-gray-300"
                disabled={isUploading}
              >
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>
            </>
          )}
        </div>
      </div>
    </Card>
  )
} 