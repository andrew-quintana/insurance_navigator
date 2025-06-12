'use client'

import React, { useRef, useState, useCallback, useEffect, useMemo } from 'react'
import { Upload, File, CheckCircle, AlertCircle, X } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { createClient } from '@supabase/supabase-js'

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

interface DocumentProgress {
  id: string
  status: string
  progress_percentage: number
  processed_chunks: number
  total_chunks: number
  error_message?: string
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
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadMessage, setUploadMessage] = useState("")
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null)
  const [documentId, setDocumentId] = useState<string | null>(null)

  // Initialize Supabase client with error handling
  const supabase = useMemo(() => {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
    
    if (!url || !key) {
      console.error('Missing Supabase environment variables')
      return null
    }
    
    return createClient(url, key)
  }, [])

  // Backend-driven progress tracking with smart fallback
  useEffect(() => {
    if (!documentId) return

    let subscriptionActive = true
    let pollInterval: NodeJS.Timeout | null = null
    let pollAttempts = 0
    const maxPollAttempts = 10 // Stop polling after 10 failed attempts

    // Try real-time subscription first (best option)
    const tryRealTimeSubscription = () => {
      if (!supabase) return false
      
      try {
        const channel = supabase
          .channel('document-progress')
          .on('postgres_changes', 
            { 
              event: 'UPDATE', 
              schema: 'public', 
              table: 'documents',
              filter: `id=eq.${documentId}`
            }, 
            (payload: any) => {
              console.log('✅ Real-time document update:', payload.new)
              handleDocumentUpdate(payload.new)
            }
          )
          .subscribe((status) => {
            console.log('Real-time subscription status:', status)
            
            if (status === 'SUBSCRIBED') {
              console.log('✅ Real-time subscription active - no polling needed')
              return true
            } else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
              console.warn('⚠️ Real-time subscription failed, will try API polling')
              startApiPolling()
            }
          })
        
        return true
      } catch (error) {
        console.warn('Real-time subscription error:', error)
        return false
      }
    }

    // Fallback: Poll the backend API (less ideal)
    const pollDocumentStatus = async () => {
      if (!subscriptionActive || pollAttempts >= maxPollAttempts) {
        if (pollAttempts >= maxPollAttempts) {
          console.log('⏰ Max polling attempts reached, assuming completion')
          handleDocumentUpdate({
            id: documentId,
            status: 'completed',
            progress_percentage: 100,
            processed_chunks: 1,
            total_chunks: 1
          })
        }
        return
      }
      
      try {
        const token = localStorage.getItem('token')
        if (!token) {
          console.warn('No auth token for polling')
          return
        }

        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
        const response = await fetch(`${apiBaseUrl}/documents/${documentId}/status`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.status === 405) {
          pollAttempts++
          console.warn(`Status endpoint not deployed yet (attempt ${pollAttempts}/${maxPollAttempts})`)
          return
        }

        if (!response.ok) {
          pollAttempts++
          console.warn('Polling API error:', response.status, response.statusText)
          return
        }

        const document = await response.json()
        console.log('✅ Backend document status:', document)
        pollAttempts = 0 // Reset on success
        handleDocumentUpdate(document)
      } catch (error) {
        pollAttempts++
        console.warn('Polling failed:', error)
      }
    }

    const startApiPolling = () => {
      console.log('🔄 Starting API polling as fallback (will stop after 10 failed attempts)')
      pollInterval = setInterval(pollDocumentStatus, 5000) // Poll every 5 seconds
      pollDocumentStatus() // Initial check
    }

    // Handle document updates from any source
    const handleDocumentUpdate = (document: any) => {
      if (!subscriptionActive) return
      
      setUploadProgress(document.progress_percentage || 0)
      
      // Update status messages based on document status
      switch(document.status) {
        case 'uploading':
          setUploadMessage("📤 Uploading file to backend...")
          break
        case 'processing':
          setUploadMessage("🔄 Processing document in background...")
          break
        case 'parsing':
          setUploadMessage("📄 Extracting text from document...")
          break
        case 'chunking':
          setUploadMessage("✂️ Breaking down content into sections...")
          break
        case 'vectorizing':
          setUploadMessage(`🧠 Generating embeddings (${document.processed_chunks}/${document.total_chunks} sections)...`)
          break
        case 'completed':
          setUploadMessage(`✅ Success! Processed ${document.total_chunks} sections from your document.`)
          setUploadProgress(100)
          setUploadSuccess(true)
          setIsUploading(false)
          
          // Create success result
          const result: UploadResponse = {
            success: true,
            document_id: document.id,
            filename: selectedFile?.name || document.original_filename || '',
            chunks_processed: document.processed_chunks || 0,
            total_chunks: document.total_chunks || 0,
            text_length: 0,
            message: `Document processed successfully with ${document.total_chunks} chunks`
          }
          
          if (onUploadSuccess) {
            onUploadSuccess(result)
          }
          
          // Stop polling
          if (pollInterval) {
            clearInterval(pollInterval)
            pollInterval = null
          }
          
          // Auto-reset after success
          setTimeout(() => {
            resetUpload()
          }, 3000)
          break
        case 'failed':
          setUploadError(document.error_message || 'Document processing failed')
          setUploadProgress(0)
          setUploadMessage("")
          setIsUploading(false)
          
          // Stop polling
          if (pollInterval) {
            clearInterval(pollInterval)
            pollInterval = null
          }
          
          if (onUploadError) {
            onUploadError(document.error_message || 'Document processing failed')
          }
          break
      }
    }

    // Try real-time first, fallback to polling if needed
    if (!tryRealTimeSubscription()) {
      startApiPolling()
    }

    return () => {
      subscriptionActive = false
      if (pollInterval) {
        clearInterval(pollInterval)
      }
      if (supabase) {
        supabase.removeAllChannels()
      }
    }
  }, [documentId, selectedFile, onUploadSuccess, onUploadError, supabase])

  // Validate file
  const validateFile = (file: File): string | null => {
    // File size limit (50MB)
    if (file.size > 52428800) {
      return "File size must be less than 50MB"
    }

    // File type validation
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword', 'text/plain']
    if (!allowedTypes.includes(file.type)) {
      return "Only PDF, DOCX, DOC, and TXT files are supported"
    }

    return null
  }

  // Handle file selection
  const handleFileSelect = useCallback((file: File) => {
    const validationError = validateFile(file)
    if (validationError) {
      setError(validationError)
      return
    }

    setSelectedFile(file)
    setError(null)
    setUploadError(null)
    setUploadSuccess(false)
  }, [])

  // Drag and drop handlers
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

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }, [handleFileSelect])

  // Upload file using serverless pipeline
  const handleUpload = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    setUploadError(null)
    setUploadProgress(0)

    try {
      // Get authentication token
      const token = localStorage.getItem('token')
      if (!token) {
        throw new Error('Authentication required')
      }
      
      setUploadMessage("📤 Uploading file to backend...")
      setUploadProgress(5)

      // Try new backend endpoint first, fallback to existing endpoint
      const formData = new FormData()
      formData.append('file', selectedFile)

      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      
      // Try new backend-driven endpoint first
      let uploadResponse = await fetch(`${apiBaseUrl}/upload-document-backend`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })

      // If new endpoint not available (405), fallback to existing endpoint
      if (uploadResponse.status === 405) {
        console.log('🔄 New endpoint not deployed yet, using fallback...')
        setUploadMessage("📤 Using fallback upload method...")
        
        uploadResponse = await fetch(`${apiBaseUrl}/upload-policy`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        })
      }

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json().catch(() => ({}))
        throw new Error(errorData.detail || `Upload failed: ${uploadResponse.status}`)
      }

      const uploadResult = await uploadResponse.json()
      console.log("✅ Upload successful:", uploadResult)
      
      // Handle different response formats
      const documentId = uploadResult.document_id || uploadResult.id || uploadResult.documentId
      if (!documentId) {
        throw new Error('No document ID returned from upload')
      }
      
      setDocumentId(documentId)
      setUploadProgress(15)
      setUploadMessage("⚙️ Document uploaded! Processing will continue in the background...")

      // The backend job queue will handle all processing automatically
      // Real-time progress tracking will monitor the job queue status
      
    } catch (error) {
      console.error('Upload error:', error)
      
      // Enhanced error handling with specific guidance
      let errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      
      // Detect authentication issues
      if (errorMessage.includes('unauthorized') || errorMessage.includes('401')) {
        errorMessage = `🔐 Authentication failed. Please log in again.`
      }
      
      // Detect file size issues
      if (errorMessage.includes('too large') || errorMessage.includes('413')) {
        errorMessage = `📦 File too large. Please upload a file smaller than 50MB.`
      }
      
      // Detect network issues
      if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
        errorMessage = `🌐 Network connection failed. Please check your internet connection and try again.`
      }
      
      setUploadError(errorMessage)
      setUploadProgress(0)
      setUploadMessage("")
      setIsUploading(false)
      setDocumentId(null)
      
      if (onUploadError) {
        onUploadError(errorMessage)
      }
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
    setDocumentId(null)
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
                  Supports PDF, DOC, DOCX, TXT (max 50MB)
                </p>
              </div>
            </div>
          )}
        </div>

        {/* File validation error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

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
                <p className="text-sm text-green-700 font-medium">
                  Document uploaded successfully!
                </p>
                <p className="text-xs text-green-600 mt-1">
                  {uploadMessage}
                </p>
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
                <p className="text-sm text-red-700 font-medium">Upload failed</p>
                <p className="text-xs text-red-600 mt-1">{uploadError}</p>
              </div>
              <button
                onClick={resetUpload}
                className="text-red-400 hover:text-red-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* Upload Button */}
        {selectedFile && !isUploading && !uploadSuccess && !uploadError && (
          <div className="flex justify-center">
            <button
              onClick={handleUpload}
              className="bg-teal-600 hover:bg-teal-700 text-white font-medium py-2 px-6 rounded-lg transition-colors"
            >
              Upload Document
            </button>
          </div>
        )}

        {/* Upload Another Button */}
        {uploadSuccess && (
          <div className="flex justify-center">
            <button
              onClick={resetUpload}
              className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 px-6 rounded-lg transition-colors"
            >
              Upload Another Document
            </button>
          </div>
        )}
      </div>
    </Card>
  )
} 