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
  const [recentUploads, setRecentUploads] = useState<any[]>([])
  const [showRecentUploads, setShowRecentUploads] = useState(false)

  // ✅ CRITICAL FIX: Global Supabase singleton to prevent multiple instances
  const supabase = useMemo(() => {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
    
    if (!url || !key) {
      console.error('Missing Supabase environment variables')
      return null
    }
    
    // Use global singleton pattern to prevent multiple GoTrueClient instances
    const globalKey = '__insurance_navigator_supabase_client'
    
    // Check if we already have a client instance
    if (typeof window !== 'undefined' && (window as any)[globalKey]) {
      console.log('📡 Reusing existing Supabase client')
      return (window as any)[globalKey]
    }
    
    console.log('🔧 Creating new Supabase client')
    const client = createClient(url, key, {
      realtime: {
        params: {
          eventsPerSecond: 1, // Further reduced to prevent overload
        },
        heartbeatIntervalMs: 30000, // 30 second heartbeat
        reconnectAfterMs: (tries: number) => Math.min(tries * 5000, 30000), // Less aggressive reconnection
      },
      auth: {
        persistSession: false, // Disable session persistence to prevent conflicts
        detectSessionInUrl: false,
        autoRefreshToken: false,
        storage: undefined // Disable auth storage completely
      },
      global: {
        headers: {
          'X-Client-Info': 'insurance-navigator-upload/1.0.0'
        }
      }
    })
    
    // Store in global scope to prevent multiple instances
    if (typeof window !== 'undefined') {
      (window as any)[globalKey] = client
    }
    
    return client
  }, [])

  // Load recent uploads on component mount
  useEffect(() => {
    const loadRecentUploads = async () => {
      if (!supabase) return
      
      try {
        const { data: documents, error } = await supabase
          .from('documents')
          .select('id, original_filename, status, created_at, file_size')
          .order('created_at', { ascending: false })
          .limit(5)
        
        if (!error && documents) {
          setRecentUploads(documents)
        }
      } catch (error) {
        console.warn('Could not load recent uploads:', error)
      }
    }

    loadRecentUploads()
  }, [supabase])

  // ✅ IMPROVED: More reliable progress tracking with better fallback
  useEffect(() => {
    if (!documentId || !supabase) return

    let subscriptionActive = true
    let timeoutId: NodeJS.Timeout
    let fallbackIntervalId: NodeJS.Timeout
    let retryCount = 0
    const maxRetries = 3

    console.log('🔄 Setting up real-time subscription for document:', documentId)

    // Improved fallback polling with exponential backoff
    const startFallbackPolling = () => {
      console.log('🚨 WebSocket failed, starting smart fallback polling...')
      setUploadMessage("⚙️ Processing in background - checking progress...")
      
      const pollInterval = Math.min(3000 + (retryCount * 2000), 10000) // 3s -> 5s -> 7s -> max 10s
      
      fallbackIntervalId = setInterval(async () => {
        if (!subscriptionActive) return
        
        try {
          const { data: document, error } = await supabase
            .from('documents')
            .select('id, status, progress_percentage, error_message, original_filename, created_at')
            .eq('id', documentId)
            .single()
          
          if (!error && document) {
            handleDocumentUpdate(document)
            
            // Stop polling if document is completed or failed
            if (document.status === 'completed' || document.status === 'failed') {
              clearInterval(fallbackIntervalId)
            }
          } else {
            retryCount++
            if (retryCount >= maxRetries) {
              console.error('Max retries reached for document polling')
              clearInterval(fallbackIntervalId)
              setUploadError('Unable to track document progress. Please check manually.')
            }
          }
        } catch (error) {
          console.warn('Fallback polling error:', error)
          retryCount++
        }
      }, pollInterval)
    }

    // Enhanced document update handler
    const handleDocumentUpdate = (document: any) => {
      if (!subscriptionActive) return
      
      console.log('📡 Document update:', { status: document.status, progress: document.progress_percentage })
      
      // Clear timeout since we received an update
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
      
      // Reset retry count on successful update
      retryCount = 0
      
             // Status-based progress with better messaging
       const statusConfig: Record<string, { progress: number; message: string; animated: boolean }> = {
         'uploading': { progress: 10, message: "📤 Uploading file...", animated: true },
         'processing': { progress: 50, message: "🔄 Processing document...", animated: true },
         'parsing': { progress: 60, message: "📄 Extracting text...", animated: true },
         'chunking': { progress: 70, message: "✂️ Breaking into sections...", animated: true },
         'vectorizing': { progress: 85, message: "🧠 Generating embeddings...", animated: true },
         'completed': { progress: 100, message: "✅ Document ready!", animated: false },
         'failed': { progress: 0, message: "❌ Processing failed", animated: false }
       }
       
       const config = statusConfig[document.status] || { progress: 25, message: "⚙️ Processing...", animated: true }
      
      setUploadProgress(config.progress)
      setUploadMessage(config.message)
      
      if (document.status === 'completed') {
          setUploadSuccess(true)
          setIsUploading(false)
          
          // Create success result
          const result: UploadResponse = {
            success: true,
            document_id: document.id,
            filename: selectedFile?.name || document.original_filename || '',
          chunks_processed: 1, // Simplified - don't track chunks
          total_chunks: 1,
          text_length: 0, // Will be calculated later if needed
          message: `Document processed successfully!`
          }
          
          if (onUploadSuccess) {
            onUploadSuccess(result)
          }
          
          // Auto-reset after success
          setTimeout(() => {
            resetUpload()
          }, 3000)
        
      } else if (document.status === 'failed') {
          setUploadError(document.error_message || 'Document processing failed')
          setUploadProgress(0)
          setUploadMessage("")
          setIsUploading(false)
          
          if (onUploadError) {
            onUploadError(document.error_message || 'Document processing failed')
          }
      }
    }

    // Start with WebSocket, fallback to polling
    const attemptWebSocketConnection = () => {
    const channel = supabase
        .channel(`document-progress-${documentId}`, {
          config: {
            presence: { key: documentId },
            broadcast: { self: true }
          }
        })
      .on('postgres_changes', 
        { 
          event: 'UPDATE', 
          schema: 'public', 
          table: 'documents',
          filter: `id=eq.${documentId}`
        }, 
        (payload: any) => {
            try {
              console.log('📡 WebSocket update received:', payload.new)
          handleDocumentUpdate(payload.new)
            } catch (err) {
              console.error('Error handling WebSocket update:', err)
            }
        }
      )
        .subscribe((status: string, err?: any) => {
          console.log(`📡 WebSocket status: ${status}`)
        
        if (status === 'SUBSCRIBED') {
            console.log('✅ WebSocket connected successfully!')
            subscriptionActive = true
            if (timeoutId) clearTimeout(timeoutId)
            
          } else if (status === 'CLOSED') {
            subscriptionActive = false
            console.log('🔄 WebSocket connection closed')
            
        } else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
            console.warn(`⚠️ WebSocket failed: ${status}`)
            if (err) console.error('WebSocket error:', err)
            subscriptionActive = false
            startFallbackPolling()
          }
        })

      // Cleanup function
      return () => {
        if (supabase && channel) {
          supabase.removeChannel(channel)
        }
      }
    }

    // Try WebSocket first, with timeout fallback
    timeoutId = setTimeout(() => {
      if (subscriptionActive) {
        console.warn('⚠️ WebSocket timeout - switching to polling')
        startFallbackPolling()
      }
    }, 15000) // Reduced timeout for faster fallback

    const cleanupWebSocket = attemptWebSocketConnection()

    // Cleanup function
    return () => {
      subscriptionActive = false
      if (timeoutId) clearTimeout(timeoutId)
      if (fallbackIntervalId) clearInterval(fallbackIntervalId)
      cleanupWebSocket()
    }
  }, [documentId, supabase, selectedFile, onUploadSuccess, onUploadError])

  // Validate file
  const validateFile = (file: File): string | null => {
    // File size validation (50MB limit)
    const maxSize = 50 * 1024 * 1024
    if (file.size > maxSize) {
      return `File size too large. Maximum allowed size is 50MB. Your file is ${(file.size / 1024 / 1024).toFixed(1)}MB.`
    }

    // File type validation
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ]
    
    const allowedExtensions = ['.pdf', '.doc', '.docx', '.txt']
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    
    if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
      return `File type not supported. Please upload PDF, DOC, DOCX, or TXT files only. Your file type: ${file.type || 'unknown'}`
    }

    // File name validation
    if (file.name.length > 200) {
      return 'File name too long. Please rename your file to be shorter than 200 characters.'
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
        // Enhanced error handling for backend API responses
        let errorData
        try {
          errorData = await uploadResponse.json()
        } catch (jsonError) {
          console.warn('Could not parse error response as JSON, trying as text')
          try {
            const textData = await uploadResponse.text()
            errorData = { error: textData || 'Unknown error' }
          } catch (textError) {
            errorData = { error: `Upload failed with status ${uploadResponse.status}` }
          }
        }
        
        // Extract error message from various response formats
        let errorMessage = 'Upload failed'
        if (errorData) {
          if (typeof errorData === 'string') {
            errorMessage = errorData
          } else if (errorData.detail) {
            // FastAPI format
            if (typeof errorData.detail === 'string') {
              errorMessage = errorData.detail
            } else if (errorData.detail.message) {
              errorMessage = errorData.detail.message
            } else if (errorData.detail.error) {
              errorMessage = errorData.detail.error
            } else {
              errorMessage = JSON.stringify(errorData.detail)
            }
          } else if (errorData.error) {
            errorMessage = errorData.error
          } else if (errorData.message) {
            errorMessage = errorData.message
          } else {
            // Fallback to stringifying the whole object
            errorMessage = JSON.stringify(errorData)
          }
        }
        
        // Add status code to error message
        errorMessage = `${errorMessage} (Status: ${uploadResponse.status})`
        
        throw new Error(errorMessage)
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
      handleUploadError(error)
    }
  }

  // ✅ CRITICAL FIX: Proper error handling for upload responses
  const handleUploadError = (error: any) => {
      console.error('Upload error:', error)
      
    // Better error message handling
    let errorMessage = 'Upload failed'
    if (error && typeof error === 'object') {
      if (error.response?.data?.error) {
        errorMessage = error.response.data.error
      } else if (error.message) {
        errorMessage = error.message
      }
    } else if (typeof error === 'string') {
      errorMessage = error
    } else {
      errorMessage = JSON.stringify(error)
    }
    
    console.log('Upload failed:', errorMessage)
    setUploadError(errorMessage)
    setIsUploading(false)
    setUploadProgress(0)
    onUploadError?.(errorMessage)
  }

  // Manual status check function
  const checkDocumentStatus = async () => {
    if (!documentId || !supabase) return
    
    console.log('🔍 Manual status check for document:', documentId)
    setUploadMessage("🔍 Checking document status...")
    
    try {
      const { data: document, error } = await supabase
        .from('documents')
        .select('id, status, progress_percentage, error_message, original_filename, created_at')
        .eq('id', documentId)
        .single()
      
      if (!error && document) {
        console.log('📄 Manual check result:', document)
        
        // Force update the UI with current status
        if (document.status === 'completed') {
          setUploadProgress(100)
          setUploadMessage("✅ Document ready!")
          setUploadSuccess(true)
          setIsUploading(false)
          
          if (onUploadSuccess) {
            onUploadSuccess({
              success: true,
              document_id: document.id,
              filename: selectedFile?.name || document.original_filename || '',
              chunks_processed: 1,
              total_chunks: 1,
              text_length: 0,
              message: 'Document processed successfully!'
            })
          }
        } else if (document.status === 'failed') {
          setUploadError(document.error_message || 'Document processing failed')
      setUploadProgress(0)
      setIsUploading(false)
        } else {
                     // Still processing
           const statusProgress: Record<string, number> = {
             'processing': 50,
             'parsing': 60, 
             'chunking': 70,
             'vectorizing': 85
           }
                      const progress = statusProgress[document.status] || 25
           
           setUploadProgress(progress)
          setUploadMessage(`🔄 ${document.status}...`)
        }
      } else {
        setUploadMessage("⚠️ Could not retrieve document status")
      }
    } catch (error) {
      console.error('Manual status check failed:', error)
      setUploadMessage("❌ Status check failed")
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
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">{uploadMessage}</span>
              <span className="text-teal-600 font-medium">{uploadProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div 
                className={`
                  h-3 rounded-full transition-all duration-500 ease-in-out
                  ${uploadProgress === 100 
                    ? 'bg-green-500' 
                    : 'bg-gradient-to-r from-teal-500 to-teal-600'
                  }
                  ${uploadProgress > 0 && uploadProgress < 100 
                    ? 'animate-pulse' 
                    : ''
                  }
                `}
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            
            {/* Processing Steps Indicator */}
            <div className="flex items-center justify-center space-x-1 py-2">
              {['📤', '🔄', '📄', '✂️', '🧠'].map((emoji, index) => {
                const stepProgress = Math.max(0, Math.min(100, (uploadProgress - (index * 20)) * 5))
                return (
                  <div 
                    key={index}
                    className={`
                      flex items-center justify-center w-8 h-8 rounded-full text-xs
                      transition-all duration-300
                      ${stepProgress > 50 
                        ? 'bg-teal-100 border-2 border-teal-500' 
                        : stepProgress > 0 
                          ? 'bg-gray-100 border-2 border-gray-300 animate-bounce' 
                          : 'bg-gray-50 border border-gray-200'
                      }
                    `}
                  >
                    {emoji}
                  </div>
                )
              })}
            </div>
            
            {/* Manual Status Check Button */}
            {documentId && uploadProgress > 0 && uploadProgress < 100 && (
              <div className="flex justify-center pt-2">
                <button
                  onClick={checkDocumentStatus}
                  className="text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-md transition-colors flex items-center space-x-1"
                >
                  <span>🔍</span>
                  <span>Check Status</span>
                </button>
              </div>
            )}
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
              <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-red-700 font-medium">Upload failed</p>
                <p className="text-xs text-red-600 mt-1 break-words">{uploadError}</p>
                
                {/* Recovery Actions */}
                <div className="flex flex-wrap gap-2 mt-3">
                  <button
                    onClick={resetUpload}
                    className="text-xs bg-red-100 hover:bg-red-200 text-red-700 px-2 py-1 rounded transition-colors"
                  >
                    Try Again
                  </button>
                  
                  {documentId && (
                    <button
                      onClick={checkDocumentStatus}
                      className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded transition-colors"
                    >
                      Check Status
                    </button>
                  )}
                  
                  <button
                    onClick={() => {
                      setUploadError(null)
                      setUploadMessage("Please try uploading a different file or contact support.")
                    }}
                    className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded transition-colors"
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
        
        {/* Recent Uploads Section */}
        {recentUploads.length > 0 && !isUploading && (
          <div className="border-t pt-4">
            <button
              onClick={() => setShowRecentUploads(!showRecentUploads)}
              className="flex items-center justify-between w-full text-sm text-gray-600 hover:text-gray-800 transition-colors"
            >
              <span>📄 Recent uploads ({recentUploads.length})</span>
              <span className={`transform transition-transform ${showRecentUploads ? 'rotate-180' : ''}`}>
                ↓
              </span>
            </button>
            
            {showRecentUploads && (
              <div className="mt-3 space-y-2">
                {recentUploads.map((doc) => {
                  const uploadTime = new Date(doc.created_at).toLocaleDateString()
                  const fileSize = (doc.file_size / 1024 / 1024).toFixed(1)
                  const statusColors: Record<string, string> = {
                    'completed': 'text-green-600',
                    'failed': 'text-red-600',
                    'processing': 'text-yellow-600',
                    'vectorizing': 'text-blue-600'
                  }
                  const statusColor = statusColors[doc.status] || 'text-gray-600'
                  
                  const statusIcons: Record<string, string> = {
                    'completed': '✅',
                    'failed': '❌', 
                    'processing': '🔄',
                    'vectorizing': '🧠'
                  }
                  const statusIcon = statusIcons[doc.status] || '⏳'
                  
                  return (
                    <div key={doc.id} className="flex items-center justify-between p-2 bg-gray-50 rounded text-xs">
                      <div className="flex items-center space-x-2 flex-1 min-w-0">
                        <span>{statusIcon}</span>
                        <span className="truncate font-medium">{doc.original_filename}</span>
                      </div>
                      <div className="flex items-center space-x-2 text-gray-500">
                        <span>{fileSize}MB</span>
                        <span>•</span>
                        <span>{uploadTime}</span>
                        <span className={`${statusColor} font-medium`}>
                          {doc.status}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  )
} 