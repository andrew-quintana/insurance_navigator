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
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadStartTime, setUploadStartTime] = useState<Date | null>(null)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState(300) // 5 minutes in seconds
  const [isComplete, setIsComplete] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [documentId, setDocumentId] = useState<string | null>(null)

  // Smart timer that moves faster to 85% and stops there until backend responds
  useEffect(() => {
    let interval: NodeJS.Timeout
    
    if (isUploading && uploadStartTime && !isComplete) {
      interval = setInterval(() => {
        const now = new Date()
        const elapsed = Math.floor((now.getTime() - uploadStartTime.getTime()) / 1000)
        setElapsedTime(elapsed)
      
        // Faster progression to 85% - reaches 85% in about 2 minutes instead of 4.25 minutes
        // This gives better visual feedback while staying realistic
        const progressToEightyFive = Math.min(85, (elapsed / 120) * 85)
        
        // Don't automatically complete - wait for backend response
        // Only set estimatedTimeRemaining based on how close we are to 85%
        const remaining = Math.max(0, Math.round((85 - progressToEightyFive) / 85 * 120))
        setEstimatedTimeRemaining(remaining)
        
        // Fallback: if 5 minutes pass and still no response, assume failure
        if (elapsed >= 300) {
          setUploadError("Upload took longer than expected. Please try again.")
          setIsUploading(false)
        }
      }, 1000)
        }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isUploading, uploadStartTime, isComplete])

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

  // Handle file selection
  const handleFileSelect = useCallback((file: File) => {
    const validation = validateFile(file)
    if (validation) {
      setError(validation)
      return
    }

    setSelectedFile(file)
    setError(null)
    setUploadSuccess(false)
    setUploadError(null)
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
    setUploadStartTime(new Date())
    setElapsedTime(0)
    setEstimatedTimeRemaining(300) // Reset to 5 minutes
    setIsComplete(false)
    setUploadSuccess(false)
    setUploadError(null)

    try {
      const token = localStorage.getItem("token")
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      
      // Create form data
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('policy_id', selectedFile.name.replace(/\.[^/.]+$/, ""))
      
      // Upload to backend
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
      console.log('✅ Upload response received:', result)
      
      // Store document ID for reference
      setDocumentId(result.document_id || result.id || 'unknown')
      
      // Complete upload immediately when backend responds (success or failure)
      setIsComplete(true)
      
      // Check if processing actually succeeded
      if (result.success) {
        // Give a brief moment for progress bar to animate to 100%, then show success
        setTimeout(() => {
          setUploadSuccess(true)
          setIsUploading(false)
          setEstimatedTimeRemaining(0)
          
          // Call success handler
          if (onUploadSuccess) {
            onUploadSuccess({
              success: true,
              document_id: result.document_id || result.id || 'unknown',
              filename: selectedFile.name,
              chunks_processed: 1,
              total_chunks: 1,
              text_length: 0,
              message: result.message || 'Document processed successfully!'
            })
          }
        }, 1500) // 1.5-second animation delay for polished completion effect
      } else {
        // Backend reported processing failure - immediately show error and stop progress bar
        setUploadError(result.message || 'Document processing failed')
        setIsUploading(false)
        setIsComplete(false) // Don't trigger completion animation
        setEstimatedTimeRemaining(0)
        
        // Call error handler
        if (onUploadError) {
          onUploadError(result.message || 'Document processing failed')
        }
      }
      
    } catch (error) {
      console.error("Upload error:", error)
      
      let errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      
      // Detect common error types
      if (errorMessage.includes('unauthorized') || errorMessage.includes('401')) {
        errorMessage = '🔐 Authentication failed. Please log in again.'
      } else if (errorMessage.includes('too large') || errorMessage.includes('413')) {
        errorMessage = '📦 File too large. Please upload a file smaller than 50MB.'
      } else if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
        errorMessage = '🌐 Network connection failed. Please check your internet connection and try again.'
      }
      
      setUploadError(errorMessage)
      setIsUploading(false)
      setUploadStartTime(null)
      setElapsedTime(0)
      
      if (onUploadError) {
        onUploadError(errorMessage)
      }
    }
  }

  // Format time display
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Reset form
  const resetUpload = () => {
    setSelectedFile(null)
    setError(null)
    setIsUploading(false)
    setUploadSuccess(false)
    setUploadError(null)
    setDocumentId(null)
    setUploadStartTime(null)
    setElapsedTime(0)
    setEstimatedTimeRemaining(300)
    setIsComplete(false)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <Card className={`p-8 max-w-2xl mx-auto ${className}`}>
      <div className="space-y-6">
        
        {/* Title */}
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload Your Document</h2>
          <p className="text-gray-600">Processing typically takes 3-5 minutes</p>
        </div>

        {/* File Selection Area */}
        {!selectedFile && !isUploading && !uploadSuccess && !uploadError && (
        <div
          className={`
              border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer
            ${isDragOver 
              ? 'border-teal-500 bg-teal-50' 
              : 'border-gray-300 hover:border-teal-400 hover:bg-teal-50'
            }
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

            <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-4">Choose your insurance document</p>
            <p className="text-sm text-gray-500">
              Supports PDF, DOC, DOCX, TXT (max 50MB)
            </p>
          </div>
        )}

        {/* Selected File Display */}
        {selectedFile && !isUploading && !uploadSuccess && !uploadError && (
          <div className="space-y-4">
            <div className="flex items-center justify-center space-x-3 p-4 bg-teal-50 rounded-lg">
              <File className="h-6 w-6 text-teal-600" />
              <div className="text-center">
                <p className="font-medium text-teal-800">{selectedFile.name}</p>
                <p className="text-sm text-teal-600">
                  {(selectedFile.size / 1024 / 1024).toFixed(1)} MB
                </p>
              </div>
        </div>

            <div className="flex space-x-3">
              <button
                onClick={handleUpload}
                className="flex-1 bg-teal-600 hover:bg-teal-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
              >
                Start Processing
              </button>
              <button
                onClick={resetUpload}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Change File
              </button>
            </div>
          </div>
        )}

        {/* Processing State */}
        {isUploading && (
          <div className="space-y-6">
            <div className="flex items-center justify-center space-x-3">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
              <span className="text-lg font-medium text-gray-800">Processing your document...</span>
            </div>
            
            {/* Smart Progress Bar */}
            <div className="bg-gray-50 rounded-lg p-6 space-y-4">
              <div className="w-full bg-gray-200 rounded-full h-4">
              <div 
                  className="bg-gradient-to-r from-teal-500 to-teal-600 h-4 rounded-full transition-all duration-1000 ease-out"
                  style={{ 
                    width: `${isComplete ? 100 : Math.min(85, Math.max(5, (elapsedTime / 120) * 85 + 5))}%` 
                  }}
                ></div>
              </div>
              
              <p className="text-center text-gray-600">
                Analyzing and processing your document...
              </p>
            </div>
            
            <p className="text-sm text-gray-500 text-center">
              You can safely close this window. Processing continues in the background.
            </p>
          </div>
        )}

        {/* Success State */}
        {uploadSuccess && (
          <div className="space-y-4 text-center">
            <div className="flex items-center justify-center space-x-3 text-green-600">
              <CheckCircle className="h-8 w-8" />
              <span className="text-lg font-medium">Document Ready!</span>
            </div>
            
            <p className="text-gray-600">
              Your document has been processed and is ready for use.
            </p>
            
            <div className="flex space-x-3">
              <button 
                className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
                onClick={() => {
                  // Navigate to chat or wherever appropriate
                  console.log('Navigate to chat')
                }}
              >
                Start Chatting
              </button>
              <button 
                onClick={resetUpload}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Upload Another
              </button>
            </div>
          </div>
        )}

        {/* Error State */}
        {uploadError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-red-700 font-medium">Upload failed</p>
                <p className="text-xs text-red-600 mt-1 break-words">{uploadError}</p>
                
                <div className="flex flex-wrap gap-2 mt-3">
                  <button
                    onClick={resetUpload}
                    className="text-xs bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1 rounded transition-colors"
                  >
                    Try Again
                  </button>
                  <button
                    onClick={() => setUploadError(null)}
                    className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded transition-colors"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
              
              <button
                onClick={() => setUploadError(null)}
                className="text-red-400 hover:text-red-600 flex-shrink-0"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* File validation error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

      </div>
    </Card>
  )
} 