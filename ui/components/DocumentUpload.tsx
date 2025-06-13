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
  const [uploadMessage, setUploadMessage] = useState<string>("")
  const [uploadSuccess, setUploadSuccess] = useState<boolean>(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  
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
  const handleUpload = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    setUploadProgress(0)
    setUploadMessage("")
    setUploadSuccess(false)
    setUploadError(null)

    try {
      // Immediate progress to show frontend activity
      setUploadMessage("📤 Uploading document...")
      setUploadProgress(20)

      const token = localStorage.getItem("token")
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      
      // Try new backend endpoint first, fallback to existing endpoint
      let uploadUrl = `${apiBaseUrl}/upload-document-backend`
      let uploadResponse = await fetch(uploadUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: (() => {
          const formData = new FormData()
          formData.append('file', selectedFile)
          formData.append('policy_id', selectedFile.name.replace(/\.[^/.]+$/, ""))
          return formData
        })(),
      })

      // If new endpoint not available (405), fallback to existing endpoint
      if (uploadResponse.status === 405) {
        console.log('🔄 New endpoint not deployed yet, using fallback...')
        uploadUrl = `${apiBaseUrl}/upload-policy`
        
        const formData = new FormData()
        formData.append('file', selectedFile)
        formData.append('policy_id', selectedFile.name.replace(/\.[^/.]+$/, ""))

        uploadResponse = await fetch(uploadUrl, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          body: formData,
        })
      }

      if (!uploadResponse.ok) {
        // Enhanced error handling for common issues
        if (uploadResponse.status === 0 || uploadResponse.status === 502) {
          throw new Error(`Connection failed - please check your internet connection and try again. (Status: ${uploadResponse.status})`)
        }
        if (uploadResponse.status === 401) {
          throw new Error(`Authentication failed - please log in again. (Status: ${uploadResponse.status})`)
        }
        if (uploadResponse.status === 403) {
          throw new Error(`Access denied - please check your permissions. (Status: ${uploadResponse.status})`)
        }
        if (uploadResponse.status === 413) {
          throw new Error(`File too large - please upload a smaller document. (Status: ${uploadResponse.status})`)
        }
        
        // Try to get error details from response
        let errorMessage = `Upload failed (Status: ${uploadResponse.status})`
        try {
          const errorData = await uploadResponse.text()
          if (errorData) {
            errorMessage += ` - ${errorData}`
          }
        } catch (e) {
          console.warn("Could not parse error response:", e)
        }
        
        throw new Error(errorMessage)
      }

      const result = await uploadResponse.json()
      
      // Show immediate completion on frontend
      setUploadProgress(100)
      setUploadSuccess(true)
      setUploadMessage(`✅ Document uploaded! Processing continues in background...`)
      
      // Call success handler immediately with upload result
      if (onUploadSuccess) {
        onUploadSuccess({
          success: true,
          document_id: result.document_id || result.id || 'unknown',
          filename: selectedFile.name,
          chunks_processed: 0, // Will be updated via background notification
          total_chunks: 1,
          text_length: 0,
          message: `Document "${selectedFile.name}" uploaded successfully. Background processing will notify you when complete.`
        })
      }

      // Auto-reset after success
      setTimeout(() => {
        resetUpload()
      }, 3000)
      
    } catch (error) {
      console.error("Upload error:", error)
      
      let errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      
      // Detect authentication issues
      if (errorMessage.includes('unauthorized') || errorMessage.includes('401')) {
        errorMessage = `🔐 Authentication failed. Please log in again.`
      }
      
      // Detect file size issues
      if (errorMessage.includes('too large') || errorMessage.includes('413')) {
        errorMessage = `📦 File too large. Please upload a file smaller than 10MB.`
      }
      
      // Detect network issues
      if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
        errorMessage = `🌐 Network connection failed. Please check your internet connection and try again.`
      }
      
      setUploadError(errorMessage)
      setUploadProgress(0)
      setUploadMessage("")
      setIsUploading(false)
      
      if (onUploadError) {
        onUploadError(errorMessage)
      }
    } finally {
      setIsUploading(false)
    }
  }

  // Reset form
  const resetUpload = () => {
    setSelectedFile(null)
    setError(null)
    setUploadResult(null)
    setUploadProgress(0)
    setUploadMessage("")
    setUploadSuccess(false)
    setUploadError(null)
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
              <span className="text-gray-600">{uploadMessage}</span>
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
        {uploadSuccess && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
              <div className="flex-1">
                <p className="font-medium text-green-800">{uploadMessage}</p>
              </div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {uploadError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
              <div className="flex-1">
                <p className="font-medium text-red-800">Upload Failed</p>
                <p className="text-sm text-red-700 mt-1">{uploadError}</p>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-3">
          {selectedFile && !isUploading && !uploadSuccess && !uploadError && (
            <>
              <Button
                onClick={handleUpload}
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
                onClick={resetUpload}
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