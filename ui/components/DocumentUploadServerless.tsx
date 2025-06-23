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

  // ✅ CRITICAL FIX: Improved real-time subscription with timeout handling
  useEffect(() => {
    if (!documentId || !supabase) return

    let subscriptionActive = true
    let timeoutId: NodeJS.Timeout
    let fallbackIntervalId: NodeJS.Timeout

    console.log('🔄 Setting up real-time subscription for document:', documentId)

    // Fallback polling mechanism for when WebSocket fails
    const startFallbackPolling = () => {
      console.log('🚨 WebSocket failed, starting fallback polling...')
      setUploadMessage("⚙️ Processing in background - checking progress...")
      
      fallbackIntervalId = setInterval(async () => {
        if (!subscriptionActive) return
        
        try {
          const { data: document, error } = await supabase
            .from('documents')
            .select('*')
            .eq('id', documentId)
            .single()
          
          if (!error && document) {
            handleDocumentUpdate(document)
          }
        } catch (error) {
          console.warn('Fallback polling error:', error)
        }
      }, 5000) // Poll every 5 seconds
    }

    // Handle document updates from Supabase real-time
    const handleDocumentUpdate = (document: any) => {
      if (!subscriptionActive) return
      
      console.log('📡 Real-time update received:', document)
      setUploadProgress(document.progress_percentage || 0)
      
      // Clear timeout since we received an update
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
      
      // Update status messages based on document status
      switch(document.status) {
        case 'uploading':
          setUploadMessage("📤 Uploading file...")
          break
        case 'processing':
          setUploadMessage("🔄 Processing document...")
          break
        case 'parsing':
          setUploadMessage("📄 Extracting text from document...")
          break
        case 'chunking':
          setUploadMessage("✂️ Breaking down content into sections...")
          break
        case 'vectorizing':
          setUploadMessage(`🧠 Generating embeddings (${document.processed_chunks || 0}/${document.total_chunks || 0} sections)...`)
          break
        case 'completed':
          setUploadMessage(`✅ Success! Processed ${document.total_chunks || 0} sections from your document.`)
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
            text_length: document.metadata?.text_length || 0,
            message: `Document processed successfully with ${document.total_chunks || 0} chunks`
          }
          
          if (onUploadSuccess) {
            onUploadSuccess(result)
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
          
          if (onUploadError) {
            onUploadError(document.error_message || 'Document processing failed')
          }
          break
      }
    }

    // Set timeout for subscription establishment (60 seconds instead of 30)
    timeoutId = setTimeout(() => {
      if (subscriptionActive) {
        console.warn('⚠️ Real-time subscription timeout, switching to fallback polling')
        startFallbackPolling()
      }
    }, 60000) // Increased timeout

    // Set up Supabase real-time subscription with enhanced error handling
    const channel = supabase
      .channel(`document-progress-${documentId}`, {
        config: {
          presence: {
            key: documentId
          }
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
            console.log('📡 Supabase real-time update:', payload.new)
            handleDocumentUpdate(payload.new)
          } catch (err) {
            console.error('Error handling real-time update:', err)
          }
        }
      )
      .subscribe((status: string, err?: any) => {
        console.log(`📡 Background notification subscription status: ${status}`)
        
        if (status === 'SUBSCRIBED') {
          console.log('✅ Background processing notifications active!')
          subscriptionActive = true
          if (timeoutId) {
            clearTimeout(timeoutId)
          }
        } else if (status === 'CLOSED') {
          subscriptionActive = false
          console.log('🔄 Cleaning up background notification subscription')
        } else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
          console.warn(`⚠️ Background notification subscription failed: ${status}`)
          if (err) {
            console.error('Subscription error details:', err)
          }
          subscriptionActive = false
          // Start fallback polling immediately on error
          if (!fallbackIntervalId) {
            startFallbackPolling()
          }
        }
      })

    return () => {
      subscriptionActive = false
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
      if (fallbackIntervalId) {
        clearInterval(fallbackIntervalId)
      }
      if (supabase && channel) {
        supabase.removeChannel(channel)
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